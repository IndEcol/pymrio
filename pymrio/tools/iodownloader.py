""" Utility functions for automatic downloading of public MRIO databases
"""

import itertools
import os
import re
from collections import namedtuple

import requests

from pymrio.tools.iometadata import MRIOMetaData

WIOD_CONFIG = {
    "url_db_view": "http://www.wiod.org/database/wiots13",
    "url_db_content": "http://www.wiod.org/",
    "mrio_regex": r"protected.*?wiot\d\d.*?xlsx",
    "satellite_urls": [
        "http://www.wiod.org/protected3/data13/SEA/WIOD_SEA_July14.xlsx",
        "http://www.wiod.org/protected3/data13/EU/EU_may12.zip",
        "http://www.wiod.org/protected3/data13/EM/EM_may12.zip",
        "http://www.wiod.org/protected3/data13/CO2/CO2_may12.zip",
        "http://www.wiod.org/protected3/data13/AIR/AIR_may12.zip",
        "http://www.wiod.org/protected3/data13/land/lan_may12.zip",
        "http://www.wiod.org/protected3/data13/materials/mat_may12.zip",
        "http://www.wiod.org/protected3/data13/water/wat_may12.zip",
    ],
}

EORA26_CONFIG = {
    "url_db_view": "http://worldmrio.com/simplified/",
    "url_db_content": "http://worldmrio.com/",
}

EXIOBASE3_CONFIG = {
    "url_db_view": "https://doi.org/10.5281/zenodo.3583070",  # lastest version
    # "url_db_view": "https://doi.org/10.5281/zenodo.3583071",  # version 3.7
    # "url_db_view": "https://doi.org/10.5281/zenodo.4277368",  # version 3.8
    "url_db_content": "",
    "mrio_regex": r"https://zenodo.org/record/\d*/files/IOT_\d\d\d\d_[p,i]x[p,i].zip",
    "requests_func": requests.get,
}


OECD_CONFIG = {
    "url_db_view": "https://www.oecd.org/sti/ind/inter-country-input-output-tables.htm",  # NOQA
    "url_db_content": "https://www.oecd.org/sti/ind/",
    "mrio_regex": r"ICIO\d\d\d\d_\d\d\d\d\.zip",
    "datafiles": {
        "v2016": {
            "1995": "https://www.oecd.org/sti/ind/ICIO2016_1995.zip",
            "1996": "https://www.oecd.org/sti/ind/ICIO2016_1996.zip",
            "1997": "https://www.oecd.org/sti/ind/ICIO2016_1997.zip",
            "1998": "https://www.oecd.org/sti/ind/ICIO2016_1998.zip",
            "1999": "https://www.oecd.org/sti/ind/ICIO2016_1999.zip",
            "2000": "https://www.oecd.org/sti/ind/ICIO2016_2000.zip",
            "2001": "https://www.oecd.org/sti/ind/ICIO2016_2001.zip",
            "2002": "https://www.oecd.org/sti/ind/ICIO2016_2002.zip",
            "2003": "https://www.oecd.org/sti/ind/ICIO2016_2003.zip",
            "2004": "https://www.oecd.org/sti/ind/ICIO2016_2004.zip",
            "2005": "https://www.oecd.org/sti/ind/ICIO2016_2005.zip",
            "2006": "https://www.oecd.org/sti/ind/ICIO2016_2006.zip",
            "2007": "https://www.oecd.org/sti/ind/ICIO2016_2007.zip",
            "2008": "https://www.oecd.org/sti/ind/ICIO2016_2008.zip",
            "2009": "https://www.oecd.org/sti/ind/ICIO2016_2009.zip",
            "2010": "https://www.oecd.org/sti/ind/ICIO2016_2010.zip",
            "2011": "https://www.oecd.org/sti/ind/ICIO2016_2011.zip",
        },
        "v2018": {
            "2005": "http://stats.oecd.org/wbos/fileview2.aspx?IDFile=1f134869-1820-49ce-b8b8-3973ec8db607",  # NOQA
            "2006": "http://stats.oecd.org/wbos/fileview2.aspx?IDFile=da62c835-f4fa-4450-bf19-1dd60f88a385",  # NOQA
            "2007": "http://stats.oecd.org/wbos/fileview2.aspx?IDFile=c4d4c21d-00db-48d8-9f9a-f722fcdca494",  # NOQA
            "2008": "http://stats.oecd.org/wbos/fileview2.aspx?IDFile=1fd2fc03-c140-46f4-818e-9a66b671ff70",  # NOQA
            "2009": "http://stats.oecd.org/wbos/fileview2.aspx?IDFile=4cc79090-d1ee-48b6-a252-e75312d32a1c",  # NOQA
            "2010": "http://stats.oecd.org/wbos/fileview2.aspx?IDFile=16d04830-3c27-47a5-bc03-e429d27f585e",  # NOQA
            "2011": "http://stats.oecd.org/wbos/fileview2.aspx?IDFile=dc48c8c0-f200-487a-aecb-0c2c17fe3ddf",  # NOQA
            "2012": "http://stats.oecd.org/wbos/fileview2.aspx?IDFile=cfd03495-8a90-4449-8097-a30f06853cab",  # NOQA
            "2013": "http://stats.oecd.org/wbos/fileview2.aspx?IDFile=8c8ac674-1b6c-4c8e-94d1-158f06285659",  # NOQA
            "2014": "http://stats.oecd.org/wbos/fileview2.aspx?IDFile=0190bd9d-31d0-4171-bd1c-82d96b88e469",  # NOQA
            "2015": "http://stats.oecd.org/wbos/fileview2.aspx?IDFile=9f579ef3-4685-45e4-a0ba-d1acbd9755a6",  # NOQA
        },
    },
}


