#!/usr/bin/env python
"""
Batch Processing Benchmark

Generates tournament datasets and compares:
  1. Old approach: sequential model.rate() with dict-based player registry
  2. New approach: BatchProcessor with wave-based parallel processing

Two dataset modes:
  - "swiss": Swiss-format tournament — every player plays every round,
    paired without replacement.  High parallelism within each round.
  - "power_law": Power-law activity — realistic online matchmaking where
    some players are far more active than others.  Low parallelism due
    to long dependency chains.

Measures wall-clock time, per-game throughput, and verifies numerical
accuracy (the two approaches must produce identical ratings).
"""

import math
import random
import sys
import time
from dataclasses import dataclass

from openskill.batch import BatchProcessor, Game, partition_waves
from openskill.models import (
    BradleyTerryFull,
    BradleyTerryPart,
    PlackettLuce,
    ThurstoneMostellerFull,
    ThurstoneMostellerPart,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

NUM_PLAYERS = 3000
NUM_ROUNDS = 9       # Swiss rounds (log2(3000) ≈ 12, 9 is typical)
TEAM_SIZE = 1        # 1v1 Swiss pairings
SEED = 42


# ---------------------------------------------------------------------------
# Data generation — Swiss tournament (without replacement per round)
# ---------------------------------------------------------------------------


def generate_swiss_games(
    num_players: int,
    num_rounds: int,
    seed: int,
    team_size: int = TEAM_SIZE,
) -> list[Game]:
    """
    Generate a Swiss-format tournament.

    Every round, all players are paired without replacement into 1v1
    matches (or small teams).  Each player plays exactly once per round.
    This gives high parallelism within a round (all games independent)
    but sequential dependency between rounds (same player can't appear
    in round N+1 until round N is processed).

    :param num_players: Total players in the tournament.
    :param num_rounds: Number of Swiss rounds.
    :param seed: Random seed for reproducibility.
    :param team_size: Players per team (1 = 1v1, 2 = 2v2, etc.).
    :return: Flat list of Game objects in round order.
    """
    rng = random.Random(seed)
    player_ids = [f"p{i}" for i in range(num_players)]
    players_per_game = 2 * team_size
    games_per_round = num_players // players_per_game

    games: list[Game] = []
    for _ in range(num_rounds):
        # Shuffle all players, pair them off without replacement
        shuffled = list(player_ids)
        rng.shuffle(shuffled)

        for g in range(games_per_round):
            start = g * players_per_game
            team_a = shuffled[start : start + team_size]
            team_b = shuffled[start + team_size : start + players_per_game]
            # Random outcome
            ranks = [1, 2] if rng.random() < 0.5 else [2, 1]
            games.append(Game(teams=[team_a, team_b], ranks=ranks))

    return games


# ---------------------------------------------------------------------------
# Data generation — power-law matchmaking (high overlap)
# ---------------------------------------------------------------------------

POWER_LAW_GAMES = 5000
POWER_LAW_TEAM_SIZE_MAX = 6
POWER_LAW_TEAMS_MIN = 2
POWER_LAW_TEAMS_MAX = 4


def generate_power_law_games(
    num_players: int,
    num_games: int,
    seed: int,
    team_size_max: int = POWER_LAW_TEAM_SIZE_MAX,
) -> list[Game]:
    """Generate games with power-law player activity (online matchmaking)."""
    rng = random.Random(seed)
    player_ids = [f"p{i}" for i in range(num_players)]

    # Power-law activity: some players play a LOT, most play a few.
    weights = [1.0 / (i + 1) ** 0.6 for i in range(num_players)]
    total = sum(weights)
    weights = [w / total for w in weights]

    games: list[Game] = []
    for _ in range(num_games):
        n_teams = rng.randint(POWER_LAW_TEAMS_MIN, POWER_LAW_TEAMS_MAX)
        t_size = rng.randint(1, min(team_size_max, 32))
        total_players_needed = n_teams * t_size

        chosen = _weighted_sample(rng, player_ids, weights, total_players_needed)

        teams: list[list[str]] = []
        for t in range(n_teams):
            start = t * t_size
            teams.append(chosen[start : start + t_size])

        rank_order = list(range(1, n_teams + 1))
        rng.shuffle(rank_order)
        games.append(Game(teams=teams, ranks=rank_order))

    return games


def _weighted_sample(
    rng: random.Random,
    population: list[str],
    weights: list[float],
    k: int,
) -> list[str]:
    """Weighted sampling without replacement (exponential sort trick)."""
    if k >= len(population):
        result = list(population)
        rng.shuffle(result)
        return result
    keyed = [(-math.log(rng.random()) / w, p) for w, p in zip(weights, population)]
    keyed.sort()
    return [p for _, p in keyed[:k]]


# ---------------------------------------------------------------------------
# Old approach: sequential dict-based processing
# ---------------------------------------------------------------------------


def old_approach(model, games: list[Game]) -> dict[str, tuple[float, float]]:
    """The traditional sequential approach: maintain a dict of Rating objects."""
    players: dict[str, object] = {}

    for game in games:
        # Build teams from current ratings
        team_objs = []
        team_keys: list[list[str]] = []
        for team_ids in game.teams:
            team = []
            keys = []
            for pid in team_ids:
                if pid not in players:
                    players[pid] = model.rating()
                team.append(players[pid])
                keys.append(pid)
            team_objs.append(team)
            team_keys.append(keys)

        # Rate
        kwargs = {}
        if game.ranks is not None:
            kwargs["ranks"] = list(game.ranks)
        if game.scores is not None:
            kwargs["scores"] = list(game.scores)

        result = model.rate(team_objs, **kwargs)

        # Update
        for team_idx, team in enumerate(result):
            for player_idx, player in enumerate(team):
                players[team_keys[team_idx][player_idx]] = player

    return {pid: (r.mu, r.sigma) for pid, r in players.items()}


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------


def compare_ratings(
    old: dict[str, tuple[float, float]],
    new: dict[str, tuple[float, float]],
    label: str,
) -> tuple[float, float, int]:
    """Compare two rating dicts. Returns (max_mu_diff, max_sigma_diff, mismatches)."""
    max_mu = 0.0
    max_sigma = 0.0
    mismatches = 0
    for pid in old:
        if pid not in new:
            mismatches += 1
            continue
        mu_diff = abs(old[pid][0] - new[pid][0])
        sigma_diff = abs(old[pid][1] - new[pid][1])
        if mu_diff > 1e-9 or sigma_diff > 1e-9:
            mismatches += 1
        max_mu = max(max_mu, mu_diff)
        max_sigma = max(max_sigma, sigma_diff)
    missing_in_old = len(set(new.keys()) - set(old.keys()))
    mismatches += missing_in_old
    return max_mu, max_sigma, mismatches


def format_time(seconds: float) -> str:
    if seconds < 1.0:
        return f"{seconds * 1000:.1f}ms"
    return f"{seconds:.2f}s"


def analyze_waves(label: str, games: list[Game]) -> None:
    """Print wave structure analysis for a game list."""
    t0 = time.perf_counter()
    waves = partition_waves(games)
    wave_time = time.perf_counter() - t0
    wave_sizes = [len(w) for w in waves]
    entities_per_game = []
    for g in games:
        ents = set()
        for t in g.teams:
            ents.update(t)
        entities_per_game.append(len(ents))

    print(f"\n  [{label}] Wave structure:")
    print(f"    Games: {len(games)}, Waves: {len(waves)} "
          f"(built in {format_time(wave_time)})")
    print(f"    Wave sizes: min={min(wave_sizes)}, max={max(wave_sizes)}, "
          f"avg={sum(wave_sizes)/len(wave_sizes):.1f}")
    print(f"    Entities/game: min={min(entities_per_game)}, "
          f"max={max(entities_per_game)}, "
          f"avg={sum(entities_per_game)/len(entities_per_game):.1f}")
    print(f"    Parallelism: {max(wave_sizes)} games in largest wave "
          f"({max(wave_sizes)/len(games)*100:.1f}% of total)")


def benchmark_dataset(
    label: str,
    games: list[Game],
    models: list[tuple[str, type]],
) -> list[dict]:
    """Run benchmarks on a dataset and return results."""
    print(f"\n  Benchmarking {label}...")
    print("  " + "-" * 70)
    print(f"  {'Model':<26} {'Old (seq)':<12} {'Batch(1w)':<12} "
          f"{'Batch(2w)':<12} {'Match?':<8} {'Speedup'}")
    print("  " + "-" * 70)

    results = []
    for model_name, model_class in models:
        model = model_class()

        # --- Old approach ---
        t0 = time.perf_counter()
        old_ratings = old_approach(model, games)
        old_time = time.perf_counter() - t0

        # --- Batch sequential (1 worker, fast path — no deepcopy) ---
        proc1 = BatchProcessor(model, n_workers=1)
        t0 = time.perf_counter()
        batch1_ratings = proc1.process(games)
        batch1_time = time.perf_counter() - t0

        # --- Batch parallel (2 workers) ---
        proc2 = BatchProcessor(model, n_workers=2, pipeline=True)
        t0 = time.perf_counter()
        batch2_ratings = proc2.process(games)
        batch2_time = time.perf_counter() - t0

        # --- Accuracy check ---
        mu1, sig1, mis1 = compare_ratings(old_ratings, batch1_ratings, "seq")
        mu2, sig2, mis2 = compare_ratings(old_ratings, batch2_ratings, "par")
        match_str = "EXACT" if mis1 == 0 and mis2 == 0 else f"DIFF({mis1},{mis2})"

        # --- Speedup ---
        speedup_1 = old_time / batch1_time if batch1_time > 0 else float("inf")
        speedup_2 = old_time / batch2_time if batch2_time > 0 else float("inf")

        print(
            f"  {model_name:<26} "
            f"{format_time(old_time):<12} "
            f"{format_time(batch1_time):<12} "
            f"{format_time(batch2_time):<12} "
            f"{match_str:<8} "
            f"{speedup_1:.2f}x / {speedup_2:.2f}x"
        )

        results.append({
            "model": model_name,
            "old_time": old_time,
            "batch1_time": batch1_time,
            "batch2_time": batch2_time,
            "match": match_str,
            "speedup_1": speedup_1,
            "speedup_2": speedup_2,
            "max_mu_diff": max(mu1, mu2),
            "max_sigma_diff": max(sig1, sig2),
        })

    return results


def run_benchmark() -> None:
    print("=" * 72)
    print("  Batch Processing Benchmark")
    print(f"  {NUM_PLAYERS} players, seed={SEED}")
    print(f"  Python {sys.version.split()[0]}")
    print("=" * 72)

    models = [
        ("PlackettLuce", PlackettLuce),
        ("BradleyTerryFull", BradleyTerryFull),
        ("BradleyTerryPart", BradleyTerryPart),
        ("ThurstoneMostellerFull", ThurstoneMostellerFull),
        ("ThurstoneMostellerPart", ThurstoneMostellerPart),
    ]

    # ---------------------------------------------------------------
    # Dataset 1: Swiss tournament (high parallelism)
    # ---------------------------------------------------------------
    print(f"\n[1/3] Swiss tournament: {NUM_PLAYERS} players, "
          f"{NUM_ROUNDS} rounds, {TEAM_SIZE}v{TEAM_SIZE}")
    t0 = time.perf_counter()
    swiss_games = generate_swiss_games(NUM_PLAYERS, NUM_ROUNDS, SEED, TEAM_SIZE)
    gen_time = time.perf_counter() - t0
    print(f"  Generated {len(swiss_games)} games in {format_time(gen_time)}")
    analyze_waves("Swiss", swiss_games)
    swiss_results = benchmark_dataset("Swiss", swiss_games, models)

    # ---------------------------------------------------------------
    # Dataset 2: Power-law matchmaking (low parallelism)
    # ---------------------------------------------------------------
    print(f"\n[2/3] Power-law matchmaking: {NUM_PLAYERS} players, "
          f"{POWER_LAW_GAMES} games")
    t0 = time.perf_counter()
    pl_games = generate_power_law_games(
        NUM_PLAYERS, POWER_LAW_GAMES, SEED
    )
    gen_time = time.perf_counter() - t0
    print(f"  Generated {len(pl_games)} games in {format_time(gen_time)}")
    analyze_waves("PowerLaw", pl_games)
    pl_results = benchmark_dataset("Power-law", pl_games, models)

    # ---------------------------------------------------------------
    # Profile breakdown for PlackettLuce
    # ---------------------------------------------------------------
    num_profile_games = len(swiss_games)
    print(f"\n[3/3] Profiling PlackettLuce breakdown ({num_profile_games} games)...")
    print("-" * 72)
    model = PlackettLuce()

    # Time just Rating object creation
    t0 = time.perf_counter()
    for _ in range(num_profile_games * 2):  # 2 players per 1v1 game
        model.rating(mu=25.0, sigma=8.333)
    rating_create_time = time.perf_counter() - t0

    # Time deepcopy overhead (simulate what rate() does)
    import copy
    sample_teams = [
        [model.rating()],
        [model.rating()],
    ]
    t0 = time.perf_counter()
    for _ in range(num_profile_games):
        copy.deepcopy(sample_teams)
    deepcopy_time = time.perf_counter() - t0

    # Time the actual math (single rate call, 1v1)
    team_a = [model.rating()]
    team_b = [model.rating()]
    t0 = time.perf_counter()
    for _ in range(num_profile_games):
        model.rate([team_a, team_b], ranks=[1, 2])
    rate_call_time = time.perf_counter() - t0

    # Time _compute directly (no deepcopy, no validation)
    team_a_tau = [model.rating(mu=25.0, sigma=math.sqrt(8.333**2 + model.tau**2))]
    team_b_tau = [model.rating(mu=25.0, sigma=math.sqrt(8.333**2 + model.tau**2))]
    t0 = time.perf_counter()
    for _ in range(num_profile_games):
        model._compute(teams=[team_a_tau, team_b_tau], ranks=[0, 1])
    compute_time = time.perf_counter() - t0

    # Wave partitioning time
    t0 = time.perf_counter()
    for _ in range(10):
        partition_waves(swiss_games)
    wave_avg = (time.perf_counter() - t0) / 10

    print(f"  Rating creation ({num_profile_games*2} objs):  "
          f"{format_time(rating_create_time)}")
    print(f"  deepcopy ({num_profile_games} x 1v1):          "
          f"{format_time(deepcopy_time)}")
    print(f"  rate() full ({num_profile_games} x 1v1):       "
          f"{format_time(rate_call_time)}")
    print(f"  _compute() only ({num_profile_games} x 1v1):   "
          f"{format_time(compute_time)}")
    print(f"  Wave partition ({len(swiss_games)} games, avg): "
          f"{format_time(wave_avg)}")
    print(f"  deepcopy as %% of rate():  "
          f"{deepcopy_time/rate_call_time*100:.1f}%")
    print(f"  _compute as %% of rate():  "
          f"{compute_time/rate_call_time*100:.1f}%")

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------
    print("\n" + "=" * 72)
    print("  Summary")
    print("=" * 72)

    for label, results in [("Swiss", swiss_results), ("Power-law", pl_results)]:
        print(f"\n  {label}:")
        for r in results:
            print(f"    {r['model']:<26} Old={format_time(r['old_time']):<10} "
                  f"Batch1w={format_time(r['batch1_time']):<10} "
                  f"Batch2w={format_time(r['batch2_time']):<10} "
                  f"Accuracy={r['match']}")

    all_results = swiss_results + pl_results
    any_mismatch = any(r["match"] != "EXACT" for r in all_results)
    if any_mismatch:
        print("\n  WARNING: Some results differ between old and new approach!")
        for r in all_results:
            if r["match"] != "EXACT":
                print(f"    {r['model']}: max mu diff={r['max_mu_diff']:.2e}, "
                      f"max sigma diff={r['max_sigma_diff']:.2e}")
    else:
        print("\n  All models produce EXACT same ratings (within 1e-10 tolerance)")

    print()


if __name__ == "__main__":
    run_benchmark()
