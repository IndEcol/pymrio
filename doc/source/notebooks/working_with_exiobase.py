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
# # Working with the EXIOBASE EE MRIO database

# %% [markdown]
# ## Getting EXIOBASE

# %% [markdown]
# EXIOBASE 1 (developed in the fp6 project [EXIOPOL](http://www.feem-project.net/exiopol/)), EXIOBASE 2 (outcome of the fp7 project [CREEA](http://www.creea.eu/)) and EXIOBASE 3 (outcome of the fp7 project [DESIRE](http://fp7desire.eu/)) are available on the [EXIOBASE webpage](http://www.exiobase.eu).
#
# You need to register before you can download the full dataset.
#
# Further information on the different EXIOBASE versions can be found in corresponding method papers.
#
# * EXIOBASE 1: [Tukker et al. 2013. Exiopol – Development and Illustrative Analyses of a Detailed Global MR EE SUT/IOT. Economic Systems Research 25(1), 50-70](https://doi.org/10.1080/09535314.2012.761952)
# * EXIOBASE 2: [Wood et al. 2015. Global Sustainability Accounting—Developing EXIOBASE for Multi-Regional Footprint Analysis. Sustainability 7(1), 138-163](https://doi.org/10.3390/su7010138)
# * EXIOBASE 3: [Stadler et al. 2018. EXIOBASE 3: Developing a Time Series of Detailed Environmentally Extended Multi‐Regional Input‐Output Tables. Journal of Industrial Ecology 22(3), 502-515](https://doi.org/10.1111/jiec.12715)

# %% [markdown]
# ### EXIOBASE 1

# %% [markdown]
# To download EXIOBASE 1 for the use with pymrio, navigate to the [EXIOBASE webpage]( https://www.exiobase.eu) - section(tab) "Data Download" - "[EXIOBASE 1 - full dataset](http://exiobase.eu/index.php/data-download/exiobase1-year-2000-full-data-set)" and download either
#
# - [pxp_ita_44_regions_coeff_txt](https://www.exiobase.eu/index.php/data-download/exiobase1-year-2000-full-data-set/49-pxp-ita-44-regions-coeff-txt/file) for the product by product (pxp) MRIO system or
#
# - [ixi_fpa_44_regions_coeff_txt](https://www.exiobase.eu/index.php/data-download/exiobase1-year-2000-full-data-set/25-ixi-fpa-44-regions-coeff-txt/file) for the industry by industry (ixi) MRIO system or
#
# - [pxp_ita_44_regions_coeff_src_txt](https://www.exiobase.eu/index.php/data-download/exiobase1-year-2000-full-data-set/52-pxp-ita-44-regions-coeff-src-txt/file) for the product by product (pxp) MRIO system with emission data per source or
#
# - [ixi_fpa_44_regions_coeff_src_txt](https://www.exiobase.eu/index.php/data-download/exiobase1-year-2000-full-data-set/28-ixi-fpa-44-regions-coeff-src-txt/file) for the industry by industry (ixi) wMRIO system with emission data per source.
#
# The links above directly lead to the required file(s), but remember that you need to be logged in to access them.

# %% [markdown]
# The Pymrio parser works with the compressed (zip) files as well as the unpacked files. If you want to unpack the files, make sure that you store them in different folders since they unpack in the current directory.

# %% [markdown]
# ### EXIOBASE 2

# %% [markdown]
# EXIOBASE 3 is available at the [EXIOBASE webpage](http://www.exiobase.eu) at the section (tab) tab "Data Download" - "[EXIOBASE 2 - full dataset](http://exiobase.eu/index.php/data-download/exiobase2-year-2007-full-data-set)".
#
# You can download either
#
#
# - [MrIOT PxP ita coefficient version2 2 2](http://www.exiobase.eu/index.php/data-download/exiobase2-year-2007-full-data-set/79-mriot-pxp-ita-coefficient-version2-2-2/file) for the product by product (pxp) MRIO system or
#
# - [MrIOT IxI fpa coefficient version2 2 2](http://www.exiobase.eu/index.php/data-download/exiobase2-year-2007-full-data-set/78-mriot-ixi-fpa-coefficient-version2-2-2/file) for the industry by industry (ixi) MRIO system.
#
# The links above directly lead to the required file(s), but remember that you need to be logged in to access them.
#
# The pymrio parser works with the compressed (zip) files as well as the unpacked files. You can unpack the files together in one directory (unpacking creates a separate folder for each EXIOBASE 2 version). The unpacking of the PxP version also creates a folder "__MACOSX" - you can delete this folder.

# %% [markdown]
# ### EXIOBASE 3

