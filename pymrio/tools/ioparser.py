"""Various parser for available MRIOs and files in a similar format.

KST 20140903
"""

import glob
import itertools
import logging
import os
import re
import warnings
import zipfile
from collections import namedtuple

import numpy as np
import pandas as pd

# Constants and global variables
from pymrio.core.constants import PYMRIO_PATH
from pymrio.core.fileio import load_all
from pymrio.core.mriosystem import Extension, IOSystem
from pymrio.tools.iometadata import MRIOMetaData
from pymrio.tools.ioutil import get_repo_content, sniff_csv_format

# Exceptions


class ParserError(Exception):
    """Base class for errors concerning parsing of IO source files."""

    pass


class ParserWarning(UserWarning):
    """Base class for warnings concerning parsing of IO source files."""

    pass


IDX_NAMES = {
    "Z_col": ["region", "sector"],
    "Z_row": ["region", "sector"],
    "Z_row_unit": ["region", "sector", "unit"],
    "A_col": ["region", "sector"],
    "A_row": ["region", "sector"],
    "A_row_unit": ["region", "sector", "unit"],
    "Y_col1": ["region"],
    "Y_col2": ["region", "category"],
    "Y_row": ["region", "sector"],
    "Y_row_unit": ["region", "sector", "unit"],
    "F_col": ["region", "sector"],
    "F_row_single": ["stressor"],
    "F_row_unit": ["stressor", "unit"],
    "F_row_comp_unit": ["stressor", "compartment", "unit"],
    "F_row_src_unit": ["stressor", "source", "unit"],
    "F_row_src": ["stressor", "source"],
    "F_row_cat_unit": ["stressor", "category", "unit"],
    "VA_row_single": ["inputtype"],
    "VA_row_unit": ["inputtype", "unit"],
    "VA_row_unit_cat": ["inputtype", "category"],
    "VA_row_region": ["region", "inputtype"],
    "unit": ["unit"],
    "_reg_sec_unit": ["region", "sector", "unit"],
    "T_col": ["region", "system", "sector"],
    "T_row": ["region", "system", "sector"],
}


# Top level functions
def parse_exio12_ext(
    ext_file,
    index_col,
    name,
    drop_compartment=True,
    version=None,
    year=None,
    iosystem=None,
    sep=",",
):
    """Parse an EXIOBASE version 1 or 2 like extension file into pymrio.Extension.

    EXIOBASE like extensions files are assumed to have two
    rows which are used as columns multiindex (region and sector)
    and up to three columns for the row index (see Parameters).

    For EXIOBASE 3 - extension can be loaded directly with pymrio.load

    Notes
    -----
    So far this only parses factor of production extensions F (not
    final demand extensions F_Y nor coeffiecents S).

    Parameters
    ----------
    ext_file : string or pathlib.Path
        File to parse

    index_col : int
        The number of columns (1 to 3) at the beginning of the file
        to use as the index. The order of the index_col must be
        - 1 index column: ['stressor']
        - 2 index columns: ['stressor', 'unit']
        - 3 index columns: ['stressor', 'compartment', 'unit']
        - > 3: everything up to three index columns will be removed

    name : string
        Name of the extension

    drop_compartment : boolean, optional
        If True (default) removes the compartment from the index.

    version : string, optional
        see pymrio.Extension

    iosystem : string, optional
        see pymrio.Extension

    year : string or int
        see pymrio.Extension

    sep : string, optional
        Delimiter to use; default ','

    Returns
    -------
    pymrio.Extension
        with F (and unit if available)

    """
    ext_file = os.path.abspath(str(ext_file))

    F = pd.read_csv(ext_file, header=[0, 1], index_col=list(range(index_col)), sep=sep)

    F.columns.names = ["region", "sector"]

    if index_col == 1:
        F.index.names = ["stressor"]

    elif index_col == 2:
        F.index.names = ["stressor", "unit"]

    elif index_col == 3:
        F.index.names = ["stressor", "compartment", "unit"]

    else:
        F = F.reset_index(level=list(range(3, index_col)), drop=True)
        F.index.names = ["stressor", "compartment", "unit"]

    unit = None
    if index_col > 1:
        unit = pd.DataFrame(F.iloc[:, 0].reset_index(level="unit").unit)
        F = F.reset_index(level="unit", drop=True)

    if drop_compartment:
        try:
            F = F.reset_index(level="compartment", drop=True)
            unit = unit.reset_index(level="compartment", drop=True)

        except KeyError:
            # In case compartment was not part to begin with
            pass

    return Extension(
        name=name,
        F=F,
        unit=unit,
        iosystem=iosystem,
        version=version,
        year=year,
    )


def get_exiobase12_version(filename):
    """Return the EXIOBASE version for the given filename.

    None if not found
    """
    try:
        ver_match = re.search(r"(\d+\w*(\.|\-|\_))*\d+\w*", filename)
        version = ver_match.string[ver_match.start() : ver_match.end()]
        if re.search(r"\_\d\d\d\d", version[-5:]):
            version = version[:-5]
    except AttributeError:
        version = None

    return version


def get_exiobase_files(path, coefficients=True):
    """Get the EXIOBASE files in path (which can be a zip file).

    Parameters
    ----------
    path: str or pathlib.Path
        Path to exiobase files or zip file
    coefficients: boolean, optional
        If True (default), considers the mrIot file as A matrix,
        and the extensions as S matrices. Otherwise as Z and F, respectively

    Returns
    -------
    dict of dict
    """
    path = os.path.normpath(str(path))
    if coefficients:
        exio_core_regex = {
            # don’t match file if starting with _
            "A": re.compile(r"(?<!\_)mrIot.*txt"),
            "Y": re.compile(r"(?<!\_)mrFinalDemand.*txt"),
            "S_factor_inputs": re.compile(r"(?<!\_)mrFactorInputs.*txt"),
            "S_emissions": re.compile(r"(?<!\_)mrEmissions.*txt"),
            "S_materials": re.compile(r"(?<!\_)mrMaterials.*txt"),
            "S_resources": re.compile(r"(?<!\_)mrResources.*txt"),
            "F_Y_resources": re.compile(r"(?<!\_)mrFDResources.*txt"),
            "F_Y_emissions": re.compile(r"(?<!\_)mrFDEmissions.*txt"),
            "F_Y_materials": re.compile(r"(?<!\_)mrFDMaterials.*txt"),
        }
    else:
        exio_core_regex = {
            # don’t match file if starting with _
            "Z": re.compile(r"(?<!\_)mrIot.*txt"),
            "Y": re.compile(r"(?<!\_)mrFinalDemand.*txt"),
            "F_factor_inputs": re.compile(r"(?<!\_)mrFactorInputs.*txt"),
            "F_emissions": re.compile(r"(?<!\_)mrEmissions.*txt"),
            "F_materials": re.compile(r"(?<!\_)mrMaterials.*txt"),
            "F_resources": re.compile(r"(?<!\_)mrResources.*txt"),
            "F_Y_emissions": re.compile(r"(?<!\_)mrFDEmissions.*txt"),
            "F_Y_materials": re.compile(r"(?<!\_)mrFDMaterials.*txt"),
        }

    repo_content = get_repo_content(path)

    exio_files = {}
    for kk, vv in exio_core_regex.items():
        found_file = [vv.search(ff).string for ff in repo_content.filelist if vv.search(ff)]
        if len(found_file) > 1:
            logging.warning(f"Multiple files found for {kk}: {found_file} - USING THE FIRST ONE")
            found_file = found_file[0:1]
        elif len(found_file) == 0:
            continue
        else:
            logging.debug(f"Process file {found_file[0]}")
            if repo_content.iszip:
                format_para = sniff_csv_format(found_file[0], zip_file=path)
            else:
                format_para = sniff_csv_format(os.path.join(path, found_file[0]))
            exio_files[kk] = {
                "root_repo": path,
                "file_path": found_file[0],
                "version": get_exiobase12_version(os.path.basename(found_file[0])),
                "index_rows": format_para["nr_header_row"],
                "index_col": format_para["nr_index_col"],
                "unit_col": format_para["nr_index_col"] - 1,
                "sep": format_para["sep"],
            }

    return exio_files


