""" 
Function and classes for (symmetric) MRIO systems
================================================

The classes and tools in this module should work with any symetric IO system.

The main class of the module (IOSystem) has attributes .A, .L, ... 
corresponding to a standard IO classification. 
Data can be assigned directly to the attributes or by calling the 
parsing or load functions.

Data storage
------------
Txt files together with a ini file are used for storing data. In addition, 
the IOSystem with all data can also be pickled (binary). 
Conversion to hdf5 and mat should be implemented...

Misc
----

Standard abbreviation for that module: mr
Dependencies:

- numpy
- scipy
- pandas
- matplotlib
- docutils (only for IOSystem.report* if format is html and tex - not 
            imported otherwise)


:Authors: Konstantin Stadler 

:license: BSD 2-Clause License

"""
# pylint: disable-msg=C0103
# general imports
import os
import sys
import configparser
import time 
import logging
import collections
import re
import string
import tools.util as util
import core.classes as core
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

import imp # debug
imp.reload(core)


# check for correct python version number
if sys.version_info.major < 3: 
    logging.warn('This package requires Python 3.0 or later.')

# version
__version__ = '0.1.0'

# constants and global variables
PYMRIO_PATH = {
    'root': os.path.dirname(__file__),
    'test_mrio': os.path.abspath(os.path.join(os.path.dirname(__file__), 
                './mrio_models/test_mrio')),
    'test': os.path.abspath(os.path.join(os.path.dirname(__file__), 
                './mrio_models/test_mrio')),
    'exio20': os.path.abspath(os.path.join(os.path.dirname(__file__), 
                './mrio_models/exio20')),
    'exio2': os.path.abspath(os.path.join(os.path.dirname(__file__), 
                './mrio_models/exio20')),
    }

# generic names (needed for the aggregation  if no names are given)
GENERIC_NAMES = {   
        'sector' : 'sec',
        'region' : 'reg',
        }

# class definitions
class Extension(core.CoreSystem):
    """ Class which gathers all information for one extension of the IOSystem

    Notes
    -----
    
    For the total accounts (D_) also reginal (appendix _reg) and 
    per capita (appendix _cap) are possible.

    Attributes
    ----------
    name : string
        Every extension must have a name. This can (reconmmended) be the name
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
        The string will be passed to the IOSystem
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
            FY_agg = (self.FY.sum(level='region', axis=1, sort=False).
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
            self.D_fp_reg = (
                    self.D_fp.sum(level='region', axis=1, sort=False).
                    reindex_axis(self.get_regions(), axis=1) + FY_agg)
            self.D_terr_reg = (
                    self.D_terr.sum(level='region', axis=1, sort=False).
                    reindex_axis(self.get_regions(), axis=1) + FY_agg)
            self.D_imp_reg = (
                    self.D_imp.sum(level='region', axis=1, sort=False).
                    reindex_axis(self.get_regions(), axis=1))
            self.D_exp_reg = (
                    self.D_exp.sum(level='region', axis=1, sort=False).
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
                 _data = pd.DataFrame(
                         getattr(self, accounts[key]).xs(key=sector, axis=1,
                             level='sector').ix[row].T)
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

class IOSystem(core.CoreSystem):
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
            Y_agg = self.Y.sum(level='region', 
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
        """ Returns a generator for the extension in the IOSystem 
        
        Parameters
        ----------

        data : boolean, optional
           If True, returns a generator which yields the dicts of the
           extensions.  
           If False, returns a generator which yields the names of
           the extensions (default)

        Returns
        -------

        generator

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

# mathematical functions
def calc_x(Z, Y):
    """ Calculate the industry output x from the Z and Y matrix 
   
    Parameters
    ----------
    Z : pandas.DataFrame or numpy.array
        Symmetric input output table (flows)
    Y : pandas.DataFrame or numpy.array
        final demand with categories (1.order) for each country (2.order)

    Returns
    -------
    pandas.DataFrame or numpy.array
        Industry output x as column vector
        The type is determined by the type of Z. If DataFrame index as Z

    """
    result = np.reshape(np.sum(np.hstack((Z, Y)), 1 ), (-1, 1))
    if type(Z) is pd.DataFrame:
        result = pd.DataFrame(result, index = Z.index, columns = ['indout'])
    return result

def calc_x_from_L(L, y):
    """ Calculate the industry output x from L and a y vector
   
    Parameters
    ----------
    L : pandas.DataFrame or numpy.array
        Symmetric input output Leontief table
    y : pandas.DataFrame or numpy.array
        a column vector of the total final demand

    Returns
    -------
    pandas.DataFrame or numpy.array
        Industry output x as column vector
        The type is determined by the type of L. If DataFrame index as L

    """
    x = L.dot(y)
    if type(L) is pd.DataFrame:
        x = pd.DataFrame(x, index = L.index, columns = ['indout'])
    return x

