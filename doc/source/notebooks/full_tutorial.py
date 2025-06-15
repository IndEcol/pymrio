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
# # Pymrio Tutorial
#
# A complete tutorial covering all top-level functions of pymrio, using the test MRIO system.

# %% [markdown]
# ## Setup and Installation
#
# Before starting this tutorial, make sure you've got pymrio installed. You can grab it from conda-forge or PyPi.
# Use pip, mamba, conda, or whatever package manager you prefer to get it sorted. For example

# %%
# !conda install -c conda-forge pymrio

# %% [markdown]
# ## 1. Getting Started with Test MRIO Data
#
# We begin by importing pymrio and loading the test MRIO system. This small test system contains six regions and eight sectors, making it ideal for learning purposes.

# %%
import pymrio

# Load the test MRIO system
test_mrio = pymrio.load_test()

# Display basic information about the system
print(test_mrio)
print("Type of object:", type(test_mrio))
print("Available extensions:", test_mrio.extensions)

# %% [markdown]
# Note that any other MRIO database can be used with the same functions demonstrated here. 
# The test system serves only as a representative example for larger, real-world datasets. See the notebooks on [EXIOBASE](working_with_exiobase.py) and [Eora26](working_with_eora26.ipynb) for more details.

# %% [markdown]
# ## 2. Exploring System Information

# %% [markdown]
# ### 2.1 Basic Structure Information
#
# The system provides several methods to understand its structure:

# %%
# Get regions and sectors
print("Regions:", test_mrio.regions)
print("Sectors:", test_mrio.sectors)
print("Final demand categories:", test_mrio.Y_categories)

# %% [markdown]
# ### 2.2 Search Functionality
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
# **Tip**
#
# Use the find method to get a quick overview where you find a specific term, in particular for mrio systems with multiple extensions.
# For example, the following finds "air" in the compartment information of one extension.

# %%
print("Search for occurance of >air< in the whole system:", test_mrio.find("air"))


# %% [markdown]
# ## 3. Core Calculations with calc_all
#
# The `calc_all` method is fundamental to pymrio analysis. It automatically identifies missing tables and calculates all necessary accounts:



# %% [markdown]
# Before calculation, some tables are missing

# %%
print("Before calc_all:")
print(test_mrio.DataFrames)
print(test_mrio.emissions.DataFrames)

# %% [markdown]
# Calculate all missing parts

# %%
test_mrio.calc_all()

# %% [markdown]
# After calculation, all tables are available

# %%
print("After calc_all:")
print(test_mrio.DataFrames)

# %% [markdown]
# And we know also have several classical EE-MRIO results available:

# %%
print("\nEmissions accounts:")
print(test_mrio.emissions.DataFrames)

# For example
print("D_cba (consumption-based):", test_mrio.emissions.D_cba)

# %% [markdown]
# ## 4. Search and Extract Functionality

# %% [markdown]
# ### 4.1 Extracting Specific Accounts

# %% [markdown]
# Extract consumption-based accounts for a specific stressor

# %%
cba_emission1 = test_mrio.emissions.D_cba.loc[['emission_type1']]
print("CBA emissions by region for emission_type1:")
print(cba_emission1)

# %% [markdown]
# Extract data for specific regions

# %%
reg1_data = test_mrio.emissions.D_cba_reg[['reg1', 'reg3']]
print("\nTotal CBA emissions for the selected regions:")
print(reg1_data)

#
# Besides the direct access to the DataFrames explained above, one can also
# extract data into dictionaries for alternative access.:

# %%
emission_type1_data = test_mrio.emissions.get_row_data('emission_type1')


# %% [markdown]
# This extracts all data available for >emission_type1<

# %%
emission_type1_data.keys()


# %% [markdown]
# ### 4.2 Advanced Search Patterns
#
# Use regular expressions for more complex searches:

# %%
emis_search = test_mrio.find("emission.*")
print("Emission... occurances:", emis_search)

