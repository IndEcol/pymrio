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

All code contribution must be provided as pull requests connected to a filed issue. 
Please set-up pull requests against the master branch of the repository. 
Use numpy style docstrings_ and lint using black_ and isort_, and follow the pep8_ style guide.
Passing the black_ and isort_ liter is a requirement to pass the tests before merging a pull request.

The following commands can be used to automatically apply the black_ and isort_ formatting.

.. code-block:: bash

   pip install black isort
   isort --project pymrio --profile black .
   black .

Check the "script" part in .travis.yml to check the required tests.
If you are using Conda you can build a development environment from environment_dev.yml which includes all packages necessary for development, testing and running.

Since pymrio is already used in research projects, please aim for keeping compatibility with previous versions.

.. _docstrings: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt
.. _pep8: https://www.python.org/dev/peps/pep-0008/
.. _black: https://github.com/psf/black/
.. _isort: https://github.com/pycqa/isort/


Running and extending the tests
===============================


Before filing a pull request, make sure your changes pass all tests.
Pymrio uses the py.test_ package for testing.
To run the tests either activate the environment_dev.yml file (if you are using 
Anaconda) or install the test requirments defined in requirments_test.txt.

Then run

::

  coverage erase
  isort --profile black --check-only .
  coverage run -m pytest --black -vv .
  coverage report 

in the root of your local copy of pymrio. The file format_and_test.sh can be 
used in Linux environments to format the code according to the black_ / isort_ format 
and run all tests.

In addition to the unit tests, the Jupyter notebook tutorials are also used 
for integration tests of the full software. Some of them (the EXIOBASE and Eora
example) require a pre-download of the respective MRIOs to a specific folder. 
Also, most of the tutorials have POSIX path specifications. However, in case 
you update some integral part of Pymrio, please either also check if the 
notebooks run or specify that you did not test them in the pull request.

For testing the notebooks install the nbval_ extension for py.test_ . 
Pymrio includes a sanitizing file to handle changing timestamps and object ids 
of the notebooks. To test all notebooks run the following command in the pymrio root directory:

::
	
	pytest --nbval --sanitize-with .notebook_test_sanitize.cfg  



.. _py.test: http://pytest.org/
.. _pytest-pep8: https://pypi.python.org/pypi/pytest-pep8
.. _Pandas: https://pandas.pydata.org/
.. _nbval: https://nbval.readthedocs.io/en/latest/


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


Pymrio is under active development. Open points include:

- parser for other available MRIOs

    * OPEN:EU (http://www.oneplaneteconomynetwork.org/)

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
