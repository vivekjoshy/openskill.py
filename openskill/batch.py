"""Batch processing for openskill rating models.

Enables parallel processing of thousands of games with automatic
wave-based partitioning for entity safety and reproducible ordering.

Architecture:
    Games are partitioned into "waves" where no entity (player) appears
    in more than one game within the same wave. This guarantees:

    1. **Safety**: No concurrent writes to the same entity's ratings.
    2. **Ordering**: If game *i* precedes game *j* and they share an
       entity, *i*'s wave is strictly earlier than *j*'s wave.
    3. **Parallelism**: All games within a wave can run simultaneously.

    A background thread builds waves ahead of time (producer) while
    worker processes/threads consume and process them.

Threading Model:
    - Free-threaded Python (3.13t/3.14t): Uses ``ThreadPoolExecutor``
      for true parallel execution with shared memory (zero-copy).
    - GIL Python: Uses ``ProcessPoolExecutor`` with per-worker model
      initialization and serialized results. Wave partitioning ensures
      no shared-state conflicts.

Usage::

    from openskill.models import PlackettLuce
    from openskill.batch import BatchProcessor, Game

    model = PlackettLuce()
    processor = BatchProcessor(model, n_workers=10)
    games = [
        Game(teams=[["alice", "bob"], ["carol", "dave"]], ranks=[1, 2]),
        Game(teams=[["alice", "eve"], ["frank", "grace"]], scores=[10, 20]),
    ]

    ratings = processor.process(games)
    # {"alice": (mu, sigma), "bob": (mu, sigma), ...}
"""

from __future__ import annotations

import importlib
import math
import multiprocessing
import queue
import sys
import sysconfig
import threading
from concurrent.futures import Executor, ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

__all__ = [
    "Game",
    "BatchProcessor",
    "_FastRating",
    "partition_waves",
    "MAX_TEAM_SIZE",
    "MAX_ENTITIES",
]

# ---------------------------------------------------------------------------
# Capacity constants
# ---------------------------------------------------------------------------
# These caps keep per-game working sets small enough for CPU-cache-friendly
# processing and bound the flat rating arrays to predictable sizes.
# They also serve as documentation of the design envelope.

MAX_TEAM_SIZE: int = 32
"""Maximum players per team.  Keeps per-game data on the stack in a future
C/Cython hot-loop (32 players × 2 floats × 8 bytes = 512 B, fits in L1)."""

MAX_ENTITIES: int = 16_000
"""Maximum tracked entities.  The two flat arrays (mu, sigma) at this size
consume 16 000 × 2 × 8 = 256 KB — comfortably within L2 cache."""


# ---------------------------------------------------------------------------
# _FastRating — minimal duck-type for _compute()
# ---------------------------------------------------------------------------


class _FastRating:
    """Disposable Rating substitute for ``_compute()``.

    ``model.rating()`` generates a UUID via ``/dev/urandom`` and
    allocates a ``__dict__`` on every call.  ``_FastRating`` avoids
    both: ``__slots__`` eliminates the dict, and there is no UUID.

    ``_compute()`` only reads/writes ``.mu``, ``.sigma``, and calls
    ``.ordinal()``.  This class satisfies that contract at minimal cost.
    """

    __slots__ = ("mu", "sigma")

    def __init__(self, mu: float, sigma: float) -> None:
        self.mu = mu
        self.sigma = sigma

    def ordinal(
        self,
        z: float = 3.0,
        alpha: float = 1,
        target: float = 0,
    ) -> float:
        return alpha * ((self.mu - z * self.sigma) + (target / alpha))


# ---------------------------------------------------------------------------
# Runtime detection
# ---------------------------------------------------------------------------


def _is_free_threaded() -> bool:
    """Check if running on free-threaded Python with GIL disabled."""
    build_supports = sysconfig.get_config_var("Py_GIL_DISABLED") == 1
    gil_disabled = hasattr(sys, "_is_gil_enabled") and not sys._is_gil_enabled()
    return build_supports and gil_disabled


_FREE_THREADED: bool = _is_free_threaded()

# Global model reference for worker processes (set by _init_worker).
_worker_model: Any = None
_worker_tau_sq: float = 0.0


# ---------------------------------------------------------------------------
# Game descriptor
# ---------------------------------------------------------------------------


