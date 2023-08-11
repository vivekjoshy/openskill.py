:py:mod:`openskill.models.weng_lin.bradley_terry_part`
======================================================

.. py:module:: openskill.models.weng_lin.bradley_terry_part

.. autoapi-nested-parse::

   Bradley-Terry Partial Pairing Model

   Specific classes and functions for the Bradley-Terry Partial Pairing model.



Module Contents
---------------

Classes
~~~~~~~

.. autoapisummary::

   openskill.models.weng_lin.bradley_terry_part.BradleyTerryPart
   openskill.models.weng_lin.bradley_terry_part.BradleyTerryPartRating




.. py:class:: BradleyTerryPart(mu = 25.0, sigma = 25.0 / 3.0, beta = 25.0 / 6.0, kappa = 0.0001, gamma = _gamma, tau = 25.0 / 300.0, limit_sigma = False)


   Algorithm 2 by :cite:t:`JMLR:v12:weng11a`

   The BradleyTerryPart model maintains the single scalar value
   representation of player performance, enables rating updates based on
   match outcomes, and utilizes a logistic regression approach for rating
   estimation. By allowing for partial pairing situations, this model
   caters to scenarios where not all players face each other directly and
   still provides accurate rating estimates.

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


   .. py:method:: _a(team_ratings)
      :staticmethod:

      Count the number of times a rank appears in the list of team ratings.

      *Represented by:*

      .. math::

         A_q = |\{s: r(s) = r(q)\}|, q = 1,...,k

      :param team_ratings: The whole rating of a list of teams in a game.
      :return: A list of integers.


   .. py:method:: _c(team_ratings)

      Calculate the square root of the collective team sigma.

      *Represented by:*

      .. math::

         c = \Biggl(\sum_{i=1}^k (\sigma_i^2 + \beta^2) \Biggr)

      Algorithm 4: Procedure 3 in :cite:p:`JMLR:v12:weng11a`

      :param team_ratings: The whole rating of a list of teams in a game.
      :return: A number.


   .. py:method:: _calculate_rankings(game, ranks = None)

      Calculates the rankings based on the scores or ranks of the teams.

      It assigns a rank to each team based on their score, with the team with
      the highest score being ranked first.

      :param game: A list of teams, where teams are lists of
                   :class:`BradleyTerryPartRating` objects.

      :param ranks: A list of ranks for each team in the game.

      :return: A list of ranks for each team in the game.


   .. py:method:: _calculate_team_ratings(game, ranks = None, scores = None)

      Get the team ratings of a game.

      :param game: A list of teams, where teams are lists of
                   :class:`BradleyTerryPartRating` objects.

      :param ranks: A list of ranks for each team in the game.

      :param scores: A list of scores for each team in the game.

      :return: A list of :class:`BradleyTerryPartTeamRating` objects.


   .. py:method:: _check_teams(teams)
      :staticmethod:

      Ensure teams argument is valid.

      :param teams: List of lists of BradleyTerryPartRating objects.


   .. py:method:: _sum_q(team_ratings, c)
      :staticmethod:

      Sum up all the values of :code:`mu / c` raised to :math:`e`.

      *Represented by:*

      .. math::

         \sum_{s \in C_q} e^{\theta_s / c}, q=1, ...,k, \text{where } C_q = \{i: r(i) \geq r(q)\}

      Algorithm 4: Procedure 3 in :cite:p:`JMLR:v12:weng11a`

      :param team_ratings: The whole rating of a list of teams in a game.

      :param c: The square root of the collective team sigma.

      :return: A list of integers.


   .. py:method:: create_rating(rating, name = None)
      :staticmethod:

      Create a :class:`BradleyTerryPartRating` object from a list of `mu`
      and `sigma` values.

      :param rating: A list of two values where the first value is the :code:`mu`
                     and the second value is the :code:`sigma`.

      :param name: An optional name for the player.

      :return: A :class:`BradleyTerryPartRating` object created from the list passed in.


   .. py:method:: predict_draw(teams)

      Predict how likely a match up against teams of one or more players
      will draw. This algorithm has a time complexity of
      :math:`\mathcal{0}(n!/(n - 2)!)` where 'n' is the number of teams.

      :param teams: A list of two or more teams.
      :return: The odds of a draw.


   .. py:method:: predict_rank(teams)

      Predict the shape of a match outcome. This algorithm has a time
      complexity of :math:`\mathcal{0}(n!/(n - 2)!)` where 'n' is the
      number of teams.

      :param teams: A list of two or more teams.
      :return: A list of team ranks with their probabilities.


   .. py:method:: predict_win(teams)

      Predict how likely a match up against teams of one or more players
      will go. This algorithm has a time complexity of
      :math:`\mathcal{0}(n!/(n - 2)!)` where 'n' is the number of teams.

      This is a generalization of the algorithm in
      :cite:p:`Ibstedt1322103` to asymmetric n-player n-teams.

      :param teams: A list of two or more teams.
      :return: A list of odds of each team winning.


   .. py:method:: rate(teams, ranks = None, scores = None, tau = None, limit_sigma = None)

      Calculate the new ratings based on the given teams and parameters.

      :param teams: A list of teams where each team is a list of
                    :class:`BradleyTerryPartRating` objects.

      :param ranks: A list of integers where the lower values
                    represent winners.

      :param scores: A list of integers where higher values
                    represent winners.

      :param tau: Additive dynamics parameter that prevents sigma from
                  getting too small to increase rating change volatility.

      :param limit_sigma: Boolean that determines whether to restrict
                          the value of sigma from increasing.

      :return: A list of teams where each team is a list of updated
              :class:`BradleyTerryPartRating` objects.


   .. py:method:: rating(mu = None, sigma = None, name = None)

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

      :return: :class:`BradleyTerryPartRating` object



.. py:class:: BradleyTerryPartRating(mu, sigma, name = None)


   Bradley-Terry Partial Pairing player rating data.

   This object is returned by the :code:`BradleyTerryPart.rating` method.

   :param mu: Represents the initial belief about the skill of
              a player before any matches have been played. Known
              mostly as the mean of the Guassian prior distribution.

              *Represented by:* :math:`\mu`

   :param sigma: Standard deviation of the prior distribution of player.

                 *Represented by:* :math:`\sigma = \frac{\mu}{z}`
                 where :math:`z` is an integer that represents the
                 variance of the skill of a player.

   :param name: Optional name for the player.

   .. py:method:: ordinal(z = 3.0)

      A single scalar value that represents the player's skill where their
      true skill is 99.7% likely to be higher.

      :param z: Integer that represents the variance of the skill of a
                player. By default, set to 3.

      :return: :math:`\mu - z * \sigma`



