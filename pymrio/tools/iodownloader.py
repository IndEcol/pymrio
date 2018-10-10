""" Utility functions for automatic downloading of public MRIO databases
"""

import os
import re
import requests
from collections import namedtuple

from pymrio.tools.iometadata import MRIOMetaData

WIOD_CONFIG = {
    'url_db_view': 'http://www.wiod.org/database/wiots13',
    'url_db_content':  'http://www.wiod.org/',
    'satellite_urls':  [
        'http://www.wiod.org/protected3/data13/SEA/WIOD_SEA_July14.xlsx',
        'http://www.wiod.org/protected3/data13/EU/EU_may12.zip',
        'http://www.wiod.org/protected3/data13/EM/EM_may12.zip',
        'http://www.wiod.org/protected3/data13/CO2/CO2_may12.zip',
        'http://www.wiod.org/protected3/data13/AIR/AIR_may12.zip',
        'http://www.wiod.org/protected3/data13/land/lan_may12.zip',
        'http://www.wiod.org/protected3/data13/materials/mat_may12.zip',
        'http://www.wiod.org/protected3/data13/water/wat_may12.zip',
    ],
    }

EORA26_CONFIG = {
    'url_db_view': 'http://worldmrio.com/simplified/',
    'url_db_content': 'http://worldmrio.com/',
    }


def _get_url_datafiles(url_db_view, url_db_content,
                       mrio_regex, access_cookie=None):
    """ Urls of mrio files by parsing url content for mrio_regex

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

    Returns
    -------
    Named tuple:
    .raw_text: content of url_db_view for later use
    .data_urls: list of url

    """
    # Use post here - NB: get could be necessary for some other pages
    # but currently works for wiod and eora
    returnvalue = namedtuple('url_content',
                             ['raw_text', 'data_urls'])
    url_text = requests.post(url_db_view, cookies=access_cookie).text
    data_urls = [url_db_content + ff
                 for ff in re.findall(mrio_regex, url_text)]
    return returnvalue(raw_text=url_text, data_urls=data_urls)


def _download_urls(url_list, storage_folder, overwrite_existing,
                   meta_handler, access_cookie=None):
    """ Save url from url_list to storage_folder

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
        req = requests.post(url, stream=True, cookies=access_cookie)
        with open(storage_file, 'wb') as lf:
            for chunk in req.iter_content(1024*5):
                lf.write(chunk)

        meta_handler._add_fileio('Downloaded {} to {}'.format(url, filename))
        meta_handler.save()

    return meta_handler


def download_wiod2013(storage_folder, years=None, overwrite_existing=False,
                      satellite_urls=WIOD_CONFIG['satellite_urls']):
    """ Downloads the 2013 wiod release

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

    """

    try:
        os.makedirs(storage_folder)
    except FileExistsError:
        pass

    if type(years) is int or type(years) is str:
        years = [years]
    years = years if years else range(1995, 2012)
    years = [str(yy).zfill(2)[-2:] for yy in years]

    wiod_web_content = _get_url_datafiles(
        url_db_view=WIOD_CONFIG['url_db_view'],
        url_db_content=WIOD_CONFIG['url_db_content'],
        mrio_regex='protected.*?wiot\d\d.*?xlsx')

    restricted_wiod_io_urls = [url for url in wiod_web_content.data_urls if
                               re.search(r"(wiot)(\d\d)",
                                         os.path.basename(url)).group(2)
                               in years]

    meta = MRIOMetaData(location=storage_folder,
                        description='WIOD metadata file for pymrio',
                        name='WIOD',
                        system='ixi',
                        version='data13')

    meta = _download_urls(url_list=restricted_wiod_io_urls + satellite_urls,
                          storage_folder=storage_folder,
                          overwrite_existing=overwrite_existing,
                          meta_handler=meta)

    meta.save()
    return meta


def download_eora26():
    """ Downloading eora26 not implemented (registration required)
    """
    raise NotImplementedError(
          "Eora26 3 requires registration prior to download. "
          "Please register at http://www.worldmrio.com and download the "
          "Eora26 files from the subdomain /simplified")
    return None

    # Development note:
    # Eora 26 autodownload was implemented before but was
    # removed since worldmrio does require
    # a registration now (by summer 2018).
    # The previous implementation can be found
    # in the github history (e.g. at 2e61424 2018-10-09
    # or before)


def download_exiobase1():
    """ Downloading exiobase not implemented (registration required)
    """
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
    """ Downloading exiobase not implemented (registration required)
    """
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


def download_exiobase3():
    """ Downloading exiobase not implemented (registration required)
    """
    raise NotImplementedError(
          "EXIOBASE 3 requires registration prior to download. "
          "Please register at www.exiobase.eu and download the "
          "EXIOBASE 3 MRIO files ")
    return None
