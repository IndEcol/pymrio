# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.7
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Convert MRIO satellite rows

# %% [markdown]
# Here we discuss the possibilities for converting entries in MRIO satellite accounts (Extensions).
# The term *convert* is used very broadly here, it includes the following tasks:
#
# - renaming the index names of results/extensions
# - adjusting the numerical values of the data,
#   e.g. for unit conversion
# - finding and extracting data based on indices across a table or an mrio(-extension).
#   This can be system based on name and potentially constrained by sector/region
#   or any other specification.
# - Aggregation/Summation of satellite accounts
# - Characterization of stressors to impact categories (with low performance, see [the Notebook on stressor characterization](./stressor_characterization.ipynb) for a faster method).
#
# We will cover each of these points in the examples below.
# First [we will go through the general setup](#Basic-setup) describing the structure of the bridging/mapping table.
# We will then cover the application of the [conversion function to a single, standalone table](#Converting-standalone-tables).
# There we will show how to rename the index/stressor names, do [unit conversions](#Unit-conversion),
# and then do [global](#Global-characterization-factors) and [regional](#Regional-specific-characterization-factors) characterizations.
# For the case of converting a full pymrio Extension, see the [converting pymrio extensions](#Converting-pymrio-Extensions) section.
#
# For the connected topics of *Aggregation of MRIOs*
# see the [Aggregation](./aggregation_examples.ipynb) page and for *Characterization of Stressors* see [the Notebook on stressor characterization](./stressor_characterization.ipynb).

# %% [markdown]
# ## Basic setup

# %% [markdown]
# All conversion relies on a *mapping table* that maps (bridges)
# the index/columns of the source data to the indices of the target data.

# %% [markdown]
# This tables requires headers (columns) corresponding to the
# index.names and columns.names of the source data (constraining data)
# as well as bridge data  which specify the new target index.
# The later are indicated by "NewIndex__OldIndex" - **the important part are
# the two underscore in the column name**. Another (optional)
# column named "factor" specifies
# the multiplication factor for the conversion.
# Finally, additional columns can be used to indicate units and other information. However, for the basic conversion this information will not be used. This becomes important later for the [converting Pymrio extensions](#Converting-pymrio-Extensions).

# %% [markdown]
# Constraining data columns can either specify columns or index.
# However, any constraining data to be bridged/mapped to a new name need to be
# in the index of the original data.

# %% [markdown]
# The first example below shows the simplest case of renaming a single table.
# This will make the concept of the mapping table clear.

# %% [markdown]
# ## Converting standalone tables


# %% [markdown]
# ### Renaming the index entries of a single table

# %% [markdown]
# Assume we have a small MRIO result table with the following structure:

# %%
import pandas as pd

import pymrio

ghg_result = pd.DataFrame(
    columns=["Region1", "Region2", "Region3"],
    index=pd.MultiIndex.from_tuples(
        [
            ("Carbon Dioxide", "Air"),
            ("Methane", "air"),
        ]
    ),
    data=[[5, 6, 7], [0.5, 0.6, 0.7]],
)
ghg_result.index.names = ["stressor", "compartment"]
ghg_result.columns.names = ["region"]

# %% [markdown]
# Our first task here is to rename to the chemical names of the stressors
# and fix the compartment spelling.

# %%
ghg_map = pd.DataFrame(
    columns=[
        "stressor",
        "compartment",
        "chem_stressor__stressor",
        "compartment__compartment",
        "factor",
    ],
    data=[
        ["Carbon Dioxide", "[A|a]ir", "CO2", "Air", 1.0],
        ["Methane", "[A|a]ir", "CH4", "Air", 1.0],
    ],
)
ghg_map

# %%
ghg_new = pymrio.convert(ghg_result, ghg_map)
ghg_new

# %% [markdown]
# Explanation: The column headers indicates that the stressor index level
# should be renamed from "stressor" to "chem_stressor" and the compartment index level
# should stay the same (NewName__OldName). The factor column is not used in this case.
# All renaming columns consider regular expressions,
# so that the spelling of the compartment can be fixed in one go.

# %% [markdown]
# For simple rename (and aggregation cases, see below) we can omit the factor column.
# Thus we obtain the same result with the following mapping table:

# %%
ghg_map_wo_factor = pd.DataFrame(
    columns=[
        "stressor",
        "compartment",
        "chem_stressor__stressor",
        "compartment__compartment",
    ],
    data=[
        ["Carbon Dioxide", "[A|a]ir", "CO2", "Air"],
        ["Methane", "[A|a]ir", "CH4", "Air"],
    ],
)
ghg_map_wo_factor

# %%
ghg_new_wo_factor = pymrio.convert(ghg_result, ghg_map_wo_factor)
ghg_new_wo_factor


# %% [markdown]
# ### Unit conversion

# %% [markdown]
# With the factor column it is easy to apply unit conversion to any result table.
# So, to start with the same table as above, we can apply a simple unit conversion.
# Assuming the data is in tonnes

