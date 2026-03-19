"""
All tests for the Ladder and RatingView classes are located here.
"""

from __future__ import annotations

import random

import pytest

from openskill.batch import Game
from openskill.ladder import _HAS_CYTHON, Ladder, RatingView
from openskill.models import (
    BradleyTerryFull,
    BradleyTerryPart,
    PlackettLuce,
    ThurstoneMostellerFull,
    ThurstoneMostellerPart,
)


def _old_approach(model, games):
    """
    Baseline sequential :code:`model.rate()` with dict.

    :param model: An openskill model instance.
    :param games: List of :class:`Game` objects.
    :return: Dictionary mapping entity IDs to ``(mu, sigma)`` tuples.
    """
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
    """
    Generate random games for testing.

    :param num_players: Number of player IDs to choose from.
    :param num_games: Number of games to generate.
    :param seed: Random seed for reproducibility.
    :return: List of :class:`Game` objects.
    """
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
                teams.append(chosen[start : start + team_size])
        if len(teams) < 2:
            continue
        ranks = list(range(1, len(teams) + 1))
        rng.shuffle(ranks)
        games.append(Game(teams=teams, ranks=ranks))
    return games


# RatingView


def test_rating_view_mu_sigma_read() -> None:
    """
    Ensures mu and sigma can be read from a :code:`RatingView`.
    """
    lad = Ladder(PlackettLuce())
    v = lad.add("a", mu=30.0, sigma=5.0)
    assert v.mu == 30.0
    assert v.sigma == 5.0


def test_rating_view_mu_sigma_write() -> None:
    """
    Ensures mu and sigma can be written via a :code:`RatingView`
    and are reflected in the backing arrays.
    """
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


def test_rating_view_ordinal() -> None:
    """
    Ensures the ordinal calculation works correctly.
    """
    lad = Ladder(PlackettLuce())
    v = lad.add("a", mu=25.0, sigma=8.333)
    assert v.ordinal() == pytest.approx(25.0 - 3.0 * 8.333)


def test_rating_view_repr() -> None:
    """
    Ensures the :code:`RatingView` repr contains entity ID and mu.
    """
    lad = Ladder(PlackettLuce())
    v = lad.add("a")
    assert "a" in repr(v)
    assert "mu=" in repr(v)


def test_rating_view_entity_id() -> None:
    """
    Ensures the entity_id property returns the correct value.
    """
    lad = Ladder(PlackettLuce())
    v = lad.add("alice")
    assert v.entity_id == "alice"


def test_rating_view_slots() -> None:
    """
    Ensures :code:`RatingView` uses ``__slots__`` (no ``__dict__``).
    """
    lad = Ladder(PlackettLuce())
    v = lad["x"]
    assert not hasattr(v, "__dict__")


def test_rating_view_eq_same() -> None:
    """
    Ensures two :code:`RatingView` objects with the same mu and sigma
    are equal.
    """
    lad = Ladder(PlackettLuce())
    v1 = lad.add("a", mu=25.0, sigma=8.0)
    v2 = lad.add("b", mu=25.0, sigma=8.0)
    assert v1 == v2


def test_rating_view_eq_different() -> None:
    """
    Ensures two :code:`RatingView` objects with different mu are not equal.
    """
    lad = Ladder(PlackettLuce())
    v1 = lad.add("a", mu=25.0, sigma=8.0)
    v2 = lad.add("b", mu=30.0, sigma=8.0)
    assert v1 != v2


def test_rating_view_eq_non_ratingview() -> None:
    """
    Ensures comparison with a non-:code:`RatingView` returns
    :code:`NotImplemented`.
    """
    lad = Ladder(PlackettLuce())
    v = lad.add("a")
    assert v != "not a rating view"
    assert v.__eq__("not a rating view") is NotImplemented


def test_rating_view_lt() -> None:
    """
    Ensures the less-than comparison works based on ordinal.
    """
    lad = Ladder(PlackettLuce())
    v_low = lad.add("low", mu=10.0, sigma=3.0)
    v_high = lad.add("high", mu=40.0, sigma=3.0)
    assert v_low < v_high
    assert not v_high < v_low


# Ladder


def test_auto_register() -> None:
    """
    Ensures entities are auto-registered on first access.
    """
    lad = Ladder(PlackettLuce())
    v = lad["new_player"]
    assert v.mu == lad._default_mu
    assert v.sigma == lad._default_sigma
    assert len(lad) == 1


