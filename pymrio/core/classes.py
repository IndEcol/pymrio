""" 
Generic classes for pymrio

Classes and function here should not be used directly. Use the API methods from the pymrio module instead.

"""

import os
import copy
import logging
import pickle
import pandas as pd
import configparser

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
        parastr = ', '.join([attr for attr in self.__dict__ if self.__dict__[attr] is not None and '__' not in attr])
        return startstr + parastr

    def reset(self):
        """ Removes all attributes which can not be aggregates and must be recalculated after agg. 

        This can be used to force a recalculation of the IOSystem and/or Extensions after modifying these.

        The attributes which should be removed must be defined in self.__non_agg_attributes__ (include all non aggregated standard attributes)
        """
        [setattr(self,key,None) for key in self.__non_agg_attributes__]

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
                ind = getattr(self, df).columns.get_level_values('category').unique()
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
                ind = getattr(self, df).columns.get_level_values('region').unique()
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
                ind = getattr(self, df).columns.get_level_values('sector').unique()
                if entries:
                    if type(entries) is str: entries = [entries]
                    ind = ind.tolist()
                    return [None if ee not in entries else ee for ee in ind]
                else:
                    return ind
        else:
            logging.warn("No attributes available to get sectors")
            return None

    def get_DataFrame(self, data=False):
        """ Returns a generator which gives all panda.DataFrames in the system
        
        Note
        ----
        For IOSystem this does not include the DataFrames in the extensions.

        Parameters
        ----------
        data : boolean, optional
           If True, returns a generator which yields the DataFrames.
           If False, returns a generator which yields only the names of the DataFrames

        Returns
        -------
        generator

        """

        for key in self.__dict__:
            if type(self.__dict__[key]) is pd.DataFrame: 
                if data:
                    yield getattr(self, key)
                else:
                    yield key

    def save(self, path, table_format = 'txt', sep = '\t', table_ext = None, float_format = '%.12g'):
        """ Saves the system as text or binary pickle files.
    
        Tables (dataframes) of the current system are saved as text or binary pickle files, meta data (all other attributes) and the specifications of the tables are saved in a ini file.

        Note
        ----
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

        if str(type(self)) ==  "<class 'pymrio.IOSystem'>":
            io_ini['systemtype']['systemtype'] = 'IOSystem'
        elif str(type(self)) ==  "<class 'pymrio.Extension'>":
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



