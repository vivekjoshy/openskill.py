import copy
import itertools
import math
from functools import reduce
from typing import List, Optional, Union

from openskill.constants import Constants, beta
from openskill.constants import mu as default_mu
from openskill.constants import sigma as default_sigma
from openskill.models.plackett_luce import PlackettLuce
from openskill.statistics import phi_major, phi_major_inverse
from openskill.util import rankings, unwind


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
        if isinstance(mu, (float, int)):
            self.mu = mu
        else:
            self.mu = default_mu(**options)

        if isinstance(sigma, (float, int)):
            self.sigma = sigma
        else:
            self.sigma = default_sigma(**options)

    def __repr__(self):
        return f"Rating(mu={self.mu}, sigma={self.sigma})"

    def __eq__(self, other):
        if isinstance(other, Rating):
            if self.mu == other.mu and self.sigma == other.sigma:
                return True
            else:
                return False
        elif isinstance(other, (list, tuple)):
            if len(other) == 2:
                for value in other:
                    if not isinstance(value, (int, float)):
                        raise ValueError(
                            f"The {other.__class__.__name__} contains an "
                            f"element '{value}' of type '{value.__class__.__name__}'"
                        )
                if self.mu == other[0] and self.sigma == other[1]:
                    return True
                else:
                    return False
            else:
                raise ValueError(
                    f"The '{other.__class__.__name__}' object has more than two floats."
                )
        else:
            raise ValueError(
                "You can only compare Rating objects with each other or a list of two floats."
            )

    def __lt__(self, other):
        if isinstance(other, Rating):
            if ordinal(self) < ordinal(other):
                return True
            else:
                return False
        elif isinstance(other, (list, tuple)):
            if len(other) == 2:
                for value in other:
                    if not isinstance(value, (int, float)):
                        raise ValueError(
                            f"The {other.__class__.__name__} contains an "
                            f"element '{value}' of type '{value.__class__.__name__}'"
                        )
                if ordinal(self) < ordinal([other[0], other[1]]):
                    return True
                else:
                    return False
            else:
                raise ValueError(
                    f"The '{other.__class__.__name__}' object has more than two floats."
                )
        else:
            raise ValueError(
                "You can only compare Rating objects with each other or a list of two floats."
            )

    def __gt__(self, other):
        if isinstance(other, Rating):
            if ordinal(self) > ordinal(other):
                return True
            else:
                return False
        elif isinstance(other, (list, tuple)):
            if len(other) == 2:
                for value in other:
                    if not isinstance(value, (int, float)):
                        raise ValueError(
                            f"The {other.__class__.__name__} contains an "
                            f"element '{value}' of type '{value.__class__.__name__}'"
                        )
                if ordinal(self) > ordinal([other[0], other[1]]):
                    return True
                else:
                    return False
            else:
                raise ValueError(
                    f"The '{other.__class__.__name__}' object has more than two floats."
                )
        else:
            raise ValueError(
                "You can only compare Rating objects with each other or a list of two floats."
            )

    def __le__(self, other):
        if isinstance(other, Rating):
            if ordinal(self) <= ordinal(other):
                return True
            else:
                return False
        elif isinstance(other, (list, tuple)):
            if len(other) == 2:
                for value in other:
                    if not isinstance(value, (int, float)):
                        raise ValueError(
                            f"The {other.__class__.__name__} contains an "
                            f"element '{value}' of type '{value.__class__.__name__}'"
                        )
                if ordinal(self) <= ordinal([other[0], other[1]]):
                    return True
                else:
                    return False
            else:
                raise ValueError(
                    f"The '{other.__class__.__name__}' object has more than two floats."
                )
        else:
            raise ValueError(
                "You can only compare Rating objects with each other or a list of two floats."
            )

    def __ge__(self, other):
        if isinstance(other, Rating):
            if ordinal(self) >= ordinal(other):
                return True
            else:
                return False
        elif isinstance(other, (list, tuple)):
            if len(other) == 2:
                for value in other:
                    if not isinstance(value, (int, float)):
                        raise ValueError(
                            f"The {other.__class__.__name__} contains an "
                            f"element '{value}' of type '{value.__class__.__name__}'"
                        )
                if ordinal(self) >= ordinal([other[0], other[1]]):
                    return True
                else:
                    return False
            else:
                raise ValueError(
                    f"The '{other.__class__.__name__}' object has more than two floats."
                )
        else:
            raise ValueError(
                "You can only compare Rating objects with each other or a list of two floats."
            )


def ordinal(agent: Union[Rating, list, tuple], **options) -> float:
    """
    Convert `mu` and `sigma` into a single value for sorting purposes.

    :param agent: A :class:`~openskill.rate.Rating` object or a :class:`~list` or :class:`~tuple` of :class:`~float`
                  objects.
    :param options: Pass in a set of custom values for constants defined in the Weng-Lin paper.
    :return: A :class:`~float` object that represents a 1 dimensional value for a rating.
    """
    if isinstance(agent, (list, tuple)):
        if len(agent) == 2:
            for value in agent:
                if not isinstance(value, (int, float)):
                    raise ValueError(
                        f"The {agent.__class__.__name__} contains an "
                        f"element '{value}' of type '{value.__class__.__name__}'"
                    )
            z = Constants(**options).Z
            return agent[0] - z * agent[1]
        else:
            raise ValueError(
                f"The '{agent.__class__.__name__}' object has more than two floats."
            )
    elif isinstance(agent, Rating):
        # Calculate Z
        z = Constants(**options).Z
        return agent.mu - z * agent.sigma
    else:
        raise ValueError(
            "You can only pass 'Rating' objects, two-tuples or lists to 'agent'."
        )


