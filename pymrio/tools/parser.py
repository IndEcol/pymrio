"""
Various parser for available MRIOs and files in a similar format


KST 20140903
"""

import os
import logging
import pandas as pd
import numpy as np

from pymrio.core.mriosystem import IOSystem
from pymrio.core.mriosystem import Extension

pd.set_option('chained_assignment',None)   # There is one chained_assignment somewhere TODO: find and fix

# constants and global variables
from pymrio.core.constants import PYMRIO_PATH

def parse_exio_ext(file, index_col, name, drop_compartment = True, 
        version = None, year = None, iosystem = None, sep = ',' ):
    """ Parse an EXIOBASE like extension file into pymrio.Extension  

    EXIOBASE like extensions files are assumed to have two
    rows which are used as columns multiindex (region and sector)
    and up to three columns for the row index (see Parameters).
     
    Notes
    -----
    So far this only parses factor of production extensions F (not 
    final demand extensions FY nor coeffiecents S).

    Parameters
    ----------

    file : string
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

    file = os.path.abspath(file)
    
    F = pd.read_table(file, 
            header = [0,1], 
            index_col = list(range(index_col)),
            sep = sep)

    F.columns.names = ['region', 'sector']

    if index_col == 1:
        F.index.names = ['stressor']

    elif index_col == 2:
        F.index.names = ['stressor', 'unit']

    elif index_col == 3:
        F.index.names = ['stressor', 'compartment', 'unit']

    else:
        F.reset_index(level = list(range(3,index_col)),
                         drop = True,
                         inplace = True)
        F.index.names = ['stressor', 'compartment', 'unit']

    unit = None
    if index_col > 1:
        unit = pd.DataFrame(F.iloc[:, 0].
                reset_index(level='unit').unit)
        F.reset_index(level='unit', drop=True, inplace=True)

    if drop_compartment:
        F.reset_index(level='compartment', 
                drop=True, inplace=True)
        unit.reset_index(level='compartment', 
                drop=True, inplace=True)

    return Extension(name = name, 
                            F = F, 
                            unit = unit,
                            iosystem = iosystem,
                            version = version,
                            year = year,
                            )

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
        raise pymrio.core.EXIOError('EXIOBASE files missing')

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
                _index.iloc[42] = _index.iloc[42] + ' 2008'
                _index.iloc[43] = _index.iloc[43] + ' 2008'
                _index.iloc[44] = _index.iloc[44] + ' 2010'
                _index.iloc[45] = _index.iloc[45] + ' 2010'
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
                              'FY':charac_dat[Qname].dot(_FY),
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


def __parse_wiod(path, year = None, sector_names = 'full',
        version = 'exiobase 2.2', popvector = 'exio2'):
    """ Parse the wiod source files for the IOSystem 
    
    WIOD provides the MRIO tables in excel - format (xlsx) at
    http://www.wiod.org/new_site/database/wiots.htm (release November 2013).
    To use WIOD in pymrio these (for the year of analysis) must be downloaded. The
    interindustry matrix of these files gets parsed in IOSystem.Z, the
    additional information is included as factor_input extension (value
    added,...)

    The folder with these xslx must than be passed to the WIOD parsing
    function. This folder may contain folders with the extension data. Every
    folder within the root folder will be parsed for extension data and will be
    added to the IOSystem. The WIOD database offers the download of the
    environmental extensions as zip files. These can be read directly by the
    parser. In case a zip file and a folder is available, the data is read from
    the folder. 

    If a WIOD SEA file is present (at the root of path or in a folder named
    'SEA' - only one file!), the labor data of this file gets included in the
    factor_input extension (calculated for the the three skill levels
    available). The monetary data in this file is not added because it is only
    given in national currency.

    Since the "World Input-Output Tables in previous years' prices" are still
    under construction (20141129), no parser for these is provided.

    Some of the meta-parameter of the IOSystem are set automatically based on
    the values given in the first four cells and the name of the WIOD data files (base
    year, version, price, iosystem). These can be overwritten afterwards if needed.

    Parameters
    ----------
    path : string
        Path to the folder with the WIOD source files. In case that the path to
        a specific file is given, only this will be parsed irrespective of the
        values given in year.
    year : int, str, optional
        Which year in the path should be parsed. The years can be given with
        four or two digits (eg [2012 or 12]). If the given path contains a
        specific file, the value of year will not be used (but inferred from
        the meta data)- otherwise it must be given For the monetary data the
        parser searches for files with 'wiot - two digit year'.
    sector_names : string, optional
        WIOD provides three different sector naming, which can be specified for
        the IOSystem: TODO: put also names used in the dict in here
        full sector names: 'full' - default
        codes : 'code'
        c-values : 'c'
    TODO popvector : string or pd.DataFrame, optional
        The population vector for the countries.  This can be given as
        pd.DataFrame(index = population, columns = countrynames) or, (default)
        will be taken from the pymrio module. If popvector = None no population
        data will be passed to the IOSystem.

    Yields
    -------
    IOSystems
        Ordered by years given (in the order given, otherwise the oldest first)
        TODO: change to one output

    Raises
    ------
    TODO WIODError
        If the wiod source files are not complete in the given path
    TODO Warning if extension data could not be found for the specific year

    """

    # DEBUG:
    #path =  r'D:\S_storage\data\WIOD'
    #path =  r'D:\S_storage\data\WIOD\wiot00_row_apr12.xlsx'
    path = r'S:\data\WIOD\\wiot00_row_apr12.xlsx'
    #year = 2008
    # END DEBUG

    # Path manipulation, should work cross platform
    path = path.rstrip('\\')
    path = path.encode('unicode-escape')
    path = os.path.abspath(path)

    # wiot start and end
    wiot_ext = b'.xlsx'
    wiot_start = b'wiot'

    # determine which wiod file to be parsed
    if not os.path.isdir(path):    
        # 1. case - one file specified in path
        if os.path.isfile(path):
            wiot_file = path
        else:
            # just in case the ending was forgotten
            wiot_file = path + wiot_ext
    else:
        # 2. case: directory given - build wiot_file with the value given in year
        if not year:
            # TODO: raise WIOD error and return
            print('year not found')
            pass
        year_two_digit = str(year)[-2:].encode('unicode-escape')
        wiot_file_list = [fl for fl in os.listdir(path)
                             if (fl[:6] == wiot_start + year_two_digit
                                 and os.path.splitext(fl)[1] == wiot_ext)]
        if len(wiot_file_list) != 1:
            # TODO: raise WIOD error
            print('multiple files for given year of file not found- specify single file in paramters')

        wiot_file = os.path.join(path, wiot_file_list[0])
    
    wiot_file = wiot_file.decode()
    root_path = os.path.split(wiot_file)[0]   
    if not os.path.exists(wiot_file):
        # TODO: raise WIOD error
        print('wiot_file not found')

    # wiot file structure
    wiot_meta = {
            'col' : 0,   # column of the meta information
            'year' : 0,  # rest: rows with the data
            'iosystem' : 2,
            'unit' : 3,
            'end_row' : 4,
            }
    wiot_header = {    # the header indexes are the same for rows after removing the first two lines (wiot_empty_top_rows)
            'code' : 0,
            'sector_names' : 1,
            'region' : 2,
            'c_code' : 3,
            }
    wiot_empty_top_rows = [0,1]

    wiot_marks = {   # special marks 
            'last_interindsec' : 'c35',    # last sector of the interindustry
            'tot_facinp' : ['r60', 'r69'], # useless totals to remove from factinp
            'total_column' : [-1],         # the total column in the whole data
            }

    wiot_sheet = 0   # assume the first one is the one with the data.

    # Wiod has an unfortunate file structure with overlapping metadata and
    # header. In order to deal with that first the full file is read.
    wiot_data = pd.read_excel(wiot_file,
                            sheetname = wiot_sheet,
                            header = None)

    # get meta data
    wiot_year = wiot_data.iloc[wiot_meta['year'],wiot_meta['col']][-4:]
    wiot_iosystem = wiot_data.iloc[wiot_meta['iosystem'],wiot_meta['col']].rstrip(')').lstrip('(')
    _wiot_unit = wiot_data.iloc[wiot_meta['unit'],wiot_meta['col']].rstrip(')').lstrip('(')

    # remove meta data, empty rows, total column
    wiot_data.iloc[0:wiot_meta['end_row'],wiot_meta['col']] = np.NaN   
    wiot_data.drop(wiot_empty_top_rows, 
                    axis = 0, inplace = True) 
    wiot_data.drop(wiot_data.columns[wiot_marks['total_column']], 
                    axis = 1, inplace = True)
        #at this stage row and column header should have the same size but 
        # the index starts now at two - replace/reset to row numbers
    wiot_data.index = range(wiot_data.shape[0])

    # get the end of the interindustry matrix
    _lastZcol = wiot_data[
        wiot_data.iloc[:,wiot_header['c_code']] == wiot_marks['last_interindsec']
        ].index[-1]
    _lastZrow = wiot_data[
        wiot_data.iloc[wiot_header['c_code'],:] == wiot_marks['last_interindsec']
        ].index[-1]

    if _lastZcol != _lastZrow:
        print('wiod parsing error, interindustry not symetric')
    else:
        Zshape = (_lastZrow, _lastZcol)
        
    # separate factor input extension and remove 
    # totals in the first and last row
    facinp = wiot_data.iloc[Zshape[0]+1:,:] 
    facinp.drop(
        facinp[facinp[wiot_header['c_code']].isin(wiot_marks['tot_facinp'])].index,
        inplace = True,
        axis = 0
        )

    Z = wiot_data.iloc[:Zshape[0]+1,:Zshape[1]+1].copy()
    Y = wiot_data.iloc[:Zshape[0]+1,Zshape[1]+1:].copy()
    F_fac = facinp.iloc[:,:Zshape[1]+1].copy()
    FY_fac = facinp.iloc[:,Zshape[1]+1:].copy()

    # set the index/columns, work with code b/c these are also used in the extensions
    Z.set_index([wiot_header['region'], wiot_header['code']], inplace = True, drop = False)
    index_wiot_headers = [nr for nr in wiot_header.values()]
    Z = Z.iloc[max(index_wiot_headers)+1:, max(index_wiot_headers)+1:]
    Z.index.names = ['region', 'sector']
    Z.columns = Z.index
    
    indexY_col_head = Y.iloc[[wiot_header['region'], wiot_header['c_code']],:]    # no code for these, use c_code
    Y.columns = pd.MultiIndex.from_arrays(indexY_col_head.values, names = Z.index.names)
    Y = Y.iloc[max(index_wiot_headers)+1:, :]
    Y.index = Z.index

    F_fac.set_index([wiot_header['sector_names']], inplace = True, drop = False) # also c_code missing, use names
    F_fac.index.names = ['inputtype']
    F_fac = F_fac.iloc[:, max(index_wiot_headers)+1:]
    F_fac.columns = Z.columns
    FY_fac.columns = Y.columns
    FY_fac.index = F_fac.index

    wiot_sector_lookup = wiot_data[wiot_data[2] == 'USA'].iloc[:,0:max(index_wiot_headers)+1] # assuming USA is present in every WIOT year 
    wiot_sector_lookup.columns = [entry[1] for entry in sorted(zip(wiot_header.values(), wiot_header.keys()))]

    # convert from object to float (was object because mixed float,str)
    Z = Z.astype('float')
    Y = Y.astype('float')
    F_fac = F_fac.astype('float')
    FY_fac = FY_fac.astype('float')

    # save the units
    Z_units = pd.DataFrame(Z.iloc[:,0])
    Z_units.columns = ['unit'] 
    Z_units['unit'] = _wiot_unit

    F_fac_units = pd.DataFrame(F_fac.iloc[:,0])
    F_fac_units.columns = ['unit'] 
    F_fac_units['unit'] = _wiot_unit

    # SEA file - append to factor_inputs if available
    sea_ext = '.xlsx'
    sea_start = 'WIOD_SEA'

    # check if a separate SEA folder exists
    _SEA_folder = os.path.join(root_path, 'SEA')
    if not os.path.exists(_SEA_folder):
        _SEA_folder = root_path

    sea_folder_content  = [ff for ff in os.listdir(_SEA_folder) 
                            if os.path.splitext(ff)[-1] == sea_ext and
                            ff[:8] == sea_start]

    if sea_folder_content:
        # take the first found file (there should be only one...) 
        sea_file = os.path.join(_SEA_folder,sorted(sea_folder_content)[0])
        sea_data, sea_units = __get_WIOD_SEA_extension(file = sea_file, year = year) #TODO make year robust - compare meta data with given year

        # append does not work with multiindex columns - remove temporarily 
        _sea = pd.DataFrame(data=sea_data.values, index=sea_data.index)
        _F_fac = pd.DataFrame(data=F_fac.values, index=F_fac.index)
        _df_append = _F_fac.append(_sea)
        _df_append.columns = F_fac.columns
        F_fac = _df_append
        F_fac_units = F_fac_units.append(sea_units)

        # make FY_fac consistent
        _FY_sea = pd.DataFrame(index = sea_data.index, columns=FY_fac.columns)
        _FY_sea = pd.DataFrame(data=_FY_sea.values, index = _FY_sea.index)
        _FY_sea.fillna(0, inplace = True)

        _FY_fac = pd.DataFrame(data=FY_fac.values, index=FY_fac.index)
        _df_append = _FY_fac.append(_FY_sea)
        _df_append.columns = FY_fac.columns
        FY_fac = _df_append

    ext = dict()
    ext['factor_inputs'] = {'F':F_fac,
                            'FY':FY_fac,
                            'year' : wiot_year,
                            'iosystem' : wiot_iosystem,
                            'unit': F_fac_units, 
                            'name':'factor input',
                            }


    wiod = IOSystem(Z = Z, Y = Y, 
                    year = wiot_year,
                    iosystem = wiot_iosystem,
                    unit = Z_units,
                    **ext) 


    # Next steps environmental extensions
        #START - check again if SEA correct, then start with env extensions
        # TODO: get canonical names of environmental extensions (note sheet) include in dict
            # check if the name can be taken from the path or is present within
            # the xls file of the extension
        # TODO: build a dict with the format (following wiot_meta) and possible files - read a subset of these
            # two kinds of extension with different format, but quite similar
            #   lower case names and upper case names have similar format
            #   for the lower case the unit could be taken from the file but better not
            #   build a dict with the spec and the unit
            # fd emissions always present - include always
            # loop over countries in Z and get values if country exist - sheet named after year
        # TODO: check if folder or zip is present for each (how to read zip?)
        # TODO: try read for each sheet based on year (read all files - save in
        # a dict with the beginning of the files (iso3))

    # TODO: Function for main loop over all years
    return locals()

def __get_WIOD_SEA_extension(file, year, data_sheet = 'DATA'):
    """ Utility function to get the useful data for the extension from the SEA file in WIOD

    This script is based on the structure in the WIOD_SEA_July14 file, and also 
    fixes the wrong index ROU (to ROM), and appends RoW if missing
    Missing values are set to zero.

    Parameters
    ----------
    seafile : string
        SEA file with full path
    year : str or int
        Year to return for the extension
    sea_data_sheet : string, optional
        Worksheet with the SEA data in the excel file

    Returns
    -------
    SEA data as extension for the WIOD MRIO
    """

    # read data 
    df_sea = pd.read_excel(file, 
            sheetname = data_sheet,
            header = 0,
            index_col = [0,1,2,3])

    # fix years
    ic_sea = df_sea.columns.tolist()
    ic_sea = [yystr.lstrip('_') for yystr in ic_sea]
    df_sea.columns = ic_sea

    ds_sea = df_sea[str(year)]

    # get useful data (employment)
    mt_sea = ['EMP', 'EMPE', 'H_EMP', 'H_EMPE'] 
    ds_use_sea = pd.concat([ds_sea.xs(key = vari, level = 'Variable', drop_level = False) for vari in mt_sea])
    ds_use_sea.drop(labels = 'TOT', level = 'Code', inplace = True)
    ds_use_sea.reset_index('Description', drop = True, inplace = True)

    # correct for wrong index in the SEA file
    df_use_sea = ds_use_sea.reset_index('Country')
    df_use_sea[df_use_sea['Country'] == 'ROU'] = 'ROM' 
    ds_use_sea = df_use_sea.set_index('Country', append = True, drop = True, ).iloc[:,0]

    # append the RoW entry
    if not 'RoW' in ds_use_sea.index.get_level_values('Country'):
        ds_RoW = ds_use_sea.xs('USA', level = 'Country', drop_level = False)
        ds_RoW.ix[:] = 0;
        df_RoW = ds_RoW.reset_index()
        df_RoW['Country'] = 'RoW'
        ds_use_sea = pd.concat([ds_use_sea.reset_index(), df_RoW]).set_index(['Country', 'Code', 'Variable'])

    ds_use_sea.fillna(value=0, inplace = True)
    df_use_sea = ds_use_sea.unstack(level = ['Country', 'Code'])[str(year)]
    df_use_sea.index.names = ['inputtype']
    df_use_sea.columns.names = ['region', 'sector']

    df_units = pd.DataFrame(
                data = [    # this data must be in the same order as mt_sea
                    'thousand persons', 
                    'thousand persons', 
                    'mill hours', 
                    'mill hours', 
                    ],
                columns = ['unit'],
                index = df_use_sea.index)

    return df_use_sea, df_units