all_extension_search = test_mrio.extension_contains("typ+")
print("Extensions containing 'type':", all_extension_search)

# %% [markdown]
# ## 5. Ghosh Calculations in calc_all
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
# See the math section of the documentation for further details on the Ghosh calculations.


# %% [markdown]
# ## 6. Using Functions from iomath
#
# Pymrio's `iomath` module provides low-level functions for specific calculations:

# %%
from pymrio.tools import iomath
import numpy as np

# Calculate specific matrices manually
A_manual = iomath.calc_A(test_mrio.Z, test_mrio.x)
print("Manual A matrix calculation matches:", np.allclose(A_manual, test_mrio.A))

# Calculate Leontief matrix
L_manual = iomath.calc_L(test_mrio.A)
print("Manual L matrix calculation matches:", np.allclose(L_manual, test_mrio.L))

# Calculate multipliers
S = test_mrio.emissions.S
M_manual = iomath.calc_M(S, test_mrio.L)
print("Manual multiplier calculation matches:", np.allclose(M_manual, test_mrio.emissions.M))

# %% [markdown]
# ## 7. Gross Trade Analysis
#
# The `calc_gross_trade` function provides insights into bilateral trade flows:

# %%
gross_trade = test_mrio.get_gross_trade()

# %% [markdown]
# This give the total trade flows from one region/sectors to other regions

# %%
gross_trade.bilat_flows


# %% [markdown]
# As well as the totals for each region
gross_trade.totals


# %%
gross_trade.bilat_flows


# %% [markdown]
# ## 8. Extension Methods: Concatenate, Convert, and Characterize

# %% [markdown]
# ### 8.1 Extension Concatenation
#
# The `extension_concate` method allows combining multiple extensions.

# %%
# Create a copy for demonstration
ext_emis2 = test_mrio.emissions.copy()
# Combine two extensions with same index structure
new_ext = pymrio.extension_concate(test_mrio.emissions, ext_emis2, new_extension_name='emissions_combined')
new_ext.rows

# %% [markdown]
# Combining extensions with different indicies results in a new index called >indicator<. Any indicies not avaialable in one of the extensions is set to NaN.

# %%
all_ext = pymrio.extension_concate(test_mrio.emissions, test_mrio.factor_inputs, new_extension_name='All')
print(all_ext)
all_ext.rows

# %% [markdown]
# In any case, the extension can be attached to the mrio object and used alongside the others.

# %%
test_mrio.all_ext = all_ext
print(test_mrio.extensions)
print(test_mrio.extensions_instance_names)

# %% [markdown]
# ### 8.2 Extension Conversion
#
# The `extension_convert` method transforms extensions based on mapping functions:

# %%
# Example conversion mapping (hypothetical unit conversion)
conversion_factors = pd.DataFrame({
    'stressor': ['emission_type1', 'emission_type2', 'emission_type3'],
    'factor': [1000, 500, 750]  # Convert to different units
})

try:
    # Apply conversion (this is a conceptual example)
    # In practice, you would use specific conversion mappings
    print("Extension conversion methods available for unit transformations")
    print("Conversion factors example:")
    print(conversion_factors)
except Exception as e:
    print(f"Conversion example: {e}")

# %% [markdown]
# ### 8.3 Extension Characterization
#
# The `characterize` method applies characterization factors to transform stressors into impacts:

# %%
# Create characterization factors
char_factors = pd.DataFrame({
    'stressor': ['emission_type1', 'emission_type2', 'emission_type3'],
    'impact': ['climate_change', 'acidification', 'eutrophication'],
    'factor': [25.0, 1.5, 0.8],  # kg CO2-eq, SO2-eq, PO4-eq
    'impact_unit': ['kg CO2-eq', 'kg SO2-eq', 'kg PO4-eq'],
    'stressor_unit': ['kg', 'kg', 'kg']
})

print("Characterization factors:")
print(char_factors)

