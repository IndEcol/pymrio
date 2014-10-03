""" 
Generic classes for pymrio

Classes and function here should not be used directly. Use the API methods from the pymrio module instead.

"""

import os
import copy
import logging
import numpy as np
import pandas as pd
import configparser
import matplotlib.pyplot as plt
import matplotlib as mpl
import string
import time
import collections
import re


from pymrio.tools.iomath import calc_x
from pymrio.tools.iomath import calc_x_from_L
from pymrio.tools.iomath import calc_Z
from pymrio.tools.iomath import calc_A
from pymrio.tools.iomath import calc_L
from pymrio.tools.iomath import calc_S
from pymrio.tools.iomath import calc_F
from pymrio.tools.iomath import calc_M
from pymrio.tools.iomath import calc_e
from pymrio.tools.iomath import calc_accounts

import pymrio.tools.util as util

# IO specific exceptions
class EXIOError(Exception):
    """ Base class for errors concerning EXIOBASE download and structure """
    def __init__(self, value='Error in Exiobase Source Files'):
        self.value = value

    def __str__(self):
        return repr(self.value)

class IO_CALCError(Exception):
    """ Base class for errors occuring during the calculation of the IO System """
    def __init__(self, value='Calculation error'):
        self.value = value
    def __str__(self):
        return repr(self.value)

