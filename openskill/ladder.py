"""In-place rating registry backed by contiguous arrays.

A :class:`Ladder` stores all entity ratings in pre-allocated
:class:`array.array` buffers (contiguous C doubles) and exposes
lightweight :class:`RatingView` flyweight objects that reference
the backing store directly.  Games are rated in-place — no copies,
no dict write-back, no per-call allocation.

Architecture::

    ┌────────────────────────────────────────────────────────┐
    │ Ladder                                                 │
    │  _mus   = array('d', [25.0, 25.0, 30.0, ...])  256 KB │
    │  _sigmas= array('d', [ 8.3,  8.3,  5.0, ...])  256 KB │
    │  _entity_to_idx = {"alice": 0, "bob": 1, ...}         │
    │  _views = {"alice": RatingView(0), ...}                │
    └────────────────────────────────────────────────────────┘
              │                                │
              ▼                                ▼
    ladder["alice"].mu  ─►  _mus[0]    ladder["alice"].sigma ─► _sigmas[0]

Usage::

    from openskill.models import PlackettLuce
    from openskill.ladder import Ladder

    model = PlackettLuce()
    lad = Ladder(model)

    # Auto-registers on first access
    lad["alice"]
    lad.add("bob", mu=30.0, sigma=5.0)

    # Rate — mutates in-place, zero copies
    lad.rate([["alice"], ["bob"]], ranks=[1, 2])
    print(lad["alice"].mu)   # updated

    # Bulk processing with wave-based parallelism
    lad.rate_batch(games)
"""

from __future__ import annotations

import array
import math
from collections.abc import Iterator, KeysView
from typing import Any

from openskill.batch import MAX_ENTITIES, Game, _FastRating, partition_waves

__all__ = ["Ladder", "RatingView"]

# Try to import the optional Cython fast path.
try:
    from openskill import _cfast  # type: ignore[attr-defined]

    _cy_rate_game = _cfast.cy_rate_game

    _HAS_CYTHON: bool = True
except ImportError:
    _cy_rate_game = None  # type: ignore[assignment,misc,unused-ignore]
    _HAS_CYTHON = False


# ---------------------------------------------------------------------------
# RatingView — flyweight into backing arrays
# ---------------------------------------------------------------------------


class RatingView:
    """Lightweight view into a Ladder's backing arrays.

    Two pointers + one int = 24 bytes.  Attribute access goes
    straight to the contiguous ``array.array('d')`` buffers
    via property descriptors — no per-access allocation.
    """

    __slots__ = ("_mus", "_sigmas", "_idx", "_id")

    def __init__(
        self,
        mus: array.array[float],
        sigmas: array.array[float],
        idx: int,
        entity_id: str,
    ) -> None:
        self._mus = mus
        self._sigmas = sigmas
        self._idx = idx
        self._id = entity_id

    # --- Properties that read/write the backing arrays directly ---

    @property
    def mu(self) -> float:
        result: float = self._mus[self._idx]
        return result

    @mu.setter
    def mu(self, value: float) -> None:
        self._mus[self._idx] = value

    @property
    def sigma(self) -> float:
        result: float = self._sigmas[self._idx]
        return result

    @sigma.setter
    def sigma(self, value: float) -> None:
        self._sigmas[self._idx] = value

    @property
    def entity_id(self) -> str:
        return self._id

    def ordinal(self, z: float = 3.0) -> float:
        """Conservative skill estimate (mu - z*sigma)."""
        mu: float = self._mus[self._idx]
        sigma: float = self._sigmas[self._idx]
        return mu - z * sigma

    def __repr__(self) -> str:
        return f"RatingView({self._id!r}, " f"mu={self.mu:.4f}, sigma={self.sigma:.4f})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RatingView):
            return NotImplemented
        return self.mu == other.mu and self.sigma == other.sigma

    def __lt__(self, other: RatingView) -> bool:
        return self.ordinal() < other.ordinal()


# ---------------------------------------------------------------------------
# Ladder — the main registry
# ---------------------------------------------------------------------------