@dataclass
class Game:
    """
    Descriptor for a single game in batch processing.

    :param teams: List of teams, each a list of entity ID strings.
    :param ranks: Optional ranks (lower = better). Mutually exclusive
                  with scores.
    :param scores: Optional scores (higher = better). Mutually exclusive
                   with ranks.
    :param weights: Optional per-player contribution weights.
    """

    teams: list[list[str]]
    ranks: list[float] | None = None
    scores: list[float] | None = None
    weights: list[list[float]] | None = None


# ---------------------------------------------------------------------------
# Wave partitioning
# ---------------------------------------------------------------------------


def partition_waves(games: list[Game]) -> list[list[tuple[int, Game]]]:
    """
    Partition games into conflict-free waves that respect chronological
    ordering.

    Two invariants are maintained:

    1. **Safety** — no entity appears in two games within the same wave.
    2. **Ordering** — if game *i* comes before game *j* in the input and
       they share at least one entity, then *i*'s wave is strictly
       earlier than *j*'s wave.

    Together these guarantee that parallel execution within a wave
    produces the same ratings as fully-sequential processing.

    :param games: Games in processing order.
    :return: List of waves. Each wave is a list of
             ``(original_index, game)`` tuples.
    """
    waves: list[list[tuple[int, Game]]] = []
    wave_entities: list[set[str]] = []
    # Track the latest wave each entity was placed in so we never
    # put a game *before* an earlier game that shares an entity.
    entity_latest_wave: dict[str, int] = {}

    for idx, game in enumerate(games):
        game_ents: set[str] = set()
        for team in game.teams:
            game_ents.update(team)

        # Earliest wave this game may occupy: must come after every
        # wave that already contains one of its entities.
        min_wave = 0
        for ent in game_ents:
            if ent in entity_latest_wave:
                min_wave = max(min_wave, entity_latest_wave[ent] + 1)

        # Find first wave >= min_wave with no entity overlap.
        placed = False
        for w_idx in range(min_wave, len(waves)):
            if game_ents.isdisjoint(wave_entities[w_idx]):
                waves[w_idx].append((idx, game))
                wave_entities[w_idx].update(game_ents)
                for ent in game_ents:
                    entity_latest_wave[ent] = w_idx
                placed = True
                break

        if not placed:
            new_idx = len(waves)
            waves.append([(idx, game)])
            wave_entities.append(game_ents.copy())
            for ent in game_ents:
                entity_latest_wave[ent] = new_idx

    return waves


# ---------------------------------------------------------------------------
# Model serialisation helpers (for multiprocessing)
# ---------------------------------------------------------------------------


def _extract_model_config(model: Any) -> tuple[str, str, dict[str, Any]]:
    """
    Extract picklable model constructor arguments.

    Custom gamma functions must be picklable (module-level functions
    work; lambdas will raise ``PickleError`` at submission time).
    """
    model_class = type(model)
    module: str = model_class.__module__
    class_name: str = model_class.__name__

    kwargs: dict[str, Any] = {
        "mu": model.mu,
        "sigma": model.sigma,
        "beta": model.beta,
        "kappa": model.kappa,
        "tau": model.tau,
        "limit_sigma": model.limit_sigma,
    }

    if hasattr(model, "gamma"):
        kwargs["gamma"] = model.gamma
    if hasattr(model, "margin"):
        kwargs["margin"] = model.margin
    if hasattr(model, "balance"):
        kwargs["balance"] = model.balance
    if hasattr(model, "weight_bounds"):
        kwargs["weight_bounds"] = model.weight_bounds

    return module, class_name, kwargs


def _init_worker(
    module_name: str, class_name: str, model_kwargs: dict[str, Any]
) -> None:
    """Initialize model in worker process (called once per process)."""
    global _worker_model, _worker_tau_sq
    mod = importlib.import_module(module_name)
    model_class = getattr(mod, class_name)
    _worker_model = model_class(**model_kwargs)
    _worker_tau_sq = _worker_model.tau**2


