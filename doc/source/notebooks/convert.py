# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.15.2
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Convert and Characterize

# %% [markdown]
# Pymrio contains several possibilities to convert data from one system to another.

# %% [markdown]
# The term *convert* is meant very general here, it contains
#     - finding and extracting data based on indicies across a table or an mrio(-extension) system based on name and potentially constrained by sector/region or any other specification
#     - converting the names of the found indicies
#     - adjusting the numerical values of the data, e.g. for unit conversion or characterisation
#     - aggregating the extracted data, e.g. for the purpose of characterization

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
