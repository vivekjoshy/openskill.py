import pytest

from openskill import Rating
from openskill.rate import predict_draw


def test_predict_draw():
    a1 = Rating()
    a2 = Rating(mu=32.444, sigma=1.123)

    b1 = Rating(35.881, 0.0001)
    b2 = Rating(mu=25.188, sigma=1.421)

    team_1 = [a1, a2]
    team_2 = [b1, b2]

    probability = predict_draw(teams=[team_1, team_2])
    assert probability == pytest.approx(0.1260703143635969)

    probability = predict_draw(teams=[team_1, team_2, [a1], [a2], [b1]])
    assert probability == pytest.approx(0.04322122887507519)

    probability = predict_draw(teams=[[b1], [b1]])
    assert probability == pytest.approx(1)

    with pytest.raises(ValueError):
        predict_draw(teams=[team_1])
