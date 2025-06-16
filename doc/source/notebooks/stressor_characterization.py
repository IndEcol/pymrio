# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# # Characterization of stressors


# Stressor characterization allows the calculation of environmental and social impacts of economic activities. It transforms raw stressor data into meaningful impact indicators.

# Pymrio implements an innovative string-matching approach for characterization.
# This method matches stressors in the characterization table (provided in long format) with available stressors in the MRIO system. This brings the following benefits:

# - Ensures stressor correspondence across the MRIO system and characterization table
# - Performs automatic unit verification
# - Works regardless of entry order in the characterization table
# - Handles characterization tables that include factors for stressors not present in the satellite account
# - Efficiently manages region and sector-specific characterization factors
# - Enables characterization across different extensions

# This contrasts with traditional approaches that rely on matrix multiplication between stressor and characterization matrices, requiring strict 1:1 correspondence between matrix dimensions and precise ordering of entries.

# The characterization functionality is available both as an extension object method and as top-level function accepting complete MRIO objects or extension collections.

# In the following, we give some examples on how to use both methods, starting with some simple example and then advancing to more complex cases with regional specific factors.

# ## Basic Example

# For this example we use the test MRIO included in Pymrio. We also need
# the Pandas library for loading the characterization table and pathlib for some folder manipulation.


from pathlib import Path

import pandas as pd

import pymrio
from pymrio.core.constants import PYMRIO_PATH  # noqa

# To load the test MRIO we use:

io = pymrio.load_test()

# and the characterization table with some foo factors can be loaded by

charact_table = pd.read_csv(
    (PYMRIO_PATH["test_mrio"] / Path("concordance") / "emissions_charact.tsv"),
    sep="\t",
)
charact_table

# This table contains the columns 'stressor' and 'compartment' which correspond
# to the index names of the test_mrio emission satellite accounts:

io.emissions.F

# Theses index-names / columns-names need to match in order to match
# characterization factors to the stressors.

# The other columns names can be passed to the characterization method. By default the method assumes the following column names:
#
# - impact: name of the characterization/impact
# - factor: the numerical (float) multiplication value for a specific stressor to derive the impact/characterized account
# - impact_unit: the unit of the calculated characterization/impact
# - stressor_unit: the unit of the stressor in the extension
#
# Alternative names can be passed through the parameters
# *characterized_name_column*, *characterization_factors_column*, *characterized_unit_column* and *orig_unit_column*
#


# To calculate the characterization we use

char_emis = io.emissions.characterize(charact_table, name="impacts")

# The parameter *name* is optional, if omitted the name will be set to
# extension_name + _characterized. In case the passed name starts with an
# underscore, the return name with be the name of the original extension concatenated with the passed name.

# The return value is a named tuple with the *validation* and *extension* as attriubtes.

print(char_emis.extension)


char_emis.validation

# Checking the validation table is a recommended step that ensures accuracy and completeness before impact calculations. The validation process helps identify potential issues such as:
#
# - Missing characterization factors for specific region/sector/stressor combinations
# - Spelling mistakes or inconsistencies in stressor, sector, or region names
# - Unit mismatches between the MRIO system and characterization factors
# - Incomplete coverage that could affect impact assessment results
#
# By systematically checking these elements, users can avoid calculation errors and ensure their impact assessment captures all relevant environmental and social dimensions with the proper characterization factors.
#

# In the current case, the *charact_table* contains a characterization called 'total
# emissions', for which the calculation requires a stressor not present in the
# satellite account. This is indicated in the validation table in the *error_missing_stressor* column.
# The calculation can proceed, but for all impacts containing the stressor it is assumed to be 0.

# It is possible, to just the verification before doing any calculation with

only_val = io.emissions.characterize(charact_table, only_validation=True)
only_val.validation

# In that case the extension attribute is set to None.
# The same applies if a characterization needs to be aborted due to unit inconsistencies.

# Anyways, in case everything works as expected, the extension can be attached to the MRIO object.

io.impacts = char_emis.extension

# and used for subsequent calculations:

io.calc_all()
io.impacts.D_cba

# Note that units are checked against the unit specification of the extension.
# Thus, any mismatch of units will abort the calculation. The validation table
# helps to identify the issue.

charact_table.loc[charact_table.stressor == "emission_type1", "stressor_unit"] = "t"

ret_error = io.emissions.characterize(charact_table)

ret_error.extension

ret_error.validation

# The error_unit_impact column indicate the stressor with the unit mismatch.

# ## Regional specific characterization factors

# Here we use a table of regionally specific characterisation factors.
# The actual factors contained here are the same as in the basic example and we
# will modify them after loading.
# We will also investigate cases with missing data or conflicting units.
# The same principles can be used for sector specific characterization factors.

# We use the same data test mrio system as before:

io = pymrio.load_test()

# with the regional specific characterization factors from

charact_table_reg = pd.read_csv(
    (PYMRIO_PATH["test_mrio"] / Path("concordance") / "emissions_charact_reg_spec.tsv"),
    sep="\t",
)
charact_table_reg

# Compared with the previous table (charact_table), this table contains an additional
# column *region* which contains the regional specific data.
# Currently, the factors are actually the same as before, thus

char_reg = io.emissions.characterize(charact_table_reg)

# For regional specific characterization, the validation table contains information per region

char_reg.validation

# The extension is again available in the extension attribute

char_reg.extension.F

