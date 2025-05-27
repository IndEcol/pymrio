# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Advanced functionality - pandas groupby with pymrio satellite accounts

# %% [markdown]
# This notebook examplifies how to directly apply [Pandas](https://pandas.pydata.org/) core functions (in this case [groupby and aggregation](https://pandas.pydata.org/pandas-docs/stable/groupby.html)) to the pymrio system.

# %% [markdown]
# ## WIOD material extension aggregation - stressor w/o compartment info

# %% [markdown]
# Here we use the WIOD MRIO system (see the notebook ["Automatic downloading of MRIO databases"](autodownload.ipynb#WIOD-download) for how to automatically retrieve this database) and will aggregate the WIOD material stressor for used and unused materials.  We assume, that the WIOD system is available at

# %%
wiod_folder = "/tmp/mrios/WIOD2013"

# %% [markdown]
# To get started we import pymrio

# %%
import pymrio

# %% [markdown]
# For the example here, we use the data from 2009:

# %%
wiod09 = pymrio.parse_wiod(path=wiod_folder, year=2009)

# %% [markdown]
# WIOD includes multiple material accounts, specified for the "Used" and "Unused" category, as well as information on the total. We will use the latter to confirm our calculations:

# %%
wiod09.mat.F

# %% [markdown]
# To aggregate these with the Pandas groupby function, we need to specify the groups which should be grouped by Pandas.
# Pymrio contains a helper function which builds such a matching dictionary.
# The matching can also include regular expressions to simplify the build:

# %%
groups = wiod09.mat.get_index(
    as_dict=True,
    grouping_pattern={".*_Used": "Material Used", ".*_Unused": "Material Unused"},
)
groups

# %% [markdown]
# Note, that the grouping contains the rows which do not match any of the specified groups.
# This allows to easily aggregates only parts of a specific stressor set. To actually omit these groups
# include them in the matching pattern and provide None as value.
#
# To have the aggregated data alongside the original data, we first copy the detailed satellite account:

# %%
wiod09.mat_agg = wiod09.mat.copy(new_name="Aggregated matrial accounts")

# %% [markdown]
# Then, we use the pymrio get_DataFrame iterator together with the pandas groupby and sum functions to aggregate the stressors.
# For the dataframe containing the unit information, we pass a custom function which concatenate non-unique unit strings.

# %%
for df_name, df in zip(
    wiod09.mat_agg.get_DataFrame(data=False, with_unit=True, with_population=False),
    wiod09.mat_agg.get_DataFrame(data=True, with_unit=True, with_population=False),
):
    if df_name == "unit":
        wiod09.mat_agg.__dict__[df_name] = df.groupby(groups).apply(
            lambda x: " & ".join(x.unit.unique())
        )
    else:
        wiod09.mat_agg.__dict__[df_name] = df.groupby(groups).sum()

# %%
wiod09.mat_agg.F

# %%
wiod09.mat_agg.unit

# %% [markdown]
# ## Use with stressors including compartment information:

# %% [markdown]
# The same regular expression grouping can be used to aggregate stressor data which is given per compartment.
# To do so, the matching dict needs to consist of tuples corresponding to a valid index value in the DataFrames.
# Each position in the tuple is interprested as a regular expression.
# Using the get_index method gives a good indication how a valid grouping dict should look like:

# %%
tt = pymrio.load_test()
tt.emissions.get_index(as_dict=True)

# %% [markdown]
# With that information, we can now build our own grouping dict, e.g.:

# %%
agg_groups = {("emis.*", ".*"): "all emissions"}

# %%
group_dict = tt.emissions.get_index(as_dict=True, grouping_pattern=agg_groups)
group_dict

# %% [markdown]
# Which can then be used to aggregate the satellite account:

# %%
for df_name, df in zip(
    tt.emissions.get_DataFrame(data=False, with_unit=True, with_population=False),
    tt.emissions.get_DataFrame(data=True, with_unit=True, with_population=False),
):
    if df_name == "unit":
        tt.emissions.__dict__[df_name] = df.groupby(group_dict).apply(
            lambda x: " & ".join(x.unit.unique())
        )
    else:
        tt.emissions.__dict__[df_name] = df.groupby(group_dict).sum()

# %% [markdown]
# In this case we loose the information on the compartment. To reset the index do:

# %%
import pandas as pd

tt.emissions.set_index(pd.Index(tt.emissions.get_index(), name="stressor"))

# %%
tt.emissions.F
