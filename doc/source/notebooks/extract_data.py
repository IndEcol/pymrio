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

# %% [markdown]
# ## Extract data from a time series of MRIOs

# %% [markdown]
# The `extract_from_mrioseries` function allows you to extract specific data from multiple MRIO systems stored in different directories or files. This is particularly useful when working with time series data where you have MRIO systems for different years.

# %% [markdown]
# ### Basic usage
# 
# The function takes several parameters:
# - `mrios`: List of paths to MRIO systems (directories or files)
# - `key_naming`: How to name the keys in the returned dictionary
# - `extension`: Which extension to extract from (or None for core system data)
# - `account`: Which account/matrix to extract (e.g., "D_cba", "Z", "Y")
# - `index`: Which rows to extract (pandas index or slice)
# - `columns`: Which columns to extract (pandas columns or slice)

# %% [markdown]
# Let's create some example MRIO systems with different years to demonstrate:

# %%
import tempfile
import os
import pymrio

# Create temporary directories for different years
with tempfile.TemporaryDirectory() as tmpdir:
    # Create test MRIO systems
    mrio_1999 = pymrio.load_test().calc_all()
    mrio_2000 = mrio_1999.copy()
    
    # Modify the 2000 system to show differences
    mrio_2000.Z = mrio_2000.Z * 2
    mrio_2000.Y = mrio_2000.Y * 2
    
    # Save to different directories
    dir_1999 = os.path.join(tmpdir, "test_1999")
    dir_2000 = os.path.join(tmpdir, "test_2000")
    
    mrio_1999.save_all(dir_1999)
    mrio_2000.save_all(dir_2000)
    
    # Extract emission data using year-based naming
    result = pymrio.extract_from_mrioseries(
        mrios=[dir_1999, dir_2000],
        key_naming="year",
        extension="emissions",
        account="D_cba",
        index=None,
        columns=["reg1"]
    )
    
    print("Available years:", list(result.keys()))
    print("1999 data shape:", result["1999"].shape)
    print("2000 data shape:", result["2000"].shape)

# %% [markdown]
# ### Key naming options
# 
# The `key_naming` parameter controls how the dictionary keys are generated:
# - `None`: Uses the folder/file name as key
# - `"year"`: Searches for 4-digit years in the folder/file name
# - Custom function: Pass a function that takes the folder name and returns a key

# %%
# Example with custom key naming
def custom_naming(folder_name):
    return f"dataset_{folder_name}"

with tempfile.TemporaryDirectory() as tmpdir:
    mrio_test = pymrio.load_test().calc_all()
    
    # Save to a test directory
    test_dir = os.path.join(tmpdir, "mrio_data")
    mrio_test.save_all(test_dir)
    
    # Extract with custom naming
    result = pymrio.extract_from_mrioseries(
        mrios=[test_dir],
        key_naming=custom_naming,
        extension="emissions",
        account="D_cba",
        index=("emission_type1", "air"),
        columns=["reg1"]
    )
    
    print("Custom key:", list(result.keys())[0])

# %% [markdown]
# ### Extracting core system data
# 
# You can extract data from the core MRIO system (Z, Y, x matrices) by setting `extension=None`:

# %%
with tempfile.TemporaryDirectory() as tmpdir:
    mrio_test = pymrio.load_test().calc_all()
    test_dir = os.path.join(tmpdir, "mrio_core")
    mrio_test.save_all(test_dir)
    
    # Extract Z matrix from core system
    z_result = pymrio.extract_from_mrioseries(
        mrios=[test_dir],
        key_naming=None,
        extension=None,  # Extract from core system
        account="Z",
        index=None,
        columns=None
    )
    
    print("Core system Z matrix shape:", z_result["mrio_core"].shape)

# %% [markdown]
# ### Working with ZIP files
# 
# The function also supports extracting data from ZIP files containing MRIO systems:

# %%
import zipfile

with tempfile.TemporaryDirectory() as tmpdir:
    # Create and save MRIO system
    mrio_test = pymrio.load_test().calc_all()
    mrio_dir = os.path.join(tmpdir, "mrio_temp")
    mrio_test.save_all(mrio_dir)
    
    # Create ZIP file
    zip_path = os.path.join(tmpdir, "mrio_2023.zip")
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for root, dirs, files in os.walk(mrio_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, mrio_dir)
                zf.write(file_path, arc_path)
    
    # Extract from ZIP file
    zip_result = pymrio.extract_from_mrioseries(
        mrios=[zip_path],
        key_naming="year",
        extension="emissions",
        account="D_cba",
        index=None,
        columns=["reg1"]
    )
    
    print("Extracted from ZIP:", list(zip_result.keys()))

# %% [markdown]
# ### Index and column selection
# 
# You can specify exactly which rows and columns to extract using pandas indexing:

# %%
with tempfile.TemporaryDirectory() as tmpdir:
    mrio_test = pymrio.load_test().calc_all()
    test_dir = os.path.join(tmpdir, "mrio_subset")
    mrio_test.save_all(test_dir)
    
    # Extract specific emission type and regions
    subset_result = pymrio.extract_from_mrioseries(
        mrios=[test_dir],
        key_naming=None,
        extension="emissions",
        account="D_cba",
        index=("emission_type1", "air"),  # Specific emission type
        columns=["reg1", "reg2"]  # Specific regions
    )
    
    print("Subset result shape:", subset_result["mrio_subset"].shape)
    print("Result type:", type(subset_result["mrio_subset"]))

# %% [markdown]
# The `extract_from_mrioseries` function returns an OrderedDict where keys are determined by the `key_naming` parameter and values are pandas DataFrames (or Series if a single row is selected) containing the extracted data.

# %%
