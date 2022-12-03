All notable changes to this openskill.py will be documented in this file.

This file is updated every release since v1.0.0 with the use of towncrier from the fragments found under changes/

.. towncrier release notes start

Openskill 3.1.0 (2022-12-03)
============================

Documentation Improvements
--------------------------

- Add more details to the documentation, fixes broken links and point a custom domain name to the docs. (`#73 <https://github.com/OpenDebates/openskill.py/issues/73>`_)


Openskill 3.0.0 (2022-11-30)
============================

Breaking Changes
----------------

- Modify default ``tau`` value to ``25/300`` #61 (`#61 <https://github.com/OpenDebates/openskill.py/issues/61>`_)


Openskill 2.5.1 (2022-11-11)
============================

Bugfixes
--------

- Allow setting ``mu`` and ``sigma`` to 0 for ``Rating`` objects. (`#60 <https://github.com/OpenDebates/openskill.py/issues/60>`_)


Openskill 2.5.0 (2022-10-26)
============================

Features
--------

- Support Python 3.11.0 Officially (`#56 <https://github.com/OpenDebates/openskill.py/issues/56>`_)


Bugfixes
--------

- Fixes issue where equal ranks below zero don't draw (`#54 <https://github.com/OpenDebates/openskill.py/issues/54>`_)


Openskill 2.4.0 (2022-06-08)
============================

Features
--------

- Add more comparison magic methods to the ``Rating`` object.


Documentation Improvements
--------------------------

- Add documentation about advanced usage.
- Add documentation about future update to the default value of ``tau``.


Openskill 2.3.0 (2022-05-14)
============================

Features
--------

- Add support for python 3.7+ (`#52 <https://github.com/OpenDebates/openskill.py/issues/52>`_)


Openskill 2.2.0 (2022-03-18)
============================

Features
--------

- ``tau`` (defaults to 0): Additive dynamics factor, which keeps a player's rating from getting stuck at a level. Normally, a player's sigma will only decrease as we gain more information about their performance. This option will put some pressure on this back up. This default will change to be sigma/100 with v3, to be more congruent with TrueSkill, but higher may make your rating system more exciting. (`#50 <https://github.com/OpenDebates/openskill.py/issues/50>`_)

- ``prevent_sigma_increase`` (defaults to ``False``): for a tau > 0, it is possible that a player could play someone with a low enough rating that even if they win, their ordinal rating will still go down slightly. If your players have no agency in matchmaking, it is not desirable to have a situation where a player goes down on the leaderboard even though they win. (`#50 <https://github.com/OpenDebates/openskill.py/issues/50>`_)


Openskill 2.1.0 (2022-03-10)
============================

Features
--------

- Faster runtime of ``predict_win`` and ``predict_draw``. (`#48 <https://github.com/OpenDebates/openskill.py/issues/48>`_)


Openskill 2.0.0 (2022-02-20)
============================

Breaking Changes
----------------

- The ``rate`` function now returns ``Rating`` objects. (`#46 <https://github.com/OpenDebates/openskill.py/issues/46>`_)
- Changes ``ordinal`` to accept both ``Rating`` objects and lists or tuples of 2 floats. (`#46 <https://github.com/OpenDebates/openskill.py/issues/46>`_)


Features
--------

- Add a function to predict draws. (`#45 <https://github.com/OpenDebates/openskill.py/issues/45>`_)
- ``create_rating`` now checks if the argument is the correct type. (`#46 <https://github.com/OpenDebates/openskill.py/issues/46>`_)


Openskill 1.0.2 (2022-02-09)
============================

Features
--------

- Updates scipy to 1.8.0 (`#37 <https://github.com/OpenDebates/openskill.py/issues/37>`_)


Openskill 1.0.1 (2022-02-04)
============================

Features
--------

- Update development status to "Stable" (`#34 <https://github.com/OpenDebates/openskill.py/issues/34>`_)


Openskill 1.0.0 (2022-02-04)
============================

Features
--------

- Capability to predict winners of match given a set of teams. (`#27 <https://github.com/OpenDebates/openskill.py/issues/27>`_)
