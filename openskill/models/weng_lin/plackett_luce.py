"""Plackett-Luce Model

Specific classes and functions for the Plackett-Luce model.
"""
import copy
import itertools
import math
import uuid
from functools import reduce
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Type, Union

from openskill.models.common import _rank_data, _unary_minus
from openskill.models.weng_lin.common import _unwind, phi_major, phi_major_inverse

__all__: List[str] = ["PlackettLuce", "PlackettLuceRating"]


class PlackettLuceRating:
    """
    Plackett-Luce player rating data.

    This object is returned by the :code:`PlackettLuce.rating` method.
    """

    def __init__(
        self,
        mu: Union[int, float],
        sigma: Union[int, float],
        name: Optional[str] = None,
    ):
        r"""
        :param mu: Represents the initial belief about the skill of
                   a player before any matches have been played. Known
                   mostly as the mean of the Guassian prior distribution.

                   *Represented by:* :math:`\mu`

        :param sigma: Standard deviation of the prior distribution of player.

                      *Represented by:* :math:`\sigma = \frac{\mu}{z}`
                      where :math:`z` is an integer that represents the
                      variance of the skill of a player.

        :param name: Optional name for the player.
        """

        # Player Information
        self.id: str = uuid.uuid4().hex.lower()
        self.name: Optional[str] = name

        self.mu: Union[int, float] = mu
        self.sigma: Union[int, float] = sigma

    def __repr__(self) -> str:
        return f"PlackettLuceRating(mu={self.mu}, sigma={self.sigma})"

    def __str__(self) -> str:
        if self.name:
            return (
                f"Plackett-Luce Player Data: \n\n"
                f"id: {self.id}\n"
                f"name: {self.name}\n"
                f"mu: {self.mu}\n"
                f"sigma: {self.sigma}\n"
            )
        else:
            return (
                f"Plackett-Luce Player Data: \n\n"
                f"id: {self.id}\n"
                f"mu: {self.mu}\n"
                f"sigma: {self.sigma}\n"
            )

    def __hash__(self) -> int:
        return hash((self.id, self.mu, self.sigma))

    def __deepcopy__(self, memodict: Dict[Any, Any] = {}) -> "PlackettLuceRating":
        plr = PlackettLuceRating(self.mu, self.sigma, self.name)
        plr.id = self.id
        return plr

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PlackettLuceRating):
            if self.mu == other.mu and self.sigma == other.sigma:
                return True
            else:
                return False
        else:
            return NotImplemented

    def __lt__(self, other: "PlackettLuceRating") -> bool:
        if isinstance(other, PlackettLuceRating):
            if self.ordinal() < other.ordinal():
                return True
            else:
                return False
        else:
            raise ValueError(
                "You can only compare PlackettLuceRating objects with each other."
            )

    def __gt__(self, other: "PlackettLuceRating") -> bool:
        if isinstance(other, PlackettLuceRating):
            if self.ordinal() > other.ordinal():
                return True
            else:
                return False
        else:
            raise ValueError(
                "You can only compare PlackettLuceRating objects with each other."
            )

    def __le__(self, other: "PlackettLuceRating") -> bool:
        if isinstance(other, PlackettLuceRating):
            if self.ordinal() <= other.ordinal():
                return True
            else:
                return False
        else:
            raise ValueError(
                "You can only compare PlackettLuceRating objects with each other."
            )

    def __ge__(self, other: "PlackettLuceRating") -> bool:
        if isinstance(other, PlackettLuceRating):
            if self.ordinal() >= other.ordinal():
                return True
            else:
                return False
        else:
            raise ValueError(
                "You can only compare PlackettLuceRating objects with each other."
            )

    def ordinal(self, z: Union[int, float] = 3.0) -> Union[int, float]:
        r"""
        A single scalar value that represents the player's skill where their
        true skill is 99.7% likely to be higher.

        :param z: Integer that represents the variance of the skill of a
                  player. By default, set to 3.

        :return: :math:`\mu - z * \sigma`
        """
        return self.mu - z * self.sigma


