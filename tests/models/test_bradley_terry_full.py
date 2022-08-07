from openskill import Rating, rate
from openskill.models import BradleyTerryFull
from tests import approx

r = Rating()
team_1 = [r]
team_2 = [r, r]
team_3 = [r, r, r]


def test_bradley_terry_full():
    assert approx(rate([team_1], model=BradleyTerryFull), [team_1])

    # 2P FFA
    assert approx(
        rate([team_1, team_1], model=BradleyTerryFull),
        [
            [[27.63523138347365, 8.065506316323548]],
            [[22.36476861652635, 8.065506316323548]],
        ],
    )

    # 3P FFA
    assert approx(
        rate([team_1, team_1, team_1], model=BradleyTerryFull),
        [
            [[30.2704627669473, 7.788474807872566]],
            [[25.0, 7.788474807872566]],
            [[19.7295372330527, 7.788474807872566]],
        ],
    )

    # 4P FFA
    assert approx(
        rate([team_1, team_1, team_1, team_1], model=BradleyTerryFull),
        [
            [[32.90569415042095, 7.5012190693964005]],
            [[27.63523138347365, 7.5012190693964005]],
            [[22.36476861652635, 7.5012190693964005]],
            [[17.09430584957905, 7.5012190693964005]],
        ],
    )

    # 5P FFA
    assert approx(
        rate([team_1, team_1, team_1, team_1, team_1], model=BradleyTerryFull),
        [
            [[35.5409255338946, 7.202515895247076]],
            [[30.2704627669473, 7.202515895247076]],
            [[25.0, 7.202515895247076]],
            [[19.729537233052703, 7.202515895247076]],
            [[14.4590744661054, 7.202515895247076]],
        ],
    )

    # 3 Different Sized Teams
    assert approx(
        rate([team_3, team_1, team_2], model=BradleyTerryFull),
        [
            [
                [25.992743915179297, 8.19709997489984],
                [25.992743915179297, 8.19709997489984],
                [25.992743915179297, 8.19709997489984],
            ],
            [[28.48909130001799, 8.220848339985736]],
            [
                [20.518164784802718, 8.127515465304823],
                [20.518164784802718, 8.127515465304823],
            ],
        ],
    )

    # Can use a custom gamma with k=2
    assert approx(
        rate([team_1, team_1], gamma=lambda c, k, *_: 1 / k, model=BradleyTerryFull),
        [
            [[27.63523138347365, 8.122328620674137]],
            [[22.36476861652635, 8.122328620674137]],
        ],
    )

    # Can use a custom gamma with k=5
    assert approx(
        rate(
            [team_1, team_1, team_1, team_1, team_1],
            gamma=lambda c, k, *_: 1 / k,
            model=BradleyTerryFull,
        ),
        [
            [[35.5409255338946, 7.993052538854532]],
            [[30.2704627669473, 7.993052538854532]],
            [[25.0, 7.993052538854532]],
            [[19.729537233052703, 7.993052538854532]],
            [[14.4590744661054, 7.993052538854532]],
        ],
    )
