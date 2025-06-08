"""
All tests common for Weng-Lin models are located here.
"""

import random
from typing import Any, List

import pytest

from openskill.models import MODELS
from openskill.models.weng_lin.common import _ladder_pairs, _unwind, v, vt, w, wt


@pytest.mark.parametrize("model", MODELS)
def test_calculate_team_ratings(model) -> None:
    """
    Tests the :code:`_calculate_team_ratings` function.
    """

    model = model()
    r = model.rating
    team_1 = [r()]
    team_2 = [r(), r()]

    # Aggregates all players in a team
    result = model._calculate_team_ratings([team_1, team_2])
    assert result[0].mu == pytest.approx(25)
    assert result[1].mu == pytest.approx(50)
    assert result[0].sigma_squared == pytest.approx(69.44444)
    assert result[1].sigma_squared == pytest.approx(138.88888)
    assert result[0].team == team_1
    assert result[1].team == team_2
    assert result[0].rank == 0
    assert result[1].rank == 1

    # 5 v 5
    result = model._calculate_team_ratings(
        [[r(), r(), r(), r(), r()], [r(), r(), r(), r(), r()]]
    )
    assert result[0].mu == pytest.approx(125)
    assert result[1].mu == pytest.approx(125)
    assert result[0].sigma_squared == pytest.approx(347.2222222)
    assert result[1].sigma_squared == pytest.approx(347.2222222)

    # 5 v 5 v 5 with ranks
    result = model._calculate_team_ratings(
        game=[
            [r(), r(), r(), r(), r()],
            [r(), r(), r(), r(), r()],
            [r(), r(), r(), r(), r()],
        ],
        ranks=[3, 1, 2],
    )
    assert result[0].mu == pytest.approx(125)
    assert result[1].mu == pytest.approx(125)
    assert result[2].mu == pytest.approx(125)
    assert result[0].sigma_squared == pytest.approx(347.2222222)
    assert result[1].sigma_squared == pytest.approx(347.2222222)
    assert result[2].sigma_squared == pytest.approx(347.2222222)


@pytest.mark.parametrize("model", MODELS)
def test_calculate_rankings(model) -> None:
    """
    Tests the :code:`_calculate_rankings` function.
    """
    model = model()
    r = model.rating

    # Generate a 5 player team
    team_1 = [r(), r(), r(), r(), r()]

    # Generate 5 players overall for single player teams
    a = [r()]
    b = [r()]
    c = [r()]
    d = [r()]
    e = [r()]

    # Conduct Tests
    assert model._calculate_rankings([]) == []
    assert model._calculate_rankings([], []) == []
    assert model._calculate_rankings([a, b, c, d]) == [0, 1, 2, 3]
    assert model._calculate_rankings([a, b], [0, 0]) == [0, 0]
    assert model._calculate_rankings([a, b, c, d], [1, 2, 3, 4]) == [0, 1, 2, 3]
    assert model._calculate_rankings([a, b, c, d], [1, 1, 3, 4]) == [0, 0, 2, 3]
    assert model._calculate_rankings([a, b, c, d], [1, 2, 3, 3]) == [0, 1, 2, 2]
    assert model._calculate_rankings([a, b, c, d], [1, 2, 2, 4]) == [0, 1, 1, 3]
    assert model._calculate_rankings([a, b, c, d, e], [14, 32, 47, 47, 48]) == [
        0,
        1,
        2,
        2,
        4,
    ]


def test_unwind() -> None:
    """
    Tests the :code:`_unwind` function.
    """
    # Zero Items
    source: List[Any] = []
    rank: List[Any] = []
    output, tenet = _unwind(rank, source)
    assert output == []
    assert tenet == []

    # Accepts 1 Item
    source = ["a"]
    rank = [0]
    output, tenet = _unwind(rank, source)
    assert output == ["a"]
    assert tenet == [0]

    # Accepts 2 Items
    source = ["b", "a"]
    rank = [1, 0]
    output, tenet = _unwind(rank, source)
    assert output == ["a", "b"]
    assert tenet == [1, 0]

    # Accepts 3 Items
    source = ["b", "c", "a"]
    rank = [1, 2, 0]
    output, tenet = _unwind(rank, source)
    assert output == ["a", "b", "c"]
    assert tenet == [2, 0, 1]

    # Accepts 4 Items
    source = ["b", "d", "c", "a"]
    rank = [1, 3, 2, 0]
    output, tenet = _unwind(rank, source)
    assert output == ["a", "b", "c", "d"]
    assert tenet == [3, 0, 2, 1]

    # Can undo the ranking
    source = [random.random() for _ in range(100)]
    random.shuffle(source)
    rank = [i for i in range(100)]
    trans, tenet = _unwind(rank, source)
    output, de_de_rank = _unwind(tenet, trans)
    assert source == output
    assert de_de_rank == rank

    # Allows ranks that are not zero-indexed integers
    source = ["a", "b", "c", "d", "e", "f"]
    rank = [0.28591, 0.42682, 0.35912, 0.21237, 0.60619, 0.47078]
    output, tenet = _unwind(rank, source)
    assert output == ["d", "a", "c", "b", "f", "e"]


def test_v() -> None:
    """
    Test the v function
    """
    assert v(1, 2) == pytest.approx(1.525135276160981, 0.00001)
    assert v(0, 2) == pytest.approx(2.373215532822843, 0.00001)
    assert v(0, -1) == pytest.approx(0.2875999709391784, 0.00001)
    assert v(0, 10) == 10


def test_vt() -> None:
    """
    Test the vt function
    """
    assert vt(-1000, -100) == 1100
    assert vt(1000, -100) == -1100
    assert vt(-1000, 1000) == pytest.approx(0.79788, 0.00001)
    assert vt(0, 1000) == 0


def test_w():
    """
    Test the w function
    """
    assert w(1, 2) == pytest.approx(0.800902334429651, 0.00001)
    assert w(0, 2) == pytest.approx(0.885720899585924, 0.00001)
    assert w(0, -1) == pytest.approx(0.3703137142233946, 0.00001)
    assert w(0, 10) == 0
    assert w(-1, 10) == 1


def test_wt():
    """
    Test the wt function
    """
    assert wt(1, 2) == pytest.approx(0.3838582646421707, 0.00001)
    assert wt(0, 2) == pytest.approx(0.2262586964500768, 0.00001)
    assert wt(0, -1) == 1
    assert wt(0, 0) == 1.0
    assert wt(0, 10) == pytest.approx(0)


def test_ladder_pairs():
    """
    Test the ladder_pairs function
    """
    assert _ladder_pairs([]) == [[]]
    assert _ladder_pairs([1]) == [[]]
    assert _ladder_pairs([1, 2]) == [[2], [1]]
    assert _ladder_pairs([1, 2, 3]) == [[2], [1, 3], [2]]
    assert _ladder_pairs([1, 2, 3, 4]) == [[2], [1, 3], [2, 4], [3]]
