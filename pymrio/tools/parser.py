"""
Various parser for available MRIOs and files in a similar format


KST 20140903
"""

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


