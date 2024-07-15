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
        href="https://github.com/vivekjoshy/openskill.py/actions/workflows/main.yml">
            <img
                src="https://github.com/vivekjoshy/openskill.py/actions/workflows/main.yml/badge.svg"
                alt="Tests"
    />
    </a>
    <a
        href="https://codecov.io/gh/vivekjoshy/openskill.py">
            <img
                src="https://codecov.io/gh/vivekjoshy/openskill.py/branch/main/graph/badge.svg?token=Ep07QEelsi"
                alt="codecov" />
    <a
        href="https://openskill.me/en/latest/?badge=latest">
            <img
                src="https://readthedocs.org/projects/openskillpy/badge/?version=latest"
                    alt="Documentation Status"
            />
    </a>
    <img
        src="https://img.shields.io/github/all-contributors/vivekjoshy/openskill.py/main"
    />
    <a style="border-width:0" href="https://doi.org/10.21105/joss.05901">
      <img src="https://joss.theoj.org/papers/10.21105/joss.05901/status.svg" alt="DOI badge" >
    </a>
</p>



## Description

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/openskill) ![Conda (channel only)](https://anaconda.org/conda-forge/openskill/badges/version.svg) ![PyPI - Implementation](https://img.shields.io/pypi/implementation/openskill)

[![Discord](https://img.shields.io/discord/1127581396345556994?logo=discord&label=Official%20Discord%20Server&color=%235865F2&link=https%3A%2F%2Fdiscord.com%2Finvite%2F4JNDeHMYkM)](https://discord.com/invite/4JNDeHMYkM)

In the multifaceted world of online gaming, an accurate multiplayer rating system plays a crucial role. A multiplayer rating system measures and compares players' skill levels in competitive games to ensure balanced match-making, boosting overall gaming experiences. Currently, TrueSkill by Microsoft Research is a notable rating system, but gaming communities are yearning for faster, more adaptable alternatives.

Here are *some*, but not all, of the reasons you should drop TrueSkill
and bury Elo once and for all:

- Multiplayer.
- Multifaction.
- Asymmetric faction size.
- Predict Win, Draw and Rank Outcomes.
- Per Player Weights
- Partial Play
- 150% faster than TrueSkill.
- 100% Pure Python.
- 100% Test Coverage.
- CPython and PyPy Support.
- 5 Separate Models.
- Fine-grained control of mathematical constants.
- Open License
- Accuracy on par with TrueSkill.


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

# Support
If you're struggling with any of the concepts, please search the discussions section to see if your question has already been answered.
If you can't find an answer, please open a new [discussion](https://github.com/vivekjoshy/openskill.py/discussions) and we'll try to help you out.
You can also get help from the official [Discord Server](https://discord.com/invite/4JNDeHMYkM>). If you have a feature request, or want to report
a bug please create a new [issue](https://github.com/vivekjoshy/openskill.py/issues/new/choose) if one already doesn't exist.

# References
This project is originally based off the [openskill.js](https://github.com/philihp/openskill.js) package. All of the Weng-Lin models are based off the work in this wonderful [paper](https://jmlr.org/papers/v12/weng11a.html) or are the derivatives of algorithms found in it.

- Julia Ibstedt, Elsa Rådahl, Erik Turesson, and Magdalena vande Voorde. Application and further development of trueskill™ ranking in sports. 2019.
- Ruby C. Weng and Chih-Jen Lin. A bayesian approximation method for online ranking. Journal of Machine Learning Research, 12(9):267–300, 2011. URL: http://jmlr.org/papers/v12/weng11a.html.

## Implementations in other Languages
- [Javascript](https://github.com/philihp/openskill.js)
- [Elixir](https://github.com/philihp/openskill.ex)
- [Kotlin](https://github.com/brezinajn/openskill.kt)
- [Lua](https://github.com/bstummer/openskill.lua)
