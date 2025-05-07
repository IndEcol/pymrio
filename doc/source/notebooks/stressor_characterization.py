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


# Note, that the *charact_table* contains a characterization called 'total
# emissions', for which the calculation requires a stressor not present in the
# satellite account. For all impacts containing the stressor it is assumed to be 0.
# Once can check for missing specification like this one by validating the characterization table
# before. See TODO: - link to below

# To calculate the characterization we use

char_emis = io.emissions.characterize(charact_table, name="impacts")

# The parameter *name* is optional, if omitted the name will be set to
# extension_name + _characterized. In case the passed name starts with an
# underscore, the return name with be the name of the original extension concatenated with the passed name.

# The return value is a pymrio.Extension object, which contains the characterized impacts.

print(char_emis)

# Any/all of the extensions can be attached to the mrio system

io.impacts = char_emis

# and used for subsequent calculations:

io.calc_all()
io.impacts.D_cba

# Note that units are checked against the unit specification of the extension.
# Thus, any mismatch of units will raise an error. For example:

try:
    charact_table.loc[charact_table.stressor == "emission_type1", "stressor_unit"] = "t"
    io.emissions.characterize(charact_table)
except ValueError as e:
    print(f"Error: {e}")

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
char_reg.F

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

char_reg_dbl = io.emissions.characterize(charact_table_reg)
char_reg_dbl.F.loc["total emissions"]

# compared to

char_reg.F.loc["total emissions"]

# ## Validating characterization tables

# Validation of characterization tables is a recommended step that ensures accuracy and completeness before impact calculations. The validation process helps identify potential issues such as:
#
# - Missing characterization factors for specific region/sector/stressor combinations
# - Spelling mistakes or inconsistencies in stressor, sector, or region names
# - Unit mismatches between the MRIO system and characterization factors
# - Incomplete coverage that could affect impact assessment results
#
# By systematically checking these elements, users can avoid calculation errors and ensure their impact assessment captures all relevant environmental and social dimensions with the proper characterization factors.
#


# The signature of the method is similar to the characterization method with the same default parameter.
# Thus, to validate the characterization table from before, we can just use

charact_table_reg = pd.read_csv(
    (PYMRIO_PATH["test_mrio"] / Path("concordance") / "emissions_charact_reg_spec.tsv"),
    sep="\t",
)

report = io.emissions.validate_characterization_table(charact_table_reg)
report

# The report covers contains the table passed, with an extension of several *error_* columns reporting on various potential errors.
# In the original table, it indicates that *emission_type3" is not present in the stressor matrix.

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


report = io.emissions.validate_characterization_table(charact_table_reg)

# The unit errors are reported for each row, and the one additional region not present in the extension is report under *error_missing_region*.
# The column *error_unit_impact* indicates the impact with inconsistent units

report[report.stressor == "emission_type1"]

# In case of emission_type2, the *error_missing_region* is True for the whole stressor, since reg2 is "no longer present" in the factor sheets due to the spelling mistake.
# Thus, not all regions are covered in the specifications.
# Again, the column *error_unit_impact* indicates the impact with inconsistent units

report[report.stressor == "emission_type2"]

# As always, more information can be found in the docstrings of the methods.