def _get_url_datafiles(
    url_db_view,
    url_db_content,
    mrio_regex,
    access_cookie=None,
    requests_func=requests.post,
):
    """Urls of mrio files by parsing url content for mrio_regex

    Parameters
    ----------

    url_db_view: url str
        Url which shows the list of mrios in the db

    url_db_content: url str
        Url which needs to be appended before the url parsed from the
        url_db_view to get a valid download link

    mrio_regex: regex str
        Regex to parse the mrio datafile from url_db_view

    access_cookie: dict, optional
        If needed, cookie to access the database

    requests_func: function
        Function to use for retrieving the url content.
        Can be requests.get or requests.post

    Returns
    -------
    Named tuple:
    .raw_text: content of url_db_view for later use
    .data_urls: list of url

    """
    # Use post here - NB: get could be necessary for some other pages
    # but currently works for wiod and eora
    returnvalue = namedtuple("url_content", ["raw_text", "data_urls"])
    url_text = requests_func(url_db_view, cookies=access_cookie).text
    data_urls = [url_db_content + ff for ff in re.findall(mrio_regex, url_text)]
    return returnvalue(raw_text=url_text, data_urls=data_urls)


def _download_urls(
    url_list, storage_folder, overwrite_existing, meta_handler, access_cookie=None
):
    """Save url from url_list to storage_folder

    Parameters
    ----------
    url_list: list of str
        Valid url to download

    storage_folder: str, valid path
        Location to store the download, folder will be created if
        not existing. If the file is already present in the folder,
        the download depends on the setting in 'overwrite_existing'.

    overwrite_existing: boolean, optional
        If False, skip download of file already existing in
        the storage folder (default). Set to True to replace
        files.

    meta_handler: instance of MRIOMetaData

    access_cookie: cookie, optional
        Cookie to be passed to the requests.post function fetching the data


    Returns
    -------

    The meta_handler is passed back

    """
    for url in url_list:
        filename = os.path.basename(url)
        if not overwrite_existing and filename in os.listdir(storage_folder):
            continue
        storage_file = os.path.join(storage_folder, filename)

        # Using requests here - tried with aiohttp but was actually slower
        # Also don’t use shutil.copyfileobj - corrupts zips from Eora
        # req = requests.post(url, stream=True, cookies=access_cookie)
        req = requests.get(url, stream=True, cookies=access_cookie)
        with open(storage_file, "wb") as lf:
            for chunk in req.iter_content(1024 * 5):
                lf.write(chunk)

        meta_handler._add_fileio("Downloaded {} to {}".format(url, filename))
        meta_handler.save()

    return meta_handler


