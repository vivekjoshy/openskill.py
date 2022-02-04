import itertools
import math
from collections import deque
from functools import reduce
from typing import Optional, Union, List

from openskill.constants import mu as default_mu, beta
from openskill.constants import sigma as default_sigma
from openskill.models.plackett_luce import PlackettLuce
from openskill.statistics import phi_major
from openskill.util import unwind, rankings


class Rating:
    """
    The storehouse of the skill and confidence the system has in an agent.
    Stores the `mu` and `sigma` values of an agent.

    :param mu: The mean skill of the agent.
    :param sigma: How confident the system is the skill of an agent.
    :param options: Pass in a set of custom values for constants defined in the Weng-Lin paper.
    """

    def __init__(
        self, mu: Optional[float] = None, sigma: Optional[float] = None, **options
    ):
        # Calculate Mu and Sigma
        self.mu = mu if mu else default_mu(**options)
        self.sigma = sigma if sigma else default_sigma(**options)

    def __repr__(self):
        return f"Rating(mu={self.mu}, sigma={self.sigma})"

    def __eq__(self, other):
        if len(other) == 2:
            if self.mu == other[0] and self.sigma == other[1]:
                return True
            else:
                return False


def create_rating(rating_list: List[Union[int, float]]) -> Rating:
    """
    Create a :class:`~openskill.rate.Rating` object from a list of `mu` and `sigma` values.

    :param rating_list: A list of two values where the first value is the `mu` and the second value is the `sigma`.
    :return: A :class:`~openskill.rate.Rating` object created from the list passed in.
    """
    return Rating(mu=rating_list[0], sigma=rating_list[1])


def team_rating(game: List[List[Rating]], **options) -> List[List[Union[int, float]]]:
    """
    Get the whole rating of a list of teams.

    :param game: A list of teams, where teams are lists of :class:`~openskill.rate.Rating` objects.
    :param options: Pass in a set of custom values for constants defined in the Weng-Lin paper.
    :return: Returns a list of lists containing `mu`, `sigma`, the `team` object and the current rank of the team.
    """
    if "rank" in options:
        rank = rankings(game, options["rank"])
    else:
        rank = rankings(game)

    result = []
    for index, team in enumerate(game):
        team_result = []
        mu_i = reduce(lambda x, y: x + y, map(lambda p: p.mu, team))
        sigma_squared = reduce(lambda x, y: x + y, map(lambda p: p.sigma**2, team))
        team_result.extend([mu_i, sigma_squared, team, rank[index]])
        result.append(team_result)
    return result


def rate(teams: List[List[Rating]], **options) -> List[List[Union[int, float]]]:
    """
    Rate multiple teams consisting of one of more agents. Order of teams determines rank.

    :param teams: A list of teams, where teams are lists of :class:`~openskill.rate.Rating` objects.
    :param rank: A list of :class:`~int` where the lower values represent the winners.
    :param score: A list of :class:`~int` where higher values represent the winners.
    :param options: Pass in a set of custom values for constants defined in the Weng-Lin paper.
    :return: Returns a list of lists containing `mu` and
             `sigma` values that can be passed into :func:`~openskill.rate.create_rating`
    """
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

    if "model" in options:
        model = options["model"](teams, team_rating=team_rating, **options)
    else:
        model = PlackettLuce(teams, team_rating=team_rating, **options)

    if rank and tenet:
        result = model.calculate()
        result, old_tenet = unwind(tenet, result)
        return result
    else:
        return model.calculate()


def predict_win(teams: List[List[Rating]], **options) -> List[Union[int, float]]:
    """
    Predict how likely a match up against teams of one or more agents will go.
    This algorithm has a time complexity of O(n!) where 'n' is the number of teams.

    :param teams: A list of two or more teams, where teams are lists of :class:`~openskill.rate.Rating` objects.
    :return: A list of probabilities of each team winning.
    """
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
                / math.sqrt(n * beta(**options) ** 2 + sigma_a**2 + sigma_b**2)
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
