import math
from typing import Callable

from openskill.constants import Constants
from openskill.util import gamma, ladder_pairs


class BradleyTerryPart:
    def __init__(self, game, team_rating: Callable, **options):
        self.constants = Constants(**options)
        self.EPSILON = self.constants.EPSILON
        self.TWO_BETA_SQUARED = self.constants.TWO_BETA_SQUARED
        self.team_ratings = team_rating(game, **options)
        self.gamma = gamma(**options)
        self.adjacent_teams = ladder_pairs(self.team_ratings)

    def calculate(self):
        def i_map(i_team_rating, i_adjacents):
            i_mu, i_sigma_squared, i_team, i_rank = i_team_rating

            def od_reduce(od, q_team_ratings):
                omega, delta = od
                for q_team_rating in q_team_ratings:
                    q_mu, q_sigma_squared, q_team, q_rank = q_team_rating
                    ciq = math.sqrt(
                        i_sigma_squared + q_sigma_squared + self.TWO_BETA_SQUARED
                    )
                    piq = 1 / (1 + math.exp((q_mu - i_mu) / ciq))
                    sigma_squared_to_ciq = i_sigma_squared / ciq

                    s = 0
                    if q_rank > i_rank:
                        s = 1
                    elif q_rank == i_rank:
                        s = 0.5

                    omega += sigma_squared_to_ciq * (s - piq)
                    gamma = self.gamma(ciq, len(self.team_ratings), *i_team_rating)
                    delta += ((gamma * sigma_squared_to_ciq) / ciq) * piq * (1 - piq)

                return omega, delta

            i_omega, i_delta = od_reduce([0, 0], i_adjacents)

            intermediate_result_per_team = []
            for j, j_players in enumerate(i_team):
                mu = j_players.mu
                sigma = j_players.sigma
                mu += (sigma**2 / i_sigma_squared) * i_omega
                sigma *= math.sqrt(
                    max(1 - (sigma**2 / i_sigma_squared) * i_delta, self.EPSILON),
                )
                intermediate_result_per_team.append([mu, sigma])
            return intermediate_result_per_team

        return list(
            map(
                lambda i: i_map(i[0], i[1]), zip(self.team_ratings, self.adjacent_teams)
            )
        )
