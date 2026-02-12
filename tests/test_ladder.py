"""Tests for openskill.ladder.Ladder and RatingView."""

from __future__ import annotations

import math
import random

import pytest

from openskill.batch import Game
from openskill.ladder import Ladder, RatingView, _HAS_CYTHON
from openskill.models import (
    BradleyTerryFull,
    BradleyTerryPart,
    PlackettLuce,
    ThurstoneMostellerFull,
    ThurstoneMostellerPart,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _old_approach(model, games):
    """Baseline sequential model.rate() with dict."""
    players = {}
    for game in games:
        team_objs = []
        team_keys = []
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
        kwargs = {}
        if game.ranks is not None:
            kwargs["ranks"] = list(game.ranks)
        if game.scores is not None:
            kwargs["scores"] = list(game.scores)
        if game.weights is not None:
            kwargs["weights"] = [list(w) for w in game.weights]
        result = model.rate(team_objs, **kwargs)
        for ti, team in enumerate(result):
            for pi, player in enumerate(team):
                players[team_keys[ti][pi]] = player
    return {pid: (r.mu, r.sigma) for pid, r in players.items()}


def _generate_games(num_players, num_games, seed=42):
    rng = random.Random(seed)
    pids = [f"p{i}" for i in range(num_players)]
    games = []
    for _ in range(num_games):
        n_teams = rng.randint(2, 4)
        team_size = rng.randint(1, 3)
        total = n_teams * team_size
        chosen = rng.sample(pids, min(total, num_players))
        teams = []
        for t in range(n_teams):
            start = t * team_size
            if start + team_size <= len(chosen):
                teams.append(chosen[start:start + team_size])
        if len(teams) < 2:
            continue
        ranks = list(range(1, len(teams) + 1))
        rng.shuffle(ranks)
        games.append(Game(teams=teams, ranks=ranks))
    return games


# ---------------------------------------------------------------------------
# TestRatingView
# ---------------------------------------------------------------------------

class TestRatingView:
    def test_mu_sigma_read(self):
        lad = Ladder(PlackettLuce())
        v = lad.add("a", mu=30.0, sigma=5.0)
        assert v.mu == 30.0
        assert v.sigma == 5.0

    def test_mu_sigma_write(self):
        lad = Ladder(PlackettLuce())
        v = lad.add("a")
        v.mu = 42.0
        v.sigma = 1.5
        assert v.mu == 42.0
        assert v.sigma == 1.5
        # Also reflected in backing arrays
        idx = lad._entity_to_idx["a"]
        assert lad._mus[idx] == 42.0
        assert lad._sigmas[idx] == 1.5

    def test_ordinal(self):
        lad = Ladder(PlackettLuce())
        v = lad.add("a", mu=25.0, sigma=8.333)
        assert v.ordinal() == pytest.approx(25.0 - 3.0 * 8.333)

    def test_repr(self):
        lad = Ladder(PlackettLuce())
        v = lad.add("a")
        assert "a" in repr(v)
        assert "mu=" in repr(v)

    def test_entity_id(self):
        lad = Ladder(PlackettLuce())
        v = lad.add("alice")
        assert v.entity_id == "alice"

    def test_slots(self):
        """RatingView should use __slots__ (no __dict__)."""
        lad = Ladder(PlackettLuce())
        v = lad["x"]
        assert not hasattr(v, "__dict__")


# ---------------------------------------------------------------------------
# TestLadder
# ---------------------------------------------------------------------------

class TestLadder:
    def test_auto_register(self):
        lad = Ladder(PlackettLuce())
        v = lad["new_player"]
        assert v.mu == lad._default_mu
        assert v.sigma == lad._default_sigma
        assert len(lad) == 1

    def test_add_explicit(self):
        lad = Ladder(PlackettLuce())
        v = lad.add("a", mu=30.0, sigma=5.0)
        assert v.mu == 30.0
        assert v.sigma == 5.0

    def test_add_update(self):
        lad = Ladder(PlackettLuce())
        lad.add("a", mu=20.0, sigma=6.0)
        lad.add("a", mu=30.0)
        v = lad["a"]
        assert v.mu == 30.0
        assert v.sigma == 6.0  # unchanged

    def test_contains(self):
        lad = Ladder(PlackettLuce())
        assert "x" not in lad
        lad["x"]
        assert "x" in lad

    def test_iter(self):
        lad = Ladder(PlackettLuce())
        lad["a"]
        lad["b"]
        lad["c"]
        assert set(lad) == {"a", "b", "c"}

    def test_overflow(self):
        lad = Ladder(PlackettLuce(), max_entities=2)
        lad["a"]
        lad["b"]
        with pytest.raises(OverflowError):
            lad["c"]

    def test_rate_single_game(self):
        model = PlackettLuce()
        lad = Ladder(model)
        lad.rate([["a"], ["b"]], ranks=[1, 2])
        # "a" won → higher mu
        assert lad["a"].mu > lad["b"].mu

    def test_rate_matches_model_rate(self):
        """Single game: Ladder.rate() must match model.rate() exactly."""
        model = PlackettLuce()
        lad = Ladder(model, use_cython=False)

        lad.rate([["a", "b"], ["c", "d"]], ranks=[1, 2])

        # Run model.rate() manually
        r = [model.rating(), model.rating(), model.rating(), model.rating()]
        result = model.rate([[r[0], r[1]], [r[2], r[3]]], ranks=[1, 2])
        expected = {
            "a": (result[0][0].mu, result[0][0].sigma),
            "b": (result[0][1].mu, result[0][1].sigma),
            "c": (result[1][0].mu, result[1][0].sigma),
            "d": (result[1][1].mu, result[1][1].sigma),
        }
        for eid in expected:
            assert lad[eid].mu == pytest.approx(expected[eid][0], abs=1e-12)
            assert lad[eid].sigma == pytest.approx(expected[eid][1], abs=1e-12)

    def test_rate_scores_mode(self):
        model = PlackettLuce()
        lad = Ladder(model, use_cython=False)
        lad.rate([["a"], ["b"]], scores=[10, 20])
        # Higher score (b=20) should win
        assert lad["b"].mu > lad["a"].mu

    def test_rate_weights(self):
        model = PlackettLuce()
        lad = Ladder(model, use_cython=False)
        lad.rate(
            [["a", "b"], ["c", "d"]],
            ranks=[1, 2],
            weights=[[1.0, 0.5], [1.0, 0.5]],
        )
        # b and d had lower weight → less sigma change
        assert abs(lad["b"].sigma - model.sigma) < abs(lad["a"].sigma - model.sigma)

    def test_sequential_matches_old_approach(self):
        """Multiple games: Ladder sequential must match old approach."""
        model = PlackettLuce()
        games = _generate_games(50, 100, seed=99)

        old = _old_approach(model, games)

        lad = Ladder(model, use_cython=False)
        for game in games:
            lad.rate(game.teams, ranks=game.ranks, scores=game.scores)

        lad_dict = lad.to_dict()
        for pid in old:
            assert pid in lad_dict, f"Missing {pid}"
            assert lad_dict[pid][0] == pytest.approx(old[pid][0], abs=1e-9)
            assert lad_dict[pid][1] == pytest.approx(old[pid][1], abs=1e-9)

    def test_rate_batch_matches_sequential(self):
        model = PlackettLuce()
        games = _generate_games(50, 100, seed=77)

        lad_seq = Ladder(model, use_cython=False)
        for game in games:
            lad_seq.rate(game.teams, ranks=game.ranks)

        lad_batch = Ladder(model, use_cython=False)
        lad_batch.rate_batch(games)

        seq = lad_seq.to_dict()
        batch = lad_batch.to_dict()
        for pid in seq:
            assert batch[pid][0] == pytest.approx(seq[pid][0], abs=1e-12)
            assert batch[pid][1] == pytest.approx(seq[pid][1], abs=1e-12)

    def test_all_models_exact(self):
        """All 5 models produce EXACT same results as old approach."""
        models = [
            PlackettLuce(),
            BradleyTerryFull(),
            BradleyTerryPart(),
            ThurstoneMostellerFull(),
            ThurstoneMostellerPart(),
        ]
        games = _generate_games(30, 60, seed=55)

        for model in models:
            old = _old_approach(model, games)

            lad = Ladder(model, use_cython=False)
            for game in games:
                lad.rate(game.teams, ranks=game.ranks)
            lad_dict = lad.to_dict()

            for pid in old:
                mu_diff = abs(lad_dict[pid][0] - old[pid][0])
                sig_diff = abs(lad_dict[pid][1] - old[pid][1])
                assert mu_diff < 1e-9, (
                    f"{type(model).__name__} {pid}: mu diff={mu_diff}"
                )
                assert sig_diff < 1e-9, (
                    f"{type(model).__name__} {pid}: sigma diff={sig_diff}"
                )

    def test_to_dict(self):
        lad = Ladder(PlackettLuce())
        lad.add("a", mu=30.0, sigma=5.0)
        lad.add("b", mu=20.0, sigma=8.0)
        d = lad.to_dict()
        assert d == {"a": (30.0, 5.0), "b": (20.0, 8.0)}

    def test_view_reflects_rate_changes(self):
        """RatingView must always reflect the latest rating."""
        lad = Ladder(PlackettLuce())
        v = lad["a"]
        old_mu = v.mu
        lad.rate([["a"], ["b"]], ranks=[1, 2])
        # View should reflect the update without re-fetching.
        assert v.mu != old_mu

    def test_initial_ratings(self):
        lad = Ladder(PlackettLuce())
        lad.add("veteran", mu=35.0, sigma=3.0)
        lad.rate([["veteran"], ["newbie"]], ranks=[1, 2])
        # Veteran starts with higher mu
        assert lad["veteran"].mu > lad["newbie"].mu

    def test_multi_team_game(self):
        """3-team game (PlackettLuce-specific)."""
        model = PlackettLuce()
        lad = Ladder(model, use_cython=False)
        lad.rate([["a"], ["b"], ["c"]], ranks=[1, 2, 3])

        old = _old_approach(
            model,
            [Game(teams=[["a"], ["b"], ["c"]], ranks=[1, 2, 3])],
        )
        for pid in old:
            assert lad[pid].mu == pytest.approx(old[pid][0], abs=1e-12)
            assert lad[pid].sigma == pytest.approx(old[pid][1], abs=1e-12)


# ---------------------------------------------------------------------------
# TestLadderCython (skip if not available)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _HAS_CYTHON, reason="Cython extension not built")
class TestLadderCython:
    def test_cython_matches_python(self):
        """Cython path must produce identical results to Python path."""
        model = PlackettLuce()
        games = _generate_games(50, 100, seed=42)

        lad_py = Ladder(model, use_cython=False)
        for game in games:
            lad_py.rate(game.teams, ranks=game.ranks)

        lad_cy = Ladder(model, use_cython=True)
        for game in games:
            lad_cy.rate(game.teams, ranks=game.ranks)

        py_dict = lad_py.to_dict()
        cy_dict = lad_cy.to_dict()
        for pid in py_dict:
            assert cy_dict[pid][0] == pytest.approx(py_dict[pid][0], abs=1e-12)
            assert cy_dict[pid][1] == pytest.approx(py_dict[pid][1], abs=1e-12)

    def test_cython_all_models(self):
        """Cython path matches old approach for all 5 models."""
        models = [
            PlackettLuce(),
            BradleyTerryFull(),
            BradleyTerryPart(),
            ThurstoneMostellerFull(),
            ThurstoneMostellerPart(),
        ]
        games = _generate_games(30, 60, seed=55)

        for model in models:
            old = _old_approach(model, games)

            lad = Ladder(model, use_cython=True)
            for game in games:
                lad.rate(game.teams, ranks=game.ranks)
            lad_dict = lad.to_dict()

            for pid in old:
                mu_diff = abs(lad_dict[pid][0] - old[pid][0])
                sig_diff = abs(lad_dict[pid][1] - old[pid][1])
                assert mu_diff < 1e-9, (
                    f"Cython {type(model).__name__} {pid}: mu diff={mu_diff}"
                )
                assert sig_diff < 1e-9, (
                    f"Cython {type(model).__name__} {pid}: sigma diff={sig_diff}"
                )

    def test_cython_scores_mode(self):
        model = PlackettLuce()
        lad = Ladder(model, use_cython=True)
        lad.rate([["a"], ["b"]], scores=[10, 20])
        assert lad["b"].mu > lad["a"].mu
