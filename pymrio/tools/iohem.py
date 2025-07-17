"""Object for applying the Hypothetical Extraction Method (HEM)."""

# %%
import json
from pathlib import Path

import numpy as np
import pandas as pd

import pymrio.tools.iomath as iomath


# %%
class HEM:
    """Class for Hypothetical Extraction Method (HEM) results."""

    def __init__(self, IOSystem=None, Y=None, A=None, x=None, L=None, IOSystem_meta=None, save_path=None) -> None:
        """
        Initialize the HEM class with the IOSystem or core IO data.

        Parameters
        ----------
        IOSystem : pymrio.IOSystem, optional
            An instance of the pymrio.IOSystem class containing the core IO data.
        Y : pd.DataFrame, optional
            Final demand matrix. If not provided, the one from the IOSystem will be used.
        A : pd.DataFrame, optional
            Input-output coefficients matrix. If not provided, the one from the IOSystem will be used.
        x : pd.DataFrame, optional
            Total output vector as a single column matrix, named indout.
            If not provided, the one from the IOSystem will be used.
        L : pd.DataFrame, optional
            Leontief inverse matrix. If not provided, it will be calculated from A.
        IOSystem_meta : dict, optional
            Metadata dictionary containing information about the IOSystem or extraction.
        save_path : str or Path, optional
            Path to save the extraction results. If not provided, it will be set to None.
        """
        if IOSystem is None:
            self.Y = Y
            self.A = A
            self.x = x
            self.L = L
            self.meta = {
                "IO System meta": IOSystem_meta,
            }
        else:
            self.Y = IOSystem.Y
            self.A = IOSystem.A
            self.x = IOSystem.x
            self.L = IOSystem.L
            self.meta = {
                "IO System meta": repr(IOSystem.meta),
            }

        self.save_path = Path(save_path or "./")
        self.L22 = None
        self.H = None

    def make_extraction(
        self,
        regions: list = None,
        sectors: list = None,
        extraction_type="1.2",
        multipliers=True,
        Y=None,
        A=None,
        x=None,
        downstream_allocation_matrix="A12",
    ):
        """
        Create a hypothetical extraction of the IOSystem based on the specified regions and sectors.

        Parameters
        ----------
        regions : list
            List of regions to be extracted.
        sectors : list
            List of sectors to be extracted.
        extraction_type : str, optional
            Type of extraction to be performed. Defaults to "1.2".
            See "https://doi.org/10.1111/jiec.13522" for more information.
        multipliers : bool, optional
            Whether to calculate multipliers for the extracted sectors. Defaults to True.
        Y : pd.DataFrame, optional
            Final demand matrix. If not provided, the one from the IOSystem will be used.
        A : pd.DataFrame, optional
            Input-output coefficients matrix. If not provided, the one from the IOSystem will be used.
        x : pd.DataFrame, optional
            Total output vector as a single column matrix, named indout.
            If not provided, the one from the IOSystem will be used.
        downstream_allocation_matrix : str, optional
            The matrix used to allocate downstream production. Defaults to "A12". Can be either "A12" or "L12".

        Returns
        -------
            None

        Notes
        -----
        This method sets the attributes of the HEM class based on the specified parameters.
        It calculates the hypothetical extraction of the IOSystem based on the specified regions and sectors.
        The extraction type must be one of the following: "1.2", "2a.2", "3a.2".
        The method also calculates the downstream allocation matrix based on the specified type.
        The method raises a ValueError if either regions or sectors are not specified,
            or if the extraction type is not implemented.
        The method raises a NotImplementedError if the extraction type is not one of the implemented ones.
        The method raises a TypeError if the intensities are not a pandas Series or DataFrame.
        The method raises a ValueError if the save path is not provided.

        Notes
        -----
        The definition of downstream and upstream production changes, if other extraction types are implemented.
        Current three implemented extraction types are identical.
        See https://doi.org/10.1111/jiec.13522 for more information.


        """
        self.meta.update(
            {
                "extraction_type": extraction_type,
                "downstream_allocation_matrix": downstream_allocation_matrix,
                "multipliers": multipliers,
            }
        )
        self.extraction_regions = regions
        self.extraction_sectors = sectors

        # In case the user does not pass Y and A, use the ones from the IOSystem
        if Y is None:
            Y = self.Y
        if A is None:
            A = self.A
        if x is None:
            x = self.x

        if (regions is not None) & (sectors is not None):
            index_extraction = pd.MultiIndex.from_product(iterables=[regions, sectors])

        elif (regions is None) & (sectors is not None):
            index_extraction = pd.MultiIndex.from_product(
                iterables=[self.A.index.get_level_values(0).unique(), sectors]
            )
        elif (regions is not None) & (sectors is None):
            index_extraction = pd.MultiIndex.from_product(
                iterables=[regions, self.A.index.get_level_values(1).unique()]
            )
        else:
            raise ValueError("Either regions or sectors must be specified, or both.")

        index_other = self.A.index.drop(index_extraction)
        self.index_extraction = index_extraction
        self.index_other = index_other

        if extraction_type not in ["1.2", "2a.2", "3a.2"]:
            raise NotImplementedError(
                "Only extraction types '1.2', '2a.2', '3a.2' are implemented at the moment.\n"
                "Please implement the extraction type you need or use one of the implemented ones.\n"
                "For more information see Table 4 in https://doi.org/10.1111/jiec.13522."
            )

        # TODO: Turn different extraction types into functions that this method can call.
        # ? How should we deal with the interpretation of the account in those cases?
        # Extracting blocks
        Y1 = Y.loc[Y.index.isin(index_extraction), :]
        Y2 = Y.loc[Y.index.isin(index_other), :]
        A11 = A.loc[A.index.isin(index_extraction), A.columns.isin(index_extraction)]
        A12 = A.loc[A.index.isin(index_extraction), A.columns.isin(index_other)]
        A22 = A.loc[A.index.isin(index_other), A.columns.isin(index_other)]
        A21 = A.loc[A.index.isin(index_other), A.columns.isin(index_extraction)]

        # Calculating HEM matrices
        I11 = pd.DataFrame(
            data=np.eye(len(A11)),
            index=A11.index,
            columns=A11.columns,
        )

        if (self.L22 is not None) and (self.L22.index.equals(A22.index)) and (self.L22.columns.equals(A22.columns)):
            # If L22 is already provided, use it directly
            self.L22 = self.L22
        else:
            self.L22 = iomath.calc_L(A22)

        if (self.H is not None) and (self.H.index.equals(A11.index)) and (self.H.columns.equals(A11.columns)):
            # If H is already provided, use it directly
            self.H = self.H
        else:
            self.H = pd.DataFrame(
                data=np.linalg.inv(I11 - A11 - A12.dot(self.L22.dot(A21))), index=A11.index, columns=A11.columns
            )

        # Calculating different accounts
        self.production_downstream_all = pd.DataFrame(
            data=np.diag(v=self.L22.dot(Y2.sum(axis=1))), index=self.L22.index, columns=self.L22.index
        )

        # Allocating downstream production
        if downstream_allocation_matrix == "A12":
            self.downstream_allocation_matrix = A12

        elif downstream_allocation_matrix == "L12":
            if self.L is None:
                self.L = iomath.calc_L(A)

            L12 = self.L.loc[index_extraction, index_other]
            L12_normalised = L12.div(L12.sum(axis=0), axis=1)
            self.downstream_allocation_matrix = L12_normalised
        else:
            raise ValueError("Downstream allocation matrix must be either 'A12' or 'L12'.")

        self.production_downstream = self.downstream_allocation_matrix.dot(self.production_downstream_all)

        self.demand_final_diagonal = pd.DataFrame(data=np.diag(v=Y1.sum(axis=1)), index=Y1.index, columns=Y1.index)
        self.demand_intermediate_diagonal = pd.DataFrame(
            data=np.diag(v=self.production_downstream.sum(axis=1)),
            index=self.production_downstream.index,
            columns=self.production_downstream.index,
        )

        self.production = self.H.dot(other=(self.demand_final_diagonal + self.demand_intermediate_diagonal))
        self.production_upstream_first_tier = A21.dot(self.production)
        self.production_upstream = self.L22.dot(self.production_upstream_first_tier)

        if multipliers:
            self.M_production = self.production.div(x.loc[index_extraction, "indout"], axis=0).replace(np.nan, 0)
            self.M_production_upstream_first_tier = self.production_upstream_first_tier.div(
                x.loc[index_extraction, "indout"], axis=1
            ).replace(np.nan, 0)
            self.M_upstream = self.production_upstream.div(x.loc[index_extraction, "indout"], axis=1).replace(
                np.nan, 0
            )
            self.M_downstream = self.production_downstream.div(x.loc[index_extraction, "indout"], axis=0).replace(
                np.nan, 0
            )

        return self

    def calculate_impacts(self, intensities=None):
        """
        Calculate the impacts of the hypothetical extraction based on the provided intensities.

        Parameters
        ----------
        intensities : pd.Series or pd.DataFrame
            Environmental intensities for the extraction sectors and other sectors.
            If a Series, it should have the extraction sectors as index.
            If a DataFrame, it should have the extraction sectors as columns and other sectors as index.

        Raises
        ------
        TypeError
            If the intensities are not a pandas Series or DataFrame.

        """
        # Keep details, if intensities are a Series
        if type(intensities) is pd.Series:
            self.intensities = [intensities.name]
            self.impact_production = self.production.mul(intensities.loc[self.index_extraction], axis=0)
            self.impact_upstream_first_tier = self.production_upstream_first_tier.mul(
                intensities.loc[self.index_other], axis=0
            )
            self.impact_upstream = self.production_upstream.mul(intensities.loc[self.index_other], axis=0)
            self.impact_downstream = self.production_downstream.mul(intensities.loc[self.index_other], axis=1)

            if self.meta["multipliers"]:
                self.M_impact_production = self.M_production.mul(intensities.loc[self.index_extraction], axis=0)
                self.M_impact_upstream_first_tier = self.M_production_upstream_first_tier.mul(
                    intensities.loc[self.index_other], axis=0
                )
                self.M_impact_upstream = self.M_upstream.mul(intensities.loc[self.index_other], axis=0)
                self.M_impact_downstream = self.M_downstream.mul(intensities.loc[self.index_other], axis=1)

        # Drop details, if intensities are a DataFrame
        elif type(intensities) is pd.DataFrame:
            self.intensities = intensities.index.to_list()
            self.impact_production = intensities.loc[:, self.index_extraction].dot(self.production)
            self.impact_upstream_first_tier = intensities.loc[:, self.index_other].dot(
                self.production_upstream_first_tier
            )
            self.impact_upstream = intensities.loc[:, self.index_other].dot(self.production_upstream)
            self.impact_downstream = self.production_downstream.dot(intensities.loc[:, self.index_other].T).T

            if self.meta["multipliers"]:
                self.M_impact_production = intensities.loc[:, self.index_extraction].dot(self.M_production)
                self.M_impact_upstream_first_tier = intensities.loc[:, self.index_other].dot(
                    self.M_production_upstream_first_tier
                )
                self.M_impact_upstream = intensities.loc[:, self.index_other].dot(self.M_upstream)
                self.M_impact_downstream = self.M_downstream.dot(intensities.loc[:, self.index_other].T).T

        else:
            raise TypeError("Intensities must be either a pandas Series or a pandas DataFrame.")
        return self

    def save_extraction(self, save_path=None, save_core_IO=False, save_details=False):
        """
        Save the extraction results to the specified path.

        Parameters
        ----------
        save_path : str or Path, optional
            Path to save the extraction results. If not provided, the save path from the IOSystem will be used.
        save_core_IO : bool, optional
            Whether to save the core IO data (A and Y). Defaults to False.
        save_details : bool, optional
            Whether to save additional details like all downstream production,
            final demand diagonal, and intermediate demand diagonal. Defaults to False.

        Raises
        ------
        ValueError
            If no save path is provided.
        """
        if save_path is None:
            save_path = self.save_path

        if save_path is None:
            raise ValueError("No save path provided. Please provide a save path.")

        save_path = Path(save_path)
        self.save_path = save_path

        # Makes subfolders for individual regions and/or sectors,
        # if it is clearly that a single region and/or sector has been extracted.
        # Will make sure that things are not overwritten, if multiple regions and/or sectors are extracted in a loop.
        if self.extraction_regions is None:
            n_regions = None
        else:
            n_regions = len(self.extraction_regions)
        if self.extraction_sectors is None:
            n_sectors = None
        else:
            n_sectors = len(self.extraction_sectors)

        if (n_regions == 1) and (n_sectors == 1):
            extraction_save_path = save_path / f"{self.extraction_regions[0]}_{self.extraction_sectors[0]}"

        elif n_regions == 1:
            extraction_save_path = save_path / f"{self.extraction_regions[0]}"

        elif n_sectors == 1:
            extraction_save_path = save_path / f"{self.extraction_sectors[0]}"

        else:
            extraction_save_path = save_path

        self.extraction_save_path = extraction_save_path
        extraction_save_path.mkdir(parents=True, exist_ok=True)

        (
            self.index_extraction.to_frame().to_csv(
                extraction_save_path / "index_extraction.txt", sep="\t", index=False, header=False
            )
        )
        (
            self.index_other.to_frame().to_csv(
                extraction_save_path / "index_other.txt", sep="\t", index=False, header=False
            )
        )
        self.L22.to_csv(extraction_save_path / "L22.txt", sep="\t")
        self.H.to_csv(extraction_save_path / "H.txt", sep="\t")
        (
            self.downstream_allocation_matrix.to_csv(
                extraction_save_path / f"{self.meta['downstream_allocation_matrix']}.txt", sep="\t"
            )
        )

        self.production.to_csv(extraction_save_path / "production.txt", sep="\t")
        (
            self.production_upstream_first_tier.to_csv(
                extraction_save_path / "production_upstream_first_tier.txt", sep="\t"
            )
        )
        self.production_upstream.to_csv(extraction_save_path / "production_upstream.txt", sep="\t")
        self.production_downstream.to_csv(extraction_save_path / "production_downstream.txt", sep="\t")

        if self.meta["multipliers"]:
            self.M_production.to_csv(extraction_save_path / "M_production.txt", sep="\t")
            (
                self.M_production_upstream_first_tier.to_csv(
                    extraction_save_path / "M_production_upstream_first_tier.txt", sep="\t"
                )
            )
            self.M_upstream.to_csv(extraction_save_path / "M_upstream.txt", sep="\t")
            self.M_downstream.to_csv(extraction_save_path / "M_downstream.txt", sep="\t")

        if save_core_IO:
            self.A.to_csv(extraction_save_path / "A.txt", sep="\t")
            self.Y.to_csv(extraction_save_path / "Y.txt", sep="\t")

        if save_details:
            self.production_downstream_all.to_csv(extraction_save_path / "production_downstream_all.txt", sep="\t")
            self.demand_final_diagonal.to_csv(extraction_save_path / "demand_final_diagonal.txt", sep="\t")
            (
                self.demand_intermediate_diagonal.to_csv(
                    extraction_save_path / "demand_intermediate_diagonal.txt", sep="\t"
                )
            )

        with open(extraction_save_path / "meta.json", "w") as json_file:
            json.dump(self.meta, json_file, indent=4)

    def save_impacts(self, extension=None, specific_impact=None):
        """
        Save the impacts of the hypothetical extraction to the specified path.

        Parameters
        ----------
        extension : str, optional
            Account name for the impacts. If not provided, the impacts will be saved in a general "impacts" folder.
        specific_impact : str, optional
            Specific impact name for the impacts. If provided, the impacts will be saved in a subfolder with this name.

        Raises
        ------
        ValueError
            If no save path is provided.

        """
        if (extension is None) & (specific_impact is None):
            save_path = Path(self.extraction_save_path) / "impacts"
        elif (extension is None) & (specific_impact is not None):
            save_path = Path(self.extraction_save_path) / "impacts" / specific_impact
        else:
            save_path = Path(self.extraction_save_path) / "impacts" / extension

        save_path.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(self.intensities).to_csv(save_path / "extensions.txt", sep="\t", index=False, header=False)
        self.impact_production.to_csv(save_path / "impact_production.txt", sep="\t")
        self.impact_upstream_first_tier.to_csv(save_path / "impact_upstream_first_tier.txt", sep="\t")
        self.impact_upstream.to_csv(save_path / "impact_upstream.txt", sep="\t")
        self.impact_downstream.to_csv(save_path / "impact_downstream.txt", sep="\t")

        if self.meta["multipliers"]:
            self.M_impact_production.to_csv(save_path / "M_impact_production.txt", sep="\t")
            self.M_impact_upstream_first_tier.to_csv(save_path / "M_impact_upstream_first_tier.txt", sep="\t")
            self.M_impact_upstream.to_csv(save_path / "M_impact_upstream.txt", sep="\t")
            self.M_impact_downstream.to_csv(save_path / "M_impact_downstream.txt", sep="\t")