def calc_Z(A, x):
    """ calculate the Z matrix (flows) from A and x

    Parameters
    ----------
    A : pandas.DataFrame or numpy.array
        Symmetric input output table (coefficients)
    x : pandas.DataFrame or numpy.array
        Industry output column vector

    Returns
    -------
    pandas.DataFrame or numpy.array
        Symmetric input output table (flows) Z
        The type is determined by the type of A. 
        If DataFrame index/columns as A

    """
    if type(x) is pd.DataFrame:
        x=x.values
    x=x.reshape((1, -1)) # use numpy broadcasting - much faster 
    # (but has to ensure that x is a row vector)
    #return A.dot(np.diagflat(x)) # old mathematical form
    if type(A) is pd.DataFrame:
        return pd.DataFrame(A.values * x, index=A.index, columns=A.columns)
    else:
        return A*x

def calc_A(Z, x):
    """ Calculate the A matrix (coefficients) from Z and x 

    Parameters
    ----------
    Z : pandas.DataFrame or numpy.array
        Symmetric input output table (flows)
    x : pandas.DataFrame or numpy.array
        Industry output column vector

    Returns
    -------
    pandas.DataFrame or numpy.array
        Symmetric input output table (coefficients) A
        The type is determined by the type of Z. 
        If DataFrame index/columns as Z

    """
    if type(x) is pd.DataFrame:
        x=x.values
    recix = 1/x
    recix[recix==np.inf]=0
    #return Z.dot(np.diagflat(recix)) # Mathematical form - slow
    recix=recix.reshape((1, -1))  # use numpy broadcasting - factor ten faster 
    if type(Z) is pd.DataFrame:
        return pd.DataFrame(Z.values * recix, index=Z.index, columns=Z.columns)
    else:
        return Z*recix

def calc_L(A):
    """ Calculate the Leontief L from A 

    Parameters
    ----------
    A : pandas.DataFrame or numpy.array
        Symmetric input output table (coefficients)

    Returns
    -------
    pandas.DataFrame or numpy.array
        Leontief input output table L
        The type is determined by the type of A. 
        If DataFrame index/columns as A

    """
    I = np.eye(A.shape[0])
    if type(A) is pd.DataFrame:
        return pd.DataFrame(np.linalg.inv(I-A), 
                index=A.index, columns=A.columns)
    else:
        return np.linalg.inv(I-A) 

def calc_S(F, x):
    """ Calculate extensions/factor inputs coefficients

    Parameters
    ----------
    F : pandas.DataFrame or numpy.array
        Total direct impacts
    x : pandas.DataFrame or numpy.array
        Industry output column vector

    Returns
    -------
    pandas.DataFrame or numpy.array
        Direct impact coefficients S
        The type is determined by the type of F. 
        If DataFrame index/columns as F

    """ 
    return calc_A(F, x)

def calc_F(S,x):
    """ Calculate total direct impacts from the impact coefficients

    Parameters
    ----------
    S : pandas.DataFrame or numpy.array
        Direct impact coefficients S
    x : pandas.DataFrame or numpy.array
        Industry output column vector

    Returns
    -------
    pandas.DataFrame or numpy.array
        Total direct impacts F
        The type is determined by the type of S. 
        If DataFrame index/columns as S

    """ 
    return calc_Z(S, x)


def calc_M(S, L):
    """ Calculate multipliers of the extensions

    Parameters
    ----------
    L : pandas.DataFrame or numpy.array
        Leontief input output table L
    S : pandas.DataFrame or numpy.array
        Direct impact coefficients

    Returns
    -------
    pandas.DataFrame or numpy.array
        Multipliers M
        The type is determined by the type of D. 
        If DataFrame index/columns as D

    """ 
    return S.dot(L)

def calc_e(M, Y):
    """ Calculate total impacts (footprints of consumption Y) 

    Parameters
    ----------
    M : pandas.DataFrame or numpy.array
        Multipliers 
    Y : pandas.DataFrame or numpy.array
        Final consumption

    TODO - this must be completely redone (D, check for dataframe, ...)
    Returns
    -------
    pandas.DataFrame or numpy.array
        Multipliers m
        The type is determined by the type of D. 
        If DataFrame index/columns as D   
    The calcubased on multipliers M and finald demand Y """

    return M.dot(Y)

def calc_accounts(S, L, Y, nr_countries, nr_sectors):
    """ Calculate sector specific footprints, terr, imp and exp accounts

    The total industry output x for the calculation 
    is recalculated from L and y

    Parameters
    ----------
    L : pandas.DataFrame
        Leontief input output table L
    S : pandas.DataFrame
        Direct impact coefficients
    Y : pandas.DataFrame
        Final demand: aggregated across categories or just one category, one
        column per country
    nr_countries : int
        Number of countries in the MRIO
    nr_sectors : int
        Number of sectors in the MRIO


    Returns
    -------
    Tuple 
        (D_fp, D_terr, D_imp, D_exp)

        Format: D_row x L_col (=nr_countries*nr_sectors)

        - D_fp        Footprint per sector and country
        - D_terr      Total factur use per sector and country
        - D_imp       Total global factor use to satisfy total final demand in
                      the country per sector
        - D_exp       Total factor use in one country to satisfy final demand in
                      all other countries (per sector)
    """
    # diagonalize each sector block per country
    # this results in a disaggregated y with final demand per country per
    # sector in one column
    Y_diag = util.diagonalize_blocks(Y.values, blocksize = nr_sectors)
    x_diag = L.dot(Y_diag)
    x_tot  = x_diag.values.sum(1)
    del Y_diag

    D_fp = pd.DataFrame(S.values.dot(x_diag), 
                        index=S.index, 
                        columns = S.columns)
    #D_terr = S.dot(np.diagflat(x_tot))
    D_terr = pd.DataFrame(S.values*x_tot.reshape((1, -1)), 
                          index = S.index, 
                          columns = S.columns) # faster broadcasted calculation
    
    # for the traded accounts set the domestic industry output to zero
    dom_block = np.zeros((nr_sectors, nr_sectors))
    x_trade = util.set_block(x_diag.values, dom_block)   
    D_imp = pd.DataFrame(S.values.dot(x_trade), 
                         index=S.index, 
                         columns = S.columns)

    x_exp = x_trade.sum(1)
    #D_exp = S.dot(np.diagflat(x_exp))
    D_exp = pd.DataFrame(S.values * x_exp.reshape((1, -1)), 
                         index = S.index, 
                         columns = S.columns)   # faster broadcasted version

    return (D_fp, D_terr, D_imp, D_exp)

