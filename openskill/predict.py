import itertools
import math
from collections import deque

from openskill.constants import beta
from openskill.statistics import phi_major
from openskill.util import unwind, team_rating


def predict_win(teams, **options):
    if "rank" in options:
        rank = options["rank"]
    else:
        if "score" in options:
            rank = list(map(lambda points: -points, options["score"]))
            options["rank"] = rank
        else:
            rank = None

    tenet = None
    if rank:
        ordered_teams, tenet = unwind(rank, teams)
        teams = ordered_teams
        rank = sorted(rank)
        options["rank"] = rank

    if len(teams) < 2:
        raise ValueError(f"Expected at least two teams.")

    n = len(teams)

    pairwise_probabilities = []
    for pairwise_subset in itertools.permutations(teams, len(teams)):
        current_team_a_rating = team_rating([pairwise_subset[0]])
        current_team_b_rating = team_rating([pairwise_subset[1]])
        mu_a = current_team_a_rating[0][0]
        sigma_a = current_team_a_rating[0][1]
        mu_b = current_team_b_rating[0][0]
        sigma_b = current_team_b_rating[0][1]
        pairwise_probabilities.append(
            phi_major(
                (mu_a - mu_b)
                / math.sqrt(n * beta(**options) ** 2 + sigma_a ** 2 + sigma_b ** 2)
            )
        )

    if n > 2:
        cache = deque(pairwise_probabilities)
        probabilities = []
        partial = len(pairwise_probabilities) / n
        while len(cache) > 0:
            aggregate = []
            for length in range(int(partial)):
                aggregate.append(cache.popleft())
            aggregate_sum = sum(aggregate)
            aggregate_multiple = n
            for length in range(1, n - 2):
                aggregate_multiple *= n - length
            probabilities.append(aggregate_sum / aggregate_multiple)
        return probabilities
    else:
        return pairwise_probabilities