def generic_exiobase12_parser(exio_files, system=None):
    """Parse EXIOBASE version 1 and 2.

    This is used internally by parse_exiobase1 / 2 functions to
    parse exiobase files. In most cases, these top-level functions
    should just work, but in case of archived exiobase versions
    it might be necessary to use low-level function here.

    Parameters
    ----------
    exio_files: dict of dict

    system: str (pxp or ixi)
        Only used for the metadata

    """
    version = " & ".join({dd.get("version", "") for dd in exio_files.values() if dd.get("version", "")})

    meta_rec = MRIOMetaData(system=system, name="EXIOBASE", version=version)

    if len(version) == 0:
        meta_rec.note("No version information found, assuming exiobase 1")
        meta_rec.change_meta("version", 1)
        version = "1"

    core_components = ["A", "Y", "Z"]

    core_data = {}
    ext_data = {}
    for tt, tpara in exio_files.items():
        full_file_path = os.path.join(tpara["root_repo"], tpara["file_path"])
        logging.debug(f"Parse {full_file_path}")
        if tpara["root_repo"][-3:] == "zip":
            with zipfile.ZipFile(tpara["root_repo"], "r") as zz:
                raw_data = pd.read_csv(
                    zz.open(tpara["file_path"]),
                    index_col=list(range(tpara["index_col"])),
                    header=list(range(tpara["index_rows"])),
                    sep="\t",
                )
        else:
            raw_data = pd.read_csv(
                full_file_path,
                index_col=list(range(tpara["index_col"])),
                header=list(range(tpara["index_rows"])),
                sep="\t",
            )

        meta_rec._add_fileio(f"EXIOBASE data {tt} parsed from {full_file_path}")
        if tt in core_components:
            core_data[tt] = raw_data
        else:
            ext_data[tt] = raw_data

    for table in core_data:
        core_data[table].index.names = ["region", "sector", "unit"]
        if table == "A" or table == "Z":
            core_data[table].columns.names = ["region", "sector"]
            _unit = pd.DataFrame(core_data[table].iloc[:, 0]).reset_index(level="unit").unit
            _unit = pd.DataFrame(_unit)
            _unit.columns = ["unit"]
        if table == "Y":
            core_data[table].columns.names = ["region", "category"]
        core_data[table] = core_data[table].reset_index(level="unit", drop=True)

    core_data["unit"] = _unit

    mon_unit = core_data["unit"].iloc[0, 0]
    if "/" in mon_unit:
        mon_unit = mon_unit.split("/")[0]
        core_data["unit"].unit = mon_unit

    extensions = {}
    for tt, tpara in exio_files.items():
        if tt in core_components:
            continue

        # The following depends on the format (upper/lower case) of the
        # dict keys returned by get_exiobase_files
        ext_name = "_".join(re.findall(r"[a-z]+", tt))
        table_type = re.match(r"[A-Z_]+", tt)[0].rstrip("_")

        if tpara["index_col"] == 3:
            ext_data[tt].index.names = ["stressor", "compartment", "unit"]
        elif tpara["index_col"] == 2:
            ext_data[tt].index.names = ["stressor", "unit"]
        else:
            raise ParserError("Unknown EXIOBASE file structure")

        if table_type == "F_Y":
            ext_data[tt].columns.names = ["region", "category"]
        else:
            ext_data[tt].columns.names = ["region", "sector"]
        try:
            _unit = pd.DataFrame(ext_data[tt].iloc[:, 0]).reset_index(level="unit").unit
        except IndexError:
            _unit = pd.DataFrame(ext_data[tt].iloc[:, 0])
            _unit.columns = ["unit"]
            _unit["unit"] = "undef"
            _unit = _unit.reset_index(level="unit", drop=True)
            _unit = pd.DataFrame(_unit)
            _unit.columns = ["unit"]

        _unit = pd.DataFrame(_unit)
        _unit.columns = ["unit"]
        _new_unit = _unit.unit.str.replace("/" + mon_unit, "", regex=True)
        _new_unit[_new_unit == ""] = _unit.unit[_new_unit == ""].str.replace("/", "", regex=True)
        _unit.unit = _new_unit

        ext_data[tt] = ext_data[tt].reset_index(level="unit", drop=True)
        ext_dict = extensions.get(ext_name, {})
        ext_dict.update({table_type: ext_data[tt], "unit": _unit, "name": ext_name})
        extensions.update({ext_name: ext_dict})

    if version[0] == "1" or version[0] == "2":
        year = 2000
    elif version[0] == "3":
        raise ParserError("This function can not be used to parse EXIOBASE 3")
    else:
        logging.warning("Unknown EXIOBASE version")
        year = None

    return IOSystem(
        version=version,
        price="current",
        year=year,
        meta=meta_rec,
        **dict(core_data, **extensions),
    )


def _get_MRIO_system(path):
    """Extract system information (ixi, pxp) from file path.

    Returns 'ixi' or 'pxp', None in undetermined
    """
    ispxp = True if re.search("pxp", path, flags=re.IGNORECASE) else False
    isixi = True if re.search("ixi", path, flags=re.IGNORECASE) else False

    if ispxp == isixi:
        system = None
    else:
        system = "pxp" if ispxp else "ixi"
    return system


def parse_exiobase1(path):
    """Parse the exiobase1 raw data files.

    This function works with

    - pxp_ita_44_regions_coeff_txt
    - ixi_fpa_44_regions_coeff_txt
    - pxp_ita_44_regions_coeff_src_txt
    - ixi_fpa_44_regions_coeff_src_txt

    which can be found on www.exiobase.eu

    The parser works with the compressed (zip) files as well as the unpacked
    files.

    Parameters
    ----------
    path : pathlib.Path or string
        Path of the exiobase 1 data

    Returns
    -------
    pymrio.IOSystem with exio1 data

    """
    path = os.path.abspath(os.path.normpath(str(path)))

    exio_files = get_exiobase_files(path)
    if len(exio_files) == 0:
        raise ParserError(f"No EXIOBASE files found at {path}")

    system = _get_MRIO_system(path)
    if not system:
        logging.warning("Could not determine system (pxp or ixi) set system parameter manually")

    io = generic_exiobase12_parser(exio_files, system=system)
    return io


def parse_exiobase2(path, charact=True, popvector="exio2"):
    """Parse the exiobase 2.2.2 source files for the IOSystem.

    The function parse product by product and industry by industry source file
    in the coefficient form (A and S).

    Filenames are hardcoded in the parser - for any other function the code has
    to be adopted. Check git comments to find older verions.

    Parameters
    ----------
    path : string or pathlib.Path
        Path to the EXIOBASE source files
    charact : string or boolean, optional
        Filename with path to the characterisation matrices for the extensions
        (xls). This is provided together with the EXIOBASE system and given as
        a xls file. The four sheets  Q_factorinputs, Q_emission, Q_materials
        and Q_resources are read and used to generate one new extensions with
        the impacts.
        If set to True, the characterisation file found in path is used (
        can be in the zip or extracted). If a string, it is assumed that
        it points to valid characterisation file. If False or None, no
        characterisation file will be used.
    popvector : string or pd.DataFrame, optional
        The population vector for the countries.  This can be given as
        pd.DataFrame(index = population, columns = countrynames) or, (default)
        will be taken from the pymrio module. If popvector = None no population
        data will be passed to the IOSystem.

    Returns
    -------
    IOSystem
        A IOSystem with the parsed exiobase 2 data

    Raises
    ------
    ParserError
        If the exiobase source files are not complete in the given path

    """
    path = os.path.abspath(os.path.normpath(str(path)))

    exio_files = get_exiobase_files(path)
    if len(exio_files) == 0:
        raise ParserError(f"No EXIOBASE files found at {path}")

    system = _get_MRIO_system(path)
    if not system:
        logging.warning("Could not determine system (pxp or ixi) set system parameter manually")

    io = generic_exiobase12_parser(exio_files, system=system)

    # read the characterisation matrices if available
    # and build one extension with the impacts
    if charact:
        logging.debug("Parse characterisation matrix")
        # dict with correspondence to the extensions
        Qsheets = {
            "Q_factorinputs": "factor_inputs",
            "Q_emission": "emissions",
            "Q_materials": "materials",
            "Q_resources": "resources",
        }

        Q_head_col = {}
        Q_head_row = {}
        Q_head_col_rowname = {}
        Q_head_col_rowunit = {}
        # Q_head_col_metadata = dict()
        # number of cols containing row headers at the beginning
        Q_head_col["Q_emission"] = 4
        # number of rows containing col headers at the top - this will be
        # skipped
        Q_head_row["Q_emission"] = 3
        # assuming the same classification as in the extensions
        Q_head_col["Q_factorinputs"] = 2
        Q_head_row["Q_factorinputs"] = 2
        Q_head_col["Q_resources"] = 2
        Q_head_row["Q_resources"] = 3
        Q_head_col["Q_materials"] = 2
        Q_head_row["Q_materials"] = 2

        #  column to use as name for the rows
        Q_head_col_rowname["Q_emission"] = 1
        Q_head_col_rowname["Q_factorinputs"] = 0
        Q_head_col_rowname["Q_resources"] = 0
        Q_head_col_rowname["Q_materials"] = 0

        # column to use as unit for the rows which gives also the last column
        # before the data
        Q_head_col_rowunit["Q_emission"] = 3
        Q_head_col_rowunit["Q_factorinputs"] = 1
        Q_head_col_rowunit["Q_resources"] = 1
        Q_head_col_rowunit["Q_materials"] = 1

        if charact is str:
            charac_data = {
                Qname: pd.read_excel(
                    charact,
                    sheet_name=Qname,
                    skiprows=list(range(0, Q_head_row[Qname])),
                    header=None,
                )
                for Qname in Qsheets
            }
        else:
            _content = get_repo_content(path)
            charac_regex = re.compile(r"(?<!\_)(?<!\.)characterisation.*xlsx")
            charac_files = [ff for ff in _content.filelist if re.search(charac_regex, ff)]
            if len(charac_files) > 1:
                raise ParserError(f"Found multiple characcterisation files in {path} - specify one: {charac_files}")
            if len(charac_files) == 0:
                raise ParserError(f"No characcterisation file found in {path}")
            if _content.iszip:
                with zipfile.ZipFile(path, "r") as zz:
                    charac_data = {
                        Qname: pd.read_excel(
                            zz.open(charac_files[0]),
                            sheet_name=Qname,
                            skiprows=list(range(0, Q_head_row[Qname])),
                            header=None,
                        )
                        for Qname in Qsheets
                    }

            else:
                charac_data = {
                    Qname: pd.read_excel(
                        os.path.join(path, charac_files[0]),
                        sheet_name=Qname,
                        skiprows=list(range(0, Q_head_row[Qname])),
                        header=None,
                    )
                    for Qname in Qsheets
                }

        _unit = {}
        # temp for the calculated impacts which than
        # get summarized in the 'impact'
        _impact = {}
        impact = {}
        for Qname in Qsheets:
            # unfortunately the names in Q_emissions are
            # not completely unique - fix that
            if Qname == "Q_emission":
                _index = charac_data[Qname][Q_head_col_rowname[Qname]].copy()
                _index.iloc[42] = _index.iloc[42] + " 2008"
                _index.iloc[43] = _index.iloc[43] + " 2008"
                _index.iloc[44] = _index.iloc[44] + " 2010"
                _index.iloc[45] = _index.iloc[45] + " 2010"
                charac_data[Qname][Q_head_col_rowname[Qname]] = _index

            charac_data[Qname].index = charac_data[Qname][Q_head_col_rowname[Qname]]

            _unit[Qname] = pd.DataFrame(charac_data[Qname].iloc[:, Q_head_col_rowunit[Qname]])
            _unit[Qname].columns = ["unit"]
            _unit[Qname].index.name = "impact"
            charac_data[Qname] = charac_data[Qname].iloc[:, Q_head_col_rowunit[Qname] + 1 :]
            charac_data[Qname].index.name = "impact"

            try:
                _F_Y = io.__dict__[Qsheets[Qname]].F_Y.to_numpy()
            except AttributeError:
                _F_Y = np.zeros([io.__dict__[Qsheets[Qname]].S.shape[0], io.Y.shape[1]])

            _impact[Qname] = {
                "S": charac_data[Qname].dot(io.__dict__[Qsheets[Qname]].S.values),
                "F_Y": charac_data[Qname].dot(_F_Y),
                "unit": _unit[Qname],
            }

        impact["S"] = pd.concat(
            [
                _impact["Q_factorinputs"]["S"],
                _impact["Q_emission"]["S"],
                _impact["Q_materials"]["S"],
                _impact["Q_resources"]["S"],
            ]
        )
        impact["F_Y"] = pd.concat(
            [
                _impact["Q_factorinputs"]["F_Y"],
                _impact["Q_emission"]["F_Y"],
                _impact["Q_materials"]["F_Y"],
                _impact["Q_resources"]["F_Y"],
            ]
        )
        impact["S"].columns = io.emissions.S.columns
        impact["F_Y"].columns = io.emissions.F_Y.columns
        impact["uunit"] = pd.concat(
            [
                _impact["Q_factorinputs"]["unit"],
                _impact["Q_emission"]["unit"],
                _impact["Q_materials"]["unit"],
                _impact["Q_resources"]["unit"],
            ]
        )
        impact["name"] = "impact"
        io.impact = Extension(**impact)

    if popvector == "exio2":
        logging.debug("Read population vector")
        io.population = pd.read_csv(
            os.path.join(PYMRIO_PATH["exio2"], "misc", "population.txt"),
            index_col=0,
            sep="\t",
        ).astype(float)
    else:
        io.population = popvector

    return io


