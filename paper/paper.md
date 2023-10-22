---
title: 'OpenSkill: A faster asymmetric multi-team, multiplayer rating system'
tags:
  - Python
  - Ranking
  - Rating System
  - Bayesian Ranking
  - Online Ranking
author:
  - "Vivek Joshy"
authors:
  - name: Vivek Joshy
    orcid: 0000-0003-2443-8827
    affiliation: 1
affiliations:
 - name: Independent Researcher, India
   index: 1
date: 21 July 2023
bibliography: paper.bib
---

# Summary

Online ranking has been a long-standing issue due to many players being stuck with a
particular rank, known colloquially as "Elo Hell" [@Elo]. Another major issue
is that most ranking systems are designed for 1v1 games, and do not scale well
to multiplayer games. If they are designed for that purpose, the algorithms that
are available are inefficient. This library is designed to  address all of these
problems while being faster than and just as accurate as proprietary algorithms.

# Statement of need

Bayesian inference of skill ratings from game outcomes is a crucial aspect of online
video game development and research. This is usually challenging because the players' performance changes
over time and also varies based on who they are competing against. Our project primarily targets game developers
and researchers interested in ranking players fairly and accurately. Nevertheless, the problem that the
software solves is applicable to any context where you have multiple players or entities and you need to track
their skills over time while they compete against each other.

The OpenSkill library furnishes a versatile suite of models and algorithms designed to support a broad spectrum
of applications. While popular use cases include assisting video game developers and researchers dealing with
multi-agent scripting environments like Neural MMO [@suarez2019neural], its practical use extends far beyond this
particular domain. For instance, it finds substantial utilization in recommendation systems, where it efficiently
gauges unique user behaviors and preferences to suggest personalized recommendations. The matchmaking mechanisms
in ranking of sports players as seen by Opta Analyst [@Rico_2022] and dating apps are another area where OpenSkill
proves crucial, ensuring an optimal pairing based on the comparative ranking of user profiles' competencies.

Derived from the research paper by Weng and Lin [@JMLR:v12:weng11a],
OpenSkill offers a pure Python implementation of their models. Similar to TrueSkill,
this framework is specifically designed for asymmetric multi-faction multiplayer games.
However, OpenSkill boasts several advantages over proprietary models like TrueSkill [@herbrich2006trueskill].
Notably, it delivers significantly faster rating updates, with performance gains of up to 150%.
Additionally, OpenSkill features a more permissive license, enabling users to freely
modify and distribute the library.

OpenSkill includes five distinct models, each with its own unique characteristics and tradeoffs.
Among these models are partial pairing and full pairing approaches.
Partial pairing models engage only a subset of players who are paired with each other
during rating updates. This strategy considerably improves computational efficiency while
sacrificing a certain level of accuracy. On the other hand, full pairing models leverage
all available information within the paired data to make precise rating updates at the cost
of increased computational requirements.

# Usage

To install the library simply `pip install openskill` and import the library. An conventional example of usage is given below:

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

Each player has a `mu` and a `sigma` value corresponding to their skill ($\mu$) and uncertainty ($\sigma$) in skill. Comparisons between two players can be done by calling the `ordinal()` method.
In this case it would be on the instances of `PlackettLuceRating`.

# Benchmarks

A reproducible set of benchmarks are available in the `benchmark/` folder at the root of the openskill.py repository.
Simply make sure the appropriate dataset files are available, run the `benchmark.py` file and select the appropriate
options.

Using a dataset of overwatch matches and player info, OpenSkill predicts the winners competitively with TrueSkill.

For games restricted to at least 2 matches per player:

|                   | OpenSkill - PlackettLuce |  TrueSkill |
|:-----------------:|:------------------------:|:----------:|
| Correct Matches   |           583            | 593        |
| Incorrect Matches |            52            | 42         |
| Accuracy          |        **91.81%**        | **93.39%** |
| Runtime Duration  |        **0.77s**         | 2.32s      |

When restricted to 1 match per player:

|                   | OpenSkill - PlackettLuce | TrueSkill  |
|:-----------------:|:------------------------:|:----------:|
| Correct Matches   |           791            |    794     |
| Incorrect Matches |           342            |    339     |
| Accuracy          |        **69.81%**        | **70.08%** |
| Runtime Duration  |        **9.09s**         |   30.76s   |

Using a dataset of chess matches, we also see a similar trend, where OpenSkill
predicts the same number of matches as TrueSkill, but in less time.

Finally, running the project against a large dataset of PUBG online matches
results in a Rank-Biased Overlap [@10.1145/1852102.1852106] of **64.11** and
an accuracy of **92.03%**.

# Acknowledgements

We extend our sincere gratitude to Philihp Busby and the openskill.js project [@Busby_2023] for their valuable contributions,
which have significantly enhanced the speed and efficiency of the prediction methods.
Special acknowledgment also goes to Jas Laferriere for their critical contribution of the additive dynamics factor.
Your collective efforts have been instrumental in improving our work.

# References
