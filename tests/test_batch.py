"""Tests for batch processing module."""

import pytest

from openskill.batch import (
    BatchProcessor,
    Game,
    _extract_model_config,
    _FastRating,
    _init_worker,
    _worker_rate_game,
    partition_waves,
)
from openskill.models import (
    BradleyTerryFull,
    BradleyTerryPart,
    PlackettLuce,
    ThurstoneMostellerFull,
    ThurstoneMostellerPart,
)


class TestPartitionWaves:
    """Tests for wave partitioning algorithms."""

    def test_independent_games_single_wave(self) -> None:
        """Games with no shared entities should all be in one wave."""
        games = [
            Game(teams=[["a", "b"], ["c", "d"]]),
            Game(teams=[["e", "f"], ["g", "h"]]),
            Game(teams=[["i", "j"], ["k", "l"]]),
        ]
        waves = partition_waves(games)
        assert len(waves) == 1
        assert len(waves[0]) == 3

    def test_dependent_games_separate_waves(self) -> None:
        """Games sharing entities must be in different waves."""
        games = [
            Game(teams=[["a", "b"], ["c", "d"]]),
            Game(teams=[["a", "e"], ["f", "g"]]),  # shares "a"
        ]
        waves = partition_waves(games)
        assert len(waves) == 2
        assert len(waves[0]) == 1
        assert len(waves[1]) == 1

    def test_mixed_dependencies(self) -> None:
        """Mix of independent and dependent games."""
        games = [
            Game(teams=[["a"], ["b"]]),  # wave 0
            Game(teams=[["c"], ["d"]]),  # wave 0 (independent of game 0)
            Game(teams=[["a"], ["c"]]),  # wave 1 (shares a and c)
            Game(teams=[["e"], ["f"]]),  # wave 0 (independent)
        ]
        waves = partition_waves(games)
        assert len(waves) == 2
        wave0_indices = [idx for idx, _ in waves[0]]
        wave1_indices = [idx for idx, _ in waves[1]]
        assert 0 in wave0_indices
        assert 1 in wave0_indices
        assert 3 in wave0_indices
        assert 2 in wave1_indices

    def test_no_entity_appears_twice_in_wave(self) -> None:
        """Verify the core safety property across many games."""
        games = [
            Game(teams=[["a", "b"], ["c", "d"]]),
            Game(teams=[["e", "f"], ["g", "h"]]),
            Game(teams=[["a", "e"], ["i", "j"]]),
            Game(teams=[["b", "f"], ["k", "l"]]),
            Game(teams=[["c", "g"], ["m", "n"]]),
        ]
        waves = partition_waves(games)
        for wave in waves:
            entities_in_wave: set[str] = set()
            for _, game in wave:
                game_entities: set[str] = set()
                for team in game.teams:
                    game_entities.update(team)
                assert game_entities.isdisjoint(
                    entities_in_wave
                ), f"Entity overlap in wave: {game_entities & entities_in_wave}"
                entities_in_wave.update(game_entities)

    def test_preserves_all_games(self) -> None:
        """All games must appear exactly once across all waves."""
        games = [
            Game(teams=[["a"], ["b"]]),
            Game(teams=[["a"], ["c"]]),
            Game(teams=[["b"], ["c"]]),
            Game(teams=[["d"], ["e"]]),
        ]
        waves = partition_waves(games)
        all_indices: list[int] = []
        for wave in waves:
            for idx, _ in wave:
                all_indices.append(idx)
        assert sorted(all_indices) == list(range(len(games)))

    def test_empty_games(self) -> None:
        """Empty game list produces no waves."""
        assert partition_waves([]) == []

    def test_single_game(self) -> None:
        """Single game produces one wave with one game."""
        games = [Game(teams=[["a"], ["b"]])]
        waves = partition_waves(games)
        assert len(waves) == 1
        assert len(waves[0]) == 1

    def test_all_games_share_entity(self) -> None:
        """Worst case: all games share one entity -> one game per wave."""
        games = [
            Game(teams=[["shared", "b"], ["c", "d"]]),
            Game(teams=[["shared", "e"], ["f", "g"]]),
            Game(teams=[["shared", "h"], ["i", "j"]]),
        ]
        waves = partition_waves(games)
        assert len(waves) == 3

    def test_ordering_preserved_across_waves(self) -> None:
        """If game i < game j share entities, i is in an earlier wave."""
        games = [
            Game(teams=[["a"], ["b"]]),  # idx 0
            Game(teams=[["a"], ["c"]]),  # idx 1, depends on 0
            Game(teams=[["a"], ["d"]]),  # idx 2, depends on 0 and 1
        ]
        waves = partition_waves(games)
        # Find which wave each game is in
        game_wave: dict[int, int] = {}
        for w_idx, wave in enumerate(waves):
            for g_idx, _ in wave:
                game_wave[g_idx] = w_idx
        assert game_wave[0] < game_wave[1]
        assert game_wave[1] < game_wave[2]