def parse_exiobase3(path):
    """Parse the public EXIOBASE 3 system.

    This parser works with either the compressed zip
    archive as downloaded or the extracted system.

    Note
    ----
    The exiobase 3 parser does so far not include
    population and characterization data.

    Parameters
    ----------
    path : string or pathlib.Path
        Path to the folder with the EXIOBASE files
        or the compressed archive.

    Returns
    -------
    IOSystem
        A IOSystem with the parsed exiobase 3 data

    """
    io = load_all(path)
    # need to rename the final demand satellite,
    # wrong name in the standard distribution
    try:
        io.satellite.F_Y = io.satellite.F_hh.copy()
        del io.satellite.F_hh
    except AttributeError:
        pass

    # some ixi in the exiobase 3.4 official distribution
    # have a country name mixup. Clean it here:
    io.rename_regions(
        {
            "AUS": "AU",
            "AUT": "AT",
            "BEL": "BE",
            "BGR": "BG",
            "BRA": "BR",
            "CAN": "CA",
            "CHE": "CH",
            "CHN": "CN",
            "CYP": "CY",
            "CZE": "CZ",
            "DEU": "DE",
            "DNK": "DK",
            "ESP": "ES",
            "EST": "EE",
            "FIN": "FI",
            "FRA": "FR",
            "GBR": "GB",
            "GRC": "GR",
            "HRV": "HR",
            "HUN": "HU",
            "IDN": "ID",
            "IND": "IN",
            "IRL": "IE",
            "ITA": "IT",
            "JPN": "JP",
            "KOR": "KR",
            "LTU": "LT",
            "LUX": "LU",
            "LVA": "LV",
            "MEX": "MX",
            "MLT": "MT",
            "NLD": "NL",
            "NOR": "NO",
            "POL": "PL",
            "PRT": "PT",
            "ROM": "RO",
            "RUS": "RU",
            "SVK": "SK",
            "SVN": "SI",
            "SWE": "SE",
            "TUR": "TR",
            "TWN": "TW",
            "USA": "US",
            "ZAF": "ZA",
            "WWA": "WA",
            "WWE": "WE",
            "WWF": "WF",
            "WWL": "WL",
            "WWM": "WM",
        }
    )

    return io