# Abstract classes
class CoreSystem():
    """ This class is the base class for IOSystem and Extension

    Note
    ----
    Thats only the base class - instantiation of this class makes no sense.
    
    """

    def __str__(self, startstr = 'System with: '):
        parastr = ', '.join([attr for attr in 
                            self.__dict__ 
                            if self.__dict__[attr] is not None 
                                and '__' not in attr])
        return startstr + parastr

    def reset_to_flows(self):
        """ Keeps only the absolute values. 
        
        This removes all attributes which can not be aggregated and must be
        recalculated after the aggregation.

        Development note: The attributes which should be removed are
        defined in self.__non_agg_attributes__ 
        """
        [setattr(self,key,None) for key in self.__non_agg_attributes__]

    def reset_to_coefficients(self):
        """ Keeps only the coefficient.

        This can be used to recalculate the IO tables for a new finald demand. 

        Development note: The coefficient attributes are 
            defined in self.__coefficients__
        """
        [setattr(self,key,None) 
                for key in self.get_DataFrame(
                    data = False, 
                    with_unit = False,
                    with_population = False)
                if key not in self.__coefficients__]

    def copy(self):
        """ Returns a deep copy of the system """
        _tmp = copy.deepcopy(self)
        return _tmp

    def get_Y_categories(self, entries = None):
        """ Returns the names of y categories in the IOSystem as unique names in order

        Parameters
        ----------
        entries : List, optional
            If given, retuns an list with None for all values not in entries.

        Returns
        -------
        Index
            List of categories, None if no attribute to determine list is available
        """
        possible_dataframes = ['Y', 'FY']
        
        for df in possible_dataframes:
            if (df in self.__dict__) and (getattr(self,df) is not None):
                try:
                    ind = getattr(self, df).columns.get_level_values('category').unique()
                except (AssertionError, KeyError):
                    ind = getattr(self, df).columns.get_level_values(1).unique()
                if entries:
                    if type(entries) is str: entries = [entries]
                    ind = ind.tolist()
                    return [None if ee not in entries else ee for ee in ind]
                else:
                    return ind
        else:
            logging.warn("No attributes available to get Y categories")
            return None

    def get_index(self):
        """ Returns the pure index of the DataFrames in the system """

        possible_dataframes = ['A', 'L', 'Z', 'Y', 'F', 'FY', 'M', 'S', 
                               'D_fp', 'D_terr',  'D_imp', 'D_exp',
                               'D_fp_reg', 'D_terr_reg',  'D_imp_reg', 'D_exp_reg',
                               'D_fp_cap', 'D_terr_cap',  'D_imp_cap', 'D_exp_cap', ]
        for df in possible_dataframes:
            if (df in self.__dict__) and (getattr(self,df) is not None):
                return getattr(self, df).index
        else:
            logging.warn("No attributes available to get regions")
            return None

    def get_regions(self, entries = None):
        """ Returns the names of regions in the IOSystem as unique names in order

        Parameters
        ----------
        entries : List, optional
            If given, retuns an list with None for all values not in entries.

        Returns
        -------
        Index 
            List of regions, None if now attribute to determine list is available

        """
        possible_dataframes = ['A', 'L', 'Z', 'Y', 'F', 'FY', 'M', 'S', 
                               'D_fp', 'D_terr',  'D_imp', 'D_exp',
                               'D_fp_reg', 'D_terr_reg',  'D_imp_reg', 'D_exp_reg',
                               'D_fp_cap', 'D_terr_cap',  'D_imp_cap', 'D_exp_cap', ]
        for df in possible_dataframes:
            if (df in self.__dict__) and (getattr(self,df) is not None):
                try:
                    ind = getattr(self, df).columns.get_level_values('region').unique()
                except (AssertionError, KeyError):
                    ind = getattr(self, df).columns.get_level_values(0).unique()
                if entries:
                    if type(entries) is str: entries = [entries]
                    ind = ind.tolist()
                    return [None if ee not in entries else ee for ee in ind]
                else:
                    return ind
        else:
            logging.warn("No attributes available to get regions")
            return None

    def get_sectors(self, entries = None):
        """ Returns the names of sectors in the IOSystem as unique names in order

        Parameters
        ----------
        entries : List, optional
            If given, retuns an list with None for all values not in entries.

        Returns
        -------
        Index
            List of sectors, None if no attribute to determine the list is available

        """
        possible_dataframes = ['A', 'L', 'Z', 'F', 'M', 'S',  
                               'D_fp', 'D_terr',  'D_imp', 'D_exp',
                               'D_fp_reg', 'D_terr_reg',  'D_imp_reg', 'D_exp_reg',
                               'D_fp_cap', 'D_terr_cap',  'D_imp_cap', 'D_exp_cap', ]
        for df in possible_dataframes:
            if (df in self.__dict__) and (getattr(self,df) is not None):
                try:
                    ind = getattr(self, df).columns.get_level_values('sector').unique()
                except (AssertionError, KeyError):
                    ind = getattr(self, df).columns.get_level_values(1).unique()
                if entries:
                    if type(entries) is str: entries = [entries]
                    ind = ind.tolist()
                    return [None if ee not in entries else ee for ee in ind]
                else:
                    return ind
        else:
            logging.warn("No attributes available to get sectors")
            return None

    def get_DataFrame(self, data=False, with_unit = True, with_population = True):
        """ Yields all panda.DataFrames or there names
        
        Notes
        -----
        For IOSystem this does not include the DataFrames in the extensions.

        Parameters
        ----------
        data : boolean, optional
            If True, returns a generator which yields the DataFrames.
            If False, returns a generator which yields only the names of the DataFrames

        with_unit: boolean, optional
            If True, includes the 'unit' DataFrame
            If False, does not include the 'unit' DataFrame. The method than only yields the numerical data tables

        with_population: boolean, optional
            If True, includes the 'population' vector
            If False, does not include the 'population' vector.

        Returns
        -------
            DataFrames or string generator, depending on parameter data

        """

        for key in self.__dict__:
            if (key is 'unit') and not with_unit: continue
            if (key is 'population') and not with_population: continue
            if type(self.__dict__[key]) is pd.DataFrame: 
                if data:
                    yield getattr(self, key)
                else:
                    yield key

    def save(self, path, table_format = 'txt', sep = '\t', table_ext = None, float_format = '%.12g'):
        """ Saves the system as text or binary pickle files.
    
        Tables (dataframes) of the current system are saved as text or binary pickle files, meta data (all other attributes) and the specifications of the tables are saved in a ini file.

        Notes
        -----
        For IOSystem this does not include the DataFrames in the extension (only the trade system itself). 
        Use save_all to save the whole system.

        Parameters
        ----------
        path : string
            path for the saved data (will be created if necessary, data within will be overwritten).
            The path can contain the name for the ini file, otherwise this will be based on the name attribute.

        table_format : string
            Format to save the DataFrames:
                
                - 'pkl' : Binary pickle files, (alias: 'pickle')
                - 'txt' : Text files, (alis: 'text') default

        table_ext : string, optional
            File extension, default depends on table_format(.pkl for pickle, .txt for text)

        sep : string, optional
            Field delimiter for the output file, only for txt files

        float_format : string, optional
            Format for saving the DataFrames, default = '%.12g', only for txt files
        """
        path = path.rstrip('\\')
        path = os.path.abspath(path)
        
        ini_file_name = self.name + '.ini'
        if os.path.splitext(path)[1] == '.ini':
            (path,ini_file_name) = os.path.split(path)
            
        
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

        if table_format == 'text' : table_format = 'txt'
        if table_format == 'pickle' : table_format = 'pkl'
        if table_format != 'txt' and table_format != 'pkl':
            logging.error('Unknown table format')
            return None

        if not table_ext:
            if table_format == 'txt': table_ext = '.txt'
            if table_format == 'pkl': table_ext = '.pkl'

        io_ini = configparser.RawConfigParser()
        io_ini.optionxform = lambda option: option
        io_ini['systemtype'] = dict()
        io_ini['meta'] = dict()
        io_ini['files'] = dict()

        if str(type(self)) ==  "<class 'pymrio.core.mriosystem.IOSystem'>":
            io_ini['systemtype']['systemtype'] = 'IOSystem'
        elif str(type(self)) ==  "<class 'pymrio.core.mriosystem.Extension'>":
            io_ini['systemtype']['systemtype'] = 'Extension'
        else:
            logging.warn('Unknown system type')
            io_ini['systemtype']['systemtype'] = 'undef'

        meta_data = [k for k in self.__dict__.keys() 
                        if not (k in self.get_DataFrame() 
                        or str(type(getattr(self,k))) == "<class 'pymrio.Extension'>")]
        
        for k in meta_data:
            if k[0:2] == '__': continue
            if getattr(self,k) is None: continue
            io_ini['meta'][k] = str(getattr(self,k))

        for df,df_name in zip(self.get_DataFrame(data = True), self.get_DataFrame()):
            if type(df.index) is pd.MultiIndex:
                nr_index_col = len(df.index.levels)
            else:
                nr_index_col = 1

            if type(df.columns) is pd.MultiIndex:
                nr_header = len(df.columns.levels)
            else:
                nr_header = 1
            
            save_file = df_name + table_ext
            save_file_with_path = os.path.join(path,save_file)
            logging.info('Save file {}'.format(save_file_with_path))
            if table_format == 'txt':
                df.to_csv(save_file_with_path, sep=sep, float_format = float_format)
            else:
                df.to_pickle(save_file_with_path)
            
            io_ini['files'][df_name] = save_file
            io_ini['files'][df_name + '_nr_index_col'] = str(nr_index_col)
            io_ini['files'][df_name + '_nr_header'] = str(nr_header)

        with open (os.path.join(path, ini_file_name), 'w') as _savefile:
            io_ini.write(_savefile) 

        logging.info('Successfully saved - description at {}'.format(os.path.join(path, ini_file_name)))

    def set_regions(self, regions):
        """ Sets new names for the regions

        Parameters
        ----------
        regions : list or dict
            In case of dict: {'old_name' :  'new_name'} with a entry for each old_name which should be renamed
            In case of list: List of new names in order and complete without repetition

        """

        if type(regions) is list: 
            regions = {old:new for old,new in zip(self.get_regions(), regions)}

        for df in self.get_DataFrame(data=True):
            df.rename(index=regions, columns=regions, inplace=True)

        try: 
            for ext in self.get_extensions(data=True):
                for df in ext.get_DataFrame(data=True):
                    df.rename(index=regions, columns=regions, inplace=True)
        except:
            pass  

    def set_sectors(self, sectors):
        """ Sets new names for the sectors

        Parameters
        ----------
        sectors : list or dict
            In case of dict: {'old_name' :  'new_name'} with a entry for each old_name which should be renamed
            In case of list: List of new names in order and complete without repetition

        """

        if type(sectors) is list: 
            sectors = {old:new for old,new in zip(self.get_sectors(), sectors)}

        for df in self.get_DataFrame(data=True):
            df.rename(index=sectors, columns=sectors, inplace=True)

        try: 
            for ext in self.get_extensions(data=True):
                for df in ext.get_DataFrame(data=True):
                    df.rename(index=sectors, columns=sectors, inplace=True)
        except:
            pass  

    def set_Y_categories(self, Y_categories):
        """ Sets new names for the Y_categories

        Parameters
        ----------
        Y_categories : list or dict
            In case of dict: {'old_name' :  'new_name'} with a entry for each old_name which should be renamed
            In case of list: List of new names in order and complete without repetition

        """

        if type(Y_categories) is list: 
            Y_categories = {old:new for old,new in zip(self.get_Y_categories(), Y_categories)}

        for df in self.get_DataFrame(data=True):
            df.rename(index=Y_categories, columns=Y_categories, inplace=True)

        try: 
            for ext in self.get_extensions(data=True):
                for df in ext.get_DataFrame(data=True):
                    df.rename(index=Y_categories, columns=Y_categories, inplace=True)
        except:
            pass  


