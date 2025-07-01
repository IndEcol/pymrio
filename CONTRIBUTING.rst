############
Contributing
############


First off, thanks for taking the time to contribute!

There are many ways you can help to improve pymrio.

- Update and improve the documentation and tutorials. 
- File bug reports and describe ideas for enhancement.
- Add new functionality to the code.

Pymrio follows an "issue/ticket driven development". 
This means, before you start working file an issue describing the planned changes or comment on an existing one to indicate that you work on it.
This allows us to discuss changes before you actually start and gives us the chance to identify synergies across ongoing work and avoid potential double work.
When you have finished, use a pull request to inform me about the improvements and make sure all tests pass (see below).
In the pull request you can use various phrases_ which automatically close the issue you have been working on.

.. _phrases: https://blog.github.com/2013-05-14-closing-issues-via-pull-requests/

****************************
Working on the documentation
****************************

Any contribution to the description of pymrio is of huge value, in particular I very much appreciate tutorials which show how you can use pymrio in actual research.

The pymrio documentation combines reStructuredText_ and Jupyter_ notebooks.
The Sphinx Documentation has an excellent introduction to reStructuredText_. Review the Sphinx docs to perform more complex changes to the documentation as well.

.. _reStructuredText: http://www.sphinx-doc.org/en/stable/rest.html
.. _Jupyter: http://jupyter.readthedocs.io/en/latest/content-quickstart.html

**********************
Changing the code base
**********************

We warmly welcome contributions to ``pymrio``! To get started, please file an
issue and submit a pull request with your changes against the ``master`` branch
of the repository.

This project uses ruff_ for code formatting and linting, and poethepoet_
(``poe``) as a task runner to simplify common development workflows. All
relevant commands are defined in the ``pyproject.toml`` file and can be run
with ``poe``.

To set up your development environment, install
``uv``, then sync the project dependencies, including test and lint requirements:

.. code-block:: bash

   uv sync --all-extras

We use the numpy style for docstrings_ and aim to maintain compatibility with
previous versions of ``pymrio``. You can run the test suite to ensure your
changes don't break existing functionality:

.. code-block:: bash

   # Run the fast (multi-core) test suite
   poe test

   # Or run the full test suite with code coverage
   poe fulltest

Before submitting a pull request, please ensure your code is formatted and
passes all linter checks. You can use the following commands:

.. code-block:: bash

   # Automatically format the code
   poe format

   # Check for linting errors and other issues
   poe check

   # Automatically fix any fixable linting errors
   poe check --fix


Passing all checks is a requirement for merging a pull request.

.. _docstrings: https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard
.. _ruff: https://docs.astral.sh/ruff/
.. _poethepoet: https://poethepoet.natn.io/index.html

**********
Versioning
**********

The versioning system follows http://semver.org/

****************************
Documentation and docstrings
****************************

Docstring should follow the numpy docstring convention. See

- http://sphinx-doc.org/latest/ext/example_numpy.html
- https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt#docstring-standard

***********
Open points
***********


Pymrio is under active development. Open points include:

- improve test cases
- wrapper for time series analysis
  
    * calculate timeseries
    * extract timeseries data

- reorder sectors/regions
- automatic sector aggregation (perhaps as a separate package similar to the country converter)
- country parameter file (GDP, GDP PPP, Population, area) for normalization of results (similar to the pop vector currently implemented for EXIOBASE 2)
- graphical output

    * flow maps of impacts embodied in trade flows
    * choropleth map for footprints

- structural decomposition analysis
