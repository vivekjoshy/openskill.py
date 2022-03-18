from openskill import Rating, rate


def test_rate():

    # Accepts a tau term
    a = Rating(sigma=3)
    b = Rating(sigma=3)
    [[winner], [loser]] = rate([[a], [b]], tau=0.3)
    assert [[winner], [loser]] == [
        [Rating(mu=25.624880438870754, sigma=2.9879993738476953)],
        [Rating(mu=24.375119561129246, sigma=2.9879993738476953)],
    ]

    # Prevents sigma from rising
    a = Rating(mu=40, sigma=3)
    b = Rating(mu=-20, sigma=3)
    [[winner], [loser]] = rate([[a], [b]], tau=0.3, prevent_sigma_increase=True)
    assert [[winner], [loser]] == [
        [Rating(mu=40.00032667136128, sigma=3)],
        [Rating(mu=-20.000326671361275, sigma=3)],
    ]

    # Ensures sigma decreases
    a = Rating()
    b = Rating()
    [[winner], [loser]] = rate([[a], [b]], tau=0.3, prevent_sigma_increase=True)
    assert [[winner], [loser]] == [
        [Rating(mu=27.6372798316677, sigma=8.070625245679999)],
        [Rating(mu=22.3627201683323, sigma=8.070625245679999)],
    ]
