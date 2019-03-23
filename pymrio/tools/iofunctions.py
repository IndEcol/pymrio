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
from pymrio.tools.iomath import inter_secs
from pymrio.tools.iomath import gras
from pymrio.tools.ioparser import themis_parser
import pandas as pd
import numpy as np
import scipy.sparse as sp 
from scipy.sparse import linalg as spla
from openpyxl import load_workbook

# TODO: manage Themis, Cecilia, and futures

def energy_sectors(self, notion): # TODO: other sectors, difference from elecs_names to add after elec and to display
    '''
    Returns the list of energy sectors (or names) corresponding to notion, which can be: secondary, secondary_fuels, elec_hydrocarbon, electricities,elecs_names
    '''
    if notion is None: sectors = self.sectors
    elif notion not in ['secondary', 'secondary_fuels', 'elec_hydrocarbon', 'electricities', 'elecs_names', 'secondary_heats', 'renewable', 'renew_names']:
        print('Error: notion unknown')
    elif notion=='elec_hydrocarbon': sectors = ['Electricity by coal', 'Electricity by gas']
    elif notion=='secondary_fuels': sectors = ['Motor Gasoline', 'Gas/Diesel Oil', 'Heavy Fuel Oil', 'Liquefied Petroleum Gases (LPG)', \
         'Naphtha', 'Non-specified Petroleum Products', 'Kerosene', 'Kerosene Type Jet Fuel', 'Petroleum Coke', 'Aviation Gasoline', 'Gasoline Type Jet Fuel']
    elif notion=='electricities': sectors = ['Electricity by ' + s for s in self.energy_sectors('elecs_names')]
    elif notion=='renewable': sectors = ['Electricity by ' + s for s in self.energy_sectors('renew_names')]
    elif notion=='secondary_heats': sectors = ['Steam and hot water supply services'] + self.energy_sectors('secondary_fuels')
        
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
#  'Liquefied Petroleum Gases (LPG)', 'Naphtha', 'Non-specified Petroleum Products', 'Kerosene','Petroleum Coke', 'Aviation Gasoline', 'Gasoline Type Jet Fuel']
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
        elif notion=='renew_names': sectors = ['wind onshore', 'wind offshore', 'solar PV', 'hydro', 'biomass&Waste', 'biomass w CCS', \
                                             'ocean', 'geothermal', 'solar CSP']
    else: print('Function not yet implemented for this IOSystem')
    return(sectors)

@property
def regions(self): 
    '''
    Returns the list of all regions in the IOSystem
    '''
    if self.name == 'THEMIS' or self.name == 'Cecilia': return(self.labels.regions)
    else: return(list(self.get_regions())) 

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

@property
def nb_regions(self): return(len(self.regions))

@property
def nb_sectors(self): return(len(self.sectors))

def find(self, string, vec='impacts'): # TODO: allow insensitivity to case
    '''
    Find vec=impacts/sectors containing string.
    '''
    if vec=='impacts' or vec=='Impacts' or vec=='impact': 
        if self.name == 'THEMIS': array = np.array(self.labels.idx_impacts)
        else: array = np.array(self.impact.unit.iloc[:,0].index) # TODO: check to replace by impact.S.index
    elif vec=='sectors' or vec=='sector': array = np.array(self.sectors)
    return([x for i,x in enumerate(array) if string in x])

def is_in(self, secs = None, regs = None): # TODO: trim spaces for themis' foreground
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
def secondary_energy_demand(self): # TODO: precalculate at the instantiation / TODO!: rename in 'electricity_demand' because this is what it is
    '''
    Returns the vector of secondary energy demand.
    '''
    if self.name=='THEMIS': return(self.energy.secondary_demand)
    else: return(self.final_demand(self.energy_sectors('secondary')))
    
@property
def VA(self): # TODO: exiobase
    '''
    Returns the vector of value added, by summing Operating surplus (Consumption of fixed capital, Rents on land, Royalties on resources, 
    Remainin net operating surplus), Compensation of Employees (wages & salaries, employers social contributions) and Fixed capital formation, unit: M€
    '''
    if self.name=='THEMIS':
        if not hasattr(self, 'VA_filled'): self.VA_filled = np.array(self.impact.S.tocsc()[list(range(1618,1624))+[1630]].sum(axis=0)).flatten()
        return(self.VA_filled)
    else: print('"Value added" not yet implemented for database other than THEMIS')

def production(self, secs=None, regs=None, non_unitary_themis = True): # TODO: change name 'non_unitary_themis' to 'secondary_energy_sector'?
    '''
    Returns the vector of production of (sec, reg) in secs x regs, computed from x.
    /!\ Beware, for THEMIS, production is unitary, unless non_unitary_themis = True, 
    In this case it is inferred using energy_demand/energy_supply for energy sectors, but is 0 for non-energy sectors.
    Setting non_unitary_themis to True provides better estimates for global EROIs but cannot cover foreground sectors, while setting it to False provides the 
    same estimates as True when the sector is unique (e.g. one sector in one region) and covers foreground, but is imprecise for several sectors or regions
    '''    
    secs, regs = self.prepare_secs_regs(secs, regs)
    if self.name!='Cecilia':
        if not hasattr(self, 'secondary_energy_supply'): self.secondary_energy_supply = self.energy_supply * self.is_in(self.energy_sectors('secondary'))
        if not hasattr(self, 'secondary_fuel_supply'): self.secondary_fuel_supply = self.energy_supply * self.is_in(self.energy_sectors('secondary_fuels'))
    if self.name=='THEMIS': 
        if non_unitary_themis: return(self.is_in(secs, regs) * div0(self.secondary_energy_demand, self.energy_supply))
        else: return(self.is_in(secs, regs))
    else: return(self.x*self.is_in(secs, regs)) 

def impacts(self, var='Total Energy supply', regs=None, secs=None, join_sort=False): # var = 'Value Added'
    '''
    Returns the vector of impact of type var related directly to (sec, reg) in secs x regs, computed from F.
    
    If join_sort is True, sorts the results by decreasing order of impact, grouped by sector.
    By default, secs is set to all sectors and regs to all regions.
    /!\ will be 0 for THEMIS & Total Energy supply if non_unitary_themis=True in production because production will be 0 (it doesn't matter for EROIs 
    computation because production is then computed from another way, and is not 0)
    '''
    secs, regs = self.prepare_secs_regs(secs, regs)
    if self.name=='Cecilia' or (self.name=='EXIOBASE' and self.meta.version=='1'):
        if var=='supply' or var=='Total Energy supply': var = 'Gross Energy Supply - '
        elif var=='use': var = 'Gross Energy Use - '
        impacts = self.materials.F.loc[[s.startswith(var) for s in self.materials.F.index]][[(r,s) for r in regs for s in secs]].sum()
    else: 
        if var=='Total Energy supply': 
            y = self.production(secs, regs)
            impacts = (self.energy_supply * y)[self.index_secs_regs(secs, regs)]
        else: impacts = self.impact.F.loc[var].loc[regs,secs]
    if join_sort: return(sorted_series(impacts.groupby('sector').sum()))
    else: return(impacts)   

