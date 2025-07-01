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
# # Loading, saving and exporting data

# %% [markdown]
# Pymrio includes several functions for data reading and storing. This section presents the methods to use for saving and loading data already in a pymrio compatible format. For parsing raw MRIO data see the different tutorials for [working with available MRIO databases](../handling.rst).

# %% [markdown]
# Here, we use the included small test MRIO system to highlight the different function. The same functions are available for any MRIO loaded into pymrio. Expect, however, significantly decreased performance due to the size of real MRIO system.

import os

# %%
import pymrio

io = pymrio.load_test().calc_all()

# %% [markdown]
# ## Basic save and read

# %% [markdown]
# To save the full system, use:

# %%
save_folder_full = "/tmp/testmrio/full"
io.save_all(path=save_folder_full)

# %% [markdown]
# To read again from that folder do:

# %%
io_read = pymrio.load_all(path=save_folder_full)

# %% [markdown]
# The fileio activities are stored in the included meta data history field:

# %%
io_read.meta

# %% [markdown]
# ## Storage format

# %% [markdown]
# Internally, pymrio stores data in csv format, with the 'economic core' data in the root and each satellite account in a subfolder. Metadata as file as a file describing the data format ('file_parameters.json') are included in each folder.

# %%

os.listdir(save_folder_full)

# %% [markdown]
# The file format for storing the MRIO data can be switched to a binary pickle format with:

# %%
save_folder_bin = "/tmp/testmrio/binary"
io.save_all(path=save_folder_bin, table_format="pkl")
os.listdir(save_folder_bin)

# %% [markdown]
# This can be used to reduce the storage space required on the disk for large MRIO databases.

# %% [markdown]
# ## Archiving MRIOs databases

# %% [markdown]
# To archive a MRIO system after saving use pymrio.archive:

# %%
mrio_arc = "/tmp/testmrio/archive.zip"

# Remove a potentially existing archive from before
try:
    os.remove(mrio_arc)
except FileNotFoundError:
    pass

pymrio.archive(source=save_folder_full, archive=mrio_arc)

# %% [markdown]
# Data can be read directly from such an archive by:

# %%
tt = pymrio.load_all(mrio_arc)

# %% [markdown]
# Currently data can not be saved directly into a zip archive.
# It is, however, possible to remove the source files after archiving:

# %%
tmp_save = "/tmp/testmrio/tmp"

# Remove a potentially existing archive from before
try:
    os.remove(mrio_arc)
except FileNotFoundError:
    pass

io.save_all(tmp_save)

print("Directories before archiving: {}".format(os.listdir("/tmp/testmrio")))
pymrio.archive(source=tmp_save, archive=mrio_arc, remove_source=True)
print("Directories after archiving: {}".format(os.listdir("/tmp/testmrio")))

# %% [markdown]
# Several MRIO databases can be stored in the same archive:

# %%
# Remove a potentially existing archive from before
try:
    os.remove(mrio_arc)
except FileNotFoundError:
    pass

tmp_save = "/tmp/testmrio/tmp"

io.save_all(tmp_save)
pymrio.archive(
    source=tmp_save, archive=mrio_arc, path_in_arc="version1/", remove_source=True
)
io2 = io.copy()
del io2.emissions
io2.save_all(tmp_save)
pymrio.archive(
    source=tmp_save, archive=mrio_arc, path_in_arc="version2/", remove_source=True
)

# %% [markdown]
# When loading from an archive which includes multiple MRIO databases, specify
# one with the parameter 'path_in_arc':

# %%
io1_load = pymrio.load_all(mrio_arc, path_in_arc="version1/")
io2_load = pymrio.load_all(mrio_arc, path_in_arc="version2/")

print(
    f"Extensions of the loaded io1 {sorted(io1_load.get_extensions())} and of io2: {sorted(io2_load.get_extensions())}"
)

# %% [markdown]
# The pymrio.load function can be used directly to only a specific satellite account
# of a MRIO database from a zip archive:

# %%
emissions = pymrio.load(mrio_arc, path_in_arc="version1/emissions")
print(emissions)

# %% [markdown]
# The archive function is a wrapper around python.zipfile module.
# There are, however, some differences to the defaults choosen in the original:
#
# -  In contrast to [zipfile.write](https://docs.python.org/3/library/zipfile.html),
#    pymrio.archive raises an
#    error if the data (path + filename) are identical in the zip archive.
#    Background: the zip standard allows that files with the same name and path
#    are stored side by side in a zip file. This becomes an issue when unpacking
#    this files as they overwrite each other upon extraction.
#
# -  The standard for the parameter 'compression' is set to ZIP_DEFLATED
#    This is different from the zipfile default (ZIP_STORED) which would
#    not give any compression.
#    See the [zipfile docs](https://docs.python.org/3/library/zipfile.html#zipfile-objects)
#    for further information.
#    Depending on the value given for the parameter 'compression'
#    additional modules might be necessary (e.g. zlib for ZIP_DEFLATED).
#    Futher information on this can also be found in the zipfile python docs.

# %% [markdown]
# ## Storing or exporting a specific table or extension

# %% [markdown]
# Each extension of the MRIO system can be stored separetly with:

# %%
save_folder_em = "/tmp/testmrio/emissions"

# %%
io.emissions.save(path=save_folder_em)

# %% [markdown]
# This can then be loaded again as separate satellite account:

# %%
emissions = pymrio.load(save_folder_em)

# %%
emissions

# %%
emissions.D_cba

# %% [markdown]
# As all data in pymrio is stored as [pandas DataFrame](https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html), the full pandas stack for exporting tables is available. For example, to export a table as excel sheet use:

# %%
io.emissions.D_cba.to_excel("/tmp/testmrio/emission_footprints.xlsx")

# %% [markdown]
# For further information see the pandas [documentation on import/export](https://pandas.pydata.org/pandas-docs/stable/io.html).
