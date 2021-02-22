"""
Methods to load previously save mrios

"""

import collections
import configparser
import json
import logging
import os
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

from pymrio.core.constants import DEFAULT_FILE_NAMES, GENERIC_NAMES, PYMRIO_PATH
from pymrio.core.mriosystem import Extension, IOSystem
from pymrio.tools.iometadata import MRIOMetaData
from pymrio.tools.ioutil import get_file_para


# Exceptions
class ReadError(Exception):
    """ Base class for errors occuring while reading MRIO data """

    pass


def load_all(path, include_core=True, subfolders=None, path_in_arc=None):
    """Loads a full IO system with all extension in path

    Parameters
    ----------
    path : pathlib.Path or string
        Path or path with para file name for the data to load.
        This must either point to the directory containing the uncompressed
        data or the location of a compressed zip file with the data. In the
        later case and if there are several mrio's in the zip file the
        parameter 'path_in_arc' need to be specifiec to further indicate the
        location of the data in the compressed file.

    include_core : boolean, optional
        If False the load method does not include A, L and Z matrix. This
        significantly reduces the required memory if the purpose is only
        to analyse the results calculated beforehand.

    subfolders: list of pathlib.Path or string, optional
        By default (subfolders=None), all subfolders in path containing a json
        parameter file (as defined in DEFAULT_FILE_NAMES['filepara']:
        metadata.json) are parsed. If only a subset should be used, pass a list
        of names of subfolders. These can either be strings specifying direct
        subfolders of path, or absolute/relative path if the extensions are
        stored at a different location. Both modes can be mixed. If the data
        is read from a zip archive the path must be given as described below in
        'path_in_arc', relative to the root defined in the paramter
        'path_in_arc'. Extensions in a different zip archive must be read
        separately by calling the function 'load' for this extension.

    path_in_arc: string, optional
        Path to the data in the zip file (where the fileparameters file is
        located). path_in_arc must be given without leading dot and slash;
        thus to point to the data in the root of the compressed file pass '',
        for data in e.g. the folder 'emissions' pass 'emissions/'.  Only used
        if parameter 'path' points to an compressed zip file.
        Can be None (default) if there is only one mrio database in the
        zip archive (thus only one file_parameter file as the systemtype entry
        'IOSystem'.

    """

    def clean(varStr):
        """get valid python name from folder"""
        return re.sub(r"\W|^(?=\d)", "_", str(varStr))

    path = Path(path)

    if zipfile.is_zipfile(str(path)):
        with zipfile.ZipFile(file=str(path), mode="r") as zz:
            zipcontent = zz.namelist()
        if path_in_arc:
            path_in_arc = str(path_in_arc)
            if path_in_arc not in zipcontent:
                # Not using os.path.join here b/c this adds the wrong
                # separator when reading the zip in windows
                if path_in_arc != "":
                    path_in_arc = (
                        path_in_arc + "/" + DEFAULT_FILE_NAMES["filepara"]
                    ).replace("//", "/")
                else:
                    path_in_arc = DEFAULT_FILE_NAMES["filepara"]

                if path_in_arc not in zipcontent:
                    raise ReadError(
                        "File parameter file {} not found in {}. "
                        "Tip: specify fileparameter filename "
                        'through "path_in_arc" if different '
                        "from default.".format(DEFAULT_FILE_NAMES["filepara"], path)
                    )

        else:
            with zipfile.ZipFile(file=str(path), mode="r") as zz:
                fpfiles = [
                    f
                    for f in zz.namelist()
                    if os.path.basename(f) == DEFAULT_FILE_NAMES["filepara"]
                    and json.loads(zz.read(f).decode("utf-8"))["systemtype"]
                    == "IOSystem"
                ]
            if len(fpfiles) == 0:
                raise ReadError(
                    "File parameter file {} not found in {}. "
                    "Tip: specify fileparameter filename "
                    'through "path_in_arc" if different '
                    "from default.".format(DEFAULT_FILE_NAMES["filepara"], path)
                )
            elif len(fpfiles) > 1:
                raise ReadError(
                    "Mulitple mrio archives found in {}. "
                    "Specify one by the "
                    'parameter "path_in_arc"'.format(path)
                )
            else:
                path_in_arc = os.path.dirname(fpfiles[0])

        logging.debug(
            "Expect file parameter-file at {} in {}".format(path_in_arc, path)
        )

    io = load(path, include_core=include_core, path_in_arc=path_in_arc)

    if zipfile.is_zipfile(str(path)):
        root_in_zip = os.path.dirname(path_in_arc)
        if subfolders is None:
            subfolders = {
                Path(os.path.relpath(os.path.dirname(p), root_in_zip)).as_posix()
                for p in zipcontent
                if p.startswith(root_in_zip) and os.path.dirname(p) != root_in_zip
            }

        for subfolder_name in subfolders:
            if subfolder_name not in zipcontent + list(
                {os.path.dirname(p) for p in zipcontent}
            ):
                # Not using os.path.join here b/c this adds the wrong
                # separator when reading the zip in windows
                subfolder_full = root_in_zip + "/" + subfolder_name
                subfolder_full = subfolder_full.replace("//", "/")
            else:
                subfolder_full = subfolder_name
            subfolder_name = os.path.basename(os.path.normpath(subfolder_name))

            if subfolder_name not in zipcontent:
                subfolder_full_meta = (
                    subfolder_full + "/" + DEFAULT_FILE_NAMES["filepara"]
                )
            else:
                subfolder_full_meta = subfolder_full

            if subfolder_full_meta in zipcontent:
                ext = load(
                    path, include_core=include_core, path_in_arc=subfolder_full_meta
                )
                setattr(io, clean(subfolder_name), ext)
                io.meta._add_fileio(
                    "Added satellite account " "from {}".format(subfolder_full)
                )
            else:
                continue

    else:
        if subfolders is None:
            subfolders = [d for d in path.iterdir() if d.is_dir()]

        for subfolder_name in subfolders:
            if not os.path.exists(str(subfolder_name)):
                subfolder_full = path / subfolder_name
            else:
                subfolder_full = subfolder_name
            subfolder_name = os.path.basename(os.path.normpath(subfolder_name))

            if not os.path.isfile(str(subfolder_full)):
                subfolder_full_meta = subfolder_full / DEFAULT_FILE_NAMES["filepara"]
            else:
                subfolder_full_meta = subfolder_full

            if subfolder_full_meta.exists():
                ext = load(subfolder_full, include_core=include_core)
                setattr(io, clean(subfolder_name), ext)
                io.meta._add_fileio(
                    "Added satellite account " "from {}".format(subfolder_full)
                )
            else:
                continue

    return io


