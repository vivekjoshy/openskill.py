import pytest

from openskill import Rating, team_rating
from openskill.util import util_c, util_sum_q

r = Rating()
team_1 = [r]
team_2 = [r, r]


def test_util_sum_q():
    # Compute Values
    ratings = team_rating([team_1, team_2])
    c = util_c(ratings)
    assert util_sum_q(ratings, c) == [29.67892702634643, 24.70819334370875]

    # 5 v 5
    ratings = team_rating([[r, r, r, r, r], [r, r, r, r, r]])
    c = util_c(ratings)
    sum_q = util_sum_q(ratings, c)
    assert sum_q[0] == pytest.approx(204.84, 0.0001)
    assert sum_q[1] == pytest.approx(102.42, 0.0001)
