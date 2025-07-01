"""Generic classes for pymrio.

Classes and function here should not be used directly.
Use the API methods from the pymrio module instead.

"""

import collections
import copy
import json
import logging
import re
import string
import time
import typing
import warnings
from collections.abc import Iterator
from pathlib import Path
from typing import Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import pymrio.tools.ioutil as ioutil
from pymrio.core.constants import (
    DEFAULT_FILE_NAMES,
    GENERIC_NAMES,
    MISSING_AGG_ENTRY,
    STORAGE_FORMAT,
)
from pymrio.tools.iomath import (
    calc_A,
    calc_accounts,
    calc_B,
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
    recalc_M,
)
from pymrio.tools.iometadata import MRIOMetaData

# internal functions
# def _warn_deprecation(message):  # pragma: no cover
#     warnings.warn(message, DeprecationWarning, stacklevel=2)


# Exceptions
class ResetError(Exception):
    """Base class for errors while reseting the system."""

    pass


class AggregationError(Exception):
    """Base class for errors while reseting the system."""

    pass


class ResetWarning(UserWarning):
    """Base class for errors while reseting the system."""

    pass


# Abstract classes
class _BaseSystem:
    """Base class for IOSystem and Extension.

    Note:
    ----
    That's is only a base class - do not make an instance of this class.

    """

    # properties to be set in the implementation classes
    __basic__ = []
    __non_agg_attributes__ = []
    __coefficients__ = []
    name = "Abstract BaseSystem"

    def __str__(self, startstr="System with: "):
        parastr = ", ".join([attr for attr in self.__dict__ if self.__dict__[attr] is not None and "__" not in attr])
        return startstr + parastr

    def __eq__(self, other):
        """Only the dataframes are compared."""
        for key, item in self.__dict__.items():
            if type(item) is pd.DataFrame:
                if key not in other.__dict__:
                    break
                try:
                    pd.testing.assert_frame_equal(item, other.__dict__[key])
                except AssertionError:
                    break
        else:
            return True

        return False

    def reset_full(self, force=False, _meta=None):
        """Remove all accounts which can be recalculated based on Z, Y, F, F_Y.

        Parameters
        ----------
        force: boolean, optional
            If True, reset to flows although the system can not be
            recalculated. Default: False

        _meta: MRIOMetaData, optional
            Metadata handler for logging, optional. Internal

        """
        # Attributes to keep must be defined in the init: __basic__
        strwarn = None
        for df in self.__basic__:
            if df == "F_Y":
                # F_Y is optional and can be None
                continue
            if (getattr(self, df)) is None:
                if force:
                    strwarn = f"Reset system warning - Recalculation after reset not possible because {df} missing"
                    warnings.warn(strwarn, ResetWarning, stacklevel=2)

                else:
                    raise ResetError(
                        "To few tables to recalculate the "
                        f"system after reset ({df} missing) "
                        "- reset can be forced by passing "
                        "'force=True')"
                    )

        if _meta:
            _meta._add_modify("Reset system to Z and Y")
            if strwarn:
                _meta._add_modify(strwarn)

        [
            setattr(self, key, None)
            for key in self.get_DataFrame(data=False, with_unit=False, with_population=False)
            if key not in self.__basic__
        ]
        return self

    def reset_to_flows(self, force=False, _meta=None):
        """Keep only the absolute values.

        This removes all attributes which can not be aggregated and must be
        recalculated after the aggregation.

        Parameters
        ----------
        force: boolean, optional
            If True, reset to flows although the system can not be
            recalculated. Default: False

        _meta: MRIOMetaData, optional
            Metadata handler for logging, optional. Internal

        """
        # Development note: The attributes which should be removed are
        # defined in self.__non_agg_attributes__
        strwarn = None
        for df in self.__basic__:
            if df == "F_Y":
                # F_Y is optional and can be None
                continue
            if (getattr(self, df)) is None:
                if force:
                    strwarn = f"Reset system warning - Recalculation after reset not possible because {df} missing"
                    warnings.warn(strwarn, ResetWarning, stacklevel=2)

                else:
                    raise ResetError(
                        "To few tables to recalculate the "
                        f"system after reset ({df} missing) "
                        "- reset can be forced by passing "
                        "'force=True')"
                    )

        if _meta:
            _meta._add_modify("Reset to absolute flows")
            if strwarn:
                _meta._add_modify(strwarn)

        [setattr(self, key, None) for key in self.__non_agg_attributes__]
        return self

    def reset_to_coefficients(self):
        """Keep only the coefficient.

        This can be used to recalculate the IO tables for a new finald demand.

        Note:
        -----
        The system can not be reconstructed after this steps
        because all absolute data is removed. Save the Y data in case
        a reconstruction might be necessary.

        """
        # Development note: The coefficient attributes are
        # defined in self.__coefficients__
        [
            setattr(self, key, None)
            for key in self.get_DataFrame(data=False, with_unit=False, with_population=False)
            if key not in self.__coefficients__
        ]
        return self

    def copy(self, new_name=None):
        """Return a deep copy of the system.

        Parameters
        ----------
        new_name: str, optional
            Set a new meta name parameter.
            Default: <old_name>_copy
        """
        _tmp = copy.deepcopy(self)
        if not new_name:
            new_name = self.name + "_copy"
        if str(type(self)) == "<class 'pymrio.core.mriosystem.IOSystem'>":
            _tmp.meta.note(f"IOSystem copy {new_name} based on {self.meta.name}")
            _tmp.meta.change_meta("name", new_name, log=False)
        else:
            _tmp.name = new_name
        return _tmp

    def get_Y_categories(self, entries=None):
        """Return names of y cat. of the IOSystem as unique names in order.

        Parameters
        ----------
        entries : List, optional
            If given, retuns an list with None for all values not in entries.

        Returns
        -------
        Index
            List of categories, None if no attribute to determine
            list is available
        """
        possible_dataframes = ["Y", "F_Y"]

        for df in possible_dataframes:
            if (df in self.__dict__) and (getattr(self, df) is not None):
                try:
                    ind = getattr(self, df).columns.get_level_values("category").unique()
                except (AssertionError, KeyError):
                    ind = getattr(self, df).columns.get_level_values(1).unique()
                if entries:
                    if type(entries) is str:
                        entries = [entries]
                    ind = ind.tolist()
                    return [None if ee not in entries else ee for ee in ind]
                return ind
        else:  # pragma: no cover
            warnings.warn("No attributes available to get Y categories", stacklevel=2)
            return None

    def get_index(self, as_dict=False, grouping_pattern=None):
        """Return the index of the DataFrames in the system.

        Parameters
        ----------
        as_dict: boolean, optional
            If True, returns a 1:1 key-value matching for further processing
            prior to groupby functions. Otherwise (default) the index
            is returned as pandas index.

        grouping_pattern: dict, optional
            Dictionary with keys being regex patterns matching index and
            values the name for the grouping. If the index is a pandas
            multiindex, the keys must be tuples of length levels in the
            multiindex, with a valid regex expression at each position.
            Otherwise, the keys need to be strings.
            Only relevant if as_dict is True.

        """
        possible_dataframes = [
            "A",
            "L",
            "Z",
            "Y",
            "F",
            "F_Y",
            "M",
            "S",
            "D_cba",
            "D_pba",
            "D_imp",
            "D_exp",
            "D_cba_reg",
            "D_pba_reg",
            "D_imp_reg",
            "D_exp_reg",
            "D_cba_cap",
            "D_pba_cap",
            "D_imp_cap",
            "D_exp_cap",
        ]
        for df in possible_dataframes:
            if (df in self.__dict__) and (getattr(self, df) is not None):
                orig_idx = getattr(self, df).index
                break
        else:  # pragma: no cover
            warnings.warn("No attributes available to get index", stacklevel=2)
            return None

        if as_dict:
            dd = {k: k for k in orig_idx}
            if grouping_pattern:
                for pattern, new_group in grouping_pattern.items():
                    if type(pattern) is str:
                        dd.update({k: new_group for k in dd if re.match(pattern, k)})
                    else:
                        dd.update(
                            {k: new_group for k in dd if all(re.match(pat, k[nr]) for nr, pat in enumerate(pattern))}
                        )
            return dd

        return orig_idx

    def set_index(self, index):
        """Set the pd dataframe index of all dataframes in the system to index."""
        for df in self.get_DataFrame(data=True, with_population=False):
            df.index = index

    def get_regions(self, entries=None):
        """Return the names of regions in the IOSystem as unique names in order.

        Parameters
        ----------
        entries : List, optional
            If given, retuns an list with None for all values not in entries.

        Returns
        -------
        Index
            List of regions,
            None if now attribute to determine list is available

        """
        possible_dataframes = [
            "A",
            "L",
            "Z",
            "Y",
            "F",
            "F_Y",
            "M",
            "S",
            "D_cba",
            "D_pba",
            "D_imp",
            "D_exp",
            "D_cba_reg",
            "D_pba_reg",
            "D_imp_reg",
            "D_exp_reg",
            "D_cba_cap",
            "D_pba_cap",
            "D_imp_cap",
            "D_exp_cap",
        ]

        for df in possible_dataframes:
            if (df in self.__dict__) and (getattr(self, df) is not None):
                try:
                    ind = getattr(self, df).columns.get_level_values("region").unique()
                except (AssertionError, KeyError):
                    ind = getattr(self, df).columns.get_level_values(0).unique()
                if entries:
                    if type(entries) is str:
                        entries = [entries]
                    ind = ind.tolist()
                    return [None if ee not in entries else ee for ee in ind]
                return ind
        else:  # pragma: no cover
            warnings.warn("No attributes available to get regions", stacklevel=2)
            return None

    def get_sectors(self, entries=None):
        """Return names of sectors in the IOSystem as unique names in order.

        Parameters
        ----------
        entries : List, optional
            If given, retuns an list with None for all values not in entries.

        Returns
        -------
        Index
            List of sectors,
            None if no attribute to determine the list is available

        """
        possible_dataframes = [
            "A",
            "L",
            "Z",
            "F",
            "M",
            "S",
            "D_cba",
            "D_pba",
            "D_imp",
            "D_exp",
            "D_cba_reg",
            "D_pba_reg",
            "D_imp_reg",
            "D_exp_reg",
            "D_cba_cap",
            "D_pba_cap",
            "D_imp_cap",
            "D_exp_cap",
        ]
        for df in possible_dataframes:
            if (df in self.__dict__) and (getattr(self, df) is not None):
                try:
                    ind = getattr(self, df).columns.get_level_values("sector").unique()
                except (AssertionError, KeyError):
                    ind = getattr(self, df).columns.get_level_values(1).unique()
                if entries:
                    if type(entries) is str:
                        entries = [entries]
                    ind = ind.tolist()
                    return [None if ee not in entries else ee for ee in ind]
                return ind
        else:  # pragma: no cover
            warnings.warn("No attributes available to get sectors", stacklevel=2)
            return None

    def get_DataFrame(self, data=False, with_unit=True, with_population=True) -> Iterator[Union[pd.DataFrame, str]]:
        """Yield all panda.DataFrames or there names.

        Notes
        -----
        For IOSystem this does not include the DataFrames in the extensions.

        Parameters
        ----------
        data : boolean, optional
            If True, returns a generator which yields the DataFrames.
            If False, returns a generator which
            yields only the names of the DataFrames

        with_unit: boolean, optional
            If True, includes the 'unit' DataFrame
            If False, does not include the 'unit' DataFrame.
            The method than only yields the numerical data tables

        with_population: boolean, optional
            If True, includes the 'population' vector
            If False, does not include the 'population' vector.

        Returns
        -------
            DataFrames or string generator, depending on parameter data

        """
        for key in self.__dict__:
            if (key == "unit") and not with_unit:
                continue
            if (key == "population") and not with_population:
                continue
            if type(self.__dict__[key]) is pd.DataFrame:
                if data:
                    yield getattr(self, key)
                else:
                    yield key

    @property
    def regions(self):
        """Return the regions of the system as Index."""
        return self.get_regions()

    @property
    def sectors(self):
        """Return the sectors of the MRIO system."""
        return self.get_sectors()

    @property
    def Y_categories(self):
        """Return the Y categories of the MRIO system."""
        return self.get_Y_categories()

    @property
    def DataFrames(self):
        """Return the DataFrames of the system as generator."""
        return list(self.get_DataFrame(data=False, with_unit=True, with_population=True))

    @property
    def empty(self):
        """True, if all dataframes of the system are empty."""
        for df in self.get_DataFrame(data=True):
            if len(df) > 0:
                return False
        else:
            return True

    def save(self, path, table_format="txt", sep="\t", float_format="%.12g"):
        r"""Save the system to path.

        Parameters
        ----------
        path : pathlib.Path or string
            path for the saved data (will be created if necessary, data
            within will be overwritten).

        table_format : string
            Format to save the DataFrames:

                - 'pkl' : Binary pickle files,
                          alias: 'pickle'
                - 'parquet': Parquet format
                          alias: 'par'
                - 'txt' : Text files (default), alias: 'text', 'csv', 'tsv'


        sep : string, optional
            Field delimiter for the output file, only for txt files.
            Default: tab ('\t')

        float_format : string, optional
            Format for saving the DataFrames, only for txt files.
            default = '%.12g'
        """
        for format_key, format_extension in STORAGE_FORMAT.items():
            if table_format.lower() in format_extension:
                table_extension = table_format
                table_format = format_key
                break
        else:
            raise ValueError(
                f'Unknown table format "{table_format}" - '
                'must be "txt", "pkl", "parquet" or an alias as '
                "defined in STORAGE_FORMAT"
            )

        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        para_file_path = path / DEFAULT_FILE_NAMES["filepara"]
        file_para = {}
        file_para["files"] = {}

        if str(type(self)) == "<class 'pymrio.core.mriosystem.IOSystem'>":
            file_para["systemtype"] = GENERIC_NAMES["iosys"]
        elif str(type(self)) == "<class 'pymrio.core.mriosystem.Extension'>":
            file_para["systemtype"] = GENERIC_NAMES["ext"]
            file_para["name"] = self.name
        else:
            warnings.warn(f'Unknown system type {str(type(self))} - set to "undef"', stacklevel=2)
            file_para["systemtype"] = "undef"

        for df, df_name in zip(self.get_DataFrame(data=True), self.get_DataFrame()):
            if type(df.index) is pd.MultiIndex:
                nr_index_col = len(df.index.levels)
            else:
                nr_index_col = 1

            if type(df.columns) is pd.MultiIndex:
                nr_header = len(df.columns.levels)
            else:
                nr_header = 1

            save_file = df_name + "." + table_extension
            save_file_with_path = path / save_file
            logging.info(f"Save file {save_file_with_path}")
            if table_format == "txt":
                df.to_csv(save_file_with_path, sep=sep, float_format=float_format)
            elif table_format == "pickle":
                df.to_pickle(save_file_with_path)
            elif table_format == "parquet":
                df.to_parquet(save_file_with_path)
            else:
                raise ValueError("Unknow table format passed through")

            file_para["files"][df_name] = {}
            file_para["files"][df_name]["name"] = save_file
            file_para["files"][df_name]["nr_index_col"] = str(nr_index_col)
            file_para["files"][df_name]["nr_header"] = str(nr_header)

        with para_file_path.open(mode="w") as pf:
            json.dump(file_para, pf, indent=4)

        if file_para["systemtype"] == GENERIC_NAMES["iosys"]:
            if not self.meta:
                self.meta = MRIOMetaData(name=self.name, location=path)

            self.meta._add_fileio(f"Saved {self.name} to {path}")
            self.meta.save(location=path)

        return self

    def rename_regions(self, regions):
        """Set new names for the regions.

        Parameters
        ----------
        regions : list or dict
            In case of dict: {'old_name' :  'new_name'} with a
                entry for each old_name which should be renamed
            In case of list: List of new names in order and complete
                without repetition

        """
        if type(regions) is list:
            regions = dict(zip(self.get_regions(), regions))

        for iodf_name, iodf in zip(self.get_DataFrame(data=False), self.get_DataFrame(data=True)):
            self.__dict__[iodf_name] = iodf.rename(index=regions, columns=regions)

        try:
            for ext in self.get_extensions(data=True):
                for extdf_name, extdf in zip(ext.get_DataFrame(data=False), ext.get_DataFrame(data=True)):
                    ext.__dict__[extdf_name] = extdf.rename(index=regions, columns=regions)
        except Exception as _:
            pass

        self.meta._add_modify("Changed country names")
        return self

    def rename_sectors(self, sectors):
        """Set new names for the sectors.

        Parameters
        ----------
        sectors : list or dict
            In case of dict: {'old_name' :  'new_name'} with an
                entry for each old_name which should be renamed
            In case of list: List of new names in order and
                complete without repetition

        """
        if type(sectors) is list:
            sectors = dict(zip(self.get_sectors(), sectors))

        for iodf_name, iodf in zip(self.get_DataFrame(data=False), self.get_DataFrame(data=True)):
            self.__dict__[iodf_name] = iodf.rename(index=sectors, columns=sectors)

        try:
            for ext in self.get_extensions(data=True):
                for extdf_name, extdf in zip(ext.get_DataFrame(data=False), ext.get_DataFrame(data=True)):
                    ext.__dict__[extdf_name] = extdf.rename(index=sectors, columns=sectors)
        except Exception as _e:
            pass
        self.meta._add_modify("Changed sector names")
        return self

    def rename_Y_categories(self, Y_categories):
        """Set new names for the Y_categories.

        Parameters
        ----------
        Y_categories : list or dict
            In case of dict: {'old_name' :  'new_name'} with an
                entry for each old_name which should be renamed
            In case of list: List of new names in order and
                complete without repetition

        """
        if type(Y_categories) is list:
            Y_categories = dict(zip(self.get_Y_categories(), Y_categories))

        for iodf_name, iodf in zip(self.get_DataFrame(data=False), self.get_DataFrame(data=True)):
            self.__dict__[iodf_name] = iodf.rename(index=Y_categories, columns=Y_categories)

        try:
            for ext in self.get_extensions(data=True):
                for extdf_name, extdf in zip(ext.get_DataFrame(data=False), ext.get_DataFrame(data=True)):
                    ext.__dict__[extdf_name] = extdf.rename(index=Y_categories, columns=Y_categories)
        except Exception:
            pass

        self.meta._add_modify("Changed Y category names")
        return self

    def find(self, term):
        """Look for term in index, sectors, regions, Y_categories.

        Mostly useful for a quick check if entry is present.

        Internally that uses pd.str.contains as implemented
        in ioutil.index_contains

        For a multiindex, all levels of the multiindex are searched.

        Parameters
        ----------
        term : string
            String to search for

        Returns
        -------
        dict of (multi)index
            With keys 'index', 'region', 'sector', 'Y_category' and
            values the found index entries.
            Empty keys are ommited.
            The values can be used directly on one of the DataFrames with .loc
        """
        res_dict = {}
        try:
            index_find = ioutil.index_contains(self.get_index(as_dict=False), find_all=term)
            if len(index_find) > 0:
                res_dict["index"] = index_find
        except Exception:  # noqa: E722
            pass
        try:
            reg_find = ioutil.index_contains(self.get_regions(), find_all=term)
            if len(reg_find) > 0:
                res_dict["regions"] = reg_find
        except Exception:  # noqa: E722
            pass
        try:
            sector_find = ioutil.index_contains(self.get_sectors(), find_all=term)
            if len(sector_find) > 0:
                res_dict["sectors"] = sector_find
        except Exception:  # noqa: E722
            pass
        try:
            Y_find = ioutil.index_contains(self.get_Y_categories(), find_all=term)
            if len(Y_find) > 0:
                res_dict["Y_categories"] = Y_find
        except Exception:  # noqa: E722
            pass
        try:
            for ext in self.get_extensions(data=False, instance_names=True):
                ext_index_find = ioutil.index_contains(getattr(self, ext).get_index(as_dict=False), find_all=term)
                if len(ext_index_find) > 0:
                    res_dict[ext + "_index"] = ext_index_find
        except Exception:  # noqa: E722
            pass

        return res_dict

    def contains(self, find_all=None, **kwargs):
        """Check if index of the system contains the regex pattern.

        Similar to pandas str.contains, thus the index
        string must contain the regex pattern. Uses ioutil.index_contains

        The index levels need to be named (df.index.name needs to
        be set for all levels).

        Note:
        -----
        Arguments are set to case=True, flags=0, na=False, regex=True.
        For case insensitive matching, use (?i) at the beginning of the pattern.

        See the pandas/python.re documentation for more details.

        Parameters
        ----------
        find_all : None or str
            If str (regex pattern) search in all index levels.
            All matching rows are returned. The remaining kwargs are ignored.
        kwargs : dict
            The regex which should be contained. The keys are the index names,
            the values are the regex.
            If the entry is not in index name, it is ignored silently.

        Returns
        -------
        pd.Index or pd.MultiIndex
            The matched rows/index

        """
        return ioutil.index_contains(self.get_index(as_dict=False), find_all, **kwargs)

    def match(self, find_all=None, **kwargs):
        """Check if index of the system match the regex pattern.

        Similar to pandas str.match, thus the start of the index string must match.
        Uses ioutil.index_match

        The index levels need to be named (df.index.name needs to
        be set for all levels).

        Note:
        -----
        Arguments are set to case=True, flags=0, na=False, regex=True.
        For case insensitive matching, use (?i) at the beginning of the pattern.

        See the pandas/python.re documentation for more details.

        Parameters
        ----------
        find_all : None or str
            If str (regex pattern) search for all matches in all index levels.
            All matching rows are returned. The remaining kwargs are ignored.
        kwargs : dict
            The regex to match. The keys are the index names,
            the values are the regex to match.
            If the entry is not in index name, it is ignored silently.

        Returns
        -------
        pd.Index or pd.MultiIndex
            The matched rows/index

        """
        return ioutil.index_match(self.get_index(as_dict=False), find_all, **kwargs)

    def fullmatch(self, find_all=None, **kwargs):
        """Check if a index row of the system is a full match to the regex pattern.

        Similar to pandas str.fullmatch, thus the whole
        string of the index must match. Uses ioutil.index_fullmatch

        The index levels need to be named (df.index.name needs to
        be set for all levels).

        Note:
        -----
        Arguments are set to case=True, flags=0, na=False, regex=True.
        For case insensitive matching, use (?i) at the beginning of the pattern.

        See the pandas/python.re documentation for more details.

        Parameters
        ----------
        find_all : None or str
            If str (regex pattern) search for all matches in all index levels.
            All matching rows are returned. The remaining kwargs are ignored.
        kwargs : dict
            The regex to match. The keys are the index names,
            the values are the regex to match.
            If the entry is not in index name, it is ignored silently.

        Returns
        -------
        pd.Index or pd.MultiIndex
            The matched rows/index

        """
        return ioutil.index_fullmatch(self.get_index(as_dict=False), find_all, **kwargs)


