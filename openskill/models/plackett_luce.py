import math
from typing import Callable

from openskill.constants import Constants
from openskill.util import gamma, util_a, util_c, util_sum_q


class PlackettLuce:
    def __init__(self, game, team_rating: Callable, **options):
        self.constants = Constants(**options)
        self.EPSILON = self.constants.EPSILON
        self.team_ratings = team_rating(game, **options)
        self.c = util_c(self.team_ratings, **options)
        self.gamma = gamma(**options)
        self.sum_q = util_sum_q(self.team_ratings, self.c)
        self.a = util_a(self.team_ratings)

    def calculate(self):
        result = []
        for i, i_team_ratings in enumerate(self.team_ratings):
            omega = 0
            delta = 0
            i_mu, i_sigma_squared, i_team, i_rank = i_team_ratings
            i_mu_over_ce = math.exp(i_mu / self.c)

            for q, q_team_ratings in enumerate(self.team_ratings):
                q_mu, q_sigma_squared, q_team, q_rank = q_team_ratings
                i_mu_over_ce_over_sum_q = i_mu_over_ce / self.sum_q[q]
                if q_rank <= i_rank:
                    delta += (
                        i_mu_over_ce_over_sum_q
                        * (1 - i_mu_over_ce_over_sum_q)
                        / self.a[q]
                    )
                    if q == i:
                        omega += (1 - i_mu_over_ce_over_sum_q) / self.a[q]
                    else:
                        omega -= i_mu_over_ce_over_sum_q / self.a[q]

            omega *= i_sigma_squared / self.c
            delta *= i_sigma_squared / self.c**2

            gamma = self.gamma(self.c, len(self.team_ratings), *i_team_ratings)
            delta *= gamma

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