class TestPartitionWavesOrdering:
    """Tests for the chronological ordering invariant."""

    def test_no_leapfrogging(self) -> None:
        """Game i before game j (shared entities) => wave(i) < wave(j)."""
        games = [
            Game(teams=[["a", "b"], ["c", "d"]]),  # 0
            Game(teams=[["a", "c"], ["e", "f"]]),  # 1: shares a,c with 0
            Game(teams=[["e"], ["g"]]),  # 2: shares e with 1
            Game(teams=[["b"], ["h"]]),  # 3: shares b with 0
        ]
        waves = partition_waves(games)
        game_wave: dict[int, int] = {}
        for w_idx, wave in enumerate(waves):
            for g_idx, _ in wave:
                game_wave[g_idx] = w_idx

        def get_ents(g: Game) -> set[str]:
            return {e for t in g.teams for e in t}

        # Check: for all pairs (i < j) sharing entities, wave(i) < wave(j)
        for i in range(len(games)):
            for j in range(i + 1, len(games)):
                if get_ents(games[i]) & get_ents(games[j]):
                    assert game_wave[i] < game_wave[j], (
                        f"game {i} (wave {game_wave[i]}) must precede "
                        f"game {j} (wave {game_wave[j]})"
                    )

    def test_power_law_no_violations(self) -> None:
        """Stress test with power-law player distribution (the bug case)."""
        import math
        import random

        rng = random.Random(42)
        pids = [f"p{i}" for i in range(30)]
        weights = [1.0 / (i + 1) ** 0.6 for i in range(30)]
        total = sum(weights)
        weights = [w / total for w in weights]

        games = []
        for _ in range(100):
            ts = rng.randint(2, 3)
            keyed = [(-math.log(rng.random()) / w, p) for w, p in zip(weights, pids)]
            keyed.sort()
            chosen = [p for _, p in keyed[: ts * 2]]
            games.append(Game(teams=[chosen[:ts], chosen[ts:]]))

        waves = partition_waves(games)

        def get_ents(g: Game) -> set[str]:
            return {e for t in g.teams for e in t}

        game_wave: dict[int, int] = {}
        for w_idx, wave in enumerate(waves):
            for g_idx, _ in wave:
                game_wave[g_idx] = w_idx

        violations = 0
        for i in range(len(games)):
            for j in range(i + 1, len(games)):
                if get_ents(games[i]) & get_ents(games[j]):
                    if game_wave[i] >= game_wave[j]:
                        violations += 1
        assert violations == 0, f"{violations} ordering violations found"


