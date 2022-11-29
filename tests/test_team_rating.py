import pytest

from openskill import Rating, team_rating

r = Rating()
team_1 = [r]
team_2 = [r, r]


def test_team_rating():
    # Aggregates all players in a team
    result = team_rating([team_1, team_2])
    assert result == [
        [25, 69.44444444444446, team_1, 0],
        [50, 138.8888888888889, team_2, 1],
    ]

    # 5 v 5
    result = team_rating([[r, r, r, r, r], [r, r, r, r, r]])
    assert result[0][0] == pytest.approx(125)
    assert result[1][0] == pytest.approx(125)
    assert result[0][1] == pytest.approx(347.22, 0.00001)
    assert result[1][1] == pytest.approx(347.22, 0.00001)
