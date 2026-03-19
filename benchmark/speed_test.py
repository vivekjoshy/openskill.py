#!/usr/bin/env python
"""
Speed test: Original vs Ladder vs BatchProcessor on Swiss and power-law datasets.

Usage:
    python benchmark/speed_test.py
    python benchmark/speed_test.py --players 5000 --rounds 12 --power-games 8000
    python benchmark/speed_test.py --repeats 5
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


def generate_swiss(num_players, num_rounds, seed):
    """Generate Swiss-format 1v1 tournament games.

    :param num_players: Total number of players.
    :param num_rounds: Number of Swiss rounds.
    :param seed: Random seed for reproducibility.
    :return: List of games.
    """
    rng = random.Random(seed)
    ids = [f"p{i}" for i in range(num_players)]
    games = []
    for _ in range(num_rounds):
        s = list(ids)
        rng.shuffle(s)
        for g in range(num_players // 2):
            ranks = [1, 2] if rng.random() < 0.5 else [2, 1]
            games.append(Game(teams=[[s[2 * g]], [s[2 * g + 1]]], ranks=ranks))
    return games


def generate_power_law(num_players, num_games, seed):
    """Generate power-law distributed matchmaking games.

    :param num_players: Total number of players.
    :param num_games: Number of games to generate.
    :param seed: Random seed for reproducibility.
    :return: List of games.
    """
    rng = random.Random(seed)
    ids = [f"p{i}" for i in range(num_players)]
    w = [1.0 / (i + 1) ** 0.6 for i in range(num_players)]
    total = sum(w)
    w = [x / total for x in w]

    games = []
    for _ in range(num_games):
        n_teams = rng.randint(2, 4)
        t_size = rng.randint(1, 6)
        needed = n_teams * t_size
        if needed >= num_players:
            chosen = list(ids)
            rng.shuffle(chosen)
        else:
            keyed = [(-math.log(rng.random()) / wi, p) for wi, p in zip(w, ids)]
            keyed.sort()
            chosen = [p for _, p in keyed[:needed]]
        teams = [chosen[t * t_size : (t + 1) * t_size] for t in range(n_teams)]
        ranks = list(range(1, n_teams + 1))
        rng.shuffle(ranks)
        games.append(Game(teams=teams, ranks=ranks))
    return games


# ---------------------------------------------------------------------------
# Approaches
# ---------------------------------------------------------------------------


def original(model, games):
    """Baseline: sequential ``model.rate()`` with dict lookups.

    :param model: An openskill model instance.
    :param games: List of games to process.
    :return: Dict of ``{player_id: (mu, sigma)}``.
    """
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
        kw = {}
        if game.ranks is not None:
            kw["ranks"] = list(game.ranks)
        if game.scores is not None:
            kw["scores"] = list(game.scores)
        result = model.rate(team_objs, **kw)
        for ti, tr in enumerate(result):
            for pi, p in enumerate(tr):
                players[team_keys[ti][pi]] = p
    return {pid: (r.mu, r.sigma) for pid, r in players.items()}


def ladder_py(model, games):
    """Ladder with pure-Python hot path.

    :param model: An openskill model instance.
    :param games: List of games to process.
    :return: Dict of ``{player_id: (mu, sigma)}``.
    """
    lad = Ladder(model, use_cython=False)
    for g in games:
        lad.rate(g.teams, ranks=g.ranks, scores=g.scores)
    return lad.to_dict()


def ladder_cy(model, games):
    """Ladder with optional Cython fast path.

    :param model: An openskill model instance.
    :param games: List of games to process.
    :return: Dict of ``{player_id: (mu, sigma)}``.
    """
    lad = Ladder(model, use_cython=True)
    for g in games:
        lad.rate(g.teams, ranks=g.ranks, scores=g.scores)
    return lad.to_dict()


def ladder_batch(model, games):
    """Ladder with wave-ordered batch processing.

    :param model: An openskill model instance.
    :param games: List of games to process.
    :return: Dict of ``{player_id: (mu, sigma)}``.
    """
    lad = Ladder(model, use_cython=False)
    lad.rate_batch(games)
    return lad.to_dict()


def batch_1w(model, games):
    """BatchProcessor with a single worker.

    :param model: An openskill model instance.
    :param games: List of games to process.
    :return: Dict of ``{player_id: (mu, sigma)}``.
    """
    return BatchProcessor(model, n_workers=1).process(games)


def batch_2w(model, games):
    """BatchProcessor with two workers.

    :param model: An openskill model instance.
    :param games: List of games to process.
    :return: Dict of ``{player_id: (mu, sigma)}``.
    """
    return BatchProcessor(model, n_workers=2).process(games)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def check_exact(baseline, other):
    """Check if two rating dicts match within floating-point tolerance.

    :param baseline: Reference ``{player_id: (mu, sigma)}`` dict.
    :param other: Comparison ``{player_id: (mu, sigma)}`` dict.
    :return: ``True`` if all ratings match within 1e-9.
    """
    for pid in baseline:
        if pid not in other:
            return False
        if abs(baseline[pid][0] - other[pid][0]) > 1e-9:
            return False
        if abs(baseline[pid][1] - other[pid][1]) > 1e-9:
            return False
    return len(baseline) == len(other)


def bench(fn, model, games, repeats):
    """Return (best_time, result_from_last_run)."""
    result = None
    best = float("inf")
    for _ in range(repeats):
        t0 = time.perf_counter()
        result = fn(model, games)
        elapsed = time.perf_counter() - t0
        best = min(best, elapsed)
    return best, result


def fmt(sec):
    """Format seconds as a human-readable time string.

    :param sec: Elapsed time in seconds.
    :return: Formatted string (e.g. ``"123.4 ms"``).
    """
    return f"{sec * 1000:.1f} ms"


def main():
    """Run speed benchmarks and print results table."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--players", type=int, default=3000)
    parser.add_argument("--rounds", type=int, default=9)
    parser.add_argument("--power-games", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--repeats", type=int, default=3, help="Runs per approach; report best time"
    )
    args = parser.parse_args()

    model = PlackettLuce()

    approaches = [
        ("Original", original),
        ("Ladder", ladder_py),
    ]
    if _HAS_CYTHON:
        approaches.append(("Ladder+Cy", ladder_cy))
    approaches += [
        ("LadderBatch", ladder_batch),
        ("Batch(1w)", batch_1w),
        ("Batch(2w)", batch_2w),
    ]

    datasets = [
        (
            "Swiss",
            f"{args.players} players, {args.rounds} rounds, 1v1",
            generate_swiss(args.players, args.rounds, args.seed),
        ),
        (
            "Power-law",
            f"{args.players} players, {args.power_games} games, 2-4 teams",
            generate_power_law(args.players, args.power_games, args.seed),
        ),
    ]

    # Column widths
    name_w = max(len(a[0]) for a in approaches) + 2
    time_w = 12
    speed_w = 10
    match_w = 7

    print()
    print(
        f"  Python {sys.version.split()[0]}  |  Cython: {'yes' if _HAS_CYTHON else 'no'}"
        f"  |  PlackettLuce  |  best of {args.repeats} runs"
    )
    print()

    for ds_name, ds_desc, games in datasets:
        waves = partition_waves(games)
        ws = [len(w) for w in waves]

        print(f"  {ds_name}: {ds_desc} ({len(games)} games)")
        print(f"  waves: {len(waves)}, largest: {max(ws)}, avg: {sum(ws)/len(ws):.1f}")
        print()

        hdr = f"  {'':>{name_w}} {'time':>{time_w}} {'speedup':>{speed_w}} {'exact':>{match_w}}"
        print(hdr)
        print(f"  {'─' * (name_w + time_w + speed_w + match_w + 3)}")

        baseline_time = None
        baseline_ratings = None

        for name, fn in approaches:
            t, ratings = bench(fn, model, games, args.repeats)

            if baseline_time is None:
                baseline_time = t
                baseline_ratings = ratings
                speedup_s = ""
                match_s = ""
            else:
                speedup = baseline_time / t if t > 0 else float("inf")
                speedup_s = f"{speedup:.2f}x"
                match_s = "yes" if check_exact(baseline_ratings, ratings) else "NO"

            print(
                f"  {name:>{name_w}} {fmt(t):>{time_w}} {speedup_s:>{speed_w}} {match_s:>{match_w}}"
            )

        print()


if __name__ == "__main__":
    main()
