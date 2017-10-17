*************
Contributing
*************

First off, thanks for taking the time to contribute!

There are many ways you can help to improve pymrio.

-) Update and improve the documentation and tutorials. 

-) File bug reports and describe ideas for enhancement

-) Add new functionality to the code

Independent of your contribution, please use pull requests to inform me about any improvements you did and make sure all tests pass (see below).


Working on the documentation
-----------------------------

The documentation of pymrio is currently not complete, any contribution to the description of pymrio is of huge value! 
We also very much appreciate tutorials which show how you can use pymrio in actual research.

The pymrio documentation consists of two main parts:

1) The documentation text:
   This is written in reStructuredText_, a very simple markup language, and built using Sphinx. The Sphinx Documentation has an excellent introduction to reStructuredText_. Review the Sphinx docs to perform more complex changes to the documentation as well.

2) Tutorials:
   These are written as Jupyter_ notebooks. To contribute, add a new notebook, describing how you use pymrio for a specific research question.  

.. _reStructuredText: http://www.sphinx-doc.org/en/stable/rest.html
.. _Jupyter: http://jupyter.readthedocs.io/en/latest/content-quickstart.html

Changing the code base
----------------------

If you plan any changes to the source code of this repo, please first discuss the change you wish to make via a filing an issue (labelled Enhancement or Bug) before making a change.
All code contribution must be provided as pull requests connected to a filed issue.
Use numpy style docstrings_ and follow pep8_ style guide.
The latter is a requirement to pass the tests before merging a pull request.
Since pymrio is already used in research projects, please aim for keeping compatibility with previous versions.

.. _docstrings: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt
.. _pep8: https://www.python.org/dev/peps/pep-0008/

Running and extending the tests
-------------------------------

Before filing a pull request, make sure your changes pass all tests.
Pymrio uses the py.test_ package with the pytest-pep8_ extension for testing.
To run the tests install these two packages (and the Pandas_ dependency) and run

::

    py.test -v -pep8

in the root of your local copy of coco.

The included tests verify the regular expressions against names commonly found in various databases.

These tests check

#) Do the short names uniquely match the regular expression?
#) Do the official name uniquely match the regular expression?
#) Do the alternative names tested so far still uniquely match the standard names?

To specify a new test set just add a tab-separated file with headers "name_short" and "name_test" and provide name (corresponding to the short name in the main classification file) and the alternative name which should be tested (one pair per row in the file).
If the file name starts with "test\_regex\_" it will be automatically recognised by the test functions.

.. _py.test: http://pytest.org/
.. _pytest-pep8: https://pypi.python.org/pypi/pytest-pep8
.. _Pandas: https://pandas.pydata.org/



**********
Versioning
**********

The versioning system follows http://semver.org/

****************************
Documentation and docstrings
****************************

Docstring should follow the numby docstring convention. See

- http://sphinx-doc.org/latest/ext/example_numpy.html
- https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt#docstring-standard

.. note::

    If you plan to build the doc yourself, install numpydoc 0.5dev from github (https://github.com/numpy/numpydoc). The version on pypi does not support python 3.

*******
Testing
*******

Pymrio uses the py.test package for all tests. Currently all mathematical
functions are covered by tests. 

In the folder pymrio/tests also a full pymrio system test based on the small
MRIO included in pymrio is available (full_run.py). This test runs longer than
the unit test and is therefore not included in the normal test run. To use it
run 

py.test full_run.py 

in the test folder.


***********
Open points
***********

pymrio is under acitive deveopment. Open points include:

- parser for other available MRIOs

    * EXIOBASE 1 (http://www.exiobase.eu)
    * OPEN:EU (http://www.oneplaneteconomynetwork.org/)
    * ...

- improve test cases
- graphical output

    * flow maps of impacts embodied in trade flows
    * choropleth map for footprints

- structural decomposition analysis
- improving the documentation (of course...)
