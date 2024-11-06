""" Function for getting and processing GLAM data.

"""

from pathlib import Path
from pymrio.tools.iodownloader import _download_urls
from pymrio.tools.iometadata import MRIOMetaData


GLAM_CONFIG = {
        "V2024.10": "https://www.lifecycleinitiative.org/wp-content/uploads/2024/10/V1.0.2024.10.zip"
    }

def get_GLAM(storage_folder, overwrite_existing=False, version="V2024.10"):
    """ Download GLAM and store in the given directory

    Parameters
    ----------
    storage_folder : str or Path
        Folder to store the downloaded GLAM data

    overwrite_existing : bool, optional
        If True, overwrite existing data, by default False

    version : str, optional
        Version of the GLAM data to download, by default "V2024.10"
        Version must be a key in the GLAM_CONFIG or can alternatively
        be a url to the zip file to download.
    """

    if type(storage_folder) is str:
        storage_folder = Path(storage_folder)
    storage_folder.mkdir(exist_ok=True, parents=True)

    downlog = MRIOMetaData._make_download_log(
        location=storage_folder,
        description="GLAM download",
        name="GLAM",
        system="impact assessment",
        version=version,
    )

    requested_urls = [GLAM_CONFIG.get(version, version)]

    downlog = _download_urls(
        url_list=requested_urls,
        storage_folder=storage_folder,
        overwrite_existing=overwrite_existing,
        downlog_handler=downlog,
    )

    downlog.save()
    return downlog