# main module functions
def load_all(path, **kwargs):
    """ Loads the whole IOSystem with Extensions given in path

    This just calls pymrio.load with recursive = True. Apart from that the 
    same parameter can as for .load can be used.

    Parameters
    ----------
    path : string
        path or ini file name for the data to load
    **kwargs : key word arguments, optional
            This will be passed directly to the load method

    Return
    ------
    IOSystem 
    None in case of errors
    """
    return load(path, recursive = True,**kwargs)


def load(path, recursive = False, 
               ini = None, 
               subini = {}, 
               include_core = True,
               only_coefficients = False):
    """ Loads a IOSystem or Extension from a ini files

    This function can be used to load a IOSystem or Extension specified in a
    ini file. DataFrames (tables) are loaded from text or binary pickle files.
    For the latter, the extension .pkl or .pickle is assumed, in all other case
    the tables are assumed to be in .txt format.
    
    Parameters
    ----------

    path : string
        path or ini file name for the data to load

    recursive : boolean, optional
        If True, load also the data in the subfolders and add them as
        extensions to the IOSystem (in that case path must point to the root).
        Only first order subfolders are considered (no subfolders in
        subfolders) and if a folder does not contain a ini file it's skipped.
        Use the subini parameter in case of multiple ini files in a subfolder.
        Attribute name of the extension in the IOSystem are based on the
        subfolder name.  Default is False

    ini : string, optional
        If there are several ini files in the root folder, take this one for
        loading the data If None (default) take the ini found in the folder,
        error if several are found

    subini : dict, optional
        If there are multiple ini in the subfolder, use the ini given in the
        dict.  Format: 'subfoldername':'ininame' If a key for a subfolder is
        not found or None (default), the ini found in the folder will be taken,
        error if several are found

    include_core : boolean, optional
        If False the load method does not include A, L and Z matrix. This 
        significantly reduces the required memory if the purpose is only
        to analyse the results calculated beforehand.

    Returns
    -------

        IOSystem or Extension class depending on systemtype in the ini file
        None in case of errors
    
    """

    # check path and given parameter
    ini_file_name = None

    path = path.rstrip('\\')
    path = os.path.abspath(path)

    if os.path.splitext(path)[1] == '.ini':
        (path, ini_file_name) = os.path.split(path)
    
    if ini: ini_file_name = ini

    if not os.path.exists(path):
        logging.error('Given path does not exist')
        return None

    if not ini_file_name:
        _inifound = False
        for file in os.listdir(path):
            if os.path.splitext(file)[1] == '.ini':
                if _inifound:
                    logging.error(
                            'Found multiple ini files in folder - specify one')
                    return None
                ini_file_name = file
                _inifound = True

    # read the ini
    io_ini = configparser.RawConfigParser()
    io_ini.optionxform = lambda option: option

    io_ini.read(os.path.join(path, ini_file_name))

    systemtype = io_ini.get('systemtype', 'systemtype', fallback=None)
    name = io_ini.get('meta', 'name', 
            fallback=os.path.splitext(ini_file_name)[0])

    if systemtype == 'IOSystem':
        ret_system = IOSystem(name = name)
    elif systemtype == 'Extension': 
        ret_system = Extension(name = name)
    else:
        logging.error('System not defined in ini')
        return None
    
    for key in io_ini['meta']:
        setattr(ret_system, key, io_ini.get('meta', key, fallback=None))
       
    for key in io_ini['files']:
        if '_nr_index_col' in key: continue
        if '_nr_header' in key: continue

        if not include_core:
            not_to_load = ['A','L','Z']
            if key in not_to_load: continue

        if only_coefficients:
            _io = IOSystem()
            if key not in _io.__coefficients__ + ['unit']: continue

        file_name = io_ini.get('files', key)
        nr_index_col = io_ini.get(
                'files', key + '_nr_index_col', fallback = None)
        nr_header = io_ini.get('files', key + '_nr_header', fallback = None)

        if (nr_index_col is None) or (nr_header is None):
            logging.error(
                    'Index or column specification missing for {}'.
                    format(str(file_name)))
            return None

        _index_col = list(range(int(nr_index_col)))
        _header = list(range(int(nr_header)))

        if _index_col == [0]: _index_col = 0
        if _header == [0]: _header = 0
        file = os.path.join(path, file_name)
        logging.info('Load data from {}'.format(file))
        
        if (os.path.splitext(file)[1] == '.pkl' 
                or os.path.splitext(file)[1] == '.pickle'):
            setattr(ret_system, key, 
                    pd.read_pickle(file)) 
        else:
            setattr(ret_system, key, 
                    pd.read_table(file, 
                        index_col = _index_col,
                        header = _header ))

    if recursive:
        # look for subfolder in the given path
        subfolder_list = os.walk(path).__next__()[1]

        # loop all subfolder and append extension based on 
        # ini file in subfolder
        for subfolder in subfolder_list:
            subini_file_name = subini.get(subfolder)
            subpath = os.path.abspath(os.path.join(path, subfolder))
   
            if not subini_file_name:
                _inifound = False
                for file in os.listdir(subpath):
                    if os.path.splitext(file)[1] == '.ini':
                        if _inifound:
                            logging.error(
                                'Found multiple ini files in subfolder {} - specify one'.format(subpath))
                            return None
                        subini_file_name = file
                        _inifound = True           
            if not _inifound: continue  # didn't find ini - don't load 
            
            # read the ini
            subio_ini = configparser.RawConfigParser()
            subio_ini.optionxform = lambda option: option

            subio_ini.read(os.path.join(subpath, subini_file_name))

            systemtype = subio_ini.get('systemtype', 'systemtype', 
                    fallback=None)
            name = subio_ini.get('meta', 'name', 
                    fallback=os.path.splitext(subini_file_name)[0])

            if systemtype == 'IOSystem':
                logging.error('IOSystem found in subfolder {} - only extensions expected'.format(subpath))
                return None
            elif systemtype == 'Extension': 
                sub_system = Extension(name = name)
            else:
                logging.error('System not defined in ini')
                return None
            
            for key in subio_ini['meta']:
                setattr(sub_system, key, subio_ini.get('meta', key, 
                    fallback=None))
               
            for key in subio_ini['files']:
                if '_nr_index_col' in key: continue
                if '_nr_header' in key: continue

                if only_coefficients:
                    _ext = Extension('temp')
                    if key not in _ext.__coefficients__ + ['unit']: continue

                file_name = subio_ini.get('files', key)
                nr_index_col = subio_ini.get('files', key + '_nr_index_col', 
                        fallback = None)
                nr_header = subio_ini.get('files', key + '_nr_header', 
                        fallback = None)

                if (nr_index_col is None) or (nr_header is None):
                    logging.error('Index or column specification missing for {}'.format(str(file_name)))
                    return None

                _index_col = list(range(int(nr_index_col)))
                _header = list(range(int(nr_header)))

                if _index_col == [0]: _index_col = 0
                if _header == [0]: _header = 0
                file = os.path.join(subpath, file_name)
                logging.info('Load data from {}'.format(file))
                if (os.path.splitext(file)[1] == '.pkl' or
                        os.path.splitext(file)[1] == '.pickle'):
                    setattr(sub_system, key, 
                            pd.read_pickle(file)) 
                else:
                    setattr(sub_system, key, 
                            pd.read_table(file, 
                                index_col = _index_col,
                                header = _header ))

                # get valid python name from folder
                clean = lambda varStr: re.sub('\W|^(?=\d)', '_', varStr) 

                setattr(ret_system, clean(subfolder), sub_system)

    return ret_system