# gives the same result as before. To highlight regional
# specificity, we double the total emission factors of region 3.

charact_table_reg.loc[
    (charact_table_reg.region == "reg3")
    & (charact_table_reg.impact == "total emissions"),
    "factor",
] = (
    charact_table_reg.loc[
        (charact_table_reg.region == "reg3")
        & (charact_table_reg.impact == "total emissions"),
        "factor",
    ]
    * 2
)

# and calculate the new impacts

char_reg_dbl = io.emissions.characterize(charact_table_reg).extension
char_reg_dbl.F.loc["total emissions"]

# compared to

char_reg.extension.F.loc["total emissions"]

# ## Some more notes on validation


# We can put some more inconsistencies into the table to showcase the validation process.
# Some unit error in the stressors:

charact_table_reg.loc[
    (charact_table_reg.region == "reg4")
    & (charact_table_reg.stressor == "emission_type1"),
    "stressor_unit",
] = "s"

# Some inconsistent impact units:

charact_table_reg.loc[
    (charact_table_reg.region == "reg2")
    & (charact_table_reg.impact == "total emissions"),
    "impact_unit",
] = "kt"


# Some spelling mistake in region 2 for some stressor:

charact_table_reg.loc[
    (charact_table_reg.region == "reg2")
    & (charact_table_reg.stressor == "emission_type2"),
    "region",
] = "reg22"

# Another region data which is not available in the extension

new_data = charact_table_reg.iloc[[0]]
new_data.loc[:, "region"] = "reg_additional"
charact_table_reg = charact_table_reg.merge(new_data, how="outer")


report = io.emissions.characterize(charact_table_reg, only_validation=True).validation

# The unit errors are reported for each row, and the one additional region not present in the extension is report under *error_missing_region*.
# The column *error_unit_impact* indicates the impact with inconsistent units

report[report.stressor == "emission_type1"]

# In case of emission_type2, the *error_missing_region* is True for the whole stressor, since reg2 is "no longer present" in the factor sheets due to the spelling mistake.
# Thus, not all regions are covered in the specifications.
# Again, the column *error_unit_impact* indicates the impact with inconsistent units

report[report.stressor == "emission_type2"]

# ## Characterization across multiple extensions

# In addition to characterizing a single extension, pymrio also offers functionality
# to apply characterization across multiple extensions simultaneously. This is useful
# when your impacts depend on stressors that are distributed across different satellite accounts.

# Let's demonstrate this using our test MRIO system:

io = pymrio.load_test()

# First, let's create multiple extensions from our emissions data to better showcase this functionality:

# Create copies of the emissions extension with different names and data subsets
io.water = io.emissions.copy("water")
io.air = io.emissions.copy("air")

# Keep only water emissions in the water extension
io.water.F = io.water.F.loc[[("emission_type2", "water")], :]
io.water.F_Y = io.water.F_Y.loc[[("emission_type2", "water")], :]

# Keep only air emissions in the air extension
io.air.F = io.air.F.loc[[("emission_type1", "air")], :]
io.air.F_Y = io.air.F_Y.loc[[("emission_type1", "air")], :]

# Examining the extensions:

io.air.F


io.water.F

# To characterize across multiple extensions, we need a characterization table that includes
# an 'extension' column specifying which extension each stressor belongs to:

# Start with our regional characterization table
factors_reg_spec = pd.read_csv(
    (PYMRIO_PATH["test_mrio"] / Path("concordance") / "emissions_charact_reg_spec.tsv"),
    sep="\t",
)

# Create a copy and add an extension column based on compartment
factors_reg_ext = factors_reg_spec.copy()
factors_reg_ext.loc[:, "extension"] = factors_reg_ext.loc[:, "compartment"]

# Filter out any entries that don't correspond to our extensions
factors_reg_ext = factors_reg_ext[factors_reg_ext.compartment.isin(["air", "water"])]

# Examine our multi-extension characterization table:
factors_reg_ext.head(10)

# There are two ways to characterize across multiple extensions:

# 1. Using the top-level function with specific extensions:
ex_reg_multi = pymrio.extension_characterize(
    io.air,
    io.water,  # List the extensions you want to include
    factors=factors_reg_ext,
    new_extension_name="multi_top_level",
).extension

# 2. Using the MRIO object's method which automatically includes all available extensions:
ex_reg_mrio = io.extension_characterize(
    factors=factors_reg_ext, new_extension_name="multi_mrio_method"
).extension

# Both approaches produce the same result when the same extensions are involved:
print("Are the characterized F matrices equal?", ex_reg_multi.F.equals(ex_reg_mrio.F))

# Add the extension to our MRIO and calculate results:
io.multi = ex_reg_multi
io.calc_all()
io.multi.D_cba

# As with single extension characterization, validation is crucial:
validation_report = pymrio.extension_characterize(
    io.air, io.water, factors=factors_reg_ext, only_validation=True
).validation

print("Validation report:")
validation_report

# The validation process helps identify issues such as:
# - Missing stressors or extensions
# - Unit inconsistencies
# - Missing regions or sectors
# - Extension name mismatches

# Important considerations for multi-extension characterization:
#
# 1. The 'extension' column in your characterization table must match the extension names in your MRIO
# 2. All extensions must have compatible region and sector classifications
# 3. Units must be consistent across extensions and characterization factors
# 4. If a characterization table references an extension that doesn't exist,
#    it will be noted in the validation report
