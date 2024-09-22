"""
All tests for the ThurstoneMostellerFull model are located here.
"""

import json
import pathlib
from typing import List

import pytest

from openskill.models.weng_lin.thurstone_mosteller_full import (
    ThurstoneMostellerFull,
    ThurstoneMostellerFullRating,
    ThurstoneMostellerFullTeamRating,
    _gamma,
)


def test_model_defaults() -> None:
    """
    Ensures default model parameters have not changed.
    """

    # Default values
    model = ThurstoneMostellerFull()
    assert model.mu == 25.0
    assert model.sigma == 25.0 / 3.0
    assert model.beta == 25.0 / 6.0
    assert model.kappa == 0.0001
    assert model.tau == 25.0 / 300.0
    assert model.limit_sigma is False
    assert model.balance is False
    assert model.__repr__() == f"ThurstoneMostellerFull(mu=25.0, sigma={25.0 / 3.0})"
    assert model.__str__() == (
        f"Thurstone-Mosteller Full Pairing Model Parameters: \n\n"
        f"mu: 25.0\n"
        f"sigma: {25.0 / 3.0}\n"
    )


def test_rating_defaults() -> None:
    """
    Ensures default rating parameters have not changed.
    """

    # Default values
    model = ThurstoneMostellerFull(mu=30, sigma=30 / 3)
    rating = model.rating()
    assert rating.mu == 30.0
    assert rating.sigma == 30.0 / 3.0
    assert (
        rating.__repr__() == f"ThurstoneMostellerFullRating(mu=30.0, sigma={30.0/3.0})"
    )
    assert rating.__str__() == (
        f"Thurstone-Mosteller Full Pairing Player Data: \n\n"
        f"id: {rating.id}\n"
        f"mu: 30.0\n"
        f"sigma: {30.0/3.0}\n"
    )

    # Test Hash
    assert hash(rating) == hash((rating.id, rating.mu, rating.sigma))


def test_rating_overrides() -> None:
    """
    Ensures rating parameters can be overridden.
    """

    # Default values
    model = ThurstoneMostellerFull(mu=30, sigma=30 / 3)

    rating_1 = model.rating(mu=40)
    assert rating_1.mu == 40
    assert rating_1.sigma == 30 / 3

    rating_2 = model.rating(sigma=40 / 3, name="Vivek Joshy")
    assert rating_2.mu == 30
    assert rating_2.sigma == 40 / 3
    assert rating_2.name == "Vivek Joshy"
    assert (
        rating_2.__repr__()
        == f"ThurstoneMostellerFullRating(mu=30.0, sigma={40.0/3.0})"
    )
    assert rating_2.__str__() == (
        f"Thurstone-Mosteller Full Pairing Player Data: \n\n"
        f"id: {rating_2.id}\n"
        f"name: Vivek Joshy\n"
        f"mu: 30.0\n"
        f"sigma: {40.0/3.0}\n"
    )


def test_rating_comparison() -> None:
    """
    Ensures rating comparison works as expected.
    """

    # Compare Values
    model = ThurstoneMostellerFull(mu=30, sigma=30 / 3)

    assert model.rating() <= model.rating()
    assert model.rating() >= model.rating()
    assert model.rating(mu=32.124, sigma=1.421) == model.rating(mu=32.124, sigma=1.421)
    assert model.rating(mu=32.124, sigma=1.421) > model.rating(mu=23.84, sigma=3.443)
    assert model.rating(mu=23.84, sigma=3.443) < model.rating(mu=32.124, sigma=1.421)
    assert not (
        model.rating(mu=32.124, sigma=1.421) == model.rating(mu=33.124, sigma=1.421)
    )
    assert not (
        model.rating(mu=32.124, sigma=1.421) < model.rating(mu=23.84, sigma=3.443)
    )
    assert not (
        model.rating(mu=23.84, sigma=3.443) > model.rating(mu=32.124, sigma=1.421)
    )
    assert not (
        model.rating(mu=32.124, sigma=1.421) <= model.rating(mu=23.84, sigma=3.443)
    )
    assert not (
        model.rating(mu=23.84, sigma=3.443) >= model.rating(mu=32.124, sigma=1.421)
    )

    # Compare rating() with different types.
    assert not (model.rating(mu=32.124, sigma=1.421) == "random_string")

    with pytest.raises(ValueError):
        assert model.rating(mu=32.124, sigma=1.421) < "random_string"  # type: ignore

    with pytest.raises(ValueError):
        assert model.rating(mu=32.124, sigma=1.421) > "random_string"  # type: ignore

    with pytest.raises(ValueError):
        assert model.rating(mu=32.124, sigma=1.421) <= "random_string"  # type: ignore

    with pytest.raises(ValueError):
        assert model.rating(mu=32.124, sigma=1.421) >= "random_string"  # type: ignore


