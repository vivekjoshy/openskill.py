:py:mod:`openskill.models.common`
=================================

.. py:module:: openskill.models.common

.. autoapi-nested-parse::

   Common functions for all models.



Module Contents
---------------


Functions
~~~~~~~~~

.. autoapisummary::

   openskill.models.common._arg_sort
   openskill.models.common._matrix_transpose
   openskill.models.common._rank_data
   openskill.models.common._unary_minus



.. py:function:: _arg_sort(vector)

   Returns the indices that would sort a vector.

   :param vector: A list of objects.
   :return: Rank vector without ties.


.. py:function:: _matrix_transpose(matrix)

   Transpose a matrix.

   :param matrix: A matrix in the form of a list of lists.
   :return: A transposed matrix.


.. py:function:: _rank_data(vector)

   Sorting with 'competition ranking'. Pure python equivalent of
   :code:`scipy.stats.rankdata` function.

   :param vector: A list of objects.
   :return: Rank vector with ties.


.. py:function:: _unary_minus(number)

   Takes value of a number and makes it negative.

   :param number: A number to convert.
   :return: Converted number.


