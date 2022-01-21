.. _installing_bot:

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

For Developers
==============

Installing from source
----------------------

openskill.py is very easy to install from source. First clone the latest development version from the master branch.

::

    git clone https://github.com/OpenDebates/openskill.py
    cd openskill.py/


Since openskill.py has a lot of dependencies, it is managed by `Poetry <https://python-poetry.org/>`_.
First install poetry from the instructions provided `here <https://python-poetry.org/docs/#installation>`_. Then create a shell:

::

    poetry shell

You should now see your terminal change to show your are you now using a virtual environment.
Let's install the package dependencies now. This may take a while depending on your machine.


::

    poetry install

Then verify it is working by running this command:

::

    python -c "import openskill; print(openskill.__version__)"

