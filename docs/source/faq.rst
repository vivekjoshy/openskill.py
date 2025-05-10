==========================
Frequently Asked Questions
==========================

1. Does this library support weights?
+++++++++++++++++++++++++++++++++++++

Yes. By weights we mean any value that represents a player's contribution to
the team's overall victory (if they win). You can pass raw scores to :code:`weights` if they mainly determine
the win condition. If they don't explicitly determine win conditions (eg: last to stay alive wins), then it's
usually redundant and won't improve predictions.


2. Does this library support partial play?
++++++++++++++++++++++++++++++++++++++++++

Yes, however it's only effective if the player's playtime determines the win condition. You can use any number
representing playtime and invert it relative to all other player durations. Simply pass these values into :code:`weights`.

3. Does this library support score margins?
+++++++++++++++++++++++++++++++++++++++++++

Yes. If a margin of victory or loss is significant, set the :code:`margin` parameter to the said margin value.
This should start to consider margins when using the :code:`scores` parameter. Margins cannot work with ranks
because of the consistent interval nature of ranks.

4. What is the main difference between a partial pairing model and full pairing model?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Partial pairing models are simply heuristics over the actual models. Instead of doing full pairwise
calculations to determine the updates, it only considers the neighbours. It is usually faster to use
a partial pairing model, especially for large games with many teams and players. However this comes
at cost of accuracy.

5. Why are ordinals not giving the correct order for leaderboards?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

You should turn on ``limit_sigma`` if you want the order to be preserved. More details can be found in the ordinal_
section.

.. _ordinal: ordinal.ipynb

6. Does this library support time decay?
++++++++++++++++++++++++++++++++++++++++

Yes. Simply adjust ``sigma`` by a small value as needed when you feel a player has been inactive. A small
delta added every day after being inactive till the value reaches the default sigma is usually good enough.
Make sure to test against your own data to ensure it actually predicts outcomes.

7. How do I scale rating ordinal score to reflect Elo?
++++++++++++++++++++++++++++++++++++++++++++++++++++++

While there is no one-to-one correpondence between Elo and OpenSkill, one standard deviation is approximately
equivalent to around 200 points for an Elo rating starting at around 1500. To mimic Elo, simply set :code:`alpha`
to :math:`\frac{200}{\sigma}` and :code:`target` to 1500 for :py:meth:`ordinal`.