# API classes
class Extension(_BaseSystem):
    """Class which gathers all information for one extension of the IOSystem.

    Notes
    -----
    For the total accounts (D_) also reginal (appendix _reg) and
    per capita (appendix _cap) are possible.

    Attributes
    ----------
    name : string
        Every extension must have a name. This can (recommended) be the name
        of the instance. However, for plotting and saving this can also be
        changed.  This name will also be used for saving the extension as
        prefix to the attributes.
    F : pandas.DataFrame
        Total direct impacts with columns as Z. Index with (['stressor',
        'compartment']).
        The second level 'compartment' is optional
    F_Y : pandas.DataFrame
        Extension of final demand with columns a y and index as F
    S : pandas.DataFrame
        Direct impact (extensions) coefficients with multiindex as F
    S_Y : pandas.DataFrame
        Direct impact (extensions) coefficients of final demand. Index as F_Y
    M : pandas.DataFrame
        Multipliers with multiindex as F
    M_down : pandas.DataFrame
        Downstream multipliers with multiindex as F
    D_cba : pandas.DataFrame
        Footprint of consumption,  further specification with
        _reg (per region) or _cap (per capita) possible
    D_pba : pandas.DataFrame
        Territorial accounts, further specification with _reg (per region) or
        _cap (per capita) possible
    D_imp : pandas.DataFrame
        Import accounts (amount of 'extension' embodied in imports), further
        specification with _reg (per region) or _cap (per capita) possible
    D_exp : pandas.DataFrame
        Export accounts (amount of 'extension' embodied in exports), further
        specification with _reg (per region) or _cap (per capita) possible
    unit : pandas.DataFrame
        Unit for each row of the extension
    iosystem : string, DEPRECATED
        Note for the IOSystem, recommended to be 'pxp' or 'ixi' for
        product by product or industry by industry.
        However, this can be any string and can have more information if needed
        (eg for different technoloy assumptions)
        The string will be passed to the Extension
        Will be removed in future versions - all data in meta
    version : string, DEPRECATED
        This can be used as a version tracking system.
        Will be removed in future versions - all data in meta
    year : int, DEPRECATED
        Baseyear of the extension data
        Will be removed in future versions - all data in meta

    """

    def __init__(
        self,
        name,
        F=None,
        F_Y=None,
        S=None,
        S_Y=None,
        M=None,
        M_down=None,
        D_cba=None,
        D_pba=None,
        D_imp=None,
        D_exp=None,
        unit=None,
        **kwargs,
    ):
        """Init function - see docstring class."""
        self.name = name
        self.F = F
        self.F_Y = F_Y
        self.S = S
        self.S_Y = S_Y
        self.M = M
        self.M_down = M_down
        self.D_cba = D_cba
        self.D_pba = D_pba
        self.D_imp = D_imp
        self.D_exp = D_exp
        self.unit = unit

        for ext in kwargs:
            setattr(self, ext, kwargs[ext])

        # Internal attributes

        # minimal necessary to calc the rest
        # F_Y is optional, but this is checked in the reset routines
        self.__basic__ = ["F", "F_Y"]
        self.__D_accounts__ = [
            "D_cba",
            "D_pba",
            "D_imp",
            "D_exp",
            "D_cba_reg",
            "D_pba_reg",
            "D_imp_reg",
            "D_exp_reg",
            "D_cba_cap",
            "D_pba_cap",
            "D_imp_cap",
            "D_exp_cap",
        ]
        self.__non_agg_attributes__ = [
            "S",
            "S_Y",
            "M",
            "D_cba_reg",
            "D_pba_reg",
            "D_imp_reg",
            "D_exp_reg",
            "D_cba_cap",
            "D_pba_cap",
            "D_imp_cap",
            "D_exp_cap",
        ]

        self.__coefficients__ = ["S", "S_Y", "M"]

        # check if all accounts are available
        for acc in self.__D_accounts__:
            if acc not in self.__dict__:
                setattr(self, acc, None)

    def __str__(self):
        """Return string representation."""
        return super().__str__("Extension {} with parameters: ").format(self.name)

    def calc_system(self, x, Y, Y_agg=None, L=None, G=None, population=None):
        """Calculate the missing part of the extension plus accounts.

        This method allows to specify an aggregated Y_agg for the
        account calculation (see Y_agg below). However, the full Y needs
        to be specified for the calculation of F_Y or S_Y.

        Calculates:

        - for each sector and country:
            S, S_Y (if F_Y available), M, M_down,
            D_cba,
        - for each region:
            D_cba_reg, D_pba_reg, D_imp_reg, D_exp_reg,
        - for each region (if population vector is given):
            D_cba_cap, D_pba_cap, D_imp_cap, D_exp_cap

        Notes
        -----
        Only attributes which are not None are recalculated (for D_* this is
        checked for each group (reg, cap, and w/o appendix)).

        Parameters
        ----------
        x : pandas.DataFrame or numpy.array
            Industry output column vector
        Y : pandas.DataFrame or numpy.arry
            Full final demand array
        Y_agg : pandas.DataFrame or np.array, optional
            The final demand aggregated (one category per country).  Can be
            used to restrict the calculation of CBA of a specific category
            (e.g. households). Default: y is aggregated over all categories
        L : pandas.DataFrame or numpy.array, optional
            Leontief input output table L. If this is not given,
            the method recalculates M based on D_cba (must be present in
            the extension).
        G : pandas.DataFrame or numpy.array, optional
            Ghosh input output table G. If this is not given,
            M_down is not calculated.
        population : pandas.DataFrame or np.array, optional
            Row vector with population per region
        """
        # TODO This should only be used for calculating the full system.
        # TODO There needs to be a new method for calculating the system
        # for a different demand vector in here

        if Y_agg is None:
            try:
                Y_agg = Y.T.groupby(level="region", sort=False).sum().T

            except (AssertionError, KeyError):
                Y_agg = Y.T.groupby(level=0, sort=False).sum().T

        y_vec = Y.sum(axis=0)

        if self.F is None:
            self.F = calc_F(self.S, x)
            logging.debug(f"{self.name} - F calculated")

        if self.S is None:
            self.S = calc_S(self.F, x)
            logging.debug(f"{self.name} - S calculated")

        if (self.F_Y is None) and (self.S_Y is not None):
            self.F_Y = calc_F_Y(self.S_Y, y_vec)
            logging.debug(f"{self.name} - F_Y calculated")

        if (self.S_Y is None) and (self.F_Y is not None):
            self.S_Y = calc_S_Y(self.F_Y, y_vec)
            logging.debug(f"{self.name} - S_Y calculated")

        if self.M is None:
            if L is not None:
                self.M = calc_M(self.S, L)
                logging.debug(f"{self.name} - M calculated based on L")
            else:
                try:
                    self.M = recalc_M(
                        self.S,
                        self.D_cba,
                        Y=Y_agg,
                        nr_sectors=self.get_sectors().size,
                    )
                    logging.debug(f"{self.name} - M calculated based on D_cba and Y")
                except Exception as ex:
                    logging.debug(f"Recalculation of M not possible - cause: {ex}")

        if self.M_down is None:
            if G is not None:
                self.M_down = calc_M_down(self.S, G)
                logging.debug(f"{self.name} - M_down calculated based on G")
            else:
                logging.debug("Calculation of M_down not possible because G is not available.")

        F_Y_agg = 0
        if self.F_Y is not None:
            # F_Y_agg = ioutil.agg_columns(
            # ext['F_Y'], self.get_Y_categories().size)
            try:
                F_Y_agg = self.F_Y.T.groupby(level="region", sort=False).sum().T
            except (AssertionError, KeyError):
                F_Y_agg = self.F_Y.T.groupby(level=0, sort=False).sum().T

        if (self.D_cba is None) or (self.D_pba is None) or (self.D_imp is None) or (self.D_exp is None):
            if L is None:
                logging.debug("Not possilbe to calculate D accounts - L not present")
                return None
            self.D_cba, self.D_pba, self.D_imp, self.D_exp = calc_accounts(self.S, L, Y_agg)
            logging.debug(f"{self.name} - Accounts D calculated")

        # aggregate to country
        if (self.D_cba_reg is None) or (self.D_pba_reg is None) or (self.D_imp_reg is None) or (self.D_exp_reg is None):
            try:
                self.D_cba_reg = self.D_cba.T.groupby(level="region", sort=False).sum().T + F_Y_agg
            except (AssertionError, KeyError):
                self.D_cba_reg = self.D_cba.T.groupby(level=0, sort=False).sum().T + F_Y_agg
            try:
                self.D_pba_reg = self.D_pba.T.groupby(level="region", sort=False).sum().T + F_Y_agg
            except (AssertionError, KeyError):
                self.D_pba_reg = self.D_pba.T.groupby(level=0, sort=False).sum().T + F_Y_agg
            try:
                self.D_imp_reg = self.D_imp.T.groupby(level="region", sort=False).sum().T
            except (AssertionError, KeyError):
                self.D_imp_reg = self.D_imp.T.groupby(level=0, sort=False).sum().T
            try:
                self.D_exp_reg = self.D_exp.T.groupby(level="region", sort=False).sum().T
            except (AssertionError, KeyError):
                self.D_exp_reg = self.D_exp.T.groupby(level=0, sort=False).sum().T

            logging.debug(f"{self.name} - Accounts D for regions calculated")

        # calc accounts per capita if population data is available
        if population is not None:
            if (
                (self.D_cba_cap is None)
                or (self.D_pba_cap is None)
                or (self.D_imp_cap is None)
                or (self.D_exp_cap is None)
            ):
                self.D_cba_cap = self.D_cba_reg / population.iloc[0][self.D_cba_reg.columns]
                self.D_pba_cap = self.D_pba_reg / population.iloc[0][self.D_pba_reg.columns]
                self.D_imp_cap = self.D_imp_reg / population.iloc[0][self.D_imp_reg.columns]
                self.D_exp_cap = self.D_exp_reg / population.iloc[0][self.D_exp_reg.columns]

                logging.debug(f"{self.name} - Accounts D per capita calculated")
        return self

    def plot_account(
        self,
        row,
        per_capita=False,
        sector=None,
        file_name=False,
        file_dpi=600,
        population=None,
        **kwargs,
    ):
        """Plot D_pba, D_cba, D_imp and D_exp for the specified row (account).

        Plot either the total country accounts or for a specific sector,
        depending on the 'sector' parameter.

        Per default the accounts are plotted as bar charts.
        However, any valid keyword for the pandas.DataFrame.plot
        method can be passed.

        Notes
        -----
            This looks prettier with the seaborn module
            (import seaborn before calling this method)

        Parameters
        ----------
        row : string, tuple or int
            A valid index for the row in the extension which
            should be plotted (one(!) row - no list allowed)
        per_capita : boolean, optional
            Plot the per capita accounts instead of the absolute values
            default is False
        sector: string, optional
            Plot the results for a specific sector of the IO table. If
            None is given (default), the total regional accounts are plotted.
        population : pandas.DataFrame or np.array, optional
            Vector with population per region. This must be given if
            values should be plotted per_capita for a specific sector since
            these values are calculated on the fly.
        file_name : path string, optional
            If given, saves the plot to the given filename
        file_dpi : int, optional
            Dpi for saving the figure, default 600

        **kwargs : key word arguments, optional
            This will be passed directly to the pd.DataFrame.plot method

        Returns
        -------
        Axis as given by pandas.DataFrame.plot, None in case of errors

        """
        # necessary if row is given for Multiindex without brackets
        if type(per_capita) is not bool:
            raise ValueError("per_capita parameter must be boolean")

        if type(row) is int:
            row = self.D_cba.loc[row].name

        name_row = str(row).replace("(", "").replace(")", "").replace("'", "").replace("[", "").replace("]", "")
        if sector:
            graph_name = name_row + " for sector " + sector
        else:
            graph_name = name_row + " total account"
        if per_capita:
            graph_name = graph_name + " - per capita"

        graph_name = self.name + " - " + graph_name

        if self.unit is not None:
            try:
                # for multiindex the entry is given with header,
                # for single index just the entry
                y_label_name = name_row + " (" + str(self.unit.loc[row, "unit"].tolist()[0]) + ")"
            except Exception:
                y_label_name = name_row + " (" + str(self.unit.loc[row, "unit"]) + ")"
        else:
            y_label_name = name_row

        if "kind" not in kwargs:
            kwargs["kind"] = "bar"

        if "colormap" not in kwargs:
            kwargs["colormap"] = "Spectral"

        accounts = collections.OrderedDict()

        if sector:
            accounts["Footprint"] = "D_cba"
            accounts["Territorial"] = "D_pba"
            accounts["Imports"] = "D_imp"
            accounts["Exports"] = "D_exp"
        else:
            if per_capita:
                accounts["Footprint"] = "D_cba_cap"
                accounts["Territorial"] = "D_pba_cap"
                accounts["Imports"] = "D_imp_cap"
                accounts["Exports"] = "D_exp_cap"
            else:
                accounts["Footprint"] = "D_cba_reg"
                accounts["Territorial"] = "D_pba_reg"
                accounts["Imports"] = "D_imp_reg"
                accounts["Exports"] = "D_exp_reg"

        data_row = pd.DataFrame(columns=list(accounts))
        for key in accounts:
            if sector:
                try:
                    _data = pd.DataFrame(getattr(self, accounts[key]).xs(key=sector, axis=1, level="sector").loc[row].T)
                except (AssertionError, KeyError):
                    _data = pd.DataFrame(getattr(self, accounts[key]).xs(key=sector, axis=1, level=1).loc[row].T)

                if per_capita:
                    if population is not None:
                        if type(population) is pd.DataFrame:
                            # check for right order:
                            if population.columns.tolist() != self.D_cba_reg.columns.tolist():
                                warnings.warn(
                                    "Population regions are inconsistent with IO regions",
                                    stacklevel=2,
                                )
                            population = population.to_numpy()
                            population = population.reshape((-1, 1))
                            _data = _data / population
                    else:
                        raise ValueError("Population vector must be given for sector results per capita")
            else:
                _data = pd.DataFrame(getattr(self, accounts[key]).loc[row].T)
            _data.columns = [key]
            data_row[key] = _data[key]

        if "title" not in kwargs:
            kwargs["title"] = graph_name

        ax = data_row.plot(**kwargs)
        plt.xlabel("Regions")
        plt.ylabel(y_label_name)
        plt.legend(loc="best")
        try:
            plt.tight_layout()
        except Exception:
            pass

        if file_name:
            plt.savefig(file_name, dpi=file_dpi)
        return ax

    def report_accounts(
        self,
        path,
        per_region=True,
        per_capita=False,
        pic_size=1000,
        format="rst",
        ffname=None,
        **kwargs,
    ):
        """Write a report to the given path for the regional accounts.

        The report consists of a text file and a folder with the pics
        (both names following parameter name)

        Notes
        -----
            This looks prettier with the seaborn module
            (import seaborn before calling this method)


        Parameters
        ----------
        path : pathlib.Path or string
            Root path for the report
        per_region : boolean, optional
            If true, reports the accounts per region
        per_capita : boolean, optional
            If true, reports the accounts per capita
            If per_capita and per_region are False, nothing will be done
        pic_size : int, optional
            size for the figures in px, 1000 by default
        format : string, optional
            file format of the report:
            'rst'(default), 'html', 'latex', ...
            except for rst all depend on the module docutils (all writer_name
            from docutils can be used as format)
        ffname : string, optional
            root file name (without extension, per_capita or per_region will be
            attached) and folder names If None gets passed (default), self.name
            with be modified to get a valid name for the operation system
            without blanks
        **kwargs : key word arguments, optional
            This will be passed directly to the pd.DataFrame.plot method
            (through the self.plot_account method)

        """
        if not per_region and not per_capita:
            raise ValueError("Either per_region or per_capita must be choosen")

        _plt = plt.isinteractive()
        plt.ioff()

        if type(path) is str:
            path = path.rstrip("\\")
            path = Path(path)

        path.mkdir(parents=True, exist_ok=True)

        if ffname is None:
            valid_char = string.ascii_letters + string.digits + "_"
            ffname = self.name.replace(" ", "_")
            ffname = "".join([r for r in ffname if r in valid_char])

        rep_spec = collections.namedtuple("rep_spec", ["make", "spec_string", "is_per_capita"])

        reports_to_write = {
            "per region accounts": rep_spec(per_region, "_per_region", False),
            "per capita accounts": rep_spec(per_capita, "_per_capita", True),
        }
        logging.info(f"Write report for {self.name}")
        fig_name_list = []
        for arep in reports_to_write:
            if not reports_to_write[arep].make:
                continue

            report_txt = []
            report_txt.append("###########")
            report_txt.append("MRIO report")
            report_txt.append("###########")
            report_txt.append("\n")
            _ext = "Extension: " + self.name + " - " + str(arep)
            report_txt.append(_ext)
            report_txt.append("=" * len(_ext))

            report_txt.append(".. contents::\n\n")

            curr_ffname = ffname + reports_to_write[arep].spec_string
            subfolder = path / curr_ffname

            subfolder.mkdir(parents=True, exist_ok=True)

            for row in self.get_rows():
                name_row = (
                    str(row)
                    .replace("(", "")
                    .replace(")", "")
                    .replace("'", "")
                    .replace(" ", "_")
                    .replace(", ", "_")
                    .replace("__", "_")
                )
                graph_name = self.name + " - " + str(row).replace("(", "").replace(")", "").replace("'", "")

                # get valid file name
                def clean(varStr):
                    return re.sub(r"\W|^(?=\d)", "_", varStr)

                file_name = clean(name_row + reports_to_write[arep].spec_string)
                # possibility of still having __ in there:
                file_name = re.sub("_+", "_", file_name)

                # restrict file length
                file_name = file_name[:50]

                def file_name_nr(a, c):
                    return a + "_" + str(c)

                _loopco = 0
                while file_name_nr(file_name, _loopco) in fig_name_list:
                    _loopco += 1
                file_name = file_name_nr(file_name, _loopco)
                fig_name_list.append(file_name)
                file_name = file_name + ".png"

                file_name = subfolder / file_name
                file_name_rel = file_name.relative_to(path)

                self.plot_account(
                    row,
                    file_name=file_name,
                    per_capita=reports_to_write[arep].is_per_capita,
                    **kwargs,
                )
                plt.close()

                report_txt.append(graph_name)
                report_txt.append("-" * len(graph_name) + "\n\n")

                report_txt.append(".. image:: " + str(file_name_rel))
                report_txt.append(f"   :width: {int(pic_size)} \n")

            # write report file and convert to given format
            report_txt.append("\nReport written on " + time.strftime("%Y%m%d %H%M%S"))
            fin_txt = "\n".join(report_txt)
            if format != "rst":
                try:
                    import docutils.core as dc

                    if format == "tex":
                        format = "latex"
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore", category=DeprecationWarning)
                        fin_txt = dc.publish_string(
                            fin_txt,
                            writer_name=format,
                            settings_overrides={"output_encoding": "unicode"},
                        )

                except Exception:
                    warnings.warn(
                        "Module docutils not available - write rst instead",
                        stacklevel=2,
                    )
                    format = "rst"
            format_str = {
                "latex": "tex",
                "tex": "tex",
                "rst": "txt",
                "txt": "txt",
                "html": "html",
            }
            _repfile = curr_ffname + "." + format_str.get(format, str(format))
            with open(path / _repfile, "w") as out_file:
                out_file.write(fin_txt)
            logging.info(f"Report for {arep} written to {str(_repfile)}")

        if _plt:  # pragma: no cover
            plt.ion()

    def get_rows(self):
        """Return the name of the rows of the extension."""
        possible_dataframes = [
            "F",
            "F_Y",
            "M",
            "S",
            "D_cba",
            "D_pba",
            "D_imp",
            "D_exp",
            "D_cba_reg",
            "D_pba_reg",
            "D_imp_reg",
            "D_exp_reg",
            "D_cba_cap",
            "D_pba_cap",
            "D_imp_cap",
            "D_exp_cap",
        ]
        for df in possible_dataframes:
            if (df in self.__dict__) and (getattr(self, df) is not None):
                return getattr(self, df).index
        else:
            warnings.warn("No attributes available to get row names", stacklevel=2)
            return None

    @property
    def rows(self):
        """Return the name of the rows of the extension."""
        return self.get_rows()

    def get_row_data(self, row, name=None):
        """Return a dict with all available data for a row in the extension.

        If you need a new extension, see the extract method.

        Parameters
        ----------
        row : index, tuple, list, string
            A valid index for the extension DataFrames
        name : string, optional
            If given, adds a key 'name' with the given value to the dict. In
            that case the dict can be
            used directly to build a new extension.

        Returns
        -------
        dict object with the data (pandas DataFrame) for the specific rows
        """
        # depraction warning

        warnings.warn(
            "This method will be removed in future versions. Use extract method instead",
            DeprecationWarning,
            stacklevel=2,
        )

        retdict = {}
        for rowname, data in zip(self.get_DataFrame(), self.get_DataFrame(data=True)):
            retdict[rowname] = pd.DataFrame(data.loc[row])
        if name:
            retdict["name"] = name
        return retdict

    def extract(self, index, dataframes=None, return_type="dataframes"):
        """Return a dict with all available data for a row in the extension.

        Parameters
        ----------
        index : valid row index or dict
            A valid index for the extension DataFrames.
            Alternatively, a dict with the extension name as key and the valid index
            as value can be passed.
        dataframes : list, optional
            The dataframes which should be extracted. If None (default),
            all available dataframes are extracted. If the list contains
            dataframes which are not available, a warning is issued and
            the missing dataframes are ignored.
        return_type: str, optional
            If 'dataframe' or 'df' (also with 's' plural, default), the returned dict contains dataframes.
            If 'extension' or 'ext' (also with 's' plural) an Extension
            object is returned (named like the original with _extracted appended).
            Any other string: an Extension object is returned, with the name set to the passed string.


        Returns
        -------
        dict object with the data (pandas DataFrame) for the specific rows
        or an Extension object (based on return_type)

        """
        if isinstance(index, dict):
            index = index.get(self.name, None)
        if type(index) in (str, tuple):
            index = [index]

        retdict = {}
        if dataframes is None:
            dataframes = self.get_DataFrame()
        else:
            if not all(elem in self.get_DataFrame() for elem in dataframes):
                warnings.warn(
                    f"Not all requested dataframes are available in {self.name}",
                    stacklevel=2,
                )
            dataframes = [elem for elem in dataframes if elem in self.get_DataFrame()]

        for dfname in dataframes:
            data = getattr(self, dfname)
            retdict[dfname] = data.loc[index, :]

        if return_type.lower() in ["dataframes", "dataframe", "dfs", "df"]:
            return retdict
        if return_type.lower() in ["extensions", "extension", "ext", "exts"]:
            ext_name = self.name + "_extracted"
        else:
            ext_name = return_type
        return Extension(name=ext_name, **retdict)

    def diag_stressor(self, stressor, name=None, _meta=None):
        """Diagonalize one row of the stressor matrix for a flow analysis.

        This method takes one row of the F matrix and diagonalize
        to the full region/sector format. Footprints calculation based
        on this matrix show the flow of embodied stressors from the source
        region/sector (row index) to the final consumer (column index).

        Note
        ----
        Since the type of analysis based on the disaggregated matrix is based
        on flows, direct household emissions (F_Y) are not included.

        Parameters
        ----------
        stressor : str or int - valid index for one row of the F matrix
            This must be a tuple for a multiindex, a string otherwise.
            The stressor to diagonalize.

        name : string (optional)
            The new name for the extension,
            if None (default): string based on the given stressor (row name)

        _meta: MRIOMetaData, optional
            Metadata handler for logging, optional. Internal

        Returns
        -------
        pymrio.Extension

        """
        if type(stressor) is int:
            stressor = self.F.index[stressor]
        if len(stressor) == 1:
            stressor = stressor[0]
        if not name:
            if type(stressor) is str:
                name = stressor
            else:
                name = "_".join(stressor) + "_diag"

        ext_diag = Extension(name)

        ext_diag.F = pd.DataFrame(
            index=self.F.columns,
            columns=self.F.columns,
            data=np.diag(self.F.loc[stressor, :]),
        )
        try:
            ext_diag.unit = pd.DataFrame(
                index=ext_diag.F.index,
                columns=self.unit.columns,
                data=self.unit.loc[stressor].unit,
            )
        except AttributeError:
            # If no unit in stressor, self.unit.columns break
            ext_diag.unit = None

        if _meta:
            _meta._add_modify(f"Calculated diagonalized accounts {name} from  {self.name}")

        return ext_diag

    def characterize(
        self,
        factors,
        characterized_name_column="impact",
        characterization_factors_column="factor",
        characterized_unit_column="impact_unit",
        orig_unit_column="stressor_unit",
        only_validation=False,
        name="_characterized",
    ):
        """Characterize stressors.

        Characterizes the extension with the characterization factors given in factors.

        The dataframe factors can contain characterization factors which depend on
        stressors not present in the Extension - these will be ignored (set to 0).

        The dataframe passed for the characterization must be in a long format.
        It must contain columns with the same names as in the index of the extension.

        The routine can also handle region or sector specific characterization factors.
        In that case, the passed dataframe must also include columns for sector and/or region.
        The names must be the same as the column names of the extension.

        Other column names can be specified in the parameters,
        see below for the default values.

        The routine also performs a validation of the input factors DataFrame and reports

            - unit errors (impact unit consistent, stressor unit match).
                Note: does not check if the conversion is correct!
            - report missing stressors, regions, sectors which are in factors
                but not in the extension
            - if factors are specified for all regions/sectors of the extension

        Besides the unit errors, the characterization routine works with missing data.
        Any missing data is assumed to be 0.

        Note
        -----
        Accordance of units is enforced.
        This is done be checking the column specified in orig_unit_column with the unit
        dataframe of the extension.

        Parameters
        ----------
        factors: pd.DataFrame
            A dataframe in long format with numerical index and columns named
            index.names of the extension to be characterized and
            'characterized_name_column', 'characterization_factors_column',
            'characterized_unit_column', 'orig_unit_column'

        characterized_name_column: str (optional) or list[str]
            Name of the column with the names of the
            characterized account (default: "impact").
            In case a list of columns is passed, these get
            conconateded to one colum and split before return.

        characterization_factors_column: str (optional)
            Name of the column with the factors for the
            characterization (default: "factor")

        characterized_unit_column: str (optional)
            Name of the column with the units of the characterized accounts
            characterization (default: "impact_unit")

        name: string (optional)
            The new name for the extension,
            if the string starts with an underscore '_' the string
            with be appended to the original name. Default: '_characterized'


        Returns
        -------
        namedtuple with the following attributes:
            validation: pd.DataFrame
            extension: pymrio.Extension

        Extension is set to None when "only_validation" is set to True.

        """
        name = self.name + name if name[0] == "_" else name

        if type(characterized_name_column) is list:
            if len(characterized_name_column) == 0:
                raise ValueError("characterized_name_column must be a string or a list with at least one element")
            if len(characterized_name_column) == 1:
                characterized_name_column = characterized_name_column[0]
                orig_characterized_name_column = None
            else:
                orig_characterized_name_column = characterized_name_column
                sep_char = "<<!>>"
                all_impacts = pd.concat([factors[col] for col in characterized_name_column]).unique()
                all_impacts_joined = "".join(all_impacts)

                while sep_char in all_impacts_joined:
                    sep_char = sep_char.replace("|", "||")

                characterized_name_column = "char_name_col_merged"
                factors.loc[:, characterized_name_column] = factors[orig_characterized_name_column].agg(
                    sep_char.join, axis=1
                )
        else:
            orig_characterized_name_column = None

        req = ioutil._characterize_get_requried_col(
            ext_index_names=list(self.get_rows().names),
            factors=factors,
            characterized_name_column=characterized_name_column,
            characterization_factors_column=characterization_factors_column,
            characterized_unit_column=characterized_unit_column,
        )

        validation = ioutil._validate_characterization_table(
            factors=factors,
            regions=self.get_regions(),
            sectors=self.get_sectors(),
            ext_unit=self.unit,
            all_required_col=req.all_required_columns,
            characterized_name_column=characterized_name_column,
            characterized_unit_column=characterized_unit_column,
            orig_unit_column=orig_unit_column,
        )

        ret_value = collections.namedtuple("characterization_result", ["validation", "extension"])

        if only_validation:
            return ret_value(validation=validation, extension=None)

        index_col = req.required_index_col

        if any(validation.error_unit_impact):
            warnings.warn(
                "Inconsistent impact units found in factors - check validation",
                stacklevel=2,
            )
            return ret_value(validation=validation, extension=None)

        if any(validation.error_unit_stressor):
            warnings.warn(
                "Unit errors/inconsistencies between passed units and extension units - check validation",
                stacklevel=2,
            )
            return ret_value(validation=validation, extension=None)

        fac_calc = (
            factors.set_index(index_col + [characterized_name_column])
            .loc[:, characterization_factors_column]
            .unstack(characterized_name_column)
            .fillna(0)
        )

        new_ext = Extension(name=name)

        # restrict to F and S and the Y stuff, otherwise we loose
        # _Y if we have multipliers etc. Also region specific not applicable to calculated results
        acc_to_char = [d for d in self.get_DataFrame(data=False, with_unit=False) if d in ["F", "F_Y", "S_Y", "S"]]

        for acc_name in acc_to_char:
            acc = getattr(self, acc_name)
            _series = acc.stack(acc.columns.names, future_stack=True)
            # template _df_shape different for final demand accounts
            _df_shape = pd.DataFrame(index=_series.index, columns=fac_calc.columns)
            res = _df_shape.assign(
                **{char_name: _series * fac_calc.loc[:, char_name] for char_name in _df_shape.columns}
            )
            _group_index = res.index.names.difference(acc.index.names)
            res = res.groupby(_group_index).sum().T.reindex(columns=acc.columns)
            if orig_characterized_name_column:
                res.index = pd.MultiIndex.from_arrays(
                    list(zip(*res.index.str.split(sep_char))),
                    names=orig_characterized_name_column,
                )
            setattr(new_ext, acc_name, res)

        res_unit = (
            factors.loc[:, [characterized_name_column, characterized_unit_column]]
            .drop_duplicates()
            .set_index(characterized_name_column)
            .rename({characterized_unit_column: "unit"}, axis=1)
        )
        if orig_characterized_name_column:
            res_unit.index = pd.MultiIndex.from_arrays(
                list(zip(*res_unit.index.str.split(sep_char))),
                names=orig_characterized_name_column,
            )
        res_unit = res_unit.loc[new_ext.get_rows(), :]
        new_ext.unit = res_unit
        if orig_characterized_name_column:
            validation = validation.drop(characterized_name_column, axis=1)

        return ret_value(
            validation=validation,
            extension=new_ext,
        )

    def convert(
        self,
        df_map,
        new_extension_name,
        agg_func="sum",
        drop_not_bridged_index=True,
        unit_column_orig="unit_orig",
        unit_column_new="unit_new",
        ignore_columns=None,
        reindex=None,
    ):
        """Apply the convert function to all dataframes in the extension.

        Parameters
        ----------
        df_map : pd.DataFrame
            The DataFrame with the mapping of the old to the new classification.
            This requires a specific structure:

            - Constraining data (e.g. stressors, regions, sectors) can be
            either in the index or columns of df_orig. They need to have the same
            name as the named index or column in df_orig. The algorithm searches
            for matching data in df_orig based on all constraining columns in df_map.

            - Bridge columns are columns with '__' in the name. These are used to
            map (bridge) some/all of the constraining columns in df_orig to the new
            classification.

            - One column "factor", which gives the multiplication factor for the
            conversion. If it is missing, it is set to 1.


            This is better explained with an example.
            Assuming a original dataframe df_orig with
            index names 'stressor' and 'compartment' and column name 'region',
            the characterizing dataframe could have the following structure (column names):

            stressor ... original index name
            compartment ... original index name
            region ... original column name
            factor ... the factor for multiplication/characterization
                If no factor is given, the factor is assumed to be 1.
                This can be used, to simplify renaming/aggregation mappings.
            impact__stressor ... the new index name,
                replacing the previous index name "stressor".
                Thus here "stressor" will be renamed to "impact", and the row index
                will be renamed by the entries here.
            compartment__compartment ... the new compartment,
                replacing the original compartment. No rename of column happens here,
                still row indicies will be renamed as given here.

            The columns with __ are called bridge columns, they are used
            to match the original index. The new dataframe will have index names
            based on the first part of the bridge column, in the order
            in which the bridge columns are given in the mapping dataframe.

            "region" is constraining column, these can either be for the index or column
            in df_orig. In case both exist, the one in index is preferred.

        extension_name: str
            The name of the new extension returned

        agg_func : str or func
            the aggregation function to use for multiple matchings (summation by default)

        drop_not_bridged_index : bool, optional
            What to do with index levels in df_orig not appearing in the bridge columns.
            If True, drop them after aggregation across these, if False,
            pass them through to the result.

            *Note:* Only index levels will be dropped, not columns.

            In case some index levels need to be dropped, and some not
            make a bridge column for the ones to be dropped and map all to the same name.
            Then drop this index level after the conversion.

        unit_column_orig : str, optional
            Name of the column in df_map with the original unit.
            This will be used to check if the unit matches the original unit in the extension.
            Default is "unit_orig", if None, no check is performed.

        unit_column_new : str, optional
            Name of the column in df_map with the new unit to be assigned to the new extension.
            Default is "unit_new", if None same unit as in df_orig TODO EXPLAIN BETTER, THINK WARNING

        ignore_columns : list, optional
            List of column names in df_map which should be ignored.
            These could be columns with additional information, etc.
            The unit columns given in unit_column_orig and unit_column_new
            are ignored by default.

        reindex: str, None or collection
            Wrapper for pandas' reindex method to control return order.
            - If None: sorts the index alphabetically.
            - If str: uses the unique value order from the specified bridge column as the index order.
            - For other types (e.g., collections): passes directly to pandas.reindex.


        """
        if not ignore_columns:
            ignore_columns = []

        if unit_column_orig:
            if unit_column_orig not in df_map.columns:
                raise ValueError(f"Unit column {unit_column_orig} not in mapping dataframe, pass None if not available")
            ignore_columns.append(unit_column_orig)
            for entry in df_map.iterrows():
                # need fullmatch here as the same is used in ioutil.convert
                corresponding_rows = self.fullmatch(**entry[1].to_dict())
                for row in corresponding_rows:
                    if self.unit.loc[row].unit != entry[1][unit_column_orig]:
                        raise ValueError(f"Unit in extension does not match the unit in mapping for row {row}")

        new_extension = Extension(name=new_extension_name)

        if unit_column_new:
            if unit_column_new not in df_map.columns:
                raise ValueError(f"Unit column {unit_column_new} not in mapping dataframe, pass None if not available")

            ignore_columns.append(unit_column_new)

        for df_name, df in zip(
            self.get_DataFrame(data=False, with_unit=False),
            self.get_DataFrame(data=True, with_unit=False),
        ):
            setattr(
                new_extension,
                df_name,
                ioutil.convert(
                    df_orig=df,
                    df_map=df_map,
                    agg_func=agg_func,
                    drop_not_bridged_index=drop_not_bridged_index,
                    ignore_columns=ignore_columns,
                    reindex=reindex,
                ),
            )

        if unit_column_new:
            unit = pd.DataFrame(columns=["unit"], index=new_extension.get_rows())
            bridge_columns = [col for col in df_map.columns if "__" in col]
            unique_new_index = (
                df_map.drop_duplicates(subset=bridge_columns).loc[:, bridge_columns].set_index(bridge_columns).index
            )
            unique_new_index.names = [col.split("__")[0] for col in bridge_columns]

            unit.unit = (
                df_map.drop_duplicates(subset=bridge_columns)
                .set_index(bridge_columns)
                .loc[unique_new_index]
                .loc[:, unit_column_new]
            )
            new_extension.unit = unit
        else:
            new_extension.unit = None

        return new_extension


