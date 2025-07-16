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
# # Pymrio Tutorial
#
# A complete tutorial covering all top-level functions of pymrio, using the test MRIO system.
#
#

# %% [markdown]
# ## Setup and Installation
#
# Before starting this tutorial, make sure you've got pymrio installed. You can grab it from conda-forge or PyPi.
# Use pip, mamba, conda, or whatever package manager you prefer to get it sorted. For example


# %% [markdown]
# ## Getting Started with Test MRIO Data
#
# We begin by importing pymrio and loading the test MRIO system. This small test system contains six regions and eight sectors, making it ideal for learning purposes.
#
# Note that any other MRIO database can be used with the same functions demonstrated here.
# The test system serves only as a representative example for larger, real-world datasets. See the other notebooks on MRIO downloading and handling (for example for [EXIOBASE](working_with_exiobase.ipynb)) for more details.


# %%
import pymrio

# Load the test MRIO system
test_mrio = pymrio.load_test()

# Display basic information about the system
print(test_mrio)
print("Type of object:", type(test_mrio))
print("Available extensions:", test_mrio.extensions)

# Get regions and sectors
print("Regions:", test_mrio.regions)
print("Sectors:", test_mrio.sectors)
print("Final demand categories:", test_mrio.Y_categories)
print("Extensions:", test_mrio.extensions)
print("Rows in emissions extension:", test_mrio.emissions.rows)

# %% [markdown]
# ### Search Functionality
#
# Pymrio offers comprehensive search capabilities to find specific accounts, regions, sectors, stressors, and impacts:
# The terms are the same as the pandas regex method names and work in the same way.
# For more details, check out the [explore notebook](explore.ipynb) and the [pandas regex documentation](https://pandas.pydata.org/pandas-docs/stable/user_guide/text.html#working-with-regular-expressions).

# %%
# Search for specific terms across the system
search_results = test_mrio.find("food")
print("Search results for 'food':", search_results)

# %%
# More specific search methods
contains_results = test_mrio.contains("electricity")
print("Contains 'electricity':", contains_results)

# %%
# Search within extensions
extension_search = test_mrio.extension_contains("emission")
print("Extension search for 'emission':", extension_search)

# Full match search
match_results = test_mrio.match("reg1")
print("Full match for 'reg1':", match_results)

# %% [markdown]
# **Tip**: Use the find method to get a quick overview where you find a specific term, in particular for mrio systems with multiple extensions.
# For example, the following finds "air" in the compartment information of one extension.

# %%
print("Search for occurance of >air< in the whole system:", test_mrio.find("air"))


# %% [markdown]
# ## Core Calculations with calc_all
#
# The `calc_all` method is fundamental to pymrio analysis. It automatically identifies missing tables and calculates all necessary accounts:


# %% [markdown]
# Before the calculation, we have the following accounts available in the test MRIO system:

# %%
print("Before calc_all:")
print(test_mrio.DataFrames)
print(test_mrio.emissions.DataFrames)

# %% [markdown]
# Calculate all missing parts

# %%
test_mrio.calc_all()

# %% [markdown]
# After calculation, these accounts are available

# %%
print("After calc_all:")
print(test_mrio.DataFrames)

# %% [markdown]
# And we now also have several classical EE-MRIO results available:

# %%
print("\nEmissions accounts:")
print(test_mrio.emissions.DataFrames)

# %% [markdown]
# For example

# %%
print("D_cba (consumption-based):", test_mrio.emissions.D_cba)

# %% [markdown]
# ## Ghosh Calculations in calc_all
#
# When `calc_all` is executed, it can optionally calculate Ghosh inverse matrices for downstream analysis:

# %%
test_mrio.calc_all(include_ghosh=True)
print(test_mrio)

# %% [markdown]
# This also calculates downstream multipliers M_down

# %%
test_mrio.emissions.M_down

# %% [markdown]
# See the [math section](../math.rst) of the documentation for further details on the Ghosh calculations.


# %% [markdown]
# ## Search and Extract Functionality

# %% [markdown]
# ### Extracting Specific Accounts

# %% [markdown]
# We can also extract consumption-based accounts for a specific stressor

# %%
cba_emission1 = test_mrio.emissions.D_cba.loc[["emission_type1"]]
print("CBA emissions by region for emission_type1:")
print(cba_emission1)

# %% [markdown]
# And extract data for specific regions:

# %%
reg1_data = test_mrio.emissions.D_cba_reg[["reg1", "reg3"]]
print("\nTotal CBA emissions for the selected regions:")
print(reg1_data)

# %% [markdown]
# Besides the direct access to the DataFrames explained above, one can also
# extract data into dictionaries for alternative access.:

# %%
emission_type1_data = test_mrio.emissions.get_row_data("emission_type1")


# %% [markdown]
# This extracts all data available for >emission_type1<

# %%
emission_type1_data.keys()


# %% [markdown]
# ### Advanced Search Patterns
#
# Use regular expressions for more complex searches:

# %%
emis_search = test_mrio.find("emission.*")
print("Emission... occurances:", emis_search)

all_extension_search = test_mrio.extension_contains("typ+")
print("Extensions containing 'type':", all_extension_search)


# %% [markdown]
# ## Using Functions from iomath
#
# Pymrio's `iomath` module provides low-level functions for specific calculations:
#
# import numpy as np

# %%
from pymrio.tools import iomath

# Calculate specific matrices manually
A_manual = iomath.calc_A(test_mrio.Z, test_mrio.x)
print("Manual A matrix calculation matches:", np.allclose(A_manual, test_mrio.A))

# Calculate Leontief matrix
L_manual = iomath.calc_L(test_mrio.A)
print("Manual L matrix calculation matches:", np.allclose(L_manual, test_mrio.L))

# Calculate multipliers
S = test_mrio.emissions.S
M_manual = iomath.calc_M(S, test_mrio.L)
print(
    "Manual multiplier calculation matches:",
    np.allclose(M_manual, test_mrio.emissions.M),
)

# %% [markdown]
# ## Gross Trade Analysis
#
# The `calc_gross_trade` function provides insights into bilateral trade flows:

# %%
gross_trade = test_mrio.get_gross_trade()

# %% [markdown]
# This give the total trade flows from one region/sectors to other regions

# %%
gross_trade.bilat_flows.head()


# %% [markdown]
# As well as the totals for each region

# %%
gross_trade.totals.head()

# %% [markdown]
# ## Extension Methods: Concatenate, Convert, and Characterize

# %% [markdown]
# ### Extension Concatenation
#
# The `extension_concate` method allows combining multiple extensions.

# %%
# Create a copy for demonstration
ext_emis2 = test_mrio.emissions.copy()
# Combine two extensions with same index structure
new_ext = pymrio.extension_concate(
    test_mrio.emissions, ext_emis2, new_extension_name="emissions_combined"
)
new_ext.rows

# %% [markdown]
# Combining extensions with different indicies results in a new index called >indicator<. Any indicies not avaialable in one of the extensions is set to NaN.

# %%
all_ext = pymrio.extension_concate(
    test_mrio.emissions, test_mrio.factor_inputs, new_extension_name="All"
)
print(all_ext)
all_ext.rows

# %% [markdown]
# In any case, the extension can be attached to the mrio object and used alongside the others.

# %%
test_mrio.all_ext = all_ext
print(test_mrio.extensions)
print(test_mrio.extensions_instance_names)

# %% [markdown]
# ### Extension Conversion
#
# The `convert` and and `extension_convert` methods transforms extensions based on mapping functions:

# %%
import pandas as pd

