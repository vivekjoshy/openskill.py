==========================
Frequently Asked Questions
==========================

1. Does this library support partial play?
++++++++++++++++++++++++++++++++++++++++++

No. Partial play is theoretically easy to implement, but hard to verify due to lack of data.
Without data, any modifications to models might end up over-fitting the data. It is also not
clear what metric to use for partial play since different groups mean different
things. If partial play is to implemented, what we mean by it is that the amount of time a
player was in a game.


2. Does this library support weights?
+++++++++++++++++++++++++++++++++++++

No. By weights we mean a value between :math:`0` and :math:`1` that represent a player's contribution to
the team's overall victory (if they win). We are however currently working on it.


3. Does this library support score margins?
+++++++++++++++++++++++++++++++++++++++++++

No. Score margins are much harder to implement and require reinterpreting the models as differences
in scores. The update rules for each model is different, so more than likely an entirely new
model will need to be constructed.

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

Yes. Simply adjust ``sigma`` by a small value as needed when you feel a player has been inactive. A small negative
delta added every day after being inactive till the value reaches the default sigma is usually good enough.
Make sure to test against your own data to ensure it actually predicts outcomes.