class PlackettLuceTeamRating:
    """
    The collective Plackett-Luce rating of a team.
    """

    def __init__(
        self,
        mu: Union[int, float],
        sigma_squared: Union[int, float],
        team: Sequence[PlackettLuceRating],
        rank: int,
    ):
        r"""
        :param mu: Represents the initial belief about the collective skill of
                   a team before any matches have been played. Known
                   mostly as the mean of the Guassian prior distribution.

                   *Represented by:* :math:`\mu`

        :param sigma_squared: Standard deviation of the prior distribution of a team.

                      *Represented by:* :math:`\sigma = \frac{\mu}{z}`
                      where :math:`z` is an integer that represents the
                      variance of the skill of a player.

        :param team: A list of Weng-Lin player ratings.

        :param rank: The rank of the team within a gam
        """
        self.mu = float(mu)
        self.sigma_squared = float(sigma_squared)
        self.team = team
        self.rank = rank

    def __repr__(self) -> str:
        return (
            f"PlackettLuceTeamRating(mu={self.mu}, sigma_squared={self.sigma_squared})"
        )

    def __str__(self) -> str:
        return (
            f"PlackettLuceTeamRating Details:\n\n"
            f"mu: {self.mu}\n"
            f"sigma_squared: {self.sigma_squared}\n"
            f"rank: {self.rank}\n"
        )

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, PlackettLuceTeamRating):
            return (
                self.mu == other.mu
                and self.sigma_squared == other.sigma_squared
                and self.team == other.team
                and self.rank == other.rank
            )
        else:
            return NotImplemented

    def __hash__(self) -> int:
        return hash((self.mu, self.sigma_squared, tuple(self.team), self.rank))


def _gamma(
    c: Union[int, float],
    k: int,
    mu: Union[int, float],
    sigma_squared: Union[int, float],
    team: Sequence[PlackettLuceRating],
    rank: int,
) -> Union[int, float]:
    """
    Default gamma function for Plackett-Luce.

    :param c: The square root of the collective team sigma.

    :param k: The number of teams in the game.

    :param mu: The mean of the team's rating.

    :param sigma_squared: The variance of the team's rating.

    :param team: The team rating object.

    :param rank: The rank of the team.

    :return: A number.
    """
    return math.sqrt(sigma_squared) / c


