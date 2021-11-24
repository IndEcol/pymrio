"""
Classification helpers for various standard MRIOs

KST 20211123
"""

import pandas as pd
from dataclasses import dataclass, field
from typing import Union
from pathlib import Path
from pymrio.core.constants import PYMRIO_PATH


def get_classification(mrio_name):
    """Get predefined classification included in pymrio"""

    if mrio_name not in PYMRIO_PATH.keys():
        raise ValueError(f"No classification available for {mrio_name}")

    return ClassificationData(
        mrio_classification_folder=PYMRIO_PATH[mrio_name],
        sectors_file_name="sectors.tsv",
        sectors_sep="\t",
        finaldemand_file_name="finaldemand.tsv",
        finaldemand_sep="\t",
    )


@dataclass
class ClassificationData(object):
    """Returns classification data present in mrio_classification_folder"""

    mrio_classification_folder: Union[str, Path]

    sectors_file_name: str
    sectors_sep: str

    finaldemand_file_name: str
    finaldemand_sep: str

    sectors: pd.DataFrame = field(init=False)
    finaldemand: pd.DataFrame = field(init=False)

    def __post_init__(self):
        self.sectors = pd.read_csv(
            Path(self.mrio_classification_folder) / self.sectors_file_name,
            sep=self.sectors_sep,
        )
        self.finaldemand = pd.read_csv(
            Path(self.mrio_classification_folder) / self.finaldemand_file_name,
            sep=self.finaldemand_sep,
        )

    def get_sector_dict(
        self, orig: Union[str, list, pd.Series], new: Union[str, pd.Series]
    ):
        """Returns sector rename dict based

        Parameters
        ----------
        orig: str or pd.Series
            Original classification, obtained by calling 'get_sectors()' on
            the given mrio or by using an instance of the class (which
            provides tab completion in an interactive environment) or by
            giving the column header name used in the classification file

        new: str or pd.Series
            New classification, name as given in the classification file. Will
            be extracted from the Series name if this is given (to allow for
            tab completion).

        Returns
        --------
            dict
        """
        if type(orig) is not str:
            for cname, cvalue in self.sectors.iteritems():
                if cvalue.isin(orig).all():
                    orig = cname
                    break
            else:
                raise ValueError("No fully matching sector classification found")

        new = new if type(new) is str else new.name
        return self.sectors.loc[:, [orig, new]].set_index(orig).squeeze().to_dict()
