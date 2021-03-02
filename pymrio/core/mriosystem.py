"""
Generic classes for pymrio

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
import warnings
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import pymrio.tools.ioutil as ioutil
from pymrio.core.constants import DEFAULT_FILE_NAMES, GENERIC_NAMES, MISSING_AGG_ENTRY
from pymrio.tools.iomath import (
    calc_A,
    calc_accounts,
    calc_F,
    calc_F_Y,
    calc_L,
    calc_M,
    calc_S,
    calc_S_Y,
    calc_x,
    calc_x_from_L,
    calc_Z,
    recalc_M,
)
from pymrio.tools.iometadata import MRIOMetaData


# internal functions
def _warn_deprecation(message):  # pragma: no cover
    warnings.warn(message, DeprecationWarning, stacklevel=2)


# Exceptions
class ResetError(Exception):
    """ Base class for errors while reseting the system"""

    pass


class AggregationError(Exception):
    """ Base class for errors while reseting the system"""

    pass


class ResetWarning(UserWarning):
    """ Base class for errors while reseting the system"""

    pass


# Abstract classes
class CoreSystem:
    """This class is the base class for IOSystem and Extension

    Note
    ----
    Thats is only a base class - do not make an instance of this class.

    """

    def __str__(self, startstr="System with: "):
        parastr = ", ".join(
            [
                attr
                for attr in self.__dict__
                if self.__dict__[attr] is not None and "__" not in attr
            ]
        )
        return startstr + parastr

    def __eq__(self, other):
        """ Only the dataframes are compared. """
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
        """Remove all accounts which can be recalculated based on Z, Y, F, F_Y

        Parameters
        ----------

        force: boolean, optional
            If True, reset to flows although the system can not be
            recalculated. Default: False

        _meta: MRIOMetaData, optional
            Metadata handler for logging, optional. Internal

        """
        # Attriubtes to keep must be defined in the init: __basic__
        strwarn = None
        for df in self.__basic__:
            if (getattr(self, df)) is None:
                if force:
                    strwarn = (
                        "Reset system warning - Recalculation after "
                        "reset not possible "
                        "because {} missing".format(df)
                    )
                    warnings.warn(strwarn, ResetWarning)

                else:
                    raise ResetError(
                        "To few tables to recalculate the "
                        "system after reset ({} missing) "
                        "- reset can be forced by passing "
                        "'force=True')".format(df)
                    )

        if _meta:
            _meta._add_modify("Reset system to Z and Y")
            if strwarn:
                _meta._add_modify(strwarn)

        [
            setattr(self, key, None)
            for key in self.get_DataFrame(
                data=False, with_unit=False, with_population=False
            )
            if key not in self.__basic__
        ]
        return self

    def reset_to_flows(self, force=False, _meta=None):
        """Keeps only the absolute values.

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
            if (getattr(self, df)) is None:
                if force:
                    strwarn = (
                        "Reset system warning - Recalculation after "
                        "reset not possible "
                        "because {} missing".format(df)
                    )
                    warnings.warn(strwarn, ResetWarning)

                else:
                    raise ResetError(
                        "To few tables to recalculate the "
                        "system after reset ({} missing) "
                        "- reset can be forced by passing "
                        "'force=True')".format(df)
                    )

        if _meta:
            _meta._add_modify("Reset to absolute flows")
            if strwarn:
                _meta._add_modify(strwarn)

        [setattr(self, key, None) for key in self.__non_agg_attributes__]
        return self

    def reset_to_coefficients(self):
        """Keeps only the coefficient.

        This can be used to recalculate the IO tables for a new finald demand.

        Note
        -----

        The system can not be reconstructed after this steps
        because all absolute data is removed. Save the Y data in case
        a reconstruction might be necessary.

        """
        # Development note: The coefficient attributes are
        # defined in self.__coefficients__
        [
            setattr(self, key, None)
            for key in self.get_DataFrame(
                data=False, with_unit=False, with_population=False
            )
            if key not in self.__coefficients__
        ]
        return self

    def copy(self, new_name=None):
        """Returns a deep copy of the system

        Parameters
        -----------

        new_name: str, optional
            Set a new meta name parameter.
            Default: <old_name>_copy
        """
        _tmp = copy.deepcopy(self)
        if not new_name:
            new_name = self.name + "_copy"
        if str(type(self)) == "<class 'pymrio.core.mriosystem.IOSystem'>":
            _tmp.meta.note(
                "IOSystem copy {new} based on {old}".format(
                    new=new_name, old=self.meta.name
                )
            )
            _tmp.meta.change_meta("name", new_name, log=False)
        else:
            _tmp.name = new_name
        return _tmp

    def get_Y_categories(self, entries=None):
        """Returns names of y cat. of the IOSystem as unique names in order

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
                    ind = (
                        getattr(self, df).columns.get_level_values("category").unique()
                    )
                except (AssertionError, KeyError):
                    ind = getattr(self, df).columns.get_level_values(1).unique()
                if entries:
                    if type(entries) is str:
                        entries = [entries]
                    ind = ind.tolist()
                    return [None if ee not in entries else ee for ee in ind]
                else:
                    return ind
        else:  # pragma: no cover
            logging.warn("No attributes available to get Y categories")
            return None

    def get_index(self, as_dict=False, grouping_pattern=None):
        """Returns the index of the DataFrames in the system

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
            logging.warn("No attributes available to get index")
            return None

        if as_dict:
            dd = {k: k for k in orig_idx}
            if grouping_pattern:
                for pattern, new_group in grouping_pattern.items():
                    if type(pattern) is str:
                        dd.update(
                            {
                                k: new_group
                                for k, v in dd.items()
                                if re.match(pattern, k)
                            }
                        )
                    else:
                        dd.update(
                            {
                                k: new_group
                                for k, v in dd.items()
                                if all(
                                    [
                                        re.match(pat, k[nr])
                                        for nr, pat in enumerate(pattern)
                                    ]
                                )
                            }
                        )
            return dd

        else:
            return orig_idx

    def set_index(self, index):
        """Sets the pd dataframe index of all dataframes in the system to index"""
        for df in self.get_DataFrame(data=True, with_population=False):
            df.index = index

    def get_regions(self, entries=None):
        """Returns the names of regions in the IOSystem as unique names in order

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
                else:
                    return ind
        else:  # pragma: no cover
            logging.warn("No attributes available to get regions")
            return None

    def get_sectors(self, entries=None):
        """Names of sectors in the IOSystem as unique names in order

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
                else:
                    return ind
        else:  # pragma: no cover
            logging.warn("No attributes available to get sectors")
            return None

    def get_DataFrame(self, data=False, with_unit=True, with_population=True):
        """Yields all panda.DataFrames or there names

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

    def save(
        self, path, table_format="txt", sep="\t", table_ext=None, float_format="%.12g"
    ):
        """Saving the system to path


        Parameters
        ----------
        path : pathlib.Path or string
            path for the saved data (will be created if necessary, data
            within will be overwritten).

        table_format : string
            Format to save the DataFrames:

                - 'pkl' : Binary pickle files,
                          alias: 'pickle', 'bin', 'binary'
                - 'txt' : Text files (default), alias: 'text', 'csv'

        table_ext : string, optional
            File extension,
            default depends on table_format(.pkl for pickle, .txt for text)

        sep : string, optional
            Field delimiter for the output file, only for txt files.
            Default: tab ('\t')

        float_format : string, optional
            Format for saving the DataFrames,
            default = '%.12g', only for txt files
        """

        path = Path(path)

        path.mkdir(parents=True, exist_ok=True)

        para_file_path = path / DEFAULT_FILE_NAMES["filepara"]
        file_para = dict()
        file_para["files"] = dict()

        if table_format in ["text", "csv", "txt"]:
            table_format = "txt"
        elif table_format in ["pickle", "bin", "binary", "pkl"]:
            table_format = "pkl"
        else:
            raise ValueError(
                'Unknown table format "{}" - '
                'must be "txt" or "pkl"'.format(table_format)
            )

        if not table_ext:
            if table_format == "txt":
                table_ext = ".txt"
            if table_format == "pkl":
                table_ext = ".pkl"

        if str(type(self)) == "<class 'pymrio.core.mriosystem.IOSystem'>":
            file_para["systemtype"] = GENERIC_NAMES["iosys"]
        elif str(type(self)) == "<class 'pymrio.core.mriosystem.Extension'>":
            file_para["systemtype"] = GENERIC_NAMES["ext"]
            file_para["name"] = self.name
        else:
            logging.warn(
                'Unknown system type {} - set to "undef"'.format(str(type(self)))
            )
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

            save_file = df_name + table_ext
            save_file_with_path = path / save_file
            logging.info("Save file {}".format(save_file_with_path))
            if table_format == "txt":
                df.to_csv(save_file_with_path, sep=sep, float_format=float_format)
            else:
                df.to_pickle(save_file_with_path)

            file_para["files"][df_name] = dict()
            file_para["files"][df_name]["name"] = save_file
            file_para["files"][df_name]["nr_index_col"] = str(nr_index_col)
            file_para["files"][df_name]["nr_header"] = str(nr_header)

        with para_file_path.open(mode="w") as pf:
            json.dump(file_para, pf, indent=4)

        if file_para["systemtype"] == GENERIC_NAMES["iosys"]:
            if not self.meta:
                self.meta = MRIOMetaData(name=self.name, location=path)

            self.meta._add_fileio("Saved {} to {}".format(self.name, path))
            self.meta.save(location=path)

        return self

    def rename_regions(self, regions):
        """Sets new names for the regions

        Parameters
        ----------
        regions : list or dict
            In case of dict: {'old_name' :  'new_name'} with a
                entry for each old_name which should be renamed
            In case of list: List of new names in order and complete
                without repetition

        """

        if type(regions) is list:
            regions = {old: new for old, new in zip(self.get_regions(), regions)}

        for df in self.get_DataFrame(data=True):
            df.rename(index=regions, columns=regions, inplace=True)

        try:
            for ext in self.get_extensions(data=True):
                for df in ext.get_DataFrame(data=True):
                    df.rename(index=regions, columns=regions, inplace=True)
        except:
            pass

        self.meta._add_modify("Changed country names")
        return self

    def rename_sectors(self, sectors):
        """Sets new names for the sectors

        Parameters
        ----------
        sectors : list or dict
            In case of dict: {'old_name' :  'new_name'} with an
                entry for each old_name which should be renamed
            In case of list: List of new names in order and
                complete without repetition

        """

        if type(sectors) is list:
            sectors = {old: new for old, new in zip(self.get_sectors(), sectors)}

        for df in self.get_DataFrame(data=True):
            df.rename(index=sectors, columns=sectors, inplace=True)

        try:
            for ext in self.get_extensions(data=True):
                for df in ext.get_DataFrame(data=True):
                    df.rename(index=sectors, columns=sectors, inplace=True)
        except:
            pass
        self.meta._add_modify("Changed sector names")
        return self

    def rename_Y_categories(self, Y_categories):
        """Sets new names for the Y_categories

        Parameters
        ----------
        Y_categories : list or dict
            In case of dict: {'old_name' :  'new_name'} with an
                entry for each old_name which should be renamed
            In case of list: List of new names in order and
                complete without repetition

        """

        if type(Y_categories) is list:
            Y_categories = {
                old: new for old, new in zip(self.get_Y_categories(), Y_categories)
            }

        for df in self.get_DataFrame(data=True):
            df.rename(index=Y_categories, columns=Y_categories, inplace=True)

        try:
            for ext in self.get_extensions(data=True):
                for df in ext.get_DataFrame(data=True):
                    df.rename(index=Y_categories, columns=Y_categories, inplace=True)
        except:
            pass

        self.meta._add_modify("Changed Y category names")
        return self


# API classes
class Extension(CoreSystem):
    """Class which gathers all information for one extension of the IOSystem

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
        D_cba=None,
        D_pba=None,
        D_imp=None,
        D_exp=None,
        unit=None,
        **kwargs,
    ):
        """ Init function - see docstring class """
        self.name = name
        self.F = F
        self.F_Y = F_Y
        self.S = S
        self.S_Y = S_Y
        self.M = M
        self.D_cba = D_cba
        self.D_pba = D_pba
        self.D_imp = D_imp
        self.D_exp = D_exp
        self.unit = unit

        for ext in kwargs:
            setattr(self, ext, kwargs[ext])

        # Internal attributes

        # minimal necessary to calc the rest excluding F_Y since this might be
        # not necessarily present
        self.__basic__ = ["F"]
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
        return super().__str__("Extension {} with parameters: ").format(self.name)

    def calc_system(self, x, Y, Y_agg=None, L=None, population=None):
        """Calculates the missing part of the extension plus accounts

        This method allows to specify an aggregated Y_agg for the
        account calculation (see Y_agg below). However, the full Y needs
        to be specified for the calculation of F_Y or S_Y.

        Calculates:

        - for each sector and country:
            S, S_Y (if F_Y available), M, D_cba, D_pba_sector, D_imp_sector,
            D_exp_sector
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
        population : pandas.DataFrame or np.array, optional
            Row vector with population per region
        """

        if Y_agg is None:
            try:
                Y_agg = Y.sum(level="region", axis=1).reindex(
                    self.get_regions(), axis=1
                )

            except (AssertionError, KeyError):
                Y_agg = Y.sum(
                    level=0,
                    axis=1,
                ).reindex(self.get_regions(), axis=1)

        y_vec = Y.sum(axis=0)

        if self.F is None:
            self.F = calc_F(self.S, x)
            logging.debug("{} - F calculated".format(self.name))

        if self.S is None:
            self.S = calc_S(self.F, x)
            logging.debug("{} - S calculated".format(self.name))

        if (self.F_Y is None) and (self.S_Y is not None):
            self.F_Y = calc_F_Y(self.S_Y, y_vec)
            logging.debug("{} - F_Y calculated".format(self.name))

        if (self.S_Y is None) and (self.F_Y is not None):
            self.S_Y = calc_S_Y(self.F_Y, y_vec)
            logging.debug("{} - S_Y calculated".format(self.name))

        if self.M is None:
            if L is not None:
                self.M = calc_M(self.S, L)
                logging.debug("{} - M calculated based on L".format(self.name))
            else:
                try:
                    self.M = recalc_M(
                        self.S, self.D_cba, Y=Y_agg, nr_sectors=self.get_sectors().size
                    )
                    logging.debug(
                        "{} - M calculated based on " "D_cba and Y".format(self.name)
                    )
                except Exception as ex:
                    logging.debug(
                        "Recalculation of M not possible - cause: {}".format(ex)
                    )

        F_Y_agg = 0
        if self.F_Y is not None:
            # F_Y_agg = ioutil.agg_columns(
            # ext['F_Y'], self.get_Y_categories().size)
            try:
                F_Y_agg = self.F_Y.sum(level="region", axis=1).reindex(
                    self.get_regions(), axis=1
                )
            except (AssertionError, KeyError):
                F_Y_agg = self.F_Y.sum(level=0, axis=1).reindex(
                    self.get_regions(), axis=1
                )

        if (
            (self.D_cba is None)
            or (self.D_pba is None)
            or (self.D_imp is None)
            or (self.D_exp is None)
        ):
            if L is None:
                logging.debug("Not possilbe to calculate D accounts - L not present")
                return
            else:
                self.D_cba, self.D_pba, self.D_imp, self.D_exp = calc_accounts(
                    self.S, L, Y_agg, self.get_sectors().size
                )
                logging.debug("{} - Accounts D calculated".format(self.name))

        # aggregate to country
        if (
            (self.D_cba_reg is None)
            or (self.D_pba_reg is None)
            or (self.D_imp_reg is None)
            or (self.D_exp_reg is None)
        ):
            try:
                self.D_cba_reg = (
                    self.D_cba.sum(level="region", axis=1).reindex(
                        self.get_regions(), axis=1
                    )
                    + F_Y_agg
                )
            except (AssertionError, KeyError):
                self.D_cba_reg = (
                    self.D_cba.sum(level=0, axis=1).reindex(self.get_regions(), axis=1)
                    + F_Y_agg
                )
            try:
                self.D_pba_reg = (
                    self.D_pba.sum(level="region", axis=1).reindex(
                        self.get_regions(), axis=1
                    )
                    + F_Y_agg
                )
            except (AssertionError, KeyError):
                self.D_pba_reg = (
                    self.D_pba.sum(level=0, axis=1).reindex(self.get_regions(), axis=1)
                    + F_Y_agg
                )
            try:
                self.D_imp_reg = self.D_imp.sum(level="region", axis=1).reindex(
                    self.get_regions(), axis=1
                )
            except (AssertionError, KeyError):
                self.D_imp_reg = self.D_imp.sum(level=0, axis=1).reindex(
                    self.get_regions(), axis=1
                )
            try:
                self.D_exp_reg = self.D_exp.sum(level="region", axis=1).reindex(
                    self.get_regions(), axis=1
                )
            except (AssertionError, KeyError):
                self.D_exp_reg = self.D_exp.sum(level=0, axis=1).reindex(
                    self.get_regions(), axis=1
                )

            logging.debug("{} - Accounts D for regions calculated".format(self.name))

        # calc accounts per capita if population data is available
        if population is not None:
            if type(population) is pd.DataFrame:
                # check for right order:
                if population.columns.tolist() != self.D_cba_reg.columns.tolist():
                    logging.warning(
                        "Population regions are inconsistent with IO regions"
                    )
                population = population.values

            if (
                (self.D_cba_cap is None)
                or (self.D_pba_cap is None)
                or (self.D_imp_cap is None)
                or (self.D_exp_cap is None)
            ):
                self.D_cba_cap = self.D_cba_reg.dot(np.diagflat(1.0 / population))
                self.D_pba_cap = self.D_pba_reg.dot(np.diagflat(1.0 / population))
                self.D_imp_cap = self.D_imp_reg.dot(np.diagflat(1.0 / population))
                self.D_exp_cap = self.D_exp_reg.dot(np.diagflat(1.0 / population))

                self.D_cba_cap.columns = self.D_cba_reg.columns
                self.D_pba_cap.columns = self.D_pba_reg.columns
                self.D_imp_cap.columns = self.D_imp_reg.columns
                self.D_exp_cap.columns = self.D_exp_reg.columns

                logging.debug("{} - Accounts D per capita calculated".format(self.name))
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
        """Plots D_pba, D_cba, D_imp and D_exp for the specified row (account)

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

        name_row = (
            str(row)
            .replace("(", "")
            .replace(")", "")
            .replace("'", "")
            .replace("[", "")
            .replace("]", "")
        )
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
                y_label_name = (
                    name_row + " (" + str(self.unit.loc[row, "unit"].tolist()[0]) + ")"
                )
            except:
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

        data_row = pd.DataFrame(columns=[key for key in accounts])
        for key in accounts:
            if sector:
                try:
                    _data = pd.DataFrame(
                        getattr(self, accounts[key])
                        .xs(key=sector, axis=1, level="sector")
                        .loc[row]
                        .T
                    )
                except (AssertionError, KeyError):
                    _data = pd.DataFrame(
                        getattr(self, accounts[key])
                        .xs(key=sector, axis=1, level=1)
                        .loc[row]
                        .T
                    )

                if per_capita:
                    if population is not None:
                        if type(population) is pd.DataFrame:
                            # check for right order:
                            if (
                                population.columns.tolist()
                                != self.D_cba_reg.columns.tolist()
                            ):
                                logging.warning(
                                    "Population regions are inconsistent "
                                    "with IO regions"
                                )
                            population = population.values
                            population = population.reshape((-1, 1))
                            _data = _data / population
                    else:
                        raise ValueError(
                            "Population vector must be given for "
                            "sector results per capita"
                        )
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
        except:  # pragma: no cover
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
        """Writes a report to the given path for the regional accounts

        The report consists of a text file and a folder with the pics
        (both names following parameter name)

        Notes
        ----
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

        rep_spec = collections.namedtuple(
            "rep_spec", ["make", "spec_string", "is_per_capita"]
        )

        reports_to_write = {
            "per region accounts": rep_spec(per_region, "_per_region", False),
            "per capita accounts": rep_spec(per_capita, "_per_capita", True),
        }
        logging.info("Write report for {}".format(self.name))
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
                graph_name = (
                    self.name
                    + " - "
                    + str(row).replace("(", "").replace(")", "").replace("'", "")
                )

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
                report_txt.append("   :width: {} \n".format(int(pic_size)))

            # write report file and convert to given format
            report_txt.append("\nReport written on " + time.strftime("%Y%m%d %H%M%S"))
            fin_txt = "\n".join(report_txt)
            if format != "rst":
                try:
                    import docutils.core as dc

                    if format == "tex":
                        format == "latex"
                    with warnings.catch_warnings():
                        warnings.filterwarnings("ignore", category=DeprecationWarning)
                        fin_txt = dc.publish_string(
                            fin_txt,
                            writer_name=format,
                            settings_overrides={"output_encoding": "unicode"},
                        )

                except:  # pragma: no cover
                    logging.warn("Module docutils not available - write rst instead")
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
            logging.info(
                "Report for {what} written to {file_where}".format(
                    what=arep, file_where=str(_repfile)
                )
            )

        if _plt:  # pragma: no cover
            plt.ion()

    def get_rows(self):
        """ Returns the name of the rows of the extension """
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
            logging.warn("No attributes available to get row names")
            return None

    def get_row_data(self, row, name=None):
        """Returns a dict with all available data for a row in the extension

        Parameters
        ----------
        row : tuple, list, string
            A valid index for the extension DataFrames
        name : string, optional
            If given, adds a key 'name' with the given value to the dict. In
            that case the dict can be
            used directly to build a new extension.

        Returns
        -------
        dict object with the data (pandas DataFrame)for the specific rows
        """
        retdict = {}
        for rowname, data in zip(self.get_DataFrame(), self.get_DataFrame(data=True)):
            retdict[rowname] = pd.DataFrame(data.loc[row])
        if name:
            retdict["name"] = name
        return retdict

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
            _meta._add_modify(
                f"Calculated diagonalized accounts {name} from  {self.name}"
            )

        return ext_diag

    def characterize(
        self,
        factors,
        characterized_name_column="impact",
        characterization_factors_column="factor",
        characterized_unit_column="impact_unit",
        name=None,
        return_char_matrix=False,
        _meta=None,
    ):
        """Characterize stressors

        Characterizes the extension with the characterization factors given in factors.
        Factors can contain more characterization factors which depend on stressors not
        present in the Extension - these will be automatically removed.

        Note
        ----
        Accordance of units is not checked - you must ensure that the
        characterization factors correspond to the units of the extension to be
        characterized.

        Parameters
        -----------
        factors: pd.DataFrame
            A dataframe in long format with numerical index and columns named
            index.names of the extension to be characterized and
            'characterized_name_column', 'characterization_factors_column',
            'characterized_unit_column'

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
            if None (default): name of the current extension with suffix
            '_characterized'

        return_char_matrix: boolean (optional)
            If False (default), returns just the characterized extension.
            If True, returns a namedtuple with extension and the actually used
            characterization matrix.

        _meta: MRIOMetaData, optional
            Metadata handler for logging, optional. Internal

        Returns
        --------

        pymrio.Extensions (when return_char_matrix==False, default)

           or

        namedtuple with .extension: pymrio.Extension .factors: pd.DataFrame (when return_char_matrix==True)

        """

        name = name if name else self.name + "_characterized"

        # making a dataframe with indexes (stressors) as values (with multiple
        # columns if multiindex)
        rows = self.get_rows()
        if type(rows) == pd.core.indexes.multi.MultiIndex:
            df_stressors = pd.DataFrame.from_records(list(rows), columns=rows.names)
        elif type(rows) == pd.core.indexes.base.Index:
            df_stressors = pd.DataFrame.from_records(
                list([[r] for r in rows]), columns=rows.names
            )

        required_columns = rows.names + [
            characterization_factors_column,
            characterized_name_column,
            characterized_unit_column,
        ]

        assert set(required_columns).issubset(
            set(factors.columns)
        ), "Not all required columns in the passed DataFrame >factors<"

        impacts_stressors_missing = []
        factors_cleaned_gathered = []
        for charact_name in factors[characterized_name_column].drop_duplicates():
            fac_rest = factors[factors[characterized_name_column] == charact_name]
            # This works since an inner merge returns a df with index present in both df
            if len(fac_rest.merge(df_stressors, how="inner")) < len(fac_rest):
                impacts_stressors_missing.append(charact_name)
            else:
                factors_cleaned_gathered.append(fac_rest)

        for imissi in impacts_stressors_missing:
            logging.warn(
                f"Impact >{imissi}< removed - calculation requires stressors "
                f"not present in extension >{self.name}<"
            )
        df_char = pd.concat(factors_cleaned_gathered)
        units = (
            df_char.loc[:, [characterized_name_column, characterized_unit_column]]
            .drop_duplicates()
            .set_index(characterized_name_column)
            .rename({characterized_unit_column: "unit"}, axis=1)
        )
        calc_matrix = (
            (
                df_char.set_index(rows.names + [characterized_name_column])
                .loc[:, characterization_factors_column]
                .unstack(rows.names)
                .fillna(0)
            )
            .reindex(rows, axis=1)  # cases when not all stressors in factors
            .fillna(value=0)
        )

        ex = Extension(
            name=name,
            unit=units,
            **{
                acc: (calc_matrix @ self.__dict__[acc]).reindex(units.index)
                for acc in set(
                    self.get_DataFrame(data=False, with_unit=False)
                ).difference(set(self.__coefficients__))
            },
        )

        if _meta:
            _meta._add_modify(
                f"Calculated characterized accounts {name} from  {self.name}"
            )

        if return_char_matrix:
            return collections.namedtuple("characterization", ["extension", "factors"])(
                extension=ex, factors=df_char
            )
        else:
            return ex


