"""
Common functions for all models.
"""
from typing import Any, List, Union


def _unary_minus(number: float) -> float:
    """
    Takes value of a number and makes it negative.

    :param number: A number to convert.
    :return: Converted number.
    """
    return -number


def _arg_sort(vector: List[Any]) -> List[int]:
    """
    Returns the indices that would sort a vector.

    :param vector: A list of objects.
    :return: Rank vector without ties.
    """
    return [i for (v, i) in sorted((v, i) for (i, v) in enumerate(vector))]


def _rank_data(vector: List[Any]) -> List[int]:
    """
    Sorting with 'competition ranking'. Pure python equivalent of
    :code:`scipy.stats.rankdata` function.

    :param vector: A list of objects.
    :return: Rank vector with ties.
    """
    vector_length = len(vector)
    arg_sort_rank_vector = _arg_sort(vector)
    arg_sorted_vector = [vector[rank] for rank in arg_sort_rank_vector]
    sum_ranks = 0
    duplicate_count = 0
    rank_vector_with_ties = [0] * vector_length
    for index in range(vector_length):
        sum_ranks += index
        duplicate_count += 1
        if (
            index == vector_length - 1
            or arg_sorted_vector[index] != arg_sorted_vector[index + 1]
        ):
            for j in range(index - duplicate_count + 1, index + 1):
                rank_vector_with_ties[arg_sort_rank_vector[j]] = (
                    index + 1 - duplicate_count + 1
                )
            sum_ranks = 0
            duplicate_count = 0
    return rank_vector_with_ties


def _matrix_transpose(matrix: List[List[Any]]) -> List[List[Any]]:
    """
    Transpose a matrix.

    :param matrix: A matrix in the form of a list of lists.
    :return: A transposed matrix.
    """
    return [list(row) for row in zip(*matrix)]