def parse_wiod(path, year=None, names=("isic", "c_codes"), popvector=None):
    """Parse the wiod source files for the IOSystem.

    WIOD provides the MRIO tables in excel - format (xlsx) at
    http://www.wiod.org/new_site/database/wiots.htm (release November 2013).
    To use WIOD in pymrio these (for the year of analysis) must be downloaded.
    The interindustry matrix of these files gets parsed in IOSystem.Z, the
    additional information is included as factor_input extension (value
    added,...)

    The folder with these xslx must than be passed to the WIOD parsing
    function. This folder may contain folders with the extension data. Every
    folder within the wiod root folder will be parsed for extension data and
    will be added to the IOSystem. The WIOD database offers the download of
    the environmental extensions as zip files. These can be read directly by
    the parser. In case a zip file and a folder with the same name are
    available, the data is read from the folder. If the zip files are
    extracted into folder, the folders must have the same name as the
    corresponding zip file (without the 'zip' extension).

    If a WIOD SEA file is present (at the root of path or in a folder named
    'SEA' - only one file!), the labor data of this file gets included in the
    factor_input extension (calculated for the the three skill levels
    available). The monetary data in this file is not added because it is only
    given in national currency.

    Since the "World Input-Output Tables in previous years' prices" are still
    under construction (20141129), no parser for these is provided.

    Some of the meta-parameter of the IOSystem are set automatically based on
    the values given in the first four cells and the name of the WIOD data
    files (base year, version, price, iosystem).
    These can be overwritten afterwards if needed.

    Parameters
    ----------
    path : string or pathlib.Path
        Path to the folder with the WIOD source files. In case that the path
        to a specific file is given, only this will be parsed irrespective of
        the values given in year.
    year : int or str
        Which year in the path should be parsed. The years can be given with
        four or two digits (eg [2012 or 12]). If the given path contains a
        specific file, the value of year will not be used (but inferred from
        the meta data)- otherwise it must be given For the monetary data the
        parser searches for files with 'wiot - two digit year'.
    names : string or tuple, optional
        WIOD provides three different sector/final demand categories naming
        schemes. These can can be specified for the IOSystem. Pass:

            1) 'isic': ISIC rev 3 Codes - available for interindustry flows
               and final demand rows.
            2) 'full': Full names - available for final demand rows and
               final demand columns (categories) and interindustry flows.
            3) 'c_codes' : WIOD specific sector numbers, available for final
               demand rows and columns (categories) and interindustry flows.

        Internally, the parser relies on 1) for the interindustry flows and 3)
        for the final demand categories. This is the default and will also be
        used if just 'isic' gets passed ('c_codes' also replace 'isic' if this
        was passed for final demand categories). To specify different finial
        consumption category names, pass a tuple with (sectors/interindustry
        classification, fd categories), eg ('isic', 'full'). Names are case
        insensitive and passing the first character is sufficient.
    TODO popvector : TO BE IMPLEMENTED (consistent with EXIOBASE)

    Returns
    -------
    IOSystem

    Raises
    ------
    ParserError
        If the WIOD source file are not complete or inconsistent

    """
    # Path manipulation, should work cross platform
    path = os.path.abspath(os.path.normpath(str(path)))

    # wiot start and end
    wiot_ext = ".xlsx"
    wiot_start = "wiot"

    # determine which wiod file to be parsed
    if not os.path.isdir(path):
        # 1. case - one file specified in path
        if os.path.isfile(path):
            wiot_file = path
        else:
            # just in case the ending was forgotten
            wiot_file = path + wiot_ext
    else:
        # 2. case: directory given-build wiot_file with the value given in year
        if not year:
            raise ParserError("No year specified (either specify a specific file or a path and year)")
        year_two_digit = str(year)[-2:]
        wiot_file_list = [
            fl
            for fl in os.listdir(path)
            if (fl[:6] == wiot_start + year_two_digit and os.path.splitext(fl)[1] == wiot_ext)
        ]
        if len(wiot_file_list) != 1:
            raise ParserError(
                "Multiple files for a given year or file not found (specify a specific file in paramters)"
            )

        wiot_file = os.path.join(path, wiot_file_list[0])

    wiot_file = wiot_file
    root_path = os.path.split(wiot_file)[0]
    if not os.path.exists(wiot_file):
        raise ParserError("WIOD file not found in the specified folder.")

    meta_rec = MRIOMetaData(location=root_path)

    # wiot file structure
    wiot_meta = {
        "col": 0,  # column of the meta information
        "year": 0,  # rest: rows with the data
        "iosystem": 2,
        "unit": 3,
        "end_row": 4,
    }
    wiot_header = {
        # the header indexes are the same for rows after removing the first
        # two lines (wiot_empty_top_rows)
        "code": 0,
        "sector_names": 1,
        "region": 2,
        "c_code": 3,
    }
    wiot_empty_top_rows = [0, 1]

    wiot_marks = {  # special marks
        "last_interindsec": "c35",  # last sector of the interindustry
        "tot_facinp": ["r60", "r69"],  # useless totals to remove from factinp
        "total_column": [-1],  # the total column in the whole data
    }

    wiot_sheet = 0  # assume the first one is the one with the data.

    # Wiod has an unfortunate file structure with overlapping metadata and
    # header. In order to deal with that first the full file is read.
    wiot_data = pd.read_excel(wiot_file, sheet_name=wiot_sheet, header=None)

    meta_rec._add_fileio(f"WIOD data parsed from {wiot_file}")
    # get meta data
    wiot_year = wiot_data.iloc[wiot_meta["year"], wiot_meta["col"]][-4:]
    wiot_iosystem = wiot_data.iloc[wiot_meta["iosystem"], wiot_meta["col"]].rstrip(")").lstrip("(")
    meta_rec.change_meta("system", wiot_iosystem)
    _wiot_unit = wiot_data.iloc[wiot_meta["unit"], wiot_meta["col"]].rstrip(")").lstrip("(")

    # remove meta data, empty rows, total column
    wiot_data.iloc[0 : wiot_meta["end_row"], wiot_meta["col"]] = np.nan
    wiot_data = wiot_data.drop(wiot_empty_top_rows, axis=0)
    wiot_data = wiot_data.drop(wiot_data.columns[wiot_marks["total_column"]], axis=1)
    # at this stage row and column header should have the same size but
    # the index starts now at two - replace/reset to row numbers
    wiot_data.index = range(wiot_data.shape[0])

    # Early years in WIOD tables have a different name for Romania:
    # 'ROM' which should be 'ROU'. The latter is also consistent with
    # the environmental extensions names.
    wiot_data.iloc[wiot_header["region"], :] = wiot_data.iloc[wiot_header["region"], :].str.replace(
        "ROM", "ROU", regex=False
    )
    wiot_data.iloc[:, wiot_header["region"]] = wiot_data.iloc[:, wiot_header["region"]].str.replace(
        "ROM", "ROU", regex=False
    )

    # get the end of the interindustry matrix
    _lastZcol = wiot_data[wiot_data.iloc[:, wiot_header["c_code"]] == wiot_marks["last_interindsec"]].index[-1]
    _lastZrow = wiot_data[wiot_data[wiot_header["c_code"]] == wiot_marks["last_interindsec"]].index[-1]

    if _lastZcol != _lastZrow:
        raise ParserError("Interindustry matrix not symetric in the WIOD source file")
    Zshape = (_lastZrow, _lastZcol)

    # separate factor input extension and remove
    # totals in the first and last row
    facinp = wiot_data.iloc[Zshape[0] + 1 :, :]
    facinp = facinp.drop(
        facinp[facinp[wiot_header["c_code"]].isin(wiot_marks["tot_facinp"])].index,
        axis=0,
    )

    Z = wiot_data.iloc[: Zshape[0] + 1, : Zshape[1] + 1].copy()
    Y = wiot_data.iloc[: Zshape[0] + 1, Zshape[1] + 1 :].copy()
    F_fac = facinp.iloc[:, : Zshape[1] + 1].copy()
    F_Y_fac = facinp.iloc[:, Zshape[1] + 1 :].copy()

    index_wiot_headers = list(wiot_header.values())
    # Save lookup of sectors and codes - to be used at the end of the parser
    # Assuming USA is present in every WIOT year
    wiot_sector_lookup = (
        wiot_data[wiot_data[wiot_header["region"]] == "USA"].iloc[:, 0 : max(index_wiot_headers) + 1]
    ).astype("str")

    wiot_sector_lookup.columns = [entry[1] for entry in sorted(zip(wiot_header.values(), wiot_header.keys()))]
    wiot_sector_lookup = wiot_sector_lookup.set_index("code", drop=False)
    _Y = Y.T.iloc[
        :,
        [
            wiot_header["code"],  # Included to be consistent with  wiot_header
            wiot_header["sector_names"],
            wiot_header["region"],
            wiot_header["c_code"],
        ],
    ]
    wiot_fd_lookup = _Y[_Y.iloc[:, wiot_header["region"]] == "USA"].astype("str")
    wiot_fd_lookup.columns = [entry[1] for entry in sorted(zip(wiot_header.values(), wiot_header.keys()))]
    wiot_fd_lookup = wiot_fd_lookup.set_index("c_code", drop=False)
    wiot_fd_lookup.index.name = "code"

    # set the index/columns, work with code b/c these are also used in the
    # extensions
    Z[wiot_header["code"]] = Z[wiot_header["code"]].astype(str)
    Z = Z.set_index([wiot_header["region"], wiot_header["code"]], drop=False)
    Z = Z.iloc[max(index_wiot_headers) + 1 :, max(index_wiot_headers) + 1 :]
    Z.index.names = IDX_NAMES["Z_col"]
    Z.columns = Z.index

    indexY_col_head = Y.iloc[[wiot_header["region"], wiot_header["c_code"]], :]
    Y.columns = pd.MultiIndex.from_arrays(indexY_col_head.values, names=IDX_NAMES["Y_col2"])
    Y = Y.iloc[max(index_wiot_headers) + 1 :, :]
    Y.index = Z.index

    F_fac = F_fac.set_index([wiot_header["sector_names"]], drop=False)  # c_code missing, use names
    F_fac.index.names = ["inputtype"]
    F_fac = F_fac.iloc[:, max(index_wiot_headers) + 1 :]
    F_fac.columns = Z.columns
    F_Y_fac.columns = Y.columns
    F_Y_fac.index = F_fac.index

    # convert from object to float (was object because mixed float,str)
    Z = Z.astype("float")
    Y = Y.astype("float")
    F_fac = F_fac.astype("float")
    F_Y_fac = F_Y_fac.astype("float")

    # save the units
    Z_unit = pd.DataFrame(Z.iloc[:, 0])
    Z_unit.columns = ["unit"]
    Z_unit["unit"] = _wiot_unit

    F_fac_unit = pd.DataFrame(F_fac.iloc[:, 0])
    F_fac_unit.columns = ["unit"]
    F_fac_unit["unit"] = _wiot_unit

    ll_countries = list(Z.index.get_level_values("region").unique())

    # Finalize the factor inputs extension
    ext = {}

    ext["factor_inputs"] = {
        "F": F_fac,
        "F_Y": F_Y_fac,
        "year": wiot_year,
        "iosystem": wiot_iosystem,
        "unit": F_fac_unit,
        "name": "factor input",
    }

    # SEA extension
    _F_sea_data, _F_sea_unit = __get_WIOD_SEA_extension(root_path=root_path, year=wiot_year)
    if _F_sea_data is not None:
        # None if no SEA file present
        _F_Y_sea = pd.DataFrame(index=_F_sea_data.index, columns=F_Y_fac.columns, data=0)
        _F_Y_sea = _F_Y_sea.astype("float")

        ext["SEA"] = {
            "F": _F_sea_data,
            "F_Y": _F_Y_sea,
            "year": wiot_year,
            "iosystem": wiot_iosystem,
            "unit": _F_sea_unit,
            "name": "SEA",
        }
        meta_rec._add_fileio(f"SEA file extension parsed from {root_path}")

    # Environmental extensions, names follow the name given
    # in the meta sheet (except for CO2 to get a better description).
    # Units are hardcoded if no consistent place to read them
    # within the files (for all extensions in upper case).
    # The units names must exactly match!
    # Start must identify exactly one folder or a zip file to
    # read the extension.
    # Within the folder, the routine looks for xls files
    # starting with the country code.
    dl_envext_para = {
        "AIR": {
            "name": "Air Emission Accounts",
            "start": "AIR_",
            "ext": ".xls",
            "unit": {
                "CO2": "Gg",
                "CH4": "t",
                "N2O": "t",
                "NOx": "t",
                "SOx": "t",
                "CO": "t",
                "NMVOC": "t",
                "NH3": "t",
            },
        },
        "CO2": {
            "name": "CO2 emissions - per source",
            "start": "CO2_",
            "ext": ".xls",
            "unit": {"all": "Gg"},
        },
        "EM": {
            "name": "Emission relevant energy use",
            "start": "EM_",
            "ext": ".xls",
            "unit": {"all": "TJ"},
        },
        "EU": {
            "name": "Gross energy use",
            "start": "EU_",
            "ext": ".xls",
            "unit": {"all": "TJ"},
        },
        "lan": {
            "name": "land use",
            "start": "lan_",
            "ext": ".xls",
            "unit": {"all": None},
        },
        "mat": {
            "name": "material use",
            "start": "mat_",
            "ext": ".xls",
            "unit": {"all": None},
        },
        "wat": {
            "name": "water use",
            "start": "wat_",
            "ext": ".xls",
            "unit": {"all": None},
        },
    }

    _F_Y_template = pd.DataFrame(columns=F_Y_fac.columns)
    _ss_F_Y_pressure_column = "c37"
    for ik_ext in dl_envext_para:
        _dl_ex = __get_WIOD_env_extension(
            root_path=root_path,
            year=wiot_year,
            ll_co=ll_countries,
            para=dl_envext_para[ik_ext],
        )
        if _dl_ex is not None:
            # None if extension not available
            _F_Y = _dl_ex["F_Y"]

            _F_Y.columns = pd.MultiIndex.from_product([_F_Y.columns, [_ss_F_Y_pressure_column]])
            _F_Y = pd.concat([_F_Y_template.astype("float"), _F_Y]).astype("float")
            _F_Y = _F_Y.fillna(0)
            _F_Y.index.names = _dl_ex["F"].index.names
            _F_Y.columns.names = _F_Y_template.columns.names
            _F_Y = _F_Y[ll_countries]
            _F_Y = _F_Y.astype("float")

            ext[ik_ext] = {
                "F": _dl_ex["F"],
                "F_Y": _F_Y,
                "year": wiot_year,
                "iosystem": wiot_iosystem,
                "unit": _dl_ex["unit"],
                "name": dl_envext_para[ik_ext]["name"],
            }
            meta_rec._add_fileio(f"Extension {ik_ext} parsed from {root_path}")

    # Build system
    wiod = IOSystem(Z=Z, Y=Y, unit=Z_unit, meta=meta_rec, **ext)

    # Replace sector/final demand category names
    if type(names) is str:
        names = (names, names)
    ll_names = [w[0].lower() for w in names]

    if ll_names[0] == "c":
        dd_sec_rename = wiot_sector_lookup.c_code.to_dict()
    elif ll_names[0] == "i":
        dd_sec_rename = wiot_sector_lookup.code.to_dict()
    elif ll_names[0] == "f":
        dd_sec_rename = wiot_sector_lookup.sector_names.to_dict()
    else:
        dd_sec_rename = wiot_sector_lookup.code.to_dict()
        warnings.warn(
            "Parameter for names not understood - used ISIC codes as sector names",
            stacklevel=2,
        )

    if ll_names[1] == "c" or ll_names[1] == "i":
        dd_fd_rename = wiot_fd_lookup.c_code.to_dict()
    elif ll_names[1] == "f":
        dd_fd_rename = wiot_fd_lookup.sector_names.to_dict()
    else:
        warnings.warn(
            "Parameter for names not understood - used c_codes as final demand category names",
            stacklevel=2,
        )

    wiod.Z = wiod.Z.rename(columns=dd_sec_rename, index=dd_sec_rename)
    wiod.Y = wiod.Y.rename(columns=dd_fd_rename, index=dd_sec_rename)
    for ext in wiod.get_extensions(data=True):
        ext.F = ext.F.rename(columns=dd_sec_rename)
        ext.F_Y = ext.F_Y.rename(columns=dd_fd_rename)

    return wiod