class TestBatchProcessor:
    """Tests for BatchProcessor."""

    def test_sequential_matches_manual_rate(self) -> None:
        """Sequential batch processing must match manual rate() calls."""
        model = PlackettLuce()

        # Manual processing
        p1 = model.rating()
        p2 = model.rating()
        p3 = model.rating()
        p4 = model.rating()

        [t1, t2] = model.rate([[p1, p2], [p3, p4]], ranks=[1, 2])
        p1, p2 = t1
        p3, p4 = t2

        [t3, t4] = model.rate([[p1, p3], [p2, p4]], ranks=[2, 1])
        p1_m, p3_m = t3
        p2_m, p4_m = t4

        # Batch processing
        games = [
            Game(teams=[["p1", "p2"], ["p3", "p4"]], ranks=[1, 2]),
            Game(teams=[["p1", "p3"], ["p2", "p4"]], ranks=[2, 1]),
        ]
        processor = BatchProcessor(model, n_workers=1)
        ratings = processor.process(games)

        assert abs(ratings["p1"][0] - p1_m.mu) < 1e-10
        assert abs(ratings["p1"][1] - p1_m.sigma) < 1e-10
        assert abs(ratings["p2"][0] - p2_m.mu) < 1e-10
        assert abs(ratings["p2"][1] - p2_m.sigma) < 1e-10
        assert abs(ratings["p3"][0] - p3_m.mu) < 1e-10
        assert abs(ratings["p3"][1] - p3_m.sigma) < 1e-10
        assert abs(ratings["p4"][0] - p4_m.mu) < 1e-10
        assert abs(ratings["p4"][1] - p4_m.sigma) < 1e-10

    def test_parallel_matches_sequential(self) -> None:
        """Parallel processing must produce identical results to sequential."""
        model = PlackettLuce()

        games = [
            Game(teams=[["a", "b"], ["c", "d"]], ranks=[1, 2]),
            Game(teams=[["e", "f"], ["g", "h"]], ranks=[2, 1]),
            Game(teams=[["a", "e"], ["b", "f"]], ranks=[1, 2]),
            Game(teams=[["c", "g"], ["d", "h"]], ranks=[2, 1]),
        ]

        seq = BatchProcessor(model, n_workers=1)
        par = BatchProcessor(model, n_workers=2, pipeline=False)

        seq_ratings = seq.process(games)
        par_ratings = par.process(games)

        for eid in seq_ratings:
            assert (
                abs(seq_ratings[eid][0] - par_ratings[eid][0]) < 1e-10
            ), f"mu mismatch for {eid}"
            assert (
                abs(seq_ratings[eid][1] - par_ratings[eid][1]) < 1e-10
            ), f"sigma mismatch for {eid}"

    def test_pipelined_matches_sequential(self) -> None:
        """Pipelined processing must produce identical results."""
        model = PlackettLuce()

        games = [
            Game(teams=[["a", "b"], ["c", "d"]], ranks=[1, 2]),
            Game(teams=[["e", "f"], ["g", "h"]], ranks=[2, 1]),
            Game(teams=[["a", "e"], ["b", "f"]], ranks=[1, 2]),
        ]

        seq = BatchProcessor(model, n_workers=1)
        pip = BatchProcessor(model, n_workers=2, pipeline=True)

        seq_ratings = seq.process(games)
        pip_ratings = pip.process(games)

        for eid in seq_ratings:
            assert abs(seq_ratings[eid][0] - pip_ratings[eid][0]) < 1e-10
            assert abs(seq_ratings[eid][1] - pip_ratings[eid][1]) < 1e-10

    def test_initial_ratings_respected(self) -> None:
        """Pre-existing ratings should be used instead of defaults."""
        model = PlackettLuce()

        games = [
            Game(teams=[["a"], ["b"]], ranks=[1, 2]),
        ]

        initial = {"a": (30.0, 5.0), "b": (20.0, 5.0)}
        processor = BatchProcessor(model, n_workers=1)
        ratings = processor.process(games, initial_ratings=initial)

        # "a" wins and starts higher, should remain higher
        assert ratings["a"][0] > ratings["b"][0]
        # Ratings should have changed from initial values
        assert ratings["a"][0] != 30.0 or ratings["a"][1] != 5.0

    def test_empty_games(self) -> None:
        """Empty game list returns empty or initial ratings."""
        model = PlackettLuce()
        processor = BatchProcessor(model, n_workers=1)

        assert processor.process([]) == {}
        assert processor.process([], initial_ratings={"a": (25.0, 8.33)}) == {
            "a": (25.0, 8.33)
        }

    def test_scores_mode(self) -> None:
        """Batch processing works with scores instead of ranks."""
        model = PlackettLuce()

        games = [
            Game(teams=[["a"], ["b"]], scores=[10.0, 5.0]),
            Game(teams=[["c"], ["d"]], scores=[3.0, 7.0]),
        ]

        processor = BatchProcessor(model, n_workers=1)
        ratings = processor.process(games)

        # Higher score -> better rating
        assert ratings["a"][0] > ratings["b"][0]
        assert ratings["d"][0] > ratings["c"][0]

    def test_all_models(self) -> None:
        """Batch processing works with all model types."""
        games = [
            Game(teams=[["a"], ["b"]], ranks=[1, 2]),
            Game(teams=[["c"], ["d"]], ranks=[2, 1]),
        ]

        for model_class in [
            PlackettLuce,
            BradleyTerryFull,
            BradleyTerryPart,
            ThurstoneMostellerFull,
            ThurstoneMostellerPart,
        ]:
            model = model_class()
            processor = BatchProcessor(model, n_workers=1)
            ratings = processor.process(games)

            assert "a" in ratings
            assert "b" in ratings
            assert "c" in ratings
            assert "d" in ratings
            # Winner should have higher mu
            assert (
                ratings["a"][0] > ratings["b"][0]
            ), f"Failed for {model_class.__name__}"
            assert (
                ratings["d"][0] > ratings["c"][0]
            ), f"Failed for {model_class.__name__}"

    def test_reproducibility(self) -> None:
        """Multiple runs produce identical results."""
        model = PlackettLuce()

        games = [
            Game(teams=[["a", "b"], ["c", "d"]], ranks=[1, 2]),
            Game(teams=[["a", "c"], ["b", "d"]], ranks=[2, 1]),
            Game(teams=[["e", "f"], ["g", "h"]], ranks=[1, 2]),
        ]

        processor = BatchProcessor(model, n_workers=2, pipeline=True)

        r1 = processor.process(games)
        r2 = processor.process(games)

        for eid in r1:
            assert r1[eid][0] == r2[eid][0], f"mu not reproducible for {eid}"
            assert r1[eid][1] == r2[eid][1], f"sigma not reproducible for {eid}"

    def test_many_independent_games(self) -> None:
        """Large batch of independent games processes correctly."""
        model = PlackettLuce()

        # 100 games, all independent (unique players)
        games = []
        for i in range(100):
            games.append(
                Game(
                    teams=[[f"p{i*2}"], [f"p{i*2+1}"]],
                    ranks=[1, 2],
                )
            )

        seq = BatchProcessor(model, n_workers=1)
        par = BatchProcessor(model, n_workers=2, pipeline=True)

        seq_ratings = seq.process(games)
        par_ratings = par.process(games)

        assert len(seq_ratings) == 200
        for eid in seq_ratings:
            assert abs(seq_ratings[eid][0] - par_ratings[eid][0]) < 1e-10
            assert abs(seq_ratings[eid][1] - par_ratings[eid][1]) < 1e-10

    def test_chain_of_dependent_games(self) -> None:
        """Chain where each game depends on the previous (worst case)."""
        model = PlackettLuce()

        # p0 plays in every game - forces fully sequential processing
        games = [
            Game(teams=[["p0"], [f"opponent_{i}"]], ranks=[1, 2]) for i in range(10)
        ]

        seq = BatchProcessor(model, n_workers=1)
        par = BatchProcessor(model, n_workers=4, pipeline=True)

        seq_ratings = seq.process(games)
        par_ratings = par.process(games)

        for eid in seq_ratings:
            assert abs(seq_ratings[eid][0] - par_ratings[eid][0]) < 1e-10
            assert abs(seq_ratings[eid][1] - par_ratings[eid][1]) < 1e-10

    def test_multiprocess_matches_sequential(self) -> None:
        """Multiprocessing path produces same results as sequential."""
        model = PlackettLuce()

        # Mix of independent and dependent games
        games = [
            Game(teams=[["a"], ["b"]], ranks=[1, 2]),
            Game(teams=[["c"], ["d"]], ranks=[2, 1]),
            Game(teams=[["e"], ["f"]], ranks=[1, 2]),
            Game(teams=[["a"], ["c"]], ranks=[1, 2]),
            Game(teams=[["b"], ["d"]], ranks=[2, 1]),
        ]

        seq = BatchProcessor(model, n_workers=1)
        mp = BatchProcessor(model, n_workers=2, pipeline=False)

        seq_ratings = seq.process(games)
        mp_ratings = mp.process(games)

        for eid in seq_ratings:
            assert (
                abs(seq_ratings[eid][0] - mp_ratings[eid][0]) < 1e-10
            ), f"mu mismatch for {eid}: {seq_ratings[eid][0]} vs {mp_ratings[eid][0]}"
            assert (
                abs(seq_ratings[eid][1] - mp_ratings[eid][1]) < 1e-10
            ), f"sigma mismatch for {eid}: {seq_ratings[eid][1]} vs {mp_ratings[eid][1]}"

    def test_weights_passed_through(self) -> None:
        """Weights are correctly passed to the underlying model."""
        model = PlackettLuce()

        # Game with weights vs without should produce different results
        game_no_weights = Game(teams=[["a", "b"], ["c", "d"]], ranks=[1, 2])
        game_with_weights = Game(
            teams=[["a", "b"], ["c", "d"]],
            ranks=[1, 2],
            weights=[[1.0, 0.5], [0.5, 1.0]],
        )

        proc = BatchProcessor(model, n_workers=1)
        r_no = proc.process([game_no_weights])
        r_with = proc.process([game_with_weights])

        # Results should differ due to weights
        assert r_no["a"][0] != r_with["a"][0] or r_no["b"][0] != r_with["b"][0]

    def test_limit_sigma(self) -> None:
        """limit_sigma=True prevents sigma from increasing."""
        model = PlackettLuce(limit_sigma=True)

        games = [
            Game(teams=[["a"], ["b"]], ranks=[1, 2]),
        ]

        processor = BatchProcessor(model, n_workers=1)
        ratings = processor.process(games)

        # With limit_sigma, sigma should not exceed the default
        assert ratings["a"][1] <= model.sigma
        assert ratings["b"][1] <= model.sigma

    def test_no_ranks_no_scores(self) -> None:
        """Games with neither ranks nor scores use default ordering."""
        model = PlackettLuce()

        games = [
            Game(teams=[["a"], ["b"]]),
        ]

        processor = BatchProcessor(model, n_workers=1)
        ratings = processor.process(games)

        # Both should have ratings (default rank ordering applied)
        assert "a" in ratings
        assert "b" in ratings

    def test_multiprocess_path_pipelined(self) -> None:
        """Force ProcessPoolExecutor path in pipelined mode."""
        model = PlackettLuce()

        games = [
            Game(teams=[["a"], ["b"]], ranks=[1, 2]),
            Game(teams=[["c"], ["d"]], ranks=[2, 1]),
            Game(teams=[["e"], ["f"]], ranks=[1, 2]),
            Game(teams=[["a"], ["c"]], ranks=[1, 2]),
        ]

        seq = BatchProcessor(model, n_workers=1)
        mp = BatchProcessor(model, n_workers=2, pipeline=True)
        mp._use_threads = False  # Force multiprocess path

        seq_ratings = seq.process(games)
        mp_ratings = mp.process(games)

        for eid in seq_ratings:
            assert abs(seq_ratings[eid][0] - mp_ratings[eid][0]) < 1e-10
            assert abs(seq_ratings[eid][1] - mp_ratings[eid][1]) < 1e-10

    def test_multiprocess_path_non_pipelined(self) -> None:
        """Force ProcessPoolExecutor path in non-pipelined mode."""
        model = PlackettLuce()

        games = [
            Game(teams=[["a"], ["b"]], ranks=[1, 2]),
            Game(teams=[["c"], ["d"]], ranks=[2, 1]),
            Game(teams=[["e"], ["f"]], ranks=[1, 2]),
            Game(teams=[["a"], ["c"]], ranks=[1, 2]),
        ]

        seq = BatchProcessor(model, n_workers=1)
        mp = BatchProcessor(model, n_workers=2, pipeline=False)
        mp._use_threads = False

        seq_ratings = seq.process(games)
        mp_ratings = mp.process(games)

        for eid in seq_ratings:
            assert abs(seq_ratings[eid][0] - mp_ratings[eid][0]) < 1e-10
            assert abs(seq_ratings[eid][1] - mp_ratings[eid][1]) < 1e-10

    def test_multiprocess_large_wave(self) -> None:
        """Force ProcessPoolExecutor with waves having >2 games."""
        model = PlackettLuce()

        # Many independent games -> single large wave, triggers the
        # executor.map path (wave > 2 games)
        games = [
            Game(teams=[[f"p{i*2}"], [f"p{i*2+1}"]], ranks=[1, 2]) for i in range(10)
        ]

        seq = BatchProcessor(model, n_workers=1)
        mp = BatchProcessor(model, n_workers=2, pipeline=False)
        mp._use_threads = False

        seq_ratings = seq.process(games)
        mp_ratings = mp.process(games)

        for eid in seq_ratings:
            assert abs(seq_ratings[eid][0] - mp_ratings[eid][0]) < 1e-10

    def test_multiprocess_scores_and_weights(self) -> None:
        """ProcessPoolExecutor path with scores and weights."""
        model = PlackettLuce()

        games = [
            Game(
                teams=[["a", "b"], ["c", "d"]],
                scores=[10.0, 5.0],
                weights=[[1.0, 0.5], [0.5, 1.0]],
            ),
            Game(
                teams=[["e", "f"], ["g", "h"]],
                scores=[3.0, 7.0],
                weights=[[1.0, 1.0], [1.0, 1.0]],
            ),
            # Third game to ensure wave has >2 games for executor.map
            Game(
                teams=[["i", "j"], ["k", "l"]],
                scores=[8.0, 2.0],
            ),
        ]

        seq = BatchProcessor(model, n_workers=1)
        mp = BatchProcessor(model, n_workers=2, pipeline=False)
        mp._use_threads = False

        seq_ratings = seq.process(games)
        mp_ratings = mp.process(games)

        for eid in seq_ratings:
            assert abs(seq_ratings[eid][0] - mp_ratings[eid][0]) < 1e-10

    def test_multiprocess_limit_sigma(self) -> None:
        """ProcessPoolExecutor path respects limit_sigma."""
        model = PlackettLuce(limit_sigma=True)

        games = [
            Game(teams=[[f"p{i*2}"], [f"p{i*2+1}"]], ranks=[1, 2]) for i in range(5)
        ]

        seq = BatchProcessor(model, n_workers=1)
        mp = BatchProcessor(model, n_workers=2, pipeline=False)
        mp._use_threads = False

        seq_ratings = seq.process(games)
        mp_ratings = mp.process(games)

        for eid in seq_ratings:
            assert abs(seq_ratings[eid][0] - mp_ratings[eid][0]) < 1e-10
            assert abs(seq_ratings[eid][1] - mp_ratings[eid][1]) < 1e-10


