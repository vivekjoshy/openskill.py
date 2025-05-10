User Manual
===========

OpenSkill requires knowledge of some domain specific jargon to navigate.
If you know what the central measures of tendency and Gaussian distributions are, you are pretty much set.

If you don't know what those are, please consider using a short resource on statistics to get acquainted with
the terms. We recommend Khan Academy's short course on `statistics and probability <https://www.khanacademy.org/math/statistics-probability>`_.

If you're struggling with any of the concepts, please search the discussions section to see if your question has already been answered.
If you can't find an answer, please open a new `discussion <https://github.com/vivekjoshy/openskill.py/discussions>`_ and we'll try to help you out.
You can also get help from the official `Discord Server <https://discord.com/invite/4JNDeHMYkM>`_. If you have a feature request, or want to report
a bug please create a new `issue <https://github.com/vivekjoshy/openskill.py/issues/new/choose>`_ if one already doesn't exist.

Let's start with a short refresher:

Arithmetic Mean
---------------

The arithmetic mean is the sum of all values divided by the number of values.
It is the most common type of average.

.. math::

   \bar{x} = \frac{1}{n} \sum_{i=1}^{n} x_i

We will denote :math:`\bar{x}` as the symbol :math:`\mu` or henceforth written in code as :code:`mu`.

Every player has a :code:`mu` value. This is the average skill of the player as determined by OpenSkill models.
On the other hand, presumably there is an actual amount of skill that a player has. This skill value obviously
fluctuates due to many factors. Our goal is to estimate this value as accurately as possible.

But how can we be certain about whether the skill the model has given a player is accurate?

Standard Deviation
------------------

The standard deviation is a measure of how spread out numbers are. It is the square root of the variance.
The variance is the average of the squared differences from the mean.

.. math::

   \sigma = \sqrt{\frac{1}{n} \sum_{i=1}^{n} (x_i - \mu)^2}


We will denote :math:`\sigma` written in code as :code:`sigma`. This is the uncertainty the model has about the player's skill.
The higher the uncertainty, the less certain the model is about the player's skill.
For instance if a player has a :code:`mu` of :code:`25` and a :code:`sigma` of :code:`8`, then the model is 95% certain that the player's skill is between :code:`9` and :code:`41`.

The Basics
----------

First we have to initialize the mode we want to use. We will use the :py:class:`PlackettLuce <openskill.models.weng_lin.plackett_luce.PlackettLuce>` model for this example.
The :py:class:`PlackettLuce <openskill.models.weng_lin.plackett_luce.PlackettLuce>` model is generally a good choice if you're not expecting large matches with lots of players and teams.
On the whole, all the 5 models have the same capabilities, but some are more accurate and some are faster than others. It's up to
you to test out what works for you.

Let's start the example by importing the model from the package. All models live
under the :code:`openskill.models` module.

.. code-block:: python

   from openskill.models import PlackettLuce

   model = PlackettLuce()


Every model comes with a set of parameters that can be set. These parameters are
used to configure the model to your liking. The parameters for all the Weng-Lin models are somewhat similar.

The default parameters for the :py:class:`PlackettLuce <openskill.models.weng_lin.plackett_luce.PlackettLuce>` model are found here, but you are free to use anything
in so far as you don't violate the rules of the underlying assumptions of the model. The important and relevant parameters
here are :code:`mu` and :code:`sigma` with :math:`25` and :math:`25/3` as their default values respectively.

You can ofcourse shift the values higher or lower. But it doesn't make sense to violate the rule that :code:`sigma` should be
:math:`\frac{1}{3}` of :code:`mu`. If you do, the model may not work as intended. If you know what you're doing and are a
statistics expert, you can change the parameters to your liking. But if you're not, we recommend you stick to the default values.

Finally, there is a :code:`balance` flag you can set to :code:`True` if you want the rating system to modify it's
assumptions about users on the tail ends of the skill distribution. With :code:`balance` turned on, the higher the rating
a player has, it's assumed it's a much more monumental achievement. The inverse is true for lower rated players. We won't
enable this feature for our purposes.

Let's now get the object representing a single player by calling the :code:`rating` method
on the model. This method returns a :py:class:`PlackettLuceRating <openskill.models.weng_lin.plackett_luce.PlackettLuceRating>` object for which you can set your own
values. Since we are using the default values, each player will also start with those values. We can also set a optional name.
It can anything, an ID, a username, anything. It's just a way to identify the player.

.. code-block:: python

   p1 = model.rating(name='john123')
   print(p1)


This will print out the following:


