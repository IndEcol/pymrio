"""
Diverse methods and functions to manipulate IOSystems, such as production of some sectors, their embodied impacts, inputs or EROI. 
Mostly developed for Exiobase 1 and 2, may not be compatible with other databases.
by adrien fabre (aka. bixiou on github), feel free to ask: adrien.fabre@psemail.eu
"""

from pymrio.core.mriosystem import IOSystem as IOS
from pymrio.tools.iomath import div0
from pymrio.tools.iomath import sorted_series
from pymrio.tools.iomath import approx_solution
from pymrio.tools.iomath import mult_cols
from pymrio.tools.iomath import mult_rows
from pymrio.tools.iomath import gras
from pymrio.tools.ioparser import themis_parser
import pandas as pd
import numpy as np
import scipy.sparse as sp 
from scipy.sparse import linalg as spla

# TODO: manage Themis, Cecilia, and futures

def energy_sectors(self, notion): # TODO: other sectors, difference from elecs_names to add after elec and to display
    '''
    Returns the list of energy sectors (or names) corresponding to notion, which can be: secondary, secondary_fuels, elec_hydrocarbon, electricities, elecs_names
    '''
    if notion is None: sectors = self.sectors
    elif notion not in ['secondary', 'secondary_fuels', 'elec_hydrocarbon', 'electricities', 'elecs_names']: print('Error: notion not implemented')
    elif notion=='elec_hydrocarbon': sectors = ['Electricity by coal', 'Electricity by gas']
    elif notion=='secondary_fuels': sectors = ['Motor Gasoline', 'Gas/Diesel Oil', 'Heavy Fuel Oil', 'Liquefied Petroleum Gases (LPG)', \
         'Naphtha', 'Non-specified Petroleum Products', 'Kerosene', 'Kerosene Type Jet Fuel', 'Petroleum Coke', 'Aviation Gasoline', 'Gasoline Type Jet Fuel']
    elif notion=='electricities': sectors = ['Electricity by ' + s for s in self.energy_sectors('elecs_names')]

    if self.name.lower()=='cecilia' or (self.name.lower()=='exiobase' and self.meta.version=='1'): 
        if notion=='secondary_fuels': sectors = ['Motor spirit (gasoline)', 'Gas oils', 'Fuel oils n.e.c.', 'Kerosene, including kerosene type jet fuel', \
                                                'Petroleum gases and other gaseous hydrocarbons, except natural gas']
        elif notion=='secondary': sectors = ['Electricity by hydro', 'Electricity nec, including biomass and waste', 'Steam and hot water supply services',
 'Electricity by nuclear', 'Electricity by coal', 'Electricity by gas', 'Motor spirit (gasoline)', 'Gas oils', 'Fuel oils n.e.c.', 'Electricity by wind', 
 'Kerosene, including kerosene type jet fuel', 'Petroleum gases and other gaseous hydrocarbons, except natural gas']
#  ['Coal and lignite; peat (10)', 'Natural gas and services related to natural gas extraction, excluding surveying', 'Nuclear fuel', 'Motor spirit (gasoline)',
#         'Gas oils', 'Fuel oils n.e.c.', 'Kerosene, including kerosene type jet fuel', 'Petroleum gases and other gaseous hydrocarbons, except natural gas']
        elif notion=='elecs_names': 
            sectors = ['wind', 'hydro', 'coal', 'gas', 'nuclear']

    elif self.name.lower()=='exiobase' and self.meta.version[0]=='2':
        if notion=='elec_hydrocarbon': sectors = sectors + ['Electricity by petroleum and other oil derivatives']
        elif notion=='secondary_fuels': sectors = ['Aviation Gasoline', 'Gas/Diesel Oil', 'Gasoline Type Jet Fuel', 'Heavy Fuel Oil', 'Kerosene', \
     'Kerosene Type Jet Fuel', 'Liquefied Petroleum Gases (LPG)', 'Motor Gasoline', 'Naphtha', 'Non-specified Petroleum Products', 'Petroleum Coke'] #TODO:check
        elif notion=='secondary': sectors =['Steam and hot water supply services', 'Electricity by petroleum and other oil derivatives',
 'Electricity by hydro', 'Electricity by wind', 'Electricity by biomass and waste', 'Electricity by tide, wave, ocean',
 'Electricity by Geothermal', 'Electricity by solar photovoltaic', 'Electricity by solar thermal', 'Electricity by coal', 'Electricity by gas',
 'Electricity by nuclear', 'Electricity nec', 'Motor Gasoline', 'Gas/Diesel Oil', 'Heavy Fuel Oil', 'Kerosene Type Jet Fuel',
 'Liquefied Petroleum Gases (LPG)', 'Naphtha', 'Non-specified Petroleum Products', 'Kerosene', 'Petroleum Coke', 'Aviation Gasoline', 'Gasoline Type Jet Fuel']
