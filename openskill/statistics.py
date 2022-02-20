import sys

import scipy.stats

normal = scipy.stats.norm(0, 1)


def phi_major(x):
    return normal.cdf(x)


def phi_major_inverse(x):
    return normal.ppf(x)


def phi_minor(x):
    return normal.pdf(x)


def v(x, t):
    xt = x - t
    denom = phi_major(xt)
    return -xt if (denom < sys.float_info.epsilon) else phi_minor(xt) / denom


def w(x, t):
    xt = x - t
    denom = phi_major(xt)
    if denom < sys.float_info.epsilon:
        return 1 if (x < 0) else 0
    return v(x, t) * (v(x, t) + xt)


def vt(x, t):
    xx = abs(x)
    b = phi_major(t - xx) - phi_major(-t - xx)
    if b < 1e-5:
        if x < 0:
            return -x - t
        return -x + t
    a = phi_minor(-t - xx) - phi_minor(t - xx)
    return (-a if x < 0 else a) / b


def wt(x, t):
    xx = abs(x)
    b = phi_major(t - xx) - phi_major(-t - xx)
    if b < sys.float_info.epsilon:
        return 1.0
    return ((t - xx) * phi_minor(t - xx) + (t + xx) * phi_minor(-t - xx)) / b + vt(
        x, t
    ) * vt(x, t)