# %%
ghg_result_ton = pd.DataFrame(
    columns=["Region1", "Region2", "Region3"],
    index=pd.MultiIndex.from_tuples(
        [
            ("Carbon Dioxide", "Air"),
            ("Methane", "air"),
        ]
    ),
    data=[[5, 6, 7], [0.5, 0.6, 0.7]],
)
ghg_result_ton.index.names = ["stressor", "compartment"]
ghg_result_ton.columns.names = ["region"]
ghg_result_ton

# %% [markdown]
# We can get the data in kg by

# %%
ghg_map_to_kg = pd.DataFrame(
    columns=[
        "stressor",
        "compartment",
        "chem_stressor__stressor",
        "compartment__compartment",
        "factor",
    ],
    data=[
        ["Carbon Dioxide", "[A|a]ir", "CO2", "Air", 1000],
        ["Methane", "[A|a]ir", "CH4", "Air", 1000],
    ],
)
ghg_map_to_kg

# %%
ghg_new_kg = pymrio.convert(ghg_result_ton, ghg_map_to_kg)
ghg_new_kg

# %% [markdown]
# In case of unit conversion of pymrio satellite accounts,
# we can also check the unit before and set the unit after conversion:
# TODO: unit conversion extensions, link to extension beow


# %% [markdown]
# ### Characterization

# %% [markdown]
# The main power of the convert function is to aggregate and characterize satellite accounts.
# If needed, region and sector specific characterizations can be applied.

# %% [markdown]
# ### Global characterization factors

# %% [markdown]
# An simple example is a conversion/aggregation based on GWP100 characterization factors.
# Here, we continue with the unit converted and cleanup dataframe from above:

# %%
ghg_new_kg


# %% [markdown]
# We define a general purpose characterization map for GHG emissions
# (based on
# [AR6 GWP100 and GWP20 factors](https://www.ipcc.ch/report/ar6/wg1/downloads/report/IPCC_AR6_WGI_Chapter07.pdf)
# ,with some simplifications):

# %%
GWP_characterization = pd.DataFrame(
    columns=["chem_stressor", "GWP__chem_stressor", "factor"],
    data=[
        ["CO2", "GWP100", 1],
        ["CH4", "GWP100", 29],
        ["NHx", "GWP100", 273],
        ["CO2", "GWP20", 1],
        ["CH4", "GWP20", 80],
        ["NHx", "GWP20", 273],
        ["CO2", "GWP500", 1],
        ["CH4", "GWP500", 8],
        ["NHx", "GWP500", 130],
    ],
)
GWP_characterization

# %%
GWP_result = pymrio.convert(ghg_new_kg, GWP_characterization)
GWP_result


# %% [markdown]
# As we can see, GWP_characterization can include factors for stressors not actually
# present in the data.
# These are silently ignored in the conversion process.
# We also did not specify the compartment and assumed the same factors apply
# independent of the compartment (we could pass through the compartment to
# the new result table via passing drop_not_bridge=False to the convert function).

# %%
GWP_result_with_comp = pymrio.convert(
    ghg_new_kg, GWP_characterization, drop_not_bridged_index=False
)
GWP_result_with_comp

# %% [markdown]
# All stressors mapped to the same "impact" are first converted via the
# value given in the factor column
# and then summed up (the aggregation function can be changed
# via the `agg_func` parameter).

# %% [markdown]
# ### Regional specific characterization factors


# %% [markdown]
# A more complex example is the application of regional specific characterization
# factors (the same principle applies to sector specific factors.).
# For that, we assume some land use results for different regions:

# %%
land_use_data = pd.DataFrame(
    columns=["Region1", "Region2", "Region3"],
    index=[
        "Wheat",
        "Maize",
        "Rice",
        "Pasture",
        "Forest extensive",
        "Forest intensive",
    ],
    data=[
        [3, 10, 1],
        [5, 20, 3],
        [0, 12, 34],
        [12, 34, 9],
        [32, 27, 11],
        [43, 17, 24],
    ],
)
land_use_data.index.names = ["stressor"]
land_use_data.columns.names = ["region"]
land_use_data

# %% [markdown]
# Now we setup a pseudo characterization table for converting the land use data into
# biodiversity impacts. We assume, that the characterization factors vary based on
# land use type and region. However, the "region" information is a pure
# constraining column (specifying the region for which the factor applies) without
# any bridge column mapping it to a new name. Thus, the "region" can either be in the index
# or in the columns of the source data - in the given case it is in the columns.

# %%
landuse_characterization = pd.DataFrame(
    columns=["stressor", "BioDiv__stressor", "region", "factor"],
    data=[
        ["Wheat|Maize", "BioImpact", "Region1", 3],
        ["Wheat", "BioImpact", "Region[2,3]", 4],
        ["Maize", "BioImpact", "Region[2,3]", 7],
        ["Rice", "BioImpact", "Region1", 12],
        ["Rice", "BioImpact", "Region2", 12],
        ["Rice", "BioImpact", "Region3", 12],
        ["Pasture", "BioImpact", "Region[1,2,3]", 12],
        ["Forest.*", "BioImpact", "Region1", 2],
        ["Forest.*", "BioImpact", "Region2", 3],
        ["Forest ext.*", "BioImpact", "Region3", 1],
        ["Forest int.*", "BioImpact", "Region3", 3],
    ],
)
landuse_characterization


