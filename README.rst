############
Pymrio
############

Pymrio: Multi-Regional Input-Output Analysis in Python.

.. image:: https://img.shields.io/pypi/v/pymrio.svg
    :target: https://pypi.python.org/pypi/pymrio/
.. image:: https://anaconda.org/conda-forge/pymrio/badges/version.svg   
    :target: https://anaconda.org/conda-forge/pymrio
.. image:: https://github.com/IndEcol/pymrio/workflows/build/badge.svg
    :target: https://github.com/IndEcol/pymrio/actions
.. image:: https://coveralls.io/repos/github/IndEcol/pymrio/badge.svg?branch=master
    :target: https://coveralls.io/github/IndEcol/pymrio
.. image:: https://readthedocs.org/projects/pymrio/badge/?version=latest
    :target: http://pymrio.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://img.shields.io/badge/License-GPL%20v3-blue.svg
    :target: https://www.gnu.org/licenses/gpl-3.0
.. image:: https://zenodo.org/badge/21688312.svg
    :target: https://zenodo.org/badge/latestdoi/21688312
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

What is it
==========

Pymrio is an open source tool for analysing global environmentally extended multi-regional input-output tables (EE MRIOs). 
Pymrio aims to provide a high-level abstraction layer for global EE MRIO databases in order to simplify common EE MRIO data tasks. 
Pymrio includes automatic download functions and parsers for available EE MRIO databases like EXIOBASE_, WIOD_ and EORA26_. 
It automatically checks parsed EE MRIOs for missing data necessary for calculating standard EE MRIO accounts (such as footprint, territorial, impacts embodied in trade) and calculates all missing tables. 
Various data report and visualization methods help to explore the dataset by comparing the different accounts across countries. 

Further functions include:

- analysis methods to identify where certain impacts occur
- modifying region/sector classification
- restructuring extensions
- export to various formats
- visualization routines and 
- automated report generation
  

Where to get it
===============

The full source code is available on Github at: https://github.com/IndEcol/pymrio

Pymrio is registered at PyPI and on the Anaconda Cloud. Install it by:

.. code:: bash

    pip install pymrio --upgrade
    
or when using conda install it by

.. code:: bash

    conda install -c conda-forge pymrio

or update to the latest version by

.. code:: bash

    conda update -c conda-forge pymrio

The source-code of Pymrio available at the GitHub repo: https://github.com/IndEcol/pymrio  

The master branch in that repo is supposed to be ready for use and might be 
ahead of the official releases. To install directly from the master branch use:

.. code:: bash

    pip install git+https://github.com/IndEcol/pymrio@master



Quickstart    
==========

A small test mrio is included in the package. 

To use it call

.. code:: python

    import pymrio
    test_mrio = pymrio.load_test()

The test mrio consists of six regions and eight sectors:  

.. code:: python


    print(test_mrio.get_sectors())
    print(test_mrio.get_regions())

The test mrio includes tables flow tables and some satellite accounts. 
To show these:

.. code:: python

    test_mrio.Z
    test_mrio.emissions.F
    
However, some tables necessary for calculating footprints (like test_mrio.A or test_mrio.emissions.S) are missing. pymrio automatically identifies which tables are missing and calculates them: 

.. code:: python

    test_mrio.calc_all()

Now, all accounts are calculated, including footprints and emissions embodied in trade:

.. code:: python

    test_mrio.A
    test_mrio.emissions.D_cba
    test_mrio.emissions.D_exp

To visualize the accounts:


.. code:: python

    import matplotlib as plt
    test_mrio.emissions.plot_account('emission_type1')
    plt.show()

Everything can be saved with

.. code:: python
    
    test_mrio.save_all('some/folder')

See the documentation_ , tutorials_ and  `Stadler 2021`_ for further examples.

Tutorials
=========

The documentation_ includes information about how to use pymrio for automatic downloading_ and parsing_ of the EE MRIOs EXIOBASE_, WIOD_, OECD_ and EORA26_ as well as tutorials_ for the handling, aggregating and analysis of these databases. 

Citation
========

If you use Pymrio in your research, citing the article describing the package 
(`Stadler 2021`_) is very much appreciated. 

.. _`Stadler 2021`: https://openresearchsoftware.metajnl.com/articles/10.5334/jors.251/

For the full bibtex key see CITATION_ file.

.. _CITATION: CITATION

Contributing
=============

Want to contribute? Great!
Please check `CONTRIBUTING.rst`_ if you want to help to improve Pymrio.
  
.. _CONTRIBUTING.rst: https://github.com/IndEcol/pymrio/blob/master/CONTRIBUTING.rst
   
Communication, issues, bugs and enhancements
============================================

Please use the issue tracker for documenting bugs, proposing enhancements and all other communication related to pymrio.

You can follow me on twitter_ to get the latest news about all my open-source and research projects (and occasionally some random retweets).

Research notice
~~~~~~~~~~~~~~~

Please note that this repository is participating in a study into
sustainability of open source projects. Data will be gathered about this
repository for approximately the next 12 months, starting from June
2021.

Data collected will include number of contributors, number of PRs, time
taken to close/merge these PRs, and issues closed.

For more information, please visit `the informational
page <https://sustainable-open-science-and-software.github.io/>`__ or
download the `participant information
sheet <https://sustainable-open-science-and-software.github.io/assets/PIS_sustainable_software.pdf>`__.


.. _twitter: https://twitter.com/kst_stadler

.. _downloading: http://pymrio.readthedocs.io/en/latest/notebooks/autodownload.html
.. _parsing: http://pymrio.readthedocs.io/en/latest/handling.html
.. _documentation: http://pymrio.readthedocs.io/en/latest/
.. _tutorials: http://pymrio.readthedocs.io/en/latest/handling.html

.. _EXIOBASE: http://www.exiobase.eu/
.. _WIOD: http://www.wiod.org/home
.. _OECD: https://www.oecd.org/sti/ind/inter-country-input-output-tables.htm
.. _EORA26: http://www.worldmrio.com/simplified/