class IOSystem(CoreSystem):
    """Class containing a whole EE MRIO System

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
        x=None,
        L=None,
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
        """ Init function - see docstring class """
        self.Z = Z
        self.Y = Y
        self.x = x
        self.A = A
        self.L = L
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
                description=description, name=name, system=system, version=version
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
        return super().__str__("IO System with parameters: ")

    def __eq__(self, other):
        """ Only the dataframes are compared. """
        self_ext = set(self.get_extensions(data=False))
        other_ext = set(other.get_extensions(data=False))
        if len(self_ext.difference(other_ext)) < 0:
            return False

        for ext in self_ext:
            if self.__dict__[ext] != other.__dict__[ext]:
                return False

        return super().__eq__(other)

    @property
    def name(self):
        try:
            return self.meta.name
        except AttributeError:
            return "undef"

    def calc_all(self):
        """
        Calculates missing parts of the IOSystem and all extensions.

        This method call calc_system and calc_extensions

        """
        self.calc_system()
        self.calc_extensions()
        return self

    def calc_system(self):
        """
        Calculates the missing part of the core IOSystem

        The method checks Z, A, x, L and calculates all which are None

        The possible cases are:
            Case    Provided    Calculated
            1)      Z           A, x, L
            2)      A, x        Z, L
            3)      A, Y        L, x, Z
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

        return self

    def calc_extensions(self, extensions=None, Y_agg=None):
        """Calculates the extension and their accounts

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
        """

        ext_list = list(self.get_extensions(data=False))
        extensions = extensions or ext_list
        if type(extensions) == str:
            extensions = [extensions]

        for ext_name in extensions:
            self.meta._add_modify(
                "Calculating accounts for extension {}".format(ext_name)
            )
            ext = getattr(self, ext_name)
            ext.calc_system(
                x=self.x, Y=self.Y, L=self.L, Y_agg=Y_agg, population=self.population
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
        """Generates a report to the given path for all extension

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

    def get_extensions(self, data=False):
        """Yields the extensions or their names

        Parameters
        ----------
        data : boolean, optional
           If True, returns a generator which yields the extensions.
           If False, returns a generator which yields the names of
           the extensions (default)

        Returns
        -------
        Generator for Extension or string

        """

        ext_list = [
            key for key in self.__dict__ if type(self.__dict__[key]) is Extension
        ]
        for key in ext_list:
            if data:
                yield getattr(self, key)
            else:
                yield key

    def reset_full(self, force=False):
        """Remove all accounts which can be recalculated based on Z, Y, F, F_Y

        Parameters
        ----------

        force: boolean, optional
            If True, reset to flows although the system can not be
            recalculated. Default: False
        """
        super().reset_full(force=force, _meta=self.meta)
        return self

    def reset_all_full(self, force=False):
        """Removes all accounts that can be recalculated (IOSystem and extensions)

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

    def reset_to_flows(self, force=False):
        """Keeps only the absolute values.

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
        """Resets the IOSystem and all extensions to absolute flows

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
        """Resets the IOSystem and all extensions to coefficients.

        This method calls reset_to_coefficients for the IOSystem and for
        all Extensions in the system

        Note
        -----

        The system can not be reconstructed after this steps
        because all absolute data is removed. Save the Y data in case
        a reconstruction might be necessary.

        """
        self.reset_to_coefficients()
        [ee.reset_to_coefficients() for ee in self.get_extensions(data=True)]
        self.meta._add_modify("Reset full system to coefficients")
        return self

    def save_all(
        self, path, table_format="txt", sep="\t", table_ext=None, float_format="%.12g"
    ):
        """Saves the system and all extensions

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
            table_ext=table_ext,
            float_format=float_format,
        )

        for ext, ext_name in zip(self.get_extensions(data=True), self.get_extensions()):
            ext_path = path / ext_name

            ext.save(
                path=ext_path,
                table_format=table_format,
                sep=sep,
                table_ext=table_ext,
                float_format=float_format,
            )
        return self

    def aggregate(
        self,
        region_agg=None,
        sector_agg=None,
        region_names=None,
        sector_names=None,
        inplace=True,
    ):
        """Aggregates the IO system.

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
            Pandas Dataframe with columns 'orignal' and 'aggregated'.
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
        # Development note: This can not be put in the CoreSystem b/c
        # than the recalculation of the extension coefficients would not
        # work.

        if not inplace:
            self = self.copy()

        try:
            self.reset_to_flows()
        except ResetError:
            raise AggregationError(
                "System under-defined for aggregation - "
                "do a 'calc_all' before aggregation"
            )

        if type(region_names) is str:
            region_names = [region_names]
        if type(sector_names) is str:
            sector_names = [sector_names]

        if type(region_agg) is pd.DataFrame:
            if ("original" not in region_agg.columns) or (
                "aggregated" not in region_agg.columns
            ):
                raise ValueError(
                    "Passed DataFrame must include the columns "
                    '"original" and "aggregated"'
                )
            region_agg = (
                region_agg.set_index("original")
                .reindex(self.get_regions(), fill_value=MISSING_AGG_ENTRY["region"])
                .loc[:, "aggregated"]
            )

        if type(sector_agg) is pd.DataFrame:
            if ("original" not in sector_agg.columns) or (
                "aggregated" not in sector_agg.columns
            ):
                raise ValueError(
                    "Passed DataFrame must include the columns "
                    '"original" and "aggregated"'
                )
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
            if type(region_agg[0]) is str:
                region_names = ioutil.unique_element(region_agg)
            else:
                # rows in the concordance matrix give the new number of
                # regions
                region_names = [
                    GENERIC_NAMES["region"] + str(nr)
                    for nr in range(region_conc.shape[0])
                ]

        if (not _same_sectors) and (not sector_names):
            if isinstance(sector_agg, np.ndarray):
                sector_agg = sector_agg.flatten().tolist()
            if type(sector_agg[0]) is str:
                sector_names = ioutil.unique_element(sector_agg)
            else:
                sector_names = [
                    GENERIC_NAMES["sector"] + str(nr)
                    for nr in range(sector_conc.shape[0])
                ]

        # Assert right shapes
        if not sector_conc.shape[1] == len(self.get_sectors()):
            raise ValueError(
                "Sector aggregation does not " "correspond to the number of sectors."
            )
        if not region_conc.shape[1] == len(self.get_regions()):
            raise ValueError(
                "Region aggregation does not " "correspond to the number of regions."
            )
        if not len(sector_names) == sector_conc.shape[0]:
            raise ValueError("New sector names do not " "match sector aggregation.")
        if not len(region_names) == region_conc.shape[0]:
            raise ValueError("New region names do not " "match region aggregation.")

        # build pandas.MultiIndex for the aggregated system
        _reg_list_for_sec = [[r] * sector_conc.shape[0] for r in region_names]
        _reg_list_for_sec = [
            entry for entrylist in _reg_list_for_sec for entry in entrylist
        ]

        _reg_list_for_Ycat = [[r] * len(self.get_Y_categories()) for r in region_names]
        _reg_list_for_Ycat = [
            entry for entrylist in _reg_list_for_Ycat for entry in entrylist
        ]

        _sec_list = list(sector_names) * region_conc.shape[0]
        _Ycat_list = list(self.get_Y_categories()) * region_conc.shape[0]

        mi_reg_sec = pd.MultiIndex.from_arrays(
            [_reg_list_for_sec, _sec_list], names=["region", "sector"]
        )
        mi_reg_Ycat = pd.MultiIndex.from_arrays(
            [_reg_list_for_Ycat, _Ycat_list], names=["region", "category"]
        )

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
                    extension.__dict__[ik_name] = pd.DataFrame(
                        data=conc.dot(ik_df).dot(conc.T)
                    )

                    # next step must be done afterwards due to unknown reasons
                    extension.__dict__[ik_name].columns = mi_reg_sec
                    extension.__dict__[ik_name].index = mi_reg_sec
                    st_redo_unit = True
                elif (
                    ik_df.index.names
                    == [
                        "region",
                        "sector",
                    ]
                    and ik_df.columns.names == ["region", "category"]
                ):

                    # Full disaggregated finald demand satellite account.
                    # Thats not implemented yet - but aggregation is in place
                    extension.__dict__[ik_name] = pd.DataFrame(
                        data=conc.dot(ik_df).dot(conc_y.T)
                    )
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

    def remove_extension(self, ext=None):
        """Remove extension from IOSystem

        For single Extensions the same can be achieved with del
        IOSystem_name.Extension_name

        Parameters
        ----------
        ext : string or list, optional
            The extension to remove, this can be given as the name of the
            instance or of Extension.name (the latter will be checked if no
            instance was found)
            If ext is None (default) all Extensions will be removed
        """
        if ext is None:
            ext = list(self.get_extensions())
        if type(ext) is str:
            ext = [ext]

        for ee in ext:
            try:
                del self.__dict__[ee]
            except KeyError:
                for exinstancename, exdata in zip(
                    self.get_extensions(data=False), self.get_extensions(data=True)
                ):
                    if exdata.name == ee:
                        del self.__dict__[exinstancename]
            finally:
                self.meta._add_modify("Removed extension {}".format(ee))

        return self


def concate_extension(*extensions, name):
    """Concatenate extensions

    Notes
    ----
    The method assumes that the first index is the name of the
    stressor/impact/input type. To provide a consistent naming this is renamed
    to 'indicator' if they differ. All other index names ('compartments', ...)
    are added to the concatenated extensions and set to NaN for missing values.

    Notes
    ----
    Attributes which are not DataFrames will be set to None if they differ
    between the extensions

    Parameters
    ----------

    extensions : Extensions
        The Extensions to concatenate as multiple parameters

    name : string
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
    df_dict = {key: None for key in set.intersection(*set_dfs)}
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
                cur_dict["F_Y"] = getattr(ext, "F_Y")
            else:
                cur_dict["F_Y"] = pd.DataFrame(
                    data=0, index=ext.get_index(), columns=SF_Y_columns
                )
        if S_Y_present:
            # doesn't work with getattr b/c S_Y can be present as attribute but
            # not as DataFrame
            if "S_Y" in ext.get_DataFrame(data=False):
                cur_dict["S_Y"] = getattr(ext, "S_Y")
            else:
                cur_dict["S_Y"] = pd.DataFrame(
                    data=0, index=ext.get_index(), columns=SF_Y_columns
                )

        # append all df data
        for key in cur_dict:
            if not first_run:
                if cur_dict[key].index.names != df_dict[key].index.names:
                    cur_ind_names = list(cur_dict[key].index.names)
                    df_ind_names = list(df_dict[key].index.names)
                    cur_ind_names[0] = "indicator"
                    df_ind_names[0] = cur_ind_names[0]
                    cur_dict[key].index.set_names(cur_ind_names, inplace=True)
                    df_dict[key].index.set_names(df_ind_names, inplace=True)

                    for ind in cur_ind_names:
                        if ind not in df_ind_names:
                            df_dict[key] = df_dict[key].set_index(
                                pd.DataFrame(
                                    data=None, index=df_dict[key].index, columns=[ind]
                                )[ind],
                                append=True,
                            )
                    for ind in df_ind_names:
                        if ind not in cur_ind_names:
                            cur_dict[key] = cur_dict[key].set_index(
                                pd.DataFrame(
                                    data=None, index=cur_dict[key].index, columns=[ind]
                                )[ind],
                                append=True,
                            )

            df_dict[key] = pd.concat([df_dict[key], cur_dict[key]])

        first_run = False

        all_dict = dict(list(attr_dict.items()) + list(df_dict.items()))
        all_dict["name"] = name

    return Extension(**all_dict)
