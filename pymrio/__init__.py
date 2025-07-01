"""Pymrio - A python module for automating io calculations and generating reports.

==================================================================================

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

from pymrio.core.fileio import (
    ReadError,
    archive,
    load,
    load_all,
    load_test,
)
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
from pymrio.tools.ioparser import (
    ParserError,
    ParserWarning,
    generic_exiobase12_parser,
    get_exiobase12_version,
    get_exiobase_files,
    parse_eora26,
    parse_exio12_ext,
    parse_exiobase1,
    parse_exiobase2,
    parse_exiobase3,
    parse_gloria,
    parse_gloria_sut,
    parse_oecd,
    parse_wiod,
)
from pymrio.tools.ioutil import (
    build_agg_matrix,
    build_agg_vec,
    convert,
    extend_rows,
    get_repo_content,
    index_contains,
    index_fullmatch,
    index_match,
    to_long,
)
from pymrio.version import __version__

__all__ = [
    # core.mriosystem
    "Extension",
    "IOSystem",
    "extension_characterize",
    "extension_concate",
    "extension_convert",
    # tools.ioclass
    "ClassificationData",
    "get_classification",
    # tools.iodownloader
    "download_eora26",
    "download_exiobase1",
    "download_exiobase2",
    "download_exiobase3",
    "download_gloria",
    "download_oecd",
    "download_wiod2013",
    # fileio
    "load_all",
    "load",
    "archive",
    "load_test",
    "ReadError",
    # tools.iomath
    "calc_A",
    "calc_accounts",
    "calc_B",
    "calc_e",
    "calc_F",
    "calc_F_Y",
    "calc_G",
    "calc_gross_trade",
    "calc_L",
    "calc_M",
    "calc_M_down",
    "calc_S",
    "calc_S_Y",
    "calc_x",
    "calc_x_from_L",
    "calc_Z",
    # tools.iometadata
    "MRIOMetaData",
    # tools.ioparser
    "ParserError",
    "ParserWarning",
    "parse_exio12_ext",
    "get_exiobase12_version",
    "get_exiobase_files",
    "generic_exiobase12_parser",
    "parse_exiobase1",
    "parse_exiobase2",
    "parse_exiobase3",
    "parse_wiod",
    "parse_oecd",
    "parse_eora26",
    "parse_gloria_sut",
    "parse_gloria",
    # tools.ioutil
    "build_agg_matrix",
    "build_agg_vec",
    "convert",
    "extend_rows",
    "index_contains",
    "index_fullmatch",
    "index_match",
    "to_long",
    "get_repo_content",
    # version
    "__version__",
    # Add any explicit imports from fileio and ioparser here
    # "load_data",
    # "parse_io_data",
]
