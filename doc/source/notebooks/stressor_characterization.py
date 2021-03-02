# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.10.2
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # Characterization of stressors

# The characterization of stressors is a standard procedure to calculate the environmental and social impacts of economic activity. This is usually accomplished by multiplying (matrix-multiplication) the stressor-matrix with a characterization-matrix. Doing that in the matrix forms requires a 1:1 correspondence of the columns of the characterization matrix to the rows of the stressor-matrix.

# Pymrio uses a different approach with matching the strings of the
# characterization table (given in long-format) to the available stressors. By
# doing that, the order of the entries in the characterization-table becomes
# unimportant.
# This implementation also allows to use characterization tables which includes
# characterization for stressors not present in the given satellite account. All
# characterizations relying on not available stressor will be automatically
# removed.

# ## Example

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
#
# Alternative names can be passed through the parameters
# *characterized_name_column*, *characterization_factors_column* and *characterized_unit_column*.
#
# Note, that units of stressor are currently not checked - units as given in
# the satellite account to be characterized are assumed. These can be seen by:

io.emissions.unit

# Also note, that the charact_table contains a characterization called 'total
# emissions', for which the calculation requires a stressor not present in the
# satellite account. This will be automatically omitted.

# To calculate the characterization we use

impacts = io.emissions.characterize(charact_table, name="impacts")

# The parameter *name* is optional, if omitted the name will be set to
# extension_name + _characterized

# The method call above results in a pymrio.Extension which can be inspected with the usual
# methods, e.g.:

impacts.F

impacts.F_Y

# and the extension can be added to the MRIO

io.impacts = impacts

# and used for subsequent calculations:

io.calc_all()
io.impacts.D_cba

# ### Characterizing calculated results

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
