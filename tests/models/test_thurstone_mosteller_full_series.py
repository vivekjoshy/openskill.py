import pytest

from openskill import Rating, rate
from openskill.models import ThurstoneMostellerFull


def test_thurstone_mosteller_full_series():
    p00 = Rating()
    p10 = Rating()
    p20 = Rating()
    p30 = Rating()
    p40 = Rating()

    result = rate(
        [[p00], [p10], [p20], [p30], [p40]],
        score=[9, 7, 7, 5, 5],
        epsilon=0.1,
        model=ThurstoneMostellerFull,
    )
    [[p01], [p11], [p21], [p31], [p41]] = result

    p02 = p01
    p32 = p31
    result = rate(
        [[p41], [p21], [p11]],
        score=[9, 5, 5],
        epsilon=0.1,
        model=ThurstoneMostellerFull,
    )
    [[p42], [p22], [p12]] = result

    p43 = p42
    result = rate(
        [[p32], [p12], [p22], [p02]],
        score=[9, 9, 7, 7],
        epsilon=0.1,
        model=ThurstoneMostellerFull,
    )
    [[p33], [p13], [p23], [p03]] = result

    assert p03.mu == pytest.approx(18.688153436)
    assert p03.sigma == pytest.approx(3.374349435)
    assert p13.mu == pytest.approx(27.015047867)
    assert p13.sigma == pytest.approx(3.250038289)
    assert p23.mu == pytest.approx(22.825795022)
    assert p23.sigma == pytest.approx(3.261730104)
    assert p33.mu == pytest.approx(27.281612237)
    assert p33.sigma == pytest.approx(3.387011242)
    assert p43.mu == pytest.approx(22.633338874)
    assert p43.sigma == pytest.approx(3.747505007)