class Ladder:
    """In-place rating registry backed by contiguous ``array.array('d')``.

    :param model: An openskill model instance (e.g. ``PlackettLuce()``).
    :param max_entities: Pre-allocated capacity.  Two arrays of this
        size consume ``max_entities * 2 * 8`` bytes (256 KB at 16 000).
    :param use_cython: Use Cython fast path if available.
        ``None`` = auto-detect.
    """

    __slots__ = (
        "_model",
        "_max",
        "_mus",
        "_sigmas",
        "_entity_to_idx",
        "_views",
        "_size",
        "_tau_sq",
        "_limit_sigma",
        "_default_mu",
        "_default_sigma",
        "_use_cython",
    )

    def __init__(
        self,
        model: Any,
        max_entities: int = MAX_ENTITIES,
        use_cython: bool | None = None,
    ) -> None:
        self._model: Any = model
        self._max: int = max_entities
        # Pre-allocated contiguous C-double arrays.
        self._mus: array.array[float] = array.array("d", bytes(8 * max_entities))
        self._sigmas: array.array[float] = array.array("d", bytes(8 * max_entities))
        self._entity_to_idx: dict[str, int] = {}
        self._views: dict[str, RatingView] = {}
        self._size: int = 0
        self._tau_sq: float = model.tau**2
        self._limit_sigma: bool = model.limit_sigma
        self._default_mu: float = model.mu
        self._default_sigma: float = model.sigma
        self._use_cython: bool = (
            _HAS_CYTHON if use_cython is None else (use_cython and _HAS_CYTHON)
        )

    # ------------------------------------------------------------------
    # Dict-like access
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return self._size

    def __contains__(self, entity_id: str) -> bool:
        return entity_id in self._entity_to_idx

    def __getitem__(self, entity_id: str) -> RatingView:
        if entity_id not in self._entity_to_idx:
            self._register(entity_id)
        return self._views[entity_id]

    def __iter__(self) -> Iterator[str]:
        return iter(self._entity_to_idx)

    def keys(self) -> KeysView[str]:
        return self._entity_to_idx.keys()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def _register(
        self,
        entity_id: str,
        mu: float | None = None,
        sigma: float | None = None,
    ) -> RatingView:
        idx = self._size
        if idx >= self._max:
            raise OverflowError(
                f"Ladder full: {self._max} entities.  " f"Increase max_entities."
            )
        self._entity_to_idx[entity_id] = idx
        self._mus[idx] = mu if mu is not None else self._default_mu
        self._sigmas[idx] = sigma if sigma is not None else self._default_sigma
        view = RatingView(self._mus, self._sigmas, idx, entity_id)
        self._views[entity_id] = view
        self._size += 1
        return view

    def add(
        self,
        entity_id: str,
        mu: float | None = None,
        sigma: float | None = None,
    ) -> RatingView:
        """Register an entity (or update its ratings if it already exists).

        :param entity_id: Unique identifier string.
        :param mu: Initial mu (default: model default).
        :param sigma: Initial sigma (default: model default).
        :return: The :class:`RatingView` for this entity.
        """
        if entity_id in self._entity_to_idx:
            idx = self._entity_to_idx[entity_id]
            if mu is not None:
                self._mus[idx] = mu
            if sigma is not None:
                self._sigmas[idx] = sigma
            return self._views[entity_id]
        return self._register(entity_id, mu, sigma)

    # ------------------------------------------------------------------
    # Single-game rating (the hot path)
    # ------------------------------------------------------------------

    def rate(
        self,
        teams: list[list[str]],
        ranks: list[float] | None = None,
        scores: list[float] | None = None,
        weights: list[list[float]] | None = None,
    ) -> None:
        """Rate a single game, updating ratings **in-place**.

        No copies are made.  Temporary Rating objects are created
        only for the ``_compute()`` call, then discarded.

        :param teams: List of teams, each a list of entity ID strings.
        :param ranks: Optional ranks (lower = better).
        :param scores: Optional scores (higher = better).
        :param weights: Optional per-player weights.
        """
        # Auto-register unknown entities.
        for team_ids in teams:
            for eid in team_ids:
                if eid not in self._entity_to_idx:
                    self._register(eid)

        if self._use_cython:
            _cy_rate_game(
                self._model,
                teams,
                self._entity_to_idx,
                self._mus,
                self._sigmas,
                self._tau_sq,
                self._limit_sigma,
                ranks,
                scores,
                weights,
            )
        else:
            self._rate_py(teams, ranks, scores, weights)

    def _rate_py(
        self,
        teams: list[list[str]],
        ranks: list[float] | None,
        scores: list[float] | None,
        weights: list[list[float]] | None,
    ) -> None:
        """Pure-Python hot path."""
        model = self._model
        tau_sq = self._tau_sq
        mus = self._mus
        sigmas = self._sigmas
        entity_to_idx = self._entity_to_idx
        limit_sigma = self._limit_sigma

        # Build disposable Rating objects with tau pre-applied.
        team_objs: list[list[Any]] = []
        team_indices: list[list[int]] = []
        for team_ids in teams:
            team: list[Any] = []
            indices: list[int] = []
            for eid in team_ids:
                idx: int = entity_to_idx[eid]
                s: float = sigmas[idx]
                team.append(_FastRating(mus[idx], math.sqrt(s * s + tau_sq)))
                indices.append(idx)
            team_objs.append(team)
            team_indices.append(indices)

        # Score → rank conversion (matches rate() logic).
        if not ranks and scores:
            ranks = list(map(lambda sc: -sc, scores))
            ranks = model._calculate_rankings(team_objs, ranks)

        # Sort by rank (PlackettLuce requires rank-ordered input).
        if ranks is not None:
            _ranks = ranks  # local binding for lambda closure
            order: list[int] = sorted(range(len(_ranks)), key=lambda i: _ranks[i])
            team_objs = [team_objs[i] for i in order]
            team_indices = [team_indices[i] for i in order]
            ranks = sorted(ranks)
            if scores is not None:
                scores = [scores[i] for i in order]
            if weights is not None:
                weights = [weights[i] for i in order]

        result = model._compute(
            teams=team_objs,
            ranks=ranks,
            scores=scores,
            weights=weights,
        )

        # Write back — direct array mutation, no dict write-back.
        for team_idx, team_result in enumerate(result):
            for player_idx, player in enumerate(team_result):
                idx = team_indices[team_idx][player_idx]
                new_sigma: float = player.sigma
                if limit_sigma:
                    new_sigma = min(new_sigma, sigmas[idx])
                mus[idx] = player.mu
                sigmas[idx] = new_sigma

    # ------------------------------------------------------------------
    # Batch processing
    # ------------------------------------------------------------------

    def rate_batch(
        self,
        games: list[Game],
        n_workers: int = 1,
    ) -> None:
        """Process many games with wave-based ordering.

        Games are partitioned into conflict-free waves that respect
        chronological ordering, then each wave is processed
        sequentially.  Ratings are updated in-place.

        :param games: Games in chronological order.
        :param n_workers: Currently only 1 is supported (sequential).
            Parallel wave processing may be added in the future.
        """
        # Pre-register all entities so _rate_py doesn't need to
        # check on every call.
        for game in games:
            for team in game.teams:
                for eid in team:
                    if eid not in self._entity_to_idx:
                        self._register(eid)

        # Process wave-by-wave to maintain ordering invariants.
        waves = partition_waves(games)
        for wave in waves:
            for _, game in wave:
                self.rate(
                    game.teams,
                    ranks=game.ranks,
                    scores=game.scores,
                    weights=game.weights,
                )

    # ------------------------------------------------------------------
    # Export / introspection
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, tuple[float, float]]:
        """Export all ratings as ``{entity_id: (mu, sigma)}``."""
        return {
            eid: (self._mus[idx], self._sigmas[idx])
            for eid, idx in self._entity_to_idx.items()
        }

    @property
    def model(self) -> Any:
        return self._model
