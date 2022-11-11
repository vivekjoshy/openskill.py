[![Stand With Ukraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner2-direct.svg)](https://vshymanskyy.github.io/StandWithUkraine)
![](https://i.imgur.com/tSTFzZY.gif)


[![Tests](https://github.com/OpenDebates/openskill.py/actions/workflows/main.yml/badge.svg)](https://github.com/OpenDebates/openskill.py/actions/workflows/main.yml) [![codecov](https://codecov.io/gh/OpenDebates/openskill.py/branch/main/graph/badge.svg?token=Ep07QEelsi)](https://codecov.io/gh/OpenDebates/openskill.py) ![PyPI - Downloads](https://img.shields.io/pypi/dm/openskill) [![Documentation Status](https://readthedocs.org/projects/openskillpy/badge/?version=latest)](https://openskillpy.readthedocs.io/en/latest/?badge=latest) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/openskill)

[![Anaconda-Server Badge](https://anaconda.org/conda-forge/openskill/badges/version.svg)](https://anaconda.org/conda-forge/openskill)

Python implementation of Weng-Lin Bayesian ranking, a better, license-free alternative to TrueSkill

This is a port of the amazing [openskill.js](https://github.com/philihp/openskill.js) package.

## Installation
```shell
pip install openskill
```

## Usage
```python
>>> from openskill import Rating, rate
>>> a1 = Rating()
>>> a1
Rating(mu=25.0, sigma=8.333333333333334)
>>> a2 = Rating(mu=32.444, sigma=5.123)
>>> a2
Rating(mu=32.444, sigma=5.123)
>>> b1 = Rating(43.381, 2.421)
>>> b1
Rating(mu=43.381, sigma=2.421)
>>> b2 = Rating(mu=25.188, sigma=6.211)
>>> b2
Rating(mu=25.188, sigma=6.211)
```

If `a1` and `a2` are on a team, and wins against a team of `b1` and `b2`, send this into rate:

```python
>>> [[x1, x2], [y1, y2]] = rate([[a1, a2], [b1, b2]])
>>> x1, x2, y1, y2
(Rating(mu=28.669648436582808, sigma=8.071520788025197), Rating(mu=33.83086971107981, sigma=5.062772998705765), Rating(mu=43.071274808241974, sigma=2.4166900452721256), Rating(mu=23.149503312339064, sigma=6.1378606973362135))
```

You can also create `Rating` objects by importing `create_rating`:

```python
>>> from openskill import create_rating
>>> x1 = [28.669648436582808, 8.071520788025197]
>>> x1 = create_rating(x1)
>>> x1
Rating(mu=28.669648436582808, sigma=8.071520788025197)
```

## Ranks
When displaying a rating, or sorting a list of ratings, you can use `ordinal`:

```python
>>> from openskill import ordinal
>>> ordinal([43.07, 2.42])
35.81
```

By default, this returns `mu - 3 * sigma`, showing a rating for which there's a [99.7%](https://en.wikipedia.org/wiki/68%E2%80%9395%E2%80%9399.7_rule) likelihood the player's true rating is higher, so with early games, a player's ordinal rating will usually go up and could go up even if that player loses.

## Artificial Ranks
If your teams are listed in one order but your ranking is in a different order, for convenience you can specify a ranks option, such as:

```python
>>> a1 = b1 = c1 = d1 = Rating()
>>> result = [[a2], [b2], [c2], [d2]] = rate([[a1], [b1], [c1], [d1]], rank=[4, 1, 3, 2])
>>> result
[[Rating(mu=20.96265504062538, sigma=8.083731307186588)], [Rating(mu=27.795084971874736, sigma=8.263160757613477)], [Rating(mu=24.68943500312503, sigma=8.083731307186588)], [Rating(mu=26.552824984374855, sigma=8.179213704945203)]]
```

It's assumed that the lower ranks are better (wins), while higher ranks are worse (losses). You can provide a score instead, where lower is worse and higher is better. These can just be raw scores from the game, if you want.

Ties should have either equivalent rank or score.

```python
>>> a1 = b1 = c1 = d1 = Rating()
>>> result = [[a2], [b2], [c2], [d2]] = rate([[a1], [b1], [c1], [d1]], score=[37, 19, 37, 42])
>>> result
[[Rating(mu=24.68943500312503, sigma=8.179213704945203)], [Rating(mu=22.826045021875203, sigma=8.179213704945203)], [Rating(mu=24.68943500312503, sigma=8.179213704945203)], [Rating(mu=27.795084971874736, sigma=8.263160757613477)]]
```

## Predicting Winners

You can compare two or more teams to get the probabilities of each team winning.

```python
>>> from openskill import predict_win
>>> a1 = Rating()
>>> a2 = Rating(mu=33.564, sigma=1.123)
>>> predictions = predict_win(teams=[[a1], [a2]])
>>> predictions
[0.45110901512761536, 0.5488909848723846]
>>> sum(predictions)
1.0
```

## Predicting Draws

You can compare two or more teams to get the probabilities of the match drawing.

```python
>>> from openskill import predict_draw
>>> a1 = Rating()
>>> a2 = Rating(mu=33.564, sigma=1.123)
>>> prediction = predict_draw(teams=[[a1], [a2]])
>>> prediction
0.09025541153402594
```

## Choosing Models

The default model is `PlackettLuce`. You can import alternate models from `openskill.models` like so:

```python
>>> from openskill.models import BradleyTerryFull
>>> a1 = b1 = c1 = d1 = Rating()
>>> rate([[a1], [b1], [c1], [d1]], rank=[4, 1, 3, 2], model=BradleyTerryFull)
[[Rating(mu=17.09430584957905, sigma=7.5012190693964005)], [Rating(mu=32.90569415042095, sigma=7.5012190693964005)], [Rating(mu=22.36476861652635, sigma=7.5012190693964005)], [Rating(mu=27.63523138347365, sigma=7.5012190693964005)]]
```

### Available Models
- `BradleyTerryFull`: Full Pairing for Bradley-Terry
- `BradleyTerryPart`: Partial Pairing for Bradley-Terry
- `PlackettLuce`: Generalized Bradley-Terry
- `ThurstoneMostellerFull`: Full Pairing for Thurstone-Mosteller
- `ThurstoneMostellerPart`: Partial Pairing for Thurstone-Mosteller

### Which Model Do I Want?

- Bradley-Terry rating models follow a logistic distribution over a player's skill, similar to Glicko.
- Thurstone-Mosteller rating models follow a gaussian distribution, similar to TrueSkill. Gaussian CDF/PDF functions differ in implementation from system to system (they're all just chebyshev approximations anyway). The accuracy of this model isn't usually as great either, but tuning this with an alternative gamma function can improve the accuracy if you really want to get into it.
- Full pairing should have more accurate ratings over partial pairing, however in high k games (like a 100+ person marathon race), Bradley-Terry and Thurstone-Mosteller models need to do a calculation of joint probability which involves is a k-1 dimensional integration, which is computationally expensive. Use partial pairing in this case, where players only change based on their neighbors.
- Plackett-Luce (**default**) is a generalized Bradley-Terry model for k ≥ 3 teams. It scales best.

## Advanced Usage
You can learn more about how to configure this library to suit your custom needs in the [project documentation](https://openskillpy.readthedocs.io/en/stable/advanced.html).


## Implementations in other Languages
- [Javascript](https://github.com/philihp/openskill.js)
- [Elixir](https://github.com/philihp/openskill.ex)
- [Kotlin](https://github.com/brezinajn/openskill.kt)
- [Lua](https://github.com/bstummer/openskill.lua)

