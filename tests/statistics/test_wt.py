import pytest

from openskill.statistics import wt


def test_wt():
    assert wt(1, 2) == pytest.approx(0.3838582646421707)
    assert wt(0, 2) == pytest.approx(0.2262586964500768)
    assert wt(0, -1) == 1
    assert wt(0, 0) == 1.0
    assert wt(0, 10) == pytest.approx(0)