#             ['Other Bituminous Coal', 'Coking Coal', 'Lignite/Brown Coal', 'Sub-Bituminous Coal', 'Anthracite', \
#  'Natural gas and services related to natural gas extraction, excluding surveying', 'Nuclear fuel', 'Biogas', 'Biodiesels', 'Charcoal', 'Ethane', \
#  'Gas Coke', 'Gas Works Gas', 'Other Hydrocarbons', 'Other Liquid Biofuels', 'Motor Gasoline', 'Gas/Diesel Oil', 'Heavy Fuel Oil', 'Kerosene Type Jet Fuel', \
#  'Liquefied Petroleum Gases (LPG)', 'Naphtha', 'Non-specified Petroleum Products', 'Kerosene', 'Petroleum Coke', 'Aviation Gasoline', 'Gasoline Type Jet Fuel']
        elif notion=='elecs_names': sectors = ['wind', 'solar photovoltaic', 'coal', 'petroleum and other oil derivatives', 'gas', 'nuclear', 'hydro']

    elif self.name.lower()=='themis':
        if notion=='elec_hydrocarbon': sectors = sectors + ['Electricity by oil']
        elif notion=='secondary': sectors = ['Steam and hot water supply services', 'Electricity by hydro', 'Electricity by wind onshore',\
                 'Electricity by wind offshore', 'Electricity by biomass&Waste', 'Electricity by ocean', 'Electricity by geothermal', \
                 'Electricity by solar PV', 'Electricity by solar CSP', 'Electricity by coal', 'Electricity by gas', 'Electricity by oil', \
                 'Electricity by nuclear', 'Motor Gasoline', 'Gas/Diesel Oil', 'Heavy Fuel Oil', 'Kerosene Type Jet Fuel', 'Liquefied Petroleum Gases (LPG)', \
                'Naphtha', 'Non-specified Petroleum Products', 'Kerosene', 'Petroleum Coke', 'Aviation Gasoline', 'Gasoline Type Jet Fuel']
        elif notion=='elecs_names': sectors = ['wind onshore', 'wind offshore', 'solar PV', 'coal', 'oil', 'gas', 'nuclear', 'hydro', 'coal w CCS', \
                                               'gas w CCS', 'biomass&Waste', 'biomass w CCS', 'ocean', 'geothermal', 'solar CSP']
    else: print('Function not yet implemented for this IOSystem')
    return(sectors)

@property
def regions(self): 
    '''
    Returns the list of all regions in the IOSystem
    '''
    if self.name == 'THEMIS' or self.name == 'Cecilia': return(self.labels.regions)
    else: return(list(self.get_regions())) # TODO: treat THEMIS

@property
def sectors(self): 
    '''
    Returns the list of all sectors in the IOSystem
    '''
    if self.name == 'THEMIS' or self.name == 'Cecilia': return(self.labels.sectors)
    else: return(list(self.get_sectors()))

def prepare_secs_regs(self, secs, regs):
    '''
    Prepare the values by default of secs and regs for many methods: all sectors and all regions of the IOSystem.
    '''
    if secs is None: secs = self.sectors
    elif type(secs)==str: secs=[secs]
    if regs is None: regs = self.regions # regions bugs with impacts ... [reg, secs]
    elif type(regs)==str: regs=[regs]
    return((secs, regs))

def index_secs(self, secs, vec_sectors=None):
    '''
    Returns an array of the indexes of secs in vec_sectors.
    
    If secs is a string, returns the indexes of secs in vec_sectors; if secs is a list or array, returns the indexes of any of its elements.
    By default, vec_sectors is the sectors of the IOSystem.
    '''
    if vec_sectors is None: vec_sectors = self.sectors
    if type(secs)==str: return(np.array([i for i,x in enumerate(vec_sectors) if x == secs]))
    else: return(np.array([i for i,x in enumerate(vec_sectors) if x in secs]))
    
