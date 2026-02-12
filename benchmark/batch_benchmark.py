#!/usr/bin/env python
"""
Batch Processing Benchmark — Shootout

Compares ALL execution models head-to-head:

  1. **Old**       — sequential model.rate() with dict (baseline)
  2. **Batch(1w)** — BatchProcessor, 1 worker, fast path (no deepcopy)
  3. **Batch(2w)** — BatchProcessor, 2 workers, multiprocess pipeline
  4. **Ladder**    — Ladder.rate() per game, array-backed, pure Python
  5. **Ladder+Cy** — Ladder.rate() per game, Cython fast path
  6. **LadBatch**  — Ladder.rate_batch(), wave-ordered sequential

Two datasets:
  - Swiss tournament (high parallelism, 1v1, no replacement)
  - Power-law matchmaking (low parallelism, variable team size)

Every approach is accuracy-verified against the Old baseline.
"""

import math
import random
import sys
import time

from openskill.batch import BatchProcessor, Game, partition_waves
from openskill.ladder import Ladder, _HAS_CYTHON
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
NUM_ROUNDS = 9
TEAM_SIZE = 1
SEED = 42

POWER_LAW_GAMES = 5000
POWER_LAW_TEAM_SIZE_MAX = 6
POWER_LAW_TEAMS_MIN = 2
POWER_LAW_TEAMS_MAX = 4


# ---------------------------------------------------------------------------
# Data generation
# ---------------------------------------------------------------------------

def generate_swiss_games(
    num_players: int, num_rounds: int, seed: int, team_size: int = TEAM_SIZE,
) -> list[Game]:
    """Swiss-format tournament: every player once per round, no replacement."""
    rng = random.Random(seed)
    player_ids = [f"p{i}" for i in range(num_players)]
    players_per_game = 2 * team_size
    games_per_round = num_players // players_per_game

    games: list[Game] = []
    for _ in range(num_rounds):
        shuffled = list(player_ids)
        rng.shuffle(shuffled)
        for g in range(games_per_round):
            start = g * players_per_game
            team_a = shuffled[start : start + team_size]
            team_b = shuffled[start + team_size : start + players_per_game]
            ranks = [1, 2] if rng.random() < 0.5 else [2, 1]
            games.append(Game(teams=[team_a, team_b], ranks=ranks))
    return games


def generate_power_law_games(
    num_players: int, num_games: int, seed: int,
    team_size_max: int = POWER_LAW_TEAM_SIZE_MAX,
) -> list[Game]:
    """Power-law activity: some players play a LOT, most play a few."""
    rng = random.Random(seed)
    player_ids = [f"p{i}" for i in range(num_players)]
    weights = [1.0 / (i + 1) ** 0.6 for i in range(num_players)]
    total = sum(weights)
    weights = [w / total for w in weights]

    games: list[Game] = []
    for _ in range(num_games):
        n_teams = rng.randint(POWER_LAW_TEAMS_MIN, POWER_LAW_TEAMS_MAX)
        t_size = rng.randint(1, min(team_size_max, 32))
        total_needed = n_teams * t_size
        chosen = _weighted_sample(rng, player_ids, weights, total_needed)

        teams: list[list[str]] = []
        for t in range(n_teams):
            start = t * t_size
            teams.append(chosen[start : start + t_size])

        rank_order = list(range(1, n_teams + 1))
        rng.shuffle(rank_order)
        games.append(Game(teams=teams, ranks=rank_order))
    return games


def _weighted_sample(rng, population, weights, k):
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

def run_old(model, games):
    """Baseline: model.rate() with dict."""
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
        for ti, team in enumerate(result):
            for pi, player in enumerate(team):
                players[team_keys[ti][pi]] = player
    return {pid: (r.mu, r.sigma) for pid, r in players.items()}


def run_batch(model, games, n_workers=1, pipeline=True):
    proc = BatchProcessor(model, n_workers=n_workers, pipeline=pipeline)
    return proc.process(games)


def run_ladder(model, games, use_cython=False):
    lad = Ladder(model, use_cython=use_cython)
    for game in games:
        lad.rate(game.teams, ranks=game.ranks, scores=game.scores)
    return lad.to_dict()


def run_ladder_batch(model, games):
    lad = Ladder(model, use_cython=False)
    lad.rate_batch(games)
    return lad.to_dict()


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------

