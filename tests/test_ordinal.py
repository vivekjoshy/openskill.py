import pytest

from openskill import Rating, ordinal


def test_ordinal():
    r = Rating(mu=23.4, sigma=1.21)

    assert ordinal(agent=r) == 19.77
    assert ordinal(agent=[23.4, 1.21]) == 19.77

    with pytest.raises(ValueError):
        ordinal(agent=1)

    with pytest.raises(ValueError):
        ordinal(agent=[1])

    with pytest.raises(ValueError):
        ordinal(agent=[1, 2, 3])

    with pytest.raises(ValueError):
        ordinal(agent=[1, "random_string"])