class IOSystem(_BaseSystem):
    """Class containing a whole EE MRIO System.

    The class collects pandas dataframes for a whole EE MRIO system. The
    attributes for the trade matrices (Z, L, A, x, Y) can be set directly,
    extensions are given as dictionaries containing F, F_Y, D, m, D_cba, D_pba,
    D_imp, D_exp

    Notes
    -----
        The attributes and extension dictionary entries are pandas.DataFrame
        with an MultiIndex.  This index must have the specified level names.

    Attributes
    ----------
    Z : pandas.DataFrame
        Symetric input output table (flows) with country and sectors as
        MultiIndex with names 'region' and 'sector' for columns and index
    Y : pandas.DataFrame
        final demand with MultiIndex with index.names = (['region', 'sector'])
        and column.names = (['region', 'category'])
    A : pandas.DataFrame
        coefficient input output table, MultiIndex as Z
    L : pandas.DataFrame
        Leontief (= inv(I-A)), MultiIndex as Z
    unit : pandas.DataFrame
        Unit for each row of Z
    system : string
        Note for the IOSystem, recommended to be 'pxp' or 'ixi' for
        product by product or industry by industry.
        However, this can be any string and can have more information if needed
        (eg for different technoloy assumptions)
        The string will be passed to the IOSystem
    meta : class
        Meta class handler
    version : string, DEPRECATED
        This can be used as a version tracking system.
        Will be removed in future versions - all data in meta
    year : string or int, DEPRECATED
        Baseyear of the IOSystem
        Will be removed in future versions - all data in meta
    price : string, DEPRECATED
        Price system of the IO (current or constant prices)
        Will be removed in future versions - all data in meta
    name : string, optional, DEPRECATED
        Name of the IOSystem, default is 'IO'
        Will be removed in future versions - all data in meta
    population: pandas.DataFrame, optional
        DataFrame with row 'Population' and columns following region names of Z

    **kwargs : dictonary
        Extensions are given as dictionaries and will be passed to the
        Extension class.  The dict must contain a key with a value for 'name',
        this can be the same as the name of the dict.  For the further keys see
        class Extension

    """

    def __init__(
        self,
        Z=None,
        Y=None,
        A=None,
        B=None,
        x=None,
        L=None,
        G=None,
        unit=None,
        population=None,
        system=None,
        version=None,
        year=None,
        price=None,
        meta=None,
        name=None,
        description=None,
        **kwargs,
    ):
        """Init function - see docstring class."""
        self.Z = Z
        self.Y = Y
        self.x = x
        self.A = A
        self.B = B
        self.L = L
        self.G = G
        self.unit = unit
        self.population = population

        if meta:
            self.meta = meta
            self.meta.change_meta("name", name)
            self.meta.change_meta("system", system)
            self.meta.change_meta("year", year)
            self.meta.change_meta("price", price)
            self.meta.change_meta("version", version)
            self.meta.change_meta("description", description)
        else:
            self.meta = MRIOMetaData(
                description=description,
                name=name,
                system=system,
                version=version,
            )

        if not getattr(self.meta, "name", None):
            self.meta.change_meta("name", "IO")

        for ext in kwargs:
            setattr(self, ext, Extension(**kwargs[ext]))

        # Attributes needed to define the IOSystem
        self.__non_agg_attributes__ = ["A", "L"]

        self.__coefficients__ = ["A", "L"]
        self.__basic__ = ["Z", "Y"]  # minimal necessary to calc the rest

    def __str__(self):
        """Return string representation."""
        return super().__str__("IO System with parameters: ")

    def __eq__(self, other):
        """Only the dataframes are compared."""
        self_ext = set(self.get_extensions(data=False, instance_names=True))
        other_ext = set(other.get_extensions(data=False, instance_names=True))
        if len(self_ext.difference(other_ext)) < 0:
            return False

        for ext in self_ext:
            if self.__dict__[ext] != other.__dict__[ext]:
                return False

        return super().__eq__(other)

    @property
    def name(self):
        """Return name."""
        try:
            return self.meta.name
        except AttributeError:
            return "undef"

    @property
    def extensions(self):
        """Return the defined extension names."""
        return list(self.get_extensions(instance_names=False))

    @property
    def extensions_instance_names(self):
        """Return the instance names of the extensions."""
        return list(self.get_extensions(instance_names=True))

    def get_gross_trade(
        self,
    ) -> typing.NamedTuple("gross_trade", [("bilat_flows", pd.DataFrame), ("totals", pd.DataFrame)]):
        """Return the gross bilateral trade flows and totals.

        These are the entries of Z and Y with the domestic blocks set to 0.

        Returns
        -------
        namedtuple (with two pandas DataFrames)
            A namedTuple with two fields:

                - bilat_flows: df with rows: exporting country and
                  sector, columns: importing countries
                - totals: df with gross total imports and exports per
                  sector and region

        """
        return calc_gross_trade(Z=self.Z, Y=self.Y)

    def calc_all(self, include_ghosh=False):
        """Calculate missing parts of the IOSystem and all extensions.

        This method calls `calc_system` and `calc_extensions` to perform the calculations.

        Parameters
        ----------
        include_ghosh : bool, optional
            If True, includes ghosh calculations in the system and extensions.
            Default is False.

        Returns
        -------
        self : IOSystem
            The updated IOSystem instance after performing all calculations.
        """
        self.calc_system(include_ghosh=include_ghosh)
        self.calc_extensions(include_ghosh=include_ghosh)
        return self

    def calc_system(self, include_ghosh=False):
        """Calculate the missing part of the core IOSystem.

        The method checks Z, A, x, L and calculates all which are None

        The possible cases are:
            Case    Provided    Calculated
            1)      Z           A, x, L
            2)      A, x        Z, L
            3)      A, Y        L, x, Z

        ghosh will be calculated if include_ghosh is True, after the cases above are
        dealt with. The ghosh calculation rely on Z

        Parameters
        ----------
        include_ghosh : bool, optional
            If True, includes ghosh calculations in the system and extensions.
            Default is False.

        """
        # Possible cases:
        # 1) Z given, rest can be None and calculated
        # 2) A and x given, rest can be calculated
        # 3) A and Y , calc L (if not given) - calc x and the rest

        # this catches case 3
        if self.x is None and self.Z is None:
            # in that case we need L or at least A to calculate it
            if self.L is None:
                self.L = calc_L(self.A)
                logging.info("Leontief matrix L calculated")
            self.x = calc_x_from_L(self.L, self.Y.sum(axis=1))
            self.meta._add_modify("Industry Output x calculated")

        # this chains of ifs catch cases 1 and 2
        if self.Z is None:
            self.Z = calc_Z(self.A, self.x)
            self.meta._add_modify("Flow matrix Z calculated")

        if self.x is None:
            self.x = calc_x(self.Z, self.Y)
            self.meta._add_modify("Industry output x calculated")

        if self.A is None:
            self.A = calc_A(self.Z, self.x)
            self.meta._add_modify("Coefficient matrix A calculated")

        if self.L is None:
            self.L = calc_L(self.A)
            self.meta._add_modify("Leontief matrix L calculated")

        if include_ghosh:
            if self.B is None:
                self.B = calc_B(self.Z, self.x)
                self.meta._add_modify("Normalized industrial flow matrix B calculated")

            if self.G is None:
                self.G = calc_G(self.B)
                self.meta._add_modify("Ghosh matrix G calculated")

        return self

    def calc_extensions(self, extensions=None, Y_agg=None, include_ghosh=False):
        """Calculate the extension and their accounts.

        For the calculation, y is aggregated across specified y categories
        The method calls .calc_system of each extension (or these given in the
        extensions parameter)

        Parameters
        ----------
        extensions : list of strings, optional
            A list of key names of extensions which shall be calculated.
            Default: all dictionaries of IOSystem are assumed to be extensions
        Y_agg : pandas.DataFrame or np.array, optional
            The final demand aggregated (one category per country).  Can be
            used to restrict the calculation of CBA of a specific category
            (e.g. households). Default: y is aggregated over all categories
        include_ghosh : bool, optional
            If True, includes ghosh calculations in the system and extensions.
            Default is False.

        """
        ext_list = list(self.get_extensions(data=False, instance_names=True))
        extensions = extensions or ext_list
        if isinstance(extensions, str):
            extensions = [extensions]

        for ext_name in extensions:
            self.meta._add_modify(f"Calculating accounts for extension {ext_name}")
            ext = getattr(self, ext_name)
            ext.calc_system(
                x=self.x,
                Y=self.Y,
                L=self.L,
                G=self.G,
                Y_agg=Y_agg,
                population=self.population,
            )
        return self

    def report_accounts(
        self,
        path,
        per_region=True,
        per_capita=False,
        pic_size=1000,
        format="rst",
        **kwargs,
    ):
        """Generate a report to the given path for all extension.

        This method calls .report_accounts for all extensions

        Notes
        -----
            This looks prettier with the seaborn module (import seaborn before
            calling this method)

        Parameters
        ----------
        path : string
            Root path for the report
        per_region : boolean, optional
            If true, reports the accounts per region
        per_capita : boolean, optional
            If true, reports the accounts per capita
            If per_capita and per_region are False, nothing will be done
        pic_size : int, optional
            size for the figures in px, 1000 by default
        format : string, optional
            file format of the report:
            'rst'(default), 'html', 'latex', ...
            except for rst all depend on the module docutils (all writer_name
            from docutils can be used as format)
        ffname : string, optional
            root file name (without extension, per_capita or per_region will be
            attached) and folder names If None gets passed (default), self.name
            with be modified to get a valid name for the operation system
            without blanks
        **kwargs : key word arguments, optional
            This will be passed directly to the pd.DataFrame.plot method
            (through the self.plot_account method)

        """
        for ext in self.get_extensions(data=True):
            ext.report_accounts(
                path=path,
                per_region=per_region,
                per_capita=per_capita,
                pic_size=pic_size,
                format=format,
                **kwargs,
            )

    def get_extensions(self, names=None, data=False, instance_names=True):
        """Yield the extensions or their names.

        Parameters
        ----------
        names = str or list like, optional
           Extension names to yield. If None (default), all extensions are
           yielded. This can be used to convert from set names to instance names
           and vice versa or to harmonize a list of extensions.

        data : boolean, optional
           If True, returns a generator which yields the extensions.
           If False, returns a generator which yields the names of
           the extensions (default)

        instance_names : boolean, optional
            If True, returns the name of the instance, otherwise
            the set (custom) name of the extension. (default: True)
            For example, the test mrio has a extension named
            'Factor Inputs' (get it with mrio.factor_inputs.name),
            and an instance name 'factor_inputs'.

        Returns
        -------
        Generator for Extension or string

        """
        all_ext_list = [key for key in self.__dict__ if isinstance(self.__dict__[key], Extension)]
        all_name_list = [getattr(self, key).name for key in all_ext_list]

        if isinstance(names, str):
            names = [names]
        _pre_ext = names if names else all_ext_list
        ext_name_or_inst = [nn.name if isinstance(nn, Extension) else nn for nn in _pre_ext]

        for name in ext_name_or_inst:
            if name in all_ext_list:
                inst_name = name
                ext_name = all_name_list[all_ext_list.index(name)]
            elif name in all_name_list:
                inst_name = all_ext_list[all_name_list.index(name)]
                ext_name = name
            else:
                raise ValueError(f"Extension {name} not present in the system.")

            if data:
                yield getattr(self, inst_name)
            else:
                if instance_names:
                    yield inst_name
                else:
                    yield ext_name

    def extension_fullmatch(self, find_all=None, extensions=None, **kwargs):
        """Get a dict of extension index dicts with full match of a search pattern.

        This calls the extension.fullmatch for all extensions.

        Similar to pandas str.fullmatch, thus the start of the index string must match.

        Note:
        -----
        Arguments are set to case=True, flags=0, na=False, regex=True.
        For case insensitive matching, use (?i) at the beginning of the pattern.

        See the pandas/python.re documentation for more details.


        Parameters
        ----------
        find_all : None or str
            If str (regex pattern) search in all index levels.
            All matching rows are returned. The remaining kwargs are ignored.
        extensions: str, list of str, list of extensions, None
            Which extensions to consider, default (None): all extensions
        kwargs : dict
            The regex which should be contained. The keys are the index names,
            the values are the regex.
            If the entry is not in index name, it is ignored silently.

        Returns
        -------
        dict
            A dict with the extension names as keys and an Index/MultiIndex of
            the matched rows as values
        """
        return self._apply_extension_method(extensions, method="match", find_all=find_all, **kwargs)

    def extension_match(self, find_all=None, extensions=None, **kwargs):
        """Get a dict of extension index dicts which match a search pattern.

        This calls the extension.match for all extensions.

        Similar to pandas str.match, thus the start of the index string must match.

        Note:
        -----
        Arguments are set to case=True, flags=0, na=False, regex=True.
        For case insensitive matching, use (?i) at the beginning of the pattern.

        See the pandas/python.re documentation for more details.


        Parameters
        ----------
        find_all : None or str
            If str (regex pattern) search in all index levels.
            All matching rows are returned. The remaining kwargs are ignored.
        extensions: str, list of str, list of extensions, None
            Which extensions to consider, default (None): all extensions
        kwargs : dict
            The regex which should be contained. The keys are the index names,
            the values are the regex.
            If the entry is not in index name, it is ignored silently.

        Returns
        -------
        dict
            A dict with the extension names as keys and an Index/MultiIndex of
            the matched rows as values
        """
        return self._apply_extension_method(extensions, method="match", find_all=find_all, **kwargs)

    def extension_contains(self, find_all=None, extensions=None, **kwargs):
        """Get a dict of extension index dicts which contains a search pattern.

        This calls the extension.contains for all extensions.

        Similar to pandas str.contains, thus the index
        string must contain the regex pattern.

        Note:
        -----
        Arguments are set to case=True, flags=0, na=False, regex=True.
        For case insensitive matching, use (?i) at the beginning of the pattern.

        See the pandas/python.re documentation for more details.


        Parameters
        ----------
        find_all : None or str
            If str (regex pattern) search in all index levels.
            All matching rows are returned. The remaining kwargs are ignored.
        extensions: str, list of str, list of extensions, None
            Which extensions to consider, default (None): all extensions
        kwargs : dict
            The regex which should be contained. The keys are the index names,
            the values are the regex.
            If the entry is not in index name, it is ignored silently.

        Returns
        -------
        dict
            A dict with the extension names as keys and an Index/MultiIndex of
            the matched rows as values
        """
        return self._apply_extension_method(extensions, method="contains", find_all=find_all, **kwargs)

    def extension_extract(
        self,
        index_dict,
        dataframes=None,
        include_empty=False,
        return_type="dataframes",
    ):
        """Extract extension data accross all extensions.

        This calls the extension.extract for all extensions.

        Parameters
        ----------
        index_dict : dict
            A dict with the extension names as keys and the values as the
            corresponding index values. The values can be a single value or a
            list of values.

        dataframes : list, optional
            The dataframes which should be extracted. If None (default),
            all available dataframes are extracted.

        include_empty: boolean, optional
            If True, the returned dict contains keys for all extensions,
            even if no match was found. If False (default), only the
            extensions with non-empty extracted data are returned.

        return_type: str, optional
            If 'dataframe' or 'df' (also with 's' plural, default), the returned dict contains dataframes.
            If 'extensions' or 'ext', the returned dict contains Extension instances.
            Any other string: Return one merged extension with the name set to the
            passed string (this will automatically exclude empty extensions).


        Returns
        -------
        dict
            A dict with the extension names as keys and an Index/MultiIndex of
            the matched rows as values

        """
        if return_type.lower() in ["dataframes", "dataframe", "dfs", "df"]:
            return_as_extension = False
            ext_name = None
        elif return_type.lower() in ["extensions", "extension", "ext", "exts"]:
            return_as_extension = True
            ext_name = None
        else:
            return_as_extension = True
            ext_name = return_type

        extracts = self._apply_extension_method(
            extensions=None,
            method="extract",
            index=index_dict,
            dataframes=dataframes,
            return_type=return_type,
        )

        if (not include_empty) or ext_name:
            if return_as_extension:
                for ext in list(extracts.keys()):
                    if extracts[ext].empty:
                        del extracts[ext]
            else:
                # first remove empty dataframes
                for ext in list(extracts.keys()):
                    for df in list(extracts[ext].keys()):
                        if extracts[ext][df].empty:
                            del extracts[ext][df]
                # second round remove empty extension keys
                for ext in list(extracts.keys()):
                    if not extracts[ext]:
                        del extracts[ext]

        if ext_name:
            return extension_concate(*extracts.values(), new_extension_name=ext_name)
        return extracts

    def _apply_extension_method(self, extensions, method, *args, **kwargs):
        """Apply a method to a list of extensions.

        Parameters
        ----------
        extensions: str, list of str, list of extensions, or None
            Specifies which extensions to consider. Use None to consider all extensions.
        method: str
            Specifies the method to apply.
        args: list
            Specifies the arguments to pass to the method.
        kwargs: dict
            Specifies the keyword arguments to pass to the method.

        Returns
        -------
        dict
            A dict with the extension names as keys and the return values of the
            method as values. The keys are the same as in 'extensions', thus
            convert these to the set names or instance names before (using
            mrio.get_extensions)

        """
        if extensions is None:
            extensions = list(self.get_extensions(data=False, instance_names=False))
        if isinstance(extensions, (Extension, str)):
            extensions = [extensions]

        instance_names = self.get_extensions(names=extensions, data=False, instance_names=True)
        ext_data = self.get_extensions(names=extensions, data=True)

        result = {}
        for ext_name, _inst_name, ext in zip(extensions, instance_names, ext_data):
            method_fun = getattr(ext, method)
            result[ext_name] = method_fun(*args, **kwargs)
        return result

    def reset_full(self, force=False):
        """Remove all accounts which can be recalculated based on Z, Y, F, F_Y.

        Parameters
        ----------
        force: boolean, optional
            If True, reset to flows although the system can not be
            recalculated. Default: False
        """
        super().reset_full(force=force, _meta=self.meta)
        return self

    def reset_all_full(self, force=False):
        """Remove all accounts that can be recalculated (IOSystem and extensions).

        This calls reset_full for the core system and all extension.

        Parameters
        ----------
        force: boolean, optional
            If True, reset to flows although the system can not be
            recalculated. Default: False

        """
        self.reset_full(force=force)
        [ee.reset_full(force=force) for ee in self.get_extensions(data=True)]
        self.meta._add_modify("Reset all calculated data")
        return self

    def reset_extensions(self, force=False):
        """Reset all extensions - preparation for recalculation with a new Y.

        This calls reset_full for all extension.
        If only a specific extension should be recalulated call reset_full on the
        extension directly.

        Parameters
        ----------
        force: boolean, optional
            If True, reset to flows although the system can not be
            recalculated. Default: False

        """
        [ee.reset_full(force=force) for ee in self.get_extensions(data=True)]
        self.meta._add_modify("Reset all extenions data")
        return self

    def reset_to_flows(self, force=False):
        """Keep only the absolute values.

        This removes all attributes which can not be aggregated and must be
        recalculated after the aggregation.

        Parameters
        ----------
        force: boolean, optional
            If True, reset to flows although the system can not be
            recalculated. Default: False
        """
        super().reset_to_flows(force=force, _meta=self.meta)
        return self

    def reset_all_to_flows(self, force=False):
        """Reset the IOSystem and all extensions to absolute flows.

        This method calls reset_to_flows for the IOSystem and for
        all Extensions in the system.

        Parameters
        ----------
        force: boolean, optional
            If True, reset to flows although the system can not be
            recalculated. Default: False

        """
        self.reset_to_flows(force=force)
        [ee.reset_to_flows(force=force) for ee in self.get_extensions(data=True)]
        self.meta._add_modify("Reset full system to absolute flows")
        return self

    def reset_all_to_coefficients(self):
        """Reset the IOSystem and all extensions to coefficients.

        This method calls reset_to_coefficients for the IOSystem and for
        all Extensions in the system

        Note:
        -----
        The system can not be reconstructed after this steps
        because all absolute data is removed. Save the Y data in case
        a reconstruction might be necessary.

        """
        self.reset_to_coefficients()
        [ee.reset_to_coefficients() for ee in self.get_extensions(data=True)]
        self.meta._add_modify("Reset full system to coefficients")
        return self

    def save_all(self, path, table_format="txt", sep="\t", float_format="%.12g"):
        """Save the system and all extensions.

        Extensions are saved in separate folders (names based on extension)

        Parameters are passed to the .save methods of the IOSystem and
        Extensions. See parameters description there.
        """
        path = Path(path)

        path.mkdir(parents=True, exist_ok=True)

        self.save(
            path=path,
            table_format=table_format,
            sep=sep,
            float_format=float_format,
        )

        for ext, ext_name in zip(
            self.get_extensions(data=True),
            self.get_extensions(instance_names=True),
        ):
            ext_path = path / ext_name

            ext.save(
                path=ext_path,
                table_format=table_format,
                sep=sep,
                float_format=float_format,
            )
        return self

    def aggregate_duplicates(self, inplace=True):
        """Aggregate duplicated regions and sectors.

        Alternative approach to aggregate MRIO by renaming sectors/regions
        in place and then adding them together. This works well if used with the included classification schemes.

        Parameters
        ----------
        inplace : boolean, optional
            If True, aggregates the IOSystem in place (default),
            otherwise aggregation happens on a copy of the IOSystem.
            Regardless of the setting, the IOSystem is returned to
            allow for chained operations.

        Returns
        -------
        IOSystem
            Aggregated IOSystem (if inplace is False)

        """
        if not inplace:
            self = self.copy()

        try:
            self.reset_all_to_flows()
        except ResetError as err:
            raise AggregationError("System under-defined for aggregation - do a 'calc_all' before aggregation") from err

        def agg_routine(iodf):
            """Aggregate duplicate columns and rows."""
            _index_names = iodf.index.names
            _columns_names = iodf.columns.names
            if (type(iodf.columns[0]) is not tuple) and iodf.columns[0].lower() == "unit":
                iodf = iodf.groupby(iodf.index, sort=False).first()
            else:
                iodf = iodf.groupby(iodf.index, sort=False).sum().T.groupby(iodf.columns, sort=False).sum().T

            if type(iodf.index[0]) is tuple:
                iodf.index = pd.MultiIndex.from_tuples(iodf.index, names=_index_names)
            if type(iodf.columns[0]) is tuple:
                iodf.columns = pd.MultiIndex.from_tuples(iodf.columns, names=_columns_names)
            return iodf

        for df_to_agg_name in self.get_DataFrame(data=False, with_unit=True):
            self.meta._add_modify(f"Aggregate economic core - {df_to_agg_name}")
            setattr(
                self,
                df_to_agg_name,
                agg_routine(iodf=getattr(self, df_to_agg_name)),
            )

        # Aggregate extension
        for ext in self.get_extensions(data=True):
            for df_to_agg_name in ext.get_DataFrame(data=False, with_unit=False):
                self.meta._add_modify(f"Aggregate extension {ext.name} - {df_to_agg_name}")
                setattr(
                    ext,
                    df_to_agg_name,
                    agg_routine(iodf=getattr(ext, df_to_agg_name)),
                )

        if not inplace:
            return self

    def aggregate(
        self,
        region_agg=None,
        sector_agg=None,
        region_names=None,
        sector_names=None,
        inplace=True,
    ):
        """Aggregate the IO system.

        Aggregation can be given as vector (use pymrio.build_agg_vec) or
        aggregation matrix. In the case of a vector this must be of length
        self.get_regions() / self.get_sectors() respectively with the new
        position as integer or a string of the new name. In the case of
        strings the final output order can be specified in region_dict and
        sector_dict in the format {str1 = int_pos, str2 = int_pos, ...}.

        If the sector / region concordance is given as matrix or numerical
        vector, generic names will be used for the new sectors/regions. One
        can define specific names by defining the aggregation as string
        vector

        Parameters
        ----------
        region_agg : list, array or string, optional
            The aggregation vector or matrix for the regions (np.ndarray or
            list). If string: aggregates to one total region and names is
            to the given string.
            Pandas DataFrame with columns 'original' and 'aggregated'.
            This is the output from the country_converter.agg_conc
        sector_agg : list, arrays or string, optional
            The aggregation vector or matrix for the sectors (np.ndarray or
            list).If string: aggregates to one total region and names is
            to the given string.
        region_names : list, optional
            Names for the aggregated regions.
            If concordance matrix - in order of rows in this matrix
            If concordance vector - in order or num. values in this vector
            If string based - same order as the passed string
            Not considered if passing a DataFrame - in this case give the
            names in the column 'aggregated'

        sector_names : list, optional
            Names for the aggregated sectors. Same behaviour as
            'region_names'

        inplace : boolean, optional
            If True, aggregates the IOSystem in place (default),
            otherwise aggregation happens on a copy of the IOSystem.
            Regardless of the setting, the IOSystem is returned to
            allow for chained operations.

        Returns
        -------
        IOSystem
            Aggregated IOSystem (if inplace is False)

        """
        # Development note: This can not be put in the BaseSystem b/c
        # than the recalculation of the extension coefficients would not
        # work.

        if len(self.unit.squeeze().unique()) > 1:
            raise NotImplementedError("Aggregation not implemented for hybrid tables")

        if not inplace:
            self = self.copy()

        try:
            self.reset_to_flows()
        except ResetError as err:
            raise AggregationError("System under-defined for aggregation - do a 'calc_all' before aggregation") from err

        if type(region_names) is str:
            region_names = [region_names]
        if type(sector_names) is str:
            sector_names = [sector_names]

        if type(region_agg) is pd.DataFrame:
            if ("original" not in region_agg.columns) or ("aggregated" not in region_agg.columns):
                raise ValueError('Passed DataFrame must include the columns "original" and "aggregated"')
            region_agg = (
                region_agg.set_index("original")
                .reindex(self.get_regions(), fill_value=MISSING_AGG_ENTRY["region"])
                .loc[:, "aggregated"]
            )

        if type(sector_agg) is pd.DataFrame:
            if ("original" not in sector_agg.columns) or ("aggregated" not in sector_agg.columns):
                raise ValueError('Passed DataFrame must include the columns "original" and "aggregated"')
            sector_agg = (
                sector_agg.set_index("original")
                .reindex(self.get_sectors(), fill_value=MISSING_AGG_ENTRY["sector"])
                .loc[:, "aggregated"]
            )

        # fill the aggregation matrix with 1:1 mapping
        # if input not given and get names if not given
        _same_regions = False
        _same_sectors = False
        if region_agg is None:
            region_agg = self.get_regions()
            region_names = region_names or self.get_regions()
            _same_regions = True
        if sector_agg is None:
            sector_agg = self.get_sectors()
            sector_names = sector_names or self.get_sectors()
            _same_sectors = True

        # capture total aggregation case
        if type(region_agg) is str:
            region_agg = [region_agg] * len(self.get_regions())
        if type(sector_agg) is str:
            sector_agg = [sector_agg] * len(self.get_sectors())

        if ioutil.is_vector(region_agg):
            region_conc = ioutil.build_agg_matrix(region_agg)
        else:
            region_conc = region_agg
        if ioutil.is_vector(sector_agg):
            sector_conc = ioutil.build_agg_matrix(sector_agg)
        else:
            sector_conc = sector_agg

        # build the new names
        if (not _same_regions) and (not region_names):
            if isinstance(region_agg, np.ndarray):
                region_agg = region_agg.flatten().tolist()
            if type(list(region_agg)[0]) is str:
                region_names = ioutil.unique_element(region_agg)
            else:
                # rows in the concordance matrix give the new number of
                # regions
                region_names = [GENERIC_NAMES["region"] + str(nr) for nr in range(region_conc.shape[0])]

        if (not _same_sectors) and (not sector_names):
            if isinstance(sector_agg, np.ndarray):
                sector_agg = sector_agg.flatten().tolist()
            if type(list(sector_agg)[0]) is str:
                sector_names = ioutil.unique_element(sector_agg)
            else:
                sector_names = [GENERIC_NAMES["sector"] + str(nr) for nr in range(sector_conc.shape[0])]

        # Assert right shapes
        if not sector_conc.shape[1] == len(self.get_sectors()):
            raise ValueError("Sector aggregation does not correspond to the number of sectors.")
        if not region_conc.shape[1] == len(self.get_regions()):
            raise ValueError("Region aggregation does not correspond to the number of regions.")
        if not len(sector_names) == sector_conc.shape[0]:
            raise ValueError("New sector names do not match sector aggregation.")
        if not len(region_names) == region_conc.shape[0]:
            raise ValueError("New region names do not match region aggregation.")

        # build pandas.MultiIndex for the aggregated system
        _reg_list_for_sec = [[r] * sector_conc.shape[0] for r in region_names]
        _reg_list_for_sec = [entry for entrylist in _reg_list_for_sec for entry in entrylist]

        _reg_list_for_Ycat = [[r] * len(self.get_Y_categories()) for r in region_names]
        _reg_list_for_Ycat = [entry for entrylist in _reg_list_for_Ycat for entry in entrylist]

        _sec_list = list(sector_names) * region_conc.shape[0]
        _Ycat_list = list(self.get_Y_categories()) * region_conc.shape[0]

        mi_reg_sec = pd.MultiIndex.from_arrays([_reg_list_for_sec, _sec_list], names=["region", "sector"])
        mi_reg_Ycat = pd.MultiIndex.from_arrays([_reg_list_for_Ycat, _Ycat_list], names=["region", "category"])

        # arrange the whole concordance matrix
        conc = np.kron(region_conc, sector_conc)
        conc_y = np.kron(region_conc, np.eye(len(self.get_Y_categories())))

        # Aggregate
        self.meta._add_modify("Aggregate final demand y")
        self.Y = pd.DataFrame(
            data=conc.dot(self.Y).dot(conc_y.T),
            index=mi_reg_sec,
            columns=mi_reg_Ycat,
        )

        self.meta._add_modify("Aggregate transaction matrix Z")
        self.Z = pd.DataFrame(
            data=conc.dot(self.Z).dot(conc.T),
            index=mi_reg_sec,
            columns=mi_reg_sec,
        )

        if self.x is not None:
            # x could also be obtained from the
            # aggregated Z, but aggregate if available
            self.x = pd.DataFrame(
                data=conc.dot(self.x),
                index=mi_reg_sec,
                columns=self.x.columns,
            )
            self.meta._add_modify("Aggregate industry output x")
        else:
            self.x = calc_x(self.Z, self.Y)

        if self.population is not None:
            self.meta._add_modify("Aggregate population vector")
            self.population = pd.DataFrame(
                data=region_conc.dot(self.population.T).T,
                columns=region_names,
                index=self.population.index,
            )

        # NOTE: this fails for none consistent units (hybrid tables)
        try:
            _value = self.unit.iloc[0].tolist()[0]
            self.unit = pd.DataFrame(
                index=self.Z.index,
                columns=self.unit.columns,
                data=_value,
            )
        except AttributeError:
            # could fail if no unit available
            self.unit = None

        for extension in self.get_extensions(data=True):
            self.meta._add_modify("Aggregate extensions...")
            extension.reset_to_flows()
            st_redo_unit = False
            for ik_name, ik_df in zip(
                extension.get_DataFrame(data=False, with_unit=False),
                extension.get_DataFrame(data=True, with_unit=False),
            ):
                # Without unit - this is reset aftwards if necessary
                if ik_df.index.names == ["region", "sector"] == ik_df.columns.names:
                    # Full disaggregated extensions - aggregate both axis
                    # (this is the case if the extions shows the flows from
                    # pda to cba)
                    extension.__dict__[ik_name] = pd.DataFrame(data=conc.dot(ik_df).dot(conc.T))

                    # next step must be done afterwards due to unknown reasons
                    extension.__dict__[ik_name].columns = mi_reg_sec
                    extension.__dict__[ik_name].index = mi_reg_sec
                    st_redo_unit = True
                elif ik_df.index.names == [
                    "region",
                    "sector",
                ] and ik_df.columns.names == ["region", "category"]:
                    # Full disaggregated finald demand satellite account.
                    # Thats not implemented yet - but aggregation is in place
                    extension.__dict__[ik_name] = pd.DataFrame(data=conc.dot(ik_df).dot(conc_y.T))
                    # next step must be done afterwards due to unknown reasons
                    extension.__dict__[ik_name].columns = mi_reg_Ycat
                    extension.__dict__[ik_name].index = mi_reg_sec

                elif ik_df.columns.names == ["region", "category"]:
                    # Satellite account connected to final demand (e.g. F_Y)
                    extension.__dict__[ik_name] = pd.DataFrame(data=ik_df.dot(conc_y.T))
                    # next step must be done afterwards due to unknown reasons
                    extension.__dict__[ik_name].columns = mi_reg_Ycat
                    extension.__dict__[ik_name].index = ik_df.index

                else:
                    # Standard case - aggregated columns, keep stressor rows
                    extension.__dict__[ik_name] = pd.DataFrame(data=ik_df.dot(conc.T))
                    # next step must be done afterwards due to unknown reasons
                    extension.__dict__[ik_name].columns = mi_reg_sec
                    extension.__dict__[ik_name].index = ik_df.index

                if st_redo_unit:
                    # NOTE: this fails for none consistent units
                    try:
                        _value = extension.unit.iloc[0].tolist()[0]
                        extension.unit = pd.DataFrame(
                            index=mi_reg_sec,
                            columns=extension.unit.columns,
                            data=_value,
                        )
                    except AttributeError:
                        # could fail if no unit available
                        extension.unit = None
        self.calc_extensions()
        return self

    def remove_extension(self, ext):
        """Remove extension from IOSystem.

        For single Extensions the same can be achieved with del
        IOSystem_name.Extension_name

        Parameters
        ----------
        ext : string or list, optional
            The extension to remove, this can be given as the name of the
            instance or of Extension.name.
            instance was found)
        """
        # TODO: rename to extension_remove
        if type(ext) is str:
            ext = [ext]

        for ee in ext:
            try:
                del self.__dict__[ee]
                self.meta._add_modify(f"Removed extension {ee}")
            except KeyError:
                ext_instance = self.get_extensions(ee, instance_names=True)
                for x in ext_instance:
                    del self.__dict__[x]
                    self.meta._add_modify(f"Removed extension {x}")

        return self

    def extension_convert(
        self,
        df_map,
        new_extension_name,
        extension_col_name="extension",
        agg_func="sum",
        drop_not_bridged_index=True,
        unit_column_orig="unit_orig",
        unit_column_new="unit_new",
        ignore_columns=None,
        reindex=None,
    ):
        """Apply the convert function to the extensions of the mrio object.

        Internally that calls the Extension.convert function for all extensions.

        If only a subset of extensions should/can be converted, use
        the pymrio.extension_convert function.

        Parameters
        ----------
        df_map : pd.DataFrame
            The DataFrame with the mapping of the old to the new classification.
            This requires a specific structure:

            - Constraining data (e.g. stressors, regions, sectors) can be
              either in the index or columns of df_orig. The need to have the
              same name as the named index or column in df_orig. The algorithm
              searches for matching data in df_orig based on all constraining
              columns in df_map.

            - Bridge columns are columns with '__' in the name. These are used
              to map (bridge) some/all of the constraining columns in df_orig
              to the new classification.

            - One column "factor", which gives the multiplication factor for
              the conversion. If it is missing, it is set to 1.

            This is better explained with an example.

            Assuming a original dataframe df_orig with
            index names 'stressor' and 'compartment' and column name 'region',
            the characterizing dataframe could have the following structure (column names):

            - stressor: original index name

            - compartment: original index name

            - region: original column name

            - factor: the factor for multiplication/characterization
                If no factor is given, the factor is assumed to be 1.
                This can be used, to simplify renaming/aggregation mappings.

            - impact__stressor: the new index name,
                replacing the previous index name "stressor".
                Thus here "stressor" will be renamed to "impact", and the row index
                will be renamed by the entries here.

            - compartment__compartment: the new compartment,
                replacing the original compartment. No rename of column happens here,
                still row index will be renamed as given here.

            The columns with __ are called bridge columns, they are used
            to match the original index. The new dataframe with have index names
            based on the first part of the bridge column, in the order
            in which the bridge columns are given in the mapping dataframe.

            "region" is constraining column, these can either be for the index or column
            in df_orig. In case both exist, the one in index is preferred.

        extension_name: str
            The name of the new extension returned

        extension_col_name : str, optional
            Name of the column specifying the extension name in df_map.
            The entry in df_map here can either be the name returned by Extension.name or the
            name of the Extension instance.
            Default: 'extension'

        agg_func : str or func
            the aggregation function to use for multiple matchings (summation by default)

        drop_not_bridged_index : bool, optional
            What to do with index levels in df_orig not appearing in the bridge columns.
            If True, drop them after aggregation across these, if False,
            pass them through to the result.

            *Note:* Only index levels will be dropped, not columns.

            In case some index levels need to be dropped, and some not
            make a bridge column for the ones to be dropped and map all to the same name.
            Then drop this index level after the conversion.

        unit_column_orig : str, optional
            Name of the column in df_map with the original unit.
            This will be used to check if the unit matches the original unit in the extension.
            Default is "unit_orig", if None, no check is performed.

        unit_column_new : str, optional
            Name of the column in df_map with the new unit to be assigned to the new extension.
            Default is "unit_new", if None same unit as in df_orig TODO EXPLAIN BETTER, THINK WARNING

        ignore_columns : list, optional
            List of column names in df_map which should be ignored.
            These could be columns with additional information, etc.
            The unit columns given in unit_column_orig and unit_column_new
            are ignored by default.

        reindex: str, None or collection
            Wrapper for pandas' reindex method to control return order.
            - If None: sorts the index alphabetically.
            - If str: uses the unique value order from the specified bridge column as the index order.
            - For other types (e.g., collections): passes directly to pandas.reindex.


        """
        return extension_convert(
            *list(self.get_extensions(data=True)),
            df_map=df_map,
            new_extension_name=new_extension_name,
            extension_col_name=extension_col_name,
            agg_func=agg_func,
            drop_not_bridged_index=drop_not_bridged_index,
            unit_column_orig=unit_column_orig,
            unit_column_new=unit_column_new,
            ignore_columns=ignore_columns,
            reindex=reindex,
        )

    def extension_characterize(
        self,
        factors,
        new_extension_name="impacts",
        extension_col_name="extension",
        characterized_name_column="impact",
        characterization_factors_column="factor",
        characterized_unit_column="impact_unit",
        orig_unit_column="stressor_unit",
        only_validation=False,
    ):
        """Characterize stressors across all extensions of the mrio object.

        If only a subset of extensions should be considered, use
        the pymrio.extension_characterize function.

        The factors dataframe must include an columns "extension"
        which specifies the 'name' of the extension in which the stressor is
        present. The 'name' is the str returned by ext.name

        For more information on the structure of the factors dataframe
        see the Extension.characterize docstring.

        Validation behaviour is consistent with Extension.characterize and
        the validation is applied to a temporary merged extension with all
        stressors.

        Parameters
        ----------
        factors: pd.DataFrame
            A dataframe in long format with numerical index and columns named
            index.names of the extension to be characterized and 'extension',
            'characterized_name_column', 'characterization_factors_column',
            'characterized_unit_column', 'orig_unit_column'

        extension_name: str
            The name of the new extension returned

        extension_col_name : str, optional
            Name of the column specifying the extension name in df_map.
            The entry in df_map here can either be the name returned by Extension.name or the
            name of the Extension instance.
            Default: 'extension'

        characterized_name_column: str (optional)
            Name of the column with the names of the
            characterized account (default: "impact")

        characterization_factors_column: str (optional)
            Name of the column with the factors for the
            characterization (default: "factor")

        characterized_unit_column: str (optional)
            Name of the column with the units of the characterized accounts
            characterization (default: "impact_unit")

        name: string (optional)
            The new name for the extension,
            if the string starts with an underscore '_' the string
            with be appended to the original name. Default: '_characterized'


        Returns
        -------
        pymrio.Extension


        """
        return extension_characterize(
            *list(self.get_extensions(data=True)),
            factors=factors,
            new_extension_name=new_extension_name,
            extension_col_name=extension_col_name,
            characterized_name_column=characterized_name_column,
            characterization_factors_column=characterization_factors_column,
            characterized_unit_column=characterized_unit_column,
            orig_unit_column=orig_unit_column,
            only_validation=only_validation,
        )

    def extension_concate(self, new_extension_name):
        """Concates all extension of the mrio object.

        This method combines all satellite accounts into a single extension.

        The method assumes that the first index is the name of the
        stressor/impact/input type. To provide a consistent naming this is renamed
        to 'indicator' if they differ. All other index names ('compartments', ...)
        are added to the concatenated extensions and set to NaN for missing values.

        If only a subset of extensions should/can be merge, use
        the pymrio.extension_concate function.


        Parameters
        ----------
        new_extension_name : str
            Name for the new extension

        Returns
        -------
        pymrio.Extension


        """
        return extension_concate(*list(self.get_extensions(data=True)), new_extension_name=new_extension_name)