def index_regs(self, regs, vec_regions=None):
    '''
    Returns an array of the indexes of secs in vec_regions.
    
    If regs is a string, returns the indexes of regs in vec_regions; if regs is a list or array, returns the indexes of any of its elements.
    By default, vec_regions is the regions of the IOSystem.
    '''
    if vec_regions is None: vec_regions = self.regions
    if type(regs)==str: return(np.array([i for i,x in enumerate(vec_regions) if x == regs]))
    else: return(np.array([i for i,x in enumerate(vec_regions) if x in regs]))
    
# def index_regs_secs(self, regs = None, secs = None, regions = None): # twice faster than index_secs_regs
#     '''
#     Returns an array of the indexes of any element (reg, sec) of regs x secs in the double index of the IOSystem.
#     '''
#     if regs is None: regs = self.regions
#     if secs is None: secs = self.sectors
#     if regions is None: regions = self.regions
#     return(np.repeat(self.index_regs(regs, regions)*self.nb_sectors(), len(secs)*(type(secs)!=str)+(type(secs)==str)) \
#            + np.tile(self.index_secs(secs), len(regs)*(type(regs)!=str)+(type(regs)==str)) )

@property
def nb_regions(self): return(len(self.regions))

@property
def nb_sectors(self): return(len(self.sectors))

def find(self, string, vec='impacts'): # TODO: themis
    '''
    Find vec=impacts/sectors containing string.
    '''
    if vec=='impacts' or vec=='Impacts' or vec=='impact': array = np.array(self.impact.unit.iloc[:,0].index) # TODO: check to replace by impact.S.index
    elif vec=='sectors' or vec=='sector': array = np.array(self.sectors)
    return([x for i,x in enumerate(array) if string in x])

def is_in(self, secs = None, regs = None): # TODO: check for themis
    '''
    Returns a list of booleans, where an element i is True iff it corresponds to a reg in regs and a sec in secs in the double index regions x sectors.
    
    By default, secs is set to all sectors and regs to all regions.
    '''
    secs, regs = self.prepare_secs_regs(secs, regs)
    if self.name=='THEMIS': return(np.array([r in regs for r in self.labels.idx_regions])*np.array([s in secs for s in self.labels.idx_sectors]))
    else: return([r in regs and s in secs for r in self.regions for s in self.sectors])

def index_secs_regs(self, secs = None, regs = None):
    '''
    Returns an array of the indexes of any element (reg, sec) of regs x secs in the double index of the IOSystem.
    
    By default, secs is set to all sectors and regs to all regions.
    '''
    return(list(np.where(self.is_in(secs, regs))[0]))

def final_demand(self, secs = None, regs = None, only_positive = True):
    '''
    Returns the vector of final demand for (sec, reg) in secs x regs, computed from Y.
    
    If only_positive is True, doesn't take into account 'Changes in inventories' and 'Changes in valuables', which can be negative. (Works only for Exiobase)
    '''
    if only_positive and self.name=='EXIOBASE':
        pos_y = ['Final consumption expenditure by government', 'Gross fixed capital formation', 'Export', \
                'Final consumption expenditure by non-profit organisations serving households (NPISH)', 'Final consumption expenditure by households']
        return(self.Y[[(reg,dom) for reg in self.regions for dom in pos_y]].sum(axis='columns')*self.is_in(secs, regs))
    else: return(self.Y[[(reg,dom) for reg in self.regions for dom in io.Y.columns.levels[1]]].sum(axis='columns')*self.is_in(secs, regs))

@property
def secondary_energy_demand(self): # TODO: precalculate at the instantiation
    '''
    Returns the vector of secondary energy demand.
    '''
    if self.name=='THEMIS': return(self.energy.secondary_demand)
    else: return(self.final_demand(self.energy_sectors('secondary')))

def production(self, secs=None, regs=None):
    '''
    Returns the vector of production of (sec, reg) in secs x regs, computed from x.
    '''    
    secs, regs = self.prepare_secs_regs(secs, regs)  # TODO: for THEMIS --> is that right, to divide the two energies?
    if self.name!='Cecilia':
        if not hasattr(self, 'secondary_energy_supply'): self.secondary_energy_supply = self.energy_supply * self.is_in(self.energy_sectors('secondary'))
        if not hasattr(self, 'secondary_fuel_supply'): self.secondary_fuel_supply = self.energy_supply * self.is_in(self.energy_sectors('secondary_fuels'))
    if self.name=='THEMIS': return(self.is_in(secs, regs) * div0(self.secondary_energy_demand, self.energy_supply))
    else: return(self.x*self.is_in(secs, regs))

