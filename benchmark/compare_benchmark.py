#!/usr/bin/env python
"""
Compare optimized approaches (Ladder, BatchProcessor) against the
original model.rate() method on Swiss and power-law datasets.

Usage:
    python benchmark/compare_benchmark.py
    python benchmark/compare_benchmark.py --rounds 5 --players 1000
"""

import argparse
import math
import random
import sys
import time

from openskill.batch import BatchProcessor, Game, partition_waves
from openskill.ladder import _HAS_CYTHON, Ladder
from openskill.models import PlackettLuce

# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------


def generate_swiss_games(num_players, num_rounds, seed):
    """Swiss-format 1v1 tournament: every player once per round."""
    rng = random.Random(seed)
    player_ids = [f"p{i}" for i in range(num_players)]
    games_per_round = num_players // 2

    games = []
    for _ in range(num_rounds):
        shuffled = list(player_ids)
        rng.shuffle(shuffled)
        for g in range(games_per_round):
            a = shuffled[2 * g]
            b = shuffled[2 * g + 1]
            ranks = [1, 2] if rng.random() < 0.5 else [2, 1]
            games.append(Game(teams=[[a], [b]], ranks=ranks))
    return games


def generate_power_law_games(num_players, num_games, seed):
    """Power-law activity: some players play heavily, most play rarely."""
    rng = random.Random(seed)
    player_ids = [f"p{i}" for i in range(num_players)]
    weights = [1.0 / (i + 1) ** 0.6 for i in range(num_players)]
    total = sum(weights)
    weights = [w / total for w in weights]

    games = []
    for _ in range(num_games):
        n_teams = rng.randint(2, 4)
        t_size = rng.randint(1, 6)
        total_needed = n_teams * t_size
        chosen = _weighted_sample(rng, player_ids, weights, total_needed)

        teams = []
        for t in range(n_teams):
            teams.append(chosen[t * t_size : (t + 1) * t_size])

        rank_order = list(range(1, n_teams + 1))
        rng.shuffle(rank_order)
        games.append(Game(teams=teams, ranks=rank_order))
    return games


def _weighted_sample(rng, population, weights, k):
    """Sample *k* items without replacement using exponential sorting.

    :param rng: Random instance.
    :param population: Items to sample from.
    :param weights: Corresponding sampling weights.
    :param k: Number of items to select.
    :return: List of selected items.
    """
    if k >= len(population):
        result = list(population)
        rng.shuffle(result)
        return result
    keyed = [(-math.log(rng.random()) / w, p) for w, p in zip(weights, population)]
    keyed.sort()
    return [p for _, p in keyed[:k]]


# ---------------------------------------------------------------------------
# Execution strategies
# ---------------------------------------------------------------------------


def run_original(model, games):
    """Baseline: sequential model.rate() with dict lookups."""
    players = {}
    for game in games:
        team_objs, team_keys = [], []
        for team_ids in game.teams:
            team, keys = [], []
            for pid in team_ids:
                if pid not in players:
                    players[pid] = model.rating()
                team.append(players[pid])
                keys.append(pid)
            team_objs.append(team)
            team_keys.append(keys)
        kwargs = {}
        if game.ranks is not None:
            kwargs["ranks"] = list(game.ranks)
        if game.scores is not None:
            kwargs["scores"] = list(game.scores)
        result = model.rate(team_objs, **kwargs)
        for ti, team_result in enumerate(result):
            for pi, player in enumerate(team_result):
                players[team_keys[ti][pi]] = player
    return {pid: (r.mu, r.sigma) for pid, r in players.items()}


def run_ladder(model, games, use_cython=False):
    """Ladder: in-place array-backed rating, one game at a time."""
    lad = Ladder(model, use_cython=use_cython)
    for game in games:
        lad.rate(game.teams, ranks=game.ranks, scores=game.scores)
    return lad.to_dict()


def run_ladder_batch(model, games):
    """Ladder with wave-ordered batch processing."""
    lad = Ladder(model, use_cython=False)
    lad.rate_batch(games)
    return lad.to_dict()


def run_batch_processor(model, games, n_workers):
    """BatchProcessor: parallel wave-based processing."""
    proc = BatchProcessor(model, n_workers=n_workers)
    return proc.process(games)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def compare_ratings(baseline, other):
    """Return (max_mu_diff, max_sigma_diff, num_mismatches)."""
    max_mu = max_sigma = 0.0
    mismatches = 0
    for pid in baseline:
        if pid not in other:
            mismatches += 1
            continue
        md = abs(baseline[pid][0] - other[pid][0])
        sd = abs(baseline[pid][1] - other[pid][1])
        if md > 1e-9 or sd > 1e-9:
            mismatches += 1
        max_mu = max(max_mu, md)
        max_sigma = max(max_sigma, sd)
    mismatches += len(set(other) - set(baseline))
    return max_mu, max_sigma, mismatches


