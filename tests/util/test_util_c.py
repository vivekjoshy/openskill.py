import pytest

from openskill import Rating, team_rating
from openskill.util import util_c

r = Rating()
team_1 = [r]
team_2 = [r, r]


def test_util_c():
    # Compute Values
    team_ratings = team_rating([team_1, team_2])
    assert util_c(team_ratings) == pytest.approx(15.590239, 0.00000001)

    # Compute 5 v 5
    team_ratings = team_rating([[r, r, r, r, r], [r, r, r, r, r]])
    assert util_c(team_ratings) == pytest.approx(27.003, 0.00001)
