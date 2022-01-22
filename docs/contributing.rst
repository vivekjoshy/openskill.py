.. _contributing:

============
Contributing
============

Style Guide
-----------
All pull requests to the python source must follow `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ conventions.

All methods and functions must be in snake_case and not camelCase. All code must also be formatted with ``black`` and it's default settings.


Pull Requests
-------------

We follow `Github Flow <https://guides.github.com/introduction/flow/>`_ as our workflow when creating pull requests. It is a neater and easier way to manage changes.
You are also responsible for writing tests(where applicable) if you are contributing to a core module. If we see an area of code that requires tests, then we will not
accept the PR until you write a test for that area of code. Tests ensure long term stability.

Also note that there are CI checks in place. If any automated tests fail, please rework and resubmit your PR.
