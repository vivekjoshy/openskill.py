"""
CLI utility to generate expected test data for the Weng-Lin models.
"""

import json
import pathlib
from statistics import NormalDist
from typing import Any, Dict, List

from openskill.models import MODELS

# Normal Distribution
mu_normal = NormalDist(mu=25.0, sigma=25.0 / 3.0)
sigma_normal = NormalDist(mu=25.0 / 3.0, sigma=25.0 / 9.0)


def generate_model_data(game_result: List[List[Any]]) -> Dict[str, Any]:
    """
    Generates the expected rating data for the Weng-Lin models.

    :param game_result: The result of a match.
    :return: The expected rating data.
    """
    section_data = {}
    for team_index, team in enumerate(game_result):
        section_data[f"team_{team_index + 1}"] = []
        for player_index, player in enumerate(team):
            section_data[f"team_{team_index + 1}"].append(
                {
                    "mu": player.mu,
                    "sigma": player.sigma,
                }
            )
    return section_data


def generate_expected_test_data() -> None:
    """
    Generates expected test data for the Weng-Lin models.
    """

    # Weng-Lin Models
    models = MODELS

    # Create folder if it doesn't exist
    file_path = pathlib.Path(__file__).parent.resolve()
    pathlib.Path(file_path / "data").mkdir(exist_ok=True)

    for current_model in models:
        # Create Model Instance
        mu = mu_normal.samples(1)[0]
        sigma = sigma_normal.samples(1)[0]
        model = current_model(mu=mu, sigma=sigma)

        r = model.rating

        team_1 = [r()]
        team_2 = [r(), r()]

        game_result = model.rate(teams=[team_1, team_2])
        normal_data = generate_model_data(game_result)

        team_1 = [r()]
        team_2 = [r(), r()]
        team_3 = [r()]
        team_4 = [r(), r()]

        game_result = model.rate(
            teams=[team_1, team_2, team_3, team_4], ranks=[2, 1, 4, 3]
        )
        rank_data = generate_model_data(game_result)

        team_1 = [r()]
        team_2 = [r(), r()]

        game_result = model.rate(teams=[team_1, team_2], scores=[1, 2])
        score_data = generate_model_data(game_result)

        model.margin = 2.0
        game = [[r(), r()], [r(), r()], [r(), r()], [r(), r()], [r(), r()]]
        game_result = model.rate(
            teams=game,
            scores=[10, 5, 5, 2, 1],
            weights=[[1, 2], [2, 1], [1, 2], [3, 1], [1, 2]],
        )
        margin_data = generate_model_data(game_result)
        model.margin = 0.0

        team_1 = [r()]
        team_2 = [r(), r()]
        team_3 = [r(), r(), r()]

        game_result = model.rate(
            teams=[
                team_1,
                team_2,
                team_3,
            ],
            ranks=[2, 1, 3],
            limit_sigma=True,
        )
        limit_sigma_data = generate_model_data(game_result)

        team_1 = [r()]
        team_2 = [r(), r()]
        team_3 = [r(), r(), r()]

        game_result = model.rate(teams=[team_1, team_2, team_3], ranks=[1, 2, 1])
        ties_data = generate_model_data(game_result)

        team_1 = [r(), r(), r()]
        team_2 = [r(), r()]
        team_3 = [r(), r(), r()]
        team_4 = [r(), r()]

        game_result = model.rate(
            teams=[team_1, team_2, team_3, team_4],
            ranks=[2, 1, 4, 3],
            weights=[[2, 0, 0], [1, 2], [0, 0, 1], [0, 1]],
        )
        weights_data = generate_model_data(game_result)

        team_1 = [r(), r()]
        team_2 = [r(), r()]

        model = current_model(mu=mu, sigma=sigma, balance=True)
        game_result = model.rate(teams=[team_1, team_2], ranks=[1, 2])
        balance_data = generate_model_data(game_result)

        # Write Expected Data
        with open(f"data/{current_model.__name__.lower()}.json", "w") as model_json:
            data = {
                "model": {
                    "mu": model.mu,
                    "sigma": model.sigma,
                },
                "normal": normal_data,
                "ranks": rank_data,
                "scores": score_data,
                "margins": margin_data,
                "limit_sigma": limit_sigma_data,
                "ties": ties_data,
                "weights": weights_data,
                "balance": balance_data,
            }
            json.dump(data, model_json, indent=4)


if __name__ == "__main__":
    generate_expected_test_data()
