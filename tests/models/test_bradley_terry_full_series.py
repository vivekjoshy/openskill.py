import pytest

from openskill import Rating, create_rating, rate
from openskill.models import BradleyTerryFull


def test_bradley_terry_full_series():
    p00 = Rating()
    p10 = Rating()
    p20 = Rating()
    p30 = Rating()
    p40 = Rating()

    result = rate(
        [[p00], [p10], [p20], [p30], [p40]],
        score=[9, 7, 7, 5, 5],
        model=BradleyTerryFull,
    )
    [[p01], [p11], [p21], [p31], [p41]] = result
    p01 = create_rating(p01)
    p11 = create_rating(p11)
    p21 = create_rating(p21)
    p31 = create_rating(p31)
    p41 = create_rating(p41)

    p02 = p01
    p32 = p31
    result = rate([[p41], [p21], [p11]], score=[9, 5, 5], model=BradleyTerryFull)
    [[p42], [p22], [p12]] = result
    p42 = create_rating(p42)
    p22 = create_rating(p22)
    p12 = create_rating(p12)

    p43 = p42
    result = rate(
        [[p32], [p12], [p22], [p02]], score=[9, 9, 7, 7], model=BradleyTerryFull
    )
    [[p33], [p13], [p23], [p03]] = result
    p33 = create_rating(p33)
    p13 = create_rating(p13)
    p23 = create_rating(p23)
    p03 = create_rating(p03)

    assert p03.mu == pytest.approx(27.643471362)
    assert p03.sigma == pytest.approx(6.716636758)
    assert p13.mu == pytest.approx(28.84497938)
    assert p13.sigma == pytest.approx(6.310098392)
    assert p23.mu == pytest.approx(20.705805441)
    assert p23.sigma == pytest.approx(6.310098392)
    assert p33.mu == pytest.approx(24.387640207)
    assert p33.sigma == pytest.approx(6.668755907)
    assert p43.mu == pytest.approx(23.354955778)
    assert p43.sigma == pytest.approx(6.854096855)