# %% [markdown]
# The table shows several possibilities to specify factors which apply to several
# regions/stressors.
# All of them are based on the [regular expression](https://docs.python.org/3/howto/regex.html):
#
# - In the first data line we use the "or" operator "|" to specify that the
# same factor applies to Wheat and Maize.
# - On the next line we use the grouping capabilities of regular expressions
# to indicate the same factor for Region 2 and 3.
# - At the last four lines .* matches any number of characters. This
# allows to specify the same factor for both forest types or to abbreviate
# the naming of the stressor (last 2 lines).
#
# The use of regular expression is optional, one can also use one line per factor.
# In the example above, we indicate the factor for Rice in 3 subsequent entries.
# This would be equivalent to ```["Rice", "BioImpact", "Region[1,2,3]", 12]```.


# %% [markdown]
# With that setup we can now characterize the land use data in land_use_result.

# %%
biodiv_characterised = pymrio.convert(land_use_data, landuse_characterization)
biodiv_characterised

# %% [markdown]
# Note, that in this example the region is not in the index
# but in the columns.
# The convert function can handle both cases.
# The only difference is that constraints which are
# in the columns will never be aggregated but keep the column resolution at the
# output. Thus the result is equivalent to

# %%
land_use_data_stacked = land_use_data.stack(level="region")
land_use_data_stacked

# %%
biodiv_characterised_stacked = pymrio.convert(
    land_use_data_stacked, landuse_characterization, drop_not_bridged_index=False
)
biodiv_characterised_stacked.unstack(level="region")[0]

# %% [markdown]
# In this case we have to specify to not drop the not bridged "region" index.
# We then unstack the result again, and have to select the first element ([0]),
# since there where not other columns left after stacking them before the
# characterization.


# %% [markdown]
# TODO: section perhaps needed somewhere?
# Irrespectively of the table or the mrio system, the convert function always follows the same pattern.
# It requires a bridge table, which contains the mapping of the indices of the source data to the indices of the target data.
# This bridge table has to follow a specific format, depending on the table to be converted.

# %% [markdown]
# # Converting pymrio Extensions

# %% [markdown]
# The same principles as for individual tables can be used for converting full pymrio type Extensions (aka satellite accounts).
# In difference to the single tables, pymrio Extensions consist of several pandas DataFrames which can be converted in one go.
# Almost the same bridge table structure as for single tables can be used. The main additional information needed is in regard to
# units. Since pymrio Extensions include a unit dataframe, information about the unit names need to be included.

# %% [markdown]
# Extensions can be converted either one at a time, but the main power of the method lies in collecting stressor data across different extensions
# and converting them in one go.

# %% [markdown]
# We start with a simple example for converting a single extension of a pymrio MRIO system.
# To do so, we load the test MRIO system from pymrio.

# %%
mrio = pymrio.load_test()

# %% [markdown]
# Among others, this system has an extension "emissions" with industry and final demand emissions.


# %%
mrio.emissions.F

# %%
mrio.emissions.F_Y

# %%
mrio.emissions.unit

# %% [markdown]
# We now setup a bridge table for converting/characterizing these emission data
# to several other accounts.

# %%
emis_bridge = pd.DataFrame(
    columns=[
        "stressor",
        "compartment",
        "total__stressor",
        "factor",
        "unit_orig",
        "unit_new",
    ],
    data=[
        ["emis.*", "air|water", "total_sum_tonnes", 1e-3, "kg", "t"],
        ["emission_type[1|2]", ".*", "total_sum", 1, "kg", "kg"],
        ["emission_type1", ".*", "air_emissions", 1e-3, "kg", "t"],
        ["emission_type2", ".*", "water_emissions", 1000, "kg", "g"],
        ["emission_type1", ".*", "char_emissions", 2, "kg", "kg_eq"],
        ["emission_type2", ".*", "char_emissions", 10, "kg", "kg_eq"],
    ],
)
emis_bridge

# %% [markdown]
# This is a fully made up example showing various capabilities of the method.
# In line
#    - 0: find all stressors with emissions (emis.*) in either air or water (air|water) compartment, rename it to "total_sum_tonnes" (total__stressor) by multiplying with a factor 0.0001 which converts the original unit "kg" to tonnes.
#    - 1: find emission_type1 and 2, over all compartments and sum them together without any multiplication
#    - 2: convert emissions of type 1 to air emissions in tons
#    - 3: convert emissions of type 2 to water emissions in g
#    - 4 and 5: two different characterization factors of 2 (type1) and 10 (type2) to convert to kg equivalent (kg_eq) of some kind and then add them together to a summary impact "char_emissions"


# %% [markdown]
# The new extensino can then be calculated with:

# %%
mrio.new_ext = mrio.emissions.convert(emis_bridge, new_extension_name="new_ext")
print(mrio.new_ext)

# %% [markdown]
# And then the new accounts can be calculated with

# %%
mrio.calc_all()
print(mrio.new_ext)
mrio.new_ext.unit

# %%
mrio.new_ext.D_cba


# CONT: test/explain characterization across different extensions

# %%
