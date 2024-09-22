"""Bradley-Terry Partial Pairing Model

Specific classes and functions for the Bradley-Terry Partial Pairing model.
"""

import copy
import itertools
import math
import uuid
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Type

from openskill.models.common import _normalize, _unary_minus
from openskill.models.weng_lin.common import (
    _ladder_pairs,
    _unwind,
    phi_major,
    phi_major_inverse,
)

__all__: List[str] = ["BradleyTerryPart", "BradleyTerryPartRating"]


class BradleyTerryPartRating:
    """
    Bradley-Terry Partial Pairing player rating data.

    This object is returned by the :code:`BradleyTerryPart.rating` method.
    """

    def __init__(
        self,
        mu: float,
        sigma: float,
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

        self.mu: float = mu
        self.sigma: float = sigma

    def __repr__(self) -> str:
        return f"BradleyTerryPartRating(mu={self.mu}, sigma={self.sigma})"

    def __str__(self) -> str:
        if self.name:
            return (
                f"Bradley-Terry Partial Pairing Player Data: \n\n"
                f"id: {self.id}\n"
                f"name: {self.name}\n"
                f"mu: {self.mu}\n"
                f"sigma: {self.sigma}\n"
            )
        else:
            return (
                f"Bradley-Terry Partial Pairing Player Data: \n\n"
                f"id: {self.id}\n"
                f"mu: {self.mu}\n"
                f"sigma: {self.sigma}\n"
            )

    def __hash__(self) -> int:
        return hash((self.id, self.mu, self.sigma))

    def __deepcopy__(self, memodict: Dict[Any, Any] = {}) -> "BradleyTerryPartRating":
        blp = BradleyTerryPartRating(self.mu, self.sigma, self.name)
        blp.id = self.id
        return blp

    def __eq__(self, other: object) -> bool:
        if isinstance(other, BradleyTerryPartRating):
            if self.mu == other.mu and self.sigma == other.sigma:
                return True
            else:
                return False
        else:
            return NotImplemented

    def __lt__(self, other: "BradleyTerryPartRating") -> bool:
        if isinstance(other, BradleyTerryPartRating):
            if self.ordinal() < other.ordinal():
                return True
            else:
                return False
        else:
            raise ValueError(
                "You can only compare BradleyTerryPartRating objects with each other."
            )

    def __gt__(self, other: "BradleyTerryPartRating") -> bool:
        if isinstance(other, BradleyTerryPartRating):
            if self.ordinal() > other.ordinal():
                return True
            else:
                return False
        else:
            raise ValueError(
                "You can only compare BradleyTerryPartRating objects with each other."
            )

    def __le__(self, other: "BradleyTerryPartRating") -> bool:
        if isinstance(other, BradleyTerryPartRating):
            if self.ordinal() <= other.ordinal():
                return True
            else:
                return False
        else:
            raise ValueError(
                "You can only compare BradleyTerryPartRating objects with each other."
            )

    def __ge__(self, other: "BradleyTerryPartRating") -> bool:
        if isinstance(other, BradleyTerryPartRating):
            if self.ordinal() >= other.ordinal():
                return True
            else:
                return False
        else:
            raise ValueError(
                "You can only compare BradleyTerryPartRating objects with each other."
            )

    def ordinal(self, z: float = 3.0, alpha: float = 1, target: float = 0) -> float:
        r"""
        A single scalar value that represents the player's skill where their
        true skill is 99.7% likely to be higher.

        :param z: Float that represents the number of standard deviations to subtract
              from the mean. By default, set to 3.0, which corresponds to a
              99.7% confidence interval in a normal distribution.

        :param alpha: Float scaling factor applied to the entire calculation.
                      Adjusts the overall scale of the ordinal value.
                      Defaults to 1.

        :param target: Float value used to shift the ordinal value
                       towards a specific target. The shift is adjusted by the
                       alpha scaling factor. Defaults to 0.

        :return: :math:`\alpha \cdot ((\mu - z * \sigma) + \frac{\text{target}}{\alpha})`
        """
        return alpha * ((self.mu - z * self.sigma) + (target / alpha))


class BradleyTerryPartTeamRating:
    """
    The collective Bradley-Terry Partial Pairing rating of a team.
    """

    def __init__(
        self,
        mu: float,
        sigma_squared: float,
        team: Sequence[BradleyTerryPartRating],
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

        :param team: A list of Bradley-Terry Partial Pairing player ratings.

        :param rank: The rank of the team within a gam
        """
        self.mu = float(mu)
        self.sigma_squared = float(sigma_squared)
        self.team = team
        self.rank = rank

    def __repr__(self) -> str:
        return f"BradleyTerryPartTeamRating(mu={self.mu}, sigma_squared={self.sigma_squared})"

    def __str__(self) -> str:
        return (
            f"BradleyTerryPartTeamRating Details:\n\n"
            f"mu: {self.mu}\n"
            f"sigma_squared: {self.sigma_squared}\n"
            f"rank: {self.rank}\n"
        )

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, BradleyTerryPartTeamRating):
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
    c: float,
    k: int,
    mu: float,
    sigma_squared: float,
    team: Sequence[BradleyTerryPartRating],
    rank: int,
    weights: Optional[List[float]] = None,
) -> float:
    """
    Default gamma function for Bradley-Terry Partial Pairing.

    :param c: The square root of the collective team sigma.

    :param k: The number of teams in the game.

    :param mu: The mean of the team's rating.

    :param sigma_squared: The variance of the team's rating.

    :param team: The team rating object.

    :param rank: The rank of the team.

    :param weights: The weights of the players in a team.

    :return: A number.
    """
    return math.sqrt(sigma_squared) / c


class BradleyTerryPart:
    r"""
    Algorithm 2 by :cite:t:`JMLR:v12:weng11a`

    The BradleyTerryPart model maintains the single scalar value
    representation of player performance, enables rating updates based on
    match outcomes, and utilizes a logistic regression approach for rating
    estimation. By allowing for partial pairing situations, this model
    caters to scenarios where not all players face each other directly and
    still provides accurate rating estimates.
    """

    def __init__(
        self,
        mu: float = 25.0,
        sigma: float = 25.0 / 3.0,
        beta: float = 25.0 / 6.0,
        kappa: float = 0.0001,
        gamma: Callable[
            [
                float,
                int,
                float,
                float,
                Sequence[BradleyTerryPartRating],
                int,
                Optional[List[float]],
            ],
            float,
        ] = _gamma,
        tau: float = 25.0 / 300.0,
        limit_sigma: bool = False,
        balance: bool = False,
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

        :param balance: Boolean that determines whether to emphasize
                        rating outliers.
        """
        # Model Parameters
        self.mu: float = float(mu)
        self.sigma: float = float(sigma)
        self.beta: float = beta
        self.kappa: float = float(kappa)
        self.gamma: Callable[
            [
                float,
                int,
                float,
                float,
                Sequence[BradleyTerryPartRating],
                int,
                Optional[List[float]],
            ],
            float,
        ] = gamma

        self.tau: float = float(tau)
        self.limit_sigma: bool = limit_sigma
        self.balance: bool = balance

        # Model Data Container
        self.BradleyTerryPartRating: Type[BradleyTerryPartRating] = (
            BradleyTerryPartRating
        )

    def __repr__(self) -> str:
        return f"BradleyTerryPart(mu={self.mu}, sigma={self.sigma})"

    def __str__(self) -> str:
        return (
            f"Bradley-Terry Partial Pairing Model Parameters: \n\n"
            f"mu: {self.mu}\n"
            f"sigma: {self.sigma}\n"
        )

    def rating(
        self,
        mu: Optional[float] = None,
        sigma: Optional[float] = None,
        name: Optional[str] = None,
    ) -> BradleyTerryPartRating:
        r"""
        Returns a new rating object with your default parameters. The given
        parameters can be overridden from the defaults provided by the main
        model, but is not recommended unless you know what you are doing.

        :param mu: Represents the initial belief about the skill of
                   a player before any matches have been played. Known
                   mostly as the mean of the Gaussian prior distribution.

                   *Represented by:* :math:`\mu`

        :param sigma: Standard deviation of the prior distribution of player.

                      *Represented by:* :math:`\sigma = \frac{\mu}{z}`
                      where :math:`z` is an integer that represents the
                      variance of the skill of a player.

        :param name: Optional name for the player.

        :return: :class:`BradleyTerryPartRating` object
        """
        return self.BradleyTerryPartRating(
            mu if mu is not None else self.mu,
            sigma if sigma is not None else self.sigma,
            name,
        )

    @staticmethod
    def create_rating(
        rating: List[float], name: Optional[str] = None
    ) -> BradleyTerryPartRating:
        """
        Create a :class:`BradleyTerryPartRating` object from a list of `mu`
        and `sigma` values.

        :param rating: A list of two values where the first value is the :code:`mu`
                       and the second value is the :code:`sigma`.

        :param name: An optional name for the player.

        :return: A :class:`BradleyTerryPartRating` object created from the list passed in.
        """
        if isinstance(rating, BradleyTerryPartRating):
            raise TypeError("Argument is already a 'BradleyTerryPartRating' object.")
        elif len(rating) == 2 and isinstance(rating, list):
            for value in rating:
                if not isinstance(value, (int, float)):
                    raise ValueError(
                        f"The {rating.__class__.__name__} contains an "
                        f"element '{value}' of type '{value.__class__.__name__}'"
                    )
            if not name:
                return BradleyTerryPartRating(mu=rating[0], sigma=rating[1])
            else:
                return BradleyTerryPartRating(mu=rating[0], sigma=rating[1], name=name)
        else:
            raise TypeError(f"Cannot accept '{rating.__class__.__name__}' type.")

    @staticmethod
    def _check_teams(teams: List[List[BradleyTerryPartRating]]) -> None:
        """
        Ensure teams argument is valid.

        :param teams: List of lists of BradleyTerryPartRating objects.
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
                        if isinstance(player, BradleyTerryPartRating):
                            pass
                        else:
                            raise TypeError(
                                f"Argument 'teams' must be a list of lists of 'BradleyTerryPartRating' objects, "
                                f"not '{player.__class__.__name__}'."
                            )
                else:
                    raise TypeError(
                        f"Argument 'teams' must be a list of lists of 'BradleyTerryPartRating' objects, "
                        f"not '{team.__class__.__name__}'."
                    )
        else:
            raise TypeError(
                f"Argument 'teams' must be a list of lists of 'BradleyTerryPartRating' objects, "
                f"not '{teams.__class__.__name__}'."
            )

    def rate(
        self,
        teams: List[List[BradleyTerryPartRating]],
        ranks: Optional[List[float]] = None,
        scores: Optional[List[float]] = None,
        weights: Optional[List[List[float]]] = None,
        tau: Optional[float] = None,
        limit_sigma: Optional[bool] = None,
    ) -> List[List[BradleyTerryPartRating]]:
        """
        Calculate the new ratings based on the given teams and parameters.

        :param teams: A list of teams where each team is a list of
                      :class:`BradleyTerryPartRating` objects.

        :param ranks: A list of floats where the lower values
                      represent winners.

        :param scores: A list of floats where higher values
                      represent winners.

        :param weights: A list of lists of floats, where each inner list
                        represents the contribution of each player to the
                        team's performance.

        :param tau: Additive dynamics parameter that prevents sigma from
                    getting too small to increase rating change volatility.

        :param limit_sigma: Boolean that determines whether to restrict
                            the value of sigma from increasing.

        :return: A list of teams where each team is a list of updated
                :class:`BradleyTerryPartRating` objects.
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

        # Catch weights argument errors
        if weights:
            if isinstance(weights, list):
                if len(weights) != len(teams):
                    raise ValueError(
                        f"Argument 'weights' must have the same number of elements as"
                        f" 'teams', not {len(weights)}."
                    )

                for index, team_weights in enumerate(weights):
                    if isinstance(team_weights, list):
                        if len(team_weights) != len(teams[index]):
                            raise ValueError(
                                f"Argument 'weights' must have the same number of elements"
                                f"as each team in 'teams', not {len(team_weights)}."
                            )
                        for weight in team_weights:
                            if isinstance(weight, (int, float)):
                                pass
                            else:
                                raise TypeError(
                                    f"Argument 'weights' must be a list of lists of 'float' values, "
                                    f"not '{weight.__class__.__name__}'."
                                )
                    else:
                        raise TypeError(
                            f"Argument 'weights' must be a list of lists of 'float' values, "
                            f"not '{team_weights.__class__.__name__}'."
                        )
            else:
                raise TypeError(
                    f"Argument 'weights' must be a list of lists of 'float' values, "
                    f"not '{weights.__class__.__name__}'."
                )

        # Deep Copy Teams
        original_teams = teams
        teams = copy.deepcopy(original_teams)

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

        # Normalize Weights
        if weights:
            weights = [_normalize(team_weights, 1, 2) for team_weights in weights]

        tenet = None
        if ranks:
            rank_teams_unwound = _unwind(ranks, teams)

            if weights:
                weights, _ = _unwind(ranks, weights)

            ordered_teams = rank_teams_unwound[0]
            tenet = rank_teams_unwound[1]
            teams = ordered_teams
            ranks = sorted(ranks)

        processed_result = []
        if ranks and tenet:
            result = self._compute(teams=teams, ranks=ranks, weights=weights)
            unwound_result = _unwind(tenet, result)[0]
            for item in unwound_result:
                team = []
                for player in item:
                    team.append(player)
                processed_result.append(team)
        else:
            result = self._compute(teams=teams, weights=weights)
            for item in result:
                team = []
                for player in item:
                    team.append(player)
                processed_result.append(team)

        # Possible Final Result
        final_result = processed_result

        if limit_sigma is not None:
            self.limit_sigma = limit_sigma

        if self.limit_sigma:
            final_result = []

            # Reuse processed_result
            for team_index, team in enumerate(processed_result):
                final_team = []
                for player_index, player in enumerate(team):
                    player.sigma = min(
                        player.sigma, original_teams[team_index][player_index].sigma
                    )
                    final_team.append(player)
                final_result.append(final_team)
        return final_result

    def _c(self, team_ratings: List[BradleyTerryPartTeamRating]) -> float:
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
    def _sum_q(team_ratings: List[BradleyTerryPartTeamRating], c: float) -> List[float]:
        r"""
        Sum up all the values of :code:`mu / c` raised to :math:`e`.

        *Represented by:*

        .. math::

           \sum_{s \in C_q} e^{\theta_s / c}, q=1, ...,k, \text{where } C_q = \{i: r(i) \geq r(q)\}

        Algorithm 4: Procedure 3 in :cite:p:`JMLR:v12:weng11a`

        :param team_ratings: The whole rating of a list of teams in a game.

        :param c: The square root of the collective team sigma.

        :return: A list of floats.
        """

        sum_q: Dict[int, float] = {}
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
    def _a(team_ratings: List[BradleyTerryPartTeamRating]) -> List[int]:
        r"""
        Count the number of times a rank appears in the list of team ratings.

        *Represented by:*

        .. math::

           A_q = |\{s: r(s) = r(q)\}|, q = 1,...,k

        :param team_ratings: The whole rating of a list of teams in a game.
        :return: A list of ints.
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
        teams: List[List[BradleyTerryPartRating]],
        ranks: Optional[List[float]] = None,
        weights: Optional[List[List[float]]] = None,
    ) -> List[List[BradleyTerryPartRating]]:
        # Initialize Constants
        original_teams = teams
        team_ratings = self._calculate_team_ratings(teams, ranks=ranks)
        beta = self.beta
        adjacent_teams = _ladder_pairs(team_ratings)

        result = []
        for i, (team_i, adjacent_i) in enumerate(zip(team_ratings, adjacent_teams)):
            omega = 0.0
            delta = 0.0

            for q, team_q in enumerate(adjacent_i):
                if q == i:
                    continue

                c_iq = math.sqrt(
                    team_i.sigma_squared + team_q.sigma_squared + (2 * beta**2)
                )
                p_iq = 1 / (1 + math.exp((team_q.mu - team_i.mu) / c_iq))
                sigma_squared_to_ciq = team_i.sigma_squared / c_iq

                s = 0.0
                if team_q.rank > team_i.rank:
                    s = 1
                elif team_q.rank == team_i.rank:
                    s = 0.5

                omega += sigma_squared_to_ciq * (s - p_iq)
                if weights:
                    gamma_value = self.gamma(
                        c_iq,
                        len(team_ratings),
                        team_i.mu,
                        team_i.sigma_squared,
                        team_i.team,
                        team_i.rank,
                        weights[i],
                    )
                else:
                    gamma_value = self.gamma(
                        c_iq,
                        len(team_ratings),
                        team_i.mu,
                        team_i.sigma_squared,
                        team_i.team,
                        team_i.rank,
                        None,
                    )
                delta += (
                    ((gamma_value * sigma_squared_to_ciq) / c_iq) * p_iq * (1 - p_iq)
                )

            intermediate_result_per_team = []
            for j, j_players in enumerate(team_i.team):

                if weights:
                    weight = weights[i][j]
                else:
                    weight = 1

                mu = j_players.mu
                sigma = j_players.sigma

                if omega > 0:
                    mu += (sigma**2 / team_i.sigma_squared) * omega * weight
                    sigma *= math.sqrt(
                        max(
                            1 - (sigma**2 / team_i.sigma_squared) * delta * weight,
                            self.kappa,
                        ),
                    )
                else:
                    mu += (sigma**2 / team_i.sigma_squared) * omega / weight
                    sigma *= math.sqrt(
                        max(
                            1 - (sigma**2 / team_i.sigma_squared) * delta / weight,
                            self.kappa,
                        ),
                    )

                modified_player = original_teams[i][j]
                modified_player.mu = mu
                modified_player.sigma = sigma
                intermediate_result_per_team.append(modified_player)
            result.append(intermediate_result_per_team)
        return result

    def predict_win(self, teams: List[List[BradleyTerryPartRating]]) -> List[float]:
        r"""
        Predict how likely a match up against teams of one or more players
        will go. This algorithm has a time complexity of
        :math:`\mathcal{0}(n^2)` where 'n' is the number of teams.

        This is a generalization of the algorithm in
        :cite:p:`Ibstedt1322103` to asymmetric n-player n-teams.

        :param teams: A list of two or more teams.
        :return: A list of odds of each team winning.
        """
        # Check Arguments
        self._check_teams(teams)

        n = len(teams)
        total_player_count = sum(len(team) for team in teams)

        # 2 Player Case
        if n == 2:
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
            pair_a_subset = self._calculate_team_ratings([pair_a])
            pair_b_subset = self._calculate_team_ratings([pair_b])
            mu_a = pair_a_subset[0].mu
            sigma_a = pair_a_subset[0].sigma_squared
            mu_b = pair_b_subset[0].mu
            sigma_b = pair_b_subset[0].sigma_squared
            pairwise_probabilities.append(
                phi_major(
                    (mu_a - mu_b)
                    / math.sqrt(total_player_count * self.beta**2 + sigma_a + sigma_b)
                )
            )

        win_probabilities = []
        for i in range(n):
            team_win_probability = sum(
                pairwise_probabilities[j] for j in range(i * (n - 1), (i + 1) * (n - 1))
            ) / (n - 1)
            win_probabilities.append(team_win_probability)

        total_probability = sum(win_probabilities)
        return [probability / total_probability for probability in win_probabilities]

    def predict_draw(self, teams: List[List[BradleyTerryPartRating]]) -> float:
        r"""
        Predict how likely a match up against teams of one or more players
        will draw. This algorithm has a time complexity of
        :math:`\mathcal{0}(n^2)` where 'n' is the number of teams.

        :param teams: A list of two or more teams.
        :return: The odds of a draw.
        """
        # Check Arguments
        self._check_teams(teams)

        total_player_count = sum(len(team) for team in teams)
        draw_probability = 1 / total_player_count
        draw_margin = (
            math.sqrt(total_player_count)
            * self.beta
            * phi_major_inverse((1 + draw_probability) / 2)
        )

        pairwise_probabilities = []
        for pair_a, pair_b in itertools.combinations(teams, 2):
            pair_a_subset = self._calculate_team_ratings([pair_a])
            pair_b_subset = self._calculate_team_ratings([pair_b])
            mu_a = pair_a_subset[0].mu
            sigma_a = pair_a_subset[0].sigma_squared
            mu_b = pair_b_subset[0].mu
            sigma_b = pair_b_subset[0].sigma_squared
            pairwise_probabilities.append(
                phi_major(
                    (draw_margin - mu_a + mu_b)
                    / math.sqrt(total_player_count * self.beta**2 + sigma_a + sigma_b)
                )
                - phi_major(
                    (mu_b - mu_a - draw_margin)
                    / math.sqrt(total_player_count * self.beta**2 + sigma_a + sigma_b)
                )
            )

        return sum(pairwise_probabilities) / len(pairwise_probabilities)

    def predict_rank(
        self, teams: List[List[BradleyTerryPartRating]]
    ) -> List[Tuple[int, float]]:
        r"""
        Predict the shape of a match outcome. This algorithm has a time
        complexity of :math:`\mathcal{0}(n^2)` where 'n' is the
        number of teams.

        :param teams: A list of two or more teams.
        :return: A list of team ranks with their probabilities.
        """
        self._check_teams(teams)

        n = len(teams)
        total_player_count = sum(len(team) for team in teams)
        team_ratings = self._calculate_team_ratings(teams)

        win_probabilities = []
        for i, team_i in enumerate(team_ratings):
            team_win_probability = 0.0
            for j, team_j in enumerate(team_ratings):
                if i != j:
                    team_win_probability += phi_major(
                        (team_i.mu - team_j.mu)
                        / math.sqrt(
                            total_player_count * self.beta**2
                            + team_i.sigma_squared
                            + team_j.sigma_squared
                        )
                    )
            win_probabilities.append(team_win_probability / (n - 1))

        total_probability = sum(win_probabilities)
        normalized_probabilities = [p / total_probability for p in win_probabilities]

        sorted_teams = sorted(
            enumerate(normalized_probabilities), key=lambda x: x[1], reverse=True
        )

        ranks = [0] * n
        current_rank = 1
        for i, (team_index, _) in enumerate(sorted_teams):
            if i > 0 and sorted_teams[i][1] < sorted_teams[i - 1][1]:
                current_rank = i + 1
            ranks[team_index] = current_rank

        return list(zip(ranks, normalized_probabilities))

    def _calculate_team_ratings(
        self,
        game: Sequence[Sequence[BradleyTerryPartRating]],
        ranks: Optional[List[float]] = None,
        weights: Optional[List[List[float]]] = None,
    ) -> List[BradleyTerryPartTeamRating]:
        """
        Get the team ratings of a game.

        :param game: A list of teams, where teams are lists of
                     :class:`BradleyTerryPartRating` objects.

        :param ranks: A list of ranks for each team in the game.

        :param weights: A list of lists of floats, where each inner list
                        represents the contribution of each player to the
                        team's performance. The values should be normalized
                        from 0 to 1.

        :return: A list of :class:`BradleyTerryPartTeamRating` objects.
        """
        if ranks:
            rank = self._calculate_rankings(game, ranks)
        else:
            rank = self._calculate_rankings(game)

        result = []
        for index, team in enumerate(game):
            sorted_team = sorted(team, key=lambda p: p.ordinal(), reverse=True)
            max_ordinal = sorted_team[0].ordinal()

            mu_summed = 0.0
            sigma_squared_summed = 0.0
            for player in sorted_team:
                if self.balance:
                    ordinal_diff = max_ordinal - player.ordinal()
                    balance_weight = 1 + (ordinal_diff / (max_ordinal + self.kappa))
                else:
                    balance_weight = 1.0
                mu_summed += player.mu * balance_weight
                sigma_squared_summed += (player.sigma * balance_weight) ** 2
            result.append(
                BradleyTerryPartTeamRating(
                    mu_summed, sigma_squared_summed, team, rank[index]
                )
            )
        return result

    def _calculate_rankings(
        self,
        game: Sequence[Sequence[BradleyTerryPartRating]],
        ranks: Optional[List[float]] = None,
    ) -> List[int]:
        """
        Calculates the rankings based on the scores or ranks of the teams.

        It assigns a rank to each team based on their score, with the team with
        the highest score being ranked first.

        :param game: A list of teams, where teams are lists of
                     :class:`BradleyTerryPartRating` objects.

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