def impacts(self, var='Total Energy supply', regs=None, secs=None, join_sort=False): # var = 'Value Added'
    '''
    Returns the vector of impact of type var related directly to (sec, reg) in secs x regs, computed from F.
    
    If join_sort is True, sorts the results by decreasing order of impact, grouped by sector.
    By default, secs is set to all sectors and regs to all regions.
    '''
    secs, regs = self.prepare_secs_regs(secs, regs)
    if self.name=='Cecilia' or (self.name=='EXIOBASE' and self.meta.version=='1'):
        if var=='supply' or var=='Total Energy supply': var = 'Gross Energy Supply - '
        elif var=='use': var = 'Gross Energy Use - '
        impacts = self.materials.F.loc[[s.startswith(var) for s in self.materials.F.index]][[(r,s) for r in regs for s in secs]].sum()
    else: impacts = self.impact.F.loc[var].loc[regs,secs]
    if join_sort: return(sorted_series(impacts.groupby('sector').sum()))
    else: return(impacts)    

@property
def energy_supply(self):
    '''
    Returns the vector of energy supply per unit of product.
    '''
    if self.name=='Cecilia' or (self.name=='EXIOBASE' and self.meta.version=='1'): 
        return(self.materials.S.loc[[s.startswith('Gross Energy Supply - ') for s in self.materials.S.index]].sum())    
    elif self.name=='EXIOBASE' and self.meta.version[0]=='2': return(self.impact.S.loc['Total Energy supply'])
    elif self.name=='THEMIS': 
        if not hasattr(self, 'supply_filled'): return(['Energy Carrier Supply' in sector for sector in self.labels.idx_impacts] * self.impact.S) # acts as .dot()
        else: return(self.supply_filled)
    else: return('Property not yet implemented for this IOSystem.')

# @property
# def secondary_energy_supply(self):
#     '''
#     Returns the vector of secondary energy supply per unit of product.
#     '''
#     if self.name=='THEMIS' or self.name=='EXIOBASE': return(self.energy_supply * self.is_in(self.energy_sectors('secondary')))
#     else: return('Property not yet implemented for this IOSystem.')    
    
# @property
# def secondary_fuel_supply(self):
#     '''
#     Returns the vector of secondary fuel supply per unit of product.
#     '''
#     if self.name=='THEMIS' or self.name=='EXIOBASE': return(self.energy_supply * self.is_in(self.energy_sectors('secondary_fuels')))
#     else: return('Property not yet implemented for this IOSystem.')
    
def embodied_prod(self, secs=None, regs=None, prod = None):
    '''
    Returns the vector of embodied production for (sec, reg) in secs x regs, i.e. all the production required to produce their production, including them.
    
    When the Leontief inverse is not known, computes an approximate solution from the technology matrix A.
    If the production is pre-calculated, it can be passed as an argument.
    '''
    secs, regs = self.prepare_secs_regs(secs, regs)
    if prod is None: prod = self.production(secs, regs)
    if self.L is None: return(spla.cgs(sp.eye(self.A.shape[0])-self.A, prod, approx_solution(self.A,prod).transpose().toarray()[0], tol=1e-7)[0])
    else: return(np.dot(self.L, prod))

def embodied_impact(self, secs=None, regs=None, var='Total Energy supply', source='secondary', group_by='region', sort=False): # TODO: source = None
    '''
    Returns a vector of impact of type var embodied in the production of (sec, reg) in secs x regs, excluding their own production.
    '''
    secs, regs = self.prepare_secs_regs(secs, regs)
    production = self.production(secs, regs)
    share_demand = div0(self.embodied_prod(secs, regs, production)-production, self.x)
    impacts = self.impacts(var)*share_demand
    impacts = impacts[self.index_secs_regs(self.energy_sectors(source))]
    if sort: return(sorted_series(impacts.groupby(group_by).sum()))
    else: return(impacts.groupby(group_by).sum())    

def sorted_array(self, array, index=None, group_by=None):
    '''
    Returns the sorted panda series of the array, grouped by group_by if it is not None, and indexed by index (the default index is that of regions x sectors)
    '''
    if index is None: index = self.x.index
    if group_by is None: return(sorted_series(pd.Series(array, index=index)))
    else: return(sorted_series(pd.Series(array, index=index).groupby(group_by).sum()))
    