def extension_characterize(
    *extensions,
    factors,
    new_extension_name="impacts",
    extension_col_name="extension",
    characterized_name_column="impact",
    characterization_factors_column="factor",
    characterized_unit_column="impact_unit",
    only_validation=False,
    orig_unit_column="stressor_unit",
):
    """Characterize stressors across different extensions.

    This works similar to the characterize method of a specific
    extension.

    The factors dataframe must include an columns "extension"
    which specifies the 'name' of the extension in which the stressor is
    present. The 'name' is the str returned by ext.name

    For more information on the structure of the factors dataframe
    see the Extension.characterize docstring.

    Validation behaviour is consistent with Extension.characterize and
    the validation is applied to a temporary merged extension with all
    stressors.


    Parameters
    ----------
    extensions : list of extensions
        Extensions to convert. All extensions passed must have the same index names/format.

    factors: pd.DataFrame
        A dataframe in long format with numerical index and columns named
        index.names of the extension to be characterized and 'extension',
        'characterized_name_column', 'characterization_factors_column',
        'characterized_unit_column', 'orig_unit_column'

    extension_name: str
        The name of the new extension returned

    extension_col_name : str, optional
        Name of the column specifying the extension name in df_map.
        The entry in df_map here can either be the name returned by Extension.name or the
        name of the Extension instance.
        Default: 'extension'

    characterized_name_column: str (optional)
        Name of the column with the names of the
        characterized account (default: "impact")

    characterization_factors_column: str (optional)
        Name of the column with the factors for the
        characterization (default: "factor")

    characterized_unit_column: str (optional)
        Name of the column with the units of the characterized accounts
        characterization (default: "impact_unit")

    name: string (optional)
        The new name for the extension,
        if the string starts with an underscore '_' the string
        with be appended to the original name. Default: '_characterized'


    Returns
    -------
    pymrio.Extension


    """
    if extension_col_name not in factors.columns:
        raise ValueError("The factors dataframe must include the column 'extension'")

    if type(extensions) is Extension:
        extensions = [extensions]
    elif type(extensions) is tuple:
        extensions = list(extensions)

    given_ext_names = [ext.name for ext in extensions]
    spec_ext_names = factors.loc[:, extension_col_name].unique()

    for spec_name in spec_ext_names:
        if spec_name not in given_ext_names:
            raise ValueError(f"Extension {spec_name} not found in the passed extensions.")

    used_ext = [ext for ext in extensions if ext.name in spec_ext_names]

    ext_specs = pd.DataFrame(
        index=spec_ext_names,
        columns=["F", "F_Y", "S_Y", "S", "unit", "index_names"],
        data=None,
    )

    for ext in used_ext:
        for df_name in ext.get_DataFrame(data=False):
            ext_specs.loc[ext.name, df_name] = True
            ext_specs.loc[ext.name, "index_names"] = str(ext.get_rows().names)
            ext_index_names = list(ext.get_rows().names)

    if len(ext_specs.loc[:, "index_names"].unique()) > 1:
        raise ValueError("All extensions must have the same index names/format.")

    merge_type = "none"
    if all(ext_specs.loc[:, "F"]):
        merge_type = "F"
    elif all(ext_specs.loc[:, "S"]):
        merge_type = "S"
    else:
        raise ValueError("All extensions must have either F or S.")

    faci = factors.set_index(ext_index_names + [extension_col_name])
    faci = faci[~faci.index.duplicated(keep="first")]
    faci = faci.reset_index(extension_col_name)

    if any(faci.index.duplicated()):
        raise NotImplementedError("Case with same stressor names in different extensions not implemented yet")

    merge = []
    merge_Y = []
    merge_unit = []
    for ext in used_ext:
        ext_df = getattr(ext, merge_type)
        req_rows = faci[faci.loc[:, extension_col_name] == ext.name].index
        avail_rows = ext_df.index
        used_rows = req_rows.intersection(avail_rows)
        merge.append(ext_df.loc[used_rows])
        merge_unit.append(ext.unit.loc[used_rows])
        try:
            ext_df_Y = getattr(ext, merge_type + "_Y")
            merge_Y.append(ext_df_Y.loc[used_rows])
        except AttributeError:
            pass

    new_ext = Extension(
        name="temp",
        unit=pd.concat(merge_unit, axis=0),
    )
    setattr(new_ext, merge_type, pd.concat(merge, axis=0))
    if len(merge_Y) > 0:
        setattr(new_ext, merge_type + "_Y", pd.concat(merge_Y, axis=0))

    char = new_ext.characterize(
        factors=factors.drop(extension_col_name, axis=1),
        name=new_extension_name,
        only_validation=only_validation,
        characterized_name_column=characterized_name_column,
        characterization_factors_column=characterization_factors_column,
        characterized_unit_column=characterized_unit_column,
        orig_unit_column=orig_unit_column,
    )
    return char


