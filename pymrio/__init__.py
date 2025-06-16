"""
Pymrio - A python module for automating io calculations and generating reports
==============================================================================

The classes and tools in this module should work with any symetric IO system.

The main class of the module (IOSystem) has attributes .A, .L, ...
corresponding to a standard IO classification.
Data can be assigned directly to the attributes or by calling the
parsing or load functions.

Data storage
------------
Txt files together with a ini file are used for storing data. In addition,
the IOSystem with all data can also be pickled (binary).


Misc
----

Standard abbreviation for that module: mr

"""

from pymrio.core.fileio import *
from pymrio.core.mriosystem import (
    Extension,
    IOSystem,
    extension_characterize,
    extension_concate,
    extension_convert,
)
from pymrio.tools.ioclass import ClassificationData, get_classification
from pymrio.tools.iodownloader import (
    download_eora26,
    download_exiobase1,
    download_exiobase2,
    download_exiobase3,
    download_gloria,
    download_oecd,
    download_wiod2013,
)
from pymrio.tools.iomath import (
    calc_A,
    calc_accounts,
    calc_B,
    calc_e,
    calc_F,
    calc_F_Y,
    calc_G,
    calc_gross_trade,
    calc_L,
    calc_M,
    calc_M_down,
    calc_S,
    calc_S_Y,
    calc_x,
    calc_x_from_L,
    calc_Z,
)
from pymrio.tools.iometadata import MRIOMetaData
from pymrio.tools.ioparser import *
from pymrio.tools.ioutil import (
    build_agg_matrix,
    build_agg_vec,
    convert,
    extend_rows,
    index_contains,
    index_fullmatch,
    index_match,
    to_long,
)
from pymrio.version import __version__