@property
def energy_supply(self):
    '''
    Returns the vector of energy supply per unit of product (in TJ).
    '''
    if self.name=='Cecilia' or (self.name=='EXIOBASE' and self.meta.version=='1'): 
        return(self.materials.S.loc[[s.startswith('Gross Energy Supply - ') for s in self.materials.S.index]].sum())
    elif self.name=='EXIOBASE' and self.meta.version[0]=='2': return(self.impact.S.loc['Total Energy supply'])
    elif self.name=='THEMIS': 
        if not hasattr(self, 'supply_filled'): 
            self.supply_filled = ['Energy Carrier Supply' in sector for sector in self.labels.idx_impacts] * self.impact.S # act as .dot()
            self.supply_filled[self.index_secs_regs('Electricity by solar CSP')] = np.ones(self.regions.size) * \
                max(self.supply_filled[self.index_secs_regs('Electricity by solar CSP')]) # to have credible figures for solar CSP
                # without this, supply[CSP] = [0,0,0,10,80,5,0,0] which is weird, I set everything to 80 # except wind, no such discrepancy in other technos
        return(self.supply_filled)
    else: return('Property not yet implemented for this IOSystem.')
    
@property
def employment_low(self): # TODO: exiobase
    '''
    Returns the vector of Employment: low skilled, unit: 1000 persons
    '''
    if self.name=='THEMIS':
        if not hasattr(self, 'empl_low'): self.empl_low = self.impact.S.tocsc()[1624].toarray().flatten()
        return(self.empl_low)
    else: print('"Employment" not yet implemented for database other than THEMIS')
    
@property
def employment_medium(self): # TODO: exiobase
    '''
    Returns the vector of Employment: medium skilled, unit: 1000 persons
    '''
    if self.name=='THEMIS':
        if not hasattr(self, 'empl_medium'): self.empl_medium = self.impact.S.tocsc()[1625].toarray().flatten()
        return(self.empl_medium)
    else: print('"Employment" not yet implemented for database other than THEMIS')
            
@property
def employment_high(self): # TODO: exiobase
    '''
    Returns the vector of Employment: high skilled, unit: 1000 persons
    '''
    if self.name=='THEMIS':
        if not hasattr(self, 'empl_high'): self.empl_high = self.impact.S.tocsc()[1626].toarray().flatten()
        return(self.empl_high)
    else: print('"Employment" not yet implemented for database other than THEMIS')
                    
@property
def employment_all(self): # TODO: exiobase
    '''
    Returns the vector of Employment (all skills combined), unit: 1000 persons
    '''
    if self.name=='THEMIS':
        if not hasattr(self, 'empl_all'): self.empl_all = np.array(self.impact.S.tocsc()[1624:1627].sum(axis=0)).flatten()
        return(self.empl_all)
    else: print('"Employment" not yet implemented for database other than THEMIS')
             
def embodied_prod(self, secs=None, regs=None, prod = None):
    '''
    Returns the vector of embodied production for (sec, reg) in secs x regs, i.e. all the production required to produce their production, including them.
    
    When the Leontief inverse is not known, computes an approximate solution from the technology matrix A.
    If the production is pre-calculated, it can be passed as an argument.
    /!\ Beware, for THEMIS, production is inferred using energy_demand/energy_supply for energy sectors, but is unitary for non-energy sectors.
    '''
    secs, regs = self.prepare_secs_regs(secs, regs)
    if prod is None: prod = self.production(secs, regs)
    if self.L is None: return(spla.cgs(sp.eye(self.A.shape[0])-self.A, prod, approx_solution(self.A,prod).transpose().toarray()[0], tol=1e-7)[0])
    else: return(np.dot(self.L, prod))

def embodied_impact(self, secs=None, regs=None, var='Total Energy supply', source='secondary', group_by='region', sort=False, production = None):
    '''
    Returns a vector of impact of type var embodied in the production of (sec, reg) in secs x regs, excluding their own production, and including only impacts
    from sectors in energy_sectors(source). Results are grouped by group_by (default: region) and can be sorted in decreasing order (default: unsorted).
    '''
    secs, regs = self.prepare_secs_regs(secs, regs) # TODO: source = None
    if production is None: production = self.production(secs, regs)
    if var=='Total Energy supply' and self.name != 'Cecilia':
        impacts = self.secondary_energy_supply * (self.embodied_prod(secs, prod=production) - production)
        impacts = pd.Series(impacts, index = pd.MultiIndex.from_arrays([self.labels.idx_regions, self.labels.idx_sectors], names=['region', 'sector']))
    else:
        share_demand = div0(self.embodied_prod(secs, regs, production)-production, self.x)
        impacts = self.impacts(var)*share_demand        
    impacts = impacts[self.index_secs_regs(self.energy_sectors(source))]
    if sort: return(sorted_series(impacts.groupby(group_by).sum()))
    else: return(impacts.groupby(group_by).sum())  
    
    
def employment(self, secs = None, regs = None, skill='all', prod = None, indirect = True): # TODO: exiobase
    '''
    For THEMIS: Returns the employment (in k persons) of the embodied production of sectors secs in regions regs.
    skill can be 'low', 'medium', 'high' or 'all'.
    '''
    secs, regs = self.prepare_secs_regs(secs, regs)
    if prod is None: prod = self.production(secs, regs)
    if indirect: x = self.embodied_prod(secs, prod=prod)
    else: x = prod
    if skill=='low': return((self.employment_low * x).sum())
    elif skill=='medium': return((self.employment_medium * x).sum())
    elif skill=='high': return((self.employment_high * x).sum())
    elif skill=='all': return((self.employment_all * x).sum())

def employments(self, secs = None, skill='all', recompute = True, indirect = True):
    '''
    Returns the serie of employments for the given skills at the global level of the list of sectors secs.
    '''
    if secs is None: secs = self.energy_sectors('electricities')
    if recompute or not hasattr(self, 'employ'):
        employments = pd.Series()
        for i, sec in enumerate(secs): 
            empl_sec = self.employment(secs = sec, skill=skill, indirect = indirect)
            employments.at[secs[i][15:]] = empl_sec
        self.employ = employments
    return(self.employ)

