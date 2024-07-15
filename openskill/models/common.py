"""
Common functions for all models.
"""

from typing import Any, List


def _unary_minus(number: float) -> float:
    """
    Takes value of a number and makes it negative.

    :param number: A number to convert.
    :return: Converted number.
    """
    return -number


def _matrix_transpose(matrix: List[List[Any]]) -> List[List[Any]]:
    """
    Transpose a matrix.

    :param matrix: A matrix in the form of a list of lists.
    :return: A transposed matrix.
    """
    return [list(row) for row in zip(*matrix)]


def _normalize(
    vector: List[float], target_minimum: float, target_maximum: float
) -> List[float]:
    """
    Normalizes a vector to a target range of values.

    :param vector: A vector to normalize.
    :param target_minimum: Minimum value to scale the values between.
    :param target_maximum: Maximum value to scale the values between.
    :return: Normalized vector.
    """

    if len(vector) == 1:
        return [target_maximum]

    source_minimum = min(vector)
    source_maximum = max(vector)
    source_range = source_maximum - source_minimum
    target_range = target_maximum - target_minimum

    if source_range == 0:
        source_range = 0.0001

    scaled_vector = [
        ((((value - source_minimum) / source_range) * target_range) + target_minimum)
        for value in vector
    ]

    return scaled_vector
