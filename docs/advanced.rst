:og:description: Experimental and advanced features for OpenSkill like time decay and additive time dynamics factor.
:og:image: https://i.imgur.com/tSTFzZY.gif
:og:image:alt: Logo of OpenSkill for Python

==============
Advanced Guide
==============

.. warning::

  These features have not been tested against real world data to check for their efficacy. You should test the parameters against your own data to ensure they suit your needs.


Additive Dynamics Factor
========================
If ``sigma`` gets too small, eventually the rating change volatility will decrease. To prevent this you can pass the parameter ``tau`` to :class:`~openskill.rate.rate`. ``tau`` should preferably be a small decimal of two significant digits.

Here are some visuals of how ordinals change with different ``tau`` values:

.. image:: _static/tau.png

You can combine ``tau`` with another parameter ``prevent_sigma_increase`` to ensure the win probability always remains congruent with the actual win rate.

Here is how this looks:

.. image:: _static/ordinals.png