.. code-block:: text

  Plackett-Luce Player Data:

  id: 58d990abafd44559bb5f63882c1456dc
  name: john123
  mu: 25.0
  sigma: 8.333333333333334


Notice, how a :py:func:`uuid.uuid4` is generated for the player. This is a unique identifier for the player.
You can use a regular :py:func:`filter` to get the player back from the model.


Let's generate a few more players.

.. code-block:: python

   p2 = model.rating(name='jane234')
   p3 = model.rating(name='joe546')
   p4 = model.rating(name='jill678')

Now let's organize them into teams. Team are represented by regular python lists.

.. code-block:: python

   team1 = [p1, p2]
   team2 = [p3, p4]

Now let's create a match and rate them using our model. The first team is the winner.

.. code-block:: python

   match = [team1, team2]
   [team1, team2] = model.rate(match)
   [p1, p2] = team1
   [p3, p4] = team2

Let's print all the player's values to see what's changed.

.. code-block:: text

   p1: mu=26.964294621803063, sigma=8.177962604389991
   p2: mu=26.964294621803063, sigma=8.177962604389991
   p3: mu=23.035705378196937, sigma=8.177962604389991
   p4: mu=23.035705378196937, sigma=8.177962604389991

As you may have noticed, the winning team has a higher :code:`mu` value than the losing team and the :code:`sigma` values
of all the players have decreased. This is because the model is more certain about the skill of the players after the match.

More often than not you'll want to store at least the :code:`mu` and :code:`sigma` values of the players in a database.
This means if you want to conduct another match, you'll have to load the players back from the database. We have a helper
method to create a player from a list of :code:`mu` and :code:`sigma` values. Just call the model's :code:`create_rating` method.

.. code-block:: python

   p1 = model.create_rating([23.035705378196937, 8.177962604389991], "jill678")



.. warning::

   Do not store the :py:func:`uuid.uuid4` in a database. It is only useful for the lifetime of the program.
   If you want to use a unique identifier to store in the database, use the :code:`name` parameter instead.

Ranks
-----

When displaying a rating, or sorting a list of ratings, you can use :py:meth:`ordinal <openskill.models.weng_lin.plackett_luce.PlackettLuceRating.ordinal>`.

.. code-block:: python

   print(p1.ordinal())
   print(p3.ordinal())


Which will print out the following:

.. code-block:: text

   2.4304068086330872
   -1.4981824349730388


By default, this returns :math:`\mu - 3\sigma`, showing a rating for which there's a 99.7% likelihood the player's true
rating is higher, so with early games, a player's ordinal rating will usually go up and could go up even if that
player loses. If you want to prevent that you can pass the :code:`limit_sigma` boolean parameter to the model defaults
or the :py:meth:`rate <openskill.models.weng_lin.plackett_luce.PlackettLuce.rate>` method.


Artificial Ranks
----------------

If your teams are listed in one order but your ranking is in a different order, for convenience you can specify a ranks
option, such as:

.. code-block:: python

   ranks = [4, 1, 3, 2]
   [[p1], [p2], [p3], [p4]] = model.rate(match, ranks=ranks)


It's assumed that the lower ranks are better (wins), while higher ranks are worse (losses).
You can provide a score instead, where lower is worse and higher is better. These can just be raw scores from the game, if you want.

Ties should have either equivalent rank or score:

.. code-block:: python

   scores = [37, 19, 37, 42]
   [[p1], [p2], [p3], [p4]] = model.rate(match, scores=scores)


Score Margins
-------------

If winning or losing by some margin of difference between two scores is important, then your can set the :code:`margin` parameter. This should normally improve accuracy
for games where for instance winning by two points (like in tennis) is not as impressive as winning by 5 or 6 points.

.. code-block:: python

   model = PlackettLuce(margin=2.0)
   scores = [11, 9, 0, 3]
   [[p1], [p2], [p3], [p4]] = model.rate(match, scores=scores)


Weights
-------

For faster convergence of ratings, you can use pass the :code:`weights` argument to the :py:meth:`rate <openskill.models.weng_lin.plackett_luce.PlackettLuce.rate>` method.
The :code:`weights` argument takes raw numeric values for each player from at the end of a match. These values should only
represent metrics that **always** contribute to a win condition in the match. For instance, in large scale open battle
arena games, there is a time limit for the entire game. In such games, a player can still win with very low points or kills.
Always make sure the metric you choose in your game is something that significantly contributes to winning the match.

.. code-block:: python

   weights = [[20], [1], [3], [15]]
   [[p1], [p2], [p3], [p4]] = model.rate(match, weights=weights)


Matchmaking
-----------

These models wouldn't be very useful, if you couldn't predict and match up players and teams.
So we have 3 methods to help you do that.