def load(path, include_core=True, path_in_arc=""):
    """Loads a IOSystem or Extension previously saved with pymrio

    This function can be used to load a IOSystem or Extension specified in a
    metadata file (as defined in DEFAULT_FILE_NAMES['filepara']: metadata.json)

    DataFrames (tables) are loaded from text or binary pickle files.
    For the latter, the extension .pkl or .pickle is assumed, in all other case
    the tables are assumed to be in .txt format.

    Parameters
    ----------
    path : pathlib.Path or string
        Path or path with para file name for the data to load. This must
        either point to the directory containing the uncompressed data or
        the location of a compressed zip file with the data. In the
        later case the parameter 'path_in_arc' need to be specific to
        further indicate the location of the data in the compressed file.

    include_core : boolean, optional
        If False the load method does not include A, L and Z matrix. This
        significantly reduces the required memory if the purpose is only
        to analyse the results calculated beforehand.

    path_in_arc: string, optional
        Path to the data in the zip file (where the fileparameters file is
        located). path_in_arc must be given without leading dot and slash;
        thus to point to the data in the root of the compressed file pass '',
        for data in e.g. the folder 'emissions' pass 'emissions/'.  Only used
        if parameter 'path' points to an compressed zip file.

    Returns
    -------

        IOSystem or Extension class depending on systemtype in the json file
        None in case of errors

    """
    path = Path(path)

    if not path.exists():
        raise ReadError("Given path does not exist")

    file_para = get_file_para(path=path, path_in_arc=path_in_arc)

    if file_para.content["systemtype"] == GENERIC_NAMES["iosys"]:
        if zipfile.is_zipfile(str(path)):
            # Not using os.path.join here b/c this adds the wrong
            # separator when reading the zip in windows
            if file_para.folder != "":
                metadata_folder = (
                    file_para.folder + "/" + DEFAULT_FILE_NAMES["metadata"]
                ).replace("//", "/")
            else:
                metadata_folder = DEFAULT_FILE_NAMES["metadata"]

            ret_system = IOSystem(
                meta=MRIOMetaData(location=path, path_in_arc=metadata_folder)
            )
            ret_system.meta._add_fileio(
                "Loaded IO system from {} - {}".format(path, path_in_arc)
            )
        else:
            ret_system = IOSystem(
                meta=MRIOMetaData(location=path / DEFAULT_FILE_NAMES["metadata"])
            )
            ret_system.meta._add_fileio("Loaded IO system from {}".format(path))

    elif file_para.content["systemtype"] == GENERIC_NAMES["ext"]:
        ret_system = Extension(file_para.content["name"])

    else:
        raise ReadError("Type of system no defined in the file parameters")
        return None

    for key in file_para.content["files"]:
        if not include_core and key not in ["A", "L", "Z"]:
            continue

        file_name = file_para.content["files"][key]["name"]
        nr_index_col = file_para.content["files"][key]["nr_index_col"]
        nr_header = file_para.content["files"][key]["nr_header"]
        _index_col = list(range(int(nr_index_col)))
        _header = list(range(int(nr_header)))
        _index_col = 0 if _index_col == [0] else _index_col
        _header = 0 if _header == [0] else _header

        if key == "FY":  # Legacy code to read data saved with version < 0.4
            key = "F_Y"

        if zipfile.is_zipfile(str(path)):
            # Not using os.path.join here b/c this adds the wrong
            # separator when reading the zip in windows
            if file_para.folder != "":
                full_file_name = file_para.folder + "/" + file_name
                full_file_name = full_file_name.replace("//", "/")
            else:
                full_file_name = file_name
            logging.info("Load data from {}".format(full_file_name))

            with zipfile.ZipFile(file=str(path)) as zf:
                if (
                    os.path.splitext(str(full_file_name))[1] == ".pkl"
                    or os.path.splitext(str(full_file_name))[1] == ".pickle"
                ):
                    setattr(ret_system, key, pd.read_pickle(zf.open(full_file_name)))
                else:
                    setattr(
                        ret_system,
                        key,
                        pd.read_csv(
                            zf.open(full_file_name),
                            index_col=_index_col,
                            header=_header,
                            sep="\t",
                        ),
                    )
        else:
            full_file_name = path / file_name
            logging.info("Load data from {}".format(full_file_name))

            if (
                os.path.splitext(str(full_file_name))[1] == ".pkl"
                or os.path.splitext(str(full_file_name))[1] == ".pickle"
            ):
                setattr(ret_system, key, pd.read_pickle(full_file_name))
            else:
                setattr(
                    ret_system,
                    key,
                    pd.read_csv(
                        full_file_name, index_col=_index_col, header=_header, sep="\t"
                    ),
                )
    return ret_system


