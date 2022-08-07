import pytest

from openskill.statistics import v


def test_v():
    assert v(1, 2) == pytest.approx(1.525135276160981)
    assert v(0, 2) == pytest.approx(2.373215532822843)
    assert v(0, -1) == pytest.approx(0.2875999709391784)
    assert v(0, 10) == 10