def test_add_explicit() -> None:
    """
    Ensures entities can be added with explicit mu and sigma.
    """
    lad = Ladder(PlackettLuce())
    v = lad.add("a", mu=30.0, sigma=5.0)
    assert v.mu == 30.0
    assert v.sigma == 5.0


def test_add_update() -> None:
    """
    Ensures adding an existing entity updates only the specified values.
    """
    lad = Ladder(PlackettLuce())
    lad.add("a", mu=20.0, sigma=6.0)
    lad.add("a", mu=30.0)
    v = lad["a"]
    assert v.mu == 30.0
    assert v.sigma == 6.0


def test_add_update_sigma() -> None:
    """
    Ensures updating only sigma leaves mu unchanged.
    """
    lad = Ladder(PlackettLuce())
    lad.add("a", mu=20.0, sigma=6.0)
    lad.add("a", sigma=3.0)
    v = lad["a"]
    assert v.mu == 20.0
    assert v.sigma == 3.0


def test_contains() -> None:
    """
    Ensures the ``in`` operator works correctly.
    """
    lad = Ladder(PlackettLuce())
    assert "x" not in lad
    lad["x"]
    assert "x" in lad


def test_iter() -> None:
    """
    Ensures iteration over a Ladder yields entity IDs.
    """
    lad = Ladder(PlackettLuce())
    lad["a"]
    lad["b"]
    lad["c"]
    assert set(lad) == {"a", "b", "c"}


def test_overflow() -> None:
    """
    Ensures an :code:`OverflowError` is raised when the Ladder is full.
    """
    lad = Ladder(PlackettLuce(), max_entities=2)
    lad["a"]
    lad["b"]
    with pytest.raises(OverflowError):
        lad["c"]


def test_rate_single_game() -> None:
    """
    Ensures a single game can be rated with the winner getting higher mu.
    """
    model = PlackettLuce()
    lad = Ladder(model)
    lad.rate([["a"], ["b"]], ranks=[1, 2])
    assert lad["a"].mu > lad["b"].mu


def test_rate_matches_model_rate() -> None:
    """
    Ensures :code:`Ladder.rate()` matches :code:`model.rate()` exactly
    for a single game.
    """
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


def test_rate_scores_mode() -> None:
    """
    Ensures rating with scores works correctly.
    """
    model = PlackettLuce()
    lad = Ladder(model, use_cython=False)
    lad.rate([["a"], ["b"]], scores=[10, 20])
    assert lad["b"].mu > lad["a"].mu


def test_rate_weights() -> None:
    """
    Ensures rating with weights affects sigma proportionally.
    """
    model = PlackettLuce()
    lad = Ladder(model, use_cython=False)
    lad.rate(
        [["a", "b"], ["c", "d"]],
        ranks=[1, 2],
        weights=[[1.0, 0.5], [1.0, 0.5]],
    )
    assert abs(lad["b"].sigma - model.sigma) < abs(lad["a"].sigma - model.sigma)


def test_sequential_matches_old_approach() -> None:
    """
    Ensures multiple games via Ladder sequential match the old approach.
    """
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


def test_rate_batch_matches_sequential() -> None:
    """
    Ensures :code:`rate_batch` produces the same results as sequential rating.
    """
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


def test_all_models_exact() -> None:
    """
    Ensures all 5 models produce the same results as the old approach.
    """
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
            assert mu_diff < 1e-9, f"{type(model).__name__} {pid}: mu diff={mu_diff}"
            assert (
                sig_diff < 1e-9
            ), f"{type(model).__name__} {pid}: sigma diff={sig_diff}"


def test_to_dict() -> None:
    """
    Ensures :code:`to_dict()` returns correct entity ratings.
    """
    lad = Ladder(PlackettLuce())
    lad.add("a", mu=30.0, sigma=5.0)
    lad.add("b", mu=20.0, sigma=8.0)
    d = lad.to_dict()
    assert d == {"a": (30.0, 5.0), "b": (20.0, 8.0)}


def test_view_reflects_rate_changes() -> None:
    """
    Ensures :code:`RatingView` always reflects the latest rating.
    """
    lad = Ladder(PlackettLuce())
    v = lad["a"]
    old_mu = v.mu
    lad.rate([["a"], ["b"]], ranks=[1, 2])
    assert v.mu != old_mu


def test_initial_ratings() -> None:
    """
    Ensures pre-set ratings are respected when rating games.
    """
    lad = Ladder(PlackettLuce())
    lad.add("veteran", mu=35.0, sigma=3.0)
    lad.rate([["veteran"], ["newbie"]], ranks=[1, 2])
    assert lad["veteran"].mu > lad["newbie"].mu


