import pytest

from openskill import Rating
from openskill.rate import predict_draw, predict_rank


def test_predict_rank():
    a1 = Rating(mu=34, sigma=0.25)
    a2 = Rating(mu=32, sigma=0.25)
    a3 = Rating(mu=34, sigma=0.25)

    b1 = Rating(mu=24, sigma=0.5)
    b2 = Rating(mu=22, sigma=0.5)
    b3 = Rating(mu=20, sigma=0.5)

    team_1 = [a1, b1]
    team_2 = [a2, b2]
    team_3 = [a3, b3]

    ranks = predict_rank(teams=[team_1, team_2, team_3])
    total_rank_probability = sum([y for x, y in ranks])
    draw_probability = predict_draw(teams=[team_1, team_2, team_3])
    assert total_rank_probability + draw_probability == pytest.approx(1)

    with pytest.raises(ValueError):
        predict_rank(teams=[team_1])
