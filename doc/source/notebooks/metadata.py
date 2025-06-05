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
# # Metadata and change recording

# %% [markdown]
# **DEPRECATED**: this will be removed and changed to loguru soon

# %% [markdown]
# Each pymrio core system object contains a field 'meta' which stores meta data as well as changes to the MRIO system. This data is stored as json file in the root of a saved MRIO data and accessible through the attribute '.meta':

# %%
import pymrio

io = pymrio.load_test()

# %%
io.meta

# %%
io.meta("Loaded the pymrio test system")

# %% [markdown]
# We can now do several steps to modify the system, for example:

# %%
io.calc_all()
io.aggregate(region_agg="global")

# %%
io.meta

# %% [markdown]
# Notes can added at any time:

# %%
io.meta.note("First round of calculations finished")

# %%
io.meta

# %% [markdown]
# In addition, all file io operations are recorde in the meta data:

# %%
io.save_all("/tmp/foo")

# %%
io_new = pymrio.load_all("/tmp/foo")

# %%
io_new.meta

# %% [markdown]
# The top level meta data can be changed as well. These changes will also be recorded in the history:

# %%
io_new.meta.change_meta("Version", "v2")

# %%
io_new.meta

# %% [markdown]
# To get the full history list, use:

# %%
io_new.meta.history

# %% [markdown]
# This can be restricted to one of the history types by:

# %%
io_new.meta.modification_history

# %% [markdown]
# or

# %%
io_new.meta.note_history