def archive(
    source,
    archive,
    path_in_arc=None,
    remove_source=False,
    compression=zipfile.ZIP_DEFLATED,
    compresslevel=-1,
):
    """Archives a MRIO database as zip file

    This function is a wrapper around zipfile.write,
    to ease the writing of an archive and removing the source data.

    Note
    ----
    In contrast to zipfile.write, this function raises an
    error if the data (path + filename) are identical in the zip archive.
    Background: the zip standard allows that files with the same name and path
    are stored side by side in a zip file. This becomes an issue when unpacking
    this files as they overwrite each other upon extraction.

    Parameters
    ----------

    source: str or pathlib.Path or list of these
        Location of the mrio data (folder).
        If not all data should be archived, pass a list of
        all files which should be included in the archive (absolute path)

    archive: str or pathlib.Path
        Full path with filename for the archive.

    path_in_arc: string, optional
        Path within the archive zip file where data should be stored.
        'path_in_arc' must be given without leading dot and slash.
        Thus to point to the data in the root of the compressed file pass '',
        for data in e.g. the folder 'mrio_v1' pass 'mrio_v1/'.
        If None (default) data will be stored in the root of the archive.

    remove_source: boolean, optional
        If True, deletes the source file from the disk (all files
        specified in 'source' or the specified directory, depending if a
        list of files or directory was passed). If False, leaves the
        original files on disk. Also removes all empty directories
        in source including source.

    compression: ZIP compression method, optional
        This is passed to zipfile.write. By default it is set to ZIP_DEFLATED.
        NB: This is different from the zipfile default (ZIP_STORED) which would
        not give any compression. See
        https://docs.python.org/3/library/zipfile.html#zipfile-objects for
        further information. Depending on the value given here additional
        modules might be necessary (e.g. zlib for ZIP_DEFLATED). Futher
        information on this can also be found in the zipfile python docs.

    compresslevel: int, optional
        This is passed to zipfile.write and specifies the compression level.
        Acceptable values depend on the method specified at the parameter
        'compression'.  By default, it is set to -1 which gives a compromise
        between speed and size for the ZIP_DEFLATED compression (this is
        internally interpreted as 6 as described here:
        https://docs.python.org/3/library/zlib.html#zlib.compressobj )
        NB: This is only used if python version >= 3.7

    Raises
    ------
    FileExistsError: In case a file to be archived already present in the
    archive.

    """
    archive = Path(archive)

    if type(source) is not list:
        source_root = str(source)
        source_files = [f for f in Path(source).glob("**/*") if f.is_file()]
    else:
        source_root = os.path.commonpath([str(f) for f in source])
        source_files = [Path(f) for f in source]

    path_in_arc = "" if not path_in_arc else path_in_arc

    arc_file_names = {
        str(f): os.path.join(path_in_arc, str(f.relative_to(source_root)))
        for f in source_files
    }

    if archive.exists():
        with zipfile.ZipFile(file=str(archive), mode="r") as zf:
            already_present = zf.namelist()
        duplicates = {
            ff: zf for ff, zf in arc_file_names.items() if zf in already_present
        }

        if duplicates:
            raise FileExistsError(
                "These files already exists in {arc} for "
                'path_in_arc "{pa}":\n  {filelist}'.format(
                    pa=path_in_arc,
                    arc=archive,
                    filelist="\n  ".join(duplicates.values()),
                )
            )

    if sys.version_info.major == 3 and sys.version_info.minor >= 7:
        zip_open_para = dict(
            file=str(archive),
            mode="a",
            compression=compression,
            compresslevel=compresslevel,
        )
    else:
        zip_open_para = dict(file=str(archive), mode="a", compression=compression)

    with zipfile.ZipFile(**zip_open_para) as zz:
        for fullpath, zippath in arc_file_names.items():
            zz.write(str(fullpath), str(zippath))

    if remove_source:
        for f in source_files:
            os.remove(str(f))

        for root, dirs, files in os.walk(source_root, topdown=False):
            for name in dirs:
                dir_path = os.path.join(root, name)
                if not os.listdir(dir_path):
                    os.rmdir(os.path.join(root, name))
        try:
            os.rmdir(source_root)
        except OSError:
            pass


