"""
Various constant values

KST 20140903
"""

import os

# path information of the package
PYMRIO_PATH = {
    "root": os.path.dirname(__file__),
    "test_mrio": os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../mrio_models/test_mrio")
    ),
    "testmrio": os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../mrio_models/test_mrio")
    ),
    "test": os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../mrio_models/test_mrio")
    ),
    "exio20": os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../mrio_models/exio20")
    ),
    "exio2": os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../mrio_models/exio20")
    ),
}

# generic names (needed for the aggregation  if no names are given)
GENERIC_NAMES = {
    "sector": "sec",
    "region": "reg",
    "iosys": "IOSystem",
    "ext": "Extension",
}

DEFAULT_FILE_NAMES = {"filepara": "file_parameters.json", "metadata": "metadata.json"}

MISSING_AGG_ENTRY = {
    "region": "Unspecified region",
    "sector": "Unspecified sector",
}
