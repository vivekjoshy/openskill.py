import pytest

from openskill import Rating, predict_win


def test_predict_win():
    a1 = Rating()
    a2 = Rating(mu=32.444, sigma=5.123)

    b1 = Rating(73.381, 1.421)
    b2 = Rating(mu=25.188, sigma=6.211)

    team_1 = [a1, a2]
    team_2 = [b1, b2]

    probabilities = predict_win(teams=[team_1, team_2, [a2], [a1], [b1]])
    assert sum(probabilities) == pytest.approx(1)

    probabilities = predict_win(teams=[team_1, team_2])
    assert sum(probabilities) == pytest.approx(1)

    with pytest.raises(ValueError):
        predict_win(teams=[team_1])
