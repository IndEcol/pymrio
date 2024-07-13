# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Convert and Characterize MRIO satellite accounts and results

# %% [markdown]
# Here we discuss the possibilities for converting MRIO satellite accounts (Extensions) 
# and results.
# The term *convert* is used very broadly here, it includes the following tasks:
#
# - renaming the index names of results/extensions
# - adjusting the numerical values of the data, 
#   e.g. for unit conversion or characterisation
# - finding and extracting data based on indicies across a table or an mrio(-extension).
#   This can be system based on name and potentially constrained by sector/region 
#   or any other specification.
# - Aggregation/Summation of satellite accounts
# - Characterization of stressors to impact categories
#
# We will cover each of these points in the examples below. 
# We will start with applying the conversion to a single table 
# and then cover the conversion of a full MRIO extension.
#
# For the connected topic of *Aggregation of MRIOs* 
# see the [Aggregation](./aggregation_examples.ipynb) page.

# %% [markdown]
# ## Basic setup

# %% [markdown]
# All conversion relies on a *mapping table* that maps (bridges)
# the indices of the source data to the indices of the target data.

# %% [markdown]
# This tables requires headers (columns) corresponding to the column headers 
# of the source data as well as bridge columns which specify the new target index.
# The later are indicated by "NewIndex__OldIndex" - **the important part are 
# the two underscore in the column name**. Another column named "factor" specifies 
# the multiplication factor for the conversion. 
# Finally, additional columns can be used to indicate units and other information.

# %% [markdown]
# All mapping occurs on the index of the original data. 
# Thus the data to be converted needs to be in long matrix format, at least for the index
# levels which are considered in the conversion.
# TODO: In case conversion happens on MRIO Extensions this conversion happens automatically.

# %% [markdown]
# The first example below shows the simplest case of renaming a single table.
# This will make the concept of the mapping table clear.

# %% [markdown]
# ## Renaming the index of a single table

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
columns=["stressor", "compartment", "chem_stressor__stressor", "compartment__compartment", "factor"],
data=[["Carbon Dioxide", "[A|a]ir", "CO2", "Air", 1.0],
      ["Methane", "[A|a]ir", "CH4", "Air", 1.0]
      ],
)

# %% 
ghg_new = pymrio.convert(ghg_result, ghg_map)

# %% [markdown]
# Explanation: The column headers indicates that the stressor index level
# should be renamed from "stressor" to "chem_stressor" and the compartment index level
# should stay the same (NewName__OldName). The factor column is not used in this case.
# All renaming columns consider regular expressions, 
# so that the spelling of the compartment can be fixed in one go.

# TODO: No factor, implement to do without factor if not given, make test case
# CONT: GHG characterization

# %% [markdown]
# Pymrio allows these convert function either on one specific table (which not necessaryly has to be a table of the mrio system) or on the whole mrio(-extension) system.

# %% [markdown]
# ## Structure of the bridge table


# %% [markdown]
# Irrespectively of the table or the mrio system, the convert function always follows the same pattern.
# It requires a bridge table, which contains the mapping of the indicies of the source data to the indicies of the target data.
# This bridge table has to follow a specific format, depending on the table to be converted.


# %% [markdown]
# Lets assume a table with the following structure (the table to be converted):

# %% [markdown]
# TODO: table from the test cases

# %% [markdown]
# A potential bridge table for this table could look like this:

# %% [markdown]
# TODO: table from the test cases

# %% [markdown]
# Describe the column names, and which entries can be regular expressions

# %% [markdown]
# Once everything is set up, we can continue with the actual conversion.

# %% [markdown]
# ## Converting a single data table


# %% [markdown]
# ## Converting a pymrio extension
