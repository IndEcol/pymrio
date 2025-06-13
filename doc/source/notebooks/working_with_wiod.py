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
# # Handling the WIOD EE MRIO database

# %% [markdown]
# ## Getting the database

# %% [markdown]
# The WIOD database is available at http://www.wiod.org. You can download these files with the pymrio automatic downloader as described at [WIOD download](autodownload.ipynb#WIOD-download).

# %% [markdown]
# In the most simple case you get the full WIOD database with:

# %%
import pymrio

# %%
wiod_storage = "/tmp/mrios/WIOD2013"

# %%
wiod_meta = pymrio.download_wiod2013(storage_folder=wiod_storage)

# %% [markdown]
# This download the whole 2013 release of WIOD including all extensions.

# %% [markdown]
# The extension (satellite accounts) are provided as zip files. You can use them directly in pymrio (without extracting them). If you want to have them extracted, create a folder with the name of each extension (without the ending ".zip") and extract the zip file there.

# %% [markdown]
# ## Parsing

# %% [markdown]
# ### Parsing a single year

# %% [markdown]
# A single year of the WIOD database can be parse by:

# %%
wiod2007 = pymrio.parse_wiod(year=2007, path=wiod_storage)

# %% [markdown]
# Which loads the specific year and extension data:

# %%
wiod2007.Z.head()

# %%
wiod2007.AIR.F

# %% [markdown]
# If a WIOD SEA file is present (at the root of path or in a folder named
# 'SEA' - only one file!), the labor data of this file gets included in the
# factor_input extension (calculated for the the three skill levels
# available). The monetary data in this file is not added because it is only
# given in national currency:

# %%
wiod2007.SEA.F

# %% [markdown]
# Provenance tracking and additional meta data is availabe in the field ```meta```:

# %%
print(wiod2007.meta)

# %% [markdown]
# WIOD provides three different sector/final demand categories naming
# schemes. The one to use for pymrio can specified by passing a tuple
# ```names=``` with:
#
# 1) 'isic': ISIC rev 3 Codes - available for interindustry flows and final demand rows.
#
# 2) 'full': Full names - available for final demand rows and final demand columns (categories) and interindustry flows.
#
# 3) 'c_codes' : WIOD specific sector numbers, available for final demand rows and columns (categories) and interindustry flows.
#
# Internally, the parser relies on 1) for the interindustry flows and 3) for the final demand categories. This is the default and will also be used if just 'isic' gets passed ('c_codes' also replace 'isic' if this was passed for final demand categories). To specify different finial consumption category names, pass a tuple with (sectors/interindustry classification, fd categories), eg ('isic', 'full'). Names are case insensitive and passing the first character is sufficient.
#
# For example, for loading wiod with full sector names:
#
#

# %%
wiod2007_full = pymrio.parse_wiod(year=2007, path=wiod_storage, names=("full", "full"))
wiod2007_full.Y.head()

# %% [markdown]
# The wiod parsing routine provides some more options - for a full specification see [the API reference](../api_doc/pymrio.parse_wiod.rst)

# %% [markdown]
# ### Parsing multiple years

# %% [markdown]
# Multiple years can be passed by running the parser in a for loop.