def download_oecd(
    storage_folder, version="v2018", years=None, overwrite_existing=False
):
    """Downloads the OECD ICIO tables

    Parameters
    ----------
    storage_folder: str, valid path
        Location to store the download, folder will be created if
        not existing. If the file is already present in the folder,
        the download of the specific file will be skipped.

    version: string or int, optional
        Two versions of the ICIO OECD tables are currently availabe:
        Version >v2016<: based on >SNA93< / >ISIC Rev.3<
        Version >v2018<: based on >SNA08< / >ISIC Rev.4< (default)
        Pass any of the identifiers between >< to specifiy the
        version to be downloaded.

    years: list of int (4 digit) or str, optional
        If years is given only downloads the specific years.

    overwrite_existing: boolean, optional
        If False, skip download of file already existing in
        the storage folder (default). Set to True to replace
        files.

    Returns
    -------

    Meta data of the downloaded MRIOs

    """
    # Implementation Notes:
    # For OECD the generic download routines can not be used
    # b/c the 2018 version is coded as aspx fileview property
    # in the html source - instead a hardcoded dict is used
    # to select the url for download

    os.makedirs(storage_folder, exist_ok=True)

    if type(version) is int:
        version = str(version)

    if ("8" in version) or ("4" in version):
        version = "v2018"
    elif ("3" in version) or ("6" in version):
        version = "v2016"
    else:
        raise ValueError("Version not understood")

    if type(years) is int or type(years) is str:
        years = [years]
    if not years:
        if version == "v2018":
            years = range(2005, 2016)
        else:
            years = range(1995, 2012)
    years = [str(yy) for yy in years]

    meta = MRIOMetaData(
        location=storage_folder,
        description="OECD-ICIO download",
        name="OECD-ICIO",
        system="IxI",
        version=version,
    )

    oecd_webcontent = requests.get(OECD_CONFIG["url_db_view"]).text
    for yy in years:
        if yy not in OECD_CONFIG["datafiles"][version].keys():
            raise ValueError("Datafile for {} not specified or available.".format(yy))
        if version == "v2016":
            url_to_check = os.path.basename(OECD_CONFIG["datafiles"][version][yy])
        else:
            url_to_check = OECD_CONFIG["datafiles"][version][yy]
        if url_to_check not in oecd_webcontent:
            raise ValueError(
                "Specified datafile for {} () not found in the current"
                "OECD ICIO webpage.\n"
                "Perhaps filenames have been changed - update OECD_CONFIG "
                "to the new filenames".format(yy, url_to_check)
            )

        filename = "ICIO" + version.lstrip("v") + "_" + yy + ".zip"
        storage_file = os.path.join(storage_folder, filename)
        req = requests.get(OECD_CONFIG["datafiles"][version][yy], stream=True)
        with open(storage_file, "wb") as lf:
            for chunk in req.iter_content(1024 * 5):
                lf.write(chunk)

        meta._add_fileio(
            "Downloaded {} to {}".format(
                OECD_CONFIG["datafiles"][version][yy], filename
            )
        )

    meta.save()
    return meta


def download_wiod2013(
    storage_folder,
    years=None,
    overwrite_existing=False,
    satellite_urls=WIOD_CONFIG["satellite_urls"],
):
    """Downloads the 2013 wiod release

    Note
    ----
    Currently, pymrio only works with the 2013 release of the wiod tables. The
    more recent 2016 release so far (October 2017) lacks the environmental and
    social extensions.


    Parameters
    ----------
    storage_folder: str, valid path
        Location to store the download, folder will be created if
        not existing. If the file is already present in the folder,
        the download of the specific file will be skipped.


    years: list of int or str, optional
        If years is given only downloads the specific years. This
        only applies to the IO tables because extensions are stored
        by country and not per year.
        The years can be given in 2 or 4 digits.

    overwrite_existing: boolean, optional
        If False, skip download of file already existing in
        the storage folder (default). Set to True to replace
        files.

    satellite_urls : list of str (urls), optional
        Which satellite accounts to download.  Default: satellite urls defined
        in WIOD_CONFIG - list of all available urls Remove items from this list
        to only download a subset of extensions

    Returns
    -------

    Meta data of the downloaded MRIOs

    """

    os.makedirs(storage_folder, exist_ok=True)

    if type(years) is int or type(years) is str:
        years = [years]
    years = years if years else range(1995, 2012)
    years = [str(yy).zfill(2)[-2:] for yy in years]

    wiod_web_content = _get_url_datafiles(
        url_db_view=WIOD_CONFIG["url_db_view"],
        url_db_content=WIOD_CONFIG["url_db_content"],
        mrio_regex=WIOD_CONFIG["mrio_regex"],
    )

    restricted_wiod_io_urls = [
        url
        for url in wiod_web_content.data_urls
        if re.search(r"(wiot)(\d\d)", os.path.basename(url)).group(2) in years
    ]

    meta = MRIOMetaData(
        location=storage_folder,
        description="WIOD metadata file for pymrio",
        name="WIOD",
        system="IxI",
        version="data13",
    )

    meta = _download_urls(
        url_list=restricted_wiod_io_urls + satellite_urls,
        storage_folder=storage_folder,
        overwrite_existing=overwrite_existing,
        meta_handler=meta,
    )

    meta.save()
    return meta


