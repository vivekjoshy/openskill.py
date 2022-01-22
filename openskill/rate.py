from functools import reduce
from typing import Optional, Union, List

from openskill.constants import mu as default_mu
from openskill.constants import sigma as default_sigma
from openskill.models.plackett_luce import PlackettLuce
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
    :return: Returns a list of lists containing `mu` and
             `sigma` values that can be passed into :func:`~openskill.rate.create_rating`
    """
    if "rank" in options:
        rank = rankings(game, options["rank"])
    else:
        rank = rankings(game)

    result = []
    for index, team in enumerate(game):
        team_result = []
        mu_i = reduce(lambda x, y: x + y, map(lambda p: p.mu, team))
        sigma_squared = reduce(lambda x, y: x + y, map(lambda p: p.sigma ** 2, team))
        team_result.extend([mu_i, sigma_squared, team, rank[index]])
        result.append(team_result)
    return result


def rate(teams: List[List[Rating]], **options) -> List[List[Union[int, float]]]:
    """
    Rate multiple teams consisting of one of more players. Order of teams determines rank.

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
