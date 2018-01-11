"""
Methods to load previously save mrios

"""

import collections
import configparser
import logging
import json
import re
import pandas as pd
import os

from pymrio.core.constants import PYMRIO_PATH

from pymrio.core.mriosystem import IOSystem
from pymrio.core.mriosystem import Extension
from pymrio.tools.iometadata import MRIOMetaData

from pymrio.core.constants import DEFAULT_FILE_NAMES
from pymrio.core.constants import GENERIC_NAMES


# Exceptions
class ReadError(Exception):
    """ Base class for errors occuring while reading MRIO data """
    pass


def load_all(path, include_core=True, subfolders=None):
    """ Loads a full IO system with all extension in path

    By default, all subfolders containing a json parameter file
    (as defined in DEFAULT_FILE_NAMES['filepara']: metadata.json)
    are parsed. If only a subset should be used, pass a to subfolders
    giving the names of these.
    """
    def clean(varStr):
        """ get valid python name from folder
        """
        return re.sub('\W|^(?=\d)', '_', varStr)

    io = load(path, include_core=include_core)

    if subfolders is None:
        subfolders = [d for d in os.listdir(path)
                      if os.path.isdir(os.path.join(path, d))]

    for subfolder_name in subfolders:
        subfolder_full = os.path.join(path, subfolder_name)

        if os.path.isfile(os.path.join(subfolder_full,
                                       DEFAULT_FILE_NAMES['filepara'])):
            ext = load(subfolder_full, include_core=include_core)
            setattr(io, clean(subfolder_name), ext)
            io.meta._add_fileio("Added satellite account "
                                "from {}".format(subfolder_full))
        else:
            continue

    return io


def load(path, include_core=True):
    """ Loads a IOSystem or Extension previously saved with pymrio

    This function can be used to load a IOSystem or Extension specified in a
    ini file. DataFrames (tables) are loaded from text or binary pickle files.
    For the latter, the extension .pkl or .pickle is assumed, in all other case
    the tables are assumed to be in .txt format.

    Parameters
    ----------

    path : string
        path or ini file name for the data to load

    include_core : boolean, optional
        If False the load method does not include A, L and Z matrix. This
        significantly reduces the required memory if the purpose is only
        to analyse the results calculated beforehand.

    Returns
    -------

        IOSystem or Extension class depending on systemtype in the json file
        None in case of errors

    """
    path = path.rstrip('\\')
    path = os.path.abspath(path)

    if not os.path.exists(path):
        raise ReadError('Given path does not exist')
        return None

    para_file_path = os.path.join(path, DEFAULT_FILE_NAMES['filepara'])
    if not os.path.isfile(para_file_path):
        raise ReadError('No file parameter file found')
        return None

    with open(para_file_path, 'r') as pf:
        file_para = json.load(pf)

    if file_para['systemtype'] == GENERIC_NAMES['iosys']:
        meta_file_path = os.path.join(path, DEFAULT_FILE_NAMES['metadata'])
        ret_system = IOSystem(meta=MRIOMetaData(location=meta_file_path))
        ret_system.meta._add_fileio("Loaded IO system from {}".format(path))
    elif file_para['systemtype'] == GENERIC_NAMES['ext']:
        ret_system = Extension(file_para['name'])
    else:
        raise ReadError('Type of system no defined in the file parameters')
        return None

    for key in file_para['files']:
        if not include_core:
            if key in ['A', 'L', 'Z']:
                continue

        file_name = file_para['files'][key]['name']
        full_file_name = os.path.join(path, file_name)
        nr_index_col = file_para['files'][key]['nr_index_col']
        nr_header = file_para['files'][key]['nr_header']

        logging.info('Load data from {}'.format(full_file_name))

        _index_col = list(range(int(nr_index_col)))
        _header = list(range(int(nr_header)))

        if _index_col == [0]:
            _index_col = 0
        if _header == [0]:
            _header = 0

        if (os.path.splitext(full_file_name)[1] == '.pkl' or
                os.path.splitext(full_file_name)[1] == '.pickle'):
            setattr(ret_system, key,
                    pd.read_pickle(full_file_name))
        else:
            setattr(ret_system, key,
                    pd.read_table(full_file_name,
                                  index_col=_index_col,
                                  header=_header))

    return ret_system


def _load_all_ini_based_io(path, **kwargs):
    """ DEPRECATED: For convert a previous version to the new json format

    Loads the whole IOSystem with Extensions given in path

    This just calls pymrio.load with recursive = True. Apart from that the
    same parameter can as for .load can be used.

    Parameters
    ----------
    path : string
        path or ini file name for the data to load
    **kwargs : key word arguments, optional
            This will be passed directly to the load method

    Returns
    -------
    IOSystem
    None in case of errors
    """
    return _load_ini_based_io(path, recursive=True, **kwargs)


