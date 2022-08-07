from openskill import Rating, rate
from openskill.models import ThurstoneMostellerPart
from tests import approx

r = Rating()
team_1 = [r]
team_2 = [r, r]
team_3 = [r, r, r]


def test_thurstone_mosteller_full():
    assert approx(rate([team_1], model=ThurstoneMostellerPart), [team_1])

    # 2P FFA
    assert approx(
        rate([team_1, team_1], model=ThurstoneMostellerPart),
        [
            [[27.10261680121866, 8.249024727693394]],
            [[22.89738319878134, 8.249024727693394]],
        ],
    )

    # 3P FFA
    assert approx(
        rate([team_1, team_1, team_1], model=ThurstoneMostellerPart),
        [
            [[27.10261680121866, 8.249024727693394]],
            [[25.0, 8.163845507587077]],
            [[22.89738319878134, 8.249024727693394]],
        ],
    )

    # 4P FFA
    assert approx(
        rate([team_1, team_1, team_1, team_1], model=ThurstoneMostellerPart),
        [
            [[27.10261680121866, 8.249024727693394]],
            [[25.0, 8.163845507587077]],
            [[25.0, 8.163845507587077]],
            [[22.89738319878134, 8.249024727693394]],
        ],
    )

    # 5P FFA
    assert approx(
        rate([team_1, team_1, team_1, team_1, team_1], model=ThurstoneMostellerPart),
        [
            [[27.10261680121866, 8.249024727693394]],
            [[25.0, 8.163845507587077]],
            [[25.0, 8.163845507587077]],
            [[25.0, 8.163845507587077]],
            [[22.89738319878134, 8.249024727693394]],
        ],
    )

    # 3 Different Sized Teams
    assert approx(
        rate([team_3, team_1, team_2], model=ThurstoneMostellerPart),
        [
            [
                [25.312878118346458, 8.309613085350666],
                [25.312878118346458, 8.309613085350666],
                [25.312878118346458, 8.309613085350666],
            ],
            [[27.735657070878023, 8.257580571375808]],
            [
                [21.95146481077552, 8.245567442404347],
                [21.95146481077552, 8.245567442404347],
            ],
        ],
    )

    # Can use a custom gamma with k=2
    assert approx(
        rate(
            [team_1, team_1], gamma=lambda c, k, *_: 1 / k, model=ThurstoneMostellerPart
        ),
        [
            [[27.10261680121866, 8.19963147044701]],
            [[22.89738319878134, 8.19963147044701]],
        ],
    )

    # Can use a custom gamma with k=5
    assert approx(
        rate(
            [team_1, team_1, team_1, team_1, team_1],
            gamma=lambda c, k, *_: 1 / k,
            model=ThurstoneMostellerPart,
        ),
        [
            [[27.10261680121866, 8.280111663928492]],
            [[25.0, 8.226545683931066]],
            [[25.0, 8.226545683931066]],
            [[25.0, 8.226545683931066]],
            [[22.89738319878134, 8.280111663928492]],
        ],
    )