def value_added(self, secs = None, regs = None, prod = None, indirect = True): # TODO: exiobase
    '''
    For THEMIS: Returns the value added (in M€) of the embodied production of sectors secs in regions regs.
    '''
    secs, regs = self.prepare_secs_regs(secs, regs)
    if prod is None: prod = self.production(secs, regs)
    if indirect: return((self.VA * self.embodied_prod(secs, prod=prod)).sum())
    else: return((self.VA * self.production(secs, prod=prod)).sum())

def price_energy(self, secs = None, regs = None, digits=0, indirect = True): # TODO: exiobase; while let the choice of indirect? indirect=False makes no sense
    '''
    For THEMIS: Returns the price of energy (in M€/TWh = €/MWh) of sectors secs in regions regs, computed using the value added of the embodied production.
    '''
    TWh2TJ = 3.6e3
    if secs is None: secs = self.energy_sectors('electricities')
    prod = self.production(secs, regs)
    return(round(self.value_added(secs, regs, prod = prod, indirect = indirect) / ((self.energy_supply @ prod) / TWh2TJ), digits))

def energy_prices(self, secs = None, recompute = False, indirect = True):
    '''
    Returns the serie of energy prices at the global level of the list of sectors secs.
    '''
    if secs is None: secs = self.energy_sectors('electricities')
    if recompute or not hasattr(self, 'energy_price'):
        prices = pd.Series()
        for i, sec in enumerate(secs): 
            price_sec = self.price_energy(secs = sec, indirect = indirect)
            prices.at[secs[i][15:]] = price_sec
        self.energy_price = prices
    return(self.energy_price)

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
    For THEMIS, returns only the second elements, embodied inputs, whose values have no clear interpretation because their units vary and can be physical.
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
    if self.name=='THEMIS':
        multi_index = pd.MultiIndex.from_arrays([self.labels.idx_regions, self.labels.idx_sectors], names=['region', 'sector']) # TODO: set as .x.index
        demand[0] = pd.Series(self.is_in(secs, regs), index = multi_index)
        for i in range(0, order_recursion):
            if i+1<order_recursion: demand[i+1] = pd.Series(self.A.dot(demand[i]), index = multi_index)
        demand = list(map(lambda j: self.sorted_array(j * self.is_in(source, self.regions), index=multi_index, group_by=group_by)[0:nb_main], demand))
        return(demand) # TODO: stop showing recursive inputs as soon as they are 0.
    else:
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
    if out_sectors is None: out_sectors = self.sectors
    if self.name=='THEMIS': 
        multi_index = pd.MultiIndex.from_arrays([self.labels.idx_regions, self.labels.idx_sectors], names=['region', 'sector'])
        outputs_Z = sorted_series(pd.Series(np.array(self.A[self.index_secs_regs(secs, self.regions),:].sum(axis=0))[0],\
                   index=multi_index).groupby('sector').sum()[out_sectors])[0:nb_main]
    else: 
        production = self.x.iloc[self.index_secs_regs(secs, self.regions)].sum()
        outputs_Z = sorted_series(self.Z.iloc[self.index_secs_regs(secs, self.regions)]\
                                    .sum().groupby('sector').sum()[out_sectors]/production)[0:nb_main]
    if not hasattr(self, 'Y') or self.Y is None: return(outputs_Z)
    else:
        if not hasattr(self, 'y'): self.y = np.sum(self.Y, axis=1)
        if out_sectors is None: out_sectors = self.sectors
        return((self.y.iloc[self.index_secs_regs(secs, self.regions)].sum()/production, outputs_Z))

def energy_required(self, secs, regs=None, var='Total Energy supply', source='secondary', netting_fuel = True):
    '''
    Returns the energy required to produce one unit of energy in sectors secs in regs, considering the energy from source with notion var, and 
    decomposed according to the sources in partition_sources.
    
    The formula is: 
    (energy embodied in production (excluding supplied) - fuels as direct inputs for electricity from hydrocarbon (if netting_fuel is True)) / energy supplied
    '''
    if len(secs)==1: secs = secs[0]
    sec_string = type(secs)==str or type(secs)==np.str_
    if netting_fuel and ((sec_string and secs in self.energy_sectors('elec_hydrocarbon')) or secs==self.energy_sectors('elec_hydrocarbon') \
                          or secs==self.energy_sectors('electricities')) or secs==list(np.array(self.energy_sectors('electricities'))\
                          [['CCS' not in s for s in self.energy_sectors('electricities')]]): input_fuel=True
    else: input_fuel = 0 # We want to include fuels that are used for transportation, not transformed into electricity (this is not secondary anymore)
    secs, regs = self.prepare_secs_regs(secs, regs)
    if self.name != 'Cecilia' and var != 'Total Energy supply': 
        print('neer not implemented for var of type ' + var + ", doing it for 'Total Energy supply' instead")
        var = 'Total Energy supply'
    prod = self.production(secs, regs)
    embodied = self.embodied_impact(secs, regs, var, source, production = prod).sum()
    if input_fuel:
        if self.name == 'Cecilia': input_fuel = self.inputs(secs, var_impacts=[var], \
            source=inter_secs(self.energy_sectors('secondary_fuels'), self.energy_sectors(source)), order_recursion=2)[2][0][1]
        elif secs==self.energy_sectors('electricities') or secs==list(np.array(self.energy_sectors('electricities'))\
                          [['CCS' not in s for s in self.energy_sectors('electricities')]]): 
            prod_fuel = self.production(self.energy_sectors('elec_hydrocarbon'), regs)
            input_fuel = ((self.secondary_fuel_supply * self.A.dot(prod_fuel))[self.index_secs_regs(self.energy_sectors(source))]).sum()
        else: input_fuel = ((self.secondary_fuel_supply * self.A.dot(prod))[self.index_secs_regs(self.energy_sectors(source))]).sum()
    return(embodied - input_fuel)

def neer(self, secs, regs=None, var='Total Energy supply', source='secondary', netting_fuel = True, factor_elec = 1):
    '''
    Returns the Net External Energy Ratio of sectors secs in regs, considering the energy from source with notion var.
    
    The formula is: 
    energy supplied / (energy embodied in production (excluding supplied) - fuels as direct inputs for electricity from hydrocarbon (if netting_fuel is True))
    '''
    er = factor_elec*self.energy_required(secs, regs, var, 'electricities', netting_fuel) +self.energy_required(secs, regs, var, 'secondary_heats', netting_fuel)
