from openskill.util import score


def test_score():
    assert score(2, 1) == 1.0
    assert score(34, 6) == 1.0
    assert score(1, 2) == 0.0
    assert score(3, 58) == 0.0
    assert score(1, 1) == 0.5
