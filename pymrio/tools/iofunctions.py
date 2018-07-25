from pymrio.core.mriosystem import IOSystem as IOS
from pymrio.tools.iomath import div0
from pymrio.tools.iomath import sorted_series
from pymrio.tools.iomath import approx_solution
import pandas as pd
import numpy as np
import scipy.sparse as sp 
from scipy.sparse import linalg as spla

# TODO: manage Themis, Cecilia, and futures

## IOSystem METHODS
def energy_sectors(self, notion): # TODO: other sectors, difference from elecs_names to add after elec and to display
    '''
    Returns the list of energy sectors (or names) corresponding to notion, which can be: secondary, secondary_fuels, elec_hydrocarbon, electricities, elecs_names
    '''
    if notion is None: sectors = self.get_sectors()
    elif notion=='elec_hydrocarbon': sectors = ['Electricity by coal', 'Electricity by gas']
    elif notion=='secondary_fuels': sectors = ['Motor Gasoline', 'Gas/Diesel Oil', 'Heavy Fuel Oil', 'Liquefied Petroleum Gases (LPG)', \
         'Naphtha', 'Non-specified Petroleum Products', 'Kerosene', 'Kerosene Type Jet Fuel', 'Petroleum Coke', 'Aviation Gasoline', 'Gasoline Type Jet Fuel']
    elif notion=='electricities': sectors = ['Electricity by ' + s for s in self.energy_sectors('elecs_names')]

    if self.name.lower()=='exiobase' and self.meta.version=='1': 
        if notion=='secondary_fuels': sectors = ['Motor spirit (gasoline)', 'Gas oils', 'Fuel oils n.e.c.', 'Kerosene, including kerosene type jet fuel', \
                                                'Petroleum gases and other gaseous hydrocarbons, except natural gas']
        elif notion=='secondary': sectors = ['Electricity by hydro', 'Electricity nec, including biomass and waste', 'Steam and hot water supply services',
 'Electricity by nuclear', 'Electricity by coal', 'Electricity by gas', 'Motor spirit (gasoline)', 'Gas oils', 'Fuel oils n.e.c.', 'Electricity by wind', 
 'Kerosene, including kerosene type jet fuel', 'Petroleum gases and other gaseous hydrocarbons, except natural gas']
#  ['Coal and lignite; peat (10)', 'Natural gas and services related to natural gas extraction, excluding surveying', 'Nuclear fuel', 'Motor spirit (gasoline)',
#         'Gas oils', 'Fuel oils n.e.c.', 'Kerosene, including kerosene type jet fuel', 'Petroleum gases and other gaseous hydrocarbons, except natural gas']
        elif notion=='elecs_names': sectors = ['wind', 'hydro', 'coal', 'gas', 'nuclear']
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
        elif notion=='elecs_names': sectors = ['wind', 'PV', 'coal', 'oil', 'gas', 'nuclear', 'hydro']
    else: print('Function not yet implemented for this IOSystem')
    return(sectors)

@property
def regions(self): 
    '''
    Returns the list of all regions in the IOSystem
    '''
    return(list(self.get_regions()))

@property
def sectors(self): 
    '''
    Returns the list of all sectors in the IOSystem
    '''
    return(list(self.get_sectors()))

def prepare_secs_regs(self, secs, regs):
    '''
    Prepare the values by default of secs and regs for many methods: all sectors and all regions of the IOSystem.
    '''
    if secs is None: secs = self.sectors
    elif type(secs)==str: secs=[secs]
    if regs is None: regs = self.regions # get_regions() bugs with impacts ... [reg, secs]
    elif type(regs)==str: regs=[regs]
    return((secs, regs))

def index_secs(self, secs, vec_sectors=None):
    '''
    Returns an array of the indexes of secs in vec_sectors.
    
    If secs is a string, returns the indexes of secs in vec_sectors; if secs is a list or array, returns the indexes of any of its elements.
    By default, vec_sectors is the sectors of the IOSystem.
    '''
    if vec_sectors is None: vec_sectors = self.get_sectors()
    if type(secs)==str: return(np.array([i for i,x in enumerate(vec_sectors) if x == secs]))
    else: return(np.array([i for i,x in enumerate(vec_sectors) if x in secs]))
    