def test_thurstone_mosteller_full_team_rating() -> None:
    """
    Tests the :code:`ThurstoneMostellerFullTeamRating` class.
    """

    # Test Constructor
    team = [ThurstoneMostellerFull().rating() for _ in range(5)]
    rating = ThurstoneMostellerFullTeamRating(1, 2, team, 3)
    assert rating.mu == 1
    assert rating.sigma_squared == 2
    assert rating.team == team
    assert rating.rank == 3

    # Test Equality
    assert rating == ThurstoneMostellerFullTeamRating(1, 2, team, 3)
    assert rating != ThurstoneMostellerFullTeamRating(2, 2, team, 3)
    assert rating != ThurstoneMostellerFullTeamRating(1, 3, team, 3)
    assert rating != ThurstoneMostellerFullTeamRating(
        1, 2, [ThurstoneMostellerFull().rating()], 3
    )
    assert rating != ThurstoneMostellerFullTeamRating(1, 2, team, 4)
    assert rating != 2

    # Test Hash
    assert hash(rating) == hash(ThurstoneMostellerFullTeamRating(1, 2, team, 3))
    assert hash(rating) != hash(ThurstoneMostellerFullTeamRating(2, 2, team, 3))
    assert hash(rating) != hash(ThurstoneMostellerFullTeamRating(1, 3, team, 3))
    assert hash(rating) != hash(
        ThurstoneMostellerFullTeamRating(
            1, 2, [ThurstoneMostellerFullRating(mu=25.0, sigma=25.0 / 3)], 3
        )
    )
    assert hash(rating) != hash(ThurstoneMostellerFullTeamRating(1, 2, team, 4))

    # Test String
    assert repr(rating) == "ThurstoneMostellerFullTeamRating(mu=1.0, sigma_squared=2.0)"
    assert str(rating) == (
        f"ThurstoneMostellerFullTeamRating Details:\n\n"
        f"mu: 1.0\n"
        f"sigma_squared: 2.0\n"
        f"rank: 3\n"
    )


def test_create_rating() -> None:
    """
    Ensures rating can be created manually from a list with a given
    mu and sigma.
    """

    # Create rating
    model = ThurstoneMostellerFull(mu=30, sigma=30 / 3)
    rating = model.create_rating([40, 40 / 3])
    assert rating.mu == 40
    assert rating.sigma == 40 / 3

    rating = model.create_rating([28, 8 * 1.27], name="Vivek Joshy")
    assert rating.name == "Vivek Joshy"

    # Raise Errors
    with pytest.raises(TypeError):
        model.create_rating(rating)  # type: ignore

    with pytest.raises(TypeError):
        model.create_rating(23)  # type: ignore

    with pytest.raises(TypeError):
        model.create_rating({"a", "b"})  # type: ignore

    with pytest.raises(ValueError):
        model.create_rating(["25.0", 25.0 / 3.0])  # type: ignore


def test_c() -> None:
    """
    Ensure the c function from Thurstone-Mosteller Full Pairing works as expected.
    """
    model = ThurstoneMostellerFull()
    r = model.rating
    team_1 = [r()]
    team_2 = [r(), r()]

    # Compute Values
    team_ratings = model._calculate_team_ratings([team_1, team_2])
    assert model._c(team_ratings) == pytest.approx(15.590239, 0.00000001)

    # Compute 5 v 5
    team_ratings = model._calculate_team_ratings(
        [[r(), r(), r(), r(), r()], [r(), r(), r(), r(), r()]]
    )
    assert model._c(team_ratings) == pytest.approx(27.003, 0.00001)


