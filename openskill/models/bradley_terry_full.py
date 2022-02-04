import math
from typing import Callable

from openskill.constants import Constants
from openskill.util import gamma


class BradleyTerryFull:
    def __init__(self, game, team_rating: Callable, **options):
        self.constants = Constants(**options)
        self.EPSILON = self.constants.EPSILON
        self.TWO_BETA_SQUARED = self.constants.TWO_BETA_SQUARED
        self.team_ratings = team_rating(game, **options)
        self.gamma = gamma(**options)

    def calculate(self):
        result = []
        for i, i_team_ratings in enumerate(self.team_ratings):
            omega = 0
            delta = 0
            i_mu, i_sigma_squared, i_team, i_rank = i_team_ratings

            for q, q_team_ratings in enumerate(self.team_ratings):
                q_mu, q_sigma_squared, q_team, q_rank = q_team_ratings

                if q == i:
                    continue

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
                gamma = self.gamma(ciq, len(self.team_ratings), *i_team_ratings)
                delta += ((gamma * sigma_squared_to_ciq) / ciq) * piq * (1 - piq)

            intermediate_result_per_team = []
            for j, j_players in enumerate(i_team):
                mu = j_players.mu
                sigma = j_players.sigma
                mu += (sigma**2 / i_sigma_squared) * omega
                sigma *= math.sqrt(
                    max(1 - (sigma**2 / i_sigma_squared) * delta, self.EPSILON),
                )
                intermediate_result_per_team.append([mu, sigma])
            result.append(intermediate_result_per_team)
        return result