conversion_factors = pd.DataFrame(
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

# %% [markdown]
# Importantly, the columns names >stressor< and >compartment< match the index names of the extension to be converted.
# Bridge columns are columns with '__' in the name. They defined a new name >impact< and how it is based on a previous column name.
# The column >Factor< is the conversion factor, and the last 2 columns define new colums and check the orignal ones.

# %%
new_emis = test_mrio.emissions.convert(
    conversion_factors, new_extension_name="converted_emissions"
)
new_emis.F

# %% [markdown]
# **Tip**: Due to the regular expression capabilities this function
# is quite powerful but also rather slow.
# Use is before doing the full analysis, and use the characterization function
# for "standard" characterization tasks (see below).
#

# %% [markdown]
# ### Characterization of stressors
#
# Pymrio uses an innovative string-matching approach to characterize stressors.
# This method matches stressors in the characterization table (in long format)
# with those in the MRIO system, ensuring consistent stressor mapping,
# automatic unit verification, and flexibility regardless of entry order. It
# also handles characterization factors for stressors not present in the
# satellite account, efficiently manages region- and sector-specific factors,
# and supports characterization across different extensions.
#
# Unlike traditional matrix multiplication methods, which require strict 1:1
# correspondence and precise ordering, this approach is more flexible.
# Characterization can be performed using either an extension object method or
# a top-level function that accepts MRIO objects or extension collections.
#
# To start, we need to first define a characterization factors table.

# %%
char_factors = pd.DataFrame(
    {
        "stressor": ["emission_type1", "emission_type2", "emission_type3"],
        "compartment": ["air", "water", "land"],
        "impact": ["climate_change", "acidification", "eutrophication"],
        "factor": [25.0, 1.5, 0.8],  # kg CO2-eq, SO2-eq, PO4-eq
        "impact_unit": ["kg CO2-eq", "kg SO2-eq", "kg PO4-eq"],
        "stressor_unit": ["kg", "kg", "kg"],
    }
)

# %% [markdown]
# This can be used to characterize the emissions extension of the test MRIO system.

# %%
characterization_result = test_mrio.emissions.characterize(
    factors=char_factors,
    characterized_name_column="impact",
    characterization_factors_column="factor",
    characterized_unit_column="impact_unit",
    orig_unit_column="stressor_unit",
)

# %% [markdown]
# The result contains a validation table, informing about the missing stressor.
#

# %%
characterization_result.validation

# %% [markdown]
# **TIP**: Alway verify and check via the validation table.
# It is also returned in cases when the characterization can not be performed (e.g. due to unit errors).

# %% [markdown]
# The characterized is available as the second attribute of the result:

# %%
characterization_result.extension

# %%
characterization_result.extension.F

# %% [markdown]
# For more details on region-specific characterization and characterization
# across multiple extensions, see the notebook stressor_characterization.

# %% [markdown]
# ## Parsing, saving and loading MRIOs


# %% [markdown]
# ### Parsing MRIOs
#
# Pymrio supports any symmetric MRIO table and provides automatic downloading and parsing for several common datasets.
# For details, see the sections "Automatic MRIO download" and "Handling MRIO data".


# %% [markdown]
# ### Saving processed MRIOs
# You can save your MRIO after you've parsed and analysed it. Pymrio lets you
# save in text, pickle or parquet formats. Parquet works well if your dataset is on the
# larger side.
#
#
#
# import os

# %%
import tempfile
from pathlib import Path

# Create temporary directory for demonstration
temp_dir = Path(tempfile.mkdtemp())


# %% [markdown]
# The difference for into the supported formats it given by the argument to the >save_all< method

# %%
# Save to text format
txt_path = temp_dir / "test_mrio_txt"
test_mrio.save_all(txt_path, table_format="txt")
list(txt_path.glob("**/*"))


# %%
# Save to parquet format
parquet_path = temp_dir / "test_mrio_parquet"
test_mrio.save_all(parquet_path, table_format="parquet")
list(parquet_path.glob("**/*"))


# %% [markdown]
# In both cases, each DataFrame (account) is stored as separate file,
# with satellite accounts a subfolders. The file >file_paramters.json<
# stores the definition of index/columns such that files can be read
# back in correctly.

# %%
mrio_reload_txt = pymrio.load_all(txt_path)
mrio_reload_parquet = pymrio.load_all(parquet_path)
print(test_mrio)
print(mrio_reload_txt)
print(mrio_reload_parquet)

# %% [markdown]
# Clean up temporary directory

# %%
import shutil

shutil.rmtree(temp_dir)
print("Temporary files cleaned up")


# %% [markdown]
# ## Conclusion
#
#
# We covered the main functionality of pymrio in this tutorial.
#
# Pymrio has many more features, including aggregation, renaming and restructuring, and analysing the source of stressors. You can explore these topics in more detail in the following example notebooks:
#
# - [Aggregation Examples](aggregation_examples.ipynb)
# - [Adjusting, Renaming and Restructuring](adjusting.ipynb)
# - [Analysing the Source of Stressors (Flow Matrix)](buildflowmatrix.ipynb)
#
# For working with specific MRIO databases, see for example:
#
# - [EXIOBASE](working_with_exiobase.ipynb)
# - [WIOD](working_with_wiod.ipynb)
# - [GLORIA](working_with_gloria.ipynb)
# - [OECD-ICIO](working_with_oecd_icio.ipynb)
#
# You can also check the [API Reference](../api_references.rst) for a full overview of available functions and classes.
#
# If you have questions or need help, please open an issue on our [GitHub page](https://github.com/IndEcol/pymrio). We're happy to help!
#
# Thank you for following the tutorial, and good luck with your MRIO analyses!