def _load_all_ini_based_io(path, **kwargs):  # pragma: no cover
    """DEPRECATED: For convert a previous version to the new json format

    Loads the whole IOSystem with Extensions given in path

    This just calls pymrio.load with recursive = True. Apart from that the
    same parameter can as for .load can be used.

    Parameters
    ----------
    path : string
        path or ini file name for the data to load
    **kwargs : key word arguments, optional
            This will be passed directly to the load method

    Returns
    -------
    IOSystem
    None in case of errors
    """
    return _load_ini_based_io(path, recursive=True, **kwargs)


def _load_ini_based_io(
    path,
    recursive=False,
    ini=None,
    subini={},
    include_core=True,
    only_coefficients=False,
):  # pragma: no cover
    """DEPRECATED: For convert a previous version to the new json format

    Loads a IOSystem or Extension from a ini files

    This function can be used to load a IOSystem or Extension specified in a
    ini file. DataFrames (tables) are loaded from text or binary pickle files.
    For the latter, the extension .pkl or .pickle is assumed, in all other case
    the tables are assumed to be in .txt format.

    Parameters
    ----------

    path : string
        path or ini file name for the data to load

    recursive : boolean, optional
        If True, load also the data in the subfolders and add them as
        extensions to the IOSystem (in that case path must point to the root).
        Only first order subfolders are considered (no subfolders in
        subfolders) and if a folder does not contain a ini file it's skipped.
        Use the subini parameter in case of multiple ini files in a subfolder.
        Attribute name of the extension in the IOSystem are based on the
        subfolder name.  Default is False

    ini : string, optional
        If there are several ini files in the root folder, take this one for
        loading the data If None (default) take the ini found in the folder,
        error if several are found

    subini : dict, optional
        If there are multiple ini in the subfolder, use the ini given in the
        dict.  Format: 'subfoldername':'ininame' If a key for a subfolder is
        not found or None (default), the ini found in the folder will be taken,
        error if several are found

    include_core : boolean, optional
        If False the load method does not include A, L and Z matrix. This
        significantly reduces the required memory if the purpose is only
        to analyse the results calculated beforehand.

    Returns
    -------

        IOSystem or Extension class depending on systemtype in the ini file
        None in case of errors

    """

    # check path and given parameter
    ini_file_name = None

    path = os.path.abspath(os.path.normpath(path))

    if os.path.splitext(path)[1] == ".ini":
        (path, ini_file_name) = os.path.split(path)

    if ini:
        ini_file_name = ini

    if not os.path.exists(path):
        raise ReadError("Given path does not exist")
        return None

    if not ini_file_name:
        _inifound = False
        for file in os.listdir(path):
            if os.path.splitext(file)[1] == ".ini":
                if _inifound:
                    raise ReadError("Found multiple ini files in folder - specify one")
                    return None
                ini_file_name = file
                _inifound = True

    # read the ini
    io_ini = configparser.RawConfigParser()
    io_ini.optionxform = lambda option: option

    io_ini.read(os.path.join(path, ini_file_name))

    systemtype = io_ini.get("systemtype", "systemtype", fallback=None)
    name = io_ini.get("meta", "name", fallback=os.path.splitext(ini_file_name)[0])

    if systemtype == "IOSystem":
        ret_system = IOSystem(name=name)
    elif systemtype == "Extension":
        ret_system = Extension(name=name)
    else:
        raise ReadError("System not defined in ini")
        return None

    for key in io_ini["meta"]:
        setattr(ret_system, key, io_ini.get("meta", key, fallback=None))

    for key in io_ini["files"]:
        if "_nr_index_col" in key:
            continue
        if "_nr_header" in key:
            continue

        if not include_core:
            not_to_load = ["A", "L", "Z"]
            if key in not_to_load:
                continue

        if only_coefficients:
            _io = IOSystem()
            if key not in _io.__coefficients__ + ["unit"]:
                continue

        file_name = io_ini.get("files", key)
        nr_index_col = io_ini.get("files", key + "_nr_index_col", fallback=None)
        nr_header = io_ini.get("files", key + "_nr_header", fallback=None)

        if (nr_index_col is None) or (nr_header is None):
            raise ReadError(
                "Index or column specification missing for {}".format(str(file_name))
            )
            return None

        _index_col = list(range(int(nr_index_col)))
        _header = list(range(int(nr_header)))

        if _index_col == [0]:
            _index_col = 0
        if _header == [0]:
            _header = 0
        file = os.path.join(path, file_name)
        logging.info("Load data from {}".format(file))

        if (
            os.path.splitext(file)[1] == ".pkl"
            or os.path.splitext(file)[1] == ".pickle"
        ):
            setattr(ret_system, key, pd.read_pickle(file))
        else:
            setattr(
                ret_system,
                key,
                pd.read_csv(file, index_col=_index_col, header=_header, sep="\t"),
            )

    if recursive:
        # look for subfolder in the given path
        subfolder_list = os.walk(path).__next__()[1]

        # loop all subfolder and append extension based on
        # ini file in subfolder
        for subfolder in subfolder_list:
            subini_file_name = subini.get(subfolder)
            subpath = os.path.abspath(os.path.join(path, subfolder))

            if not subini_file_name:
                _inifound = False
                for file in os.listdir(subpath):
                    if os.path.splitext(file)[1] == ".ini":
                        if _inifound:
                            raise ReadError(
                                "Found multiple ini files in subfolder "
                                "{} - specify one".format(subpath)
                            )
                            return None
                        subini_file_name = file
                        _inifound = True
            if not _inifound:
                continue

            # read the ini
            subio_ini = configparser.RawConfigParser()
            subio_ini.optionxform = lambda option: option

            subio_ini.read(os.path.join(subpath, subini_file_name))

            systemtype = subio_ini.get("systemtype", "systemtype", fallback=None)
            name = subio_ini.get(
                "meta", "name", fallback=os.path.splitext(subini_file_name)[0]
            )

            if systemtype == "IOSystem":
                raise ReadError(
                    "IOSystem found in subfolder {} - "
                    "only extensions expected".format(subpath)
                )
                return None
            elif systemtype == "Extension":
                sub_system = Extension(name=name)
            else:
                raise ReadError("System not defined in ini")
                return None

            for key in subio_ini["meta"]:
                setattr(sub_system, key, subio_ini.get("meta", key, fallback=None))

            for key in subio_ini["files"]:
                if "_nr_index_col" in key:
                    continue
                if "_nr_header" in key:
                    continue

                if only_coefficients:
                    _ext = Extension("temp")
                    if key not in _ext.__coefficients__ + ["unit"]:
                        continue

                file_name = subio_ini.get("files", key)
                nr_index_col = subio_ini.get(
                    "files", key + "_nr_index_col", fallback=None
                )
                nr_header = subio_ini.get("files", key + "_nr_header", fallback=None)

                if (nr_index_col is None) or (nr_header is None):
                    raise ReadError(
                        "Index or column specification missing "
                        "for {}".format(str(file_name))
                    )
                    return None

                _index_col = list(range(int(nr_index_col)))
                _header = list(range(int(nr_header)))

                if _index_col == [0]:
                    _index_col = 0
                if _header == [0]:
                    _header = 0
                file = os.path.join(subpath, file_name)
                logging.info("Load data from {}".format(file))
                if (
                    os.path.splitext(file)[1] == ".pkl"
                    or os.path.splitext(file)[1] == ".pickle"
                ):
                    setattr(sub_system, key, pd.read_pickle(file))
                else:
                    setattr(
                        sub_system,
                        key,
                        pd.read_csv(
                            file, index_col=_index_col, header=_header, sep="\t"
                        ),
                    )

                # get valid python name from folder
                def clean(varStr):
                    return re.sub(r"\W|^(?=\d)", "_", str(varStr))

                setattr(ret_system, clean(subfolder), sub_system)

    return ret_system


