#############
API Reference
#############

API references for all modules

.. currentmodule:: pymrio


*********************
Data input and output
*********************

Test system
===========

.. autosummary::
    :toctree: api_doc/

    load_test

Raw data
========

.. autosummary::
    :toctree: api_doc/

    parse_exiobase22 

Save data
=========

Currently, the full MRIO system can be saved in txt or the python specific
binary format ('pickle'). Both formats work with the same API interface:

.. autosummary::
   :toctree: api_doc/

   IOSystem.save
   IOSystem.save_all


Load processed data
===================

This functions load IOSystems or individual extensions which 
have been saved with pymrio before.

.. autosummary::
   :toctree: api_doc/

   load
   load_all


Accessing
=========

pymrio stores all tables as pandas DataFrames. This data can be accessed with
the usual pandas methods. On top of that, the following functions return (in
fact yield) several tables at once:

.. autosummary::
   :toctree: api_doc/

   IOSystem.get_DataFrame
   IOSystem.get_extensions

For the extensions, it is also possible to receive all data (F, S, M, D_fp, ...) 
for one specified row. 

.. autosummary::
   :toctree: api_doc/

   Extension.get_row_data

***********************
Exploring the IO System
***********************

The following functions provide informations about the structure of 
the IO System and the extensions. The methods work on the IOSystem as well as
directly on the Extensions.


.. autosummary::
   :toctree: api_doc/

   IOSystem.get_regions
   IOSystem.get_sectors
   IOSystem.get_Y_categories
   IOSystem.get_index
   Extension.get_rows



************
Calculations
************

Top level methods
===================

The top level level function calc_all checks the IO System and its extensions
for missing parts and calculate these. This function calls the specific
calculation method for the core system and for the extensions.

.. autosummary::
   :toctree: api_doc/

   IOSystem.calc_all
   IOSystem.calc_system
   Extension.calc_system

Low level matrix calculations
=============================

The top level functions work by calling the following low level functions.
These can also be used independently from the IO System for pandas DataFrames and
numpy array. 

.. autosummary::
   :toctree: api_doc/

   calc_x
   calc_Z
   calc_A
   calc_L
   calc_S
   calc_F
   calc_M
   calc_e
   calc_accounts


*******************************************
Modifiying the IO System and its Extensions
*******************************************

Aggregation
===========

The IO System method 'aggregate' accepts concordance matrices and/or
aggregation vectors. The latter can be generated automatically for various
aggregation levels for the test system and EXIOBASE 2.

.. autosummary::
   :toctree: api_doc/

   IOSystem.aggregate
   build_agg_vec

Analysing the source of impacts
===============================

.. autosummary::
   :toctree: api_doc/

   Extension.per_source

Changing extensions
===================

.. autosummary::
   :toctree: api_doc/

   IOSystem.remove_extension
   parse_exio_ext

Renaming
========

.. autosummary::
   :toctree: api_doc/

   IOSystem.set_regions
   IOSystem.set_sectors
   IOSystem.set_Y_categories

******
Report
******

The following method works on the IO System (generating reports for every
extension available) or at individual extensions.

.. autosummary::
   :toctree: api_doc/

   IOSystem.report_accounts

*************
Visualization
*************

.. autosummary::
   :toctree: api_doc/

   Extension.plot_account

*************
Miscellaneous
*************

.. autosummary::
   :toctree: api_doc/

   IOSystem.reset_to_flows
   IOSystem.reset_to_coefficients
   IOSystem.copy
