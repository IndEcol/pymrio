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
# # Linking GLAM with EXIOBASE 3

# %% [markdown]
# This tutorial covers the linking of the [Global Guidance for Life Cycle Impact Assessment Indicators and Methods (GLAM)](https://www.lifecycleinitiative.org/activities/life-cycle-assessment-data-and-methods/global-guidance-for-life-cycle-impact-assessment-indicators-and-methods-glam/) with the Environmentally-Extended Multi-Regional Input Output database [EXIOBASE 3](https://onlinelibrary.wiley.com/doi/full/10.1111/jiec.12715).

# %% [markdown]
# The tutorial was tested with the latest version of both datasets:
#
# - [GLAM V1.0.2024.10](https://www.lifecycleinitiative.org/activities/life-cycle-assessment-data-and-methods/global-guidance-for-life-cycle-impact-assessment-indicators-and-methods-glam/)
# - [EXIOBASE 3.8.2](https://doi.org/10.5281/zenodo.5589597)

# %% [markdown]
# After the initial setup and data retrieval, the linking approach follows a two step approach. First, we translate the EXIOBASE stressor names to GLAM flow names; second, we characterise the flows with the GLAM characterization factors.
# TODO: insert links to the headers later
# The whole tutorial is self contained and automatically downloads all required data. The only pre-requisite is a [working installation of the latest version of Pymrio](https://pymrio.readthedocs.io/en/latest/installation.html).

# %% [markdown]
# ## Setup, folder definitions and data gathering

# %% [markdown]
# Here we import the required Python modules and define the folders to store the data.

# %%
from pathlib import Path

import pandas as pd

import pymrio

# %% [markdown]
# Next, we specify were data should be stored


# %%
# TODO: Fix back
# DATA_ROOT = Path("/tmp/glam_exio_tutorial") # set this to your data directory
DATA_ROOT = Path(
    "/home/konstans/tmp/glam_exio_tutorial"
)  # set this to your data directory

EXIOBASE_STORAGE_FOLDER = DATA_ROOT / "exiobase"
GLAM_STORAGE_FOLDER = DATA_ROOT / "glam"

EXIOBASE_STORAGE_FOLDER.mkdir(parents=True, exist_ok=True)
GLAM_STORAGE_FOLDER.mkdir(parents=True, exist_ok=True)

# %% [markdown]
# Then, we download the data needed for the linking.
# Here, we use EXIOBASE 3.8.2 in the product by product (pxp) classification for the year 2018.

# %%
pymrio.download_exiobase3(
    storage_folder=EXIOBASE_STORAGE_FOLDER,
    years=[2018],
    system="pxp",
    overwrite_existing=False,
)

# %% [markdown]
# The command downloaded the EXIOBASE 3 zip archive for given year/system if the data not already exists in the given folder.
# We do not need to extract the archive, pymrio can handle all processing from the zip archive.
#
#

# %% [markdown]
# Next, we download the latest GLAM data. Again, the function checks if the data is already available.

# %%
pymrio.GLAMprocessing.get_GLAM(
    storage_folder=GLAM_STORAGE_FOLDER, overwrite_existing=False
)

# %% [markdown]
# The download contains one single zip archive. We can keep that compressed, but we need the
# name for further processing.

# %%
GLAM_raw = [
    archive for archive in GLAM_STORAGE_FOLDER.glob("*") if archive.suffix == ".zip"
][0]


# %% [markdown]
# Now we need to process the GLAM data:
# We need to concatenate the characterization factors and the flow names into a single table, change the region classification to fit the EXIOBASE classification and rename some columns names. This can be done by calling (this takes a couple of minutes):

# %%
GLAM_char = pymrio.GLAMprocessing.prep_GLAM(GLAM_data=GLAM_raw)

# TODO: remove later, just for fast testing
GLAM_char_archive = GLAM_char.copy()

# TODO: remove later
# take 10000 random samples:
GLAM_char = GLAM_char_archive.sample(10000)

# %% [markdown]
# This results in a long table with all characterization factors from GLAM.
# We can then later use this table to characterize EXIOBASE flows after renaming to GLAM flow names.
# We can have a look at the table:

# %%
GLAM_char.head()

# %% [markdown]
# We can also save the data for later use

# %%
GLAM_char.to_csv(GLAM_STORAGE_FOLDER / "GLAM_characterization_table.csv")

