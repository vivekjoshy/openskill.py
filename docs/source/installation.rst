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

* Python 3.8+
* `PDM Package Manager <https://pdm.fming.dev/latest/#recommended-installation-method>`_

Installing from source
----------------------

openskill.py is easy to install from source if you already meet the requirements. First clone the latest development version from the master branch.

::

    git clone https://github.com/OpenDebates/openskill.py
    cd openskill.py/

::

    pdm install -d

Then verify it is working by running this command:

::

    python -c "import openskill; print(openskill.__version__)"