# %% [markdown]
# EXIOBASE 3 is available at the [EXIOBASE webpage](http://www.exiobase.eu) at the section (tab) tab "Data Download" - "[EXIOBASE 3 - monetary](http://exiobase.eu/index.php/data-download/exiobase3mon)".
# The EXIOBASE 3 parser works with both, the compressed zip archives and the extracted database.
#

# %% [markdown]
# ## Parsing

# %%
import pymrio

# %% [markdown]
# For each publically available version of EXIOBASE pymrio provides a specific parser.
# All exiobase parser work with the zip archive (as downloaded from the exiobase webpage) or the extracted data.

# %% [markdown]
# To parse **EXIOBASE 1** use:

# %% jupyter={"outputs_hidden": false}
exio1 = pymrio.parse_exiobase1(
    path="/tmp/mrios/exio1/zip/121016_EXIOBASE_pxp_ita_44_regions_coeff_txt.zip"
)

# %% [markdown]
# The parameter 'path' needs to point to either the folder with the extracted EXIOBASE1 files for the downloaded zip archive.

# %% [markdown]
# Similarly, **EXIOBASE 2** can be parsed by:

# %%
exio2 = pymrio.parse_exiobase2(
    path="/tmp/mrios/exio2/zip/mrIOT_PxP_ita_coefficient_version2.2.2.zip",
    charact=True,
    popvector="exio2",
)

# %% [markdown]
# The additional parameter 'charact' specifies if the characterization matrix provided with EXIOBASE 2 should be used. This can be specified with True or False; in addition, a custom one can be provided. In the latter case, pass the full path to the custom characterisatio file to 'charact'.
#
# The parameter 'popvector' allows to pass information about the population per EXIOBASE2 country. This can either be a custom vector of, if 'exio2' is passed, the one provided with pymrio.

# %% [markdown]
# **EXIOBASE 3** can be parsed by:

# %%
exio3 = pymrio.parse_exiobase3(path="/tmp/mrios/exio3/zip/exiobase3.4_iot_2009_pxp.zip")

# %% [markdown]
# Currently, no characterization or population vectors are provided for EXIOBASE 3.

# %% [markdown]
# For the rest of the tutorial, we use *exio2*; deleting *exio1* and *exio3* to free some memory:

# %% jupyter={"outputs_hidden": false}
del exio1
del exio3

# %% [markdown]
# ## Exploring EXIOBASE

# %% [markdown]
# After parsing a EXIOBASE version, the handling of the database is the same as for any IO.
# Here we use the parsed EXIOBASE2 to explore some characteristics of the EXIBOASE system.
#
# After reading the raw files, metadata about EXIOBASE can be accessed within the meta field:

# %% jupyter={"outputs_hidden": false}
exio2.meta

# %% [markdown]
# Custom points can be added to the history in the meta record. For example:

# %% jupyter={"outputs_hidden": false}
exio2.meta.note("First test run of EXIOBASE 2")
exio2.meta

# %% [markdown]
# To check for sectors, regions and extensions:

# %% jupyter={"outputs_hidden": false}
exio2.get_sectors()

# %% jupyter={"outputs_hidden": false}
exio2.get_regions()

# %% jupyter={"outputs_hidden": false}
list(exio2.get_extensions())

# %% [markdown]
# ## Calculating the system and extension results

# %% [markdown]
# The following command checks for missing parts in the system and calculates them. In case of the parsed EXIOBASE this includes A, L, multipliers M, footprint accounts, ..

# %% jupyter={"outputs_hidden": false}
exio2.calc_all()

# %% [markdown]
# ## Exploring the results

# %% jupyter={"outputs_hidden": false}
import matplotlib.pyplot as plt

plt.figure(figsize=(15, 15))
plt.imshow(exio2.A, vmax=1e-3)
plt.xlabel("Countries - sectors")
plt.ylabel("Countries - sectors")
plt.show()

# %% [markdown]
# The available impact data can be checked with:

# %% jupyter={"outputs_hidden": false}
list(exio2.impact.get_rows())

# %% [markdown]
# And to get for example the footprint of a specific impact do:

# %% jupyter={"outputs_hidden": false}
print(exio2.impact.unit.loc["global warming (GWP100)"])
exio2.impact.D_cba_reg.loc["global warming (GWP100)"]

# %% [markdown]
# ## Visualizing the data

# %% jupyter={"outputs_hidden": false}
with plt.style.context("ggplot"):
    exio2.impact.plot_account(["global warming (GWP100)"], figsize=(15, 10))
    plt.show()

# %% [markdown]
# See the other notebooks for further information on [aggregation](../notebooks/aggregation_examples.ipynb) and [file io](../notebooks/load_save_export.ipynb).