class TestFastRating:
    """Tests for _FastRating."""

    def test_basic(self) -> None:
        r = _FastRating(25.0, 8.333)
        assert r.mu == 25.0
        assert r.sigma == 8.333

    def test_ordinal_default(self) -> None:
        r = _FastRating(25.0, 8.333)
        assert r.ordinal() == pytest.approx(25.0 - 3.0 * 8.333)

    def test_ordinal_custom_params(self) -> None:
        r = _FastRating(25.0, 8.333)
        result = r.ordinal(z=2.0, alpha=0.5, target=10.0)
        expected = 0.5 * ((25.0 - 2.0 * 8.333) + (10.0 / 0.5))
        assert result == pytest.approx(expected)


class TestExtractModelConfig:
    """Tests for _extract_model_config."""

    def test_basic_model(self) -> None:
        model = PlackettLuce()
        module, class_name, kwargs = _extract_model_config(model)
        assert "PlackettLuce" in module or class_name == "PlackettLuce"
        assert "mu" in kwargs
        assert "sigma" in kwargs

    def test_model_with_margin_balance(self) -> None:
        """ThurstoneMostellerFull has margin, balance, and weight_bounds."""
        model = ThurstoneMostellerFull()
        module, class_name, kwargs = _extract_model_config(model)
        assert class_name == "ThurstoneMostellerFull"
        assert "gamma" in kwargs
        assert "margin" in kwargs
        assert "balance" in kwargs

    def test_model_with_weight_bounds(self) -> None:
        """BradleyTerryFull has weight_bounds."""
        model = BradleyTerryFull()
        _, _, kwargs = _extract_model_config(model)
        if hasattr(model, "weight_bounds"):
            assert "weight_bounds" in kwargs


