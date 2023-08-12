# Benchmark Instructions

Simply run ``benchmark.py`` with a compatible Python version and choose the options.

## Available Benchmarks

- ``Win``: Compares win performance against TrueSkill.
- ``Draw``: Predicts draws on standard chess matches.
- ``Rank``: Predicts the rank of players.
- ``Large``: Uses rank prediction on a large multi-faction dataset.

The ``Large`` benchmark requires the ``pubg.csv`` file (around 1 GB) be extracted from ``pubg.7z`` and place in the ``data`` folder.