def test_a():
    """
    Ensure the `a` function from Thurstone-Mosteller Full Pairing works as expected.
    """
    model = ThurstoneMostellerFull()
    r = model.rating
    team_1 = [r()]
    team_2 = [r(), r()]
    team_3 = [r(), r()]
    team_4 = [r()]

    # Compute Values
    ratings = model._calculate_team_ratings([team_1, team_2])
    assert model._a(ratings) == [1, 1]

    # 1 Team per Rank
    ratings = model._calculate_team_ratings([team_1, team_2, team_3, team_4])
    assert model._a(ratings) == [1, 1, 1, 1]

    # Count how many share the rank
    ratings = model._calculate_team_ratings(
        [team_1, team_2, team_3, team_4], ranks=[1, 1, 1, 4]
    )
    assert model._a(ratings) == [3, 3, 3, 1]


def test_sum_q() -> None:
    """
    Ensure the summation of `mu/c` raised to `e` works normally.
    """
    model = ThurstoneMostellerFull()
    r = model.rating
    team_1 = [r()]
    team_2 = [r(), r()]

    # Compute Values
    ratings = model._calculate_team_ratings([team_1, team_2])
    c = model._c(ratings)
    assert model._sum_q(ratings, c) == [29.67892702634643, 24.70819334370875]

    # 5 v 5
    ratings = model._calculate_team_ratings(
        [[r(), r(), r(), r(), r()], [r(), r(), r(), r(), r()]]
    )
    c = model._c(ratings)
    sum_q = model._sum_q(ratings, c)
    assert sum_q[0] == pytest.approx(204.84, 0.0001)
    assert sum_q[1] == pytest.approx(102.42, 0.0001)


def test_gamma() -> None:
    """
    Ensure the default gamma function works normally.
    """
    model = ThurstoneMostellerFull()
    r = model.rating
    team = [r(), r(), r(), r(), r()]

    assert _gamma(2, 2, 3, 4, team, 0) == pytest.approx(1)
    assert _gamma(2, 2, 3, 16, team, 0) == pytest.approx(2)
    assert _gamma(2, 2, 3, 64, team, 1) == pytest.approx(4)


def check_expected(
    data, data_key: str, results: List[List[ThurstoneMostellerFullRating]]
) -> None:
    """
    Checks the expected results against the results from the model.

    :param data: The JSON data to check against.
    :param data_key: The JSON identifier for the data.
    :param results: The results from the model.
    """
    teams_type = data[data_key]
    for team_index, team in enumerate(results):
        for player_index, player in enumerate(team):
            assert player.mu == pytest.approx(
                teams_type[f"team_{team_index + 1}"][player_index]["mu"], 0.0001
            )
            assert player.sigma == pytest.approx(
                teams_type[f"team_{team_index + 1}"][player_index]["sigma"], 0.0001
            )


