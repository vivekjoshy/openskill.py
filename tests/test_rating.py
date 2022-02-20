import pytest

from openskill import Rating


def test_rating():
    assert Rating() == Rating()
    assert Rating(mu=32.124, sigma=1.421) == Rating(mu=32.124, sigma=1.421)
    assert Rating(mu=32.124, sigma=1.421) != Rating()
    assert Rating(mu=32.124, sigma=1.421) != [23.84, 3.443]

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) == ["random_string", 5.6]

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) == [23.84, 3.443, 5.6]

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) == "random_string"
