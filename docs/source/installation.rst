.. _installing:

======================
Installing the Library
======================

For Users
=========

For production use, please install from pip.

::

    pip install openskill

Then verify it is working by running this command:

::

    $ python -c "import openskill; print(openskill.__version__)"


It should print the current version number of the package.

For Contributors
================

Requirements
------------

* Python 3.9+
* `UV Package Manager <https://docs.astral.sh/uv/getting-started/installation/>`_

Installing from source
----------------------

openskill.py is easy to install from source if you already meet the requirements. First clone the latest development version from the main branch.

::

    git clone https://github.com/vivekjoshy/openskill.py
    cd openskill.py/

Then enter this command to download and install the locked dependencies.

::

    uv sync

This will create a virtual environment under `.venv` locally. Activate it using `source .venv/bin/activate`.

Then verify openskill is installed and working by running this command:

::

    python -c "import openskill; print(openskill.__version__)"
