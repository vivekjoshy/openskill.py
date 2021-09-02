from openskill.statistics import v


def test_v():
    assert v(1, 2) == 1.525135276160981
    assert v(0, 2) == 2.373215532822843
    assert v(0, -1) == 0.2875999709391784
    assert v(0, 10) == 10