# %% [markdown]
# ## Convert EXIOBASE stressors to GLAM flows

# %% [markdown]
# Here we first get the EXIOBASE GLAM bridge with:

# %%
exio_glam_bridge = pymrio.GLAMprocessing.get_GLAM_EXIO3_bridge()

# %% [markdown]
# This bride links the EXIOBASE stressors to the GLAM flow names and UUIDs.
# EXIOBASE stressors are linked via [regular expressions](https://docs.python.org/3/library/re.html)
# TODO: function for showing the link without regular expressions

# %%
exio_glam_bridge

# %% [markdown]
# We can then convert the EXIOBASE stressors to GLAM flows.
# To do so, we first load the EXIOBASE 3 data we downloaded previously into memory:

# %%
exio3 = pymrio.parse_exiobase3(EXIOBASE_STORAGE_FOLDER / "IOT_2018_pxp.zip")

# %% [markdown]
# To get a clean state, we reset any pre-calculated data from the MRIO system.


# %%
exio3.reset_full()

# %% [markdown]
# We also do not need the "impact" satellite account, so we can remove that

# %%
del exio3.impacts

# %% [markdown]
# We remain with one satellite account "satellite", lets have a look:

# %%
print(exio3.satellite)

# %% [markdown]
# With over 1000 stressor names:

# %%
exio3.satellite.F


# %% [markdown]
# We are now ready to convert these stressors to GLAM flows. To do so we use the convert function of Pymrio.
# This function can be used for many more things and is [explained in detail in the notebook here](./convert.ipynb)

# TODO: remove later, just a fast way to save and load for pymrio development

EXIO3_TMP = Path(EXIOBASE_STORAGE_FOLDER / "TMP_2018")
EXIO3_TMP.mkdir(parents=True, exist_ok=True)
exio3.save_all(EXIO3_TMP, table_format="parquet")

import pyinstrument

import pymrio

exio3 = pymrio.load_all(EXIO3_TMP)
exio3.reset_all_full()

# %%
debug_bridge = exio_glam_bridge

with pyinstrument.Profiler() as p:
    debug_sat = exio3.satellite.convert(
        debug_bridge,
        new_extension_name="GLAM flows",
        unit_column_orig="EXIOBASE_unit",
        unit_column_new="FLOW_unit",
        ignore_columns=["comment"],
    )
debug_sat.F


exio3.glam_flows = exio3.satellite.convert(
    exio_glam_bridge,
    new_extension_name="GLAM flows",
    unit_column_orig="EXIOBASE_unit",
    unit_column_new="FLOW_unit",
    ignore_columns=["comment"],
)

# %% [markdown]
# This now gives us a new satellite account "glam_flows".

# %%
print(exio3.glam_flows)

# %% [markdown]
# With flow names corresponding to GLAM flows.

# %%
exio3.glam_flows.D_cba

# %% [markdown]
# ## Characterize GLAM flows

# %% [markdown]
# In the previous section we converted the EXIOBASE stressors to GLAM flows and prepared the GLAM characterization.
# With these to things in place, we can now characterize the EXIOBASE-GLAM flows with the GLAM characterization factors.
#
#

# %%
# TODO: some prep in GLAM char which needs to be implmented in pymrio

# drop all nan in uuid column
# FIX: work with Flow names instead
GLAM_char = GLAM_char.dropna(subset=["FLOW_uuid"])

# FIX: work with Flow names instead
# replace m2*y string in unit column with m2
GLAM_char.loc[:, "unit_orig"] = GLAM_char["unit_orig"].str.replace("m2*y", "m2")

# FIX: work with Flow names instead
# replace m2*y string in unit column with m2
GLAM_char.loc[:, "unit_orig"] = GLAM_char["unit_orig"].str.replace("kg emitted", "kg")

GLAM_char = GLAM_char.loc[GLAM_char.LCIAMethod_name__FLOW_uuid == "EQ Land use"]

# TODO: fix region error - use GLAM_char only with land use for that
# %%
# when debug, only one country (200 columns) and not the full dataset in there.
# must be as long as the full dataset, with 0 otherwise
exio3.glam_characterized = exio3.glam_flows.convert(
    GLAM_char, new_extension_name="GLAM characterized"
)


# %% [markdown]
# This gives us a new satellite account, based on EXIOBASE stressors characterized with the newest GLAM version:

# %%
print(exio3.glam_characterized)

# %%
exio3.glam_characterized.D_cba
