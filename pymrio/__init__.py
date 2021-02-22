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
Dependencies:

- numpy
- scipy
- pandas
- matplotlib
- docutils (only for IOSystem.report* if format is html and tex - not
            imported otherwise)

:Authors: Konstantin Stadler

:license: BSD 3-Clause License

"""

import logging
import sys

from pymrio.core.fileio import *
from pymrio.core.mriosystem import Extension, IOSystem, concate_extension
from pymrio.tools.iodownloader import (
    download_eora26,
    download_exiobase1,
    download_exiobase2,
    download_exiobase3,
    download_oecd,
    download_wiod2013,
)
from pymrio.tools.iomath import (
    calc_A,
    calc_accounts,
    calc_e,
    calc_F,
    calc_F_Y,
    calc_L,
    calc_M,
    calc_S,
    calc_S_Y,
    calc_x,
    calc_x_from_L,
    calc_Z,
)
from pymrio.tools.iometadata import MRIOMetaData
from pymrio.tools.ioparser import *
from pymrio.tools.ioutil import build_agg_matrix, build_agg_vec
from pymrio.version import __version__