def load_test():
    """Returns a small test MRIO

    The test system contains:

        - six regions,
        - seven sectors,
        - seven final demand categories
        - two extensions (emissions and factor_inputs)

    The test system only contains Z, Y, F, F_Y. The rest can be calculated with
    calc_all()

    Notes
    -----

        For development: This function can be used as an example of
        how to parse an IOSystem

    Returns
    -------

    IOSystem

    """

    # row_header:
    #    number of rows containing header on the top of the file (for the
    #    columns)
    # col_header:
    #    number of cols containing header on the beginning of the file (for the
    #    rows)
    # row and columns header contain also the row for the units, this are
    # afterwards safed as a extra dataframe
    #
    # unit_col: column containing the unit for the table
    file_data = collections.namedtuple(
        "file_data", ["file_name", "row_header", "col_header", "unit_col"]
    )

    # file names and header specs of the system
    test_system = dict(
        Z=file_data(
            file_name="trade_flows_Z.txt", row_header=2, col_header=3, unit_col=2
        ),
        Y=file_data(
            file_name="finald_demand_Y.txt", row_header=2, col_header=3, unit_col=2
        ),
        fac=file_data(
            file_name="factor_input.txt", row_header=2, col_header=2, unit_col=1
        ),
        emissions=file_data(
            file_name="emissions.txt", row_header=2, col_header=3, unit_col=2
        ),
        FDemissions=file_data(
            file_name="FDemissions.txt", row_header=2, col_header=3, unit_col=2
        ),
    )

    meta_rec = MRIOMetaData(location=PYMRIO_PATH["test_mrio"])

    # read the data into a dicts as pandas.DataFrame
    data = {
        key: pd.read_csv(
            os.path.join(PYMRIO_PATH["test_mrio"], test_system[key].file_name),
            index_col=list(range(test_system[key].col_header)),
            header=list(range(test_system[key].row_header)),
            sep="\t",
        )
        for key in test_system
    }

    meta_rec._add_fileio("Load test_mrio from {}".format(PYMRIO_PATH["test_mrio"]))

    # distribute the data into dics which can be passed to
    # the IOSystem. To do so, some preps are necessary:
    # - name the header data
    # - save unit in own dataframe and drop unit from the tables

    trade = dict(Z=data["Z"], Y=data["Y"])
    factor_inputs = dict(F=data["fac"])
    emissions = dict(F=data["emissions"], F_Y=data["FDemissions"])

    trade["Z"].index.names = ["region", "sector", "unit"]
    trade["Z"].columns.names = ["region", "sector"]
    trade["unit"] = pd.DataFrame(trade["Z"].iloc[:, 0].reset_index(level="unit").unit)
    trade["Z"].reset_index(level="unit", drop=True, inplace=True)

    trade["Y"].index.names = ["region", "sector", "unit"]
    trade["Y"].columns.names = ["region", "category"]
    trade["Y"].reset_index(level="unit", drop=True, inplace=True)

    factor_inputs["name"] = "Factor Inputs"
    factor_inputs["F"].index.names = [
        "inputtype",
        "unit",
    ]
    factor_inputs["F"].columns.names = ["region", "sector"]
    factor_inputs["unit"] = pd.DataFrame(
        factor_inputs["F"].iloc[:, 0].reset_index(level="unit").unit
    )
    factor_inputs["F"].reset_index(level="unit", drop=True, inplace=True)

    emissions["name"] = "Emissions"
    emissions["F"].index.names = [
        "stressor",
        "compartment",
        "unit",
    ]
    emissions["F"].columns.names = ["region", "sector"]
    emissions["unit"] = pd.DataFrame(
        emissions["F"].iloc[:, 0].reset_index(level="unit").unit
    )
    emissions["F"].reset_index(level="unit", drop=True, inplace=True)
    emissions["F_Y"].index.names = ["stressor", "compartment", "unit"]
    emissions["F_Y"].columns.names = ["region", "category"]
    emissions["F_Y"].reset_index(level="unit", drop=True, inplace=True)

    # the population data - this is optional (None can be passed if no data is
    # available)
    popdata = pd.read_csv(
        os.path.join(PYMRIO_PATH["test_mrio"], "./population.txt"),
        index_col=0,
        sep="\t",
    ).astype(float)

    return IOSystem(
        Z=data["Z"],
        Y=data["Y"],
        unit=trade["unit"],
        meta=meta_rec,
        factor_inputs=factor_inputs,
        emissions=emissions,
        population=popdata,
    )