# Traverse value chain backwards from regs-secs. group_by: None, sector, region / nb_main: number or 'all
def inputs(self, secs=None, regs=None, var_impacts=[], source='all', order_recursion=4, nb_main=5, group_by='sector'): 
    '''
    Returns the Structural Path Analysis, i.e. the inputs recursively embodied in the production of secs in regs.
    
    var_impacts specifies the impacts of inputs to be displayed (e.g.: 'Total Energy supply', 'global warming (GWP100)', 'Employment' or 'Employment hour')
    source allows to restricts the inputs to certain sectors
    order_recursion gives the number of steps for the recursive inputs
    nb_main gives the number of inputs that are shown for each step
    group_by allows to aggregate the inputs by region or sector (by default)
    
    Returns a tuple of ([impacts], value of inputs, sums[impacts/values][step] of all impacts and values by step (not only the first nb_main which are shown))
    '''
    secs, regs = self.prepare_secs_regs(secs, regs)
    if nb_main=='all': nb_main==self.nb_sectors()*self.nb_regions()
    if source=='all': source = self.sectors
    elif source=='secondary': source = self.energy_sectors('secondary')
    if type(var_impacts)==str: var_impacts = [var_impacts]
    nb_var = len(var_impacts)
    demand = [None for i in range(order_recursion)]
    impacts = [[None for i in range(order_recursion)] for j in range(nb_var)]
    sums = [[] for i in range(nb_var+1)]
#     demand[0] = final_demand(secs, regs)
    demand[0] = self.production(secs, regs)
    for i in range(0, order_recursion):
        if nb_var>0: share_demand_i = div0(demand[i], self.x)
        for l in range(0, nb_var): 
            impacts_l_i = self.impacts(var_impacts[l])*share_demand_i
            impacts[l][i] = impacts_l_i[self.index_secs_regs(source, self.regions)]
            sums[l].append(impacts[l][i].sum())
        if i+1<order_recursion: demand[i+1] = np.dot(self.A, demand[i])
        sums[nb_var].append(demand[i].sum())
    for k in range(0, nb_var): impacts[k] = list(map(lambda j: self.sorted_array(j, group_by=group_by)[0:nb_main],impacts[k]))
    demand = list(map(lambda j: self.sorted_array(j, group_by=group_by)[0:nb_main], demand))
    return((impacts, demand, sums))

def outputs(self, secs, out_sectors=None, nb_main=5):
    '''
    Returns a tuple: (the final demand, the list of sectors taking secs as inputs (i.e. the outputs), sorted decreasingly by use of secs)
    
    The first nb_main values are shown, out_sectors allows to restrict the outputs to certain sectors.
    '''
    outputs_Z = sorted_series(self.Z.iloc[index_secs_regs(secs, self.regions)].sum().groupby('sector').sum()[out_sectors]/production)[0:nb_main]
    if not hasattr(self, 'Y'): return(outputs_Z)
    else:
        if not hasattr(self, 'y'): self.y = np.sum(self.Y, axis=1)
        if out_sectors is None: out_sectors = self.sectors
        production = self.x.iloc[index_secs_regs(secs, self.regions)].sum()
        return((self.y.iloc[index_secs_regs(secs, self.regions)].sum()/production, outputs_Z))

def neer(self, secs, regs=None, var='Total Energy supply', source='secondary', netting_fuel = True):
    '''
    Returns the Net External Energy Ratio of sectors secs in regs, considering the energy from source with notion var.
    
    The formula is: 
    energy supplied / (energy embodied in production (excluding supplied) - fuels as direct inputs for electricity from hydrocarbon (if netting_fuel is True))
    '''
    if netting_fuel and ((type(secs)==str and secs in self.energy_sectors('elec_hydrocarbon')) or secs==self.energy_sectors('elec_hydrocarbon')): input_fuel=True
    else: input_fuel = 0 # We want to include fuels that are used for transportation, not transformed into electricity (this is not secondary anymore)
    secs, regs = self.prepare_secs_regs(secs, regs)
    x = self.production(secs)
    if self.name == 'Cecilia':
        supply = self.impacts(var, regs, secs).sum()
        embodied = self.embodied_impact(secs, regs, var, source).sum()
        if input_fuel: input_fuel = self.inputs(secs, var_impacts=[var], source=self.energy_sectors('secondary_fuels'), order_recursion=2)[2][0][1]
    else: 
        supply = self.energy_supply.dot(x).sum()
        embodied = (self.secondary_energy_supply.dot(self.embodied_prod(secs, prod=x) - x)).sum() 
        if input_fuel: input_fuel = (self.secondary_fuel_supply.dot(self.A.dot(x))).sum()
    return(round(supply/(embodied - input_fuel),1))
        

