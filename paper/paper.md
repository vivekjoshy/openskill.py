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
particular rank, know colloquially as "Elo Hell" [@Elo]. Another major issue
is that most ranking systems are designed for 1v1 games, and do not scale well
to multiplayer games. If they are designed for that purpose, the algorithms that
are available are inefficient. This library is designed to  address all of these
problems while being faster than and just as accurate as proprietary algorithms.

# Statement of need

Bayesian inference of skill ratings from game outcomes is a crucial aspect of online
video game development and research. The OpenSkill library provides a comprehensive
set of models and algorithms to facilitate this process. It is primarily meant to be used
by video game developers and researchers working on multi-agent scripting environments
such as Neural MMO [@suarez2019neural]. Derived from the research paper by Weng and Lin [@JMLR:v12:weng11a],
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

# Acknowledgements

Sincere thanks to Philihp Busby for the speedups to the prediction methods.

# References