# API classes
class Extension(CoreSystem):
    """ Class which gathers all information for one extension of the IOSystem

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
    FY : pandas.DataFrame       
        Extension of final demand with columns a y and index as F
    S : pandas.DataFrame        
        Direct impact (extensions) coefficients with multiindex as F
    M : pandas.DataFrame        
        Multipliers with multiindex as F
    D_fp : pandas.DataFrame        
        Footprint of consumption,  further specification with 
        _reg (per region) or _cap (per capita) possible 
    D_terr : pandas.DataFrame        
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
    iosystem : string
        Note for the IOSystem, recommended to be 'pxp' or 'ixi' for
        product by product or industry by industry.
        However, this can be any string and can have more information if needed
        (eg for different technoloy assumptions)
        The string will be passed to the Extension
    version : string
        This can be used as a version tracking system. 
    year : int
        Baseyear of the extension data

    """

    def __init__(self, name, F = None, FY = None, S = None, M = None, D_fp =
            None, D_terr = None, D_imp = None, D_exp = None, unit = None,
            iosystem = None, version = None, year = None, **kwargs):
        """ Init function - see docstring class """
        self.name = name
        self.F = F
        self.FY = FY
        self.S = S
        self.M = M
        self.D_fp = D_fp
        self.D_terr = D_terr
        self.D_imp = D_imp
        self.D_exp = D_exp
        self.unit = unit
        self.iosystem = iosystem
        self.version = version
        self.year = year
        
        for ext in kwargs:
            setattr(self, ext, kwargs[ext])

        # Internal attributes
        self.__D_accounts__ = ['D_fp', 'D_terr', 'D_imp', 'D_exp', 'D_fp_reg',
                'D_terr_reg', 'D_imp_reg', 'D_exp_reg', 'D_fp_cap',
                'D_terr_cap', 'D_imp_cap', 'D_exp_cap']
        self.__non_agg_attributes__ = ['S', 'M']
        self.__non_agg_attributes__.extend(self.__D_accounts__)

        self.__coefficients__ = ['S', 'M']    # TODO check FY

        # check if all accounts are available
        for acc in self.__D_accounts__:
            if acc not in self.__dict__:
                setattr(self, acc, None)

    def __str__(self):
        return super().__str__(
                "Extension {} with parameters: "
                ).format(self.name)

    def calc_system(self, x, L, Y_agg, population = None ):
        """ Calculates the missing part of the extension plus accounts 
        
        
        This method uses y aggregated across specified y categories
        
        Calculates:

        - for each sector and country: 
            D, M, D_fp, D_terr_sector, D_imp_sector, D_exp_sector
        - for each region:  
            D_fp_reg, D_terr_reg, D_imp_reg, D_exp_reg, 
        - for each region (if population vector is given): 
            D_fp_cap, D_terr_cap, D_imp_cap, D_exp_cap

        Notes
        -----
        Only attributes which are not None are recalculated (for D_* this is
        checked for each group (reg, cap, and w/o appendix)).

        Parameters
        ----------
        x : pandas.DataFrame or numpy.array
            Industry output column vector
        L : pandas.DataFrame or numpy.array
            Leontief input output table L
        Y_agg : pandas.DataFrame or np.array
            The final demand aggregated (one category per country)
        population : pandas.DataFrame or np.array, optional
            Row vector with population per region
        """

        if self.F is None:
            try:
                self.F = calc_F(self.S, x)
                logging.info('Total direct impacts calculated')
            except (ValueError, AttributeError):
                logging.error(
                        core.IO_CALCError(
                        'Calculation of F not possible for {} - check S and x'
                        ).format(self.name))

        if self.S is None:
            try:
                self.S = calc_S(self.F, x)
                logging.info('Factors of production coefficients S calculated')
            except (ValueError, AttributeError):
                logging.error(
                        core.IO_CALCError(
                        'Calculation of S not possible for {} - check F and x'
                        ).format(self.name))

        if self.M is None:
            try:
                self.M = calc_M(self.S, L)
                logging.info('Multipliers M calculated')
            except (ValueError, AttributeError):
                logging.error(
                        core.IO_CALCError(
                        'Calculation of M not possible for {} - check S and L'
                        ).format(self.name))

        FY_agg = 0
        if self.FY is not None:
            #FY_agg = util.agg_columns(ext['FY'], self.get_Y_categories().size)
            try:
                FY_agg = (self.FY.sum(level='region', axis=1, sort=False).
                      reindex_axis(self.get_regions(), axis=1))
            except (AssertionError, KeyError):
                FY_agg = (self.FY.sum(level=0, axis=1, sort=False).
                      reindex_axis(self.get_regions(), axis=1))
            

        if ((self.D_fp is None) or 
                (self.D_terr is None) or 
                (self.D_imp is None) or 
                (self.D_exp is None)):
            self.D_fp, self.D_terr, self.D_imp, self.D_exp = (
                    calc_accounts(self.S, L, Y_agg, 
                        self.get_regions().size, self.get_sectors().size))
            logging.info('Accounts D calculated')

        # aggregate to country
        if ((self.D_fp_reg is None) or (self.D_terr_reg is None) or
                (self.D_imp_reg is None) or (self.D_exp_reg is None)):
            try:
                self.D_fp_reg = (
                        self.D_fp.sum(level='region', axis=1, sort=False).
                        reindex_axis(self.get_regions(), axis=1) + FY_agg)
            except (AssertionError, KeyError):
                self.D_fp_reg = (
                        self.D_fp.sum(level=0, axis=1, sort=False).
                        reindex_axis(self.get_regions(), axis=1) + FY_agg)
            try:
                self.D_terr_reg = (
                        self.D_terr.sum(level='region', axis=1, sort=False).
                        reindex_axis(self.get_regions(), axis=1) + FY_agg)
            except (AssertionError, KeyError):
                self.D_terr_reg = (
                        self.D_terr.sum(level=0, axis=1, sort=False).
                        reindex_axis(self.get_regions(), axis=1) + FY_agg)
            try:
                self.D_imp_reg = (
                        self.D_imp.sum(level='region', axis=1, sort=False).
                        reindex_axis(self.get_regions(), axis=1))
            except (AssertionError, KeyError):
                self.D_imp_reg = (
                        self.D_imp.sum(level=0, axis=1, sort=False).
                        reindex_axis(self.get_regions(), axis=1))
            try:
                self.D_exp_reg = (
                        self.D_exp.sum(level='region', axis=1, sort=False).
                        reindex_axis(self.get_regions(), axis=1))
            except (AssertionError, KeyError):
                self.D_exp_reg = (
                        self.D_exp.sum(level=0, axis=1, sort=False).
                        reindex_axis(self.get_regions(), axis=1))

            logging.info('Accounts D for regions calculated')

        # calc accounts per capita if population data is available
        if population is not None:
            if type(population) is pd.DataFrame:
                # check for right order:
                if population.columns.tolist() != self.D_fp_reg.columns.tolist():
                    logging.warning('Population regions are inconsistent with IO regions')
                population = population.values

            if ((self.D_fp_cap is None) or (self.D_terr_cap is None) or
                    (self.D_imp_cap is None) or (self.D_exp_cap is None)):
                self.D_fp_cap = self.D_fp_reg.dot(
                        np.diagflat(1./population))
                self.D_terr_cap = self.D_terr_reg.dot(
                        np.diagflat(1./population))
                self.D_imp_cap = self.D_imp_reg.dot(
                        np.diagflat(1./population))
                self.D_exp_cap = self.D_exp_reg.dot(
                        np.diagflat(1./population))

                self.D_fp_cap.columns = self.D_fp_reg.columns
                self.D_terr_cap.columns = self.D_terr_reg.columns
                self.D_imp_cap.columns = self.D_imp_reg.columns
                self.D_exp_cap.columns = self.D_exp_reg.columns

                logging.info('Accounts D per capita calculated')

    def plot_account(self, row, per_capita = False, sector = None,
            file_name = False, file_dpi = 600,  population = None, **kwargs):
        """ Plots D_terr, D_fp, D_imp and D_exp for the specified row (account)

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

        if type(per_capita) is not bool:  # necessary if row is given for 
                                          # Multiindex without brackets
            logging.error('per_capita parameter must be boolean')
            return None
        
        if type(row) is int: row = self.D_fp.ix[row].name
        
        name_row = (str(row).
                replace('(', '').
                replace(')', '').
                replace("'", "").
                replace('[', '').
                replace(']', ''))
        if sector: 
            graph_name = name_row + ' for sector ' + sector
        else:
            graph_name = name_row + ' total account'
        if per_capita: graph_name = graph_name + ' - per capita'

        graph_name = self.name + ' - ' + graph_name

        try:
            # for multiindex the entry is given with header, for single index
            # just the entry
            y_label_name = (name_row + 
                            ' (' + 
                            str(self.unit.ix[row, 'unit'].tolist()[0]) + ')')
        except:
            y_label_name = (name_row + ' (' + 
                            str(self.unit.ix[row, 'unit']) + ')')

        if 'kind' not in kwargs:
            kwargs['kind'] = 'bar'

        if 'colormap' not in kwargs:
            kwargs['colormap'] = 'Spectral'

        accounts = collections.OrderedDict()

        if sector:
            accounts['Footprint'] = 'D_fp'
            accounts['Territorial'] = 'D_terr'
            accounts['Imports'] = 'D_imp'
            accounts['Exports'] = 'D_exp'
        else:
            if per_capita:
                accounts['Footprint'] = 'D_fp_cap'
                accounts['Territorial'] = 'D_terr_cap'
                accounts['Imports'] = 'D_imp_cap'
                accounts['Exports'] = 'D_exp_cap'
            else:
                accounts['Footprint'] = 'D_fp_reg'
                accounts['Territorial'] = 'D_terr_reg'
                accounts['Imports'] = 'D_imp_reg'
                accounts['Exports'] = 'D_exp_reg'

        data_row = pd.DataFrame(columns = [key for key in accounts])
        for key in accounts:
            if sector:
                try:
                    _data = pd.DataFrame(
                             getattr(self, accounts[key]).xs(key=sector, axis=1,
                                 level='sector').ix[row].T)
                except (AssertionError, KeyError):
                    _data = pd.DataFrame(
                             getattr(self, accounts[key]).xs(key=sector, axis=1,
                                 level=1).ix[row].T)

                if per_capita:
                    if population is not None:
                        if type(population) is pd.DataFrame:
                            # check for right order:
                            if population.columns.tolist() != self.D_fp_reg.columns.tolist():
                                logging.warning('Population regions are inconsistent with IO regions')
                            population = population.values
                            population = population.reshape((-1,1))
                            _data = _data / population
                    else:
                        logging.error('Population must be given for sector results per capita')
                        return
            else:
                 _data = pd.DataFrame(
                         getattr(self, accounts[key]).ix[row].T)
            _data.columns = [key]
            data_row[key] = _data[key]

        if 'title' not in kwargs:
            kwargs['title'] = graph_name

        ax = data_row.plot(**kwargs)
        plt.xlabel('Regions')
        plt.ylabel(y_label_name)
        plt.legend(loc='best')
        try:
            plt.tight_layout()
        except:
            pass

        if file_name:
            plt.savefig(file_name, dpi=file_dpi)
        return ax

    def report_accounts(self, path, per_region = True, per_capita = False, 
                pic_size = 1000, format='rst', ffname = None,  **kwargs):
        """ Writes a report to the given path for the regional accounts 

        The report consists of a text file and a folder with the pics 
        (both names following parameter name)

        Notes
        ----
            This looks prettier with the seaborn module 
            (import seaborn before calling this method)


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

        if not per_region and not per_capita:
            return

        _plt = plt.isinteractive()
        _rcParams = mpl.rcParams.copy()
        rcParams={
        'figure.figsize' : (10, 5),
        'figure.dpi' : 350,
        'axes.titlesize' : 20,
        'axes.labelsize' : 20,
        }
        plt.ioff()

        path = os.path.abspath(path.rstrip('\\'))
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

        if ffname is None:
            valid_char = string.ascii_letters + string.digits + '_'
            ffname = self.name.replace(' ', '_')
            ffname = "".join([r for r in ffname if r in valid_char])

        rep_spec=collections.namedtuple('rep_spec', 
                            ['make', 'spec_string', 'is_per_capita'])
          
        reports_to_write = {'per region accounts':rep_spec(per_region, 
                                                '_per_region', False), 
                            'per capita accounts':rep_spec(per_capita, 
                                                '_per_capita', True)}
        logging.info('Write report for {}'.format(self.name))
        for arep in reports_to_write:
            if not reports_to_write[arep].make:
                continue

            report_txt = []
            report_txt.append('###########')
            report_txt.append('MRIO report')
            report_txt.append('###########')
            report_txt.append('\n')
            _ext = 'Extension: ' + self.name + ' - ' + str(arep)
            report_txt.append(_ext)
            report_txt.append('='*len(_ext))

            report_txt.append('.. contents::\n\n')

            curr_ffname = ffname + reports_to_write[arep].spec_string
            subfolder = os.path.join(path, curr_ffname)

            if not os.path.exists(subfolder):
                os.makedirs(subfolder, exist_ok=True)

            for row in self.get_rows():
                name_row = (str(row).
                        replace('(', '').
                        replace(')', '').
                        replace("'", "").
                        replace(' ', '_').
                        replace(', ', '_').
                        replace('__', '_'))
                graph_name = (self.name + ' - ' + str(row).
                                                replace('(', '').
                                                replace(')', '').
                                                replace("'", ""))

                # get valid file name
                clean = lambda varStr: re.sub('\W|^(?=\d)', '_', varStr) 
                file_name = (clean(name_row + 
                                reports_to_write[arep].spec_string) + '.png')
                
                file_name = os.path.join(subfolder, file_name)
                file_name_rel = './' + os.path.relpath(file_name, start = path)

                self.plot_account(row, file_name = file_name, 
                                  per_capita = reports_to_write[arep].
                                    is_per_capita, **kwargs)
                plt.close()

                report_txt.append(graph_name)
                report_txt.append('-'*len(graph_name) + '\n\n')

                report_txt.append('.. image:: ' + file_name_rel)
                report_txt.append('   :width: {} \n'.format(int(pic_size)))

            # write report file and convert to given format
            report_txt.append('\nReport written on ' 
                        + time.strftime("%Y%m%d %H%M%S") )
            fin_txt = '\n'.join(report_txt)
            if format is not 'rst':
                try:
                    import docutils as du
                    if format == 'tex': 
                        format == 'latex'
                    fin_txt = du.core.publish_string(fin_txt, 
                            writer_name=format, 
                            settings_overrides={'output_encoding':'unicode'})
                except:
                    logging.warn(
                        'Module docutils not available - write rst instead')
                    format = 'rst'
            format_str = {'latex':'tex', 
                          'tex':'tex', 
                          'rst':'txt', 
                          'txt':'txt', 
                          'html':'html'}
            _repfile = curr_ffname + '.' + format_str.get(format, str(format))
            with open(os.path.join(path, _repfile), 'w') as out_file:
                out_file.write(fin_txt)
            logging.info('Report for {what} written to {file_where}'.
                    format(what = arep, file_where = str(_repfile)))

        # restore plot status
        mpl.rcParams.update(_rcParams)
        if _plt: 
            plt.ion() 

    def get_rows(self):
        """ Returns the name of the rows of the extension"""
        possible_dataframes = ['F', 'FY', 'M', 'S', 
                               'D_fp', 'D_terr',  'D_imp', 'D_exp',
                               'D_fp_reg', 'D_terr_reg',  
                               'D_imp_reg', 'D_exp_reg',
                               'D_fp_cap', 'D_terr_cap',  
                               'D_imp_cap', 'D_exp_cap', ]
        for df in possible_dataframes:
            if (df in self.__dict__) and (getattr(self, df) is not None):
                return getattr(self, df).index.get_values()
        else:
            logging.warn("No attributes available to get row names")
            return None

    def get_row_data(self, row, name = None):
        """ Returns a dict with all available data for a row in the extension

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
        for rowname, data in zip(self.get_DataFrame(), 
                                 self.get_DataFrame(data=True)):
            retdict[rowname] = pd.DataFrame(data.ix[row])
        if name:
            retdict['name'] = name
        return retdict

    def per_source(self, name = None):
        """ Returns a extension disaggregated into the regional source 

        The returned extension included F, FY if present in the original
        extension, and units.

        Notes
        -----
            This method changes the order of the accounts lexicographically.

        Parameters
        ----------
        Name : string (optional)
            The new name for the extension, 
            if None (default): original name + 'per source region'

        Returns
        -------
        Extension
        """
        if not name: name = self.name + " per source region"
        persou = Extension(name)
        persou.version = self.version
        persou.iosystem = self.iosystem
        persou.year = self.year
        
        # build the disaggregated index and allocate new arrays
        new_index_list = []
        for origind in self.F.index:
            # ensure list for index
            if type(origind) is str: 
                origind = [origind, ]
            else:
                origind = list(origind)
            new_index_list = (new_index_list + 
                    [origind + [reg] for reg in self.get_regions()])
        
        new_index_names = list(self.F.index.names)
        new_index_names.append('region')
        new_mi = pd.MultiIndex.from_tuples(
                [tuple(entry) for entry in new_index_list], 
                 names = new_index_names)

        persou.F = pd.DataFrame(data = 0, 
                                index = new_mi, 
                                columns = self.F.columns)

        # fill new array with data
        persou.F = persou.F.swaplevel(0, -1, axis=0)
        for reg in self.get_regions():
            persou.F.loc[reg, reg] = self.F[reg].values
        persou.F = persou.F.swaplevel(0, -1, axis=0)

        ## same for FY
        if 'FY' in self.get_DataFrame():
            persou.FY = pd.DataFrame(data = 0, 
                                     index = new_mi, 
                                     columns = self.FY.columns)       
            persou.FY = persou.FY.swaplevel(0, -1, axis=0)
            for reg in self.get_regions():
                persou.FY.loc[reg, reg] = self.FY[reg].values
            persou.FY = persou.FY.swaplevel(0, -1, axis=0)

        # update the units
        persou.unit = pd.DataFrame(data = 0, 
                                   index = new_mi, 
                                   columns = self.unit.columns)
        persou.unit.reset_index('region', inplace=True)
        persou.unit.update(self.unit)
        persou.unit.set_index('region', append = True, 
                              inplace = True, drop = True)

        return persou


class IOSystem(CoreSystem):
    """ Class containing a whole EE MRIO System

    The class collects pandas dataframes for a whole EE MRIO system. The
    attributes for the trade matrices (Z, L, A, x, Y) can be set directly,
    extensions are given as dictionaries containing F, FY, D, m, D_fp, D_terr,
    D_imp, D_exp

    Notes
    -----
        The attributes and extension dictionary entries are pandas.DataFrame with
        an MultiIndex.  This index must have the specified level names.

    Attributes
    ----------
    Z : pandas.DataFrame
        Symetric input output table (flows) with country and sectors as
        MultiIndex with names 'region' and 'sector' for columns and index
    Y : pandas.DataFrame   
        final demand with MultiIndex with index.names = (['region', 'sector'])
        and column.names = (['region', 'category'])
    A : pandas.DataFrame   
        coefficient input output table, MultiTndex as Z
    L : pandas.DataFrame    
        Leontief, MultiTndex as Z
    unit : pandas.DataFrame    
        Unit for each row of Z
    iosystem : string
        Note for the IOSystem, recommended to be 'pxp' or 'ixi' for
        product by product or industry by industry.
        However, this can be any string and can have more information if needed
        (eg for different technoloy assumptions)
        The string will be passed to the IOSystem
    version : string
        This can be used as a version tracking system. 
    year : string or int
        Baseyear of the IOSystem
    price : string
        Price system of the IO (current or constant prices)
    name : string, optional
        Name of the IOSystem, default is 'IO'

    **kwargs : dictonary
        Extensions are given as dictionaries and will be passed to the
        Extension class.  The dict must contain a key with a value for 'name',
        this can be the same as the name of the dict.  For the further keys see
        class Extension
    
    """

    def __init__(self, Z = None, Y = None, A = None, x = None, L = None, 
            unit = None, population = None, iosystem = None, version = None, 
            year = None, price = None, name = 'IO', **kwargs):
        """ Init function - see docstring class """
        self.Z = Z
        self.Y = Y
        self.x = x
        self.A = A
        self.L = L
        self.name = name
        self.unit = unit
        self.population = population

        self.iosystem = iosystem
        self.version = version
        self.year = year
        self.price = price
        for ext in kwargs:
            setattr(self, ext, Extension(**kwargs[ext]))

        # Attributes needed to define the IOSystem
        self.__non_agg_attributes__ = ['A', 'L']

        self.__coefficients__ = ['A', 'L']

    def __str__(self):
        return super().__str__("IO System with parameters: ")

    def calc_all(self):
        """
        Calculates missing parts of the IOSystem and all extensions.

        This method call calc_system and calc_extensions

        """
        self.calc_system()
        self.calc_extensions()

    def calc_system(self):
        """ 
        Calculates the missing part of the core IOSystem

        The method checks Z, x, A, L and calculates all which are None 
        """

        # Possible cases: 
        # 1) Z given, rest can be None and calculated
        # 2) A and x given, rest can be calculated
        # 3) A and y given, calc L (if not given) - calc x and the rest

        # this catches case 3
        if self.x is None and self.Z is None:
            # in that case we need L or at least A to calculate it
            try:
                if self.L is None:
                    try:
                        self.L = calc_L(self.A)
                        logging.info('Leontief matrix L calculated')
                    except (ValueError, AttributeError):
                        logging.error(core.IO_CALCError(
                                'Calculation of L not possible - check A')) 

                self.x = calc_x_from_L(self.L, self.Y.sum(axis=1))
                logging.info('Industry Ooutput x calculated')
            except (ValueError, AttributeError):
                logging.error(
                    core.IO_CALCError(
                    'Calculation of x not possible - check A and x'))

        # this chains of ifs catch cases 1 and 2
        if self.Z is None:
            try:
                self.Z = calc_Z(self.A, self.x)
                logging.info('Flow matrix Z calculated')
            except (ValueError, AttributeError):
                logging.error(
                    core.IO_CALCError(
                    'Calculation of Z not possible - check A and x'))

        if self.x is None:
            try:
                self.x = calc_x(self.Z, self.Y)
                logging.info('Industry output x calculated')
            except (ValueError, AttributeError):
                logging.error(
                    core.IO_CALCError(
                        'Calculation of x not possible - check Z and Y'))

        if self.A is None: 
            try:
                self.A = calc_A(self.Z, self.x)
                logging.info('Coefficient matrix A calculated')
            except (ValueError, AttributeError):
                logging.error(core.IO_CALCError(
                        'Calculation of A not possible - check Z and x')) 

        if self.L is None:
            try:
                self.L = calc_L(self.A)
                logging.info('Leontief matrix L calculated')
            except (ValueError, AttributeError):
                logging.error(core.IO_CALCError(
                        'Calculation of L not possible - check A')) 

    def calc_extensions(self, extensions = None, Y_agg = None):
        """ Calculates the extension and their accounts 
        
        For the calculation, y is aggregated across specified y categories
        The method calls .calc_system of each extension (or these given in the
        extensions parameter)

        Parameters
        ----------
        extensions : list of strings, optional
            A list of key names of extensions which shall be calculated. 
            Default: all dictionaries of IOSystem are assumed to be extensions
        Y_agg : pandas.DataFrame or np.array, optional 
            The final demand aggregated (one category per country)
            Default: y is aggregated over all categories
        """
        
        ext_list = list(self.get_extensions(data=False))
        extensions = extensions or ext_list
        if type(extensions) == str: extensions = [extensions]
        
        if not Y_agg:  # this is needed in every loop iteration below
            logging.info('Calculating aggregated final demand')
            #Y_agg = util.agg_columns(self.Y, self.get_Y_categories().size)  
            try:
                Y_agg = self.Y.sum(level='region', 
                               axis=1, 
                               sort=False).reindex_axis(self.get_regions(), 
                                                        axis=1)
            except (AssertionError, KeyError):
                Y_agg = self.Y.sum(level=0, 
                               axis=1, 
                               sort=False).reindex_axis(self.get_regions(), 
                                                        axis=1)

        for ext_name in extensions:
            ext = getattr(self, ext_name)
            logging.info('**Calculating extension {}**'.format(ext.name))
            ext.calc_system(x = self.x,
                            L = self.L,
                            Y_agg = Y_agg,
                            population = self.population
                            )

    def report_accounts(self, path, per_region = True, 
                        per_capita = False, pic_size = 1000, 
                        format='rst', **kwargs):
        """ Generates a report to the given path for all extension

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
            ext.report_accounts(path=path, 
                                per_region=per_region, 
                                per_capita=per_capita, 
                                pic_size=pic_size, 
                                format=format,
                                **kwargs)


    def get_extensions(self, data=False):
        """ Yields the extensions or their names
        
        Parameters
        ----------
        data : boolean, optional
           If True, returns a generator which yields the dicts of the
           extensions.  
           If False, returns a generator which yields the names of
           the extensions (default)

        Returns
        -------
        Generator for Extension or string

        """
        
        ext_list = [key for key in 
                    self.__dict__ if type(self.__dict__[key]) is Extension]
        for key in ext_list:
            if data:
                yield getattr(self, key)
            else:
                yield key

    def reset_all_to_flows(self):
        """ Resets the IOSystem and all extensions to absolute flows

        This method calls reset_to_flows for the IOSystem and for
        all Extensions in the system
        """
        self.reset_to_flows()
        [ee.reset_to_flows() for ee in self.get_extensions(data=True)]

    def reset_all_to_coefficients(self):
        """ Resets the IOSystem and all extensions to coefficients.

        This method calls reset_to_coefficients for the IOSystem and for
        all Extensions in the system
        """
        self.reset_to_coefficients()
        [ee.reset_to_coefficients() for ee in self.get_extensions(data=True)]

    def save_all(self, path, table_format = 'txt', sep = '\t', 
            table_ext = None, float_format = '%.12g'):
        """ Saves the system and all extensions

        Extensions are saved in separate folders (names based on extension)

        Parameters are passed to the .save methods of the IOSystem and
        Extensions
        """
        self.save(path = path, 
                  table_format = table_format,
                  sep = sep,
                  table_ext = table_ext,
                  float_format = float_format)
        
        for ext, ext_name in zip(self.get_extensions(data=True), 
                                 self.get_extensions()):
            ext_path = os.path.join(path, ext_name)
            if not os.path.exists(ext_path):
                os.makedirs(ext_path, exist_ok=True)
            ext_ini_file = os.path.join(ext_path, ext_name + '.ini')
            ext.save(path = ext_ini_file,
                     table_format = table_format,
                     sep = sep,
                     table_ext = table_ext,
                     float_format = float_format)

    def aggregate(self, region_agg = None, sector_agg = None, 
                  region_dict = None, sector_dict = None, 
                  recalc = False, inplace = False):
        """ Aggregates the IO system
            
            This removes all data which can't be aggregated (coefficients)
            these must be recalculated afterwards
            
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
            region_agg : list or array, optional
                The aggregation vector or matrix for the regions (np.ndarray or
                list)
            sector_agg : list or arrays, optional
                The aggregation vector or matrix for the sectors (np.ndarray or
                list)
            region_dict : dict, optional    
                Information to reorder the aggregated regions
            secotor_dict : dict, optional    
                Information to reorder the aggregated sectors
            recalc : boolean, optional
                Recalc IOSystem and accounts after aggregation, default: False
            inplace : boolean, optional
                If True, aggregates the IOSystem in place, otherwise return a
                new IOSystem (default)
                
            Returns
            -------
            IOSystem 
                Aggregated IOSystem (if inplace is False)

        """
        if not inplace:
            self = self.copy()

        self.reset_to_flows()

        _same_regions = False
        _same_sectors = False

        # fill the aggregation matrix with 1:1 mapping if input not given
        # and get names if not given
        if not region_agg:
            region_agg = self.get_regions()
            names_regions = self.get_regions()
            _same_regions = True
        if not sector_agg:
            sector_agg = self.get_sectors()
            names_sectors = self.get_sectors()
            _same_sectors = True

        # build aggregation concordance matrix for regions and sectors if
        # concordance is not given as matrix
        if not util.is_vector(region_agg):
            region_conc = region_agg
        else:
            region_conc = util.build_agg_matrix(region_agg, region_dict)
        if not util.is_vector(sector_agg):
            sector_conc = sector_agg
        else:
            sector_conc = util.build_agg_matrix(sector_agg, sector_dict)


        # build the new names
        if not _same_regions:
            if region_dict:
                names_regions = sorted(region_dict, 
                                       key = lambda x: region_dict[x])
            else:
                if isinstance(region_agg, np.ndarray): 
                    region_agg = region_agg.flatten().tolist()
                if type(region_agg[0]) is str: 
                    names_regions = util.unique_element(region_agg)
                else:  
                    # rows in the concordance matrix give the new number of
                    # regions
                    names_regions = [GENERIC_NAMES['region'] + 
                            str(nr) for nr in range(region_conc.shape[0])] 

        if not _same_sectors:
            if sector_dict:
                names_sectors = sorted(
                        sector_dict, key = lambda x: sector_dict[x])
            else:
                if isinstance(sector_agg, np.ndarray): sector_agg = (
                        sector_agg.flatten().tolist())
                if type(sector_agg[0]) is str: 
                    names_sectors = util.unique_element(sector_agg)
                else: 
                    names_sectors = [GENERIC_NAMES['sector'] + 
                            str(nr) for nr in range(sector_conc.shape[0])]

        # build pandas.MultiIndex for the aggregated system
        _reg_list_for_sec = [[r] * sector_conc.shape[0] for r in names_regions]
        _reg_list_for_sec = [entry for entrylist in 
                             _reg_list_for_sec for entry in entrylist]

        _reg_list_for_Ycat = [[r] * len(self.get_Y_categories()) for r in
                              names_regions]
        _reg_list_for_Ycat = [entry for entrylist in 
                              _reg_list_for_Ycat for entry in entrylist]

        _sec_list = list(names_sectors) * region_conc.shape[0]
        _Ycat_list = list(self.get_Y_categories()) * region_conc.shape[0]

        mi_reg_sec = pd.MultiIndex.from_arrays(
                [_reg_list_for_sec, _sec_list], 
                names = ['region', 'sector'])
        mi_reg_Ycat = pd.MultiIndex.from_arrays(
                [_reg_list_for_Ycat, _Ycat_list], 
                names = ['region', 'category'])

        # arrange the whole concordance matrix
        conc = np.kron(region_conc, sector_conc)
        conc_y = np.kron(region_conc , np.eye(len(self.get_Y_categories())))

        # Aggregate
        try:    
            # x can also be obtained from the aggregated Z, but aggregate if
            # available
            self.x = pd.DataFrame(
                        data = conc.dot(self.x),
                        index = mi_reg_sec,
                        columns = self.x.columns,
                        )
            logging.info('Aggregate industry output x')
        except:
            pass
        
        logging.info('Aggregate final demand y')
        self.Y = pd.DataFrame(
                    data = conc.dot(self.Y).dot(conc_y.T),
                    index = mi_reg_sec,
                    columns = mi_reg_Ycat,
                    )

        logging.info('Aggregate transaction matrix Z')           
        self.Z = pd.DataFrame(
                    data = conc.dot(self.Z).dot(conc.T),
                    index = mi_reg_sec,
                    columns = mi_reg_sec,
                    )

        if self.population is not None:
            logging.info('Aggregate population vector')
            self.population = pd.DataFrame(
                        data = region_conc.dot(self.population.T).T,
                        columns = names_regions,
                        index = self.population.index,
                        )

        for extension in self.get_extensions(data = True):
            logging.info(
                    'Aggregate extension matrices F aggregated for {}'.
                    format(extension.name))
            extension.reset_to_flows()
            extension.F = pd.DataFrame(
                        data = extension.F.dot(conc.T),
                        index = extension.F.index,
                        )
            # the next step must be done afterwards due to unknown reasons
            extension.F.columns = mi_reg_sec 
            if getattr(extension, 'FY') is not None:
                logging.info(
                        'Aggregate final demand extension matrices FY for {}'
                        .format(extension.name))           
                extension.FY = pd.DataFrame(
                        data = extension.FY.dot(conc_y.T),
                        index = extension.FY.index,
                        )
                # the next step must be done afterwards due to unknown reasons
                extension.FY.columns = mi_reg_Ycat
        
        if recalc:
            self.calc_all()

        if not inplace:
            return self
    def remove_extension(self, ext=None):
        """ Remove extension from IOSystem

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
        if ext is None: ext = list(self.get_extensions())
        if type(ext) is str: ext = [ext]

        for ee in ext:
            try:
                del self.__dict__[ee]
            except:
                for exinstancename, exdata in zip(
                        self.get_extensions(data=False), 
                        self.get_extensions(data=True)):
                    if exdata.name == ee: del self.__dict__[exinstancename]

