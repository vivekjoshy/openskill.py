import pytest

from openskill import Rating


def test_rating():
    assert Rating() == Rating()
    assert Rating(mu=32.124, sigma=1.421) == Rating(mu=32.124, sigma=1.421)
    assert Rating(mu=32.124, sigma=1.421) != Rating()
    assert Rating(mu=32.124, sigma=1.421) != [23.84, 3.443]
    assert Rating(mu=32.124, sigma=1.421) == [32.124, 1.421]

    assert Rating() <= Rating()
    assert Rating() >= Rating()
    assert Rating(mu=32.124, sigma=1.421) > [23.84, 3.443]
    assert Rating(mu=32.124, sigma=1.421) > Rating(mu=23.84, sigma=3.443)
    assert Rating(mu=23.84, sigma=3.443) < [32.124, 1.421]
    assert [23.84, 3.443] < Rating(mu=32.124, sigma=1.421)
    assert Rating(mu=23.84, sigma=3.443) < Rating(mu=32.124, sigma=1.421)
    assert [23.84, 3.443] <= Rating(mu=32.124, sigma=1.421)
    assert Rating(mu=23.84, sigma=3.443) <= [32.124, 1.421]
    assert not (Rating(mu=32.124, sigma=1.421) < [23.84, 3.443])
    assert not (Rating(mu=32.124, sigma=1.421) < Rating(mu=23.84, sigma=3.443))
    assert not ([23.84, 3.443] > Rating(mu=32.124, sigma=1.421))
    assert not (Rating(mu=23.84, sigma=3.443) > Rating(mu=32.124, sigma=1.421))
    assert not (Rating(mu=23.84, sigma=3.443) > [32.124, 1.421])
    assert not (Rating(mu=32.124, sigma=1.421) <= Rating(mu=23.84, sigma=3.443))
    assert not (Rating(mu=32.124, sigma=1.421) <= [23.84, 3.443])
    assert not (Rating(mu=23.84, sigma=3.443) >= Rating(mu=32.124, sigma=1.421))
    assert not (Rating(mu=23.84, sigma=3.443) >= [32.124, 1.421])

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) == ["random_string", 5.6]

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) == [23.84, 3.443, 5.6]

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) == "random_string"

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) < ["random_string", 5.6]

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) < [23.84, 3.443, 5.6]

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) < "random_string"

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) > ["random_string", 5.6]

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) > [23.84, 3.443, 5.6]

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) > "random_string"

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) <= ["random_string", 5.6]

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) <= [23.84, 3.443, 5.6]

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) <= "random_string"

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) >= ["random_string", 5.6]

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) >= [23.84, 3.443, 5.6]

    with pytest.raises(ValueError):
        assert Rating(mu=32.124, sigma=1.421) >= "random_string"
