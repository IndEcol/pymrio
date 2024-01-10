# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.15.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Exploring MRIOs with Pymrio

# %% [markdown]
# The first step when working with a new MRIO data set is to familiarize yourself with the data. 
# This notebook shows how to use the `pymrio` package to explore the data. 
# We use the test data set that is included in the `pymrio` package. 
# This is a completely artificial, very small MRIO. 
# It is not meant to be realistic, but it is useful for developing, testing and learning.


# %% [markdown]
# First we import the required packages:

# %%
import pymrio

# %% [markdown]
# We can now load the test data set with the `load_test` function. We can call 
# the MRIO whatever we want, here we use mrio.

# %%
mrio = pymrio.load_test()

# %% [markdown]
# We can get some first information about the MRIO by printing it.

# %%
print(mrio)

# %% [markdown]
# This tells us what the MRIO data we just loaded contains.
# We find a Z and Y matrix, some unit information and two satellite accounts, factor_inputs and emissions.

# %% [markdown]
# To get more specific data we can ask pymrio for regions, sectors, products, etc.

# %%
mrio.name

# %%
mrio.get_regions()

# %%
mrio.get_sectors()

# %%
mrio.get_Y_categories()

# %% [markdown]
# The same methods can be used to explore one of the satellite accounts.

# %%
print(mrio.emissions)

# %%
mrio.emissions.name
# %%
mrio.emissions.get_regions()








