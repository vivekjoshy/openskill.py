.. _contributing:

============
Contributing
============

Style Guide
-----------
All pull requests to the python source must follow `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ conventions.

All methods and functions must be in snake_case and not camelCase. All code must also be formatted with ``black`` and it's default settings.


Towncrier
---------

To aid with the generation of ``CHANGELOG.rst`` as well as the releases changelog we use towncrier.

You will need to install towncrier and openskill.py from source before making changelog additions.

.. code::

    poetry install

For every pull request made to this project, there should be a short explanation of the change under changes/ with the following format: ``{pull_request_number}.{type}.rst``,

Possible types are:

- breaking: Signifying a backwards incompatible change.
- feature: Signifying a new feature.
- bugfix: Signifying a bugfix.
- doc: Signifying a documentation improvement.
- deprecation: Signifying a deprecation or removal of public API.

For changes that do not fall under any of the above cases, please specify the lack of the changelog in the pull request description so that a maintainer can skip the job that checks for newly added fragments.

Best way to create the fragments is to run towncrier create ``{pull_request_number}.{type}.rst`` after creating the pull request, edit the created file and committing the changes.

Multiple fragment types can be created per pull request if it covers multiple areas.

Pull Requests
-------------

We follow `Github Flow <https://guides.github.com/introduction/flow/>`_ as our workflow when creating pull requests. It is a neater and easier way to manage changes.
You are also responsible for writing tests(where applicable) if you are contributing to a core module. If we see an area of code that requires tests, then we will not
accept the PR until you write a test for that area of code. Tests ensure long term stability.

Also note that there are CI checks in place. If any automated tests fail, please rework and resubmit your PR.