def download_eora26():
    """Downloading eora26 not implemented (registration required)"""
    raise NotImplementedError(
        "Eora26 3 requires registration prior to download. "
        "Please register at http://www.worldmrio.com and download the "
        "Eora26 files from the subdomain /simplified"
    )
    return None

    # Development note:
    # Eora 26 autodownload was implemented before but was
    # removed since worldmrio does require
    # a registration now (by summer 2018).
    # The previous implementation can be found
    # in the github history (e.g. at 2e61424 2018-10-09
    # or before)


def download_exiobase1():
    """Downloading exiobase not implemented (registration required)"""
    raise NotImplementedError(
        "EXIOBASE 1 requires registration prior to download. "
        "Please register at www.exiobase.eu and download the "
        "EXIOBASE MRIO files "
        "pxp_ita_44_regions_coeff_txt or "
        "ixi_fpa_44_regions_coeff_txt "
        "manually (tab Data Download - EXIOBASE 1 (full data set)."
    )
    return None


def download_exiobase2():
    """Downloading exiobase not implemented (registration required)"""
    raise NotImplementedError(
        "EXIOBASE 2 requires registration prior to download. "
        "Please register at www.exiobase.eu and download the "
        "EXIOBASE MRIO files "
        ">MrIOT_IxI_fpa_coefficient_version2.2.2.zip<_"
        "and/or_"
        ">MrIOT_PxP_ita_coefficient_version2.2.2.zip<_"
        "manually (tab Data Download - EXIOBASE 2)."
    )
    return None


# def download_exiobase3():


def download_exiobase3(
    storage_folder,
    years=None,
    system=None,
    overwrite_existing=False,
    doi="10.5281/zenodo.3583070",
):
    """
    Downloads EXIOBASE 3 files from Zenodo

    Since version 3.7 EXIOBASE gets published on the Zenodo scientific data
    repository.  This function download the lastest available version from
    Zenodo, for previous version the corresponding DOI (parameter 'doi') needs
    to specified.

    Version 3.7: 10.5281/zenodo.3583071
    Version 3.8: 10.5281/zenodo.4277368


    Parameters
    ----------
    storage_folder: str, valid path
        Location to store the download, folder will be created if
        not existing. If the file is already present in the folder,
        the download of the specific file will be skipped.


    years: list of int or str, optional
        If years is given only downloads the specific years (be default all years will be downloaded).
        Years must be given in 4 digits.

    system: string or list of strings, optional
        'pxp': download product by product classification
        'ixi': download industry by industry classification
        ['ixi', 'pxp'] or None (default): download both classifications

    overwrite_existing: boolean, optional
        If False, skip download of file already existing in
        the storage folder (default). Set to True to replace
        files.

    doi: string, optional.
        The EXIOBASE DOI to be downloaded. By default that resolves
        to the DOI citing the latest available version. For the previous DOI
        see the block 'Versions' on the right hand side of
        https://zenodo.org/record/4277368.

    Returns
    -------

    Meta data of the downloaded MRIOs

    """

    os.makedirs(storage_folder, exist_ok=True)

    doi_url = "https://doi.org/" + doi
    EXIOBASE3_CONFIG["url_db_view"] = doi_url

    exio_web_content = _get_url_datafiles(**EXIOBASE3_CONFIG)

    file_pattern = re.compile(r"IOT_[1,2]\d\d\d_[p,i]x[p,i]\.zip")
    available_files = [
        file_pattern.search(url).group() for url in exio_web_content.data_urls
    ]

    available_years = {filename.split("_")[1] for filename in available_files}
    if type(years) is int or type(years) is str:
        years = [years]
    years = years if years else list(available_years)

    system = system if system else ["pxp", "ixi"]
    if type(system) is str:
        system = [system]

    meta = MRIOMetaData(
        location=storage_folder,
        description="EXIOBASE3 metadata file for pymrio",
        name="EXIO3",
        system=",".join(system),
        version=doi,
    )

    requested_urls = []
    for file_specs in itertools.product(years, system):
        filename = list(
            filter(
                lambda x: str(file_specs[0]) in x and str(file_specs[1]) in x,
                available_files,
            )
        )

        if not filename:
            meta._add_fileio(
                "Could not find EXIOBASE 3 source file with >{}< and >{}<".format(
                    file_specs[0], file_specs[1]
                )
            )
            continue
        requested_urls += [
            u for u in exio_web_content.data_urls for f in filename if f in u
        ]

    meta = _download_urls(
        url_list=requested_urls,
        storage_folder=storage_folder,
        overwrite_existing=overwrite_existing,
        meta_handler=meta,
    )

    meta.save()
    return meta