def compare_ratings(old, new):
    max_mu = max_sigma = 0.0
    mismatches = 0
    for pid in old:
        if pid not in new:
            mismatches += 1
            continue
        md = abs(old[pid][0] - new[pid][0])
        sd = abs(old[pid][1] - new[pid][1])
        if md > 1e-9 or sd > 1e-9:
            mismatches += 1
        max_mu = max(max_mu, md)
        max_sigma = max(max_sigma, sd)
    mismatches += len(set(new) - set(old))
    return max_mu, max_sigma, mismatches


def fmt(seconds):
    return f"{seconds * 1000:.0f}ms" if seconds < 1.0 else f"{seconds:.2f}s"


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

def benchmark_dataset(label, games, model_name, model):
    """Run all approaches for one model+dataset, return result row."""
    approaches = {}

    # 1. Old
    t0 = time.perf_counter()
    old_ratings = run_old(model, games)
    approaches["Old"] = (time.perf_counter() - t0, old_ratings)

    # 2. Batch(1w)
    t0 = time.perf_counter()
    approaches["Batch1w"] = (
        time.perf_counter() - t0,
        None,  # placeholder
    )
    r = run_batch(model, games, n_workers=1)
    approaches["Batch1w"] = (time.perf_counter() - t0, r)

    # 3. Batch(2w)
    t0 = time.perf_counter()
    r = run_batch(model, games, n_workers=2, pipeline=True)
    approaches["Batch2w"] = (time.perf_counter() - t0, r)

    # 4. Ladder (Python)
    t0 = time.perf_counter()
    r = run_ladder(model, games, use_cython=False)
    approaches["Ladder"] = (time.perf_counter() - t0, r)

    # 5. Ladder (Cython) — if available
    if _HAS_CYTHON:
        t0 = time.perf_counter()
        r = run_ladder(model, games, use_cython=True)
        approaches["LadCy"] = (time.perf_counter() - t0, r)

    # 6. Ladder batch
    t0 = time.perf_counter()
    r = run_ladder_batch(model, games)
    approaches["LadBatch"] = (time.perf_counter() - t0, r)

    # Accuracy vs Old baseline
    old_time = approaches["Old"][0]
    mismatches = []
    for name, (t, ratings) in approaches.items():
        if name == "Old":
            continue
        _, _, mis = compare_ratings(old_ratings, ratings)
        mismatches.append(mis)

    all_exact = all(m == 0 for m in mismatches)
    match_str = "EXACT" if all_exact else f"DIFF"

    return {
        "model": model_name,
        "label": label,
        "approaches": {k: v[0] for k, v in approaches.items()},
        "match": match_str,
        "old_time": old_time,
    }