def _load_ini_based_io(path, recursive=False, ini=None,
                       subini={}, include_core=True,
                       only_coefficients=False):
    """ DEPRECATED: For convert a previous version to the new json format

    Loads a IOSystem or Extension from a ini files

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

    if ini:
        ini_file_name = ini

    if not os.path.exists(path):
        raise ReadError('Given path does not exist')
        return None

    if not ini_file_name:
        _inifound = False
        for file in os.listdir(path):
            if os.path.splitext(file)[1] == '.ini':
                if _inifound:
                    raise ReadError(
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
        ret_system = IOSystem(name=name)
    elif systemtype == 'Extension':
        ret_system = Extension(name=name)
    else:
        raise ReadError('System not defined in ini')
        return None

    for key in io_ini['meta']:
        setattr(ret_system, key, io_ini.get('meta', key, fallback=None))

    for key in io_ini['files']:
        if '_nr_index_col' in key:
            continue
        if '_nr_header' in key:
            continue

        if not include_core:
            not_to_load = ['A', 'L', 'Z']
            if key in not_to_load:
                continue

        if only_coefficients:
            _io = IOSystem()
            if key not in _io.__coefficients__ + ['unit']:
                continue

        file_name = io_ini.get('files', key)
        nr_index_col = io_ini.get(
            'files', key + '_nr_index_col', fallback=None)
        nr_header = io_ini.get('files', key + '_nr_header', fallback=None)

        if (nr_index_col is None) or (nr_header is None):
            raise ReadError(
                    'Index or column specification missing for {}'.
                    format(str(file_name)))
            return None

        _index_col = list(range(int(nr_index_col)))
        _header = list(range(int(nr_header)))

        if _index_col == [0]:
            _index_col = 0
        if _header == [0]:
            _header = 0
        file = os.path.join(path, file_name)
        logging.info('Load data from {}'.format(file))

        if (os.path.splitext(file)[1] == '.pkl' or
                os.path.splitext(file)[1] == '.pickle'):
            setattr(ret_system, key,
                    pd.read_pickle(file))
        else:
            setattr(ret_system, key,
                    pd.read_table(file,
                                  index_col=_index_col,
                                  header=_header))

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
                            raise ReadError(
                                'Found multiple ini files in subfolder '
                                '{} - specify one'.format(subpath))
                            return None
                        subini_file_name = file
                        _inifound = True
            if not _inifound:
                continue

            # read the ini
            subio_ini = configparser.RawConfigParser()
            subio_ini.optionxform = lambda option: option

            subio_ini.read(os.path.join(subpath, subini_file_name))

            systemtype = subio_ini.get('systemtype', 'systemtype',
                                       fallback=None)
            name = subio_ini.get('meta', 'name',
                                 fallback=os.path.splitext(
                                     subini_file_name)[0])

            if systemtype == 'IOSystem':
                raise ReadError('IOSystem found in subfolder {} - '
                                'only extensions expected'.format(subpath))
                return None
            elif systemtype == 'Extension':
                sub_system = Extension(name=name)
            else:
                raise ReadError('System not defined in ini')
                return None

            for key in subio_ini['meta']:
                setattr(sub_system, key, subio_ini.get('meta', key,
                                                       fallback=None))

            for key in subio_ini['files']:
                if '_nr_index_col' in key:
                    continue
                if '_nr_header' in key:
                    continue

                if only_coefficients:
                    _ext = Extension('temp')
                    if key not in _ext.__coefficients__ + ['unit']:
                        continue

                file_name = subio_ini.get('files', key)
                nr_index_col = subio_ini.get('files', key + '_nr_index_col',
                                             fallback=None)
                nr_header = subio_ini.get('files', key + '_nr_header',
                                          fallback=None)

                if (nr_index_col is None) or (nr_header is None):
                    raise ReadError('Index or column specification missing '
                                    'for {}'.format(str(file_name)))
                    return None

                _index_col = list(range(int(nr_index_col)))
                _header = list(range(int(nr_header)))

                if _index_col == [0]:
                    _index_col = 0
                if _header == [0]:
                    _header = 0
                file = os.path.join(subpath, file_name)
                logging.info('Load data from {}'.format(file))
                if (os.path.splitext(file)[1] == '.pkl' or
                        os.path.splitext(file)[1] == '.pickle'):
                    setattr(sub_system, key,
                            pd.read_pickle(file))
                else:
                    setattr(sub_system, key,
                            pd.read_table(file,
                                          index_col=_index_col,
                                          header=_header))

                # get valid python name from folder
                def clean(varStr):
                    return re.sub('\W|^(?=\d)', '_', varStr)

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

        For development: This function can be used as an example of
        how to parse an IOSystem

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
    file_data = collections.namedtuple(
            'file_data', ['file_name', 'row_header', 'col_header', 'unit_col'])

    # file names and header specs of the system
    test_system = dict(
        Z=file_data(file_name='trade_flows_Z.txt',
                    row_header=2, col_header=3, unit_col=2),
        Y=file_data(file_name='finald_demand_Y.txt',
                    row_header=2, col_header=3, unit_col=2),
        fac=file_data(file_name='factor_input.txt',
                      row_header=2, col_header=2, unit_col=1),
        emissions=file_data(file_name='emissions.txt',
                            row_header=2, col_header=3, unit_col=2),
        FDemissions=file_data(file_name='FDemissions.txt',
                              row_header=2, col_header=3, unit_col=2),
        )

    meta_rec = MRIOMetaData(location=PYMRIO_PATH['test_mrio'])

    # read the data into a dicts as pandas.DataFrame
    data = {key: pd.read_table(
                 os.path.join(PYMRIO_PATH['test_mrio'],
                              test_system[key].file_name),
                 index_col=list(range(test_system[key].col_header)),
                 header=list(range(test_system[key].row_header)))
            for key in test_system}

    meta_rec._add_fileio('Load test_mrio from {}'.format(
        PYMRIO_PATH['test_mrio']))

    # distribute the data into dics which can be passed to
    # the IOSystem. To do so, some preps are necessary:
    # - name the header data
    # - save unit in own dataframe and drop unit from the tables

    trade = dict(Z=data['Z'], Y=data['Y'])
    factor_inputs = dict(F=data['fac'])
    emissions = dict(F=data['emissions'], FY=data['FDemissions'])

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

    return IOSystem(Z=data['Z'],
                    Y=data['Y'],
                    unit=trade['unit'],
                    meta=meta_rec,
                    factor_inputs=factor_inputs,
                    emissions=emissions,
                    population=popdata)
