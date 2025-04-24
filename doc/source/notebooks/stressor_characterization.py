# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.7
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# # Characterization of stressors

# The characterization of stressors is a standard procedure to calculate the environmental and social impacts of economic activity. This is usually accomplished by multiplying (matrix-multiplication) the stressor-matrix with a characterization-matrix. Doing that in the matrix forms requires a 1:1 correspondence of the columns of the characterization matrix to the rows of the stressor-matrix.

# Pymrio uses a different approach with matching the strings of the
# characterization table (given in long-format) to the available stressors.
# Advantages:

#   - enforcing correspondence of stressors across the mrio system and characterization table
#   - unit checks across the extension and characterization table 
#   - agnostic to the order of the entries in the characterization table
#   - allows to use characterization tables which includes characterization for stressors not present in the given satellite account. All characterizations relying on not available stressor will be automatically removed.
#   - efficient handling of region and/or sector specific characterization factors 
#   - enables characterization of stressors across different extensions


# The characterization function is available as a method of the extension object and as top-level function accepting a full MRIO object or collection of extensions (TODO: implement).

# In the following, we go through some example on how to use both methods, starting with some simple example and then advancing to more complex cases with regional specific factors.

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


# Note, that the charact_table contains a characterization called 'total
# emissions', for which the calculation requires a stressor not present in the
# satellite account. This will be automatically omitted.

# To calculate the characterization we use

char_emis = io.emissions.characterize(charact_table, name="impacts")

# The parameter *name* is optional, if omitted the name will be set to
# extension_name + _characterized. In case the passed name starts with an 
# underscore, the return name with be the name of the original extension concatenated with the passed name.

# The method call returns a namedTuple with *extension* and *factors*.
# The attribute *extension* is the new extension which can be attached to the MRIO object.

print(char_emis.extension)

# The *factors* attribute contains information on the used characterization factors.

char_emis.factors

# It reports on errors encountered during the processing (all columns starting with *error_*) and if a specific stressor was dropped. In the case above, emission_type3 is not available in the extension data, and the report specifies that this stressor was not used for the calculation. 

# We can also choose to omit any impact which includes stressors not present in the extension. 
# To do so, we set *drop_missing* to True:

char_emis_dropped = io.emissions.characterize(charact_table, name="impacts", drop_missing=True)

# which results in 

char_emis_dropped.factors

# All impacts effected by the missing stressor have been dropped. Compare

char_emis.extension.F

# with

char_emis_dropped.extension.F


# Any/all of the extensions can be attached to the mrio system

io.impacts = char_emis.extension

# and used for subsequent calculations:

io.calc_all()
io.impacts.D_cba


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
char_reg.extension.F

# gives the same result as before. To highlight regional
# specificity, we double the total emission factors of region 3.

charact_table_reg.loc[(charact_table_reg.region == "reg3") & (charact_table_reg.impact == "total emissions"), "factor"] = charact_table_reg.loc[(charact_table_reg.region == "reg3") & (charact_table_reg.impact == "total emissions"), "factor"] * 2

# and calculate the new impacts

char_reg_dbl = io.emissions.characterize(charact_table_reg)
char_reg_dbl.extension.F.loc["total emissions"]

# compared to

char_reg.extension.F.loc["total emissions"]

# The return value also contains the report with the used factors

char_reg_dbl.factors

# Next, we will look at different cases of missing data handling.

### Missing data 

# This section extends on the basic missing data section from the basic example above.
# We will use the regional characterization table again, calling it *ch* to 
# shorten the syntax.

ch = pd.read_csv(
    (PYMRIO_PATH["test_mrio"] / Path("concordance") / "emissions_charact_reg_spec.tsv"),
    sep="\t",
)
ch

# And modify different rows to showcase missing/contradicting data.

# First, we will cover the case with miss-aligned units.
# Lets set the unit of the stressor *emission_type1* to "t".


ch.loc[ch.stressor == "emission_type1", "stressor_unit"] = "t"
ch

# Using this table for characterization leads to multiple dropped values, with 
# the cause given in the column *error_unit_stressor*

unit_miss = io.emissions.characterize(ch)
unit_miss.factors

# Note: in production ready code one can guard against such cases by simply 
# asserting that the error columns are False, e.g.

assert all(unit_miss.factors.error_unit_stressor is False), "Unit mismatch"

# Further note, since any error leads to dropping the specific row, one can also check for any dropped data to identify any error



# ### Characterizing calculated results
# TODO: think of dropping this. Its trivial or dangerous, in case of regional characteriation

# The characterize method can also be used to characterize already calculated
# results. This works in the same way:

io_aly = pymrio.load_test().calc_all()

io_aly.emissions.D_cba

io_aly.impacts = io_aly.emissions.characterize(charact_table, name="impacts_new")

# Note, that all results which can be characterized directly (all flow accounts
# like D_cba, D_pba, ...) are automatically included:

io_aly.impacts.D_cba

# Whereas coefficient accounts (M, S) are removed:

io_aly.impacts.M

# To calculated these use

io_aly.calc_all()
io_aly.impacts.M

# which will calculate the missing accounts.

# For these calculations, the characterized accounts can also be used outside
# the MRIO system. Thus:

independent_extension = io_aly.emissions.characterize(charact_table, name="impacts_new")

type(independent_extension)

independent_extension.M

independent_extension_calc = independent_extension.calc_system(x=io_aly.x, Y=io_aly.Y)

independent_extension.M

# ## Inspecting the used characterization table

# Pymrio automatically adjust the characterization table by removing accounts
# which can not be calculated using a given extension. The removed accounts are
# reported through a warning message (e.g. "WARNING:root:Impact >total
# emissions< removed - calculation requires stressors not present in extension
# >Emissions<" in the examples above).
#
# It is also possible, to obtain the cleaned characterization-table for
# inspection and further use. To do so:

impacts = io.emissions.characterize(
    charact_table, name="impacts", return_char_matrix=True
)

# This changes the return type from a pymrio.Extension to a named tuple

type(impacts)

# with

impacts.extension

# and

impacts.factors

# The latter is the characterization table used for the calculation.
#
# For further information see the characterization docstring:

print(io.emissions.characterize.__doc__)
