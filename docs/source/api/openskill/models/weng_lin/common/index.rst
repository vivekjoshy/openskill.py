:py:mod:`openskill.models.weng_lin.common`
==========================================

.. py:module:: openskill.models.weng_lin.common

.. autoapi-nested-parse::

   Common functions for the Weng-Lin models.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   openskill.models.weng_lin.common._ladder_pairs
   openskill.models.weng_lin.common._unwind
   openskill.models.weng_lin.common.phi_major
   openskill.models.weng_lin.common.phi_major_inverse
   openskill.models.weng_lin.common.phi_minor
   openskill.models.weng_lin.common.v
   openskill.models.weng_lin.common.vt
   openskill.models.weng_lin.common.w
   openskill.models.weng_lin.common.wt



.. py:function:: _ladder_pairs(teams)

   Returns a list of pairs of ranks that are adjacent in the ladder.

   :param teams: A list of teams.
   :return: A list of pairs of teams that are adjacent in the ladder.


.. py:function:: _unwind(tenet, objects)

   Retain the stochastic tenet of a sort to revert original sort order.

   :param tenet: A list of tenets for each object in the list.

   :param objects: A list of teams to sort.
   :return: Ordered objects and their tenets.


.. py:function:: phi_major(x)

   Normal cumulative distribution function.

   :param x: A number.
   :return: A number.


.. py:function:: phi_major_inverse(x)

   Normal inverse cumulative distribution function.

   :param x: A number.
   :return: A number.


.. py:function:: phi_minor(x)

   Normal probability density function.

   :param x: A number.
   :return: A number.


.. py:function:: v(x, t)

   The function :math:`V` as defined in :cite:t:`JMLR:v12:weng11a`

   :param x: A number.
   :param t: A number.
   :return: A number.


.. py:function:: vt(x, t)

   The function :math:`\tilde{V}` as defined in :cite:t:`JMLR:v12:weng11a`

   :param x: A number.
   :param t: A number.
   :return: A number.


.. py:function:: w(x, t)

   The function :math:`W` as defined in :cite:t:`JMLR:v12:weng11a`

   :param x: A number.
   :param t: A number.
   :return: A number.


.. py:function:: wt(x, t)

   The function :math:`\tilde{W}` as defined in :cite:t:`JMLR:v12:weng11a`

   :param x: A number.
   :param t: A number.
   :return: A number.