def test_rate() -> None:
    # Load Expected Data
    file_path = (
        pathlib.Path(__file__).parent.parent.resolve()
        / "data"
        / "thurstonemostellerfull.json"
    )
    with open(file_path, "r") as f:
        data = json.load(f)

    mu = data["model"]["mu"]
    sigma = data["model"]["sigma"]
    model = ThurstoneMostellerFull(mu, sigma)
    r = model.rating
    team_1 = [r()]
    team_2 = [r(), r()]

    results_normal = model.rate(teams=[team_1, team_2])
    check_expected(data, "normal", results_normal)

    team_1 = [r()]
    team_2 = [r(), r()]
    team_3 = [r()]
    team_4 = [r(), r()]

    results_ranks = model.rate(
        teams=[team_1, team_2, team_3, team_4], ranks=[2, 1, 4, 3]
    )
    check_expected(data, "ranks", results_ranks)

    team_1 = [r()]
    team_2 = [r(), r()]

    results_scores = model.rate(teams=[team_1, team_2], scores=[1, 2])
    check_expected(data, "scores", results_scores)

    team_1 = [r()]
    team_2 = [r(), r()]
    team_3 = [r(), r(), r()]

    results_limit_sigma = model.rate(
        teams=[team_1, team_2, team_3], ranks=[2, 1, 3], limit_sigma=True
    )
    check_expected(data, "limit_sigma", results_limit_sigma)

    # Test Ties
    team_1 = [r()]
    team_2 = [r(), r()]
    team_3 = [r(), r(), r()]

    results_ties = model.rate(teams=[team_1, team_2, team_3], ranks=[1, 2, 1])
    check_expected(data, "ties", results_ties)

    # Test Weights
    team_1 = [r(), r(), r()]
    team_2 = [r(), r()]
    team_3 = [r(), r(), r()]
    team_4 = [r(), r()]

    results_weights = model.rate(
        teams=[team_1, team_2, team_3, team_4],
        ranks=[2, 1, 4, 3],
        weights=[[2, 0, 0], [1, 2], [0, 0, 1], [0, 1]],
    )
    check_expected(data, "weights", results_weights)

    # Test Balance
    team_1 = [r(), r()]
    team_2 = [r(), r()]

    model = ThurstoneMostellerFull(mu, sigma, balance=True)
    results_balance = model.rate(teams=[team_1, team_2], ranks=[1, 2])
    check_expected(data, "balance", results_balance)


def test_rate_errors() -> None:
    """
    Manual testing of the rating function errors.
    """
    model = ThurstoneMostellerFull()
    r = model.rating
    team_1 = [r()]
    team_2 = [r(), r()]
    team_3 = [r(), r(), r()]

    with pytest.raises(TypeError):
        model.rate(teams=())  # type: ignore

    with pytest.raises(TypeError):
        model.rate(teams=[21, 21])  # type: ignore

    with pytest.raises(TypeError):
        model.rate(teams=[[r(), 21], team_2])  # type: ignore

    with pytest.raises(TypeError):
        model.rate(teams=[team_1, team_2, team_3], ranks=21)  # type: ignore

    with pytest.raises(TypeError):
        model.rate(teams=[team_1, team_2, team_3], ranks=[21, "abc", 23])

    with pytest.raises(ValueError):
        model.rate(teams=[team_1, team_2], ranks=[2, 1], scores=[2, 1])

    with pytest.raises(TypeError):
        model.rate(teams=[team_1, team_2, team_3], scores=21)  # type: ignore

    with pytest.raises(TypeError):
        model.rate(teams=[team_1, team_2, team_3], scores=[21, "abc", 23])

    with pytest.raises(ValueError):
        model.rate(teams=[team_1, team_2], ranks=[2, 1], weights=[[10, 5], [10, 5]])

    with pytest.raises(ValueError):
        model.rate(teams=[team_1, team_2], ranks=[2, 1], weights=[10, 5, 5])  # type: ignore

    with pytest.raises(TypeError):
        model.rate(teams=[team_1, team_2], ranks=[2, 1], weights=[[10], [10, "5"]])

    with pytest.raises(TypeError):
        model.rate(teams=[team_1, team_2], ranks=[2, 1], weights=21)  # type: ignore

    with pytest.raises(TypeError):
        model.rate(teams=[team_1, team_2], ranks=[2, 1], weights=[[10], "5"])

    with pytest.raises(ValueError):
        model.rate(
            teams=[team_1, team_2], ranks=[2, 1], weights=[[10], [10, 5], [1, 2, 50]]
        )

    # Make sure this doesn't result in an error
    [[_], [_, _]] = model.rate(
        teams=[team_1, team_2], ranks=[2, 1], weights=[[5], [5, 10]]
    )

    # Prevents sigma from rising
    a = r(mu=40, sigma=3)
    b = r(mu=-20, sigma=3)
    [[winner], [loser]] = model.rate([[a], [b]], tau=0.3, limit_sigma=True)
    assert winner.sigma <= a.sigma
    assert loser.sigma <= b.sigma

    # Ensures sigma does not increase
    a = r()
    b = r()
    [[winner], [loser]] = model.rate([[a], [b]], tau=0.3, limit_sigma=True)
    assert winner.sigma <= a.sigma
    assert loser.sigma <= b.sigma

    # Test ValueError
    team_1 = [r()]
    team_2 = [r(), r()]
    team_3 = [r(), r(), r()]

    with pytest.raises(ValueError):
        model.rate(teams=[team_1, team_2, team_3], ranks=[21, "abc"])

    with pytest.raises(ValueError):
        model.rate(teams=[team_1, team_2, team_3], scores=[21, "abc"])

    with pytest.raises(ValueError):
        model.rate(teams=[])

    with pytest.raises(ValueError):
        model.rate(teams=[[], []])

    with pytest.raises(ValueError):
        model.rate(teams=[[]])

    with pytest.raises(ValueError):
        model.rate(teams=[team_1])