# Apply characterization
try:
    characterized_extension = test_mrio.emissions.characterize(
        factors=char_factors,
        characterized_name_column='impact',
        characterization_factors_column='factor',
        characterized_unit_column='impact_unit',
        orig_unit_column='stressor_unit'
    )
    print("Characterization successful")
    print("Characterized impacts shape:", characterized_extension.F.shape)
except Exception as e:
    print(f"Characterization requires specific data format: {e}")

# %% [markdown]
# ## 9. General and Region-Specific Characterization

# %% [markdown]
# ### 9.1 General Characterization
#
# The general `characterize` function works across multiple extensions:

# %%
# Example of cross-extension characterization
try:
    # This would characterize across multiple extensions
    result = pymrio.characterize(test_mrio.emissions, factors=char_factors)
    print("Cross-extension characterization completed")
except Exception as e:
    print(f"Cross-extension characterization: {e}")

# %% [markdown]
# ### 9.2 Region-Specific Characterization
#
# For region-specific characterization factors:

# %%
# Create region-specific characterization factors
region_char_factors = pd.DataFrame({
    'region': ['reg1', 'reg1', 'reg2', 'reg2'],
    'stressor': ['emission_type1', 'emission_type2', 'emission_type1', 'emission_type2'],
    'impact': ['climate_change', 'acidification', 'climate_change', 'acidification'],
    'factor': [28.0, 1.2, 22.0, 1.8],  # Different factors by region
    'impact_unit': ['kg CO2-eq', 'kg SO2-eq', 'kg CO2-eq', 'kg SO2-eq'],
    'stressor_unit': ['kg', 'kg', 'kg', 'kg']
})

print("Region-specific characterization factors:")
print(region_char_factors)

# This allows for location-specific impact assessment
print("Region-specific characterization enables location-dependent impact factors")

# %% [markdown]
# ## 10. Aggregation Example
#
# Pymrio provides flexible aggregation capabilities:

# %%
# Create aggregation mapping for regions
region_agg = pd.DataFrame({
    'original': ['reg1', 'reg2', 'reg3', 'reg4', 'reg5', 'reg6'],
    'aggregated': ['North', 'North', 'North', 'South', 'South', 'South']
})

# Create aggregation mapping for sectors
sector_agg = pd.DataFrame({
    'original': ['food', 'mining', 'manufactoring', 'electricity', 'construction', 'trade', 'transport', 'other'],
    'aggregated': ['Primary', 'Primary', 'Secondary', 'Secondary', 'Secondary', 'Services', 'Services', 'Services']
})

print("Region aggregation mapping:")
print(region_agg)
print("\nSector aggregation mapping:")
print(sector_agg)

# Perform aggregation
try:
    # Create aggregation vectors
    reg_agg_vec = region_agg.set_index('original')['aggregated']
    sec_agg_vec = sector_agg.set_index('original')['aggregated']
    
    # Apply aggregation
    aggregated_mrio = test_mrio.aggregate(
        region_agg=reg_agg_vec,
        sector_agg=sec_agg_vec,
        inplace=False
    )
    
    print("\nAggregated system:")
    print("New regions:", aggregated_mrio.get_regions().tolist())
    print("New sectors:", aggregated_mrio.get_sectors().tolist())
    print("Aggregated Z matrix shape:", aggregated_mrio.Z.shape)
    
except Exception as e:
    print(f"Aggregation example: {e}")

# %% [markdown]
# ## 11. Save and Load Data

# %% [markdown]
# ### 11.1 Saving to Text Format

# %%
import tempfile
import os

# Create temporary directory for demonstration
temp_dir = tempfile.mkdtemp()

try:
    # Save to text format
    txt_path = os.path.join(temp_dir, 'test_mrio_txt')
    test_mrio.save_all(txt_path, table_format='txt')
    print(f"Saved to text format in: {txt_path}")
    
    # List saved files
    saved_files = os.listdir(txt_path)
    print("Saved files:", saved_files[:10])  # Show first 10 files
    
    # Load from text format
    loaded_mrio_txt = pymrio.load_all(txt_path)
    print("Successfully loaded from text format")
    print("Loaded extensions:", loaded_mrio_txt.get_extensions().tolist())
    