def test_multi_team_game() -> None:
    """
    Ensures 3-team game (PlackettLuce-specific) works correctly.
    """
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


def test_keys() -> None:
    """
    Ensures :code:`keys()` returns all registered entity IDs.
    """
    lad = Ladder(PlackettLuce())
    lad["a"]
    lad["b"]
    lad["c"]
    assert set(lad.keys()) == {"a", "b", "c"}


def test_model_property() -> None:
    """
    Ensures the :code:`model` property returns the underlying model.
    """
    model = PlackettLuce()
    lad = Ladder(model)
    assert lad.model is model


def test_rate_no_ranks_no_scores() -> None:
    """
    Ensures rating with neither ranks nor scores uses default ordering.
    """
    model = PlackettLuce()
    lad = Ladder(model, use_cython=False)
    lad.rate([["a"], ["b"]])
    assert "a" in lad
    assert "b" in lad


def test_rate_limit_sigma() -> None:
    """
    Ensures :code:`limit_sigma` prevents sigma from increasing.
    """
    model = PlackettLuce(limit_sigma=True)
    lad = Ladder(model, use_cython=False)
    lad.rate([["a"], ["b"]], ranks=[1, 2])
    assert lad["a"].sigma <= model.sigma
    assert lad["b"].sigma <= model.sigma


# Cython


@pytest.mark.skipif(not _HAS_CYTHON, reason="Cython extension not built")
def test_cython_matches_python() -> None:
    """
    Ensures Cython path produces identical results to Python path.
    """
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


@pytest.mark.skipif(not _HAS_CYTHON, reason="Cython extension not built")
def test_cython_all_models() -> None:
    """
    Ensures Cython path matches the old approach for all 5 models.
    """
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
            assert (
                mu_diff < 1e-9
            ), f"Cython {type(model).__name__} {pid}: mu diff={mu_diff}"
            assert (
                sig_diff < 1e-9
            ), f"Cython {type(model).__name__} {pid}: sigma diff={sig_diff}"


@pytest.mark.skipif(not _HAS_CYTHON, reason="Cython extension not built")
def test_cython_scores_mode() -> None:
    """
    Ensures Cython path works with scores.
    """
    model = PlackettLuce()
    lad = Ladder(model, use_cython=True)
    lad.rate([["a"], ["b"]], scores=[10, 20])
    assert lad["b"].mu > lad["a"].mu


# Cython Fallback


def test_use_cython_false_explicit() -> None:
    """
    Ensures :code:`use_cython=False` disables Cython even when available.
    """
    lad = Ladder(PlackettLuce(), use_cython=False)
    assert lad._use_cython is False


def test_cython_fallback() -> None:
    """
    Ensures :code:`use_cython=True` falls back gracefully when Cython is
    not available.
    """
    import openskill.ladder as ladder_mod

    orig = ladder_mod._HAS_CYTHON
    try:
        ladder_mod._HAS_CYTHON = False
        lad = Ladder(PlackettLuce(), use_cython=True)
        assert lad._use_cython is False
        lad.rate([["a"], ["b"]], ranks=[1, 2])
        assert lad["a"].mu > lad["b"].mu
    finally:
        ladder_mod._HAS_CYTHON = orig


def test_import_fallback_path() -> None:
    """
    Ensures the :code:`ImportError` fallback for :code:`_cfast` import
    sets :code:`_HAS_CYTHON` to ``False``.
    """
    import importlib
    import sys

    import openskill
    import openskill.ladder as ladder_mod

    # Save and remove _cfast from sys.modules and openskill package
    saved_modules = {}
    for key in list(sys.modules):
        if "_cfast" in key:
            saved_modules[key] = sys.modules.pop(key)

    saved_attr = getattr(openskill, "_cfast", None)
    if hasattr(openskill, "_cfast"):
        delattr(openskill, "_cfast")

    # Block re-import by inserting None (triggers ImportError)
    sys.modules["openskill._cfast"] = None  # type: ignore[assignment]
    try:
        importlib.reload(ladder_mod)
        assert ladder_mod._HAS_CYTHON is False
        assert ladder_mod._cy_rate_game is None
    finally:
        del sys.modules["openskill._cfast"]
        sys.modules.update(saved_modules)
        if saved_attr is not None:
            openskill._cfast = saved_attr  # type: ignore[attr-defined]
        importlib.reload(ladder_mod)