class TestWorkerFunctions:
    """Tests for _init_worker and _worker_rate_game."""

    def test_init_worker(self) -> None:
        model = PlackettLuce()
        module, class_name, kwargs = _extract_model_config(model)
        _init_worker(module, class_name, kwargs)

        import openskill.batch as batch_mod

        assert batch_mod._worker_model is not None
        assert batch_mod._worker_tau_sq == model.tau**2

    def test_worker_rate_game(self) -> None:
        """_worker_rate_game produces correct results."""
        model = PlackettLuce()
        module, class_name, kwargs = _extract_model_config(model)
        _init_worker(module, class_name, kwargs)

        args = (
            [[0, 1], [2, 3]],  # team_indices
            [[25.0, 25.0], [25.0, 25.0]],  # team_mus
            [[8.333, 8.333], [8.333, 8.333]],  # team_sigmas
            [1.0, 2.0],  # ranks
            None,  # scores
            None,  # weights
        )
        updates = _worker_rate_game(args)
        assert len(updates) == 4
        for idx, mu, sigma in updates:
            assert isinstance(idx, int)
            assert isinstance(mu, float)
            assert isinstance(sigma, float)

    def test_worker_rate_game_with_scores(self) -> None:
        """_worker_rate_game works with scores instead of ranks."""
        model = PlackettLuce()
        module, class_name, kwargs = _extract_model_config(model)
        _init_worker(module, class_name, kwargs)

        args = (
            [[0], [1]],
            [[25.0], [25.0]],
            [[8.333], [8.333]],
            None,  # ranks
            [10.0, 5.0],  # scores
            None,  # weights
        )
        updates = _worker_rate_game(args)
        assert len(updates) == 2

    def test_worker_rate_game_with_weights(self) -> None:
        """_worker_rate_game works with weights."""
        model = PlackettLuce()
        module, class_name, kwargs = _extract_model_config(model)
        _init_worker(module, class_name, kwargs)

        args = (
            [[0, 1], [2, 3]],
            [[25.0, 25.0], [25.0, 25.0]],
            [[8.333, 8.333], [8.333, 8.333]],
            [1.0, 2.0],  # ranks
            None,  # scores
            [[1.0, 0.5], [0.5, 1.0]],  # weights
        )
        updates = _worker_rate_game(args)
        assert len(updates) == 4

    def test_worker_rate_game_limit_sigma(self) -> None:
        """_worker_rate_game respects limit_sigma."""
        model = PlackettLuce(limit_sigma=True)
        module, class_name, kwargs = _extract_model_config(model)
        _init_worker(module, class_name, kwargs)

        args = (
            [[0], [1]],
            [[25.0], [25.0]],
            [[8.333], [8.333]],
            [1.0, 2.0],
            None,
            None,
        )
        updates = _worker_rate_game(args)
        for _, _, sigma in updates:
            assert sigma <= 8.333

    def test_worker_rate_game_no_ranks_no_scores(self) -> None:
        """_worker_rate_game with neither ranks nor scores."""
        model = PlackettLuce()
        module, class_name, kwargs = _extract_model_config(model)
        _init_worker(module, class_name, kwargs)

        args = (
            [[0], [1]],
            [[25.0], [25.0]],
            [[8.333], [8.333]],
            None,  # ranks
            None,  # scores
            None,  # weights
        )
        updates = _worker_rate_game(args)
        assert len(updates) == 2


class TestPartitionWavesEdgeCases:
    """Additional edge cases for partition_waves."""

    def test_wave_scan_skips_occupied_waves(self) -> None:
        """Force the inner loop to scan past occupied waves.

        Game 0: {a, b} -> wave 0
        Game 1: {a, c} -> wave 1 (a in wave 0)
        Game 2: {b, c} -> must scan: wave 0 has b, wave 1 has c -> wave 2
        """
        games = [
            Game(teams=[["a"], ["b"]]),
            Game(teams=[["a"], ["c"]]),
            Game(teams=[["b"], ["c"]]),
        ]
        waves = partition_waves(games)
        assert len(waves) == 3
        wave_indices = {
            idx: w_idx for w_idx, wave in enumerate(waves) for idx, _ in wave
        }
        assert wave_indices[0] == 0
        assert wave_indices[1] == 1
        assert wave_indices[2] == 2
