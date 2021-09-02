import pytest

from openskill.statistics import vt


def test_vt():
    assert vt(-1000, -100) == 1100
    assert vt(1000, -100) == -1100
    assert vt(-1000, 1000) == pytest.approx(0.79788, 0.00001)
    assert vt(0, 1000) == 0