#     if ((type(secs)==str and secs in self.energy_sectors('electricities')) or secs==self.energy_sectors('electricities')): 
#         return(round(factor_elec * self.impacts(var, regs, secs).sum() / er, 1))
#     else: return(round(self.impacts(var, regs, secs).sum() / er, 1))
    if var=='Total Energy supply' and source=='secondary': supply = self.secondary_energy_demand[self.index_secs_regs(secs, regs)].sum()
    else: supply = self.impacts(var, regs, secs).sum() # TODO!: Why impacts doesn't work in all cases?!
    return(round(factor_elec * supply / er, 1)) # TODO!: code the option non_unitary_themis=False for biofuels and cie

def erois(self, secs = None, var='Total Energy supply', source='secondary', netting_fuel = True, factor_elec = 1, recompute=False):
    '''
    Returns the serie of EROIs (Gross Energy Ratio) of the list of sectors secs, considering the energy from source with notion var.
    '''
    if secs is None: 
        if self.scenario in ['REF', 'ER', 'ADV', 'combo']: secs = list(np.array(self.energy_sectors('electricities'))\
                                                                    [['CCS' not in s for s in self.energy_sectors('electricities')]])
        else: secs = self.energy_sectors('electricities')
    if recompute or not hasattr(self, 'eroi'):
        neers = pd.Series()
        for i, sec in enumerate(secs): 
            eroi_sec = self.neer(secs=sec, regs=self.regions, var=var, source=source, netting_fuel=netting_fuel, factor_elec=factor_elec)
            neers.at[secs[i][15:]] = eroi_sec
#             neers.set_value(secs[i][15:], eroi_sec)
#         neers.set_value('Power sector', self.neer([s for s in secs], self.regions, var, source, netting_fuel, factor_elec))
        neers.at['Power sector'] = self.neer(secs, self.regions, var, source, netting_fuel, factor_elec)
    # we could also have used that eroi_total = 1/sum(share_mix_s / EROI_s, s in sectors)
        self.eroi = neers.copy()
    return(self.eroi)

def erois_and_prices(self, secs = None, var='Total Energy supply', source='secondary', netting_fuel = True, factor_elec = 1, recompute=False):
    '''
    Returns the series of regional EROIs and prices of the list of sectors secs for each region, considering the energy from source with notion var.
    '''
    if secs is None: 
        if self.scenario in ['REF', 'ER', 'ADV', 'combo']: secs = list(np.array(self.energy_sectors('electricities'))\
                                                                    [['CCS' not in s for s in self.energy_sectors('electricities')]])
        else: secs = self.energy_sectors('electricities')
    if recompute or not hasattr(self, 'eroi_price'):
        res = pd.DataFrame(index = pd.MultiIndex.from_product([list(self.regions)+['World'], secs+['total']], names=['region', 'sector']), \
                           columns = ['eroi', 'price'])
        for reg in self.regions:
            for i, sec in enumerate(secs):
                res['eroi'][(reg, sec)] =self.neer(secs=sec,regs=reg,var=var,source=source,netting_fuel=netting_fuel,factor_elec=factor_elec)
                res['price'][(reg, sec)] = self.price_energy(secs = sec, regs = reg, digits=5, indirect = True)
            res['eroi'][(reg, 'total')]=self.neer(secs=secs,regs=reg,var=var,source=source,netting_fuel=netting_fuel,factor_elec=factor_elec)
            res['price'][(reg, 'total')] = self.price_energy(secs = secs, regs = reg, digits=5, indirect = True)
        for i, sec in enumerate(secs):
            res['eroi'][('World', sec)]=self.neer(secs=sec, regs=self.regions, var=var, source=source, netting_fuel=netting_fuel, factor_elec=factor_elec)
            res['price'][('World', sec)] = self.price_energy(secs = sec, regs = self.regions, digits=5, indirect = True)        
        res['eroi'][('World', 'total')]=self.neer(secs=secs,regs=self.regions,var=var,source=source,netting_fuel=netting_fuel,factor_elec=factor_elec)
        res['price'][('World', 'total')] = self.price_energy(secs = secs, regs = self.regions, digits=5, indirect = True)
        self.eroi_price = res.copy()
    return(self.eroi_price)

def err(self, secs, regs=None, var='Total Energy supply', partition_sources=['secondary_heats', 'electricities'], netting_fuel = True, decimals=2):
    '''
    Returns energy required to produce one unit of energy in sectors secs in regs, decomposed according to the sources in partition_sources.
    '''
    ratios = {}
    for source in partition_sources:
#         ratio[source] = round(1/self.neer(secs = secs, regs = regs, var = var, source = source, netting_fuel = netting_fuel), decimals)
        ratios[source] = round(self.energy_required(secs=secs, regs=regs, var=var, source=source, netting_fuel=netting_fuel)\
                           /self.impacts(var, regs, secs).sum(), decimals) # impacts = supply
    return(ratios) # TODO: put this and errs in the install, check them before
    
def errs(self, secs=None, var='Total Energy supply', partition_sources=['secondary_heats', 'electricities'], netting_fuel = True, recompute = False):
    '''
    Returns the series of energy required of the list of sectors secs, decomposed according to the sources in partition_sources.
    '''
    if secs is None: secs = self.energy_sectors('electricities')
    if recompute or not hasattr(self, 'errs'):
        errs = pd.DataFrame(columns = partition_sources)
        for i, sec in enumerate(secs): 
            err_sec = self.err(sec, regs = self.regions, var = var, partition_sources = partition_sources, netting_fuel = netting_fuel)
            errs = errs.append(pd.Series(er_sec).rename(secs[i][15:]))
        errs = errs.append(pd.Series(self.err([s for s in secs], regs = self.regions, var = var, partition_sources = partition_sources, \
                                           netting_fuel = netting_fuel)).rename('Power sector'))
        self.errs = errs.copy()
    return(self.errs) # TODO: add column 'total'
       
def regional_mix(global_mix, nb_regions = 9, nb_sectors = None):
    '''
    Returns an array of regional mixes (i.e. stacked shares of sec in each reg), computed from an array of global mix (i.e. shares of sec x reg in global total)
    '''
    if nb_sectors is None: nb_sectors = int(max(global_mix.shape)/nb_regions)
    return(div0(global_mix, np.kron(np.eye(nb_regions),np.ones((nb_sectors, nb_sectors))).dot(global_mix)))