def index_regs(self, regs, vec_regions=None):
    '''
    Returns an array of the indexes of secs in vec_regions.
    
    If regs is a string, returns the indexes of regs in vec_regions; if regs is a list or array, returns the indexes of any of its elements.
    By default, vec_regions is the regions of the IOSystem.
    '''
    if vec_regions is None: vec_regions = self.get_regions()
    if type(regs)==str: return(np.array([i for i,x in enumerate(vec_regions) if x == regs]))
    else: return(np.array([i for i,x in enumerate(vec_regions) if x in regs]))
    
# def index_regs_secs(self, regs = None, secs = None, regions = None): # twice faster than index_secs_regs
#     '''
#     Returns an array of the indexes of any element (reg, sec) of regs x secs in the double index of the IOSystem.
#     '''
#     if regs is None: regs = self.get_regions()
#     if secs is None: secs = self.get_sectors()
#     if regions is None: regions = self.get_regions()
#     return(np.repeat(self.index_regs(regs, regions)*self.nb_sectors(), len(secs)*(type(secs)!=str)+(type(secs)==str)) \
#            + np.tile(self.index_secs(secs), len(regs)*(type(regs)!=str)+(type(regs)==str)) )

def nb_regions(self): return(len(self.get_regions())) # TODO: precalculate them with an decorator
def nb_sectors(self): return(len(self.get_sectors()))

def find(self, string, vec='impacts'):
    '''
    Find vec=impacts/sectors containing string.
    '''
    if vec=='impacts' or vec=='Impacts' or vec=='impact': array = np.array(self.impact.unit.iloc[:,0].index)
    elif vec=='sectors' or vec=='sector': array = np.array(self.get_sectors())
    return([x for i,x in enumerate(array) if string in x])

def is_in(self, secs = None, regs = None):
    '''
    Returns a list of booleans, where an element i is True iff it corresponds to a reg in regs and a sec in secs in the double index regions x sectors.
    
    By default, secs is set to all sectors and regs to all regions.
    '''
    secs, regs = self.prepare_secs_regs(secs, regs)
    return([r in regs and s in secs for r in self.get_regions() for s in self.get_sectors()])

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
        return(self.Y[[(reg,dom) for reg in self.get_regions() for dom in pos_y]].sum(axis='columns')*self.is_in(secs, regs))
    else: return(self.Y[[(reg,dom) for reg in self.get_regions() for dom in io.Y.columns.levels[1]]].sum(axis='columns')*self.is_in(secs, regs))
    
def production(self, secs=None, regs=None):
    '''
    Returns the vector of production of (sec, reg) in secs x regs, computed from x.
    '''    
    secs, regs = self.prepare_secs_regs(secs, regs)
    return(self.x*self.is_in(secs, regs))

def impacts(self, var='Total Energy supply', regs=None, secs=None, join_sort=False): # var = 'Value Added'
    '''
    Returns the vector of impact of type var related directly to (sec, reg) in secs x regs, computed from F.
    
    If join_sort is True, sorts the results by decreasing order of impact, grouped by sector.
    By default, secs is set to all sectors and regs to all regions.
    '''
    secs, regs = self.prepare_secs_regs(secs, regs)
    if self.name=='EXIOBASE' and self.meta.version=='1':
        if var=='supply' or var=='Total Energy supply': var = 'Gross Energy Supply - '
        elif var=='use': var = 'Gross Energy Use - '
        impacts = self.materials.F.loc[[s.startswith(var) for s in self.materials.F.index]][[(r,s) for r in regs for s in secs]].sum()
    else: impacts = self.impact.F.loc[var].loc[regs,secs]
    if join_sort: return(sorted_series(impacts.groupby('sector').sum()))
    else: return(impacts)
    
