"""
Various constant values

KST 20140903
"""

import os
from pathlib import Path

# path information of the package
__ROOT = Path(os.path.dirname(__file__))
PYMRIO_PATH = {
    "test_mrio": Path(__ROOT / "../mrio_models/test_mrio").absolute(),
    "test_mrio_data": Path(__ROOT / "../mrio_models/test_mrio/mrio_data").absolute(),
    "testmrio": Path(__ROOT / "../mrio_models/test_mrio").absolute(),
    "test": Path(__ROOT / "../mrio_models/test_mrio").absolute(),
    # TODO remove "exio2": just here to keep the tests running
    "exio2": Path(__ROOT / "../mrio_models/exio2_pxp").absolute(),
    "exio2_pxp": Path(__ROOT / "../mrio_models/exio2_pxp").absolute(),
    "exio2_ixi": Path(__ROOT / "../mrio_models/exio2_ixi").absolute(),
    "exio3_pxp": Path(__ROOT / "../mrio_models/exio3_pxp").absolute(),
    "exio3_ixi": Path(__ROOT / "../mrio_models/exio3_ixi").absolute(),
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