def run_benchmark():
    print("=" * 80)
    print("  Batch Processing Benchmark — SHOOTOUT")
    print(f"  {NUM_PLAYERS} players, seed={SEED}, Python {sys.version.split()[0]}")
    print(f"  Cython: {'YES' if _HAS_CYTHON else 'NO (pip install cython && python build_cfast.py)'}")
    print("=" * 80)

    models = [
        ("PlackettLuce", PlackettLuce),
        ("BradleyTerryFull", BradleyTerryFull),
        ("BradleyTerryPart", BradleyTerryPart),
        ("ThurstoneMostellerFull", ThurstoneMostellerFull),
        ("ThurstoneMostellerPart", ThurstoneMostellerPart),
    ]

    # Build the approach column headers
    cols = ["Old", "Batch1w", "Batch2w", "Ladder"]
    if _HAS_CYTHON:
        cols.append("LadCy")
    cols.append("LadBatch")

    all_results = []

    for ds_label, games, ds_desc in [
        ("Swiss", generate_swiss_games(NUM_PLAYERS, NUM_ROUNDS, SEED, TEAM_SIZE),
         f"{NUM_PLAYERS} players, {NUM_ROUNDS} rounds, {TEAM_SIZE}v{TEAM_SIZE}"),
        ("PowerLaw", generate_power_law_games(NUM_PLAYERS, POWER_LAW_GAMES, SEED),
         f"{NUM_PLAYERS} players, {POWER_LAW_GAMES} games, mixed teams"),
    ]:
        print(f"\n{'─' * 80}")
        print(f"  Dataset: {ds_label} — {ds_desc} ({len(games)} games)")
        print(f"{'─' * 80}")

        # Wave analysis
        waves = partition_waves(games)
        wsizes = [len(w) for w in waves]
        print(f"  Waves: {len(waves)}, max wave: {max(wsizes)}, "
              f"avg: {sum(wsizes)/len(wsizes):.1f}")

        # Header
        col_w = 10
        hdr = f"  {'Model':<22}"
        for c in cols:
            hdr += f" {c:>{col_w}}"
        hdr += "  Match?  Best speedup"
        print(hdr)
        print("  " + "-" * (len(hdr) - 2))

        for model_name, model_class in models:
            model = model_class()
            row = benchmark_dataset(ds_label, games, model_name, model)
            all_results.append(row)

            old_t = row["approaches"]["Old"]
            line = f"  {model_name:<22}"
            best_name = "Old"
            best_time = old_t
            for c in cols:
                t = row["approaches"].get(c, 0)
                line += f" {fmt(t):>{col_w}}"
                if c != "Old" and t < best_time:
                    best_time = t
                    best_name = c
            speedup = old_t / best_time if best_time > 0 else float("inf")
            line += f"  {row['match']:<7} {best_name} {speedup:.2f}x"
            print(line)

    # ──────────────────────────────────────────────────────────────
    # Profile breakdown
    # ──────────────────────────────────────────────────────────────
    print(f"\n{'─' * 80}")
    print("  Profile breakdown: PlackettLuce 1v1 (13500 iterations)")
    print(f"{'─' * 80}")
    import copy
    model = PlackettLuce()
    N = 13500

    team_a = [model.rating()]
    team_b = [model.rating()]
    t0 = time.perf_counter()
    for _ in range(N):
        model.rate([team_a, team_b], ranks=[1, 2])
    rate_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    for _ in range(N):
        copy.deepcopy([team_a, team_b])
    dc_time = time.perf_counter() - t0

    tau_sig = math.sqrt(model.sigma ** 2 + model.tau ** 2)
    ta = [model.rating(mu=model.mu, sigma=tau_sig)]
    tb = [model.rating(mu=model.mu, sigma=tau_sig)]
    t0 = time.perf_counter()
    for _ in range(N):
        model._compute(teams=[ta, tb], ranks=[0, 1])
    compute_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    for _ in range(N * 2):
        model.rating(mu=25.0, sigma=8.333)
    rating_time = time.perf_counter() - t0

    lad = Ladder(model, use_cython=False)
    lad.add("a"); lad.add("b")
    t0 = time.perf_counter()
    for _ in range(N):
        lad.rate([["a"], ["b"]], ranks=[1, 2])
    ladder_time = time.perf_counter() - t0

    if _HAS_CYTHON:
        lad_cy = Ladder(model, use_cython=True)
        lad_cy.add("a"); lad_cy.add("b")
        t0 = time.perf_counter()
        for _ in range(N):
            lad_cy.rate([["a"], ["b"]], ranks=[1, 2])
        ladder_cy_time = time.perf_counter() - t0

    print(f"  model.rate()     {fmt(rate_time):>10}  (baseline = deepcopy + validate + compute)")
    print(f"  copy.deepcopy()  {fmt(dc_time):>10}  ({dc_time/rate_time*100:.0f}% of rate)")
    print(f"  model._compute() {fmt(compute_time):>10}  ({compute_time/rate_time*100:.0f}% of rate) — pure math")
    print(f"  model.rating()   {fmt(rating_time):>10}  ({N*2} objects)")
    print(f"  Ladder.rate()    {fmt(ladder_time):>10}  ({ladder_time/rate_time:.2f}x vs rate)")
    if _HAS_CYTHON:
        print(f"  Ladder+Cy.rate() {fmt(ladder_cy_time):>10}  ({ladder_cy_time/rate_time:.2f}x vs rate)")

    # ──────────────────────────────────────────────────────────────
    # Summary & recommendation
    # ──────────────────────────────────────────────────────────────
    print(f"\n{'=' * 80}")
    print("  RESULTS SUMMARY")
    print(f"{'=' * 80}")

    any_mismatch = any(r["match"] != "EXACT" for r in all_results)
    if any_mismatch:
        print("\n  WARNING: Some approaches differ from baseline!")
    else:
        print("\n  Accuracy: ALL approaches EXACT vs baseline (within 1e-9)\n")

    # Find overall winners
    for ds in ["Swiss", "PowerLaw"]:
        ds_rows = [r for r in all_results if r["label"] == ds]
        print(f"  {ds}:")
        for r in ds_rows:
            old_t = r["approaches"]["Old"]
            best_name = min(
                (k for k in r["approaches"] if k != "Old"),
                key=lambda k: r["approaches"][k],
            )
            best_t = r["approaches"][best_name]
            speedup = old_t / best_t if best_t > 0 else 0
            print(f"    {r['model']:<26} winner={best_name:<10} "
                  f"{speedup:.2f}x faster than Old")
        print()


if __name__ == "__main__":
    run_benchmark()