def create_rating(rating_list: List[Union[int, float]]) -> Rating:
    """
    Create a :class:`~openskill.rate.Rating` object from a list of `mu` and `sigma` values.

    :param rating_list: A list of two values where the first value is the `mu` and the second value is the `sigma`.
    :return: A :class:`~openskill.rate.Rating` object created from the list passed in.
    """
    if isinstance(rating_list, Rating):
        raise TypeError("Argument is already a 'Rating' object.")
    elif len(rating_list) == 2:
        for value in rating_list:
            if not isinstance(value, (int, float)):
                raise ValueError(
                    f"The {rating_list.__class__.__name__} contains an "
                    f"element '{value}' of type '{value.__class__.__name__}'"
                )
        return Rating(mu=rating_list[0], sigma=rating_list[1])
    else:
        raise TypeError(f"Cannot accept '{rating_list.__class__.__name__}' type.")


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


def rate(teams: List[List[Rating]], **options) -> List[List[Rating]]:
    """
    Rate multiple teams consisting of one of more agents. Order of teams determines rank.

    :param teams: A list of teams, where teams are lists of :class:`~openskill.rate.Rating` objects.
    :param rank: A list of :class:`~int` where the lower values represent the winners.
    :param score: A list of :class:`~int` where higher values represent the winners.
    :param tau: A :class:`~float` that modifies the additive dynamics factor.
    :param prevent_sigma_increase: A :class:`~bool` that prevents sigma from ever increasing.
    :param options: Pass in a set of custom values for constants defined in the Weng-Lin paper.
    :return: Returns a list of :class:`~openskill.rate.Rating` objects.
    """
    constants = Constants(**options)
    tau = constants.TAU
    original_teams = copy.deepcopy(teams)
    if "tau" in options:
        tau_squared = tau * tau
        for team_index, team in enumerate(teams):
            for player_index, player in enumerate(team):
                teams[team_index][player_index].sigma = math.sqrt(
                    player.sigma * player.sigma + tau_squared
                )

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

    processed_result = []
    if rank and tenet:
        result = model.calculate()
        result, old_tenet = unwind(tenet, result)
        for item in result:
            team = []
            for player in item:
                team.append(create_rating(player))
            processed_result.append(team)
    else:
        result = model.calculate()
        for item in result:
            team = []
            for player in item:
                team.append(create_rating(player))
            processed_result.append(team)

    final_result = processed_result

    if options.get("tau"):
        if options.get("prevent_sigma_increase"):
            final_result = []
            for team_index, team in enumerate(processed_result):
                final_team = []
                for player_index, player in enumerate(team):
                    player_original = original_teams[team_index][player_index]
                    if player.sigma <= player_original.sigma:
                        sigma = player.sigma
                    else:
                        sigma = player_original.sigma
                    final_team.append(Rating(mu=player.mu, sigma=sigma))
                final_result.append(final_team)
    return final_result


def predict_win(teams: List[List[Rating]], **options) -> List[Union[int, float]]:
    """
    Predict how likely a match up against teams of one or more agents will go.
    This algorithm has a time complexity of O(n!/(n - 2)!) where 'n' is the number of teams.

    :param teams: A list of two or more teams, where teams are lists of :class:`~openskill.rate.Rating` objects.
    :return: A list of probabilities of each team winning.
    """
    if len(teams) < 2:
        raise ValueError(f"Expected at least two teams.")

    n = len(teams)
    denom = (n * (n - 1)) / 2

    pairwise_probabilities = []
    for pairwise_subset in itertools.permutations(teams, 2):
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

    return [
        (sum(team_prob) / denom)
        for team_prob in itertools.zip_longest(
            *[iter(pairwise_probabilities)] * (n - 1)
        )
    ]


def predict_draw(teams: List[List[Rating]], **options) -> Union[int, float]:
    """
    Predict how likely a match up against teams of one or more agents will draw.
    This algorithm has a time complexity of O(n!/(n - 2)!) where 'n' is the number of teams.

    :param teams: A list of two or more teams, where teams are lists of :class:`~openskill.rate.Rating` objects.
    :return: A :class:`~float` that represents the probability of the teams drawings.
    """
    if len(teams) < 2:
        raise ValueError(f"Expected at least two teams.")

    n = len(teams)
    total_player_count = sum([len(_) for _ in teams])
    draw_probability = 1 / n
    draw_margin = (
        math.sqrt(total_player_count)
        * beta(**options)
        * phi_major_inverse((1 + draw_probability) / 2)
    )

    pairwise_probabilities = []
    for pairwise_subset in itertools.permutations(teams, 2):
        current_team_a_rating = team_rating([pairwise_subset[0]])
        current_team_b_rating = team_rating([pairwise_subset[1]])
        mu_a = current_team_a_rating[0][0]
        sigma_a = current_team_a_rating[0][1]
        mu_b = current_team_b_rating[0][0]
        sigma_b = current_team_b_rating[0][1]
        pairwise_probabilities.append(
            phi_major(
                (draw_margin - mu_a + mu_b)
                / math.sqrt(n * beta(**options) ** 2 + sigma_a**2 + sigma_b**2)
            )
            - phi_major(
                (mu_a - mu_b - draw_margin)
                / math.sqrt(n * beta(**options) ** 2 + sigma_a**2 + sigma_b**2)
            )
        )

    denom = 1
    if n > 2:
        denom = n * (n - 1)

    return abs(sum(pairwise_probabilities)) / denom