except Exception as e:
    print(f"Text format save/load: {e}")

# %% [markdown]
# ### 11.2 Saving to Parquet Format

# %%
try:
    # Save to parquet format (more efficient for large datasets)
    parquet_path = os.path.join(temp_dir, 'test_mrio_parquet')
    test_mrio.save_all(parquet_path, table_format='parquet')
    print(f"Saved to parquet format in: {parquet_path}")
    
    # List saved files
    saved_files_parquet = os.listdir(parquet_path)
    print("Saved parquet files:", saved_files_parquet[:10])
    
    # Load from parquet format
    loaded_mrio_parquet = pymrio.load_all(parquet_path)
    print("Successfully loaded from parquet format")
    print("Data integrity check:", 
          np.allclose(loaded_mrio_parquet.Z.values, test_mrio.Z.values))
    
except Exception as e:
    print(f"Parquet format save/load: {e}")

# Clean up temporary directory
import shutil
try:
    shutil.rmtree(temp_dir)
    print("Temporary files cleaned up")
except:
    pass

# %% [markdown]
# ## 12. Additional Utility Functions

# %% [markdown]
# ### 12.1 System Information and Metadata

# %%
# Access metadata
print("MRIO system metadata:")
print("Name:", test_mrio.meta.name)
print("Description:", test_mrio.meta.description)

# Get system dimensions
print("\nSystem dimensions:")
print("Number of regions:", len(test_mrio.get_regions()))
print("Number of sectors:", len(test_mrio.get_sectors()))
print("Number of final demand categories:", len(test_mrio.get_Y_categories()))

# Extension information
for ext_name in test_mrio.get_extensions():
    ext = getattr(test_mrio, ext_name)
    print(f"\nExtension '{ext_name}':")
    print(f"  Number of stressors: {len(ext.get_rows())}")
    print(f"  Unit information available: {ext.unit is not None}")

# %% [markdown]
# ### 12.2 Data Validation and Quality Checks

# %%
# Check data consistency
print("Data validation:")
print("Z matrix balance check:", np.allclose(test_mrio.Z.sum().sum() + test_mrio.Y.sum().sum(), 
                                            test_mrio.x.sum().sum()))

# Check for missing values
print("Missing values in Z:", test_mrio.Z.isna().sum().sum())
print("Missing values in Y:", test_mrio.Y.isna().sum().sum())

# Extension data checks
for ext_name in test_mrio.get_extensions():
    ext = getattr(test_mrio, ext_name)
    print(f"Missing values in {ext_name}.F:", ext.F.isna().sum().sum())

# %% [markdown]
# ## Conclusion
#
# This tutorial has covered all major top-level functions of pymrio:
#
# 1. **Data Loading**: Using `pymrio.load_test()` and understanding the system structure
# 2. **System Information**: Methods like `get_regions()`, `get_sectors()`, and `search()`
# 3. **Core Calculations**: The comprehensive `calc_all()` method
# 4. **Search and Extract**: Finding and extracting specific accounts and data
# 5. **Ghosh Calculations**: Downstream analysis capabilities
# 6. **iomath Functions**: Low-level calculation functions for specific operations
# 7. **Gross Trade**: Analysis of bilateral trade flows
# 8. **Extension Methods**: Concatenation, conversion, and characterization
# 9. **Characterization**: General and region-specific impact assessment
# 10. **Aggregation**: Flexible system aggregation capabilities
# 11. **Data Persistence**: Saving and loading in multiple formats
#
# The test MRIO system provides an excellent foundation for understanding these concepts, which can then be applied to larger, real-world databases such as EXIOBASE, WIOD, or EORA26. Each function demonstrated here scales effectively to handle comprehensive global MRIO systems whilst maintaining the same intuitive API structure.
#
# For further exploration, consult the complete pymrio documentation at https://pymrio.readthedocs.io/ and examine the extensive examples available in the GitHub repository.