def mix(self, scenario = None, path_dlr = '/media/adrien/dd/adrien/DD/Économie/Données/Themis/', recompute = False): # TODO: change name to mix_dlr
    '''
    Returns an array of global mix (i.e. shares of sec x reg in global total) and stores it as an attribute
    for DLR (= Greenpeace) scenario in ['REF', 'ER', 'ADV'] for year in [2010, 2030, 2050]
    ''' 
    if scenario is None: scenario = self.scenario
    if not hasattr(self, 'dlr_elec') or self.dlr_elec=={}:
        self.dlr_elec = dict()
        for reg in ['World', 'Africa', 'China', 'Eurasia', 'India', 'Latin America', 'Middle East', \
                        'OECD Europe', 'OECD North America', 'OECD Asia Oceania', 'O-Asia']:
            data = pd.read_excel(path_dlr+'Greenpeace_scenarios.xlsx', header=[1], index_col=0, skiprows=[0], skipfooter=144-53, \
                                 sheet_name=scenario+' '+reg, usecols=[1,2,6,10])
            self.dlr_elec[reg] = pd.DataFrame(columns = [2012, 2030, 2050])\
                .append(data.loc[['    - Lignite', '    - Hard coal (& non-renewable waste)']].iloc[[1,3]].sum(axis=0).rename('coal'))\
                .append(data.loc['    - Gas'].iloc[1].rename('gas')).append(data.loc[['    - Oil', '    - Diesel']].iloc[[1,2]].sum(axis=0).rename('oil'))\
                .append(data.loc['  - Nuclear'].iloc[0].rename('nuclear')).append(data.loc['    - Biomass (& renewable waste)'].iloc[1].rename('biomass&Waste'))\
                .append(data.loc['  - Hydro'].rename('hydro')).append(data.loc['of which wind offshore'].rename('wind offshore'))\
                .append((data.loc['  - Wind']-data.loc['of which wind offshore']).rename('wind onshore'))\
                .append(data.loc['  - PV'].rename('solar PV')).append(data.loc['    - Geothermal'].iloc[1].rename('geothermal'))\
                .append(data.loc['  - Solar thermal power plants'].rename('solar CSP')).append(data.loc['  - Ocean energy'].rename('ocean'))\
                .rename(columns = {2012: 2010})
        self.dlr_elec['Africa and Middle East'] = self.dlr_elec['Africa'] + self.dlr_elec['Middle East']
        self.dlr_elec['OECD Pacific'] = self.dlr_elec.pop('OECD Asia Oceania')
        self.dlr_elec['Rest of developing Asia'] = self.dlr_elec.pop('O-Asia')
        self.dlr_elec['Economies in transition'] = self.dlr_elec.pop('Eurasia') # TODO: put this and below in a dataframe format
        
    if not hasattr(self, 'dlr_capacity'):
        self.dlr_capacity = dict()
        for reg in ['World', 'Africa', 'China', 'Eurasia', 'India', 'Latin America', 'Middle East', \
                        'OECD Europe', 'OECD North America', 'OECD Asia Oceania', 'O-Asia']:
            data = pd.read_excel(path_dlr+'Greenpeace_scenarios.xlsx', header=[1], index_col=0, skiprows=[0], skipfooter=144-23, \
                                 sheet_name=scenario+' '+reg, usecols=[12,13,17,21])
            self.dlr_capacity[reg] = pd.DataFrame(columns = [2012, 2030, 2050])\
                .append(data.loc[['    - Lignite', '    - Hard coal (& non-renewable waste)']].sum(axis=0).rename('coal'))\
                .append(data.loc['    - Gas (w/o H2)'].rename('gas')).append(data.loc[['    - Oil', '    - Diesel']].sum(axis=0).rename('oil'))\
                .append(data.loc['  - Nuclear'].rename('nuclear')).append(data.loc['    - Biomass (& renewable waste)'].rename('biomass&Waste'))\
                .append(data.loc['    - Hydro'].rename('hydro')).append(data.loc['of which wind offshore'].rename('wind offshore'))\
                .append((data.loc['    - Wind']-data.loc['of which wind offshore']).rename('wind onshore'))\
                .append(data.loc['    - PV'].rename('solar PV')).append(data.loc['    - Geothermal'].rename('geothermal'))\
                .append(data.loc['    - Solar thermal power plants'].rename('solar CSP')).append(data.loc['    - Ocean energy'].rename('ocean'))\
                .rename(columns = {2012: 2010})
        self.dlr_capacity['Africa and Middle East'] = self.dlr_capacity['Africa'] + self.dlr_capacity['Middle East']
        self.dlr_capacity['OECD Pacific'] = self.dlr_capacity.pop('OECD Asia Oceania')
        self.dlr_capacity['Rest of developing Asia'] = self.dlr_capacity.pop('O-Asia')
        self.dlr_capacity['Economies in transition'] = self.dlr_capacity.pop('Eurasia')
        
        self.adjustment_capacity = dict()
        self.adjust_capacity = dict()
        for y in [2010, 2030, 2050]:
            self.adjustment_capacity[y] = pd.Series(index = pd.MultiIndex.from_product([self.regions, self.dlr_elec['World'].index], names=['region', 'sector']))
            self.adjust_capacity[y] = [0] * len(self.labels.idx_sectors)
            for reg in self.regions: # TODO: which energy.capacity are 0?
                for sec in self.dlr_elec['World'].index:
                    self.adjust_capacity[y][self.index_secs_regs('Electricity by ' + sec, reg)[0]] = div0(div0(self.dlr_capacity[reg][y].loc[sec], \
                        self.dlr_elec[reg][y].loc[sec]), div0(self.energy.capacity[(reg, y)].loc['Electricity by ' + sec], \
                        self.energy.demand[(reg, y)].loc['Electricity by ' + sec]), replace_by=1)
                    self.adjustment_capacity[y][(reg, sec)] = div0(div0(self.dlr_capacity[reg][y].loc[sec], self.dlr_elec[reg][y].loc[sec]), \
                        div0(self.energy.capacity[(reg, y)].loc['Electricity by ' + sec], self.energy.demand[(reg, y)].loc['Electricity by ' + sec]), replace_by=1)

    if recompute or not hasattr(self, 'mixes'):
        mix = dict()
        for year in [2010, 2030, 2050]:
            mix[year] = []
            dlr_sectors = self.dlr_elec['World'].index
            for i in self.index_secs_regs(['Electricity by ' + s for s in self.energy_sectors('elecs_names')], self.regions):
                sec, reg = self.labels.idx_sectors[i][15:], self.labels.idx_regions[i]
                if sec in dlr_sectors: mix[year] = mix[year] + [self.dlr_elec[reg].loc[sec, year]]
                else: mix[year] = mix[year] + [0]
            mix[year] = div0(mix[year], np.array(mix[year]).sum())
        self.mixes = mix
    return(self.mixes)
        
