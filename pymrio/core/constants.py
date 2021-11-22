"""
Various constant values

KST 20140903
"""

import os
import pandas as pd
from dataclasses import dataclass, field

# path information of the package
PYMRIO_PATH = {
    "root": os.path.dirname(__file__),
    "test_mrio": os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../mrio_models/test_mrio")
    ),
    "test_mrio_data": os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../mrio_models/test_mrio/mrio_data")
    ),
    "testmrio": os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../mrio_models/test_mrio")
    ),
    "test": os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../mrio_models/test_mrio")
    ),
    # TODO remove: just here to keep the tests running
    "exio2": os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../mrio_models/exio2_pxp")
    ),
    "exio2_pxp": os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../mrio_models/exio2_pxp")
    ),
    "exio2_ixi": os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../mrio_models/exio2_ixi")
    ),
    "exio3_pxp": os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../mrio_models/exio3_pxp")
    ),
    "exio3_ixi": os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../mrio_models/exio3_ixi")
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

@dataclass
class ClassData(object):
    """ Returns classification for mrio_name """
    mrio_name: str
    sectors: pd.DataFrame = field(init=False)

    def __post_init__(self):
        if self.mrio_name not in PYMRIO_PATH.keys():
            raise ValueError(f"No classification available for {self.mrio_name}")
        self.sectors = pd.read_csv()

    def get_sector_dict(self, orig):
        """ Returns sector rename dict based

        Parameters 
        ----------
        orig: TODO
            Original classification, obtained by calling 'get_sectors()' on the given mrio

        Returns
        --------
            dict
        """
        return dict()



