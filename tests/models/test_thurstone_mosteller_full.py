from openskill import Rating, rate
from openskill.models import ThurstoneMostellerFull
from tests import approx

r = Rating()
team_1 = [r]
team_2 = [r, r]
team_3 = [r, r, r]


def test_thurstone_mosteller_full():
    assert approx(rate([team_1], model=ThurstoneMostellerFull), [team_1])

    # 2P FFA
    assert approx(
        rate([team_1, team_1], model=ThurstoneMostellerFull),
        [
            [[29.205246334857588, 7.632833420130952]],
            [[20.794753665142412, 7.632833420130952]],
        ],
    )

    # 3P FFA
    assert approx(
        rate([team_1, team_1, team_1], model=ThurstoneMostellerFull),
        [
            [[33.410492669715175, 6.861184124806115]],
            [[25.0, 6.861184124806115]],
            [[16.589507330284825, 6.861184124806115]],
        ],
    )

    # 4P FFA
    assert approx(
        rate([team_1, team_1, team_1, team_1], model=ThurstoneMostellerFull),
        [
            [[37.61573900457276, 5.990955614049813]],
            [[29.205246334857588, 5.990955614049813]],
            [[20.794753665142412, 5.990955614049813]],
            [[12.384260995427237, 5.990955614049813]],
        ],
    )

    # 5P FFA
    assert approx(
        rate([team_1, team_1, team_1, team_1, team_1], model=ThurstoneMostellerFull),
        [
            [[41.82098533943035, 4.970638866839803]],
            [[33.410492669715175, 4.970638866839803]],
            [[25.0, 4.970638866839803]],
            [[16.589507330284825, 4.970638866839803]],
            [[8.17901466056965, 4.970638866839803]],
        ],
    )

    # 3 Different Sized Teams
    assert approx(
        rate([team_3, team_1, team_2], model=ThurstoneMostellerFull),
        [
            [
                [25.72407717049428, 8.154234193613432],
                [25.72407717049428, 8.154234193613432],
                [25.72407717049428, 8.154234193613432],
            ],
            [[34.001083968844945, 7.757937033019591]],
            [
                [15.274838860660772, 7.373381567544504],
                [15.274838860660772, 7.373381567544504],
            ],
        ],
    )

    # Can use a custom gamma with k=2
    assert approx(
        rate(
            [team_1, team_1], gamma=lambda c, k, *_: 1 / k, model=ThurstoneMostellerFull
        ),
        [
            [[29.205246334857588, 7.784759481252749]],
            [[20.794753665142412, 7.784759481252749]],
        ],
    )

    # Can use a custom gamma with k=5
    assert approx(
        rate(
            [team_1, team_1, team_1, team_1, team_1],
            gamma=lambda c, k, *_: 1 / k,
            model=ThurstoneMostellerFull,
        ),
        [
            [[41.82098533943035, 7.436215544405679]],
            [[33.410492669715175, 7.436215544405679]],
            [[25.0, 7.436215544405679]],
            [[16.589507330284825, 7.436215544405679]],
            [[8.17901466056965, 7.436215544405679]],
        ],
    )

    # Works with ties in ranks
    assert approx(
        rate(
            [team_1, team_1, team_1, team_1, team_1],
            rank=[1, 2, 2, 4, 5],
            model=ThurstoneMostellerFull,
        ),
        [
            [[41.82098533943035, 4.970638866839803]],
            [[29.20528633485759, 4.280577057550792]],
            [[29.20528633485759, 4.280577057550792]],
            [[16.589507330284825, 4.970638866839803]],
            [[8.17901466056965, 4.970638866839803]],
        ],
    )
