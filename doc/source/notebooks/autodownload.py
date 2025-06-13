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

# # Automatic downloading of MRIO databases

# Pymrio includes functions to automatically download some of the publicly available global EE MRIO databases.
# This is currently implemented for [EXIOBASE 3](https://doi.org/10.5281/zenodo.3583070), [OECD](https://www.oecd.org/sti/ind/inter-country-input-output-tables.htm) and [WIOD](http://www.wiod.org).

# The functions described here download the raw data files. Thus, they can also be used for post processing by other tools.

# ## EXIOBASE 3 download

# EXIOBASE 3 is licensed under the [Creative Commons Attribution ShareAlike 4.0 International-license](https://creativecommons.org/licenses/by-sa/4.0/legalcode). Thus you can use EXIOBASE 3 for analyses as well as remix, tweak, and build uponit, even commercially, as long as you give credit to the EXIOBASE compilers and share your results/new databases under the same licence. The suggested citation for EXIOBASE 3 is [Stadler et al 2018](https://doi.org/10.1111/jiec.12715). You can find more information, links to documentation as well as concordance matrices on the [EXIOBASE 3 Zenodo repository](https://doi.org/10.5281/zenodo.3583070). The download function of pymrio also downloads the files from this repository.

# To download, start with:

import pymrio

# and define a folder for storing the data:

exio3_folder = "/tmp/mrios/autodownload/EXIO3"

# With that we can start the download with (this might take a moment):

exio_downloadlog = pymrio.download_exiobase3(
    storage_folder=exio3_folder, system="pxp", years=[2011, 2012]
)

# The command above will download the latest EXIOBASE 3 tables in the product
# by product classification (system='pxp') for the years 2011 and 2012. Both
# parameters (system and years) are optional and when omitted the function will
# download all available files.

# The function returns a log of the download data (which is stored in ```download_log.json``` in the download folder).
# You can inspect the meta data by:

# + jupyter={"outputs_hidden": false}
print(exio_downloadlog)
# -

# By default, the download_exiobase3 fetches the latest version of EXIOBASE3
# available at the [EXIOBASE 3 Zenodo repository](https://doi.org/10.5281/zenodo.3583070).
# To download one of the previous versions specify the DOI with the doi
# parameter:

prev_version_storage = "/tmp/mrios/autodownload/EXIO3_7"
exio_downlog_37 = pymrio.download_exiobase3(
    storage_folder=prev_version_storage,
    system="ixi",
    years=2004,
    doi="10.5281/zenodo.3583071",
)

print(exio_downlog_37)

# We also recommend to specifiy a specific DOI version even when using the latest version of EXIOBASE. In that way the used version is documented in the code and can be reproduced in case a newer EXIOBASE version becomes available.


# ## WIOD download


# **DUE TO A RESTRUCTERING OF THE WIOD WEBPAGE THIS IS CURRENTLY BROKEN.**
#
#
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

# The OECD Inter-Country Input-Output tables (ICIO) are available on the [OECD webpage.](https://www.oecd.org/sti/ind/inter-country-input-output-tables.htm) There is no specific license given for the these tables, but the webpage state that "Data can be downloaded for free" (per June 2023) and to cite this database "OECD (2021), OECD Inter-Country Input-Output Database, http://oe.cd/icio".
#
# Currently OECD provides three versions 2016, 2018, and 2021, which are available through pymrio
#

# To download the data, we first define the folder for storing the data (these will be created if they do not exist yet):

oecd_folder_v2021 = "/tmp/mrios/autodownload/OECD_2021"
oecd_folder_v2018 = "/tmp/mrios/autodownload/OECD_2018"

# Than we can start the download with

log_2021 = pymrio.download_oecd(storage_folder=oecd_folder_v2021)

# By default, the 2021 release of the OECD - ICIO tables are downloaded.
# To retrieve other versions, simply pass "version='v&lt;version date&gt;'", for example to get the 2018 release, pass "version='v2018'" .
#
# As for WIOD, specific years can be specified by passing a list of years:

log_2018 = pymrio.download_oecd(
    storage_folder=oecd_folder_v2018, version="v2016", years=[2003, 2008]
)

# However, the 2021 release of OECD is only available in 5-year bundles starting from 1995 to 2018
# 1995-1999, 2000-2004, 2005-2009, 2010-2014, 2015-2018
#
# Therefore whenever 2021 release is used, it is recommended to pass years as a list of the wanted bundles in string forms:

log_2021 = pymrio.download_oecd(
    storage_folder=oecd_folder_v2021, years=["1995-1999", "2015-2018"]
)

# Otherwise the corresponding bundles for the entered years would be downloaded, for example if year 2003 is requested, the bundle 2000-2004 would be downloaded

log_2021 = pymrio.download_oecd(storage_folder=oecd_folder_v2021, years=[2003, 2012])

# The bundles 2000-2004 and 2010-2014 would be downloaded
# <br/>
# <br/>
# <br/>
# <br/>

# The function returns a log for the download progress and MRIO info:

print(log_2021)

# ## Eora26 download

# Eora26 provides a simplified, symmetric version of the full Eora database.
#
# Downloading the Eora data requires registration through the [Eora website (worldmrio)](http://www.worldmrio.com) .
# Currently (August 2023), open Eora26 data are only offered for the years 1990 - 2016.
#
# Therefore, you have to have the Eora account email and password in advance to use the downloader.

# Setup the download with

# + jupyter={"outputs_hidden": true}
import pymrio

eora_folder = "/tmp/mrios/eora26"
# -

# Start the download with (passing the email and password of the eora account)
# If you pass invalid email or password, you get a prompt about that and asked to enter them again, otherwise the function will download the data (this can take some minutes)
#
# This will download all available years 1990 - 2016

eora_log = pymrio.download_eora26(
    storage_folder=eora_folder,
    email="<Your Eora account email>",
    password="<Your Eora account password>",
)

# + jupyter={"outputs_hidden": false}
print(eora_log)
# -

# As in the case of the WIOD downloader, you can restrict the
#
# 1) years to download by passing ```years=[list of int or str - 4 digits]```
#
# 2) force the overwriting of existing files by passing ```overwrite_existing=True```
#
# Satellite accounts, however, can not be restricted since they are included in one file.
#
# The tables are in basic prices as it is the only price system available to download for Eora26.

# ## EXIOBASE download (previous version 1 and 2)

# Previous EXIOBASE version requires registration prior to download and therefore an automatic download has not been implemented.
# For further information check the download instruction at the [EXIOBASE example notebook.](working_with_exiobase.ipynb#Getting-EXIOBASE)

# ## GLORIA download

# The Global Resource Input Output Assessment (GLORIA) database are available to download through a dropbox folder [GLORIA database.](https://www.dropbox.com/sh/o4fxq94n7grvdbk/AABhKvEVx0UuMvz4dQ4NlWC8a?d) There is no specific licence given for the this database.
#
# Currently (as per April 2023), there are four available versions 53, 54, 55, and 57 (Release 056 was only
# distributed to a limited number of users for feedback).
#

# The download function can (as per April 2023) download all four versions

# To download, start with:

import pymrio

# Define a folder for storing the data

gloria_folder = "/tmp/mrios/autodownload/GLORIA2014"

# And start the download with (this will take a couple of minutes):

gloria_log_2014 = pymrio.download_gloria(storage_folder=gloria_folder)

# The function returns the download log data for the release (which is stored in ```download_log.json``` in the download folder).
# You can inspect the log data by:

print(gloria_log_2014)

# By default the function downloads all years for the final release (57 as per April 2023), but the year and version can be specified by passing them to the function

gloria_log_v053_2012 = pymrio.download_gloria(gloria_folder, year=2012, version=53)