def _worker_rate_game(
    args: tuple[
        list[list[int]],
        list[list[float]],
        list[list[float]],
        list[float] | None,
        list[float] | None,
        list[list[float]] | None,
    ],
) -> list[tuple[int, float, float]]:
    """
    Rate a single game in a worker process — fast path.

    Bypasses ``model.rate()`` to avoid deepcopy and validation.
    Applies tau correction inline and calls ``_compute`` directly.

    :return: List of ``(entity_array_index, new_mu, new_sigma)``.
    """
    team_indices, team_mus, team_sigmas, ranks, scores, weights = args
    model = _worker_model
    tau_sq: float = _worker_tau_sq
    limit_sigma: bool = model.limit_sigma

    # Build teams with tau pre-applied (no deepcopy needed).
    teams: list[list[Any]] = []
    for t_mus, t_sigs in zip(team_mus, team_sigmas):
        team = [
            _FastRating(m, math.sqrt(s * s + tau_sq)) for m, s in zip(t_mus, t_sigs)
        ]
        teams.append(team)

    # Convert scores → ranks (matches rate() logic exactly).
    ranks_list: list[float] | None = list(ranks) if ranks is not None else None
    scores_list: list[float] | None = list(scores) if scores is not None else None
    if not ranks_list and scores_list:
        ranks_list = list(map(lambda s: -s, scores_list))
        ranks_list = model._calculate_rankings(teams, ranks_list)

    weight_lists: list[list[float]] | None = (
        [list(w) for w in weights] if weights is not None else None
    )

    # Sort teams by rank before _compute (PlackettLuce requires this).
    if ranks_list is not None:
        _rl = ranks_list  # local binding for lambda closure
        order: list[int] = sorted(range(len(_rl)), key=lambda i: _rl[i])
        teams = [teams[i] for i in order]
        team_indices = [team_indices[i] for i in order]
        team_sigmas = [team_sigmas[i] for i in order]
        ranks_list = sorted(ranks_list)
        if scores_list is not None:
            scores_list = [scores_list[i] for i in order]
        if weight_lists is not None:
            weight_lists = [weight_lists[i] for i in order]

    result = model._compute(
        teams=teams,
        ranks=ranks_list,
        scores=scores_list,
        weights=weight_lists,
    )

    updates: list[tuple[int, float, float]] = []
    for team_idx, team in enumerate(result):
        for player_idx, player in enumerate(team):
            eidx: int = team_indices[team_idx][player_idx]
            new_sigma: float = player.sigma
            if limit_sigma:
                new_sigma = min(new_sigma, team_sigmas[team_idx][player_idx])
            updates.append((eidx, player.mu, new_sigma))

    return updates


# ---------------------------------------------------------------------------
# BatchProcessor
# ---------------------------------------------------------------------------


