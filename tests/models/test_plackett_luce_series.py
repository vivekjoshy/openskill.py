import pytest

from openskill import Rating, rate


def test_plackett_luce_series():
    p00 = Rating()
    p10 = Rating()
    p20 = Rating()
    p30 = Rating()
    p40 = Rating()

    result = rate([[p00], [p10], [p20], [p30], [p40]], score=[9, 7, 7, 5, 5])
    [[p01], [p11], [p21], [p31], [p41]] = result

    p02 = p01
    p32 = p31
    result = rate([[p41], [p21], [p11]], score=[9, 5, 5])
    [[p42], [p22], [p12]] = result

    p43 = p42
    result = rate([[p32], [p12], [p22], [p02]], score=[9, 9, 7, 7])
    [[p33], [p13], [p23], [p03]] = result

    assert p03.mu == pytest.approx(26.353761103)
    assert p03.sigma == pytest.approx(8.11102706)
    assert p13.mu == pytest.approx(24.618479789)
    assert p13.sigma == pytest.approx(7.90533551)
    assert p23.mu == pytest.approx(23.065819512)
    assert p23.sigma == pytest.approx(7.822005595)
    assert p33.mu == pytest.approx(24.476332403)
    assert p33.sigma == pytest.approx(8.106111471)
    assert p43.mu == pytest.approx(26.385499685)
    assert p43.sigma == pytest.approx(8.054090809)