def __get_WIOD_env_extension(root_path, year, ll_co, para):
    """Parse the wiod environmental extension.

    Extension can either be given as original .zip files or as extracted
    data in a folder with the same name as the corresponding zip file (with-
    out the extension).

    This function is based on the structure of the extensions from _may12.

    Note
    ----
    The function deletes 'secQ' which is not present in the economic tables.

    Parameters
    ----------
    root_path : string
        Path to the WIOD data or the path with the
        extension data folder or zip file.
    year : str or int
        Year to return for the extension = valid sheetname for the xls file.
    ll_co : list like
        List of countries in WIOD - used for finding and matching
        extension data in the given folder.
    para : dict
        Defining the parameters for reading the extension.

    Returns
    -------
    dict with keys
        F : pd.DataFrame with index 'stressor' and columns 'region', 'sector'
        F_Y : pd.Dataframe with index 'stressor' and column 'region'
            This data is for household stressors - must be applied to the right
            final demand column afterwards.
        unit : pd.DataFrame with index 'stressor' and column 'unit'


    """
    ll_root_content = [ff for ff in os.listdir(root_path) if ff.startswith(para["start"])]
    if len(ll_root_content) < 1:
        warnings.warn(
            "Extension data for {} not found - Extension not included".format(para["start"]),
            ParserWarning,
            stacklevel=2,
        )
        return None

    if len(ll_root_content) > 1:
        raise ParserError("Several raw data for extension{} available - clean extension folder.".format(para["start"]))

    pf_env = os.path.join(root_path, ll_root_content[0])

    if pf_env.endswith(".zip"):
        rf_zip = zipfile.ZipFile(pf_env)
        ll_env_content = [ff for ff in rf_zip.namelist() if ff.endswith(para["ext"])]
    else:
        ll_env_content = [ff for ff in os.listdir(pf_env) if ff.endswith(para["ext"])]

    dl_env = {}
    dl_env_hh = {}
    for co in ll_co:
        ll_pff_read = [
            ff
            for ff in ll_env_content
            if ff.endswith(para["ext"]) and (ff.startswith(co.upper()) or ff.startswith(co.lower()))
        ]

        if len(ll_pff_read) < 1:
            raise ParserError("Country data not complete for Extension {} - missing {}.".format(para["start"], co))

        if len(ll_pff_read) > 1:
            raise ParserError("Multiple country data for Extension {} - country {}.".format(para["start"], co))

        pff_read = ll_pff_read[0]

        if pf_env.endswith(".zip"):
            ff_excel = pd.ExcelFile(rf_zip.open(pff_read))
        else:
            ff_excel = pd.ExcelFile(os.path.join(pf_env, pff_read))
        if str(year) in ff_excel.sheet_names:
            df_env = ff_excel.parse(sheet_name=str(year), index_col=None, header=0)
        else:
            warnings.warn(
                "Extension {} does not includedata for the year {} - Extension not included".format(
                    para["start"], year
                ),
                ParserWarning,
                stacklevel=2,
            )
            return None

        if not pd.api.types.is_numeric_dtype(df_env.index):
            # upper case letter extensions gets parsed with multiindex, not
            # quite sure why...
            df_env = df_env.reset_index()

        # unit can be taken from the first cell in the excel sheet
        if df_env.columns[0] != "level_0":
            para["unit"]["all"] = df_env.columns[0]

        # two clean up cases - can be identified by lower/upper case extension
        # description
        if para["start"].islower():
            pass
        elif para["start"].isupper():
            df_env = df_env.iloc[:, 1:]
        else:
            raise ParserError("Format of extension not given.")

        df_env = df_env.dropna(axis=0, how="all")
        df_env = df_env[df_env.iloc[:, 0] != "total"]
        df_env = df_env[df_env.iloc[:, 0] != "secTOT"]
        df_env = df_env[df_env.iloc[:, 0] != "secQ"]
        df_env.iloc[:, 0] = df_env.iloc[:, 0].astype(str).replace(to_replace="sec", value="", regex=True)
        df_env = df_env.set_index([df_env.columns[0]])
        df_env.index.names = ["sector"]
        df_env = df_env.T

        ikc_hh = "FC_HH"
        dl_env_hh[co] = df_env[ikc_hh]
        del df_env[ikc_hh]
        dl_env[co] = df_env

    df_F = pd.concat(dl_env, axis=1)[ll_co]
    df_F_Y = pd.concat(dl_env_hh, axis=1)[ll_co]
    df_F = df_F.fillna(0)
    df_F_Y = df_F_Y.fillna(0)

    df_F.columns.names = IDX_NAMES["F_col"]
    df_F.index.names = IDX_NAMES["F_row_single"]

    df_F_Y.columns.names = IDX_NAMES["Y_col1"]
    df_F_Y.index.names = IDX_NAMES["F_row_single"]

    # build the unit df
    df_unit = pd.DataFrame(index=df_F.index, columns=["unit"])
    _ss_unit = para["unit"].get("all", "undef")
    for ikr in df_unit.index:
        df_unit.loc[ikr, "unit"] = para["unit"].get(ikr, _ss_unit)

    df_unit.columns.names = ["unit"]
    df_unit.index.names = ["stressor"]

    if pf_env.endswith(".zip"):
        rf_zip.close()

    return {"F": df_F, "F_Y": df_F_Y, "unit": df_unit}


def __get_WIOD_SEA_extension(root_path, year, data_sheet="DATA"):
    """Get the extension data from the SEA file in WIOD.

    This function is based on the structure in the WIOD_SEA_July14 file.
    Missing values are set to zero.

    The function works if the SEA file is either in path or in a subfolder
    named 'SEA'.

    Parameters
    ----------
    root_path : string
        Path to the WIOD data or the path with the SEA data.
    year : str or int
        Year to return for the extension
    sea_data_sheet : string, optional
        Worksheet with the SEA data in the excel file

    Returns
    -------
    SEA data as extension for the WIOD MRIO
    """
    sea_ext = ".xlsx"
    sea_start = "WIOD_SEA"

    _SEA_folder = os.path.join(root_path, "SEA")
    if not os.path.exists(_SEA_folder):
        _SEA_folder = root_path

    sea_folder_content = [
        ff for ff in os.listdir(_SEA_folder) if os.path.splitext(ff)[-1] == sea_ext and ff[:8] == sea_start
    ]

    if sea_folder_content:
        # read data
        sea_file = os.path.join(_SEA_folder, sorted(sea_folder_content)[0])

        df_sea = pd.read_excel(sea_file, sheet_name=data_sheet, header=0, index_col=[0, 1, 2, 3])

        # fix years
        ic_sea = df_sea.columns.tolist()
        ic_sea = [yystr.lstrip("_") for yystr in ic_sea]
        df_sea.columns = ic_sea

        try:
            ds_sea = df_sea[str(year)]
        except KeyError:
            warnings.warn(
                f"SEA extension does not include data for the year {year} - SEA-Extension not included",
                ParserWarning,
                stacklevel=2,
            )
            return None, None

        # get useful data (employment)
        mt_sea = ["EMP", "EMPE", "H_EMP", "H_EMPE"]
        ds_use_sea = pd.concat([ds_sea.xs(key=vari, level="Variable", drop_level=False) for vari in mt_sea])
        ds_use_sea = ds_use_sea.drop(labels="TOT", level="Code")
        ds_use_sea = ds_use_sea.reset_index("Description", drop=True)

        # RoW not included in SEA but needed to get it consistent for
        # all countries. Just add a dummy with 0 for all accounts.
        if "RoW" not in ds_use_sea.index.get_level_values("Country"):
            ds_RoW = ds_use_sea.xs("USA", level="Country", drop_level=False)
            ds_RoW.loc[:] = 0
            df_RoW = ds_RoW.reset_index()
            df_RoW["Country"] = "RoW"
            ds_use_sea = pd.concat([ds_use_sea.reset_index(), df_RoW]).set_index(["Country", "Code", "Variable"])

        ds_use_sea = ds_use_sea.fillna(value=0)
        df_use_sea = ds_use_sea.unstack(level=["Country", "Code"])[str(year)]
        df_use_sea.index.names = IDX_NAMES["VA_row_single"]
        df_use_sea.columns.names = IDX_NAMES["F_col"]
        df_use_sea = df_use_sea.astype("float")

        df_unit = pd.DataFrame(
            data=[  # this data must be in the same order as mt_sea
                "thousand persons",
                "thousand persons",
                "mill hours",
                "mill hours",
            ],
            columns=["unit"],
            index=df_use_sea.index,
        )

        return df_use_sea, df_unit
    warnings.warn(
        "SEA extension raw data file not found - SEA-Extension not included",
        ParserWarning,
        stacklevel=2,
    )
    return None, None


