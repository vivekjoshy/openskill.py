import pytest

from openskill.constants import beta, beta_squared, epsilon, mu, sigma, tau, z


def test_constants():
    assert z(z=5) == 5
    assert z() == 3

    assert mu(mu=23) == 23
    assert mu() == 25

    assert sigma(sigma=5) == 5
    assert sigma() == 25 / 3

    assert epsilon(epsilon=0.0002) == 0.0002
    assert epsilon() == 0.0001

    assert beta(beta=3.6) == 3.6
    assert beta() == pytest.approx(4.166666666666667)

    assert beta_squared(beta_squared=16.2) == 16.2
    assert beta_squared() == pytest.approx(17.361111111111114)

    assert tau(tau=0.3) == 0.3
    assert tau() == pytest.approx(0.08333333)