def load_test():
    """ Returns a small test MRIO
    
    The test system contains:
    
        - six regions, 
        - seven sectors, 
        - seven final demand categories
        - two extensions (emissions and factor_inputs)

    The test system only contains Z, Y, F, FY. The rest can be calculated with
    calc_all()

    Notes
    -----

        For development: This function can be used as an example of how to parse an IOSystem
    
    Returns
    -------

    IOSystem

    """
    
    # row_header: 
    #    number of rows containing header on the top of the file (for the
    #    columns)
    # col_header: 
    #    number of cols containing header on the beginning of the file (for the
    #    rows)
    # row and columns header contain also the row for the units, this are
    # afterwards safed as a extra dataframe
    #
    # unit_col: column containing the unit for the table
    file_data=collections.namedtuple(
            'file_data', ['file_name', 'row_header', 'col_header', 'unit_col'])

    # file names and header specs of the system
    test_system = dict(
        Z = file_data(file_name = 'trade_flows_Z.txt', 
            row_header = 2, col_header=3, unit_col = 2),
        Y = file_data(file_name = 'finald_demand_Y.txt', 
            row_header = 2, col_header = 3, unit_col = 2),
        fac = file_data(file_name = 'factor_input.txt', 
            row_header = 2, col_header = 2, unit_col = 1),
        emissions = file_data(file_name = 'emissions.txt', 
            row_header = 2, col_header = 3, unit_col = 2),
        FDemissions = file_data(file_name = 'FDemissions.txt', 
            row_header = 2, col_header = 3, unit_col = 2),
        )

    # read the data into a dicts as pandas.DataFrame
    data = {key:pd.read_table(
                os.path.join(PYMRIO_PATH['test_mrio'], 
                    test_system[key].file_name),
                index_col = list(range(test_system[key].col_header)), 
                header = list(range(test_system[key].row_header))) 
            for key in test_system}
    
    # distribute the data into dics which can be passed to 
    # the IOSystem. To do so, some preps are necessary:
    # - name the header data 
    # - save unit in own dataframe and drop unit from the tables
    
    trade = dict(Z = data['Z'], Y = data['Y'])
    factor_inputs = dict(F = data['fac'])
    emissions = dict(F = data['emissions'], FY = data['FDemissions'])

    trade['Z'].index.names = ['region', 'sector', 'unit']
    trade['Z'].columns.names = ['region', 'sector']
    trade['unit'] = (pd.DataFrame(trade['Z'].iloc[:, 0]
                     .reset_index(level='unit').unit))
    trade['Z'].reset_index(level='unit', drop=True, inplace=True)
    
    trade['Y'].index.names = ['region', 'sector', 'unit']
    trade['Y'].columns.names = ['region', 'category']
    trade['Y'].reset_index(level='unit', drop=True, inplace=True)

    factor_inputs['name'] = 'Factor Inputs'
    factor_inputs['F'].index.names = ['inputtype', 'unit', ]
    factor_inputs['F'].columns.names = ['region', 'sector']
    factor_inputs['unit'] = (pd.DataFrame(factor_inputs['F'].iloc[:, 0]
                             .reset_index(level='unit').unit))
    factor_inputs['F'].reset_index(level='unit', drop=True, inplace=True)

    emissions['name'] = 'Emissions'
    emissions['F'].index.names = ['stressor', 'compartment', 'unit', ]
    emissions['F'].columns.names = ['region', 'sector']
    emissions['unit'] = (pd.DataFrame(emissions['F'].iloc[:, 0]
                         .reset_index(level='unit').unit))
    emissions['F'].reset_index(level='unit', drop=True, inplace=True)
    emissions['FY'].index.names = ['stressor', 'compartment', 'unit']
    emissions['FY'].columns.names = ['region', 'category']
    emissions['FY'].reset_index(level='unit', drop=True, inplace=True)

    # the population data - this is optional (None can be passed if no data is
    # available)
    popdata = pd.read_table(
            os.path.join(PYMRIO_PATH['test_mrio'], './population.txt'), 
            index_col=0).astype(float)

    return IOSystem(version = 'v1', 
                    price = 'currentUSD',
                    year = '2010',
                    Z = data['Z'], 
                    Y = data['Y'], 
                    unit = trade['unit'], 
                    factor_inputs = factor_inputs, 
                    emissions=emissions, 
                    population = popdata)

