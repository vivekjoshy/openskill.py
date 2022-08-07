from openskill import Rating, rate
from openskill.models import BradleyTerryPart
from tests import approx

r = Rating()
team_1 = [r]
team_2 = [r, r]
team_3 = [r, r, r]


def test_bradley_terry_part():
    assert approx(rate([team_1], model=BradleyTerryPart), [team_1])

    # 2P FFA
    assert approx(
        rate([team_1, team_1], model=BradleyTerryPart),
        [
            [[27.63523138347365, 8.065506316323548]],
            [[22.36476861652635, 8.065506316323548]],
        ],
    )

    # 3P FFA
    assert approx(
        rate([team_1, team_1, team_1], model=BradleyTerryPart),
        [
            [[27.63523138347365, 8.065506316323548]],
            [[25.0, 7.788474807872566]],
            [[22.36476861652635, 8.065506316323548]],
        ],
    )

    # 4P FFA
    assert approx(
        rate([team_1, team_1, team_1, team_1], model=BradleyTerryPart),
        [
            [[27.63523138347365, 8.065506316323548]],
            [[25.0, 7.788474807872566]],
            [[25.0, 7.788474807872566]],
            [[22.36476861652635, 8.065506316323548]],
        ],
    )

    # 5P FFA
    assert approx(
        rate([team_1, team_1, team_1, team_1, team_1], model=BradleyTerryPart),
        [
            [[27.63523138347365, 8.065506316323548]],
            [[25.0, 7.788474807872566]],
            [[25.0, 7.788474807872566]],
            [[25.0, 7.788474807872566]],
            [[22.36476861652635, 8.065506316323548]],
        ],
    )

    # 3 Different Sized Teams
    assert approx(
        rate([team_3, team_1, team_2], model=BradleyTerryPart),
        [
            [
                [25.219231461891965, 8.293401112661954],
                [25.219231461891965, 8.293401112661954],
                [25.219231461891965, 8.293401112661954],
            ],
            [[28.48909130001799, 8.220848339985736]],
            [
                [21.291677238090045, 8.206896387427937],
                [21.291677238090045, 8.206896387427937],
            ],
        ],
    )

    # Can use a custom gamma with k=2
    assert approx(
        rate([team_1, team_1], gamma=lambda c, k, *_: 1 / k, model=BradleyTerryPart),
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
            model=BradleyTerryPart,
        ),
        [
            [[27.63523138347365, 8.249579113843055]],
            [[25.0, 8.16496580927726]],
            [[25.0, 8.16496580927726]],
            [[25.0, 8.16496580927726]],
            [[22.36476861652635, 8.249579113843055]],
        ],
    )
