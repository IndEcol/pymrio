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
# # Extract data from Pymrio

# %% [markdown]
# This notebook shows how to extract specific data from the pymrio object for further processing in Python. For exporting/saving the data to another file format see [the notebook on saving/loading/exporting data.](./load_save_export.ipynb)

# %%
import pymrio

# %%
mrio = pymrio.load_test().calc_all()

### Basic pandas indexing of pymrio tables

# %% [markdown]
# Since pymrio is built on top of pandas, we can use the pandas functions to extract data from the pymrio object. For example, to access the part of the A matrix from the region 2 we can use:

# %%
A_reg2 = mrio.A.loc["reg2", "reg2"]
A_reg2

# %% [markdown]
# Most tables are indexed via a multiindex, in case of the A matrix the index is a tuple of the region and the sector.
# To access all technical coefficients (column) data for mining from all regions we can use:


# %%
A_mining = mrio.A.loc[:, (slice(None), "mining")]
A_mining

# %% [markdown]
# For further information on the pandas multiindex see the [pandas documentation on advanced indexing.](https://pandas.pydata.org/docs/user_guide/advanced.html)

### Extracting data across extension tables

# %% [markdown]
# Pymrio includes methods for bulk extraction of data across extension tables. These can either work on a specific extension or across all extensions of the system.

# %% [markdown]
#### Extracting from a specific extension


# %% [markdown]
# Here we use use the `extract` method available in the extension object.
# This expect a list of rows (index) to extract.

row = mrio.emissions.get_rows()

df_extract = mrio.emissions.extract(row, return_type="dataframe")
ext_extract = mrio.emissions.extract(row, return_type="extension")

# CONT: DESRIBE STUFF ABOVE
# For example, to extract the total value added for all regions and sectors we can use:
