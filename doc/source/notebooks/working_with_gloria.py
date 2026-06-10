# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Working with the GLORIA database

# %% [markdown]
# ## UPDATE: 
#
# The GLORIA database is now licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International licence (CC BY-NC-SA 4.0).
#
# Access to recent GLORIA releases is now managed externally and now longer available through the GLORIA dropbox folder. At present, we cannot confirm whether the existing pymrio parser works with the latest GLORIA data format or access mechanism.
#
# Contributions are welcome. If you have access to the current GLORIA release and can update or verify the parser, please consider opening a pull request with the necessary parsing changes and documentation updates. The latest confirmed versions working with the parser are 53, 54, 55, 57 and 59.

# %% [markdown]
# ## Getting GLORIA

# %% [markdown]
# **Accessing GLORIA data**
#
# GLORIA data must be downloaded manually. To request access and download the database, visit the IELab GLORIA page:
#
# https://ielab.info/labs/ielab-gloria
#
# After downloading the required files, place them in the location expected by the pymrio GLORIA parser before running the parser locally.
#

# %% [markdown]
# ## Parsing

# %%
import pymrio
gloria = pymrio.parse_gloria(
    path="/tmp/mrios/autodownload/GLORIA2014/", version=59, year=2014
)

# %% [markdown]
# ## Exploring GLORIA

# %% [markdown]
# After parsing a GLORIA version, the handling of the database is the same as for any IO. 

# %% jupyter={"outputs_hidden": false}
gloria.meta

# %% [markdown]
# To check for sectors, regions and extensions:

# %% jupyter={"outputs_hidden": false}
gloria.get_sectors()

# %% jupyter={"outputs_hidden": false}
gloria.get_regions()

# %% [markdown]
# Currently, the parser includes value added and the satellite data from GLORIA, ie material use, EDGAR emissions and OECD emissions. 

# %% jupyter={"outputs_hidden": false}
list(gloria.get_extensions())

# %% [markdown]
# ## Calculating the system and extension results

# %% [markdown]
# The following command checks for missing parts in the system and calculates them. In case of the parsed GLORIA this includes Z, L, multipliers, footprint accounts, ..

# %% jupyter={"outputs_hidden": false}
gloria.calc_all()

# %% [markdown]
# ## Exploring the results

# %% jupyter={"outputs_hidden": false}
import matplotlib.pyplot as plt

plt.figure(figsize=(15, 15))
plt.imshow(gloria.A, vmax=1e-3)
plt.xlabel("Countries - sectors")
plt.ylabel("Countries - sectors")
plt.show()

# %% [markdown]
# The available impact data can be checked with:

# %% jupyter={"outputs_hidden": false}
list(gloria.Q.get_rows())

# %% [markdown]
# And to get for example the footprint of a specific impact do:

# %% jupyter={"outputs_hidden": false}
print(gloria.Q.unit.loc["'GHG_total_EDGAR_consistent'"])
gloria.Q.D_cba_reg.loc["'GHG_total_EDGAR_consistent'"]

# %% [markdown]
# ## Visualizing the data

# %% jupyter={"outputs_hidden": false}
with plt.style.context("ggplot"):
    gloria.Q.plot_account(["'GHG_total_EDGAR_consistent'"], figsize=(15, 10))
    plt.show()

# %% [markdown]
# See the other notebooks for further information on [aggregation](../notebooks/aggregation_examples.ipynb) and [file io](../notebooks/load_save_export.ipynb).