Predicting Winners
~~~~~~~~~~~~~~~~~~

You can compare two or more teams to get the probabilities of each team winning.

.. code-block:: python

   p1 = model.rating()
   p2 = model.rating(mu=33.564, sigma=1.123)

   predictions = model.predict_win([[p1], [p2]])
   print(predictions)
   print(sum(predictions))

Let's see what this outputs:

.. code-block:: text

   [0.2021226121041832, 0.7978773878958167]
   1.0


As you can see the team with the higher :code:`mu` and lower :code:`sigma` has a higher probability of winning.
The sum of the probabilities is :math:`1.0` as expected.

Predicting Draws
~~~~~~~~~~~~~~~~

You can also predict the probability of a draw between two teams. This behaves more like a match quality metric.
The higher the probability of a draw, the more likely the teams are to be evenly matched.

.. code-block:: python

   p1 = model.rating(mu=35, sigma=1.0)
   p2 = model.rating(mu=35, sigma=1.0)
   p3 = model.rating(mu=35, sigma=1.0)
   p4 = model.rating(mu=35, sigma=1.0)
   p5 = model.rating(mu=35, sigma=1.0)

   team1 = [p1, p2]
   team2 = [p3, p4, p5]

   predictions = model.predict_draw([team1, team2])
   print(predictions)

Let's see what this outputs:

.. code-block:: text

   0.0002807397636510


Odd, we have almost no chance for a draw. This is because the more teams we have the possibilities
for draws decrease due to match dynamics. Let's try with 2 teams and fewer players.

.. code-block:: python

   p1 = model.rating(mu=35, sigma=1.0)
   p2 = model.rating(mu=35, sigma=1.1)

   team1 = [p1]
   team2 = [p2]

   predictions = model.predict_draw([team1, team2])
   print(predictions)

Okay let's see what changed:

.. code-block:: text

   0.4868868769871696

A much higher draw probability! So keep in mind that the more teams you have, the lower the probability of a draw and
you should account for that in your matchmaking service.

.. note::

   Draw probabilities will never exceed 0.5 since there is always some uncertainty.

Predicting Ranks
~~~~~~~~~~~~~~~~

We can go even more fine grained and predict the ranks of the teams. This is useful if you want to match the lowest
ranked teams with the highest ranked teams allowing you to quickly eliminate weaker players from quickly from a tournament.

.. code-block:: python

   p1 = model.rating(mu=34, sigma=0.25)
   p2 = model.rating(mu=34, sigma=0.25)
   p3 = model.rating(mu=34, sigma=0.25)

   p4 = model.rating(mu=32, sigma=0.5)
   p5 = model.rating(mu=32, sigma=0.5)
   p6 = model.rating(mu=32, sigma=0.5)

   p7 = model.rating(mu=30, sigma=1)
   p8 = model.rating(mu=30, sigma=1)
   p9 = model.rating(mu=30, sigma=1)

   team1, team2, team3 = [p1, p2, p3], [p4, p5, p6], [p7, p8, p9]

   rank_predictions = model.predict_rank([team1, team2, team3])
   print(rank_predictions)

It will produce the rank and the likelihood of that rank for each team:

.. code-block:: text

   [(1, 0.5043035277836156), (2, 0.3328317993957732), (3, 0.16286467282061112)]


.. warning::

    The sum of the probabilities of the ranks and the draw probability no longer equal 1.0 from :code:`v6` onwards.


Picking Models
--------------

The models are all very similar, but some are more efficient and more accurate depending up on the specific use case.

There are currently 5 models:

* :py:class:`BradleyTerryFull <openskill.models.weng_lin.bradley_terry_full.BradleyTerryFull>`
* :py:class:`BradleyTerryPart <openskill.models.weng_lin.bradley_terry_part.BradleyTerryPart>`
* :py:class:`PlackettLuce <openskill.models.weng_lin.plackett_luce.PlackettLuce>`
* :py:class:`ThurstoneMostellerFull <openskill.models.weng_lin.thurstone_mosteller_full.ThurstoneMostellerFull>`
* :py:class:`ThurstoneMostellerPart <openskill.models.weng_lin.thurstone_mosteller_part.ThurstoneMostellerPart>`

:code:`Part` stands for partial paring and is a reference to how ratings are calculated underneath the hood. Suffice to say
the partial pairing models are more efficient, but less accurate than the full pairing models. The :py:class:`Plackett-Luce <openskill.models.weng_lin.plackett_luce.PlackettLuce>`
model is a good balance between efficiency and accuracy and is the recommended model for most use cases.
