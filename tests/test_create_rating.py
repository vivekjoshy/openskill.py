import pytest

from openskill import Rating, create_rating


def test_create_rating():
    r = Rating()

    assert create_rating([25, 25 / 3]) == r

    with pytest.raises(TypeError):
        create_rating(5)

    with pytest.raises(ValueError):
        create_rating([1, "dj"])

    with pytest.raises(TypeError):
        create_rating(r)

    with pytest.raises(TypeError):
        create_rating("shshsh")
