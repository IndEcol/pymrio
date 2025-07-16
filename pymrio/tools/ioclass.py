"""Classification helpers for various standard MRIOs.

KST 20211123
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Union

import pandas as pd

from pymrio.core.constants import PYMRIO_PATH


def get_classification(mrio_name: Optional[str] = None):
    """Get predefined classifications included in pymrio.

    Parameters
    ----------
    mrio_name: str
        MRIO for which to get the classification.
        Pass None (default) for a list of available classifications.

    Returns
    -------
        pymrio.ClassificationData
    """
    if not mrio_name:
        return PYMRIO_PATH.keys()

    if mrio_name not in PYMRIO_PATH.keys():
        raise ValueError(
            f"No classification available for {mrio_name}. "
            "Run the function without parameter to get available classifications."
        )

    return ClassificationData(
        mrio_classification_folder=PYMRIO_PATH[mrio_name],
        sectors_file_name="sectors.tsv",
        sectors_sep="\t",
        finaldemand_file_name="finaldemand.tsv",
        finaldemand_sep="\t",
    )


@dataclass
class ClassificationData:
    """Classification data for MRIOs.

    Typically includes .sectors and .finaldemand

    """

    mrio_classification_folder: Union[str, Path]

    sectors_file_name: str
    sectors_sep: str

    finaldemand_file_name: str
    finaldemand_sep: str

    sectors: pd.DataFrame = field(init=False)
    finaldemand: pd.DataFrame = field(init=False)

    def __post_init__(self):
        """Set sectors and final demand."""
        self.sectors = pd.read_csv(
            Path(self.mrio_classification_folder) / self.sectors_file_name,
            sep=self.sectors_sep,
        )
        self.finaldemand = pd.read_csv(
            Path(self.mrio_classification_folder) / self.finaldemand_file_name,
            sep=self.finaldemand_sep,
        )

    def get_sector_dict(self, orig: Union[str, list, pd.Series], new: Union[str, pd.Series]):
        """Return sector rename dict based.

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
        -------
            dict
        """
        if not isinstance(orig, str):
            for cname, cvalue in self.sectors.items():
                if cvalue.isin(orig).all():
                    orig = cname
                    break
            else:
                raise ValueError("No fully matching sector classification found")

        new = new if isinstance(new, str) else new.name
        return self.sectors.loc[:, [orig, new]].set_index(orig).squeeze().to_dict()