def extension_convert(
    *extensions,
    df_map,
    new_extension_name,
    extension_col_name="extension",
    agg_func="sum",
    drop_not_bridged_index=True,
    unit_column_orig="unit_orig",
    unit_column_new="unit_new",
    ignore_columns=None,
    reindex=None,
):
    """Apply the convert function to a list of extensions.

    Internally that calls the Extension.convert function for all extensions.


    Parameters
    ----------
    extensions : list of extensions
        Extensions to convert. All extensions passed must
        have an index structure (index names) as described in df_map.

    df_map : pd.DataFrame
        The DataFrame with the mapping of the old to the new classification.
        This requires a specific structure:

        - Constraining data (e.g. stressors, regions, sectors) can be either
          in the index or columns of df_orig. The need to have the same name
          as the named index or column in df_orig. The algorithm searches for
          matching data in df_orig based on all constraining columns in
          df_map.

        - Bridge columns are columns with '__' in the name. These are used to
          map (bridge) some/all of the constraining columns in df_orig to the
          new classification.

        - One column "factor", which gives the multiplication factor for the
          conversion. If it is missing, it is set to 1.

        This is better explained with an example.

        Assuming a original dataframe df_orig with
        index names 'stressor' and 'compartment' and column name 'region',
        the characterizing dataframe could have the following structure (column names):

        - stressor: original index name

        - compartment: original index name

        - region: original column name

        - factor: the factor for multiplication/characterization
            If no factor is given, the factor is assumed to be 1.
            This can be used, to simplify renaming/aggregation mappings.

        - impact__stressor: the new index name,
            replacing the previous index name "stressor".
            Thus here "stressor" will be renamed to "impact", and the row index
            will be renamed by the entries here.

        - compartment__compartment: the new compartment,
            replacing the original compartment. No rename of column happens here,
            still row index will be renamed as given here.

        The columns with __ are called bridge columns, they are used
        to match the original index. The new dataframe with have index names
        based on the first part of the bridge column, in the order
        in which the bridge columns are given in the mapping dataframe.


        "region" is constraining column, these can either be for the index or column
        in df_orig. In case both exist, the one in index is preferred.

    extension_name: str
        The name of the new extension returned

    extension_col_name : str, optional
        Name of the column specifying the extension name in df_map.
        The entry in df_map here can either be the name returned by Extension.name or the
        name of the Extension instance.
        Default: 'extension'

    agg_func : str or func
        the aggregation function to use for multiple matchings (summation by default)

    drop_not_bridged_index : bool, optional
        What to do with index levels in df_orig not appearing in the bridge columns.
        If True, drop them after aggregation across these, if False,
        pass them through to the result.

        *Note:* Only index levels will be dropped, not columns.

        In case some index levels need to be dropped, and some not
        make a bridge column for the ones to be dropped and map all to the same name.
        Then drop this index level after the conversion.

    unit_column_orig : str, optional
        Name of the column in df_map with the original unit.
        This will be used to check if the unit matches the original unit in the extension.
        Default is "unit_orig", if None, no check is performed.

    unit_column_new : str, optional
        Name of the column in df_map with the new unit to be assigned to the new extension.
        Default is "unit_new", if None same unit as in df_orig TODO EXPLAIN BETTER, THINK WARNING

    ignore_columns : list, optional
        List of column names in df_map which should be ignored.
        These could be columns with additional information, etc.
        The unit columns given in unit_column_orig and unit_column_new
        are ignored by default.

    reindex: str, None or collection
        Wrapper for pandas' reindex method to control return order.
        - If None: sorts the index alphabetically.
        - If str: uses the unique value order from the specified bridge column as the index order.
        - For other types (e.g., collections): passes directly to pandas.reindex.


    """
    if type(extensions) is Extension:
        extensions = [extensions]
    elif type(extensions) is tuple:
        extensions = list(extensions)

    if not ignore_columns:
        ignore_columns = []
    ignore_columns.append(extension_col_name)

    gather = []

    for ext in extensions:
        if ext.name not in df_map[extension_col_name].unique():
            warnings.warn(
                f"Extension {ext.name} not found in df_map. Skipping extension.",
                stacklevel=2,
            )
            # TODO: later go to logging
            continue
        gather.append(
            ext.convert(
                df_map=df_map[df_map[extension_col_name] == ext.name],
                agg_func=agg_func,
                new_extension_name=new_extension_name,
                drop_not_bridged_index=drop_not_bridged_index,
                unit_column_orig=unit_column_orig,
                unit_column_new=unit_column_new,
                ignore_columns=ignore_columns,
                reindex=reindex,
            )
        )

    result_ext = extension_concate(*gather, new_extension_name=new_extension_name)

    # Need to reindex again, as the order might be mixed up by the
    # order of the extensions
    if type(reindex) is str:
        group_order = df_map.loc[:, reindex].unique()
    elif reindex is None:
        group_order = None
    else:
        group_order = reindex

    for df, df_name in zip(
        result_ext.get_DataFrame(data=True, with_unit=True),
        result_ext.get_DataFrame(data=False, with_unit=True),
    ):
        if df_name == "unit":
            df_result = df.groupby(level=df.index.names).agg(lambda x: ",".join(set(x)))
        else:
            df_result = df.groupby(level=df.index.names, sort=False).agg(agg_func)
        if group_order is not None:
            df_result = df_result.reindex(group_order)
        setattr(
            result_ext,
            df_name,
            df_result,
        )

    return result_ext