def parse_oecd(path, year=None):
    """Parse the OECD ICIO tables.

    This function works for both, the 2016 and 2018 release.
    The OECd webpage provides the data as csv files in zip compressed
    archives. This function works with both, the compressed archives
    and the unpacked csv files.

    Note
    ----
    I) The original OECD ICIO tables provide some disaggregation of the Mexican
    and Chinese tables for the interindustry flows. The pymrio parser
    automatically aggregates these into Chinese And Mexican totals. Thus, the
    MX1, MX2, ..  and CN1, CN2, ... entries are aggregated into MEX and CHN.

    II) If a given storage folder contains both releases, the datafile
    must be specified in the 'path' parameter.

    Parameters
    ----------
    path: str or pathlib.Path
        Either the full path to one specific OECD ICIO file
        or the path to a storage folder with several OECD files.
        In the later case, a specific year needs to be specified.

    year: str or int, optional
        Year to parse if 'path' is given as a folder.
        If path points to a specific file, this parameter is not used.

    Returns
    -------
    IOSystem

    Raises
    ------
    ParserError
        If the file to parse could not be definitely identified.
    FileNotFoundError
        If the specified data file could not be found.

    """
    path = os.path.abspath(os.path.normpath(str(path)))

    oecd_file_starts = ["ICIO2016_", "ICIO2018_", "ICIO2021_", "ICIO2023_"]

    # determine which oecd file to be parsed
    if not os.path.isdir(path):
        # 1. case - one file specified in path
        oecd_file = path
        path = os.path.split(oecd_file)[0]
    else:
        # 2. case: dir given - build oecd_file with the value given in year
        if not year:
            raise ParserError("No year specified (either specify a specific file or path and year)")

        oecd_file_list = [
            fl
            for fl in os.listdir(path)
            if (
                os.path.splitext(fl)[1] in [".csv", ".CSV", ".zip"]
                and os.path.splitext(fl)[0] in [oo + str(year) for oo in oecd_file_starts]
            )
        ]

        if len(oecd_file_list) > 1:
            unique_file_data = {os.path.splitext(fl)[0] for fl in oecd_file_list}

            if len(unique_file_data) > 1:
                raise ParserError(
                    'Multiple files for a given year found (specify a specific file in the parameter "path")'
                )

        elif len(oecd_file_list) == 0:
            raise FileNotFoundError("No data file for the given year found")

        oecd_file = os.path.join(path, oecd_file_list[0])

    oecd_file_name = os.path.split(oecd_file)[1]

    try:
        years = re.findall(r"\d\d\d\d", oecd_file_name)
        oecd_version = "v" + years[0]
        oecd_year = years[1]
        meta_desc = f"OECD ICIO for {oecd_year}"

    except IndexError:
        oecd_version = "n/a"
        oecd_year = "n/a"
        meta_desc = "OECD ICIO - year undefined"

    meta_rec = MRIOMetaData(
        location=path,
        name="OECD-ICIO",
        description=meta_desc,
        version=oecd_version,
        system="IxI",  # base don the readme
    )

    oecd_raw = pd.read_csv(oecd_file, sep=",", index_col=0).fillna(0)
    meta_rec._add_fileio(f"OECD data parsed from {oecd_file}")

    mon_unit = "Million USD"

    oecd_totals_col = ["OUT", "TOTAL"]
    oecd_totals_row = ["OUT", "OUTPUT"]

    oecd_raw = oecd_raw.drop(oecd_totals_col, axis=1, errors="ignore")
    oecd_raw = oecd_raw.drop(oecd_totals_row, axis=0, errors="ignore")

    # Important - these must not match any country or industry name
    factor_input_exact = oecd_raw.filter(items=["TLS", "VA"], axis=0)
    factor_input_regex = oecd_raw.filter(regex="VALU|TAX", axis=0)
    factor_input = pd.concat([factor_input_exact, factor_input_regex], axis=0)
    final_demand = oecd_raw.filter(regex="HFCE|NPISH|NPS|GGFC|GFCF|INVNT|INV|DIRP|DPABR|FD|P33|DISC|OUT", axis=1)

    Z = oecd_raw.loc[
        oecd_raw.index.difference(factor_input.index),
        oecd_raw.columns.difference(final_demand.columns),
    ].astype("float")
    F_factor_input = factor_input.loc[:, factor_input.columns.difference(final_demand.columns)].astype("float")
    F_Y_factor_input = factor_input.loc[:, final_demand.columns].astype("float")
    Y = final_demand.loc[final_demand.index.difference(F_factor_input.index), :].astype("float")

    Z_index = pd.MultiIndex.from_tuples(tuple(ll) for ll in Z.index.map(lambda x: x.split("_", maxsplit=1)))
    Z_columns = Z_index.copy()
    Z_index.names = IDX_NAMES["Z_row"]
    Z_columns.names = IDX_NAMES["Z_col"]
    Z.index = Z_index
    Z.columns = Z_columns

    _midx = []
    for orig_idx in Y.columns:
        entries = orig_idx.split("_")
        if len(entries) == 1:
            # Capturing the discrepancy column
            entries = ["ALL", entries[0]]
        if entries[1] in Z.index.get_level_values("region").unique():
            # Fixing the reversed indexing in the 2016 ICIO version
            entries = [entries[1], entries[0]]
        _midx.append(tuple(entries))
    Y.columns = pd.MultiIndex.from_tuples(_midx)
    Y.columns.names = IDX_NAMES["Y_col2"]
    Y.index = Z.index

    F_factor_input.columns = Z.columns
    F_factor_input.index.names = IDX_NAMES["VA_row_single"]
    F_Y_factor_input.columns = Y.columns
    F_Y_factor_input.index = F_factor_input.index

    # Aggregation of CN and MX subregions
    core_co_names = Z.columns.get_level_values("region").unique()

    agg_corr = {
        "CHN": [a for a in core_co_names if re.match(r"CN\d", a)],
        "MEX": [a for a in core_co_names if re.match(r"MX\d", a)],
    }

    for co_name, agg_list in agg_corr.items():
        if (co_name not in core_co_names) or (len(agg_list) == 0):
            continue

        # DEBUG note for all below: have to assign with np values due to
        # alignment issues bug in pandas,
        # see https://github.com/pandas-dev/pandas/issues/10440

        # aggregate rows
        Z.loc[co_name, :] = (Z.loc[co_name, :] + Z.loc[agg_list, :].groupby(level="sector").sum()).to_numpy()
        Z = Z.drop(agg_list, axis=0)
        Y.loc[co_name, :] = (Y.loc[co_name, :] + Y.loc[agg_list, :].groupby(level="sector").sum()).to_numpy()
        Y = Y.drop(agg_list, axis=0)

        # aggregate columns
        Z.loc[:, co_name] = (Z.loc[:, co_name] + Z.loc[:, agg_list].T.groupby(level="sector").sum().T).to_numpy()
        Z = Z.drop(agg_list, axis=1)

        F_factor_input.loc[:, co_name] = (
            F_factor_input.loc[:, co_name] + F_factor_input.loc[:, agg_list].T.groupby(level="sector").sum().T
        ).to_numpy()
        F_factor_input = F_factor_input.drop(agg_list, axis=1)

    # unit df generation at the end to have consistent index
    unit = pd.DataFrame(index=Z.index, data=mon_unit, columns=IDX_NAMES["unit"])
    F_unit = pd.DataFrame(index=F_factor_input.index, data=mon_unit, columns=IDX_NAMES["unit"])

    oecd = IOSystem(
        Z=Z,
        Y=Y,
        unit=unit,
        meta=meta_rec,
        factor_inputs={
            "name": "factor_inputs",
            "unit": F_unit,
            "F": F_factor_input,
            "F_Y": F_Y_factor_input,
        },
    )

    return oecd


def parse_eora26(path, year=None, price="bp", country_names="eora"):
    """Parse the Eora26 database.

    Note
    ----
    This parser deletes the statistical discrepancy columns from
    the parsed Eora system (reports the amount of loss in the
    meta records).

    Eora does not provide any information on the unit of the
    monetary values. Based on personal communication the unit
    is set to Mill USD manually.


    Parameters
    ----------
    path : string or pathlib.Path
       Path to the Eora raw storage folder or a specific eora zip file to
       parse.  There are several options to specify the data for parsing:

       1) Pass the name of Eora zip file. In this case the parameters 'year'
          and 'price' will not be used
       2) Pass a folder which either contains Eora zip files or unpacked Eora
          data. In that case, a year must be given
       3) Pass a folder which contains subfolders in the format 'YYYY', e.g.
          '1998' This subfolder can either contain an Eora zip file or an
          unpacked Eora system

    year : int or str
        4 digit year spec. This will not be used if a zip file
        is specified in 'path'

    price : str, optional
        'bp' or 'pp'

    country_names: str, optional
        Which country names to use:
        'eora' = Eora flavoured ISO 3 varian
        'full' = Full country names as provided by Eora
        Passing the first letter suffice.


    """
    path = os.path.abspath(os.path.normpath(str(path)))

    if country_names[0].lower() == "e":
        country_names = "eora"
    elif country_names[0].lower() == "f":
        country_names = "full"
    else:
        raise ParserError("Parameter country_names must be Eora or full")

    row_name = "ROW"
    eora_zip_ext = ".zip"
    is_zip = False

    # determine which eora file to be parsed
    if os.path.splitext(path)[1] == eora_zip_ext:
        # case direct pass of eora zipfile
        year = re.search(r"\d\d\d\d", os.path.basename(path)).group(0)
        price = re.search(r"bp|pp", os.path.basename(path)).group(0)
        eora_loc = path
        root_path = os.path.split(path)[0]
        is_zip = True
    else:
        root_path = path
        if str(year) in os.listdir(path):
            path = os.path.join(path, str(year))

        eora_file_list = [
            fl
            for fl in os.listdir(path)
            if os.path.splitext(fl)[1] == eora_zip_ext and str(year) in fl and str(price) in fl
        ]

        if len(eora_file_list) > 1:
            raise ParserError("Multiple files for a given year found (specify a specific file in parameters)")
        if len(eora_file_list) == 1:
            eora_loc = os.path.join(path, eora_file_list[0])
            is_zip = True
        else:
            # Just a path was given, no zip file found,
            # continue with only the path information - assumed an
            # unpacked zip file
            eora_loc = path
            is_zip = False

    meta_rec = MRIOMetaData(location=root_path)

    # Eora file specs
    eora_sep = "\t"
    ZY_col = namedtuple("ZY", "full eora system name")(0, 1, 2, 3)

    eora_files = {
        "Z": f"Eora26_{str(year)}_{price}_T.txt",
        "Q": f"Eora26_{str(year)}_{price}_Q.txt",
        "QY": f"Eora26_{str(year)}_{price}_QY.txt",
        "VA": f"Eora26_{str(year)}_{price}_VA.txt",
        "Y": f"Eora26_{str(year)}_{price}_FD.txt",
        "labels_Z": "labels_T.txt",
        "labels_Y": "labels_FD.txt",
        "labels_Q": "labels_Q.txt",
        "labels_VA": "labels_VA.txt",
    }

    header = namedtuple("header", "index columns index_names, column_names")

    eora_header_spec = {
        "Z": header(
            index="labels_Z",
            columns="labels_Z",
            index_names=IDX_NAMES["Z_row"],
            column_names=IDX_NAMES["Z_col"],
        ),
        "Q": header(
            index="labels_Q",
            columns="labels_Z",
            index_names=IDX_NAMES["F_row_src"],
            column_names=IDX_NAMES["F_col"],
        ),
        "QY": header(
            index="labels_Q",
            columns="labels_Y",
            index_names=IDX_NAMES["F_row_src"],
            column_names=IDX_NAMES["Y_col2"],
        ),
        "VA": header(
            index="labels_VA",
            columns="labels_Z",
            index_names=IDX_NAMES["VA_row_unit_cat"],
            column_names=IDX_NAMES["F_col"],
        ),
        "Y": header(
            index="labels_Z",
            columns="labels_Y",
            index_names=IDX_NAMES["Y_row"],
            column_names=IDX_NAMES["Y_col2"],
        ),
    }

    if is_zip:
        zip_file = zipfile.ZipFile(eora_loc)
        indices_file = None
        for _key, filename in eora_files.items():
            if filename not in zip_file.namelist() and filename.startswith("labels"):
                try:
                    indices_loc = os.path.join(path, "indices.zip")
                    indices_file = zipfile.ZipFile(indices_loc)
                except Exception as err:
                    raise ValueError(
                        f"{filename} is not available in the zip file and no indices.zip file is available "
                        f"in the directory provided"
                    ) from err

        eora_data = {
            key: (
                pd.read_csv(
                    zip_file.open(filename),
                    sep=eora_sep,
                    header=None,
                )
                if filename in zip_file.namelist()
                else pd.read_csv(
                    indices_file.open(filename),
                    sep=eora_sep,
                    header=None,
                )
            )
            for key, filename in eora_files.items()
        }
        zip_file.close()
    else:
        eora_data = {
            key: pd.read_csv(
                os.path.join(eora_loc, filename),
                sep=eora_sep,
                header=None,
            )
            for key, filename in eora_files.items()
        }
    meta_rec._add_fileio(f"Eora26 for {year}-{price} data parsed from {eora_loc}")

    eora_data["labels_Z"] = eora_data["labels_Z"].loc[:, [getattr(ZY_col, country_names), ZY_col.name]]
    eora_data["labels_Y"] = eora_data["labels_Y"].loc[:, [getattr(ZY_col, country_names), ZY_col.name]]
    eora_data["labels_VA"] = eora_data["labels_VA"].iloc[:, : len(eora_header_spec["VA"].column_names)]
    labQ = eora_data["labels_Q"].iloc[:, : len(eora_header_spec["Q"].column_names)]
    labQ.columns = IDX_NAMES["F_row_src"]
    Q_unit = pd.DataFrame(labQ["stressor"].str.extract(r"\((.*)\)", expand=False))
    Q_unit.columns = IDX_NAMES["unit"]

    labQ["stressor"] = labQ["stressor"].str.replace(r"\s\((.*)\)", "", regex=True)
    eora_data["labels_Q"] = labQ

    for key in eora_header_spec:
        eora_data[key].columns = (
            eora_data[eora_header_spec[key].columns].set_index(list(eora_data[eora_header_spec[key].columns])).index
        )
        eora_data[key].columns.names = eora_header_spec[key].column_names
        eora_data[key].index = (
            eora_data[eora_header_spec[key].index].set_index(list(eora_data[eora_header_spec[key].index])).index
        )
        eora_data[key].index.names = eora_header_spec[key].index_names

        try:
            meta_rec._add_modify(
                f"Remove Rest of the World ({row_name}) "
                f"row from {key} - "
                f"loosing {eora_data[key].loc[:, row_name].sum().to_numpy()[0]}"
            )
            eora_data[key] = eora_data[key].drop(row_name, axis=1)
        except KeyError:
            pass

        try:
            meta_rec._add_modify(
                f"Remove Rest of the World ({row_name}) column "
                f"from {key} - loosing "
                f"{eora_data[key].loc[row_name, :].sum().to_numpy()[0]}"
            )
            eora_data[key] = eora_data[key].drop(row_name, axis=0)
        except KeyError:
            pass

    Q_unit.index = eora_data["Q"].index

    meta_rec.note("Set Eora moneatry units to Mill USD manually")
    Z_unit = pd.DataFrame(
        data=["Mill USD"] * len(eora_data["Z"].index),
        index=eora_data["Z"].index,
        columns=["unit"],
    )
    VA_unit = pd.DataFrame(
        data=["Mill USD"] * len(eora_data["VA"].index),
        index=eora_data["VA"].index,
        columns=["unit"],
    )

    eora = IOSystem(
        Z=eora_data["Z"],
        Y=eora_data["Y"],
        unit=Z_unit,
        Q={"name": "Q", "unit": Q_unit, "F": eora_data["Q"], "F_Y": eora_data["QY"]},
        VA={
            "name": "VA",
            "F": eora_data["VA"],
            "unit": VA_unit,
        },
        meta=meta_rec,
    )

    return eora