class PlackettLuce:
    r"""
    Algorithm 4 by :cite:t:`JMLR:v12:weng11a`

    The PlackettLuce model departs from single scalar representations of
    player performance present in simpler models. There is a vector of
    abilities for each player that captures their performance across multiple
    dimensions. The outcome of a match between multiple players depends on
    their abilities in each dimension. By introducing this multidimensional
    aspect, the Plackett-Luce model provides a richer framework for ranking
    players based on their abilities in various dimensions.
    """

    def __init__(
        self,
        mu: Union[int, float] = 25.0,
        sigma: Union[int, float] = 25.0 / 3.0,
        beta: Union[int, float] = 25.0 / 6.0,
        kappa: Union[int, float] = 0.0001,
        gamma: Callable[
            [
                Union[int, float],
                int,
                Union[int, float],
                Union[int, float],
                Sequence[PlackettLuceRating],
                int,
            ],
            Union[int, float],
        ] = _gamma,
        tau: Union[int, float] = 25.0 / 300.0,
        limit_sigma: bool = False,
    ):
        r"""
        :param mu: Represents the initial belief about the skill of
                   a player before any matches have been played. Known
                   mostly as the mean of the Guassian prior distribution.

                   *Represented by:* :math:`\mu`

        :param sigma: Standard deviation of the prior distribution of player.

                      *Represented by:* :math:`\sigma = \frac{\mu}{z}`
                      where :math:`z` is an integer that represents the
                      variance of the skill of a player.


        :param beta: Hyperparameter that determines the level of uncertainty
                     or variability present in the prior distribution of
                     ratings.

                     *Represented by:* :math:`\beta = \frac{\sigma}{2}`

        :param kappa: Arbitrary small positive real number that is used to
                      prevent the variance of the posterior distribution from
                      becoming too small or negative. It can also be thought
                      of as a regularization parameter.

                      *Represented by:* :math:`\kappa`

        :param gamma: Custom function you can pass that must contain 5
                      parameters. The function must return a float or int.

                      *Represented by:* :math:`\gamma`

        :param tau: Additive dynamics parameter that prevents sigma from
                    getting too small to increase rating change volatility.

                    *Represented by:* :math:`\tau`

        :param limit_sigma: Boolean that determines whether to restrict
                            the value of sigma from increasing.

        """
        # Model Parameters
        self.mu: Union[int, float] = float(mu)
        self.sigma: Union[int, float] = float(sigma)
        self.beta: Union[int, float] = beta
        self.kappa: Union[int, float] = float(kappa)
        self.gamma: Callable[
            [
                Union[int, float],
                int,
                Union[int, float],
                Union[int, float],
                Sequence[PlackettLuceRating],
                int,
            ],
            Union[int, float],
        ] = gamma

        self.tau: Union[int, float] = float(tau)
        self.limit_sigma: bool = limit_sigma

        # Model Data Container
        self.PlackettLuceRating: Type[PlackettLuceRating] = PlackettLuceRating

    def __repr__(self) -> str:
        return f"PlackettLuce(mu={self.mu}, sigma={self.sigma})"

    def __str__(self) -> str:
        return (
            f"Plackett-Luce Model Parameters: \n\n"
            f"mu: {self.mu}\n"
            f"sigma: {self.sigma}\n"
        )

    def rating(
        self,
        mu: Optional[Union[int, float]] = None,
        sigma: Optional[Union[int, float]] = None,
        name: Optional[str] = None,
    ) -> PlackettLuceRating:
        r"""
        Returns a new rating object with your default parameters. The given
        parameters can be overriden from the defaults provided by the main
        model, but is not recommended unless you know what you are doing.

        :param mu: Represents the initial belief about the skill of
                   a player before any matches have been played. Known
                   mostly as the mean of the Guassian prior distribution.

                   *Represented by:* :math:`\mu`

        :param sigma: Standard deviation of the prior distribution of player.

                      *Represented by:* :math:`\sigma = \frac{\mu}{z}`
                      where :math:`z` is an integer that represents the
                      variance of the skill of a player.

        :param name: Optional name for the player.

        :return: :class:`PlackettLuceRating` object
        """
        return self.PlackettLuceRating(
            mu if mu is not None else self.mu,
            sigma if sigma is not None else self.sigma,
            name,
        )

    @staticmethod
    def create_rating(
        rating: List[Union[Union[int, float]]], name: Optional[str] = None
    ) -> PlackettLuceRating:
        """
        Create a :class:`PlackettLuceRating` object from a list of `mu`
        and `sigma` values.

        :param rating: A list of two values where the first value is the :code:`mu`
                       and the second value is the :code:`sigma`.

        :param name: An optional name for the player.

        :return: A :class:`PlackettLuceRating` object created from the list passed in.
        """
        if isinstance(rating, PlackettLuceRating):
            raise TypeError("Argument is already a 'PlackettLuceRating' object.")
        elif len(rating) == 2 and isinstance(rating, list):
            for value in rating:
                if not isinstance(value, (int, float)):
                    raise ValueError(
                        f"The {rating.__class__.__name__} contains an "
                        f"element '{value}' of type '{value.__class__.__name__}'"
                    )
            if not name:
                return PlackettLuceRating(mu=rating[0], sigma=rating[1])
            else:
                return PlackettLuceRating(mu=rating[0], sigma=rating[1], name=name)
        else:
            raise TypeError(f"Cannot accept '{rating.__class__.__name__}' type.")

    @staticmethod
    def _check_teams(teams: List[List[PlackettLuceRating]]) -> None:
        """
        Ensure teams argument is valid.
        :param teams: List of lists of PlackettLuceRating objects.
        """
        # Catch teams argument errors
        if isinstance(teams, list):
            if len(teams) < 2:
                raise ValueError(
                    f"Argument 'teams' must have at least 2 teams, not {len(teams)}."
                )

            for team in teams:
                if isinstance(team, list):
                    if len(team) < 1:
                        raise ValueError(
                            f"Argument 'teams' must have at least 1 player per team, not {len(team)}."
                        )

                    for player in team:
                        if isinstance(player, PlackettLuceRating):
                            pass
                        else:
                            raise TypeError(
                                f"Argument 'teams' must be a list of lists of 'PlackettLuceRating' objects, "
                                f"not '{player.__class__.__name__}'."
                            )
                else:
                    raise TypeError(
                        f"Argument 'teams' must be a list of lists of 'PlackettLuceRating' objects, "
                        f"not '{team.__class__.__name__}'."
                    )
        else:
            raise TypeError(
                f"Argument 'teams' must be a list of lists of 'PlackettLuceRating' objects, "
                f"not '{teams.__class__.__name__}'."
            )

    def rate(
        self,
        teams: List[List[PlackettLuceRating]],
        ranks: Optional[List[Union[int, float]]] = None,
        scores: Optional[List[Union[int, float]]] = None,
        tau: Optional[Union[int, float]] = None,
        limit_sigma: Optional[bool] = None,
    ) -> List[List[PlackettLuceRating]]:
        """
        Calculate the new ratings based on the given teams and parameters.

        :param teams: A list of teams where each team is a list of
                      :class:`PlackettLuceRating` objects.

        :param ranks: A list of Decimals where the lower values
                      represent winners.

        :param scores: A list of Decimals where higher values
                      represent winners.

        :param tau: Additive dynamics parameter that prevents sigma from
                    getting too small to increase rating change volatility.

        :param limit_sigma: Boolean that determines whether to restrict
                            the value of sigma from increasing.

        :return: A list of teams where each team is a list of updated
                :class:`PlackettLuceRating` objects.
        """
        # Catch teams argument errors
        self._check_teams(teams)

        # Catch ranks argument errors
        if ranks:
            if isinstance(ranks, list):
                if len(ranks) != len(teams):
                    raise ValueError(
                        f"Argument 'ranks' must have the same number of elements as 'teams', "
                        f"not {len(ranks)}."
                    )

                for rank in ranks:
                    if isinstance(rank, (int, float)):
                        pass
                    else:
                        raise TypeError(
                            f"Argument 'ranks' must be a list of 'int' or 'float' values, "
                            f"not '{rank.__class__.__name__}'."
                        )
            else:
                raise TypeError(
                    f"Argument 'ranks' must be a list of 'int' or 'float' values, "
                    f"not '{ranks.__class__.__name__}'."
                )

            # Catch scores and ranks together
            if scores:
                raise ValueError(
                    "Cannot accept both 'ranks' and 'scores' arguments at the same time."
                )

        # Catch scores argument errors
        if scores:
            if isinstance(scores, list):
                if len(scores) != len(teams):
                    raise ValueError(
                        f"Argument 'scores' must have the same number of elements as 'teams', "
                        f"not {len(scores)}."
                    )

                for score in scores:
                    if isinstance(score, (int, float)):
                        pass
                    else:
                        raise TypeError(
                            f"Argument 'scores' must be a list of 'int' or 'float' values, "
                            f"not '{score.__class__.__name__}'."
                        )
            else:
                raise TypeError(
                    f"Argument 'scores' must be a list of 'int' or 'float' values, "
                    f"not '{scores.__class__.__name__}'."
                )

        # Deep Copy Teams
        original_teams = copy.deepcopy(teams)

        # Correct Sigma With Tau
        tau = tau if tau else self.tau
        tau_squared = tau * tau
        for team_index, team in enumerate(teams):
            for player_index, player in enumerate(team):
                teams[team_index][player_index].sigma = math.sqrt(
                    player.sigma * player.sigma + tau_squared
                )

        # Convert Score to Ranks
        if not ranks and scores:
            ranks = []
            for score in scores:
                ranks.append(_unary_minus(score))

        tenet = None
        if ranks:
            rank_teams_unwound = _unwind(ranks, teams)
            ordered_teams = rank_teams_unwound[0]
            tenet = rank_teams_unwound[1]
            teams = ordered_teams
            ranks = sorted(ranks)

        processed_result = []
        if ranks and tenet:
            result = self._compute(teams, ranks)
            unwound_result = _unwind(tenet, result)[0]
            for item in unwound_result:
                team = []
                for player in item:
                    team.append(player)
                processed_result.append(team)
        else:
            result = self._compute(teams)
            for item in result:
                team = []
                for player in item:
                    team.append(player)
                processed_result.append(team)

        # Possible Final Result
        final_result = processed_result

        if limit_sigma:
            final_result = []

            # Reuse processed_result
            for team_index, team in enumerate(processed_result):
                final_team = []
                for player_index, player in enumerate(team):
                    player_original = original_teams[team_index][player_index]
                    if player.sigma <= player_original.sigma:
                        player.sigma = player.sigma
                    else:
                        player.sigma = player_original.sigma
                    final_team.append(player)
                final_result.append(final_team)
        return final_result

    def _c(self, team_ratings: List[PlackettLuceTeamRating]) -> Union[int, float]:
        r"""
        Calculate the square root of the collective team sigma.

        *Represented by:*

        .. math::

           c = \Biggl(\sum_{i=1}^k (\sigma_i^2 + \beta^2) \Biggr)

        Algorithm 4: Procedure 3 in :cite:p:`JMLR:v12:weng11a`

        :param team_ratings: The whole rating of a list of teams in a game.
        :return: A number.
        """
        beta_squared = self.beta**2
        collective_team_sigma = 0.0
        for team in team_ratings:
            collective_team_sigma += team.sigma_squared + beta_squared
        return math.sqrt(collective_team_sigma)

    @staticmethod
    def _sum_q(
        team_ratings: List[PlackettLuceTeamRating], c: Union[int, float]
    ) -> List[Union[int, float]]:
        r"""
        Sum up all the values of :code:`mu / c` raised to :math:`e`.

        *Represented by:*

        .. math::

           \sum_{s \in C_q} e^{\theta_s / c}, q=1, ...,k, \text{where } C_q = \{i: r(i) \geq r(q)\}

        Algorithm 4: Procedure 3 in :cite:p:`JMLR:v12:weng11a`

        :param team_ratings: The whole rating of a list of teams in a game.

        :param c: The square root of the collective team sigma.

        :return: A list of Decimals.
        """

        sum_q: Dict[int, Union[int, float]] = {}
        for i, team_i in enumerate(team_ratings):
            summed = math.exp(team_i.mu / c)
            for q, team_q in enumerate(team_ratings):
                if team_i.rank >= team_q.rank:
                    if q in sum_q:
                        sum_q[q] += summed
                    else:
                        sum_q[q] = summed
        return list(sum_q.values())

    @staticmethod
    def _a(team_ratings: List[PlackettLuceTeamRating]) -> List[int]:
        r"""
        Count the number of times a rank appears in the list of team ratings.

        *Represented by:*

        .. math::

           A_q = |\{s: r(s) = r(q)\}|, q = 1,...,k

        :param team_ratings: The whole rating of a list of teams in a game.
        :return: A list of Decimals.
        """
        result = list(
            map(
                lambda i: len(list(filter(lambda q: i.rank == q.rank, team_ratings))),
                team_ratings,
            )
        )
        return result

    def _compute(
        self,
        teams: Sequence[Sequence[PlackettLuceRating]],
        ranks: Optional[List[Union[int, float]]] = None,
    ) -> List[List[PlackettLuceRating]]:
        # Initialize Constants
        original_teams = teams
        team_ratings = self._calculate_team_ratings(teams, ranks=ranks)
        c = self._c(team_ratings)
        sum_q = self._sum_q(team_ratings, c)
        a = self._a(team_ratings)

        result = []
        for i, team_i in enumerate(team_ratings):
            omega = 0.0
            delta = 0.0
            i_mu_over_c = math.exp(team_i.mu / c)

            for q, team_q in enumerate(team_ratings):
                i_mu_over_ce_over_sum_q = i_mu_over_c / sum_q[q]
                if team_q.rank <= team_i.rank:
                    delta += (
                        i_mu_over_ce_over_sum_q * (1 - i_mu_over_ce_over_sum_q) / a[q]
                    )
                    if q == i:
                        omega += (1 - i_mu_over_ce_over_sum_q) / a[q]
                    else:
                        omega -= i_mu_over_ce_over_sum_q / a[q]

            omega *= team_i.sigma_squared / c
            delta *= team_i.sigma_squared / c**2

            gamma_value = self.gamma(
                c,
                len(team_ratings),
                team_i.mu,
                team_i.sigma_squared,
                team_i.team,
                team_i.rank,
            )
            delta *= gamma_value

            intermediate_result_per_team = []
            for j, j_players in enumerate(team_i.team):
                mu = j_players.mu
                sigma = j_players.sigma
                mu += (sigma**2 / team_i.sigma_squared) * omega
                sigma *= math.sqrt(
                    max(1 - (sigma**2 / team_i.sigma_squared) * delta, self.kappa),
                )
                modified_player = original_teams[i][j]
                modified_player.mu = mu
                modified_player.sigma = sigma
                intermediate_result_per_team.append(modified_player)
            result.append(intermediate_result_per_team)
        return result

    def predict_win(
        self, teams: List[List[PlackettLuceRating]]
    ) -> List[Union[int, float]]:
        r"""
        Predict how likely a match up against teams of one or more players
        will go. This algorithm has a time complexity of
        :math:`\mathcal{0}(n!/(n - 2)!)` where 'n' is the number of teams.

        This is a generalization of the algorithm in
        :cite:p:`Ibstedt1322103` to asymmetric n-player n-teams.

        :param teams: A list of two or more teams.
        :return: A list of odds of each team winning.
        """
        # Check Arguments
        self._check_teams(teams)

        n = len(teams)
        denominator = (n * (n - 1)) / 2

        # 2 Player Case
        if n == 2:
            total_player_count = len(teams[0]) + len(teams[1])
            teams_ratings = self._calculate_team_ratings(teams)
            a = teams_ratings[0]
            b = teams_ratings[1]
            result = phi_major(
                (a.mu - b.mu)
                / math.sqrt(
                    total_player_count * self.beta**2
                    + a.sigma_squared
                    + b.sigma_squared
                )
            )
            return [result, 1 - result]

        pairwise_probabilities = []
        for pair_a, pair_b in itertools.permutations(teams, 2):
            pair_a_subset = pair_a[0]
            pair_b_subset = pair_b[0]
            mu_a = pair_a_subset.mu
            sigma_a = pair_a_subset.sigma
            mu_b = pair_b_subset.mu
            sigma_b = pair_b_subset.sigma
            pairwise_probabilities.append(
                phi_major(
                    (mu_a - mu_b)
                    / math.sqrt(n * self.beta**2 + sigma_a**2 + sigma_b**2)
                )
            )

        return [
            (sum(team_prob) / denominator)
            for team_prob in itertools.zip_longest(
                *[iter(pairwise_probabilities)] * (n - 1)
            )
        ]

    def predict_draw(self, teams: List[List[PlackettLuceRating]]) -> Union[int, float]:
        r"""
        Predict how likely a match up against teams of one or more players
        will draw. This algorithm has a time complexity of
        :math:`\mathcal{0}(n!/(n - 2)!)` where 'n' is the number of teams.

        :param teams: A list of two or more teams.
        :return: The odds of a draw.
        """
        # Check Arguments
        self._check_teams(teams)

        n = len(teams)
        total_player_count = sum([len(_) for _ in teams])
        draw_probability = 1 / total_player_count
        draw_margin = (
            math.sqrt(total_player_count)
            * self.beta
            * phi_major_inverse((1 + draw_probability) / 2)
        )

        pairwise_probabilities = []
        for pair_a, pair_b in itertools.permutations(teams, 2):
            pair_a_subset = pair_a[0]
            pair_b_subset = pair_b[0]
            mu_a = pair_a_subset.mu
            sigma_a = pair_a_subset.sigma
            mu_b = pair_b_subset.mu
            sigma_b = pair_b_subset.sigma
            pairwise_probabilities.append(
                phi_major(
                    (draw_margin - mu_a + mu_b)
                    / math.sqrt(n * self.beta**2 + sigma_a**2 + sigma_b**2)
                )
                - phi_major(
                    (mu_a - mu_b - draw_margin)
                    / math.sqrt(n * self.beta**2 + sigma_a**2 + sigma_b**2)
                )
            )

        denominator = 1
        if n > 2:
            denominator = n * (n - 1)

        return abs(sum(pairwise_probabilities)) / denominator

    def predict_rank(
        self, teams: List[List[PlackettLuceRating]]
    ) -> List[Tuple[int, Union[int, float]]]:
        r"""
        Predict the shape of a match outcome. This algorithm has a time
        complexity of :math:`\mathcal{0}(n!/(n - 2)!)` where 'n' is the
        number of teams.

        :param teams: A list of two or more teams.
        :return: A list of team ranks with their probabilities.
        """
        self._check_teams(teams)

        n = len(teams)
        total_player_count = sum([len(_) for _ in teams])
        denom = (n * (n - 1)) / 2
        draw_probability = 1 / total_player_count
        draw_margin = (
            math.sqrt(total_player_count)
            * self.beta
            * phi_major_inverse((1 + draw_probability) / 2)
        )

        pairwise_probabilities = []
        for pair_a, pair_b in itertools.permutations(teams, 2):
            pair_a_subset = pair_a[0]
            pair_b_subset = pair_b[0]
            mu_a = pair_a_subset.mu
            sigma_a = pair_a_subset.sigma
            mu_b = pair_b_subset.mu
            sigma_b = pair_b_subset.sigma
            pairwise_probabilities.append(
                phi_major(
                    (mu_a - mu_b - draw_margin)
                    / math.sqrt(n * self.beta**2 + sigma_a**2 + sigma_b**2)
                )
            )
        win_probability = [
            (sum(team_prob) / denom)
            for team_prob in itertools.zip_longest(
                *[iter(pairwise_probabilities)] * (n - 1)
            )
        ]

        ranked_probability = [abs(_) for _ in win_probability]
        ranks = list(_rank_data(ranked_probability))
        max_ordinal = max(ranks)
        ranks = [abs(_ - max_ordinal) + 1 for _ in ranks]
        predictions = list(zip(ranks, ranked_probability))
        return predictions

    def _calculate_team_ratings(
        self,
        game: Sequence[Sequence[PlackettLuceRating]],
        ranks: Optional[List[Union[int, float]]] = None,
    ) -> List[PlackettLuceTeamRating]:
        """
        Get the team ratings of a game.

        :param game: A list of teams, where teams are lists of
                     :class:`PlackettLuceRating` objects.

        :param ranks: A list of ranks for each team in the game.

        :return: A list of :class:`PlackettLuceTeamRating` objects.
        """
        if ranks:
            rank = self._calculate_rankings(game, ranks)
        else:
            rank = self._calculate_rankings(game)

        result = []
        for index, team in enumerate(game):
            mu_summed = reduce(lambda x, y: x + y, map(lambda p: p.mu, team))
            sigma_squared = reduce(
                lambda x, y: x + y, map(lambda p: p.sigma**2, team)
            )
            result.append(
                PlackettLuceTeamRating(mu_summed, sigma_squared, team, rank[index])
            )
        return result

    def _calculate_rankings(
        self,
        game: Sequence[Sequence[PlackettLuceRating]],
        ranks: Optional[List[Union[int, float]]] = None,
    ) -> List[int]:
        """
        Calculates the rankings based on the scores or ranks of the teams.

        It assigns a rank to each team based on their score, with the team with
        the highest score being ranked first.

        :param game: A list of teams, where teams are lists of
                     :class:`PlackettLuceRating` objects.

        :param ranks: A list of ranks for each team in the game.

        :return: A list of ranks for each team in the game.
        """
        if ranks:
            team_scores = []
            for index, _ in enumerate(game):
                if isinstance(ranks[index], int):
                    team_scores.append(ranks[index])
                else:
                    team_scores.append(index)
        else:
            team_scores = [i for i, _ in enumerate(game)]

        rank_output = {}
        s = 0
        for index, value in enumerate(team_scores):
            if index > 0:
                if team_scores[index - 1] < team_scores[index]:
                    s = index
            rank_output[index] = s
        return list(rank_output.values())