def test_predict_win():
    """
    Ensure the predict_win function works normally.
    """
    model = ThurstoneMostellerFull()
    r = model.rating
    a1 = r()
    a2 = r(mu=32.444, sigma=5.123)

    b1 = r(73.381, 1.421)
    b2 = r(mu=25.188, sigma=6.211)

    team_1 = [a1, a2]
    team_2 = [b1, b2]

    probabilities = model.predict_win(teams=[team_1, team_2, [a2], [a1], [b1]])
    assert sum(probabilities) == pytest.approx(1, 0.0001)

    probabilities = model.predict_win(teams=[team_1, team_2])
    assert sum(probabilities) == pytest.approx(1, 0.0001)

    with pytest.raises(ValueError):
        model.predict_win(teams=[team_1])


def test_predict_5p_impostor():
    """
    Detects impostor in a 5p game.
    """
    model = ThurstoneMostellerFull()
    r = model.rating
    a1 = r()
    a2 = r(mu=32.444, sigma=5.123)
    p1, p2, p3, p4, p5 = model.predict_win(teams=[[a1], [a1], [a1], [a2], [a1]])
    assert sorted([p1, p2, p3, p4, p5])[4] == p4


def test_predict_draw():
    """
    Ensure the predict_draw function works normally.
    """
    model = ThurstoneMostellerFull()
    r = model.rating
    a1 = r()
    a2 = r(mu=32.444, sigma=1.123)

    b1 = r(35.881, 0.0001)
    b2 = r(mu=25.188, sigma=0.00001)

    team_1 = [a1, a2]
    team_2 = [b1, b2]

    probability = model.predict_draw(teams=[team_1, team_2])
    assert probability == pytest.approx(0.1694772, 0.0001)

    probability = model.predict_draw(teams=[team_1, team_2, [a1], [a2], [b1]])
    assert probability == pytest.approx(0.0518253, 0.0001)

    probability = model.predict_draw(teams=[[b1], [b1]])
    assert probability == pytest.approx(0.5)

    with pytest.raises(ValueError):
        model.predict_draw(teams=[team_1])


def test_predict_rank():
    """
    Ensure the predict_rank function works normally.
    """
    model = ThurstoneMostellerFull()
    r = model.rating

    a1 = r(mu=34, sigma=0.25)
    a2 = r(mu=32, sigma=0.25)
    a3 = r(mu=30, sigma=0.25)

    b1 = r(mu=24, sigma=0.5)
    b2 = r(mu=22, sigma=0.5)
    b3 = r(mu=20, sigma=0.5)

    team_1 = [a1, b1]
    team_2 = [a2, b2]
    team_3 = [a3, b3]

    # Test predict_rank
    ranks = model.predict_rank(teams=[team_1, team_2, team_3])
    total_rank_probability = sum([y for x, y in ranks])
    assert total_rank_probability == pytest.approx(1)

    # Test with identical teams
    identical_ranks = model.predict_rank(teams=[team_1, team_1, team_1])
    identical_total_rank_probability = sum([y for x, y in identical_ranks])
    assert identical_total_rank_probability == pytest.approx(1)

    with pytest.raises(ValueError):
        model.predict_rank(teams=[team_1])
