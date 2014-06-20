############
Introduction
############

pymrio is an open source tool for analysing global environmental extended multi-regional input-output tables (EEMRIOs). 

Source Repository: https://github.com/konstantinstadler/pymrio

pymrio aims to provide a consistent framework for handling EEMRIOs. It include methods for 

- parsing global MRIOs
- modifying region/sector classification
- restructuring extensions
- calculating various accounts (footprint, territorial, impacts embodied in trade)
- exporting to various formats
- visualization and 
- automated report generation

Current development concentrates on methods for investigating the source of impacts, in depth analysis of the MRIO system and parsing further MRIO systems. 


For using pymrio I recommend the following import convention:

>>> import pymrio as pmr


.. note::

    The main data manipulation and storage in pymrio depend on pandas DataFrames. It is recommend that you are familiar with the pandas DataFrame structure and API before using pymrio.

