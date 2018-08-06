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

Use numpy style docstrings_ and follow pep8_ style guide.
The latter is a requirement to pass the tests before merging a pull request.
Since pymrio is already used in research projects, please aim for keeping compatibility with previous versions.

.. _docstrings: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt
.. _pep8: https://www.python.org/dev/peps/pep-0008/

Running and extending the tests
===============================


Before filing a pull request, make sure your changes pass all tests.
Pymrio uses the py.test_ package with the pytest-pep8_ extension for testing.
To run the tests install these two packages (and the Pandas_ dependency) and run

::

    py.test -v -pep8

in the root of your local copy of pymrio.

.. _py.test: http://pytest.org/
.. _pytest-pep8: https://pypi.python.org/pypi/pytest-pep8
.. _Pandas: https://pandas.pydata.org/


Debugging and logging
=====================

Pymrio includes a logging class which is used for documenting changes in the IO system through Pymrio.
This is defined in tools/iometadata.py. 

To use is import it by

:: 

    from pymrio.tools.iometadata import MRIOMetaData
    
and than document changes by using the methods provided by the class.


All logs necessary only for development or later debugging should be logged by

::

    import logging    
    logging.debug("Message")


In the python terminal you can show these debug messages by:

::

    import logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
   
    

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

***********
Open points
***********


pymrio is under acitive deveopment. Open points include:

- parser for other available MRIOs

    * OPEN:EU (http://www.oneplaneteconomynetwork.org/)
    * OECD MRIO

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