def extension_concate(*extensions, new_extension_name):
    """Concatenate extensions.

    Notes
    -----
    The method assumes that the first index is the name of the
    stressor/impact/input type. To provide a consistent naming this is renamed
    to 'indicator' if they differ. All other index names ('compartments', ...)
    are added to the concatenated extensions and set to NaN for missing values.

    Notes
    -----
    Attributes which are not DataFrames will be set to None if they differ
    between the extensions

    Parameters
    ----------
    extensions : Extensions
        The Extensions to concatenate as multiple parameters

    new_extension_name : string
        Name of the new extension

    Returns
    -------
    Concatenated extension

    """
    if type(extensions[0]) is tuple or type(extensions[0]) is list:
        extensions = extensions[0]

    # check if fd extensions is present in one of the given extensions
    F_Y_present = False
    S_Y_present = False
    SF_Y_columns = None
    for ext in extensions:
        if "F_Y" in ext.get_DataFrame(data=False):
            F_Y_present = True
            SF_Y_columns = ext.F_Y.columns
        if "S_Y" in ext.get_DataFrame(data=False):
            S_Y_present = True
            SF_Y_columns = ext.S_Y.columns

    # get the intersection of the available dataframes
    set_dfs = [set(ext.get_DataFrame(data=False)) for ext in extensions]
    df_dict = dict.fromkeys(set.intersection(*set_dfs))
    if F_Y_present:
        df_dict["F_Y"] = None
    if S_Y_present:
        df_dict["S_Y"] = None
    empty_df_dict = df_dict.copy()
    attr_dict = {}

    # get data from each extension
    first_run = True
    for ext in extensions:
        # get corresponding attributes of all extensions
        for key in ext.__dict__:
            if type(ext.__dict__[key]) is not pd.DataFrame:
                if attr_dict.get(key, -99) == -99:
                    attr_dict[key] = ext.__dict__[key]
                elif attr_dict[key] == ext.__dict__[key]:
                    continue
                else:
                    attr_dict[key] = None

        # get DataFrame data
        cur_dict = empty_df_dict.copy()

        for df in cur_dict:
            cur_dict[df] = getattr(ext, df)

        # add zero final demand extension if final demand extension present in
        # one extension
        if F_Y_present:
            # doesn't work with getattr b/c F_Y can be present as attribute but
            # not as DataFrame
            if "F_Y" in ext.get_DataFrame(data=False):
                cur_dict["F_Y"] = ext.F_Y
            else:
                cur_dict["F_Y"] = pd.DataFrame(data=0, index=ext.get_index(), columns=SF_Y_columns)
        if S_Y_present:
            # doesn't work with getattr b/c S_Y can be present as attribute but
            # not as DataFrame
            if "S_Y" in ext.get_DataFrame(data=False):
                cur_dict["S_Y"] = ext.S_Y
            else:
                cur_dict["S_Y"] = pd.DataFrame(data=0, index=ext.get_index(), columns=SF_Y_columns)

        # append all df data
        for key in cur_dict:
            if not first_run:
                if cur_dict[key].index.names != df_dict[key].index.names:
                    cur_ind_names = list(cur_dict[key].index.names)
                    df_ind_names = list(df_dict[key].index.names)
                    cur_ind_names[0] = "indicator"
                    df_ind_names[0] = cur_ind_names[0]
                    cur_dict[key].index = cur_dict[key].index.set_names(cur_ind_names)
                    df_dict[key].index = df_dict[key].index.set_names(df_ind_names)

                    for ind in cur_ind_names:
                        if ind not in df_ind_names:
                            df_dict[key] = df_dict[key].set_index(
                                pd.DataFrame(
                                    data=None,
                                    index=df_dict[key].index,
                                    columns=[ind],
                                )[ind],
                                append=True,
                            )
                    for ind in df_ind_names:
                        if ind not in cur_ind_names:
                            cur_dict[key] = cur_dict[key].set_index(
                                pd.DataFrame(
                                    data=None,
                                    index=cur_dict[key].index,
                                    columns=[ind],
                                )[ind],
                                append=True,
                            )

            df_dict[key] = pd.concat([df_dict[key], cur_dict[key]])

        first_run = False

        all_dict = dict(list(attr_dict.items()) + list(df_dict.items()))
        all_dict["name"] = new_extension_name

    return Extension(**all_dict)
