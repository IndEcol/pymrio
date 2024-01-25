# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.15.0
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# # Adjusting, Renaming and Restructuring

# In this tutorial we will cover how to modify the structure of an MRIO system. 
# This includes renaming sectors, regions and Y categories, 
# as well as restructuring (extracting and merging) satellite accounts.


# We use the small test MRIO system that is included in the pymrio package for all examples.
# The method work the same for any MRIO system.

import pymrio

mrio = pymrio.load_test()

# We can use several functions to get a quick overview over the MRIO system [(see the Exploring MRIO tutorial for more examples)](explore.ipynb).

mrio.get_sectors()

mrio.get_regions()

mrio.get_Y_categories()

# A list of available satellite accounts can be obtained by

mrio.get_extensions()

# this returns a generator over all extensions, to just get the names which can be used to loop over the extensions. To just get the names:

list(mrio.get_extensions())

# ## Renaming

# ### Manual renaming

# All the names returned are literally just names and can easily be renamed.
# To rename sectors or regions just pass a dictionary with the new names:

mrio.rename_regions({"reg1": "REGION A", "reg2": "REGION B"})

mrio.get_regions()

# Renaming sectors or Y categories works the same way

mrio.rename_sectors({"mining": "dwarf business"})
mrio.rename_Y_categories({"Final consumption expenditure by households": "fin_house"})

mrio.get_sectors()

mrio.get_Y_categories()

# ### Renaming based on included classifications synonyms

# Some MRIOs come with a selections of names which can be used for renaming.
# These can be obtained via 'get_classification', passing the name of the IO (pass None to get a list of available classifications).

mrio_class = pymrio.get_classification(mrio_name="test")

# The classification data contains different names and aggregation levels for the sectors and final demand categories. The easiest way to explore the classification data is by using the autocomplete functionality. Depending on the editor your are using this might work with typing mrio_class.sectors. pressing Tab or Ctrl-Space. The same works for mrio_class.finaldemand.

# Alternatively it is possible to just print the underlying dataframes with (similar for finaldemand)

mrio_class.sectors

# This can be used to generate dictionaries for renaming the sectors of the MRIO, eg with:

conv_dict = mrio_class.get_sector_dict(
    mrio_class.sectors.TestMrioName, mrio_class.sectors.TestMrioCode
)
conv_dict

# This can then be used for renaming the sectors:

mrio = pymrio.load_test()

mrio.rename_sectors(conv_dict)
mrio.get_sectors()


# In the mrio_class.sectors you will also find an entry 'Type' which represents a many to one mapping. This can be used for aggregating the MRIO and is explained [in the aggregation tutorial](aggregation_examples.ipynb#Aggregation-by-renaming).

## Extracting satellite accounts

# Each extension/satellite account of the MRIO contains a method 'extract'.


# Satellite accounts can be extracted from the MRIO system by using the extension_extract method. This method takes the name of the satellite account as first argument and a list of regions as second argument. The regions can be given as a list of region names or as a list of region indices. The method returns a new MRIO system with the extracted satellite account.

mrio.extension_extract("emissions", ["reg1", "reg2"])
