"""
Common functions for the Weng-Lin models.
"""

import sys
from itertools import zip_longest
from statistics import NormalDist
from typing import Any, List, Tuple

from openskill.models.common import _matrix_transpose

_normal = NormalDist()


def _unwind(tenet: List[float], objects: List[Any]) -> Tuple[List[Any], List[float]]:
    """
    Retain the stochastic tenet of a sort to revert original sort order.

    :param tenet: A list of tenets for each object in the list.

    :param objects: A list of teams to sort.
    :return: Ordered objects and their tenets.
    """

    def _pick_zeroth_index(item: Tuple[float, Any]) -> float:
        """
        Returns the first item in a list.

        :param item: A list of objects.
        :return: The first item in the list.
        """
        return item[0]

    def _sorter(
        objects_to_sort: List[Any],
    ) -> Tuple[List[Any], List[float]]:
        """
        Sorts a list of objects based on a tenet.

        :param objects_to_sort: A list of objects to sort.
        :return: A tuple of the sorted objects and their tenets.
        """
        matrix = [[tenet[i], [x, i]] for i, x in enumerate(objects_to_sort)]
        unsorted_matrix = _matrix_transpose(matrix)
        if unsorted_matrix:
            zipped_matrix = list(zip(unsorted_matrix[0], unsorted_matrix[1]))
            zipped_matrix.sort(key=_pick_zeroth_index)
            sorted_matrix = [x for _, x in zipped_matrix]
            return [x for x, _ in sorted_matrix], [x for _, x in sorted_matrix]
        else:
            return [], []

    return _sorter(objects) if isinstance(objects, list) else _sorter


def phi_major(x: float) -> float:
    """
    Normal cumulative distribution function.

    :param x: A number.
    :return: A number.
    """
    return _normal.cdf(x)


def phi_major_inverse(x: float) -> float:
    """
    Normal inverse cumulative distribution function.

    :param x: A number.
    :return: A number.
    """
    return _normal.inv_cdf(x)


def phi_minor(x: float) -> float:
    """
    Normal probability density function.

    :param x: A number.
    :return: A number.
    """
    return _normal.pdf(x)


def v(x: float, t: float) -> float:
    """
    The function :math:`V` as defined in :cite:t:`JMLR:v12:weng11a`

    :param x: A number.
    :param t: A number.
    :return: A number.
    """
    xt = x - t
    denominator = phi_major(xt)
    return (
        -xt if (denominator < sys.float_info.epsilon) else phi_minor(xt) / denominator
    )


def w(x: float, t: float) -> float:
    """
    The function :math:`W` as defined in :cite:t:`JMLR:v12:weng11a`

    :param x: A number.
    :param t: A number.
    :return: A number.
    """
    xt = x - t
    denominator = phi_major(xt)
    if denominator < sys.float_info.epsilon:
        return 1 if (x < 0) else 0
    return v(x, t) * (v(x, t) + xt)


def vt(x: float, t: float) -> float:
    r"""
    The function :math:`\tilde{V}` as defined in :cite:t:`JMLR:v12:weng11a`

    :param x: A number.
    :param t: A number.
    :return: A number.
    """
    xx = abs(x)
    b = phi_major(t - xx) - phi_major(-t - xx)
    if b < 1e-5:
        if x < 0:
            return -x - t
        return -x + t
    a = phi_minor(-t - xx) - phi_minor(t - xx)
    return (-a if x < 0 else a) / b


def wt(x: float, t: float) -> float:
    r"""
    The function :math:`\tilde{W}` as defined in :cite:t:`JMLR:v12:weng11a`

    :param x: A number.
    :param t: A number.
    :return: A number.
    """
    xx = abs(x)
    b = phi_major(t - xx) - phi_major(-t - xx)
    if b < sys.float_info.epsilon:
        return 1.0
    return ((t - xx) * phi_minor(t - xx) + (t + xx) * phi_minor(-t - xx)) / b + vt(
        x, t
    ) * vt(x, t)


def _ladder_pairs(teams: List[Any]) -> List[List[Any]]:
    """
    Returns a list of pairs of ranks that are adjacent in the ladder.

    :param teams: A list of teams.
    :return: A list of pairs of teams that are adjacent in the ladder.
    """
    left: List[Any] = [None]
    left.extend(teams[:-1])
    right: List[Any] = list(teams[1:])
    right.append(None)
    zipped_lr = zip_longest(left, right)
    result = []
    for _left, _right in zipped_lr:
        if _left and _right:
            result.append([_left, _right])
        elif _left and not _right:
            result.append([_left])
        elif not _left and _right:
            result.append([_right])
        else:
            result.append([])
    return result
