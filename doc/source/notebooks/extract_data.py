# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.2
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
#
# ## Extracting data across extension tables

# %% [markdown]
# Pymrio includes methods for bulk extraction of data across extension tables. These can either work on a specific extension or across all extensions of the system.

# %% [markdown]
# ### Extracting from a specific extension


# %% [markdown]
# Here we use use the `extract` method available in the extension object.
# This expect a list of rows (index) to extract.
# Here we extract some rows from the emission extension table.
# To do so, we first define the rows (index) to extract:

# %%
rows_to_extract = [("emission_type1", "air"), ("emission_type2", "water")]

# %% [markdown]
# We can now use the `extract` method to extract the data, either as a pandas DataFrame

# %%
df_extract = mrio.emissions.extract(rows_to_extract, return_type="dataframe")
df_extract.keys()

# %% [markdown]
# Or we extract into a new extension object:

# %%
ext_extract = mrio.emissions.extract(rows_to_extract, return_type="extension")
str(ext_extract)

# %% [markdown]
# Note that the name of the extension object is now `Emissions_extracted`, based on the name of the original extension object.
# To use another name, just pass the name as the `return_type` method.

# %%
new_extension = mrio.emissions.extract(rows_to_extract, return_type="new_extension")
str(new_extension)

# %% [markdown]
# Extracting to dataframes is also a convienient
# way to convert an extension object to a dictionary:

# %%
df_all = mrio.emissions.extract(mrio.emissions.get_rows(), return_type="dfs")
df_all.keys()


# The method also allows to only extract some of the accounts:
df_some = mrio.emissions.extract(
    mrio.emissions.get_rows(), dataframes=["D_cba", "D_pba"], return_type="dfs"
)
df_some.keys()


# %% [markdown]
# ### Extracting from all extensions

# %% [markdown]
# We can also extract data from all extensions at once.
# This is done using the `extension_extract` method from the pymrio object.
# This expect a dict with keys based on the extension names and values as a list of rows (index) to extract.

# %% [markdown]
# Lets assume we want to extract value added and all emissions.
# We first define the rows (index) to extract:

# %%
to_extract = {
    "Factor Inputs": "Value Added",
    "Emissions": [("emission_type1", "air"), ("emission_type2", "water")],
}


# %% [markdown]
# And can then use the `extension_extract` method to extract the data, either as a pandas DataFrame,
# which returns a dictionary with the extension names as keys

# %%
df_extract_all = mrio.extension_extract(to_extract, return_type="dataframe")
df_extract_all.keys()

# %%
df_extract_all["Factor Inputs"].keys()

# %% [markdown]
# We can also extract into a dictionary of extension objects:

# %%
ext_extract_all = mrio.extension_extract(to_extract, return_type="extensions")
ext_extract_all.keys()

# %%
str(ext_extract_all["Factor Inputs"])

# %% [markdown]
# Or merge the extracted data into a new pymrio Extension object (when passing a new name as return_type):

# %%
ext_new = mrio.extension_extract(to_extract, return_type="new_merged_extension")
str(ext_new)

# %% [markdown]
# CONT: Continue with explaining, mention the work with find_all etc

# %% [markdown]
# ### Search and extract

# %% [markdown]
# The extract methods can also be used in combination with the [search/explore](./explore.ipynb) methods of pymrio.
# This allows to search for specific rows and then extract the data.

# %% [markdown]
# For example, to extract all emissions from the air compartment we can use:

# %%
match_air = mrio.extension_match(find_all="air")

# %% [markdown]
# And then make a new extension object with the extracted data:

# %%
air_emissions = mrio.emissions.extract(match_air, return_type="extracted_air_emissions")
print(air_emissions)

# %% [markdown]
# For more information on the search methods see the [explore notebook](./explore.ipynb).
