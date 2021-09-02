def z(**options) -> float:
    if "z" in options:
        return options["z"]
    else:
        return 3


def mu(**options) -> float:
    if "mu" in options:
        return options["mu"]
    else:
        return 25


def sigma(**options) -> float:
    if "sigma" in options:
        return options["sigma"]
    else:
        return mu(**options) / z(**options)


def epsilon(**options) -> float:
    if "epsilon" in options:
        return options["epsilon"]
    else:
        return 0.0001


def beta(**options) -> float:
    if "beta" in options:
        return options["beta"]
    else:
        return sigma(**options) / 2


def beta_squared(**options) -> float:
    if "beta_squared" in options:
        return options["beta_squared"]
    else:
        return beta(**options) ** 2


class Constants:
    def __init__(self, **options):
        self.EPSILON: float = epsilon(**options)
        self.TWO_BETA_SQUARED: float = 2 * beta_squared(**options)
        self.BETA_SQUARED: float = beta_squared(**options)
        self.Z: float = z(**options)
