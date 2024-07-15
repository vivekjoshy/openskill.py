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

   openskill.models.common._matrix_transpose
   openskill.models.common._normalize
   openskill.models.common._unary_minus



.. py:function:: _matrix_transpose(matrix)

   Transpose a matrix.

   :param matrix: A matrix in the form of a list of lists.
   :return: A transposed matrix.


.. py:function:: _normalize(vector, target_minimum, target_maximum)

   Normalizes a vector to a target range of values.

   :param vector: A vector to normalize.
   :param target_minimum: Minimum value to scale the values between.
   :param target_maximum: Maximum value to scale the values between.
   :return: Normalized vector.


.. py:function:: _unary_minus(number)

   Takes value of a number and makes it negative.

   :param number: A number to convert.
   :return: Converted number.


