import pytest

from openskill.statistics import w


def test_w():
    assert w(1, 2) == pytest.approx(0.800902334429651)
    assert w(0, 2) == pytest.approx(0.885720899585924)
    assert w(0, -1) == pytest.approx(0.3703137142233946)
    assert w(0, 10) == 0
    assert w(-1, 10) == 1
