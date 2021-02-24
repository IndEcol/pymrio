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

# # Automatic downloading of MRIO databases

# Pymrio includes functions to automatically download some of the publicly available global EE MRIO databases.
# This is currently implemented for [EXIOBASE 3](https://doi.org/10.5281/zenodo.3583070), [OECD](https://www.oecd.org/sti/ind/inter-country-input-output-tables.htm) and [WIOD](http://www.wiod.org).

# The functions described here download the raw data files. Thus, they can also be used for post processing by other tools.

# ## EXIOBASE 3 download

# EXIOBASE 3 is licensed under the [Creative Commons Attribution 4.0 International-license](http://creativecommons.org/licenses/by/4.0/). Thus you can remix, tweak, and build upon EXIOBASE 3, even commercially, as long as you give credit to the EXIOBASE compilers. The suggested citation for EXIOBASE 3 is [Stadler et al 2018](https://doi.org/10.1111/jiec.12715). You can find more information, links to documentation as well as concordance matrices on the [EXIOBASE 3 Zenodo repository](https://doi.org/10.5281/zenodo.3583070). The download function of pymrio also downloads the files from this repository.

# To download, start with:

import pymrio

# and define a folder for storing the data:

exio3_folder = "/tmp/mrios/autodownload/EXIO3"

# With that we can start the download with (this might take a moment):

exio_meta = pymrio.download_exiobase3(
    storage_folder=exio3_folder, system="pxp", years=[2011, 2012]
)

# The command above will download the latest EXIOBASE 3 tables in the product
# by product classification (system='pxp') for the years 2011 and 2012. Both
# parameters (system and years) are optional and when omitted the function will
# download all available files.

# The function returns the meta data for the release (which is stored in ```metadata.json``` in the download folder).
# You can inspect the meta data by:

# + jupyter={"outputs_hidden": false}
print(exio_meta)
# -

# By default, the download_exiobase3 fetches the latest version of EXIOBASE3
# available at the [EXIOBASE 3 Zenodo repository](https://doi.org/10.5281/zenodo.3583070).
# To download one of the previous versions specify the DOI with the doi
# parameter:

prev_version_storage = "/tmp/mrios/autodownload/EXIO3_7"
exio_meta_37 = pymrio.download_exiobase3(
    storage_folder=prev_version_storage,
    system="ixi",
    years=2004,
    doi="10.5281/zenodo.3583071",
)

print(exio_meta_37)

# Currently (Feb 2021), the following versions are available. Please
# double-check at the [EXIOBASE 3 Zenodo
# repository](https://doi.org/10.5281/zenodo.3583070) (a box at the left
# sidebar titled 'Versions')
#
# - Version 3.7: 10.5281/zenodo.3583071 (only ixi files from 1995 to 2011 are
# available)
# - Version 3.8: 10.5281/zenodo.4277368


# ## WIOD download


# WIOD is licensed under the [Creative Commons Attribution 4.0 International-license](http://creativecommons.org/licenses/by/4.0/). Thus you can remix, tweak, and build upon WIOD, even commercially, as long as you give credit to WIOD. The WIOD web-page suggest to cite [Timmer et al. 2015](http://doi.wiley.com/10.1111/roie.12178) when you use the database. You can find more information on the [WIOD webpage](http://www.wiod.org).

# The download function for WIOD currently processes the [2013 release version of WIOD](http://www.wiod.org/database/wiots13).

# To download, start with:

import pymrio

# Define a folder for storing the data

wiod_folder = "/tmp/mrios/autodownload/WIOD2013"

# And start the download with (this will take a couple of minutes):

wiod_meta = pymrio.download_wiod2013(storage_folder=wiod_folder)

# The function returns the meta data for the release (which is stored in ```metadata.json``` in the download folder).
# You can inspect the meta data by:

# + jupyter={"outputs_hidden": false}
print(wiod_meta)
# -

# The WIOD database provide data for several years and satellite accounts.
# In the default case, all of them are downloaded. You can, however, specify
# years and satellite account.

# You can specify the years as either int or string (2 or 4 digits):

res_years = [97, 2004, "2005"]

# The available satellite accounts for WIOD are listed in the ```WIOD_CONFIG```.
# To get them import this dict by:

from pymrio.tools.iodownloader import WIOD_CONFIG

# + jupyter={"outputs_hidden": false}
WIOD_CONFIG
# -

# To restrict this list, you can either copy paste the urls or automatically select the accounts:

sat_accounts = ["EU", "CO2"]
res_satellite = [
    sat
    for sat in WIOD_CONFIG["satellite_urls"]
    if any(acc in sat for acc in sat_accounts)
]

# + jupyter={"outputs_hidden": false}
res_satellite
# -

wiod_meta_res = pymrio.download_wiod2013(
    storage_folder="/tmp/foo_folder/WIOD2013_res",
    years=res_years,
    satellite_urls=res_satellite,
)

# + jupyter={"outputs_hidden": false}
print(wiod_meta_res)
# -

# Subsequent download will only catch files currently not present in the folder, e.g.:

additional_years = [2000, 2001]
wiod_meta_res = pymrio.download_wiod2013(
    storage_folder="/tmp/foo_folder/WIOD2013_res",
    years=res_years + additional_years,
    satellite_urls=res_satellite,
)

# only downloads the years given in ```additional_years```, appending these downloads to the meta data file.

# + jupyter={"outputs_hidden": false}
print(wiod_meta_res)
# -

# To catch all files, irrespective if present in the storage_folder or not pass ```overwrite_existing=True```

# ## OECD download

# The OECD Inter-Country Input-Output tables (ICIO) are available on the [OECD webpage.](https://www.oecd.org/sti/ind/inter-country-input-output-tables.htm) There is no specific licence given for the these tables, but the webpage state that "Data can be downloaded for free" (per July 2019).
#
# The download function works for both, the 2016 and 2018 release.
#

# To download the data, we first define the folder for storing the data (these will be created if they do not exist yet):

oecd_folder_v2018 = "/tmp/mrios/autodownload/OECD_2018"
oecd_folder_v2016 = "/tmp/mrios/autodownload/OECD_2016"

# Than we can start the download with

meta_2018 = pymrio.download_oecd(storage_folder=oecd_folder_v2018)

# Be default, the 2018 release of the OECD - ICIO tables are downloaded.
# To retrieve the 2016 version, pass "version='v2016".
#
# As for WIOD, specific years can be specified by passing a list of years:

meta_2016 = pymrio.download_oecd(
    storage_folder=oecd_folder_v2016, version="v2016", years=[2003, 2008]
)

# Both functions return the meta data describing the download progress and MRIO info. Thus:

print(meta_2018)

# ## Eora26 download

# Eora26 requires registration prior to download and therefore an automatic download has not been implemented.
# For further information check the download instruction at the [Eora26 example notebook.](working_with_eora26.ipynb#Getting-Eora26)

# ## EXIOBASE download (previous version 1 and 2)

# Previous EXIOBASE version requires registration prior to download and therefore an automatic download has not been implemented.
# For further information check the download instruction at the [EXIOBASE example notebook.](working_with_exiobase.ipynb#Getting-EXIOBASE)
