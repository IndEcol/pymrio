#########
Changelog
#########

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