def change_mix(self, global_mix = None, inplace = True, method = 'regional', path_dlr = None, scenario = None, year = None, only_exiobase = True,adjust_GW=True): 
    '''
    (for THEMIS) Returns matrix A with electricity inputs replaced according to the new mix global_mix
    global_mix gives the share of each techno-region in the global mix, so that its sum is the number of regions
    As arguments, either global_mix and year must be passed, or path_dlr, scenario and year
    only_exiobase = True doesn't modify the matrix for outputs other than background ones (in practice, True or False doesn't change EROI results)
    method = ['gras', 'regional', 'global']: GRAS is preferable but requires Z (and y) (absent from THEMIS), 'regional' (default) assumes the same mix for each
    sector of a given region, 'global' the same mix for each sector globally
    '''
    if year is None: print('year must be provided, otherwise I cannot infer total demand')
    if type(global_mix)==dict and scenario is not None and year is not None: global_mix = global_mix[scenario][year]
    elif global_mix is None and path_dlr is not None:
        if scenario is not None: self.scenario = scenario
        global_mix = self.mix(path_dlr = path_dlr)[year]
        
    if hasattr(self, 'dlr_elec'): dlr_sectors = self.dlr_elec['World'].index
    else: dlr_sectors = self.energy_sectors('elecs_names')
    TWh2TJ = 3.6e3
    self.secondary_energy_demand[np.where(self.secondary_energy_demand!=0)[0]] = 0
    for reg in self.regions: # TODO: integrate this change in secondary_energy_demand more properly
        if hasattr(self, 'dlr_elec'):
            for sec in dlr_sectors: self.secondary_energy_demand[self.index_secs_regs('Electricity by ' + sec, reg)] = self.dlr_elec[reg][year][sec] * TWh2TJ
        else:
            total_demand = self.secondary_energy_demand[self.index_secs_regs(dlr_sectors)].sum()
            self.secondary_energy_demand[self.index_secs_regs(self.energy_sectors('electricities'))] = global_mix * TWh2TJ
                        
    if inplace: A = self.A
    else: A = self.A.copy()
    elec_idx = self.index_secs_regs(self.energy_sectors('electricities'))
    if not hasattr(self, 'energy_supply_original'):
        self.energy_supply_original = self.energy_supply.copy()
        self.supply_filled = self.energy_supply.copy() # fill unitary energy supplied of zero energy sectors such as geothermal Africa
        for i in np.array(elec_idx)[np.where(self.energy_supply_original[elec_idx]==0)[0]]: # fills (reg, sec) with 0 supply with mean value of other regs 
            sec_i = self.labels.idx_sectors[i]  
            self.supply_filled[i] = self.energy_supply_original.dot(self.is_in(sec_i))/len(np.where(self.energy_supply_original*self.is_in(sec_i)!=0)[0])

    if only_exiobase: idx0 = 42219
    else: idx0 = 0
    elecs_by_sec = mult_rows(A[elec_idx,idx0:], self.energy_supply[elec_idx]) # unit of elec needed by each unitary sec
    
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
    
    if adjust_GW and self.scenario in ['REF', 'ER', 'ADV'] and hasattr(self, 'adjust_capacity'): 
        renewable_idx = self.index_secs_regs(self.energy_sectors('renewable'))
        A[:, renewable_idx] = mult_cols(A[:, renewable_idx], np.array(self.adjust_capacity[year])[renewable_idx])
    return(A)

def mix_matrix(self, secs = None, method='demand', global_mix = True, digits = 2): # TODO: store as attribute
    '''
    Returns the share of energy supplied by each sec in secs (among the energy supplied by all secs), according to the IOT.
    The result is at the global level if global_mix = True, at regional level if not.
    The energy supplied can be given by the secondary_energy_demand attribute or by the method impacts (there is a difference when energy_supply=0)
    '''
    PWh2TJ = 3.6e6
    if secs is None: secs = self.energy_sectors('electricities')
    mix = {}
    if not global_mix:
        mix['total'] = self.secondary_energy_demand[self.index_secs_regs(secs)].sum()
        if method=='impacts': print('Regional mix not coded for "impacts" method')   
        return(self.secondary_energy_demand[self.index_secs_regs(secs)]/mix['total'])
    else:
        if method=='impacts' or method=='impact':
            if global_mix:
                mix['total'] = self.impacts(secs = secs).sum()
                for sec in secs: mix[sec[15:]] = self.impacts(secs = sec).sum()/mix['total']
        elif method=='demand':
            mix['total'] = self.secondary_energy_demand[self.index_secs_regs(secs)].sum()
            for sec in secs: mix[sec[15:]] = self.secondary_energy_demand[self.index_secs_regs(sec)].sum()/mix['total']
        mix['total'] /= PWh2TJ
        return(round(pd.Series(mix), digits))

def aggregate_mix(self, mix = None, secs = None, path_dlr = '/media/adrien/dd/adrien/DD/Économie/Données/Themis/', recompute=False):
    '''
    Returns the aggregate global mix from an array of global mix. Thus, the sum of the original array is 1 and the sum of the output is the number of regions.
    '''
    if not hasattr(self, 'agg_mix') or recompute:
        if secs is None: secs = self.energy_sectors('electricities')
        elec_idx = self.index_secs_regs(secs)
        if mix is None and self.scenario not in ['REF', 'ER', 'ADV', 'combo']: global_mix = self.mix_matrix(method='demand', global_mix = True, digits = 5)
        else:
            if mix is None: mix = self.mix(path_dlr = path_dlr)[self.meta.year]
            global_mix = {}
            for sec in self.labels.idx_sectors[elec_idx].unique():
                global_mix[sec[15:]] = round(mix[np.where(self.labels.idx_sectors[elec_idx]==sec)[0]].sum(), 5)
#             if hasattr(self, 'dlr_elec'): global_mix.append(pd.Series({'total': self.dlr_elec['World'][self.meta.year].sum()/1000}))
            if hasattr(self, 'dlr_elec'): global_mix['total'] = self.dlr_elec['World'][self.meta.year].sum()/1000            
        self.agg_mix = pd.Series(global_mix)
    return(self.agg_mix)