def embodied_prod(self, secs=None, regs=None, prod = None):
    '''
    Returns the vector of embodied production for (sec, reg) in secs x regs, i.e. all the production required to produce their production, including them.
    
    When the Leontief inverse is not known, computes an approximate solution from the technology matrix A.
    If the production is pre-calculated, it can be passed as an argument.
    '''
    secs, regs = self.prepare_secs_regs(secs, regs)
    if prod is None: prod = self.production(secs, regs)
    if self.L is None: return(spla.cgs(sp.eye(self.A.shape[0])-self.A, prod, approx_solution(self.A,prod).transpose().toarray()[0], tol=1e-7))
    else: return(np.dot(self.L, prod))

def embodied_impact(self, secs=None, regs=None, var='Total Energy supply', source='secondary', group_by='region', sort=False): # TODO: source = None
    '''
    Returns a vector of impact of type var embodied in the production of (sec, reg) in secs x regs, excluding their own production.
    '''
    secs, regs = self.prepare_secs_regs(secs, regs)
    source = self.energy_sectors(source)
    production = self.production(secs, regs)
    share_demand = div0(self.embodied_prod(secs, regs, production)-production, self.x)
    impacts = self.impacts(var)*share_demand
    impacts = impacts[self.index_secs_regs(source)]
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
    
    Returns a tuple of ([impacts], value of inputs, sums of all [impacts] and values for each step (not only the first nb_main which are shown))
    '''
    secs, regs = self.prepare_secs_regs(secs, regs)
    if nb_main=='all': nb_main==self.nb_sectors()*self.nb_regions()
    if source=='all': source = self.get_sectors()
    elif source=='secondary': source = self.get_sectors('secondary')
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
            impacts[l][i] = impacts_l_i[self.index_secs_regs(source, self.get_regions())]
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
    if out_sectors is None: out_sectors = self.get_sectors()
    production = self.x.iloc[index_secs_regs(secs, self.get_regions())].sum()
    return((self.y.iloc[index_secs_regs(secs, self.get_regions())].sum()/production, \
            sorted_series(self.Z.iloc[index_secs_regs(secs, self.get_regions())].sum().groupby('sector').sum()[out_sectors]/production)[0:nb_main]))

def eroi(self, secs, regs=None, var='Total Energy supply', source='secondary', netting_fuel = True):
    '''
    Returns the EROI (Net External Energy Ratio) of sectors secs in regs, considering the energy from source with notion var.
    
    The formula is: 
    energy supplied / (energy embodied in production (excluding supplied) - fuels as direct inputs for electricity from hydrocarbon (if netting_fuel is True))
    '''
    if netting_fuel and ((type(secs)==str and secs in self.energy_sectors('elec_hydrocarbon')) or secs==self.energy_sectors('elec_hydrocarbon')): input_fuel=True
    else: input_fuel = 0 # We want to include fuels that are used for transportation, not transformed into electricity (this is not secondary anymore)
    secs, regs = self.prepare_secs_regs(secs, regs)
    supply = self.impacts(var, regs, secs).sum()
    embodied = self.embodied_impact(secs, regs, var, source).sum()
    if input_fuel: input_fuel = self.inputs(secs, var_impacts=[var], source=self.energy_sectors('secondary_fuels'), order_recursion=2)[2][0][1]         
    return(round(supply/(embodied - input_fuel),1))
#     y = production(secs)
#     supply = energy_supply.dot(y).sum() # energy_supply * production 
#     embodied = (secondary_energy_supply.dot(embodied_prod(secs, futur, y=y)[0] - y)).sum() 
#         input_oil = (secondary_oil_supply.dot(A.dot(y))).sum()

def erois(self, secs = None, var='Total Energy supply', source='secondary', display=True):
    '''
    Returns the list of EROIs of the list of sectors secs, considering the energy from source with notion var.
    '''
    if secs is None: secs = self.energy_sectors('electricities')
    erois = []
    if display: 
        print('EROI with '+var+' from '+source+' sources at the denominator, unadjusted for growth')
    for i, sec in enumerate(secs): 
        eroi_sec = self.eroi(sec, self.get_regions(), var, source)
        erois.append(eroi_sec)
        if display: print(self.energy_sectors('elecs_names')[i], eroi_sec)
    return(erois)

## DECLARATION OF METHODS
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
IOS.eroi = eroi
IOS.erois = erois
IOS.energy_sectors = energy_sectors
IOS.regions = regions
IOS.sectors = sectors