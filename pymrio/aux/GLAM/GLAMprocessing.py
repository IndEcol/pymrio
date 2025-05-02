""" Function for getting and processing GLAM data.

"""

from pathlib import Path
from pymrio.tools.iodownloader import _download_urls
from pymrio.tools.iometadata import MRIOMetaData

import pandas as pd
from pandas._libs.parsers import STR_NA_VALUES

import zipfile

GLAM_CONFIG = {
    "V2024.10": "https://www.lifecycleinitiative.org/wp-content/uploads/2024/10/V1.0.2024.10.zip"
}


def get_GLAM(storage_folder, overwrite_existing=False, version="V2024.10"):
    """Download GLAM and store in the given directory

    Parameters
    ----------
    storage_folder : str or Path
        Folder to store the downloaded GLAM data

    overwrite_existing : bool, optional
        If True, overwrite existing data, by default False

    version : str, optional
        Version of the GLAM data to download, by default "V2024.10"
        Version must be a key in the GLAM_CONFIG or can alternatively
        be a url to the zip file to download.
    """

    if isinstance(storage_folder, str):
        storage_folder = Path(storage_folder)
    storage_folder.mkdir(exist_ok=True, parents=True)

    downlog = MRIOMetaData._make_download_log(
        location=storage_folder,
        description="GLAM download",
        name="GLAM",
        system="impact assessment",
        version=version,
    )

    requested_urls = [GLAM_CONFIG.get(version, version)]

    downlog = _download_urls(
        url_list=requested_urls,
        storage_folder=storage_folder,
        overwrite_existing=overwrite_existing,
        downlog_handler=downlog,
    )

    downlog.save()
    return downlog


def prep_GLAM(GLAM_data):
    """Extract/read GLAM data and convert to valid characterization file

    This reads the data either from the GLAM zip archive or from the
    extracted GLAM folder. It then merges all GLAM xlsx files and
    renames the header to make it a valid characterization table
    for pymrio.

    GLAM_data : Path or str
        Path to the GLAM zip archive or the extracted GLAM folder.
        If the ending is .zip, data is read directly from the zip archive.
        Otherwise, the routing finds all xlsx files in the folder given
        in GLAM_data.

    Returns
    -------
    pd.DataFrame
        DataFrame with the GLAM data in the format needed for pymrio

    """
    GLAM_subfolders = ["EQ", "HH", "SEA"]

    if isinstance(GLAM_data, str):
        GLAM_data = Path(GLAM_data)

    def read_GLAM_xlsx(file):
        accepted_na_values = STR_NA_VALUES - {"NA"}
        GLAMdata = pd.read_excel(
            file,
            sheet_name="lciamethods_CF_GLAM",
            keep_default_na=False,
            na_values=accepted_na_values,
            dtype={
                "FLOW_uuid": str,
                "FLOW_name": str,
                "FLOW_casnumber": str,
                "LCIAMethod_location": str,
                "LCIAMethod_location_name": str,
                "LCIAMethod_loction_ISO2": str,
                "CF": float,
                "Unit": str,
                "CF_Uncertainty_Lower": float,
                "CF_Uncertainty_Higher": float,
                "FLOW_class0": str,
                "FLOW_class1": str,
                "FLOW_class2": str,
                "Species": str,
                "LCIAMethod_realm": str,
                "LCIAMethod_mathematicalApproach": str,
                "Scenario": str,
                "CF_derivation": str,
                "Matching_CF": str,
                "Matching_Compartment": str,
                "LCIAMethod_type": str,
                "LCIAMethod_name": str,
            },
        )
        return GLAMdata

    GLAM_collector = {}

    if GLAM_data.suffix == ".zip":
        with zipfile.ZipFile(GLAM_data, "r") as zz:
            all_xlsx = [
                xlsx
                for xlsx in zz.namelist()
                for subfolder in GLAM_subfolders
                if subfolder in xlsx
            ]
            for xlsx in all_xlsx:
                print(f"Reading {xlsx}")
                data_name = Path(xlsx).stem
                GLAM_collector[data_name] = read_GLAM_xlsx(zz.open(xlsx))

    else:
        # read all xlsx files in the folder
        all_xlsx = [
            xlsx
            for xlsx in GLAM_data.rglob("*.xlsx")
            for subfolder in GLAM_subfolders
            if subfolder in xlsx.name
        ]
        for xlsx in all_xlsx:
            print(f"Reading {xlsx}")
            data_name = xlsx.stem
            GLAM_collector[data_name] = read_GLAM_xlsx(xlsx)

    GLAM_full = pd.concat(GLAM_collector, axis=0, ignore_index=True)

    # TODO: base it on flow name/classes, not uuid
    GLAM_char_col_rename = {
        "LCIAMethod_name": "LCIAMethod_name__FLOW_uuid",
        "LCIAMethod_realm": "LCIAMethod_realm__FLOW_uuid",
        "LCIAMethod_location_ISO2": "region",
        "Unit": "unit_new",
        "CF": "factor",
    }

    GLAM_char_col_dtypes = {
        "LCIAMethod_name__FLOW_uuid": str,
        "LCIAMethod_realm__FLOW_uuid": str,
        "region": str,
        "unit_new": str,
        "factor": float,
    }

    # Find nan in GLAM_full columns iso 2
    # TODO: change to raise error
    iso2nans = GLAM_full.loc[GLAM_full.LCIAMethod_location_ISO2.isna(), :]
    print(f"Found {iso2nans.shape[0]} rows with nan in LCIAMethod_location_ISO2")

    GLAM_res = (
        GLAM_full.loc[
            :,
            [
                "FLOW_uuid",
                "LCIAMethod_name",
                "LCIAMethod_realm",
                "CF",
                "LCIAMethod_location_ISO2",
                "Unit",
            ],
        ]
        .rename(columns=GLAM_char_col_rename)
        .astype(GLAM_char_col_dtypes)
    )

    # make the unit conversion - this assumes the flows in EXIOBASE will be already
    # converted to the correct denominator. It will be checked(by the convert method)!
    GLAM_res.loc[:, "unit_orig"] = GLAM_res["unit_new"].str.split("/").str[1]

    # update the regions with the regex needed for EXIOBASE

    # global characterizations for Climate Change apply to all regions in EXIOBASE
    GLAM_res.loc[
        GLAM_res.LCIAMethod_name__FLOW_uuid == "EQ Climate Change", "region"
    ] = ".*"

    # using China characterization factors for Taiwan as well
    GLAM_res.loc[GLAM_res.region == "CN", "region"] = "CN|TW"

    # Use the GLO value for all rest of world regions
    GLAM_res.loc[GLAM_res.region == "GLO", "region"] = "WA|WL|WE|WF|WM"

    return GLAM_res


def get_GLAM_EXIO3_bridge(GLAM_version="V2024.10", EXIOBASE_version="3.8.2"):
    """Get GLAM bridge for EXIOBASE stressors"""

    if GLAM_version != "V2024.10":
        raise NotImplementedError("Only the V2024.10 version is supported")

    if EXIOBASE_version != "3.8.2":
        raise NotImplementedError("Only the 3.8.2 version is supported")

    # get directory of currrent file
    # HACK: needs to be in the data folder, include in package
    current_dir = Path(__file__).parent
    return pd.read_csv(current_dir / "EXIO382_to_GLAM202410.tsv", sep="\t")