def results(themis, stats=['eroi', 'world_mix'], scenarios=['BL', 'BM', 'ADV'], to_plot = False, not_all_2010=True, rounded=True, fillNA=True, longnames=False,
            dlr_sectors=False, longtotal=True, year = None, extend_wo_GW = False, regional = False): # TODO: re-order index, mix_real, specific region
    '''
    Returns a panda dataframe with results from stats and scenarios specified.
    stats can include: 'eroi', 'eroi_adj', 'eroi_wo_GW', 'eroi_wo_GW_adj', 'world_mix', 'employ', 'employ_direct', 'energy_price'
    scenarios can include: BL, BM, REF, ER, ADV, combo
    not_all_2010 keeps only one scenario for year 2010
    fillNA fills NaN with '–' instead of 0, rounded rounds the figures to max 2 digit, longnames details the scenario name, dlr_sectors removes CCS from sectors,
        longtotal puts 'Total (PWh/a)' instead of 'total' for the last index: all these parameters should be set to False to plot figures
    to_plot = True overrides all previous parameters and set them to False, use this if the results are used to be plotted
    if year is in [2010, 2030, 2050], only the result for the given year are returned
    extend_wo_GW copy/pastes (normal) EROI to the eroi_wo_GW column for scenarios not concerned by the adjustment (BL, BM, combo)
    regional = True overrides other options and provide estimates disaggregated by region rather than sectors
    '''
    if to_plot: not_all_2010, rounded, fillNA, longnames, dlr_sectors, longtotal = False, False, False, False, False, False
    if type(scenarios)==str: scenarios = [scenarios]
    if type(stats)==str: stats = [stats]
    names_stats = {'eroi': 'EROI', 'world_mix': 'mix', 'eroi_adj': 'EROI adj', 'eroi_wo_GW': 'EROI w/o GW', 'eroi_wo_GW_adj': 'EROI w/o GW adj',\
                   'employ': 'k Employ', 'employ_direct': 'k Employ direct', 'energy_price': 'price'}
    stats_names = {'EROI': 'eroi', 'mix': 'world_mix', 'EROI adj': 'eroi_adj', 'EROI w/o GW': 'eroi_wo_GW', 'EROI w/o GW adj': 'eroi_wo_GW_adj',\
                   'k Employ': 'employ', 'k Employ direct': 'employ_direct', 'price': 'energy_price'}
    if dlr_sectors: secs = list(np.array(themis[scenarios[0]][2050].energy_sectors('elecs_names'))\
                                                      [['CCS' not in s for s in themis['BM'][2010].energy_sectors('elecs_names')]])
    else: secs = themis[scenarios[0]][2050].energy_sectors('elecs_names')
    years = [2010, 2030, 2050]
    
    if regional:
        PWh2TJ = 3.6e6
        stats = ['eroi', 'world_mix']
        res = pd.DataFrame(index = list(themis[scenarios[0]][2050].regions)+['total'])
        for s in scenarios:
            secs = themis[s][2010].energy_sectors('electricities')
            for y in years:
                if y in themis[s].keys():
                    if not hasattr(themis[s][y], 'mix_by_region') or not hasattr(themis[s][y], 'eroi_by_region'): 
                        mix_r = {}
                        eroi_r = {}
                        mix_r['total'] = themis[s][y].secondary_energy_demand[themis[s][y].index_secs_regs()].sum()
                        for r in themis[s][y].regions:
                            mix_r[r] = themis[s][y].secondary_energy_demand[themis[s][y].index_secs_regs(regs = r)].sum()/mix_r['total']
                            eroi_r[r] = themis[s][y].eroi_price['eroi'][(r, 'total')]
                        mix_r['total'] /= PWh2TJ
                        if hasattr(themis[s][y], 'eroi'): eroi_r['total'] = themis[s][y].eroi[-1]           
                        themis[s][y].mix_by_region = pd.Series(mix_r)
                        themis[s][y].eroi_by_region = pd.Series(eroi_r)
                    res[(s, y, 'world_mix')] = themis[s][y].mix_by_region
                    res[(s, y, 'eroi')] = themis[s][y].eroi_by_region
        stats = np.unique([c[2] for c in res.columns])
        res = pd.DataFrame(res, columns=pd.MultiIndex.from_product([scenarios, years, stats], names=['scenario', 'year', 'stat']))

    else: 
        stats = [stats_names[s] if s in stats_names.keys() else s for s in stats]
        res = pd.DataFrame(index = secs+['total'])
        for y in years:
            for s in scenarios:
                for stat in stats:
                    if y in themis[s].keys():
                        if stat in ['eroi_wo_GW', 'eroi_wo_GW_adj', 'eroi_GW', 'eroi_GW_adj', 'eroi_TWh', 'eroi_TWh_adj']:
                            if s in ['REF', 'ER', 'ADV']:
                                res[(s, y, 'eroi_wo_GW'+'_adj'*(stat[-4:]=='_adj'))] = getattr(themis[s][y].wo_GW_adj, \
                                                'eroi'+'_adj'*(stat[-4:]=='_adj')).rename(index={'Power sector': 'total', 'total': 'total'}) #loc[secs].fillna(0).
                            else: 
                                if extend_wo_GW: res[(s, y, 'eroi_wo_GW'+'_adj'*(stat[-4:]=='_adj'))] = getattr(themis[s][y], \
                                                'eroi'+'_adj'*(stat[-4:]=='_adj')).rename(index={'Power sector': 'total', 'total': 'total'}) #loc[secs].fillna(0).
                        else:
                            res[(s, y, stat)] = getattr(themis[s][y], stat).rename(index={'Power sector': 'total', 'total': 'total'}) #loc[secs].fillna(0).
                            if stat=='energy_price': 
                                res[(s, y, stat)].at['total'] = res[(s, y, stat)].loc[secs].fillna(0).dot(themis[s][y].world_mix.loc[secs].fillna(0))
                            elif stat in ['employ', 'employ_direct']: res[(s, y, stat)].at['total'] = res[(s, y, stat)].loc[secs].sum()

        stats = np.unique([c[2] for c in res.columns])
        res = pd.DataFrame(res, columns=pd.MultiIndex.from_product([scenarios, years, stats], names=['scenario', 'year', 'stat']))

        res = res.loc[['biomass w CCS', 'biomass&Waste', 'ocean', 'geothermal','solar CSP','solar PV','wind offshore',\
                                       'wind onshore','hydro','nuclear', 'gas w CCS', 'coal w CCS', 'oil', 'gas', 'coal', 'total']]
    if rounded and 'world_mix' in stats: 
        res[[(s, y, 'world_mix') for y in years for s in scenarios]] = round(res[[(s, y, 'world_mix') for y in years for s in scenarios]], 2)
    if rounded and 'employ' in stats: 
        res[[(s, y, 'employ') for y in years for s in scenarios]] = round(res[[(s, y, 'employ') for y in years for s in scenarios]]) # TODO: int or millions
    if rounded and 'employ_direct' in stats: 
        res[[(s, y, 'employ_direct') for y in years for s in scenarios]] = round(res[[(s, y, 'employ_direct') for y in years for s in scenarios]])
    if rounded and 'energy_price' in stats: 
        res[[(s, y, 'energy_price') for y in years for s in scenarios]] = round(res[[(s, y, 'energy_price') for y in years for s in scenarios]], 1)
    if longtotal: res = res.rename(index={'total': 'Total (PWh/a)'})
    if fillNA: res = res.fillna('–')
    long = {'BL': "Baseline ('BL')", 'BM': "Blue Map ('BM', +2°C)", 'REF': "Reference DLR ('REF')", \
                'ER': "Energy [R]evolution ('ER', +2°C, no CCS nor nuclear)", 'ADV': "Advanced ER ('ADV', 100% renewable)", 'combo': 'Combination of scenarios'}
    new_col_names = [long[c] for c in res.columns.levels[0]]
    if not_all_2010: # TODO: rearrange columns so that same scenarios are gathered
        scenarios2010 = ['BL']*('BL' in scenarios) + ['REF']*('REF' in scenarios) + ['combo']*('combo' in scenarios)
        res = res[[(sc, 2010, st) for sc in scenarios2010 for st in stats]+[(s, y, st) for s in scenarios for y in [2030, 2050] for st in stats]]
    if type(year)==int: res = res[[(s, year, st) for s in scenarios for st in stats]]
    if longnames: res.columns.set_levels([long[c] for c in res.columns.levels[0]], level=0, inplace=True)
    res.columns.set_levels([names_stats[s] for s in res.columns.levels[2]], level=2, inplace=True)

    if regional: return((res, themis))
    else: return(res)

