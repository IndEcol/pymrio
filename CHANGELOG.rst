#########
Changelog
#########

**********************
v0.3.3 (Jan 11, 2018)
**********************

Note: This includes all changes from 0.3 to 0.3.3

- downloaders for EORA26 and WIOD
- codebase fully pep8 compliant
- restructured and extended the documentation
  
- License changed to GNU GENERAL PUBLIC LICENSE v3
  
Dependencies
============

- pandas minimal version changed to 0.22
- Optional (for aggregation): country converter coco >= 0.6.3

API breaking changes  
=====================

- The format for saving MRIOs changed from csv + ini to csv + json. Use the method '_load_all_ini_based_io' to read a previously saved MRIO and than save it again to convert to the new save format.
- method set_sectors(), set_regions() and set_Y_categories() renamed to rename_sectors() etc.
- connected the aggregation function to the country_converter coco
- removed previously deprecated method 'per_source'. Use 'diag_stressor' instead.


**********************
v0.2.2 (May 27, 2016)
**********************

Dependencies
============

- pytest. For the unit tests.

Misc
====

- Fixed filename error for the test system.
- Various small bug fixes.
- Preliminary EXIOBASE 3 parser.
- Preliminary World Input-Output Database (WIOD) parser.

**********************
v0.2.1 (Nov 17, 2014)
**********************

Dependencies
============

- pandas version > 0.15. This required some change in the xls reading within
  the parser.
- pytest. For the unit tests.

Misc
====

- Unit testing for all mathematical functions and a first system wide check.
- Fixed some mistakes in the tutorials and readme

**********************
v0.2.0 (Sept 11, 2014)
**********************

API changes
===========

- IOSystem.reset() replaced by IOSystem.reset_all_to_flows()
- IOSystem.reset_to_flows() and IOSystem.reset_to_coefficients() added
- Version number attribute added
- Parser for EXIOBASE like extensions (pymrio.parse_exio_ext) added.
- plot_accounts now works also for for specific products (with parameter "sector")

Misc
====

- Several bugfixes
- Mainmodule split into several packages and submodules
- Added 3rd tutorial
- Added CHANGELOG

**********************
v0.1.0 (June 20, 2014)
**********************

Initial version
