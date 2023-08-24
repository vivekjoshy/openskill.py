"""
Tests common for all models.
"""
from models import MODELS
from openskill.models.common import (
    _arg_sort,
    _matrix_transpose,
    _rank_data,
    _unary_minus,
)


def test_model_rating() -> None:
    """
    Checks the cases where Falsy values are passed into rating methods.
    """
    for model in MODELS:
        model = model(sigma=21)
        player = model.rating(mu=0)
        assert player.sigma == 21
        assert player.mu == 0

    for model in MODELS:
        model = model(mu=22)
        player = model.rating(sigma=0)
        assert player.sigma == 0
        assert player.mu == 22


def test_unary_minus() -> None:
    """
    Tests the :code:`_unary_minus` function.
    """
    assert _unary_minus(1) == -1
    assert _unary_minus(-1) == 1
    assert _unary_minus(0) == 0
    assert _unary_minus(1.0) == -1.0
    assert _unary_minus(-1.0) == 1.0
    assert _unary_minus(0.0) == 0.0


def test_arg_sort() -> None:
    """
    Tests the :code:`_arg_sort` function.
    """
    assert _arg_sort([1, 2, 3]) == [0, 1, 2]
    assert _arg_sort([3, 2, 1]) == [2, 1, 0]
    assert _arg_sort([1, 3, 2]) == [0, 2, 1]
    assert _arg_sort([1, 1, 1]) == [0, 1, 2]
    assert _arg_sort([1, 1, 2]) == [0, 1, 2]
    assert _arg_sort([1, 2, 1]) == [0, 2, 1]


def test_rank_data() -> None:
    """
    Tests the :code:`_rank_data` function.
    """
    assert _rank_data([1, 2, 3]) == [1, 2, 3]
    assert _rank_data([3, 2, 1]) == [3, 2, 1]
    assert _rank_data([1, 3, 2]) == [1, 3, 2]
    assert _rank_data([1, 1, 1]) == [1, 1, 1]
    assert _rank_data([1, 1, 3]) == [1, 1, 3]
    assert _rank_data([1, 2, 3, 3, 3, 4]) == [1, 2, 3, 3, 3, 6]
    assert _rank_data([1, 2, 2, 3, 3, 4]) == [1, 2, 2, 4, 4, 6]


def test_matrix_transpose() -> None:
    """
    Tests the :code:`_matrix_transpose` function.
    """
    assert _matrix_transpose([[1, 2, 3]]) == [[1], [2], [3]]
    assert _matrix_transpose([[1], [2], [3]]) == [[1, 2, 3]]
    assert _matrix_transpose([[1, 2, 3], [4, 5, 6]]) == [[1, 4], [2, 5], [3, 6]]
    assert _matrix_transpose([[1, 2], [3, 4], [5, 6]]) == [[1, 3, 5], [2, 4, 6]]
    assert _matrix_transpose([[1, 2, 3], [4, 5, 6], [7, 8, 9]]) == [
        [1, 4, 7],
        [2, 5, 8],
        [3, 6, 9],
    ]
    assert _matrix_transpose([[1, 2], [3, 4]]) == [[1, 3], [2, 4]]
