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
Conversion to hdf5 and mat should be implemented...

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

import sys
import logging

from pymrio.version import __version__

from pymrio.core.mriosystem import IOSystem
from pymrio.core.mriosystem import Extension
from pymrio.core.mriosystem import concate_extension

from pymrio.core.fileio import *

from pymrio.tools.ioparser import *

from pymrio.tools.iodownloader import download_eora26
from pymrio.tools.iodownloader import download_wiod2013
from pymrio.tools.iodownloader import download_oecd
from pymrio.tools.iodownloader import download_exiobase3
from pymrio.tools.iodownloader import download_exiobase2
from pymrio.tools.iodownloader import download_exiobase1

from pymrio.tools.iometadata import MRIOMetaData

from pymrio.tools.ioutil import build_agg_vec
from pymrio.tools.ioutil import build_agg_matrix

from pymrio.tools.iomath import calc_x
from pymrio.tools.iomath import calc_x_from_L
from pymrio.tools.iomath import calc_Z
from pymrio.tools.iomath import calc_A
from pymrio.tools.iomath import calc_L
from pymrio.tools.iomath import calc_S
from pymrio.tools.iomath import calc_S_Y
from pymrio.tools.iomath import calc_F
from pymrio.tools.iomath import calc_F_Y
from pymrio.tools.iomath import calc_M
from pymrio.tools.iomath import calc_e
from pymrio.tools.iomath import calc_accounts
