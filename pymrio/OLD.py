""" 
Function and classes for (symmetric) MRIO systems
================================================

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

:license: BSD 2-Clause License

"""
# pylint: disable-msg=C0103
# general imports
import os
import sys
import configparser
import time 
import logging
import collections
import re
import string
import tools.util as util
import core.classes as core
from tools.parser import parse_exiobase22
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

import imp # debug
#imp.reload(core)


# constants and global variables
from core.constants import PYMRIO_PATH

# generic names (needed for the aggregation  if no names are given)
from core.constants import GENERIC_NAMES


# class definitions



if __name__ == "__main__":
    logging.warn("This module can't be run directly")
    logging.info("%s", __doc__)
 
