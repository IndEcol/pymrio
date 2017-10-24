"""
Various parser for available MRIOs and files in a similar format


KST 20140903
"""

import os
import logging
import warnings
import pandas as pd
import numpy as np
import zipfile
import collections

from pymrio.core.mriosystem import IOSystem
from pymrio.core.mriosystem import Extension
from pymrio.tools.iometadata import MRIOMetaData

# Constants and global variables
from pymrio.core.constants import PYMRIO_PATH

# There is one chained_assignment somewhere TODO: find and fix
pd.set_option('chained_assignment', None)


# Exceptions
class ParserError(Exception):
    """ Base class for errors concerning parsing of IO source files """
    pass


class ParserWarning(UserWarning):
    """ Base class for warnings concerning parsing of IO source files """
    pass


# Top level functions
def parse_exio_ext(file, index_col, name, drop_compartment=True,
                   version=None, year=None, iosystem=None, sep=','):
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

    F = pd.read_table(
        file,
        header=[0, 1],
        index_col=list(range(index_col)),
        sep=sep)

    F.columns.names = ['region', 'sector']

    if index_col == 1:
        F.index.names = ['stressor']

    elif index_col == 2:
        F.index.names = ['stressor', 'unit']

    elif index_col == 3:
        F.index.names = ['stressor', 'compartment', 'unit']

    else:
        F.reset_index(level=list(range(3, index_col)),
                      drop=True,
                      inplace=True)
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

    return Extension(name=name,
                     F=F,
                     unit=unit,
                     iosystem=iosystem,
                     version=version,
                     year=year,
                     )