def erois(self, secs = None, var='Total Energy supply', source='secondary', recompute=False):
    '''
    Returns the list of EROIs (Net External Energy Ratio) of the list of sectors secs, considering the energy from source with notion var.
    '''
    if secs is None: secs = self.energy_sectors('electricities')
    if recompute or not hasattr(self, 'eroi'):
        neers = pd.Series()
        for i, sec in enumerate(secs): 
            eroi_sec = self.neer(sec, self.regions, var, source)
            neers.set_value(secs[i][15:], eroi_sec)
        neers.set_value('Power sector', self.neer([s for s in secs], self.regions, var, source))
        self.eroi = neers.copy()
    return(self.eroi)


def regional_mix(global_mix, nb_regions = 9, nb_sectors = None):
    if nb_sectors is None: nb_sectors = int(max(global_mix.shape)/nb_regions)
    return(div0(global_mix, np.kron(np.eye(nb_regions),np.ones((nb_sectors, nb_sectors))).dot(global_mix)))
    
def change_mix(self, global_mix = None, inplace = True, method = 'regional', path_dlr = None, scenario = None, year = None, only_exiobase = True): 
        # returns A with only renewable electricity in the energy mix, works only for THEMIS
    # method can be 'regional' (default), 'global' or 'gras' (the latter is preferable but requires y and Z)
    if type(global_mix)==dict and scenario is not None and year is not None: global_mix = global_mix[scenario][year]
    elif global_mix is None and path_dlr is not None:
        s = 'ER'
        if year is None: year = 2050 # TODO: make global_mix a function
        dlr_elec = dict()
        for reg in ['World', 'Africa', 'China', 'Eurasia', 'India', 'Latin America', 'Middle East', \
                        'OECD Europe', 'OECD North America', 'OECD Asia Oceania', 'O-Asia']:
            data = pd.read_excel(path_dlr+'Greenpeace_scenarios.xlsx', header=[1], index_col=0, skiprows=[0], skipfooter=144-53, \
                                 sheet_name=s+' '+reg, usecols=[1,2,6,10])
            dlr_elec[reg] = pd.DataFrame(columns = [2012, 2030, 2050])\
                .append(data.loc[['    - Lignite', '    - Hard coal (& non-renewable waste)']].iloc[[1,3]].sum(axis=0).rename('coal'))\
                .append(data.loc['    - Gas'].iloc[1].rename('gas')).append(data.loc[['    - Oil', '    - Diesel']].iloc[[1,2]].sum(axis=0).rename('oil'))\
                .append(data.loc['  - Nuclear'].iloc[0].rename('nuclear')).append(data.loc['    - Biomass (& renewable waste)'].iloc[1].rename('biomass&Waste'))\
                .append(data.loc['  - Hydro'].rename('hydro')).append(data.loc['of which wind offshore'].rename('wind offshore'))\
                .append((data.loc['  - Wind']-data.loc['of which wind offshore']).rename('wind onshore'))\
                .append(data.loc['  - PV'].rename('solar PV')).append(data.loc['    - Geothermal'].iloc[1].rename('geothermal'))\
                .append(data.loc['  - Solar thermal power plants'].rename('solar CSP')).append(data.loc['  - Ocean energy'].rename('ocean'))\
                .rename(columns = {2012: 2010})
        dlr_elec['Africa and Middle East'] = dlr_elec['Africa'] + dlr_elec['Middle East']
        dlr_elec['OECD Pacific'] = dlr_elec.pop('OECD Asia Oceania')
        dlr_elec['Rest of developing Asia'] = dlr_elec.pop('O-Asia')
        dlr_elec['Economies in transition'] = dlr_elec.pop('Eurasia')
        global_mix = []
        dlr_sectors = dlr_elec['World'].index
        themis_BM = themis_parser(path_dlr, year = year, scenario = 'BM')
        for i in themis_BM.index_secs_regs(['Electricity by ' + s for s in themis_BM.energy_sectors('elecs_names')], \
                                                    themis_BM.regions):
            sec, reg = themis_BM.labels.idx_sectors[i][15:], themis_BM.labels.idx_regions[i]
            if sec in dlr_sectors: global_mix = global_mix + [dlr_elec[reg].loc[sec, year]]
            else: global_mix = global_mix + [0]
        global_mix = div0(global_mix, np.array(global_mix).sum())

    if inplace: A = self.A
    else: A = self.A.copy()
    elec_idx = self.index_secs_regs(self.energy_sectors('electricities'))
    if not hasattr(self, 'energy_supply_original'):
        self.energy_supply_original = self.energy_supply.copy()
        self.supply_filled = self.energy_supply.copy() # fill unitary energy supplied of zero energy sectors such as geothermal Africa
        for i in np.array(elec_idx)[np.where(self.energy_supply_original[elec_idx]==0)[0]]: # fills (reg, sec) with 0 supply with mean value of other regs 
            sec_i = self.labels.idx_sectors[i]  # TODO!: median instead of mean?, optimize this piece of code
            self.supply_filled[i] = self.energy_supply_original.dot(self.is_in(sec_i))/len(np.where(self.energy_supply_original*self.is_in(sec_i)!=0)[0])
   # TODO: how to respect energy demand of Greenpeace ?
    if only_exiobase: idx0 = 42219
    else: idx0 = 0
    elecs_by_sec = mult_rows(A[elec_idx,idx0:], self.energy_supply[elec_idx]) # unit of elec needed by each unitary sec
    # TODO: check one unit of output from A corresponds to energy supply units
    
    if method=='global':
    # global_mix . elecs_by_sec: matrix of elec need by sec and type of elec -> /unitary_supply (<=> *unit_per_supply): convert back to arbitrary units
        A[elec_idx,idx0:] = mult_rows(global_mix.reshape(-1,1).dot(elecs_by_sec.sum(axis=0)), div0(1, self.energy_supply[elec_idx]))
    elif method=='regional' or method=='region':
        agg_matrix = sp.kron(sp.eye(self.nb_regions),np.ones((len(self.energy_sectors('electricities')), len(self.energy_sectors('electricities')))))
        A[elec_idx,idx0:] = mult_rows(agg_matrix.dot(elecs_by_sec), div0(regional_mix(global_mix, self.nb_regions), self.energy_supply[elec_idx]))
    elif method=='gras' or method=='GRAS': # GRAS method on submatrix of elecs, never tested
        if inplace: A = self.Z
        else: A = self.Z.copy()    
        elecs_by_sec = mult_rows(A[elec_idx,idx0:], self.energy_supply[elec_idx]) # unit of elec needed by each sec
