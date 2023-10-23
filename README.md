<p align="center" style="text-align: center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://i.imgur.com/7yAVFkZ.png">
  <source media="(prefers-color-scheme: light)" srcset="https://i.imgur.com/UvrkUF3.png">
  <img alt="Multiplayer Rating System. No Friction." src="https://i.imgur.com/QJUy18S.png">
</picture>
</p>

<p align="center" style="text-align: center">A faster and open license asymmetric multi-team, multiplayer rating system comparable to TrueSkill.</p>

<p align="center" style="text-align: center">
    <a href="https://stand-with-ukraine.pp.ua">
        <img
            src="https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/badges/StandWithUkraine.svg"
            alt="Stand With Ukraine"
        />
    </a>
</p>

<p align="center" style="text-align: center">
    <a
        href="https://github.com/OpenDebates/openskill.py/actions/workflows/main.yml">
            <img
                src="https://github.com/OpenDebates/openskill.py/actions/workflows/main.yml/badge.svg"
                alt="Tests"
    />
    </a>
    <a
        href="https://codecov.io/gh/OpenDebates/openskill.py">
            <img
                src="https://codecov.io/gh/OpenDebates/openskill.py/branch/main/graph/badge.svg?token=Ep07QEelsi"
                alt="codecov" />
    </a>
    <img src="https://img.shields.io/pypi/dm/openskill"
        alt="PyPI - Downloads"
    />
    <a
        href="https://openskill.me/en/latest/?badge=latest">
            <img
                src="https://readthedocs.org/projects/openskillpy/badge/?version=latest"
                    alt="Documentation Status"
            />
    </a>
    <img
        src="https://img.shields.io/github/all-contributors/OpenDebates/openskill.py/main"
    />
</p>



## Description

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/openskill) ![Conda (channel only)](https://img.shields.io/conda/vn/conda-forge/openskill) ![PyPI - Implementation](https://img.shields.io/pypi/implementation/openskill)

[![Discord](https://img.shields.io/discord/1127581396345556994?logo=discord&label=Official%20Discord%20Server&color=%235865F2&link=https%3A%2F%2Fdiscord.com%2Finvite%2F4JNDeHMYkM)](https://discord.com/invite/4JNDeHMYkM)

Here are *some*, but not all, of the reasons you should drop TrueSkill
and bury Elo once and for all:

- Multiplayer.
- Multifaction.
- Asymmetric faction size.
- Predict Win, Draw and Rank Outcomes.
- 150% faster than TrueSkill.
- 100% Pure Python.
- 100% Test Coverage.
- CPython and PyPy Support.
- 5 Separate Models.
- Fine-grained control of mathematical constants.
- Open License
- Up to 7% more accurate than TrueSkill.


## Installation
```shell
pip install openskill
```

## Usage

The official documentation is hosted [here](https://openskill.me/en/stable/).
Please refer to it for details on how to use this library.

### Limited Example

```python
>>> from openskill.models import PlackettLuce
>>> model = PlackettLuce()
>>> model.rating()
PlackettLuceRating(mu=25.0, sigma=8.333333333333334)
>>> r = model.rating
>>> [[a, b], [x, y]] = [[r(), r()], [r(), r()]]
>>> [[a, b], [x, y]] = model.rate([[a, b], [x, y]])
>>> a
PlackettLuceRating(mu=26.964294621803063, sigma=8.177962604389991)
>>> x
PlackettLuceRating(mu=23.035705378196937, sigma=8.177962604389991)
>>> (a == b) and (x == y)
True
```

# References
This project is originally based off the [openskill.js](https://github.com/philihp/openskill.js) package. All of the Weng-Lin models are based off the work in this wonderful [paper](https://jmlr.org/papers/v12/weng11a.html) or are the derivatives of algorithms found in it.

- Julia Ibstedt, Elsa Rådahl, Erik Turesson, and Magdalena vande Voorde. Application and further development of trueskill™ ranking in sports. 2019.
- Ruby C. Weng and Chih-Jen Lin. A bayesian approximation method for online ranking. Journal of Machine Learning Research, 12(9):267–300, 2011. URL: http://jmlr.org/papers/v12/weng11a.html.

## Implementations in other Languages
- [Javascript](https://github.com/philihp/openskill.js)
- [Elixir](https://github.com/philihp/openskill.ex)
- [Kotlin](https://github.com/brezinajn/openskill.kt)
- [Lua](https://github.com/bstummer/openskill.lua)
