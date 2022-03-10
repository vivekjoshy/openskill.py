All notable changes to this openskill.py will be documented in this file.

This file is updated every release since v1.0.0 with the use of towncrier from the fragments found under changes/

.. towncrier release notes start

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