#         print('starting GRAS')
        new_elecs_by_sec = grasp(elecs_by_sec, new_row_sums = elecs_by_row.sum()*global_mix)
#         print('GRAS complete')
        A[elec_idx,idx0:] = mult_rows(new_elecs_by_row, div0(1, self.energy_supply[elec_idx]))
    else: print('method unknown')
    return(A)

IOS.change_mix = change_mix

IOS.prepare_secs_regs = prepare_secs_regs
IOS.index_secs = index_secs
IOS.index_regs = index_regs
IOS.nb_regions = nb_regions
IOS.nb_sectors = nb_sectors
IOS.find = find
# IOS.index_regs_secs = index_regs_secs
IOS.is_in = is_in
IOS.final_demand = final_demand
IOS.index_secs_regs = index_secs_regs
IOS.production = production
IOS.impacts = impacts
IOS.embodied_prod = embodied_prod
IOS.embodied_impact = embodied_impact
IOS.sorted_array = sorted_array
IOS.inputs = inputs
IOS.outputs = outputs
IOS.neer = neer
IOS.erois = erois
IOS.energy_sectors = energy_sectors
IOS.regions = regions
IOS.sectors = sectors
# IOS.secondary_energy_supply = secondary_energy_supply
IOS.secondary_energy_demand = secondary_energy_demand
# IOS.secondary_fuel_supply = secondary_fuel_supply
IOS.energy_supply = energy_supply
IOS.change_mix = change_mix
# IOS. = 
# IOS. = 
# other: internal_energy, composition_impact, change IOT for efficiency or gdp, calc_Z, etc., not_regs, regs_or_no, gdp, import, embodied_import