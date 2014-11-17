############
Development
############

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

    * WIOD (http://www.wiod.org/)
    * EXIOBASE 1 (http://www.exiobase.eu)
    * OPEN:EU (http://www.oneplaneteconomynetwork.org/)

- test cases
- graphical output

    * flow maps of impacts embodied in trade flows
    * choropleth map for footprints

- structural decomposition analysis
- improving the documentation (of course...)


******
Vision
******

pymrio aims to provide on one hand a consistent API interface to (multi regional) input output models. Using that as starting point, the next step would be to build a GUI around this API to further simplify the access to MRIO data.


