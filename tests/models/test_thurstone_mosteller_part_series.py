import pytest

from openskill import Rating, rate
from openskill.models import ThurstoneMostellerPart


def test_thurstone_mosteller_part_series():
    p00 = Rating()
    p10 = Rating()
    p20 = Rating()
    p30 = Rating()
    p40 = Rating()

    result = rate(
        [[p00], [p10], [p20], [p30], [p40]],
        score=[9, 7, 7, 5, 5],
        epsilon=0.1,
        gamma=lambda *_: 1,
        model=ThurstoneMostellerPart,
    )
    [[p01], [p11], [p21], [p31], [p41]] = result

    assert p01.mu == pytest.approx(27.108980741)
    assert p01.sigma == pytest.approx(8.063357519)
    assert p11.mu == pytest.approx(22.891019259)
    assert p11.sigma == pytest.approx(7.620583708)
    assert p21.mu == pytest.approx(27.108980741)
    assert p21.sigma == pytest.approx(7.620583708)
    assert p31.mu == pytest.approx(22.891019259)
    assert p31.sigma == pytest.approx(7.620583708)
    assert p41.mu == pytest.approx(25.0)
    assert p41.sigma == pytest.approx(7.905694531)