# %%

def load_extraction(extraction_path, load_multipliers=True, load_core=True, load_details=True):
    """Load extraction results from the specified path.

    Parameters
    ----------
    extraction_path : str or Path
        Path to the extraction results.
    load_multipliers : bool, optional
        Whether to load the multipliers (M_production, M_production_upstream_first_tier, M_upstream, M_downstream).
    load_core : bool, optional
        Whether to load the core IO data (A, Y).
    load_details : bool, optional
        Whether to load additional details 
        (production_downstream_all, demand_final_diagonal, demand_intermediate_diagonal).

    Returns
    -------
    HEM
        An instance of the HEM class with the loaded extraction results.
    """
    extraction_path = Path(extraction_path)

    if list(extraction_path.glob("meta.json")):
        with open(extraction_path / "meta.json") as json_file:
            meta = json.load(json_file)

    if list(extraction_path.glob("index_extraction.txt")):
        index_extraction = pd.read_csv(extraction_path / "index_extraction.txt", sep="\t", header=None)
        if index_extraction.shape[1] == 1:
            index_extraction = pd.Index(index_extraction.iloc[:, 0]).unique()
            dimensions = [0]
        elif index_extraction.shape[1] == 2:
            index_extraction = pd.MultiIndex.from_frame(index_extraction)
            dimensions = [0, 1]

    if list(extraction_path.glob("index_other.txt")):
        index_other = pd.read_csv(extraction_path / "index_other.txt", sep="\t", header=None)
        if index_other.shape[1] == 1:
            index_other = pd.Index(index_other.iloc[:, 0]).unique()
        elif index_other.shape[1] == 2:
            index_other = pd.MultiIndex.from_frame(index_other)


    if list(extraction_path.glob("L22.txt")):
        L22 = pd.read_csv(extraction_path / "L22.txt", sep="\t", index_col=dimensions, header=dimensions)
    if list(extraction_path.glob("H.txt")):
        H = pd.read_csv(extraction_path / "H.txt", sep="\t", index_col=dimensions, header=dimensions)

    if list(extraction_path.glob(f"{meta['downstream_allocation_matrix']}.txt")):
        downstream_allocation_matrix = pd.read_csv(
            extraction_path / f"{meta['downstream_allocation_matrix']}.txt", sep="\t", index_col=dimensions, header=dimensions
        )

    if list(extraction_path.glob("production.txt")):
        production = pd.read_csv(extraction_path / "production.txt", sep="\t", index_col=dimensions, header=dimensions)
    if list(extraction_path.glob("production_upstream_first_tier.txt")):
        production_upstream_first_tier = pd.read_csv(
            extraction_path / "production_upstream_first_tier.txt", sep="\t", index_col=dimensions, header=dimensions
        )
    if list(extraction_path.glob("production_upstream.txt")):
        production_upstream = pd.read_csv(
            extraction_path / "production_upstream.txt", sep="\t", index_col=dimensions, header=dimensions
        )
    if list(extraction_path.glob("production_downstream.txt")):
        production_downstream = pd.read_csv(
            extraction_path / "production_downstream.txt", sep="\t", index_col=dimensions, header=dimensions
        )

    if load_multipliers:
        if list(extraction_path.glob("M_production.txt")):
            M_production = pd.read_csv(extraction_path / "M_production.txt", sep="\t", index_col=dimensions, header=dimensions)
        if list(extraction_path.glob("M_production_upstream_first_tier.txt")):
            M_production_upstream_first_tier = pd.read_csv(
                extraction_path / "M_production_upstream_first_tier.txt", sep="\t", index_col=dimensions, header=dimensions
            )
        if list(extraction_path.glob("M_upstream.txt")):
            M_upstream = pd.read_csv(extraction_path / "M_upstream.txt", sep="\t", index_col=dimensions, header=dimensions)
        if list(extraction_path.glob("M_downstream.txt")):
            M_downstream = pd.read_csv(extraction_path / "M_downstream.txt", sep="\t", index_col=dimensions, header=dimensions)

    if load_core:
        if list(extraction_path.glob("A.txt")):
            A = pd.read_csv(extraction_path / "A.txt", sep="\t", index_col=dimensions, header=dimensions)
        if list(extraction_path.glob("Y.txt")):
            Y = pd.read_csv(extraction_path / "Y.txt", sep="\t", index_col=dimensions, header=dimensions)

    if load_details:
        if list(extraction_path.glob("production_downstream_all.txt")):
            production_downstream_all = pd.read_csv(
                extraction_path / "production_downstream_all.txt", sep="\t", index_col=dimensions, header=dimensions
            )
        if list(extraction_path.glob("demand_final_diagonal.txt")):
            demand_final_diagonal = pd.read_csv(
                extraction_path / "demand_final_diagonal.txt", sep="\t", index_col=dimensions, header=dimensions
            )
        if list(extraction_path.glob("demand_intermediate_diagonal.txt")): 
            demand_intermediate_diagonal = pd.read_csv(
                extraction_path / "demand_intermediate_diagonal.txt", sep="\t", index_col=dimensions, header=dimensions
            )
    HEM_extraction = HEM()
    HEM_extraction.extraction_save_path = extraction_path
    HEM_extraction.meta = meta
    HEM_extraction.index_extraction = index_extraction
    HEM_extraction.index_other = index_other

    HEM_extraction.L22 = L22
    HEM_extraction.H = H

    HEM_extraction.downstream_allocation_matrix = downstream_allocation_matrix
    HEM_extraction.production = production
    HEM_extraction.production_upstream_first_tier = production_upstream_first_tier
    HEM_extraction.production_upstream = production_upstream
    HEM_extraction.production_downstream = production_downstream

    if load_multipliers:
        HEM_extraction.M_production = M_production
        HEM_extraction.M_production_upstream_first_tier = M_production_upstream_first_tier
        HEM_extraction.M_upstream = M_upstream
        HEM_extraction.M_downstream = M_downstream

    if load_core:
        HEM_extraction.A = A
        HEM_extraction.Y = Y

    if load_details:
        HEM_extraction.production_downstream_all = production_downstream_all
        HEM_extraction.demand_final_diagonal = demand_final_diagonal
        HEM_extraction.demand_intermediate_diagonal = demand_intermediate_diagonal

    return HEM_extraction

# %%