def concate_extension(*extensions, name):
    """ Concatenate extensions

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
    FY_present = False    
    SY_present = False
    SFY_columns = None
    for ext in extensions:
        if 'FY' in ext.get_DataFrame(data=False): 
            FY_present = True
            SFY_columns = ext.FY.columns
        if 'SY' in ext.get_DataFrame(data=False): 
            SY_present = True
            SFY_columns = ext.SY.columns
    
    # get the intersection of the available dataframes
    set_dfs = [set(ext.get_DataFrame(data=False)) for ext in extensions]
    df_dict = {key:None for key in set.intersection(*set_dfs)}  
    if FY_present: df_dict['FY'] = None
    if SY_present: df_dict['SY'] = None
    empty_df_dict = df_dict.copy()
    attr_dict={}

    # get data from each extension
    first_run = True
    for ext in extensions:
        # get corresponding attributes of all extensions
        for key in ext.__dict__:
            if type(ext.__dict__[key]) is not pd.DataFrame:
                if attr_dict.get(key, -99) == -99:
                    attr_dict[key] = ext.__dict__[key]
                elif attr_dict[key] == ext.__dict__[key]: continue
                else:
                    attr_dict[key] = None

        # get DataFrame data
        cur_dict = empty_df_dict.copy()

        for df in cur_dict: 
            cur_dict[df] = getattr(ext, df)
        
        # add zero final demand extension if final demand extension present in
        # one extension 
        if FY_present: 
            # doesn't work with getattr b/c FY can be present as attribute but
            # not as DataFrame
            if 'FY' in ext.get_DataFrame(data = False):  
                cur_dict['FY'] = getattr(ext, 'FY')
            else:
                cur_dict['FY'] = pd.DataFrame(data = 0, 
                                    index = ext.get_index(), 
                                    columns = SFY_columns)
        if SY_present:
            # doesn't work with getattr b/c SY can be present as attribute but
            # not as DataFrame
            if 'SY' in ext.get_DataFrame(data = False):  
                cur_dict['SY'] = getattr(ext, 'SY')
            else:
                cur_dict['SY'] = pd.DataFrame(data = 0, 
                        index = ext.get_index(), columns = SFY_columns)           

        # append all df data
        for key in cur_dict:
            if not first_run:
                if cur_dict[key].index.names != df_dict[key].index.names:
                    cur_ind_names = list(cur_dict[key].index.names) 
                    df_ind_names = list(df_dict[key].index.names) 
                    cur_ind_names[0] = 'indicator'
                    df_ind_names[0] = cur_ind_names[0]
                    cur_dict[key].index.set_names(cur_ind_names, 
                                                  inplace = True) 
                    df_dict[key].index.set_names(df_ind_names, 
                                                  inplace = True)

                    for ind in cur_ind_names:
                        if ind not in df_ind_names:
                            df_dict[key] = (df_dict[key].
                                            set_index(pd.DataFrame(data=None, 
                                                index=df_dict[key].index, 
                                                columns =
                                                [ind])[ind],
                                                append=True))
                    for ind in df_ind_names:
                        if ind not in cur_ind_names:
                            cur_dict[key] = (cur_dict[key].
                                            set_index(pd.DataFrame(data=None, 
                                                index=cur_dict[key].index, 
                                                columns =
                                                [ind])[ind],
                                                append=True))
                    
            df_dict[key] = pd.concat([df_dict[key], cur_dict[key]])

        first_run = False

        all_dict = dict(list(attr_dict.items()) + list(df_dict.items()))
        all_dict['name'] = name
        
    return Extension(**all_dict)

def build_agg_vec(agg_vec, **source):
    """ Builds an combined aggregation vector based on various classifications
    
    This function build an aggregation vector based on the order in agg_vec.
    The naming and actual mapping is given in source, either explicitly or by
    pointing to a folder with the mapping.

    >>> build_agg_vec(['EU', 'OECD'], path = 'test')
    ['EU', 'EU', 'EU', 'OECD', 'REST', 'REST']
    
    >>> build_agg_vec(['OECD', 'EU'], path = 'test', miss='RoW')
    ['OECD', 'EU', 'OECD', 'OECD', 'RoW', 'RoW']

    >>> build_agg_vec(['EU', 'orig_regions'], path = 'test')
    ['EU', 'EU', 'EU', 'reg4', 'reg5', 'reg6']

    >>> build_agg_vec(['supreg1', 'other'], path = 'test', 
    >>>        other = [None, None, 'other1', 'other1', 'other2', 'other2'])
    ['supreg1', 'supreg1', 'other1', 'other1', 'other2', 'other2']


    Parameters
    ----------
    agg_vec : list
        A list of sector or regions to which the IOSystem shall be aggregated.     
        The order in agg_vec is important: 
        If a string was assigned to one specific entry it will not be
        overwritten if it is given in the next vector, e.g.  ['EU', 'OECD']
        would aggregate first into EU and the remaining one into OECD, whereas
        ['OECD', 'EU'] would first aggregate all countries into OECD and than
        the remaining countries into EU. 


    source : list or string
        Definition of the vectors in agg_vec.  The input vectors (either in the
        file or given as list for the entries in agg_vec) must be as long as
        the desired output with a string for every position which should be
        aggregated and None for position which should not be used.

        Special keywords:

            - path : Path to a folder with concordance matrices.     
                     The files in the folder can have any extension but must be
                     in text format (tab separated) with one entry per row.
                     The last column in the file will be taken as aggregation
                     vectors (other columns can be used for documentation).
                     Values must be given for every entry in the original
                     classification (string None for all values not used) If
                     the same entry is given in source and as text file in
                     path than the one in source will be used.
                     
                     Two special path entries are available so far:

                     - 'exio2'
                       Concordance matrices for EXIOBASE 2.0
                     - 'test'
                       Concordance matrices for the test IO system

                     If a entry is not found in source and no path is given
                     the current directory will be searched for the definition. 

            - miss : Entry to use for missing values, default: 'REST'

    Return
    ------ 
    list (aggregation vector)
    
    """

    # build a dict with aggregation vectors in source and folder
    if type(agg_vec) is str: agg_vec = [agg_vec]
    agg_dict = dict()
    for entry in agg_vec:
        try:
            agg_dict[entry] = source[entry]
        except KeyError:
            folder = source.get('path', './')
            folder = os.path.join(PYMRIO_PATH[folder], 'concordance')
            for file in os.listdir(folder):
                if entry == os.path.splitext(file)[0]:
                    _tmp = np.genfromtxt(os.path.join(folder, file), dtype=str)
                    if _tmp.ndim == 1: 
                        agg_dict[entry] = [None if ee == 'None' 
                                else ee for ee in _tmp.tolist()]
                    else:
                        agg_dict[entry] = [None if ee == 'None' 
                                else ee for ee in _tmp[:, -1].tolist()]
                    break
            else:
                logging.error(
                        'Aggregation vector -- {} -- not found'
                        .format(str(entry)))
    
    # build the summary aggregation vector
    def _rep(ll, ii, vv): ll[ii] = vv
    miss_val = source.get( 'miss', 'REST' )

    vec_list = [agg_dict[ee] for ee in agg_vec]
    out = [None, ] * len(vec_list[0])
    for currvec in vec_list:
        if len(currvec) != len(out):
            logging.warn('Inconsistent vector length')
        [_rep(out, ind, val) for ind, val 
                in enumerate(currvec) if not out[ind]]

    [_rep(out, ind, miss_val) for ind, val in enumerate(out) if not val]

    return out
    
def parse_exiobase22(path, charact = None, iosystem = None, 
                     version = 'exiobase 2.2', popvector = 'exio2' ):
    """ Parse the exiobase 2.2 source files for the IOSystem 
   
    The function parse product by product and industry by industry source file
    with flow matrices (Z)

    Parameters
    ----------
    path : string
        Path to the EXIOBASE source files
    charact : string, optional
        Filename with path to the characterisation matrices for the extensions
        (xls).  This is provided together with the EXIOBASE system and given as
        a xls file. The four sheets  Q_factorinputs, Q_emission, Q_materials and
        Q_resources are read and used to generate one new extensions with the
        impacts 
    iosystem : string, optional
        Note for the IOSystem, recommended to be 'pxp' or 'ixi' for
        product by product or industry by industry.
        However, this can be any string and can have more information if needed
        (eg for different technology assumptions)
        The string will be passed to the IOSystem.
    version : string, optional
        This can be used as a version tracking system. Default: exiobase 2.2 
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
    EXIOError
        If the exiobase source files are not complete in the given path

    """
    path = path.rstrip('\\')
    path = os.path.abspath(path)

    # standard file names in exiobase
    files_exio = dict(

        # exiobase 2.2
        Z = 'mrIot_version2.2.0.txt',
        Y = 'mrFinalDemand_version2.2.0.txt',
        F_fac = 'mrFactorInputs_version2.2.0.txt',
        F_emissions = 'mrEmissions_version2.2.0.txt',
        F_materials = 'mrMaterials_version2.2.0.txt',
        F_resources = 'mrResources_version2.2.0.txt',
        FY_emissions = 'mrFDEmissions_version2.2.0.txt',
        FY_materials = 'mrFDMaterials_version2.2.0.txt',

        # old exiobase 2.1 filenames
        #Z = 'mrIot.txt',
        #Y = 'mrFinalDemand.txt',
        #F_fac = 'mrFactorInputs.txt',
        #F_emissions = 'mrEmissions.txt',
        #F_materials = 'mrMaterials.txt',
        #F_resources = 'mrResources.txt',
        #FY_emissions = 'mrFDEmissions.txt',
        #FY_materials = 'mrFDMaterials.txt',
        )

    # check if source exiobase is complete
    _intersect = [val for val in files_exio.values() 
            if val in os.listdir(path)]
    if len(_intersect) != len(files_exio.values()):
        raise core.EXIOError('EXIOBASE files missing')

    # number of row and column headers in EXIOBASE 
    head_col = dict()
    head_row = dict()
    head_col['Z'] = 3 #  number of cols containing row headers at the beginning
    head_row['Z'] = 2 #  number of rows containing col headers at the top
    head_col['Y'] = 3
    head_row['Y'] = 2
    head_col['F_fac'] = 2
    head_row['F_fac'] = 2
    head_col['F_emissions'] = 3
    head_row['F_emissions'] = 2
    head_col['F_materials'] = 2
    head_row['F_materials'] = 2
    head_col['F_resources'] = 3
    head_row['F_resources'] = 2
    head_col['FY_emissions'] = 3
    head_row['FY_emissions'] = 2
    head_col['FY_materials'] = 2
    head_row['FY_materials'] = 2

    # read the data into pandas
    logging.info('Read exiobase2 from {}'.format(path))
    data = {key:pd.read_table(os.path.join(path, files_exio[key]), 
            index_col = list(range(head_col[key])), 
            header = list(range(head_row[key]))) 
            for key in files_exio}
    
    # refine multiindex and save units
    data['Z'].index.names = ['region', 'sector', 'unit']
    data['Z'].columns.names = ['region', 'sector']
    data['unit'] = pd.DataFrame(data['Z'].iloc[:, 0].
                    reset_index(level='unit').unit)
    data['Z'].reset_index(level='unit', drop=True, inplace=True)
    data['Y'].index.names = ['region', 'sector', 'unit']
    data['Y'].columns.names = ['region', 'category']
    data['Y'].reset_index(level='unit', drop=True, inplace=True)
    ext_unit = dict()
    for key in ['F_fac', 'F_emissions', 'F_materials', 
                'F_resources', 'FY_emissions', 'FY_materials']:
        if head_col[key] == 3:
            data[key].index.names = ['stressor', 'compartment', 'unit']
        if head_col[key] == 2:
            data[key].index.names = ['stressor', 'unit']
        if 'FY' in key:
            data[key].columns.names = ['region', 'category']
            data[key].reset_index(level='unit', drop=True, inplace=True)
        else:
            data[key].columns.names = ['region', 'sector']
            ext_unit[key] = pd.DataFrame(data[key].iloc[:, 0].
                                reset_index(level='unit').unit)
            data[key].reset_index(level='unit', drop=True, inplace=True)
            if key is 'F_resources': 
                data[key].reset_index(level='compartment', 
                                        drop=True, inplace=True)
                ext_unit[key].reset_index(level='compartment', 
                                        drop=True, inplace=True)


    # build the extensions
    ext=dict()
    ext['factor_inputs'] = {'F':data['F_fac'], 
                            'unit':ext_unit['F_fac'], 'name':'factor input'}
    ext['emissions'] = {'F':data['F_emissions'], 'FY':data['FY_emissions'], 
                            'unit':ext_unit['F_emissions'], 'name':'emissons'}
    ext['materials'] = {'F':data['F_materials'], 'FY':data['FY_materials'], 
                            'unit':ext_unit['F_materials'], 
                            'name':'material extraction'}
    ext['resources'] = {'F':data['F_resources'], 
                            'unit':ext_unit['F_resources'], 'name':'resources'}

    # read the characterisation matrices if available
    # and build one extension with the impacts
    if charact:
        # dict with correspondence to the extensions
        Qsheets =  {'Q_factorinputs':'factor_inputs',   
                    'Q_emission':'emissions', 
                    'Q_materials':'materials', 
                    'Q_resources':'resources'}
        Q_head_col = dict()
        Q_head_row = dict()
        Q_head_col_rowname = dict()
        Q_head_col_rowunit= dict()
        Q_head_col_metadata= dict()
        # number of cols containing row headers at the beginning
        Q_head_col['Q_emission'] = 4 
        # number of rows containing col headers at the top - this will be
        # skipped
        Q_head_row['Q_emission'] = 3 
        # assuming the same classification as in the extensions
        Q_head_col['Q_factorinputs'] = 2 
        Q_head_row['Q_factorinputs'] = 2 
        Q_head_col['Q_resources'] = 2 
        Q_head_row['Q_resources'] = 3 
        Q_head_col['Q_materials'] = 2 
        Q_head_row['Q_materials'] = 2

        #  column to use as name for the rows
        Q_head_col_rowname['Q_emission'] = 1 
        Q_head_col_rowname['Q_factorinputs'] = 0 
        Q_head_col_rowname['Q_resources'] = 0 
        Q_head_col_rowname['Q_materials'] = 0 

        # column to use as unit for the rows which gives also the last column
        # before the data
        Q_head_col_rowunit['Q_emission'] = 3  
        Q_head_col_rowunit['Q_factorinputs'] = 1
        Q_head_col_rowunit['Q_resources'] = 1 
        Q_head_col_rowunit['Q_materials'] = 1 

        charac_data = {Qname:pd.read_excel(charact, 
                        sheetname = Qname, 
                        skiprows = list(range(0, Q_head_row[Qname])), 
                        header=None) 
                       for Qname in Qsheets} 

        _units = dict()
        # temp for the calculated impacts which than 
        # get summarized in the 'impact'
        _impact = dict()  
        impact = dict()
        for Qname in Qsheets:
            # unfortunately the names in Q_emissions are 
            # not completely unique - fix that
            _index = charac_data[Qname][Q_head_col_rowname[Qname]]
            if Qname is 'Q_emission':
                _index[42] = _index[42] + ' 2008'
                _index[43] = _index[43] + ' 2008'
                _index[44] = _index[44] + ' 2010'
                _index[45] = _index[45] + ' 2010'
            charac_data[Qname].index = (
                    charac_data[Qname][Q_head_col_rowname[Qname]])

            _units[Qname] = pd.DataFrame(
                    charac_data[Qname].iloc[:, Q_head_col_rowunit[Qname]])
            _units[Qname].columns = ['unit']
            _units[Qname].index.name = 'impact'
            charac_data[Qname] = charac_data[Qname].ix[:, 
                                            Q_head_col_rowunit[Qname]+1:]
            charac_data[Qname].index.name = 'impact'
            
            if 'FY' in ext[Qsheets[Qname]]:
                _FY = ext[Qsheets[Qname]]['FY'].values
            else:
                _FY = np.zeros([ext[Qsheets[Qname]]['F'].shape[0], 
                                data['Y'].shape[1]])
            _impact[Qname] = {'F':charac_data[Qname].dot(
                                ext[Qsheets[Qname]]['F'].values),
                              'FY':charac_data[Qname].dot(_FY),
                              'unit':_units[Qname]
                             }

        impact['F'] = (_impact['Q_factorinputs']['F']
                        .append(_impact['Q_emission']['F'])
                        .append(_impact['Q_materials']['F'])
                        .append(_impact['Q_resources']['F']))
        impact['FY'] = (_impact['Q_factorinputs']['FY']
                        .append(_impact['Q_emission']['FY'])
                        .append(_impact['Q_materials']['FY'])
                        .append(_impact['Q_resources']['FY']))
        impact['F'].columns = ext['emissions']['F'].columns 
        impact['FY'].columns = ext['emissions']['FY'].columns 
        impact['unit'] = (_impact['Q_factorinputs']['unit']
                        .append(_impact['Q_emission']['unit'])
                        .append(_impact['Q_materials']['unit'])
                        .append(_impact['Q_resources']['unit']))
        impact['name'] = 'impact'
        ext['impacts'] = impact

    
    if popvector is 'exio2':
        popdata = pd.read_table(os.path.join(PYMRIO_PATH['exio20'], 
                    './misc/population.txt'), 
                    index_col=0).astype(float)
    else:
        popdata =  popvector

    return IOSystem( Z = data['Z'], Y = data['Y'], unit = data['unit'], population = popdata, **ext)


# program code
if __name__ == "__main__":
    logging.warn("This module can't be run directly")
    logging.info("%s", __doc__)
 
