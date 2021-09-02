from openskill.constants import Constants


def ordinal(mu: float, sigma: float, **options) -> float:
    # Calculate Z
    z = Constants(**options).Z
    return mu - z * sigma
