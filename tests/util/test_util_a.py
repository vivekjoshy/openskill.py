from openskill import Rating, team_rating
from openskill.util import util_a

r = Rating()
team_1 = [r]
team_2 = [r, r]
team_3 = [r, r]
team_4 = [r]


def test_util_a():
    # Compute Values
    ratings = team_rating([team_1, team_2])
    assert util_a(ratings) == [1, 1]

    # 1 Team per Rank
    ratings = team_rating([team_1, team_2, team_3, team_4])
    assert util_a(ratings) == [1, 1, 1, 1]

    # Count how many share the rank
    ratings = team_rating([team_1, team_2, team_3, team_4], rank=[1, 1, 1, 4])
    assert util_a(ratings) == [3, 3, 3, 1]