def fmt_time(seconds):
    """Format seconds as a human-readable time string.

    :param seconds: Elapsed time in seconds.
    :return: Formatted string (e.g. ``"123ms"`` or ``"1.23s"``).
    """
    if seconds < 1.0:
        return f"{seconds * 1000:.0f}ms"
    return f"{seconds:.2f}s"


def time_it(fn):
    """Run fn, return (elapsed_seconds, result)."""
    t0 = time.perf_counter()
    result = fn()
    return time.perf_counter() - t0, result


# ---------------------------------------------------------------------------
# Main benchmark
# ---------------------------------------------------------------------------


def run_dataset_benchmark(label, games, model):
    """Benchmark all approaches on one dataset, print results table."""
    waves = partition_waves(games)
    wave_sizes = [len(w) for w in waves]
    print(
        f"  Waves: {len(waves)}, max size: {max(wave_sizes)}, "
        f"avg: {sum(wave_sizes) / len(wave_sizes):.1f}"
    )
    print()

    results = {}

    # Original (baseline)
    t, ratings = time_it(lambda: run_original(model, games))
    results["Original"] = (t, ratings)
    baseline = ratings

    # Ladder (pure Python)
    t, ratings = time_it(lambda: run_ladder(model, games, use_cython=False))
    results["Ladder"] = (t, ratings)

    # Ladder + Cython
    if _HAS_CYTHON:
        t, ratings = time_it(lambda: run_ladder(model, games, use_cython=True))
        results["Ladder+Cy"] = (t, ratings)

    # Ladder batch
    t, ratings = time_it(lambda: run_ladder_batch(model, games))
    results["LadderBatch"] = (t, ratings)

    # BatchProcessor 1 worker
    t, ratings = time_it(lambda: run_batch_processor(model, games, n_workers=1))
    results["Batch(1w)"] = (t, ratings)

    # BatchProcessor 2 workers
    t, ratings = time_it(lambda: run_batch_processor(model, games, n_workers=2))
    results["Batch(2w)"] = (t, ratings)

    # Print table
    old_time = results["Original"][0]
    col_w = 12
    header = (
        f"  {'Approach':<16} {'Time':>{col_w}} {'Speedup':>{col_w}} {'Match':>{col_w}}"
    )
    print(header)
    print("  " + "-" * (len(header) - 2))

    for name, (t, ratings) in results.items():
        if name == "Original":
            speedup_str = "(baseline)"
            match_str = "-"
        else:
            speedup = old_time / t if t > 0 else float("inf")
            speedup_str = f"{speedup:.2f}x"
            _, _, mis = compare_ratings(baseline, ratings)
            match_str = "EXACT" if mis == 0 else f"{mis} DIFF"

        print(
            f"  {name:<16} {fmt_time(t):>{col_w}} {speedup_str:>{col_w}} {match_str:>{col_w}}"
        )

    print()
    return results


def main():
    """Run comparison benchmarks and print results tables."""
    parser = argparse.ArgumentParser(description="Benchmark openskill approaches")
    parser.add_argument("--players", type=int, default=3000, help="Number of players")
    parser.add_argument("--rounds", type=int, default=9, help="Swiss rounds")
    parser.add_argument("--power-games", type=int, default=5000, help="Power-law games")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print("=" * 70)
    print("  openskill Benchmark — Original vs Optimized")
    print(f"  Python {sys.version.split()[0]}")
    print(f"  Cython: {'YES' if _HAS_CYTHON else 'NO'}")
    print(f"  Model: PlackettLuce (default params)")
    print("=" * 70)

    model = PlackettLuce()

    # --- Swiss dataset ---
    swiss = generate_swiss_games(args.players, args.rounds, args.seed)
    n_swiss = len(swiss)
    print(
        f"\n  SWISS — {args.players} players, {args.rounds} rounds, "
        f"1v1, {n_swiss} games"
    )
    print(f"  {'-' * 66}")
    run_dataset_benchmark("Swiss", swiss, model)

    # --- Power-law dataset ---
    power = generate_power_law_games(args.players, args.power_games, args.seed)
    print(
        f"  POWER-LAW — {args.players} players, {args.power_games} games, "
        f"2-4 teams, 1-6 per team"
    )
    print(f"  {'-' * 66}")
    run_dataset_benchmark("PowerLaw", power, model)


if __name__ == "__main__":
    main()
