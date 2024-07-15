"""
Tests common for all models.
"""

from openskill.models import MODELS
from openskill.models.common import _matrix_transpose, _normalize, _unary_minus


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


def test_normalize() -> None:
    """
    Tests the :code:`_normalize` function.
    """
    assert _normalize([1, 2, 3], 0, 1) == [0.0, 0.5, 1.0]
    assert _normalize([1, 2, 3], 0, 100) == [0.0, 50.0, 100.0]
    assert _normalize([1, 2, 3], 0, 10) == [0.0, 5.0, 10.0]
    assert _normalize([1, 2, 3], 1, 0) == [1.0, 0.5, 0.0]
    assert _normalize([1, 1, 1], 0, 1) == [0.0, 0.0, 0.0]