def export_all_excel(path_themis, themis):
    book = load_workbook(path_themis + 'all_results.xlsx')
    writer = pd.ExcelWriter(path_themis + 'all_results.xlsx', engine = 'openpyxl')
    writer.book = book
    writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
    res = results(themis, scenarios=['BL', 'BM', 'ADV'], stats=['eroi', 'mix'])
    res.to_excel(writer, 'Main Results BL-BM-ADV EROI,mix')
    res = results(themis, scenarios=['REF', 'ER', 'ADV'], stats=['eroi', 'mix'])
    res.to_excel(writer, 'Greenpeace EROI,mix')
    res = results(themis, scenarios=['BL', 'BM'], stats=['eroi_adj', 'mix'])
    res.to_excel(writer, 'IEA EROI adj,mix')
    res = results(themis, scenarios=['REF', 'ER', 'ADV'], stats=['eroi_adj', 'mix'])
    res.to_excel(writer, 'Greenpeace EROI adj,mix')
    res = results(themis, scenarios=['REF', 'ER', 'ADV'], stats=['eroi_wo_GW', 'mix'])
    res.to_excel(writer, 'Greenpeace wo GW EROI,mix')
    res = results(themis, scenarios=['REF', 'ER', 'ADV'], stats=['eroi_wo_GW_adj', 'mix'])
    res.to_excel(writer, 'Greenpeace wo GW EROI adj,mix')

    for sc in ['BL', 'BM', 'REF', 'ER', 'ADV', 'combo']:
        res = results(themis, scenarios=[sc], stats=['eroi', 'eroi_adj', 'eroi_wo_GW', 'eroi_wo_GW_adj', 'world_mix', 'employ', 'employ_direct', 'energy_price'])
        res.to_excel(writer, sc) # to_latex exists also

    res = results(themis, scenarios=['BL', 'BM', 'REF', 'ER', 'ADV', 'combo'], stats=['employ', 'employ_direct'])
    res.to_excel(writer, 'Employments')
    res = results(themis, scenarios=['BL', 'BM', 'REF', 'ER', 'ADV', 'combo'], stats=['energy_price'])
    res.to_excel(writer, 'prices')
    res = results(themis, scenarios=['BL', 'BM', 'REF', 'ER', 'ADV', 'combo'], stats=['eroi'])
    res.to_excel(writer, 'EROI')
    res = results(themis, scenarios=['BL', 'BM', 'REF', 'ER', 'ADV', 'combo'], stats=['eroi_adj'])
    res.to_excel(writer, 'EROI adj')
    res = results(themis, scenarios=['BL', 'BM', 'REF', 'ER', 'ADV', 'combo'], stats=['eroi_wo_GW'])
    res.to_excel(writer, 'EROI wo GW')
    res = results(themis, scenarios=['BL', 'BM', 'REF', 'ER', 'ADV', 'combo'], stats=['eroi_wo_GW_adj'])
    res.to_excel(writer, 'EROI wo GW adj')
    res = results(themis, scenarios=['BL', 'BM', 'REF', 'ER', 'ADV', 'combo'], stats=['eroi', 'eroi_adj', 'eroi_wo_GW', 'eroi_wo_GW_adj'])
    res.to_excel(writer, 'EROIs')
    res = results(themis, scenarios=['BL', 'BM', 'REF', 'ER', 'ADV', 'combo'], stats=['mix'])
    res.to_excel(writer, 'mix')
    res = results(themis, regional = True)[0]
    res.to_excel(writer, 'By region')
    writer.save()

IOS.aggregate_mix = aggregate_mix
IOS.mix_matrix = mix_matrix
IOS.change_mix = change_mix
IOS.mix = mix
IOS.regional_mix = regional_mix
IOS.prepare_secs_regs = prepare_secs_regs
IOS.index_secs = index_secs
IOS.index_regs = index_regs
IOS.nb_regions = nb_regions
IOS.nb_sectors = nb_sectors
IOS.find = find
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
IOS.err = err
IOS.errs = errs
IOS.erois = erois
IOS.erois_and_prices = erois_and_prices
IOS.energy_sectors = energy_sectors
IOS.regions = regions
IOS.sectors = sectors
IOS.secondary_energy_demand = secondary_energy_demand
IOS.energy_supply = energy_supply
IOS.energy_required = energy_required
IOS.VA = VA
IOS.value_added = value_added
IOS.price_energy = price_energy
IOS.energy_prices = energy_prices
IOS.employment_high = employment_high
IOS.employment_medium = employment_medium
IOS.employment_low = employment_low
IOS.employment_all   = employment_all
IOS.employments = employments
IOS.employment = employment
IOS.results = results
# IOS. = 
# IOS. = 
# other: internal_energy, composition_impact, change IOT for efficiency or gdp, calc_Z, etc., not_regs, regs_or_no, gdp, import, embodied_import