def parse_gloria_sut(path, year, version=59, price="bp", country_names="gloria"):
    """Parse the GLORIA database in SUT format.

    Note
    ----
    Countries with null transaction matrix are removed to avoid singular matrices

    Parameters
    ----------
    path : string or pathlib.Path
       Path to the Gloria raw storage folder, which should contain 3
       files/folders for a given year (as downloaded by download_gloria in
       iodownloader) :
        - GLORIA_MRIOs_{version}_{year}.zip or extracted folder
        - GLORIA_SatelliteAccounts_0{version}_{year}.zip or extracted folder
        - GLORIA_ReadMe_{version}.xlsx

    year : int or str
        4 digit year spec.

    version :  int or str, option
        version of gloria to use

    price : str, optional
        'bp' or 'pp'

    country_names: str, optional
        Which country names to use:
        'gloria' = Gloria ISO 3
        'full' = Full country names as provided by Gloria
        Passing the first letter suffice.
    """
    if country_names[0].lower() == "g":
        country_names = "gloria"
        country_col = "Region_acronyms"
    elif country_names[0].lower() == "f":
        country_names = "full"
        country_col = "Region_names"
    else:
        raise ParserError("Parameter country_names must be gloria or full")

    path = os.path.abspath(os.path.normpath(str(path)))

    if price == "bp":
        extension = "Markup001(full)"
    elif price == "pp":
        extension = "Markup005(full)"
    else:
        raise ValueError("price should be bp or pp")

    if version == "59a":
        version = 59
        version_readme = "59a"
        warnings.warn(
            "Files in version 59a and 59 have the same name, make sure to not store both in the same folder",
            stacklevel=2,
        )
    else:
        version_readme = version

    gloria_mrio_files = {
        "T": f"_120secMother_AllCountries_002_T-Results_{str(year)}_0{str(version)}_{extension}.csv",
        "Y": f"_120secMother_AllCountries_002_Y-Results_{str(year)}_0{str(version)}_{extension}.csv",
        "VA": f"_120secMother_AllCountries_002_V-Results_{str(year)}_0{str(version)}_Markup001(full).csv",
    }

    gloria_satellite_files = {
        "Q": f"_120secMother_AllCountries_002_TQ-Results_{str(year)}_0{str(version)}_Markup001(full).csv",
        "QY": f"_120secMother_AllCountries_002_YQ-Results_{str(year)}_0{str(version)}_Markup001(full).csv",
    }

    header = namedtuple("header", "index columns index_names, column_names")

    gloria_header_spec = {
        "T": header(
            index="labels_T",
            columns="labels_T",
            index_names=IDX_NAMES["T_row"],
            column_names=IDX_NAMES["T_col"],
        ),
        "Q": header(
            index="labels_Q",
            columns="labels_T",
            index_names=IDX_NAMES["F_row_cat_unit"],
            column_names=IDX_NAMES["T_col"],
        ),
        "QY": header(
            index="labels_Q",
            columns="labels_Y",
            index_names=IDX_NAMES["F_row_cat_unit"],
            column_names=IDX_NAMES["Y_col2"],
        ),
        "VA": header(
            index="labels_VA",
            columns="labels_T",
            index_names=IDX_NAMES["VA_row_region"],
            column_names=IDX_NAMES["T_col"],
        ),
        "Y": header(
            index="labels_T",
            columns="labels_Y",
            index_names=IDX_NAMES["T_row"],
            column_names=IDX_NAMES["Y_col2"],
        ),
    }

    mrio_path = glob.glob(os.path.join(path, f"GLORIA_MRIOs_{str(version)}_{str(year)}*"))[0]
    gloria_zip_ext = ".zip"

    # First we load the monetary data
    if os.path.splitext(mrio_path)[1] == gloria_zip_ext:
        mrio_is_zip = True
        root_path = os.path.split(mrio_path)[0]
    else:
        root_path = mrio_path
        mrio_is_zip = False

    meta_rec = MRIOMetaData(location=root_path)
    gloria_data_sut = {}

    if mrio_is_zip:
        zip_file = zipfile.ZipFile(mrio_path)
        for key, filename in gloria_mrio_files.items():
            file = [fn for fn in zip_file.namelist() if fn.endswith(filename)][0]
            gloria_data_sut[key] = pd.read_csv(
                zip_file.open(file),
                header=None,
            )
        zip_file.close()
    else:
        for key, filename in gloria_mrio_files.items():
            gloria_data_sut[key] = pd.read_csv(glob.glob(os.path.join(mrio_path, "*" + filename))[0], header=None)

    # Then we load the satellite data
    satellite_path = glob.glob(os.path.join(path, f"GLORIA_SatelliteAccounts_0{str(version)}_{str(year)}*"))[0]
    if os.path.splitext(satellite_path)[1] == gloria_zip_ext:
        satellite_is_zip = True
    else:
        satellite_is_zip = False

    if satellite_is_zip:
        zip_file = zipfile.ZipFile(satellite_path)
        for key, filename in gloria_satellite_files.items():
            file = [fn for fn in zip_file.namelist() if fn.endswith(filename)][0]
            gloria_data_sut[key] = pd.read_csv(
                zip_file.open(file),
                header=None,
            )
        zip_file.close()
    else:
        for key, filename in gloria_satellite_files.items():
            gloria_data_sut[key] = pd.read_csv(glob.glob(os.path.join(satellite_path, "*" + filename))[0], header=None)

    # And finally the labels
    gloria_meta_path = glob.glob(os.path.join(path, f"GLORIA_ReadMe_0{str(version_readme)}.xlsx"))[0]
    regions = pd.read_excel(gloria_meta_path, sheet_name="Regions")[country_col]
    sectors = pd.read_excel(gloria_meta_path, sheet_name="Sectors")["Sector_names"]

    va_fd_sheet = pd.read_excel(gloria_meta_path, sheet_name="Value added and final demand")
    fd_cats = va_fd_sheet["Final_demand_names"].to_list()
    va_cats = va_fd_sheet["Value_added_names"].to_list()

    satellite_cats = pd.read_excel(gloria_meta_path, sheet_name="Satellites")

    system = ["Industry", "Product"]

    gloria_data_sut["labels_T"] = pd.DataFrame(itertools.product(regions, system, sectors))
    gloria_data_sut["labels_Y"] = pd.DataFrame(itertools.product(regions, fd_cats))
    gloria_data_sut["labels_VA"] = pd.DataFrame(itertools.product(regions, va_cats))
    gloria_data_sut["labels_Q"] = satellite_cats[["Sat_indicator", "Sat_head_indicator", "Sat_unit"]]

    for key in gloria_header_spec:
        gloria_data_sut[key].columns = (
            gloria_data_sut[gloria_header_spec[key].columns]
            .set_index(list(gloria_data_sut[gloria_header_spec[key].columns]))
            .index
        )
        gloria_data_sut[key].columns.names = gloria_header_spec[key].column_names
        gloria_data_sut[key].index = (
            gloria_data_sut[gloria_header_spec[key].index]
            .set_index(list(gloria_data_sut[gloria_header_spec[key].index]))
            .index
        )
        gloria_data_sut[key].index.names = gloria_header_spec[key].index_names

    # Remove empty countries (Such as DYE in 2022)
    row_sum = gloria_data_sut["T"].groupby("region").sum().sum(axis=1)
    column_sum = gloria_data_sut["T"].T.groupby("region").sum().sum(axis=1)
    empty_countries = row_sum[(row_sum == 0) & (column_sum == 0)].index.to_list()

    for key in gloria_data_sut:
        if "region" in gloria_data_sut[key].columns.names:
            meta_rec._add_modify(f"Remove empty countries ({empty_countries}) columns from {key}")
            gloria_data_sut[key] = gloria_data_sut[key].drop(empty_countries, axis=1, level=0)
        if "region" in gloria_data_sut[key].index.names:
            meta_rec._add_modify(f"Remove empty countries ({empty_countries}) row from {key}")
            gloria_data_sut[key] = gloria_data_sut[key].drop(empty_countries, axis=0, level=0)

    # Extract Supply and Use tables from the Transaction matrix
    gloria_data_sut["V"] = gloria_data_sut["T"].loc[
        gloria_data_sut["T"].index.get_level_values(1) == "Industry",
        gloria_data_sut["T"].columns.get_level_values(1) == "Product",
    ]
    gloria_data_sut["V"].columns = gloria_data_sut["V"].columns.droplevel(1)
    gloria_data_sut["V"].index = gloria_data_sut["V"].index.droplevel(1)

    gloria_data_sut["U"] = gloria_data_sut["T"].loc[
        gloria_data_sut["T"].index.get_level_values(1) == "Product",
        gloria_data_sut["T"].columns.get_level_values(1) == "Industry",
    ]
    gloria_data_sut["U"].columns = gloria_data_sut["U"].columns.droplevel(1)
    gloria_data_sut["U"].index = gloria_data_sut["U"].index.droplevel(1)

    # Remove 0s in value added, final demand and satellites
    gloria_data_sut["VA"] = gloria_data_sut["VA"].loc[
        :, gloria_data_sut["VA"].columns.get_level_values(1) == "Industry"
    ]
    gloria_data_sut["VA"].columns = gloria_data_sut["VA"].columns.droplevel(1)

    gloria_data_sut["Y"] = gloria_data_sut["Y"].loc[gloria_data_sut["Y"].index.get_level_values(1) == "Product", :]
    gloria_data_sut["Y"].index = gloria_data_sut["Y"].index.droplevel(1)

    gloria_data_sut["Q"] = gloria_data_sut["Q"].loc[:, gloria_data_sut["Q"].columns.get_level_values(1) == "Industry"]
    gloria_data_sut["Q"].columns = gloria_data_sut["Q"].columns.droplevel(1)

    return gloria_data_sut, meta_rec


