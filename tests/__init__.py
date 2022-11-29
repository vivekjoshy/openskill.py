import math
from abc import ABC, abstractmethod
from collections import UserString
from collections.abc import Mapping, Sequence, Set
from decimal import Decimal
from numbers import Real
from typing import List

from openskill import Rating


def approx(actual, expected, rel_tol=1e-8, abs_tol=None):
    if abs_tol is None:
        abs_tol = 0

    handlers = [
        StringHandler(),
        RealNumHandler(),
        MappingHandler(),
        SequenceHandler(),
        SetHandler(),
        CompositeHandler(),
    ]

    for handler in handlers:
        result = handler.handle(actual, expected, rel_tol=rel_tol, abs_tol=abs_tol)
        if result is not None:
            return result

    msg = f"Cannot compare {actual} and {expected} of types {type(actual)} and {type(expected)}"
    raise TypeError(msg)


class GenericHandler(ABC):
    allowed_types: List = []
    forbidden_types: List = []

    def handle(self, actual, expected, **kwargs):
        if self.can_handle(actual, expected):
            return self.check_equal(actual, expected, **kwargs)

    @abstractmethod
    def check_equal(self, actual, expected, **kwargs):
        pass

    def can_handle(self, actual, expected):
        return all(self._can_handle_one_item(item) for item in (actual, expected))

    def _can_handle_one_item(self, item):
        in_allowed_types = any(isinstance(item, type_) for type_ in self.allowed_types)

        in_forbidden_types = any(
            isinstance(item, type_) for type_ in self.forbidden_types
        )

        return in_allowed_types and not in_forbidden_types


class StringHandler(GenericHandler):
    allowed_types = [
        str,
        UserString,
    ]

    @staticmethod
    def check_equal(actual, expected, **kwargs):
        return actual == expected


class RealNumHandler(GenericHandler):
    allowed_types = [
        Real,
        Decimal,
    ]

    def check_equal(self, actual, expected, **kwargs):
        return math.isclose(
            actual,
            expected,
            rel_tol=kwargs["rel_tol"],
            abs_tol=kwargs["abs_tol"],
        )


class MappingHandler(GenericHandler):
    allowed_types = [
        Mapping,
    ]

    @staticmethod
    def check_equal(actual, expected, **kwargs):
        if len(actual) != len(expected):
            return False

        return all(
            approx(k1, k2, **kwargs) and approx(v1, v2, **kwargs)
            for (k1, v1), (k2, v2) in zip(
                sorted(actual.items()), sorted(expected.items())
            )
        )


class SequenceHandler(GenericHandler):
    allowed_types = [Sequence, Rating]

    forbidden_types = [
        str,
        Mapping,
    ]

    @staticmethod
    def check_equal(actual, expected, **kwargs):
        if all(isinstance(item, Sequence) for item in (actual, expected)):
            if len(actual) != len(expected):
                return False
            return all(
                approx(val1, val2, **kwargs) for val1, val2 in zip(actual, expected)
            )
        elif isinstance(actual, Rating) and isinstance(expected, Sequence):
            if len(expected) == 2:
                if math.isclose(
                    actual.mu,
                    expected[0],
                    rel_tol=kwargs["rel_tol"],
                    abs_tol=kwargs["abs_tol"],
                ) and math.isclose(
                    actual.sigma,
                    expected[1],
                    rel_tol=kwargs["rel_tol"],
                    abs_tol=kwargs["abs_tol"],
                ):
                    return True
                else:
                    return False
            else:
                return False
        elif isinstance(actual, Sequence) and isinstance(expected, Rating):
            if len(actual) == 2:
                if math.isclose(
                    actual[0],
                    expected.mu,
                    rel_tol=kwargs["rel_tol"],
                    abs_tol=kwargs["abs_tol"],
                ) and math.isclose(
                    actual[1],
                    expected.sigma,
                    rel_tol=kwargs["rel_tol"],
                    abs_tol=kwargs["abs_tol"],
                ):
                    return True
                else:
                    return False
            else:
                return False
        else:
            if math.isclose(
                actual.mu,
                expected.mu,
                rel_tol=kwargs["rel_tol"],
                abs_tol=kwargs["abs_tol"],
            ) and math.isclose(
                actual.sigma,
                expected.sigma,
                rel_tol=kwargs["rel_tol"],
                abs_tol=kwargs["abs_tol"],
            ):
                return True
            else:
                return False


class SetHandler(GenericHandler):
    allowed_types = [
        Set,
    ]

    @staticmethod
    def check_equal(actual, expected, **kwargs):
        # sets are compared exactly only
        return actual == expected


class CompositeHandler(GenericHandler):
    def can_handle(self, actual, expected):
        return all([hasattr(item, "__dict__") for item in (actual, expected)])

    @staticmethod
    def check_equal(actual, expected, **kwargs):
        return MappingHandler().handle(
            actual.__dict__,
            expected.__dict__,
            **kwargs,
        )


class RatingHandler(GenericHandler):
    allowed_types = [
        Rating,
    ]

    @staticmethod
    def check_equal(actual, expected, **kwargs):
        if math.isclose(
            actual.mu, expected.mu, rel_tol=kwargs["rel_tol"], abs_tol=kwargs["abs_tol"]
        ) and math.isclose(
            actual.sigma,
            expected.sigma,
            rel_tol=kwargs["rel_tol"],
            abs_tol=kwargs["abs_tol"],
        ):
            return True
        else:
            return False