def parse_exiobase2(path, charact=None, iosystem=None,
                    version='exiobase 2.2.2', popvector='exio2'):
    """ Parse the exiobase 2.2.2 source files for the IOSystem

    The function parse product by product and industry by industry source file
    in the coefficient form (A and S).

    Filenames are hardcoded in the parser - for any other function the code has
    to be adopted. Check git comments to find older verions.

    Parameters
    ----------
    path : string
        Path to the EXIOBASE source files
    charact : string, optional
        Filename with path to the characterisation matrices for the extensions
        (xls).  This is provided together with the EXIOBASE system and given as
        a xls file. The four sheets  Q_factorinputs, Q_emission, Q_materials
        and Q_resources are read and used to generate one new extensions with
        the impacts
    iosystem : string, optional
        Note for the IOSystem, recommended to be 'pxp' or 'ixi' for
        product by product or industry by industry.
        However, this can be any string and can have more information if needed
        (eg for different technology assumptions)
        The string will be passed to the IOSystem.
    version : string, optional
        This can be used as a version tracking system. Default: exiobase 2.2.2
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
    path = path.rstrip('\\')
    path = os.path.abspath(path)

    # standard file names in exiobase
    files_exio = dict(
        # exiobase 2.2.2
        A='mrIot_version2.2.2.txt',
        Y='mrFinalDemand_version2.2.2.txt',
        S_fac='mrFactorInputs_version2.2.2.txt',
        S_emissions='mrEmissions_version2.2.2.txt',
        S_materials='mrMaterials_version2.2.2.txt',
        S_resources='mrResources_version2.2.2.txt',
        FY_emissions='mrFDEmissions_version2.2.2.txt',
        FY_materials='mrFDMaterials_version2.2.2.txt',
        )

    # check if source exiobase is complete
    _intersect = [val for val in files_exio.values()
                  if val in os.listdir(path)]
    if len(_intersect) != len(files_exio.values()):
        raise ParserError('EXIOBASE files missing')

    # number of row and column headers in EXIOBASE
    head_col = dict()
    head_row = dict()
    head_col['A'] = 3  # number of cols containing row headers at the beginning
    head_row['A'] = 2  # number of rows containing col headers at the top
    head_col['Y'] = 3
    head_row['Y'] = 2
    head_col['S_fac'] = 2
    head_row['S_fac'] = 2
    head_col['S_emissions'] = 3
    head_row['S_emissions'] = 2
    head_col['S_materials'] = 2
    head_row['S_materials'] = 2
    head_col['S_resources'] = 3
    head_row['S_resources'] = 2
    head_col['FY_emissions'] = 3
    head_row['FY_emissions'] = 2
    head_col['FY_materials'] = 2
    head_row['FY_materials'] = 2

    # read the data into pandas
    logging.info('Read exiobase2 from {}'.format(path))
    data = {key: pd.read_table(os.path.join(path, files_exio[key]),
            index_col=list(range(head_col[key])),
            header=list(range(head_row[key])))
            for key in files_exio}

    logging.debug('Refine multiindex')
    data['A'].index.names = ['region', 'sector', 'unit']
    data['A'].columns.names = ['region', 'sector']
    data['unit'] = pd.DataFrame(
        data['A'].iloc[:, 0].
        reset_index(level='unit').unit)
    logging.debug('Refine units')
    data['unit'].unit = data['unit'].unit.str.replace('/.*', '')
    data['A'].reset_index(level='unit', drop=True, inplace=True)
    data['Y'].index.names = ['region', 'sector', 'unit']
    data['Y'].columns.names = ['region', 'category']
    data['Y'].reset_index(level='unit', drop=True, inplace=True)
    ext_unit = dict()
    for key in ['S_fac', 'S_emissions', 'S_materials',
                'S_resources', 'FY_emissions', 'FY_materials']:
        logging.debug('Parse extension {}'.format(key))
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
            ext_unit[key].unit = ext_unit[key].unit.str.replace('/.*', '')

    logging.debug('Build the extensions')
    ext = dict()
    ext['factor_inputs'] = {'S': data['S_fac'],
                            'unit': ext_unit['S_fac'], 'name': 'factor input'}
    ext['emissions'] = {'S': data['S_emissions'], 'FY': data['FY_emissions'],
                        'unit': ext_unit['S_emissions'], 'name': 'emissons'}
    ext['materials'] = {'S': data['S_materials'], 'FY': data['FY_materials'],
                        'unit': ext_unit['S_materials'],
                        'name': 'material extraction'}
    ext['resources'] = {'S': data['S_resources'],
                        'unit': ext_unit['S_resources'], 'name': 'resources'}

    # read the characterisation matrices if available
    # and build one extension with the impacts
    if charact:
        logging.debug('Parse characterisation matrix')
        # dict with correspondence to the extensions
        Qsheets = {'Q_factorinputs': 'factor_inputs',
                   'Q_emission': 'emissions',
                   'Q_materials': 'materials',
                   'Q_resources': 'resources'}

        Q_head_col = dict()
        Q_head_row = dict()
        Q_head_col_rowname = dict()
        Q_head_col_rowunit = dict()
        Q_head_col_metadata = dict()
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

        charac_data = {Qname: pd.read_excel(charact,
                       sheetname=Qname,
                       skiprows=list(range(0, Q_head_row[Qname])),
                       header=None)
                       for Qname in Qsheets}

        _unit = dict()
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

            _unit[Qname] = pd.DataFrame(
                    charac_data[Qname].iloc[:, Q_head_col_rowunit[Qname]])
            _unit[Qname].columns = ['unit']
            _unit[Qname].index.name = 'impact'
            charac_data[Qname] = charac_data[Qname].ix[
                :, Q_head_col_rowunit[Qname]+1:]
            charac_data[Qname].index.name = 'impact'

            if 'FY' in ext[Qsheets[Qname]]:
                _FY = ext[Qsheets[Qname]]['FY'].values
            else:
                _FY = np.zeros([ext[Qsheets[Qname]]['S'].shape[0],
                                data['Y'].shape[1]])

            _impact[Qname] = {'S': charac_data[Qname].dot(
                                ext[Qsheets[Qname]]['S'].values),
                              'FY': charac_data[Qname].dot(_FY),
                              'unit': _unit[Qname]
                              }

        impact['S'] = (_impact['Q_factorinputs']['S']
                       .append(_impact['Q_emission']['S'])
                       .append(_impact['Q_materials']['S'])
                       .append(_impact['Q_resources']['S']))
        impact['FY'] = (_impact['Q_factorinputs']['FY']
                        .append(_impact['Q_emission']['FY'])
                        .append(_impact['Q_materials']['FY'])
                        .append(_impact['Q_resources']['FY']))
        impact['S'].columns = ext['emissions']['S'].columns
        impact['FY'].columns = ext['emissions']['FY'].columns
        impact['unit'] = (_impact['Q_factorinputs']['unit']
                          .append(_impact['Q_emission']['unit'])
                          .append(_impact['Q_materials']['unit'])
                          .append(_impact['Q_resources']['unit']))
        impact['name'] = 'impact'
        ext['impacts'] = impact

    if popvector is 'exio2':
        logging.debug('Read population vector')
        popdata = pd.read_table(os.path.join(PYMRIO_PATH['exio20'],
                                './misc/population.txt'),
                                index_col=0).astype(float)
    else:
        popdata = popvector

    return IOSystem(
            A=data['A'],
            Y=data['Y'],
            unit=data['unit'],
            population=popdata,
            **ext)


def parse_exiobase3(zip_file,
                    path_in_zip='',
                    version='3.0',
                    iosystem=None,
                    year=None,
                    charact=None):
    """ Parse the exiobase 3 source files for the IOSystem

    The function parse product by product and industry by industry source file
    with flow matrices (Z).

    Currently EXIOBASE 3 is delivered in the format year/some_zip_file.zip
    This file must be passed (parameter zip_file). Within the zip_file the
    structure changed during the last versions of the EXIOBASE 3 development.
    Some versions have the data stored in a subfolder with in the zip file,
    in other versions the data is directly in the root of the file. The
    parameter path_in_zip allows to specify the relative folder within the
    zip file.

    TODO: popvector (see exio2 parser), charac

    Parameters
    ----------
    zip_file : string
        Zip file containing EXIO3 (abs or relative path)
    path_in_zip : string, optional
        Relative path to the data within the zipfile. Default: root ('')
    version : string, optional
        The version defines the filename in EXIOBASE.
        For example:
            mrIOT3.0.txt for EXIOBASE3 requires the
            version parameter to be "3.0",
            mrIOT_3_1.txt requires version to be "_3_1"
            version parameter to be "3.0"
    charact : string, optional
        Filename with path to the characterisation matrices for the extensions
        (xls).  This is provided together with the EXIOBASE system and given as
        a xls file. The four sheets  Q_factorinputs, Q_emission, Q_materials
        and Q_resources are read and used to generate one new extensions
        with the impacts
    iosystem : string, optional
        Note for the IOSystem, recommended to be 'pxp' or 'ixi' for
        product by product or industry by industry.
        However, this can be any string and can have more information if needed
        (eg for different technology assumptions)
        The string will be passed to the IOSystem.
    year : string or int
        see pymrio.Extension

    Returns
    -------
    IOSystem
        A IOSystem with the parsed exiobase 3 data

    Raises
    ------
    ParserError
        If the exiobase source files are not
        complete in the given path or EXIOBASE files missing TODO

    """

    zip_file = os.path.abspath(zip_file)

    file_data = collections.namedtuple(
        'file_data', [
            'file_name',
            # nr of rows containing index on the top of the table (for columns)
            'index_rows',
            # nr of cols containing index on the left of the table (for rows)
            'index_col',
            # column containing the unit for the table (couting starts at zero)
            'unit_col',
            ])
    ver_ext = version + '.txt'

    core_files = dict(
        # for the core files the unit_col is still
        # hard coded below - fix if needed
        Z=file_data(file_name='mrIot' + ver_ext,
                    index_rows=2, index_col=3, unit_col=2),
        Y=file_data(file_name='mrFinalDemand' + ver_ext,
                    index_rows=2, index_col=3, unit_col=2),
                )
    extension_files = dict(
        factor_inputs=dict(
            F=file_data(file_name='mrFactorInputs' + ver_ext,
                        index_rows=2, index_col=2, unit_col=1),
            ),
        emissions=dict(
            F=file_data(file_name='mrEmissions' + ver_ext,
                        index_rows=2, index_col=3, unit_col=2),
            FY=file_data(file_name='mrFDEmissions' + ver_ext,
                         index_rows=2, index_col=3, unit_col=2),
            ),
        materials=dict(
            F=file_data(file_name='mrMaterials' + ver_ext,
                        index_rows=2, index_col=2, unit_col=1),
            FY=file_data(file_name='mrFDMaterials' + ver_ext,
                         index_rows=2, index_col=2, unit_col=1),
            ),
        resources=dict(
            F=file_data(file_name='mrResources' + ver_ext,
                        index_rows=2, index_col=3, unit_col=2),
            FY=file_data(file_name='mrFDResources' + ver_ext,
                         index_rows=2, index_col=3, unit_col=2),
            ),
        )

    # read the data into a dicts as pandas.DataFrame
    logging.info('Read exiobase3 from {}'.format(zip_file))
    zip_file = zipfile.ZipFile(zip_file)

    core_data = {exio_table: pd.read_table(
                    zip_file.open(
                        path_in_zip + core_files[exio_table].file_name),
                    index_col=list(range(core_files[exio_table].index_col)),
                    header=list(range(core_files[exio_table].index_rows)))
                 for exio_table in core_files}
    # zip_file.close()

    extension = dict()
    for ext_type in extension_files:
        extension[ext_type] = {
            exio_table: pd.read_table(
                zip_file.open(
                    path_in_zip +
                    extension_files[ext_type][exio_table].file_name),
                index_col=list(
                    range(extension_files[ext_type][exio_table].index_col)),
                header=list(
                    range(extension_files[ext_type][exio_table].index_rows)))
            for exio_table in extension_files[ext_type]
            }
        extension[ext_type]['name'] = ext_type
    zip_file.close()

    # adjust index
    for table in core_data:
        core_data[table].index.names = ['region', 'sector', 'unit']
        if table == 'A' or table == 'Z':
            core_data[table].columns.names = ['region', 'sector']
            _unit = pd.DataFrame(
                    core_data[table].iloc[:, 0]).reset_index(
                        level='unit').unit
            _unit = pd.DataFrame(_unit)
            _unit.columns = ['unit']
        if table == 'Y':
            core_data[table].columns.names = ['region', 'category']
        core_data[table].reset_index(level='unit', drop=True, inplace=True)
    core_data['unit'] = _unit

    for ext_type in extension:
        _unit = None
        for table in extension[ext_type]:
            if type(extension[ext_type][table]) is not pd.core.frame.DataFrame:
                continue
            if extension_files[ext_type][table].index_col == 3:
                extension[ext_type][table].index.names = [
                        'stressor', 'compartment', 'unit']
            elif extension_files[ext_type][table].index_col == 2:
                extension[ext_type][table].index.names = [
                        'stressor', 'unit']
            else:
                raise ParserError('Unknown EXIOBASE file structure')
            if table == 'S' or table == 'F':
                extension[ext_type][table].columns.names = ['region', 'sector']
                try:
                    _unit = pd.DataFrame(
                            extension[ext_type][table].iloc[:, 0]
                            ).reset_index(level='unit').unit
                except IndexError:
                    _unit = pd.DataFrame(
                        extension[ext_type][table].iloc[:, 0])
                    _unit.columns = ['unit']
                    _unit['unit'] = 'undef'
                    _unit.reset_index(level='unit', drop=True, inplace=True)
                _unit = pd.DataFrame(_unit)
                _unit.columns = ['unit']

            if table == 'FY':
                extension[ext_type][table].columns.names = [
                        'region', 'category']

            extension[ext_type][table].reset_index(level='unit',
                                                   drop=True,
                                                   inplace=True)
        extension[ext_type]['unit'] = _unit

    # read the characterisation matrices if available
    # and build one extension with the impacts
    if charact:
        # dict with correspondence to the extensions
        Qsheets = {'Q_factorinputs': 'factor_inputs',
                   'Q_emission': 'emissions',
                   'Q_materials': 'materials',
                   'Q_resources': 'resources'}
        Q_head_col = dict()
        Q_head_row = dict()
        Q_head_col_rowname = dict()
        Q_head_col_rowunit = dict()
        Q_head_col_metadata = dict()
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

        charac_data = {Qname: pd.read_excel(charact,
                       sheetname=Qname,
                       skiprows=list(range(0, Q_head_row[Qname])),
                       header=None)
                       for Qname in Qsheets}

        _unit = dict()
        # temp for the calculated impacts which than
        # get summarized in the 'impact'
        _impact = dict()
        impact = dict()
        for Qname in Qsheets:
            charac_data[Qname].index = (
                    charac_data[Qname][Q_head_col_rowname[Qname]])

            _unit[Qname] = pd.DataFrame(
                    charac_data[Qname].iloc[:, Q_head_col_rowunit[Qname]])
            _unit[Qname].columns = ['unit']
            _unit[Qname].index.name = 'impact'
            charac_data[Qname] = charac_data[Qname].ix[
                    :, Q_head_col_rowunit[Qname]+1:]
            charac_data[Qname].index.name = 'impact'

            if 'FY' in extension[Qsheets[Qname]]:
                _FY = extension[Qsheets[Qname]]['FY'].values
            else:
                _FY = np.zeros([extension[Qsheets[Qname]]['F'].shape[0],
                                core_data['Y'].shape[1]])
            _impact[Qname] = {'F': charac_data[Qname].dot(
                                extension[Qsheets[Qname]]['F'].values),
                              'FY': charac_data[Qname].dot(_FY),
                              'unit': _unit[Qname]
                              }

        impact['F'] = (_impact['Q_factorinputs']['F']
                       .append(_impact['Q_emission']['F'])
                       .append(_impact['Q_materials']['F'])
                       .append(_impact['Q_resources']['F']))
        impact['FY'] = (_impact['Q_factorinputs']['FY']
                        .append(_impact['Q_emission']['FY'])
                        .append(_impact['Q_materials']['FY'])
                        .append(_impact['Q_resources']['FY']))
        impact['F'].columns = extension['emissions']['F'].columns
        impact['FY'].columns = extension['emissions']['FY'].columns
        impact['unit'] = (_impact['Q_factorinputs']['unit']
                          .append(_impact['Q_emission']['unit'])
                          .append(_impact['Q_materials']['unit'])
                          .append(_impact['Q_resources']['unit']))
        impact['name'] = 'impact'
        extension['impacts'] = impact

    return IOSystem(version=version,
                    price='current',
                    year=year,
                    **dict(core_data, **extension))


def parse_wiod(path, year=None, names=('isic', 'c_codes'), 
               popvector=None):
    """ Parse the wiod source files for the IOSystem

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
    path : string
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

    Yields
    -------
    IOSystem

    Raises
    ------
    ParserError
        If the WIOD source file are not complete or inconsistent

    """

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
        # 2. case: directory given-build wiot_file with the value given in year
        if not year:
            raise ParserError('No year specified '
                              '(either specify a specific file '
                              'or a path and year)')
        year_two_digit = str(year)[-2:].encode('unicode-escape')
        wiot_file_list = [fl for fl in os.listdir(path)
                          if (fl[:6] == wiot_start + year_two_digit and
                          os.path.splitext(fl)[1] == wiot_ext)]
        if len(wiot_file_list) != 1:
            raise ParserError('Multiple files for a given year or file not '
                              'found (specify a specific file in paramters)')

        wiot_file = os.path.join(path, wiot_file_list[0])

    wiot_file = wiot_file.decode()
    root_path = os.path.split(wiot_file)[0]
    if not os.path.exists(wiot_file):
        raise ParserError('WIOD file not found in the specified folder.')
    
    meta_rec = MRIOMetaData(storage_folder=root_path)

    # wiot file structure
    wiot_meta = {
            'col': 0,   # column of the meta information
            'year': 0,  # rest: rows with the data
            'iosystem': 2,
            'unit': 3,
            'end_row': 4,
            }
    wiot_header = {
            # the header indexes are the same for rows after removing the first
            # two lines (wiot_empty_top_rows)
            'code': 0,
            'sector_names': 1,
            'region': 2,
            'c_code': 3,
            }
    wiot_empty_top_rows = [0, 1]

    wiot_marks = {   # special marks
        'last_interindsec': 'c35',     # last sector of the interindustry
        'tot_facinp': ['r60', 'r69'],  # useless totals to remove from factinp
        'total_column': [-1],          # the total column in the whole data
        }

    wiot_sheet = 0   # assume the first one is the one with the data.

    # Wiod has an unfortunate file structure with overlapping metadata and
    # header. In order to deal with that first the full file is read.
    wiot_data = pd.read_excel(wiot_file,
                              sheetname=wiot_sheet,
                              header=None)

    meta_rec._add_fileio('WIOD data load from {}'.format(wiot_file))
    # get meta data
    wiot_year = wiot_data.iloc[wiot_meta['year'], wiot_meta['col']][-4:]
    wiot_iosystem = wiot_data.iloc[
            wiot_meta['iosystem'], wiot_meta['col']].rstrip(')').lstrip('(')
    meta_rec.change_meta('system', wiot_iosystem)
    _wiot_unit = wiot_data.iloc[
            wiot_meta['unit'], wiot_meta['col']].rstrip(')').lstrip('(')
    
    # remove meta data, empty rows, total column
    wiot_data.iloc[0:wiot_meta['end_row'], wiot_meta['col']] = np.NaN
    wiot_data.drop(wiot_empty_top_rows,
                   axis=0, inplace=True)
    wiot_data.drop(wiot_data.columns[wiot_marks['total_column']],
                   axis=1, inplace=True)
    # at this stage row and column header should have the same size but
    # the index starts now at two - replace/reset to row numbers
    wiot_data.index = range(wiot_data.shape[0])

    # Early years in WIOD tables have a different name for Romania:
    # 'ROM' which should be 'ROU'. The latter is also consistent with
    # the environmental extensions names.
    wiot_data.iloc[wiot_header['region'], :] = wiot_data.iloc[
        wiot_header['region'], :].str.replace('ROM', 'ROU')
    wiot_data.iloc[:, wiot_header['region']] = wiot_data.iloc[
        :, wiot_header['region']].str.replace('ROM', 'ROU')

    # get the end of the interindustry matrix
    _lastZcol = wiot_data[
        wiot_data.iloc[
            :, wiot_header['c_code']] == wiot_marks['last_interindsec']
        ].index[-1]
    _lastZrow = wiot_data[
        wiot_data[wiot_header['c_code']] == wiot_marks['last_interindsec']
        ].index[-1]

    if _lastZcol != _lastZrow:
        raise ParserError(
            'Interindustry matrix no symetric in the WIOD source file')
    else:
        Zshape = (_lastZrow, _lastZcol)

    # separate factor input extension and remove
    # totals in the first and last row
    facinp = wiot_data.iloc[Zshape[0]+1:, :]
    facinp.drop(
        facinp[facinp[wiot_header['c_code']].isin(
            wiot_marks['tot_facinp'])].index,
        inplace=True,
        axis=0
        )

    Z = wiot_data.iloc[:Zshape[0]+1, :Zshape[1]+1].copy()
    Y = wiot_data.iloc[:Zshape[0]+1, Zshape[1]+1:].copy()
    F_fac = facinp.iloc[:, :Zshape[1]+1].copy()
    FY_fac = facinp.iloc[:, Zshape[1]+1:].copy()

    index_wiot_headers = [nr for nr in wiot_header.values()]
    # Save lookup of sectors and codes - to be used at the end of the parser
    # Assuming USA is present in every WIOT year
    wiot_sector_lookup = wiot_data[
        wiot_data[wiot_header['region']] == 'USA'].iloc[
            :, 0:max(index_wiot_headers)+1].applymap(str)
    wiot_sector_lookup.columns = [
        entry[1] for entry in sorted(
            zip(wiot_header.values(), wiot_header.keys()))]
    wiot_sector_lookup.set_index('code', inplace=True, drop=False)
    _Y = Y.T.iloc[:, [
        wiot_header['code'],  # Included to be consistent with  wiot_header
        wiot_header['sector_names'],
        wiot_header['region'],
        wiot_header['c_code'],
        ]]
    wiot_fd_lookup = _Y[_Y.iloc[
        :, wiot_header['region']] == 'USA'].applymap(str)
    wiot_fd_lookup.columns = [
        entry[1] for entry in
        sorted(zip(wiot_header.values(), wiot_header.keys()))]
    wiot_fd_lookup.set_index('c_code', inplace=True, drop=False)
    wiot_fd_lookup.index.name = 'code'

    # set the index/columns, work with code b/c these are also used in the
    # extensions
    Z[wiot_header['code']] = Z[wiot_header['code']].astype(str)
    Z.set_index([wiot_header['region'],
                wiot_header['code']], inplace=True, drop=False)
    Z = Z.iloc[max(index_wiot_headers)+1:, max(index_wiot_headers)+1:]
    Z.index.names = ['region', 'sector']
    Z.columns = Z.index

    indexY_col_head = Y.iloc[[wiot_header['region'],
                              wiot_header['c_code']], :]
    Y.columns = pd.MultiIndex.from_arrays(indexY_col_head.values,
                                          names=Z.index.names)
    Y = Y.iloc[max(index_wiot_headers)+1:, :]
    Y.index = Z.index

    F_fac.set_index([wiot_header['sector_names']],
                    inplace=True, drop=False)  # c_code missing, use names
    F_fac.index.names = ['inputtype']
    F_fac = F_fac.iloc[:, max(index_wiot_headers)+1:]
    F_fac.columns = Z.columns
    FY_fac.columns = Y.columns
    FY_fac.index = F_fac.index

    # convert from object to float (was object because mixed float,str)
    Z = Z.astype('float')
    Y = Y.astype('float')
    F_fac = F_fac.astype('float')
    FY_fac = FY_fac.astype('float')

    # save the units
    Z_unit = pd.DataFrame(Z.iloc[:, 0])
    Z_unit.columns = ['unit']
    Z_unit['unit'] = _wiot_unit

    F_fac_unit = pd.DataFrame(F_fac.iloc[:, 0])
    F_fac_unit.columns = ['unit']
    F_fac_unit['unit'] = _wiot_unit

    ll_countries = list(Z.index.get_level_values('region').unique())

    # Finalize the factor inputs extension
    ext = dict()

    ext['factor_inputs'] = {'F': F_fac,
                            'FY': FY_fac,
                            'year': wiot_year,
                            'iosystem': wiot_iosystem,
                            'unit': F_fac_unit,
                            'name': 'factor input',
                            }

    # SEA extension
    _F_sea_data, _F_sea_unit = __get_WIOD_SEA_extension(
                            root_path=root_path, year=year)
    if _F_sea_data is not None:
        # None if no SEA file present
        _FY_sea = pd.DataFrame(index=_F_sea_data.index,
                               columns=FY_fac.columns, data=0)
        _FY_sea = _FY_sea.astype('float')

        ext['SEA'] = {'F': _F_sea_data,
                      'FY': _FY_sea,
                      'year': wiot_year,
                      'iosystem': wiot_iosystem,
                      'unit': _F_sea_unit,
                      'name': 'SEA',
                      }
        meta_rec._add_fileio('SEA file extension parsed from {}'.format(root_path))

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
            'AIR': {'name': 'Air Emission Accounts',
                    'start': 'AIR_',
                    'ext': '.xls',
                    'unit': {
                            'CO2': 'Gg',
                            'CH4': 't',
                            'N2O': 't',
                            'NOx': 't',
                            'SOx': 't',
                            'CO': 't',
                            'NMVOC': 't',
                            'NH3': 't',
                            },
                    },
            'CO2': {'name': 'CO2 emissions - per source',
                    'start': 'CO2_',
                    'ext': '.xls',
                    'unit': {
                        'all': 'Gg'}
                    },

            'EM': {'name': 'Emission relevant energy use',
                   'start': 'EM_',
                   'ext': '.xls',
                   'unit': {
                        'all': 'TJ'}
                   },
            'EU': {'name': 'Gross energy use',
                   'start': 'EU_',
                   'ext': '.xls',
                   'unit': {
                        'all': 'TJ'}
                   },
            'lan': {'name': 'land use',
                    'start': 'lan_',
                    'ext': '.xls',
                    'unit': {
                        'all': None}
                    },
            'mat': {'name': 'material use',
                    'start': 'mat_',
                    'ext': '.xls',
                    'unit': {
                        'all': None}
                    },
            'wat': {'name': 'water use',
                    'start': 'wat_',
                    'ext': '.xls',
                    'unit': {
                        'all': None}
                    },
            }

    _FY_template = pd.DataFrame(columns=FY_fac.columns)
    _ss_FY_pressure_column = 'c37'
    for ik_ext in dl_envext_para:
        _dl_ex = __get_WIOD_env_extension(root_path=root_path,
                                          year=year,
                                          ll_co=ll_countries,
                                          para=dl_envext_para[ik_ext])
        if _dl_ex is not None:
            # None if extension not available
            _FY = _dl_ex['FY']

            _FY.columns = pd.MultiIndex.from_product([
                                _FY.columns, [_ss_FY_pressure_column]])
            _FY = _FY_template.append(_FY)
            _FY.fillna(0, inplace=True)
            _FY.index.names = _dl_ex['F'].index.names
            _FY.columns.names = _FY_template.columns.names
            _FY = _FY[ll_countries]
            _FY = _FY.astype('float')

            ext[ik_ext] = {
                    'F': _dl_ex['F'],
                    'FY': _FY,
                    'year': wiot_year,
                    'iosystem': wiot_iosystem,
                    'unit': _dl_ex['unit'],
                    'name': dl_envext_para[ik_ext]['name'],
                    }
            meta_rec._add_fileio('Extension {} parsed from {}'.format(ik_ext, root_path))

    # Build system
    wiod = IOSystem(Z=Z, Y=Y,
                    iosystem=wiot_iosystem,
                    unit=Z_unit,
                    meta=meta_rec,
                    **ext)

    # Replace sector/final demand category names
    if type(names) is str:
        names = (names, names)
    ll_names = [w[0].lower() for w in names]

    if ll_names[0] == 'c':
        dd_sec_rename = wiot_sector_lookup.c_code.to_dict()
    elif ll_names[0] == 'i':
        dd_sec_rename = wiot_sector_lookup.code.to_dict()
    elif ll_names[0] == 'f':
        dd_sec_rename = wiot_sector_lookup.sector_names.to_dict()
    else:
        dd_sec_rename = wiot_sector_lookup.code.to_dict()
        warnings.warn('Parameter for names not understood - '
                      'used ISIC codes as sector names')

    if ll_names[1] == 'c':
        dd_fd_rename = wiot_fd_lookup.c_code.to_dict()
    elif ll_names[1] == 'i':
        dd_fd_rename = wiot_fd_lookup.c_code.to_dict()
    elif ll_names[1] == 'f':
        dd_fd_rename = wiot_fd_lookup.sector_names.to_dict()
    else:
        warnings.warn('Parameter for names not understood - '
                      'used c_codes as final demand category names')

    wiod.Z.rename(columns=dd_sec_rename, index=dd_sec_rename, inplace=True)
    wiod.Y.rename(columns=dd_fd_rename, index=dd_sec_rename, inplace=True)
    for ext in wiod.get_extensions(data=True):
        ext.F.rename(columns=dd_sec_rename, inplace=True)
        ext.FY.rename(columns=dd_fd_rename, inplace=True)

    return wiod


def __get_WIOD_env_extension(root_path, year, ll_co, para):
    """ Parses the wiod environmental extension

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
        FY : pd.Dataframe with index 'stressor' and column 'region'
            This data is for household stressors - must be applied to the right
            final demand column afterwards.
        unit : pd.DataFrame with index 'stressor' and column 'unit'


    """

    ll_root_content = [ff for ff in os.listdir(root_path) if
                       ff.startswith(para['start'])]
    if len(ll_root_content) < 1:
        warnings.warn(
            'Extension data for {} not found - '
            'Extension not included'.format(para['start']), ParserWarning)
        return None

    elif len(ll_root_content) > 1:
        raise ParserError(
            'Several raw data for extension'
            '{} available - clean extension folder.'.format(para['start']))

    pf_env = os.path.join(root_path, ll_root_content[0])

    if pf_env.endswith('.zip'):
        rf_zip = zipfile.ZipFile(pf_env)
        ll_env_content = [ff for ff in rf_zip.namelist() if
                          ff.endswith(para['ext'])]
    else:
        ll_env_content = [ff for ff in os.listdir(pf_env) if
                          ff.endswith(para['ext'])]

    dl_env = dict()
    dl_env_hh = dict()
    for co in ll_co:
        ll_pff_read = [ff for ff in ll_env_content if
                       ff.endswith(para['ext']) and
                       (ff.startswith(co.upper()) or
                        ff.startswith(co.lower()))]

        if len(ll_pff_read) < 1:
            raise ParserError('Country data not complete for Extension '
                              '{} - missing {}.'.format(para['start'], co))

        elif len(ll_pff_read) > 1:
            raise ParserError('Multiple country data for Extension '
                              '{} - country {}.'.format(para['start'], co))

        pff_read = ll_pff_read[0]

        if pf_env.endswith('.zip'):
            ff_excel = pd.ExcelFile(rf_zip.open(pff_read))
        else:
            ff_excel = pd.ExcelFile(os.path.join(pf_env, pff_read))
        if str(year) in ff_excel.sheet_names:
            df_env = ff_excel.parse(sheetname=str(year),
                                    index_col=None,
                                    header=0
                                    )
        else:
            warnings.warn('Extension {} does not include'
                          'data for the year {} - '
                          'Extension not included'.format(para['start'], year),
                          ParserWarning)
            return None

        if not df_env.index.is_numeric():
            # upper case letter extensions gets parsed with multiindex, not
            # quite sure why...
            df_env.reset_index(inplace=True)

        # unit can be taken from the first cell in the excel sheet
        if df_env.columns[0] != 'level_0':
            para['unit']['all'] = df_env.columns[0]

        # two clean up cases - can be identified by lower/upper case extension
        # description
        if para['start'].islower():
            pass
        elif para['start'].isupper():
            df_env = df_env.iloc[:, 1:]
        else:
            raise ParserError('Format of extension not given.')

        df_env.dropna(axis=0, how='all', inplace=True)
        df_env = df_env[df_env.iloc[:, 0] != 'total']
        df_env = df_env[df_env.iloc[:, 0] != 'secTOT']
        df_env = df_env[df_env.iloc[:, 0] != 'secQ']
        df_env.iloc[:, 0].astype(str, inplace=True)
        df_env.iloc[:, 0].replace(to_replace='sec',
                                  value='',
                                  regex=True,
                                  inplace=True)

        df_env.set_index([df_env.columns[0]], inplace=True)
        df_env.index.names = ['sector']
        df_env = df_env.T

        ikc_hh = 'FC_HH'
        dl_env_hh[co] = df_env[ikc_hh]
        del df_env[ikc_hh]
        dl_env[co] = df_env

    df_F = pd.concat(dl_env, axis=1)[ll_co]
    df_FY = pd.concat(dl_env_hh, axis=1)[ll_co]
    df_F.fillna(0, inplace=True)
    df_FY.fillna(0, inplace=True)

    df_F.columns.names = ['region', 'sector']
    df_F.index.names = ['stressor']

    df_FY.columns.names = ['region']
    df_FY.index.names = ['stressor']

    # build the unit df
    df_unit = pd.DataFrame(index=df_F.index, columns=['unit'])
    _ss_unit = para['unit'].get('all', 'undef')
    for ikr in df_unit.index:
        df_unit.ix[ikr, 'unit'] = para['unit'].get(ikr, _ss_unit)

    df_unit.columns.names = ['unit']
    df_unit.index.names = ['stressor']

    if pf_env.endswith('.zip'):
        rf_zip.close()

    return {'F': df_F,
            'FY': df_FY,
            'unit': df_unit
            }


def __get_WIOD_SEA_extension(root_path, year, data_sheet='DATA'):
    """ Utility function to get the extension data from the SEA file in WIOD

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
    sea_ext = '.xlsx'
    sea_start = 'WIOD_SEA'

    _SEA_folder = os.path.join(root_path, 'SEA')
    if not os.path.exists(_SEA_folder):
        _SEA_folder = root_path

    sea_folder_content = [ff for ff in os.listdir(_SEA_folder)
                          if os.path.splitext(ff)[-1] == sea_ext and
                          ff[:8] == sea_start]

    if sea_folder_content:
        # read data
        sea_file = os.path.join(_SEA_folder, sorted(sea_folder_content)[0])

        df_sea = pd.read_excel(sea_file,
                               sheetname=data_sheet,
                               header=0,
                               index_col=[0, 1, 2, 3])

        # fix years
        ic_sea = df_sea.columns.tolist()
        ic_sea = [yystr.lstrip('_') for yystr in ic_sea]
        df_sea.columns = ic_sea

        try:
            ds_sea = df_sea[str(year)]
        except KeyError:
            warnings.warn(
                'SEA extension does not include data for the '
                'year {} - SEA-Extension not included'.format(year),
                ParserWarning)
            return None, None

        # get useful data (employment)
        mt_sea = ['EMP', 'EMPE', 'H_EMP', 'H_EMPE']
        ds_use_sea = pd.concat(
                [ds_sea.xs(key=vari, level='Variable', drop_level=False)
                 for vari in mt_sea])
        ds_use_sea.drop(labels='TOT', level='Code', inplace=True)
        ds_use_sea.reset_index('Description', drop=True, inplace=True)

        # RoW not included in SEA but needed to get it consistent for
        # all countries. Just add a dummy with 0 for all accounts.
        if 'RoW' not in ds_use_sea.index.get_level_values('Country'):
            ds_RoW = ds_use_sea.xs('USA',
                                   level='Country', drop_level=False)
            ds_RoW.ix[:] = 0
            df_RoW = ds_RoW.reset_index()
            df_RoW['Country'] = 'RoW'
            ds_use_sea = pd.concat(
                        [ds_use_sea.reset_index(), df_RoW]).set_index(
                                        ['Country', 'Code', 'Variable'])

        ds_use_sea.fillna(value=0, inplace=True)
        df_use_sea = ds_use_sea.unstack(level=['Country', 'Code'])[str(year)]
        df_use_sea.index.names = ['inputtype']
        df_use_sea.columns.names = ['region', 'sector']
        df_use_sea = df_use_sea.astype('float')

        df_unit = pd.DataFrame(
                    data=[    # this data must be in the same order as mt_sea
                        'thousand persons',
                        'thousand persons',
                        'mill hours',
                        'mill hours',
                        ],
                    columns=['unit'],
                    index=df_use_sea.index)

        return df_use_sea, df_unit
    else:
        warnings.warn(
            'SEA extension raw data file not found - '
            'SEA-Extension not included', ParserWarning)
        return None, None