class BatchProcessor:
    """
    Parallel batch processor for openskill rating models.

    Partitions games into conflict-free waves and processes each
    wave in parallel. A background thread builds waves ahead of
    computation so workers never wait for partitioning.

    :param model: An openskill model instance (e.g. ``PlackettLuce()``).
    :param n_workers: Number of parallel workers. Defaults to CPU count.
    :param pipeline: If ``True``, build waves in a background thread
                     while workers process earlier waves.
    """

    def __init__(
        self,
        model: Any,
        n_workers: int | None = None,
        pipeline: bool = True,
    ) -> None:
        self.model: Any = model
        self.n_workers: int = n_workers or multiprocessing.cpu_count()
        self.pipeline: bool = pipeline
        self._use_threads: bool = _FREE_THREADED
        self._model_config: tuple[str, str, dict[str, Any]] = _extract_model_config(
            model
        )
        self._tau_sq: float = model.tau**2
        self._limit_sigma: bool = model.limit_sigma

    def process(
        self,
        games: list[Game],
        initial_ratings: dict[str, tuple[float, float]] | None = None,
    ) -> dict[str, tuple[float, float]]:
        """
        Process all games and return final ratings.

        :param games: Games in chronological/processing order.
        :param initial_ratings: Pre-existing ``{entity_id: (mu, sigma)}``.
        :return: Final ``{entity_id: (mu, sigma)}`` for all entities.
        """
        if not games:
            return dict(initial_ratings) if initial_ratings else {}

        # Build entity registry
        entity_to_idx: dict[str, int] = {}
        for game in games:
            for team in game.teams:
                for eid in team:
                    if eid not in entity_to_idx:
                        entity_to_idx[eid] = len(entity_to_idx)

        n: int = len(entity_to_idx)
        mus: list[float] = [self.model.mu] * n
        sigmas: list[float] = [self.model.sigma] * n

        if initial_ratings:
            for eid, (mu, sigma) in initial_ratings.items():
                if eid in entity_to_idx:
                    idx = entity_to_idx[eid]
                    mus[idx] = mu
                    sigmas[idx] = sigma

        # Dispatch to processing strategy
        if self.n_workers <= 1:
            self._process_sequential(games, entity_to_idx, mus, sigmas)
        elif self.pipeline:
            self._process_pipelined(games, entity_to_idx, mus, sigmas)
        else:
            waves = partition_waves(games)
            self._process_waves(waves, entity_to_idx, mus, sigmas)

        # Build result
        idx_to_eid: dict[int, str] = {v: k for k, v in entity_to_idx.items()}
        return {idx_to_eid[i]: (mus[i], sigmas[i]) for i in range(n)}

    # ------------------------------------------------------------------
    # Processing strategies
    # ------------------------------------------------------------------

    def _process_sequential(
        self,
        games: list[Game],
        entity_to_idx: dict[str, int],
        mus: list[float],
        sigmas: list[float],
    ) -> None:
        """Process all games sequentially (single worker)."""
        for game in games:
            self._rate_game_fast(game, entity_to_idx, mus, sigmas)

    def _process_pipelined(
        self,
        games: list[Game],
        entity_to_idx: dict[str, int],
        mus: list[float],
        sigmas: list[float],
    ) -> None:
        """
        Producer-consumer pipeline.

        A background thread builds waves (fast — set operations only)
        while workers process each wave as it arrives.
        """
        wave_q: queue.Queue[list[tuple[int, Game]] | None] = queue.Queue(
            maxsize=self.n_workers * 2
        )

        def build_waves_ahead() -> None:
            for wave in partition_waves(games):
                wave_q.put(wave)
            wave_q.put(None)  # sentinel

        builder = threading.Thread(target=build_waves_ahead, daemon=True)
        builder.start()

        try:
            if self._use_threads:
                with ThreadPoolExecutor(max_workers=self.n_workers) as executor:
                    while True:
                        wave = wave_q.get()
                        if wave is None:
                            break
                        self._execute_wave_threaded(
                            wave, entity_to_idx, mus, sigmas, executor
                        )
            else:
                module, class_name, model_kwargs = self._model_config
                with ProcessPoolExecutor(
                    max_workers=self.n_workers,
                    initializer=_init_worker,
                    initargs=(module, class_name, model_kwargs),
                ) as proc_executor:
                    while True:
                        wave = wave_q.get()
                        if wave is None:
                            break
                        self._execute_wave_multiprocess(
                            wave, entity_to_idx, mus, sigmas, proc_executor
                        )
        finally:
            builder.join()

    def _process_waves(
        self,
        waves: list[list[tuple[int, Game]]],
        entity_to_idx: dict[str, int],
        mus: list[float],
        sigmas: list[float],
    ) -> None:
        """Process pre-built waves (non-pipelined)."""
        if self._use_threads:
            with ThreadPoolExecutor(max_workers=self.n_workers) as executor:
                for wave in waves:
                    self._execute_wave_threaded(
                        wave, entity_to_idx, mus, sigmas, executor
                    )
        else:
            module, class_name, model_kwargs = self._model_config
            with ProcessPoolExecutor(
                max_workers=self.n_workers,
                initializer=_init_worker,
                initargs=(module, class_name, model_kwargs),
            ) as proc_executor:
                for wave in waves:
                    self._execute_wave_multiprocess(
                        wave, entity_to_idx, mus, sigmas, proc_executor
                    )

    # ------------------------------------------------------------------
    # Wave execution
    # ------------------------------------------------------------------

    def _execute_wave_threaded(
        self,
        wave: list[tuple[int, Game]],
        entity_to_idx: dict[str, int],
        mus: list[float],
        sigmas: list[float],
        executor: ThreadPoolExecutor,
    ) -> None:
        """Process a wave with ThreadPoolExecutor (free-threaded Python)."""
        if len(wave) <= 2:
            for _, game in wave:
                self._rate_game_fast(game, entity_to_idx, mus, sigmas)
            return

        futures = [
            executor.submit(self._rate_game_fast, game, entity_to_idx, mus, sigmas)
            for _, game in wave
        ]
        for f in futures:
            f.result()

    def _execute_wave_multiprocess(
        self,
        wave: list[tuple[int, Game]],
        entity_to_idx: dict[str, int],
        mus: list[float],
        sigmas: list[float],
        executor: ProcessPoolExecutor,
    ) -> None:
        """Process a wave with ProcessPoolExecutor (GIL Python)."""
        if len(wave) <= 2:
            for _, game in wave:
                self._rate_game_fast(game, entity_to_idx, mus, sigmas)
            return

        work_items: list[
            tuple[
                list[list[int]],
                list[list[float]],
                list[list[float]],
                list[float] | None,
                list[float] | None,
                list[list[float]] | None,
            ]
        ] = []
        for _, game in wave:
            team_indices: list[list[int]] = []
            team_mus: list[list[float]] = []
            team_sigmas: list[list[float]] = []

            for team_ids in game.teams:
                indices = [entity_to_idx[eid] for eid in team_ids]
                team_indices.append(indices)
                team_mus.append([mus[i] for i in indices])
                team_sigmas.append([sigmas[i] for i in indices])

            work_items.append(
                (
                    team_indices,
                    team_mus,
                    team_sigmas,
                    game.ranks,
                    game.scores,
                    game.weights,
                )
            )

        chunksize: int = max(1, len(work_items) // (self.n_workers * 4))
        for updates in executor.map(_worker_rate_game, work_items, chunksize=chunksize):
            for idx, new_mu, new_sigma in updates:
                mus[idx] = new_mu
                sigmas[idx] = new_sigma

    # ------------------------------------------------------------------
    # Per-game rating (fast path — no deepcopy)
    # ------------------------------------------------------------------

    def _rate_game_fast(
        self,
        game: Game,
        entity_to_idx: dict[str, int],
        mus: list[float],
        sigmas: list[float],
    ) -> None:
        """
        Rate a single game — fast path.

        Bypasses ``model.rate()`` to avoid:
        - ``copy.deepcopy`` (~58 % of rate() time)
        - Input validation (we control the inputs)

        Applies tau correction inline and calls ``_compute`` directly.
        """
        model: Any = self.model
        tau_sq: float = self._tau_sq
        limit_sigma: bool = self._limit_sigma

        teams: list[list[Any]] = []
        team_indices: list[list[int]] = []
        for team_ids in game.teams:
            team: list[Any] = []
            indices: list[int] = []
            for eid in team_ids:
                idx: int = entity_to_idx[eid]
                team.append(_FastRating(mus[idx], math.sqrt(sigmas[idx] ** 2 + tau_sq)))
                indices.append(idx)
            teams.append(team)
            team_indices.append(indices)

        ranks: list[float] | None = list(game.ranks) if game.ranks is not None else None
        scores: list[float] | None = (
            list(game.scores) if game.scores is not None else None
        )
        weights: list[list[float]] | None = (
            [list(w) for w in game.weights] if game.weights is not None else None
        )

        # Convert scores → ranks (matches rate() logic exactly).
        # _calculate_rankings returns a flat list of 0-based ordinals.
        if not ranks and scores:
            ranks = list(map(lambda s: -s, scores))
            ranks = model._calculate_rankings(teams, ranks)

        # Sort teams by rank before calling _compute.
        # PlackettLuce (and potentially future models) requires teams
        # in rank order for its sequential-elimination formula.
        if ranks is not None:
            _ranks = ranks  # local binding for lambda closure
            order: list[int] = sorted(range(len(_ranks)), key=lambda i: _ranks[i])
            teams = [teams[i] for i in order]
            team_indices = [team_indices[i] for i in order]
            ranks = sorted(ranks)
            if scores is not None:
                scores = [scores[i] for i in order]
            if weights is not None:
                weights = [weights[i] for i in order]

        result = model._compute(
            teams=teams,
            ranks=ranks,
            scores=scores,
            weights=weights,
        )

        # Write back to flat arrays (team_indices already sorted to
        # match the order passed to _compute).
        for team_idx, team_result in enumerate(result):
            for player_idx, player in enumerate(team_result):
                idx = team_indices[team_idx][player_idx]
                new_sigma: float = player.sigma
                if limit_sigma:
                    new_sigma = min(new_sigma, sigmas[idx])
                mus[idx] = player.mu
                sigmas[idx] = new_sigma
