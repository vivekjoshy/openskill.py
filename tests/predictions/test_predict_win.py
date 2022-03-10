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


def test_predict_win_1v1():
    a1 = Rating()
    a2 = Rating(mu=32.444, sigma=5.123)
    b1 = Rating(mu=73.381, sigma=1.421)
    b2 = Rating(mu=25.188, sigma=6.211)
    team1 = [a1, a2]
    team2 = [b1, b2]

    prob1, prob2 = predict_win(teams=[team1, team2])
    assert prob1 == pytest.approx(0.34641823958165474)
    assert prob2 == pytest.approx(0.6535817604183453)


def test_predict_win_asymmetric():
    a1 = Rating()
    a2 = Rating(mu=32.444, sigma=5.123)
    b1 = Rating(mu=73.381, sigma=1.421)
    b2 = Rating(mu=25.188, sigma=6.211)
    team1 = [a1, a2]
    team2 = [b1, b2]
    prob1, prob2, prob3, prob4 = predict_win(teams=[team1, team2, [a2], [b2]])
    assert prob1 == pytest.approx(0.2613515941642222)
    assert prob2 == pytest.approx(0.41117430943389155)
    assert prob3 == pytest.approx(0.1750905983112395)
    assert prob4 == pytest.approx(0.15238349809064686)


def test_predict_win_3p_ffa():
    a1 = Rating()
    prob1, prob2, prob3 = predict_win(teams=[[a1], [a1], [a1]])
    assert prob1 == pytest.approx(0.333333333333)
    assert prob2 == pytest.approx(0.333333333333)
    assert prob3 == pytest.approx(0.333333333333)


def test_predict_win_4p_ffa():
    a1 = Rating()
    p1, p2, p3, p4 = predict_win(teams=[[a1], [a1], [a1], [a1]])
    assert p1 == pytest.approx(0.25)
    assert p2 == pytest.approx(0.25)
    assert p3 == pytest.approx(0.25)
    assert p4 == pytest.approx(0.25)


def test_predict_win_4p_varying_skill():
    r1 = Rating(mu=1, sigma=0.1)
    r2 = Rating(mu=2, sigma=0.1)
    r3 = Rating(mu=3, sigma=0.1)
    r4 = Rating(mu=4, sigma=0.1)
    p1, p2, p3, p4 = predict_win(teams=[[r1], [r2], [r3], [r4]])
    assert p1 == pytest.approx(0.2028051110543726)
    assert p2 == pytest.approx(0.23419421333676907)
    assert p3 == pytest.approx(0.2658057866632309)
    assert p4 == pytest.approx(0.29719488894562746)


def test_predict_win_5p_ffa():
    a1 = Rating()
    p1, p2, p3, p4, p5 = predict_win(teams=[[a1], [a1], [a1], [a1], [a1]])
    assert p1 == pytest.approx(0.2)
    assert p2 == pytest.approx(0.2)
    assert p3 == pytest.approx(0.2)
    assert p4 == pytest.approx(0.2)
    assert p5 == pytest.approx(0.2)


def test_predict_5p_impostor():
    a1 = Rating()
    a2 = Rating(mu=32.444, sigma=5.123)
    p1, p2, p3, p4, p5 = predict_win(teams=[[a1], [a1], [a1], [a2], [a1]])
    assert p1 == pytest.approx(0.196037416522638)
    assert p2 == pytest.approx(0.196037416522638)
    assert p3 == pytest.approx(0.196037416522638)
    assert p4 == pytest.approx(0.21585034503812)
    assert p5 == pytest.approx(0.196037416522638)
