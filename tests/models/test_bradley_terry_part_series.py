import pytest

from openskill import Rating, rate
from openskill.models import BradleyTerryPart


def test_bradley_terry_part_series():
    p00 = Rating()
    p10 = Rating()
    p20 = Rating()
    p30 = Rating()
    p40 = Rating()

    result = rate(
        [[p00], [p10], [p20], [p30], [p40]],
        score=[9, 7, 7, 5, 5],
        model=BradleyTerryPart,
    )
    [[p01], [p11], [p21], [p31], [p41]] = result

    p02 = p01
    p32 = p31
    result = rate([[p41], [p21], [p11]], score=[9, 5, 5], model=BradleyTerryPart)
    [[p42], [p22], [p12]] = result

    p43 = p42
    result = rate(
        [[p32], [p12], [p22], [p02]], score=[9, 9, 7, 7], model=BradleyTerryPart
    )
    [[p33], [p13], [p23], [p03]] = result

    assert p03.mu == pytest.approx(27.303389976)
    assert p03.sigma == pytest.approx(7.786799495)
    assert p13.mu == pytest.approx(25.349369733)
    assert p13.sigma == pytest.approx(7.097135632)
    assert p23.mu == pytest.approx(22.388557102)
    assert p23.sigma == pytest.approx(6.9235932)
    assert p33.mu == pytest.approx(22.414946624)
    assert p33.sigma == pytest.approx(7.540451289)
    assert p43.mu == pytest.approx(27.834104352)
    assert p43.sigma == pytest.approx(7.80374707)
