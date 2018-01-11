############
pymrio
############

Pymrio is an open source tool for analysing global environmental extended multi-regional input-output tables (EE MRIOs). 

.. image:: https://travis-ci.org/konstantinstadler/pymrio.svg?branch=master
    :target: https://travis-ci.org/konstantinstadler/pymrio

Pymrio aims to provide a high-level abstraction layer to available global EE MRIO databases in order to simplify common EE MRIO data tasks. Pymrio includes automatic download functions and parsers for available EE MRIO databases like EXIOBASE_, WIOD_ and EORA26_. It automatically checks parsed EE MRIOs for missing data necessary for calculating standard EE MRIO accounts (such as footprint, territorial, impacts embodied in trade) and calculates all missing tables. Various data visualization methods help to explore the dataset by comparing the different accounts across countries. 

Further functions include:

- analysis methods to identify where certain impacts occurr
- modifying region/sector classification
- restructuring extensions
- export to various formats
- visualization routines and 
- automated report generation
  
.. _EXIOBASE: http://www.exiobase.eu/
.. _WIOD: http://www.wiod.org/home
.. _EORA26: http://www.worldmrio.com/simplified/

Where to get it
===============

The full source code is available on Github at: https://github.com/konstantinstadler/pymrio

pymrio is registered at PyPI. Install it by:

.. code:: bash

    pip install pymrio --upgrade

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
    test_mrio.emissions.D_fp
    test_mrio.emissions.D_exp

To visualize the accounts:


.. code:: python

    import matplotlib as plt
    test_mrio.emissions.plot_account('emission_type1')
    plt.show()

Everything can be saved with

.. code:: python
    
    test_mrio.save_all('some/folder')

See the documentation and tutorials for further examples.


Tutorials
=========

TODO: Point to documentation


Contributing
=============

Want to contribute? Great!
Please check `CONTRIBUTING.rst`_ if you want to help to improve coco.
  
.. _CONTRIBUTING.rst: https://github.com/konstantinstadler/pymrio/blob/master/CONTRIBUTING.rst
   
Communication, issues, bugs and enhancements
============================================

Please use the issue tracker for documenting bugs, proposing enhancements and all other communication related to coco.

You can follow me on twitter_ to get the latest news about all my open-source and research projects (and occasionally some random retweets).

.. _twitter: https://twitter.com/kst_stadler