def __construct_IO(data_sut, construct="B"):
    # Construct the IO matrices from the SUT matrices
    """Build input output matrices from SUT matrices.

    Note
    ----

    Parameters
    ----------
    data_sut : dict
        Dictionary containing the SUT matrices (pd.DataFrames)
        V: Supply matrix: industry x commodity
        U: Use matrix: commodity x industry
        Y: Final demand: commodity x final demand category
        Q: Satellite accounts: satellite account x industry
        QY: Final demand satellite account: satellite account x final demand category
        VA: Value added: value added category x industry

    construct: int, optional
        A: Commodity Technology, commodity by commodity
        B: Industry Technology, commodity by commodity
        C: Fixed Industry Sales Structure, industry by industry
        D: Fixed Commodity Sales Structure, industry by industry

    Equations and notations from Eurostat Manual of Supply, Use and
    Input-Output Tables p.349
    https://ec.europa.eu/eurostat/documents/3859598/5902113/KS-RA-07-013-EN.PDF/b0b3d71e-3930-4442-94be-70b36cea9b39
    """
    # Industry output
    g = data_sut["V"].sum(axis=1)
    g_inv = 1 / g
    g_inv[g_inv == np.inf] = 0

    # Commodity output
    q = data_sut["U"].sum(axis=1) + data_sut["Y"].sum(axis=1)
    q_inv = 1 / q
    q_inv[q_inv == np.inf] = 0

    if construct == "A":
        # Transformer matrix (called T in Eurostat)
        T = np.linalg.inv(data_sut["V"].T.values) @ np.diag(q)

        A = pd.DataFrame(
            data_sut["U"].to_numpy() @ T @ np.diag(q_inv),
            index=data_sut["U"].index,
            columns=data_sut["U"].index,
        )

        # Value added in commodity x value added category
        VA = pd.DataFrame(
            data_sut["VA"].to_numpy() @ T,
            index=data_sut["VA"].index,
            columns=data_sut["U"].index,
        )
        Q = pd.DataFrame(
            data_sut["Q"].to_numpy() @ T,
            index=data_sut["Q"].index,
            columns=data_sut["U"].index,
        )
        Y = data_sut["Y"]

    elif construct == "B":
        T = np.diag(g_inv) @ data_sut["V"].to_numpy()

        A = pd.DataFrame(
            data_sut["U"].to_numpy() @ T @ np.diag(q_inv),
            index=data_sut["U"].index,
            columns=data_sut["U"].index,
        )

        VA = pd.DataFrame(
            data_sut["VA"].to_numpy() @ T,
            index=data_sut["VA"].index,
            columns=data_sut["U"].index,
        )
        Q = pd.DataFrame(
            data_sut["Q"].to_numpy() @ T,
            index=data_sut["Q"].index,
            columns=data_sut["U"].index,
        )
        Y = data_sut["Y"]

    elif construct == "C":
        T = np.diag(g) @ np.linalg.inv(data_sut["V"].T.values)

        A = pd.DataFrame(
            T @ data_sut["U"].to_numpy() @ np.diag(q_inv),
            index=data_sut["U"].index,
            columns=data_sut["U"].index,
        )

        VA = data_sut["VA"]
        Q = data_sut["Q"]
        Y = pd.DataFrame(
            T @ data_sut["Y"].to_numpy(),
            index=data_sut["U"].columns,
            columns=data_sut["Y"].columns,
        )

    elif construct == "D":
        T = data_sut["V"].to_numpy() @ np.diag(q_inv)

        A = pd.DataFrame(
            T @ data_sut["U"].to_numpy() @ np.diag(q_inv),
            index=data_sut["U"].index,
            columns=data_sut["U"].index,
        )

        VA = data_sut["VA"]
        Q = data_sut["Q"]
        Y = pd.DataFrame(
            T @ data_sut["Y"].to_numpy(),
            index=data_sut["U"].columns,
            columns=data_sut["Y"].columns,
        )

    else:
        raise ParserError("Construct should be A, B, C or D")

    data_io = {}
    data_io["Y"] = Y
    data_io["Q"] = Q
    data_io["QY"] = data_sut["QY"]
    data_io["VA"] = VA
    data_io["A"] = A

    return data_io


def parse_gloria(path, year=2022, version=59, price="bp", country_names="gloria", construct="B"):
    """Parse the GLORIA database in IO format.

    Note
    ----
    Countries with null transaction matrix are removed to avoid singular matrices
    For GLORIA, all constructs are equivalent (Supply table is diagonal)

    Parameters
    ----------
    path : string or pathlib.Path
       Path to the Gloria raw storage folder, which should contain 3
       files/folders for a given year (as downloaded by download_gloria in
       iodownloader) :
        - GLORIA_MRIOs_{version}_{year}.zip or extracted folder
        - GLORIA_SatelliteAccounts_0{version}_{year}.zip or extracted folder
        - GLORIA_ReadMe_{version}.xlsx

    year : int or str
        4 digit year spec.

    version :  int or str, option
        version of gloria to use

    price : str, optional
        'bp' or 'pp'

    country_names: str, optional
        Which country names to use:
        'gloria' = Gloria ISO 3
        'full' = Full country names as provided by Gloria
        Passing the first letter suffice.
    """
    gloria_data_sut, meta_rec = parse_gloria_sut(path, year, version, price, country_names)

    # Construct the IO matrices from the SUT matrices, for GLORIA all
    # constructs are equivalent (the supply table only has diagonal values)
    gloria_data = __construct_IO(gloria_data_sut, construct=construct)

    A_unit = pd.DataFrame(
        data=["‘000 US$"] * len(gloria_data["A"].index),
        index=gloria_data["A"].index,
        columns=["unit"],
    )
    VA_unit = pd.DataFrame(
        data=["‘000 US$"] * len(gloria_data["VA"].index),
        index=gloria_data["VA"].index,
        columns=["unit"],
    )

    Q_unit = pd.DataFrame(gloria_data["Q"].index.get_level_values(2))
    gloria_data["Q"].index = gloria_data["Q"].index.droplevel(2)
    gloria_data["QY"].index = gloria_data["QY"].index.droplevel(2)
    Q_unit.columns = IDX_NAMES["unit"]
    Q_unit.index = gloria_data["Q"].index

    gloria = IOSystem(
        A=gloria_data["A"],
        Y=gloria_data["Y"],
        unit=A_unit,
        Q={
            "name": "Q",
            "unit": Q_unit,
            "F": gloria_data["Q"],
            "F_Y": gloria_data["QY"],
        },
        VA={
            "name": "VA",
            "F": gloria_data["VA"],
            "unit": VA_unit,
        },
        meta=meta_rec,
    )

    return gloria
