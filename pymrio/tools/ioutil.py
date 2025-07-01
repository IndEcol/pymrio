"""Utility function for pymrio.

KST 20140502
"""

import json
import logging
import os
import re
import ssl
import zipfile
from collections import namedtuple
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
import requests
import urllib3
from requests.adapters import HTTPAdapter

from pymrio.core.constants import DEFAULT_FILE_NAMES, LONG_VALUE_NAME, PYMRIO_PATH


def is_vector(inp):
    """Return true if the input can be interpreted as a 'true' vector.

    Note:
    ----
    Does only check dimensions, not if type is numeric

    Parameters
    ----------
    inp : numpy.ndarray or something that can be converted into ndarray

    Returns
    -------
    Boolean
        True for vectors: ndim = 1 or ndim = 2 and shape of one axis = 1
        False for all other arrays
    """
    inp = np.asarray(inp)
    nr_dim = np.ndim(inp)
    if nr_dim == 1 or (nr_dim == 2) and (1 in inp.shape):
        return True
    return False


def get_repo_content(path):
    """List of files in a repo (path or zip).

    Parameters
    ----------
    path: string or pathlib.Path

    Returns
    -------
    Returns a namedtuple with .iszip and .filelist
    The path in filelist are pure strings.

    """
    path = Path(path)

    if zipfile.is_zipfile(str(path)):
        with zipfile.ZipFile(str(path)) as zz:
            filelist = [info.filename for info in zz.infolist()]
        iszip = True
    else:
        iszip = False
        filelist = [str(f) for f in path.glob("**/*") if f.is_file()]
    return namedtuple("repocontent", ["iszip", "filelist"])(iszip, filelist)


def get_file_para(path, path_in_arc=""):
    """Read the file parameter file.

    Helper function to consistently read the file parameter file, which can
    either be uncompressed or included in a zip archive.  By default, the file
    name is to be expected as set in DEFAULT_FILE_NAMES['filepara'] (currently
    file_parameters.json), but can defined otherwise by including the file
    name of the parameter file in the parameter path.

    Parameters
    ----------
    path: pathlib.Path or string
        Path or path with para file name for the data to load.
        This must either point to the directory containing the uncompressed
        data or the location of a compressed zip file with the data. In the
        later case the parameter 'path_in_arc' needs to be specific to
        further indicate the location of the data in the compressed file.

    path_in_arc: string, optional
        Path to the data in the zip file (where the fileparameters file is
        located). path_in_arc must be given without leading dot and slash;
        thus to point to the data in the root of the compressed file pass ''
        (default), for data in e.g. the folder 'emissions' pass 'emissions/'.
        Only used if parameter 'path' points to an compressed zip file.

    Returns
    -------
    Returns a namedtuple with
    .folder: str with the absolute path containing the
           file parameter file. In case of a zip the path
           is relative to the root in the zip
    .name: Filename without folder of the used parameter file.
    .content: Dictionary with the content oft the file parameter file

    Raises
    ------
    FileNotFoundError if parameter file not found

    """
    path = Path(path)

    if zipfile.is_zipfile(str(path)):
        para_file_folder = str(path_in_arc)
        with zipfile.ZipFile(file=str(path)) as zf:
            files = zf.namelist()
    else:
        para_file_folder = str(path)
        files = [str(f) for f in path.glob("**/*")]

    if para_file_folder not in files:
        if zipfile.is_zipfile(str(path)):
            # b/c in win os.path.join adds \ also for within zipfile
            if para_file_folder != "":
                para_file_full_path = (para_file_folder + "/" + DEFAULT_FILE_NAMES["filepara"]).replace("//", "/")
            else:
                para_file_full_path = DEFAULT_FILE_NAMES["filepara"]

        else:
            para_file_full_path = os.path.join(para_file_folder, DEFAULT_FILE_NAMES["filepara"])
    else:
        para_file_full_path = para_file_folder
        para_file_folder = os.path.dirname(para_file_full_path)

    if para_file_full_path not in files:
        raise FileNotFoundError(f"File parameter file {para_file_full_path} not found")

    if zipfile.is_zipfile(str(path)):
        with zipfile.ZipFile(file=str(path)) as zf:
            para_file_content = json.loads(zf.read(para_file_full_path).decode("utf-8"))
    else:
        with open(para_file_full_path) as pf:
            para_file_content = json.load(pf)

    return namedtuple("file_parameter", ["folder", "name", "content"])(
        para_file_folder,
        os.path.basename(para_file_full_path),
        para_file_content,
    )


def build_agg_matrix(agg_vector, pos_dict=None):
    """Aggregate based on mapping given in input as numerical or str vector.

    Parameters
    ----------
        agg_vector : list or vector like numpy ndarray
            This can be row or column vector.
            Length m with position given for n and -1 if values
            should not be included
            or
            length m with id_string for the aggregation

        pos_dict : dictionary
            (only possible if agg_vector is given as string)
            output order for the new matrix
            must be given as dict with
            'string in agg_vector' = pos
            (as int, -1 if value should not be included in the aggregation)

    Returns
    -------
    agg_matrix : numpy ndarray
        Aggregation matrix with shape (n, m) with n (rows) indicating the
        new classification and m (columns) the old classification

    Examples
    --------
    Assume an input vector with either

    >>> inp1 = np.array([0, 1, 1, 2])

    or

    >>> inp2 = ['a', 'b', 'b', 'c']

    inp1 and inp2 are equivalent, the entries are just indicators.

    >>> build_agg_matrix(inp1)
    >>> build_agg_matrix(inp2)

    results in
    >>> array([[1., 0., 0., 0.],
    >>>        [0., 1., 1., 0.],
    >>>        [0., 0., 0., 1.]])

    The order can be defined by a dictionary, thus

    >>> pymrio.build_agg_matrix(np.array([1, 0, 0, 2]))

    is equivalent to

    >>> pymrio.build_agg_matrix(['b', 'a', 'a', 'c'], dict(a=0,b=1,c=2))

    >>> array([[0., 1., 1., 0.],
    >>>        [1., 0., 0., 0.],
    >>>        [0., 0., 0., 1.]])

    """
    if isinstance(agg_vector, np.ndarray):
        agg_vector = agg_vector.flatten().tolist()

    if type(list(agg_vector)[0]) is str:
        str_vector = agg_vector
        agg_vector = np.zeros(len(str_vector))
        if pos_dict:
            if len(pos_dict.keys()) != len(set(str_vector)):
                raise ValueError("Posistion elements inconsistent with aggregation vector")
            seen = pos_dict
        else:
            seen = {}
        counter = 0
        for ind, item in enumerate(str_vector):
            if item not in seen:
                seen[item] = counter
                counter += 1
            agg_vector[ind] = seen[item]

    agg_vector = np.array(agg_vector, dtype=int)
    agg_vector = agg_vector.reshape((1, -1))
    row_corr = agg_vector
    col_corr = np.arange(agg_vector.size)

    agg_matrix = np.zeros((row_corr.max() + 1, col_corr.max() + 1))
    agg_matrix[row_corr, col_corr] = 1

    # set columns with -1 value to 0
    agg_matrix[np.tile(agg_vector == -1, (np.shape(agg_matrix)[0], 1))] = 0

    return agg_matrix


def diagonalize_columns_to_sectors(df: pd.DataFrame, sector_index_level: Union[str, int] = "sector") -> pd.DataFrame:
    """Add the resolution of the rows to columns by diagonalizing.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to diagonalize
    sector_index_name : string, optional
        Name or number of the index level containing sectors.

    Returns
    -------
    pd.DataFrame, diagonalized


    Example:
    --------
        input       output
         (all letters are index or header)
            A B     A A A B B B
                    x y z x y z
        A x 3 1     3 0 0 1 0 0
        A y 4 2     0 4 0 0 2 0
        A z 5 3     0 0 5 0 0 3
        B x 6 9     6 0 0 9 0 0
        B y 7 6     0 7 0 0 6 0
        B z 8 4     0 0 8 0 0 4

    """
    sectors = df.index.get_level_values(sector_index_level).unique()
    sector_name = sector_index_level if type(sector_index_level) is str else "sector"

    diag_df = pd.DataFrame(
        data=diagonalize_blocks(df.values, blocksize=len(sectors)),
        index=df.index,
        columns=pd.MultiIndex.from_product([df.columns, sectors], names=[*df.columns.names, sector_name]),
    )
    return diag_df


def diagonalize_blocks(arr, blocksize: int):
    """Diagonalize sections of columns of an array for the whole array.

    Parameters
    ----------
    arr : numpy array
        Input array

    blocksize : int
        number of rows/colums forming one block

    Returns
    -------
    numpy ndarray with shape (columns 'arr' * blocksize,
                              columns 'arr' * blocksize)

    Example:
    --------
    arr:      output: (blocksize = 3)
        3 1     3 0 0 1 0 0
        4 2     0 4 0 0 2 0
        5 3     0 0 5 0 0 3
        6 9     6 0 0 9 0 0
        7 6     0 7 0 0 6 0
        8 4     0 0 8 0 0 4
    """
    nr_col = arr.shape[1]
    nr_row = arr.shape[0]

    if np.mod(nr_row, blocksize):
        raise ValueError("Number of rows of input array must be a multiple of blocksize")

    arr_diag = np.zeros((nr_row, blocksize * nr_col))

    for col_ind, col_val in enumerate(arr.T):
        col_start = col_ind * blocksize
        col_end = blocksize + col_ind * blocksize
        for _ind in range(int(nr_row / blocksize)):
            row_start = _ind * blocksize
            row_end = blocksize + _ind * blocksize
            arr_diag[row_start:row_end, col_start:col_end] = np.diag(col_val[row_start:row_end])

    return arr_diag


def set_dom_block(df: pd.DataFrame, value: float = 0) -> pd.DataFrame:
    """Set domestic blocks to value (0 by default).

    Requires that the region is the top index in the multiindex
    hierarchy (default case in pymrio).

    Parameters
    ----------
    df : pd.DataFrame
    value : float, optional

    Returns
    -------
    pd.DataFrame

    """
    regions = df.index.get_level_values(0).unique()
    df_res = df.copy()
    for reg in regions:
        df_res.loc[reg, reg] = value
    return df_res


def set_block(arr, arr_block):
    """Set the diagonal blocks of an array to an given array.

    Parameters
    ----------
    arr : numpy ndarray
        the original array
    block_arr : numpy ndarray
        the block array for the new diagonal

    Returns
    -------
    numpy ndarray (the modified array)

    """
    nr_col = arr.shape[1]
    nr_row = arr.shape[0]

    nr_col_block = arr_block.shape[1]
    nr_row_block = arr_block.shape[0]

    if np.mod(nr_row, nr_row_block) or np.mod(nr_col, nr_col_block):
        raise ValueError("Number of rows/columns of the input array must be a multiple of block shape")
    if nr_row / nr_row_block != nr_col / nr_col_block:
        raise ValueError("Block array can not be filled as diagonal blocks in the given array")

    arr_out = arr.copy()

    for row_ind in range(int(nr_row / nr_row_block)):
        row_start = row_ind * nr_row_block
        row_end = nr_row_block + nr_row_block * row_ind
        col_start = row_ind * nr_col_block
        col_end = nr_col_block + nr_col_block * row_ind

        arr_out[row_start:row_end, col_start:col_end] = arr_block

    return arr_out


def unique_element(ll):
    """Return unique elements from a list preserving the original order."""
    seen = {}
    result = []
    for item in ll:
        if item in seen:
            continue
        seen[item] = 1
        result.append(item)
    return result


def build_agg_vec(agg_vec, **source):
    """Build an combined aggregation vector considering diff classifications.

    This function build an aggregation vector based on the order in agg_vec.
    The naming and actual mapping is given in source, either explicitly or by
    pointing to a folder with the mapping.


    Parameters
    ----------
    agg_vec : list
        A list of sector or regions to which the IOSystem shall be aggregated.
        The order in agg_vec is important:
        If a string was assigned to one specific entry it will not be
        overwritten if it is given in the next vector, e.g.  ['EU', 'OECD']
        would aggregate first into EU and the remaining one into OECD, whereas
        ['OECD', 'EU'] would first aggregate all countries into OECD and than
        the remaining countries into EU.

    source : list or string
        Definition of the vectors in agg_vec.  The input vectors (either in the
        file or given as list for the entries in agg_vec) must be as long as
        the desired output with a string for every position which should be
        aggregated and None for position which should not be used.

        Special keywords:

            - path : Path to a folder with concordance matrices.
                     The files in the folder can have any extension but must be
                     in text format (tab separated) with one entry per row.
                     The last column in the file will be taken as aggregation
                     vectors (other columns can be used for documentation).
                     Values must be given for every entry in the original
                     classification (string None for all values not used) If
                     the same entry is given in source and as text file in
                     path than the one in source will be used.

                     Two special path entries are available so far:

                     - 'exio2'
                       Concordance matrices for EXIOBASE 2.0
                     - 'test'
                       Concordance matrices for the test IO system

                     If a entry is not found in source and no path is given
                     the current directory will be searched for the definition.

            - miss : Entry to use for missing values, default: 'REST'

    Returns
    -------
    list
        The aggregation vector

    Examples
    --------
    >>> build_agg_vec(['EU', 'OECD'], path = 'test')
    ['EU', 'EU', 'EU', 'OECD', 'REST', 'REST']

    >>> build_agg_vec(['OECD', 'EU'], path = 'test', miss='RoW')
    ['OECD', 'EU', 'OECD', 'OECD', 'RoW', 'RoW']

    >>> build_agg_vec(['EU', 'orig_regions'], path = 'test')
    ['EU', 'EU', 'EU', 'reg4', 'reg5', 'reg6']

    >>> build_agg_vec(['supreg1', 'other'], path = 'test',
    >>>        other = [None, None, 'other1', 'other1', 'other2', 'other2'])
    ['supreg1', 'supreg1', 'other1', 'other1', 'other2', 'other2']



    """
    # build a dict with aggregation vectors in source and folder
    # TODO: the logic here should be moved to constants
    if type(agg_vec) is str:
        agg_vec = [agg_vec]
    agg_dict = {}
    for entry in agg_vec:
        try:
            agg_dict[entry] = source[entry]
        except KeyError:
            folder = source.get("path", "./")
            folder = os.path.join(PYMRIO_PATH[folder], "concordance")
            for file in os.listdir(folder):
                if entry == os.path.splitext(file)[0]:
                    _tmp = np.genfromtxt(os.path.join(folder, file), dtype=str)
                    if _tmp.ndim == 1:
                        agg_dict[entry] = [None if ee == "None" else ee for ee in _tmp.tolist()]
                    else:
                        agg_dict[entry] = [None if ee == "None" else ee for ee in _tmp[:, -1].tolist()]
                    break
            else:
                logging.error(f"Aggregation vector -- {str(entry)} -- not found")

    # build the summary aggregation vector
    def _rep(ll, ii, vv):
        ll[ii] = vv

    miss_val = source.get("miss", "REST")

    vec_list = [agg_dict[ee] for ee in agg_vec]
    out = [
        None,
    ] * len(vec_list[0])
    for currvec in vec_list:
        if len(currvec) != len(out):
            logging.warning("Inconsistent vector length")
        [_rep(out, ind, val) for ind, val in enumerate(currvec) if not out[ind]]

    [_rep(out, ind, miss_val) for ind, val in enumerate(out) if not val]

    return out


def find_first_number(ll):
    """Return nr of first entry parseable to float in ll, None otherwise."""
    for nr, entry in enumerate(ll):
        try:
            float(entry)
        except (ValueError, TypeError):
            pass
        else:
            return nr
    return None


def sniff_csv_format(
    csv_file,
    potential_sep=None,
    max_test_lines=10,
    zip_file=None,
):
    r"""Attempt to get the separator, nr of index cols and header rows in a csv file.

    Parameters
    ----------
    csv_file: str
        Path to a csv file

    potential_sep: list, optional
        List of potential separators (delimiters) to test.
        Default: '\t', ',', ';', '|', '-', '_' (used when passing None)

    max_test_lines: int, optional
        How many lines to test, default: 10 or available lines in csv_file

    zip_file: str, optional
        Path to a zip file containing the csv file (if any, default: None).
        If a zip file is given, the path given at 'csv_file' is assumed
        to be the path to the file within the zip_file.

    Returns
    -------
        dict with
            sep: string (separator)
            nr_index_col: int
            nr_header_row: int

        Entries are set to None if inconsistent information in the file
    """
    potential_sep = potential_sep if potential_sep else ["\t", ",", ";", "|", "-", "_"]

    def read_first_lines(filehandle):
        lines = []
        for _ in range(max_test_lines):
            line = filehandle.readline()
            if line == "":
                continue
            try:
                line = line.decode("utf-8")
            except AttributeError:
                pass
            lines.append(line[:-1])
        return lines

    if zip_file:
        with zipfile.ZipFile(zip_file, "r") as zz:
            with zz.open(csv_file, "r") as ff:
                test_lines = read_first_lines(ff)
    else:
        with open(csv_file) as ff:
            test_lines = read_first_lines(ff)

    sep_aly_lines = [
        sorted(
            [(line.count(sep), sep) for sep in potential_sep if line.count(sep) > 0],
            key=lambda x: x[0],
            reverse=True,
        )
        for line in test_lines
    ]

    sep = None
    for nr, (count, sep) in enumerate(sep_aly_lines[0]):
        for line in sep_aly_lines:
            if line[nr][0] == count:
                break
        else:
            sep = None

        if sep:
            break

    lines_with_sep = [line for line in test_lines if sep in line]

    nr_header_row = None
    nr_index_col = None

    if sep:
        nr_index_col = find_first_number(lines_with_sep[-1].split(sep))
        if nr_index_col:
            for header_row, line in enumerate(lines_with_sep):
                nr_header_row = header_row
                if find_first_number(line.split(sep)) == nr_index_col:
                    break

    return {"sep": sep, "nr_header_row": nr_header_row, "nr_index_col": nr_index_col}


def filename_from_url(url):
    """Extract a file name from the download link for that file.

    Parameters
    ----------
    url: str,
        The download link of the file

    Returns
    -------
    str,
        The extracted file name

    """
    name = re.search(r"[^/\\&?]+\.\w{2,7}(?=([?&].*$|$))", url)
    if name:
        return name.group()
    raise ValueError("Could not extract filename from url")


def check_if_long(df, value_name=LONG_VALUE_NAME):
    """Check if a given DataFrame follows is in a long format.

    Currently this only checks if 'value_name' is in the columns.
    In no parameter is given, it uses the default value 'value', defined
    in constants.py

    Note:
    -----
    This function does not check if the DataFrame is actually in a long format,
    it only checks if the DataFrame has a column with the name 'value_name'.
    There is an edge case of having 'value_name' as a column name, but not
    being in a long format. This function will return True in this case.

    Returns
    -------
    bool
        True if the DataFrame is in a long format, False otherwise
    """
    if not isinstance(df, pd.DataFrame) or isinstance(df, pd.Series):
        return False

    # TODO: refactor once we have these in the constants.py
    if isinstance(df, pd.DataFrame):
        if "region" in df.columns.names:
            return False
        if "sector" in df.columns.names:
            return False
        if "category" in df.columns.names:
            return False

    if value_name not in df.columns:
        return False
    return True


def to_long(df, value_name=LONG_VALUE_NAME):
    """Convert the pymrio matrix df format to a long format.

    FIX: All index and columns become separate columns (not index!)

    Parameters
    ----------
    df: pymrio matrix
        The pymrio matrix (e.g. Z, F, etc) to convert

    value_name: str, optional
        The name of the value column, default: 'value'
        as defined in constants.py

    Returns
    -------
    pd.DataFrame
    """
    df_long = df.stack(df.columns.names)
    df_long.name = value_name
    df_long = pd.DataFrame(df_long)
    return df_long


def ssl_fix(*args, **kwargs):
    """Try to use a request connection with Lagacy option when normal connection fails.

    Parameters
    ----------
    Parameters of a normal requests.get() function
        url: URL for the new :class:`Request` object.
        params: (optional) Dictionary, list of tuples or bytes to send
        in the query string for the class `Request`.
        **kwargs: Optional arguments that `request` takes.

    Returns
    -------
        r: class:`Response <Response>` object
    """

    class CustomHttpAdapter(HTTPAdapter):
        # "Transport adapter" that allows us to use custom ssl_context.

        def __init__(self, ssl_context=None, **kwargs):
            self.ssl_context = ssl_context
            super().__init__(**kwargs)

        def init_poolmanager(self, connections, maxsize, block=False):
            self.poolmanager = urllib3.poolmanager.PoolManager(
                num_pools=connections,
                maxsize=maxsize,
                block=block,
                ssl_context=self.ssl_context,
            )

    try:
        r = requests.get(*args, **kwargs)
    except Exception:
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        session = requests.session()
        session.mount("https://", CustomHttpAdapter(ctx))
        r = session.get(*args, **kwargs)

    return r


def index_fullmatch(df_ix, find_all=None, **kwargs):
    """Fullmatch regex on index of df_ix.

    Similar to pandas str.fullmatch, thus the whole
    string of the index must match.

    The index levels need to be named (df.index.name needs to
    be set for all levels).

    Note:
    -----
    Arguments are set to case=True, flags=0, na=False, regex=True.
    For case insensitive matching, use (?i) at the beginning of the pattern.

    See the pandas/python.re documentation for more details.


    Parameters
    ----------
    df_ix : pd.DataFrame, pd.Series, pd.Index or pd.MultiIndex
        Method works on Index directly or extract from DataFrame/Series
    find_all : None or str
        If str (regex pattern) search for all matches in all index levels.
        All matching rows are returned. The remaining kwargs are ignored.
    kwargs : dict
        The regex to match. The keys are the index names,
        the values are the regex to match.
        If the entry is not in index name, it is ignored silently.

    Returns
    -------
    pd.DataFrame, pd.Series, pd.Index or pd.MultiIndex
        The matched rows/index, same type as _dfs_idx

    """
    return _index_regex_matcher(_dfs_idx=df_ix, _method="fullmatch", _find_all=find_all, **kwargs)


def index_match(df_ix, find_all=None, **kwargs):
    """Match regex on index of df_ix.

    Similar to pandas str.match, thus the start of the index string must match.

    The index levels need to be named (df.index.name needs to
    be set for all levels).

    Note:
    -----
    Arguments are set to case=True, flags=0, na=False, regex=True.
    For case insensitive matching, use (?i) at the beginning of the pattern.

    See the pandas/python.re documentation for more details.


    Parameters
    ----------
    df_ix : pd.DataFrame, pd.Series, pd.Index or pd.MultiIndex
        Method works on Index directly or extract from DataFrame/Series
    find_all : None or str
        If str (regex pattern) search for all matches in all index levels.
        All matching rows are returned. The remaining kwargs are ignored.
    kwargs : dict
        The regex to match. The keys are the index names,
        the values are the regex to match.
        If the entry is not in index name, it is ignored silently.

    Returns
    -------
    pd.DataFrame, pd.Series, pd.Index or pd.MultiIndex
        The matched rows/index, same type as _dfs_idx

    """
    return _index_regex_matcher(_dfs_idx=df_ix, _method="match", _find_all=find_all, **kwargs)


def index_contains(df_ix, find_all=None, **kwargs):
    """Check if index contains a regex pattern.

    Similar to pandas str.contains, thus the index
    string must contain the regex pattern.

    The index levels need to be named (df.index.name needs to
    be set for all levels).

    Note:
    -----
    Arguments are set to case=True, flags=0, na=False, regex=True.
    For case insensitive matching, use (?i) at the beginning of the pattern.

    See the pandas/python.re documentation for more details.


    Parameters
    ----------
    df_ix : pd.DataFrame, pd.Series, pd.Index or pd.MultiIndex
        Method works on Index directly or extract from DataFrame/Series
    find_all : None or str
        If str (regex pattern) search for all matches in all index levels.
        All matching rows are returned. The remaining kwargs are ignored.
    kwargs : dict
        The regex to match. The keys are the index names,
        the values are the regex to match.
        If the entry is not in index name, it is ignored silently.

    Returns
    -------
    pd.DataFrame, pd.Series, pd.Index or pd.MultiIndex
        The matched rows/index, same type as _dfs_idx

    """
    return _index_regex_matcher(_dfs_idx=df_ix, _method="contains", _find_all=find_all, **kwargs)


def _index_regex_matcher(_dfs_idx, _method, _find_all=None, **kwargs):
    """Match index of df with regex.

    The generic method for the contain, match, fullmatch implementation
    along the index of the pymrio dataframes.

    The index levels need to be named (df.index.name needs to
    be set for all levels).

    Note:
    -----
    Arguments are set to case=True, flags=0, na=False, regex=True.
    For case insensitive matching, use (?i) at the beginning of the pattern.

    See the pandas/python.re documentation for more details.


    Parameters
    ----------
    _dfs_idx : pd.DataFrame, pd.Series, pd.Index or pd.MultiIndex
        Method works on Index directly or extract from DataFrame/Series
    _method : str
        The method to use for matching, one of 'contains', 'match', 'fullmatch'
    _find_all : None or str
        If str (regex pattern) search for all matches in all index levels.
        All matching rows are returned. The remaining kwargs are ignored.
    kwargs : dict
        The regex to match. The keys are the index names,
        the values are the regex to match.
        If the entry is not in index name, it is ignored silently.

    Returns
    -------
    pd.DataFrame, pd.Series, pd.Index or pd.MultiIndex
        The matched rows/index, same type as _dfs_idx

    """
    if _method not in ["contains", "match", "fullmatch"]:
        raise ValueError('Method must be one of "contains", "match", "fullmatch"')

    if _find_all is not None:
        if type(_dfs_idx) in [pd.DataFrame, pd.Series]:
            idx = _dfs_idx.index
        elif type(_dfs_idx) in [pd.Index, pd.MultiIndex]:
            idx = _dfs_idx
        else:
            raise ValueError("Type of _dfs_idx must be one of pd.DataFrame, pd.Series, pd.Index or pd.MultiIndex")
        found = np.array([], dtype=int)
        for idx_name in idx.names:
            fun = getattr(idx.get_level_values(idx_name).str, _method)
            ff = idx[fun(_find_all, case=True, flags=0, na=False)]
            found = np.append(found, idx.get_indexer(ff))
        found = np.unique(found)
        if type(_dfs_idx) in [pd.DataFrame, pd.Series]:
            return _dfs_idx.iloc[found]
        return _dfs_idx[found]

    at_least_one_valid = False
    for key, value in kwargs.items():
        try:
            if type(_dfs_idx) in [pd.DataFrame, pd.Series]:
                fun = getattr(_dfs_idx.index.get_level_values(key).str, _method)
            elif type(_dfs_idx) in [pd.Index, pd.MultiIndex]:
                fun = getattr(_dfs_idx.get_level_values(key).str, _method)
            else:
                raise ValueError("Type of _dfs_idx must be one of pd.DataFrame, pd.Series, pd.Index or pd.MultiIndex")
            _dfs_idx = _dfs_idx[fun(value, case=True, flags=0, na=False)]
            at_least_one_valid = True
        except KeyError:
            pass

    if not at_least_one_valid:
        if type(_dfs_idx) in [pd.DataFrame, pd.Series]:
            _dfs_idx = pd.DataFrame(columns=_dfs_idx.columns)
        elif type(_dfs_idx) in [pd.Index, pd.MultiIndex]:
            _dfs_idx = pd.Index([])

    return _dfs_idx


def _characterize_get_requried_col(
    factors,
    ext_index_names,
    characterized_name_column,
    characterization_factors_column,
    characterized_unit_column,
):
    """Check and return a list of required columns.

    For paramters naming see function characterize.

    """
    req_index = ext_index_names.copy()

    if "region" in factors.columns:
        req_index.append("region")
    if "sector" in factors.columns:
        req_index.append("sector")

    required_columns = req_index + [
        characterization_factors_column,
        characterized_name_column,
        characterized_unit_column,
    ]

    if not set(required_columns).issubset(set(factors.columns)):
        raise ValueError("Not all required columns in the passed DataFrame >factors<")

    return namedtuple("ret_val", ["required_index_col", "all_required_columns"])(req_index, required_columns)


def _validate_characterization_table(
    factors,
    all_required_col,
    regions,
    sectors,
    ext_unit,
    characterized_name_column="impact",
    characterized_unit_column="impact_unit",
    orig_unit_column="stressor_unit",
):
    """Check a factors sheet for characterization (internal function).

    This should not be called directly, use characterize with only_validation instead.

    Given a factors sheet reports error in

        - unit errors (impact unit consistent, stressor unit match).
            Note: does not check if the conversion is correct!
        - report missing stressors, regions, sectors which are in factors
            but not in the extension
        - if factors are specified for all regions/sectors of the extension

    Besides the unit errors, factors can still be passed to the characterization
    routine, and missing data will be assumed to be 0.

    Parameters follow the convention of the characterization method:

    Parameters
    ----------
    factors: pd.DataFrame
        A dataframe in long format with numerical index and columns named
        index.names of the extension to be characterized and
        'characterized_name_column', 'characterization_factors_column',
        'characterized_unit_column', 'orig_unit_column'

    regions: Index
        Regions in the mrio object (from get_regions())

    sectors: Index
        Sectors in the mrio object (from get_sectors())

    ext_unit: pd.DataFrame
        The mrio.unit dataframe

    characterized_name_column: str (optional)
        Name of the column with the names of the
        characterized account (default: "impact")

    characterization_factors_column: str (optional)
        Name of the column with the factors for the
        characterization (default: "factor")

    characterized_unit_column: str (optional)
        Name of the column with the units of the characterized accounts
        characterization (default: "impact_unit")

    Returns
    -------
    pd.DataFrame: factors sheet with additional error columns

    """
    # searching the next available df to get the
    # index of stressors/regions/sector depending on input

    fac = factors.copy()

    fac.loc[:, "error_unit_impact"] = False
    fac.loc[:, "error_unit_stressor"] = False
    fac.loc[:, "error_missing_stressor"] = False

    if "region" in fac.columns:
        fac.loc[:, "error_missing_region"] = False
    if "sector" in fac.columns:
        fac.loc[:, "error_missing_sector"] = False

    unique_impacts = fac.loc[:, characterized_name_column].unique()

    # Check for consistent units per impact
    for imp in unique_impacts:
        if not (
            fac.loc[
                fac.loc[:, characterized_name_column] == imp,
                characterized_unit_column,
            ]
            .eq(
                fac.loc[
                    fac.loc[:, characterized_name_column] == imp,
                    characterized_unit_column,
                ].iloc[0]
            )
            .all()
        ):
            fac.loc[
                fac.loc[:, characterized_name_column] == imp,
                "error_unit_impact",
            ] = True

    # unit per stressor check
    fac = fac.set_index(ext_unit.index.names).sort_index()
    if "unit" in fac.columns:
        um = fac.join(ext_unit, how="inner", rsuffix="_ext_orig")
        ext_unit_col = "unit_ext_orig"
    else:
        um = fac.join(ext_unit, how="inner")
        ext_unit_col = "unit"
    fac = fac.reset_index()
    um = um.reset_index()

    fac.error_unit_stressor = fac.error_unit_stressor.astype("object")
    fac.loc[:, "error_unit_stressor"] = um.loc[:, orig_unit_column] != um.loc[:, ext_unit_col]
    with pd.option_context("future.no_silent_downcasting", True):
        fac.loc[:, "error_unit_stressor"] = fac.loc[:, "error_unit_stressor"].fillna(False)
    fac.error_unit_stressor = fac.error_unit_stressor.infer_objects(copy=False)

    fac = fac.set_index(ext_unit.index.names).sort_index()
    for row in fac.index.unique():
        # Stressor not in the extension
        if row not in ext_unit.index:
            fac.loc[row, "error_missing_stressor"] = True
            continue

        # Checking for region/sector data
        # This covers if not all regions present in the mrio
        # are specified in the factors sheet.
        # In that case, the full error_missing_region/sector for the
        # the full region is set to True
        if "region" in all_required_col:
            reg_cov = (
                fac.loc[row, ["region", characterized_name_column]].groupby(characterized_name_column).region.apply(set)
            )
            for improw in reg_cov.index:
                if len(regions.difference(reg_cov[improw])) > 0:
                    fac.loc[row, "error_missing_region"] = True

        if "sector" in all_required_col:
            reg_cov = (
                fac.loc[row, ["sector", characterized_name_column]].groupby(characterized_name_column).sector.apply(set)
            )
            for improw in reg_cov.index:
                if len(sectors.difference(reg_cov[improw])) > 0:
                    fac.loc[row, "error_missing_sector"] = True

    # check if additional region/sectors in the data
    if "region" in all_required_col:
        for reg in fac.region.unique():
            if reg not in regions:
                fac.loc[fac.region == reg, "error_missing_region"] = True
    if "sector" in all_required_col:
        for sec in fac.sector.unique():
            if sec not in sectors:
                fac.loc[fac.sector == sec, "error_missing_sector"] = True

    return fac.reset_index()


def extend_rows(df, **kwargs):
    """Given a df, duplicate rows by spreading one columns.

    This function takes a dataframe (e.g. a bridge or characterization specs),
    and spreads rows based on the input given in the keyword arguments.

    Each keyword can be a column header, with the argument being a dict with the
    values to be spread.

    Example:
    -------
    >>> df = pd.DataFrame(
    ...     {
    ...         "region": ["GLO", "GLO", "GLO"],
    ...         "sector": ["A", "B", "C"],
    ...         "value": [1, 2, 3],
    ...     }
    ... )
    >>> extend_rows(df, region={"GLO": ["reg1", "reg2", "reg3"]},
    ...             sector={"B": ["b1", "b2"]})
       region sector  value
    0    reg1      A      1
    1    reg1      C      3
    2    reg2      A      1
    3    reg2      C      3
    4    reg3      A      1
    5    reg3      C      3
    6    reg1     b1      2
    7    reg2     b1      2
    8    reg3     b1      2
    9    reg1     b2      2
    10   reg2     b2      2
    11   reg3     b2      2

    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to extend with rows. Must have a numerical index.
    **kwargs : dict
        Column names as keys and dictionaries as values. Each dictionary maps
        original values in the column to lists of new values that will replace
        the original value in the new rows.

    Returns
    -------
    pandas.DataFrame
        A new DataFrame with rows spread according to the mapping in kwargs,
        sorted by the columns specified in kwargs.

    Raises
    ------
    ValueError
        If the DataFrame index is not a RangeIndex (numerical)
        If a specified column in kwargs is not in the DataFrame
        If no rows are found to spread for a value specified in the mapping


    """
    if not pd.api.types.is_numeric_dtype(df.index):
        raise ValueError("DataFrame index must be numerical")

    result = df.copy()

    for column, mapping in kwargs.items():
        if column not in result.columns:
            raise ValueError(f"Column {column} not in DataFrame")
        for original_value, new_values in mapping.items():
            new_dfs = []
            # Select rows with the original value in the specified column
            rows_to_spread = result[result[column] == original_value]
            if rows_to_spread.empty:
                raise ValueError(f"No rows found to spread for value: {original_value}")
            # Create new dataframes with the new values
            for new_value in new_values:
                new_df = rows_to_spread.copy()
                new_df[column] = new_value
                new_dfs.append(new_df)
            # Remove the original rows that have been spread
            if new_dfs:
                result = result[result[column] != original_value]
                result = pd.concat([result] + new_dfs, ignore_index=True)

    return result.sort_values(by=list(kwargs.keys()))


def check_df_map(df_orig, df_map):
    """Check which entries of df_map would be in effect given df_orig."""
    # TODO: we need a way to check for spelling mistakes
    # and other hickups sneaking into df_map.
    # In this function, we check for each line of df_map which entries
    # would be in effect given df_orig.
    pass


# CONT:
# TODO: bridge column indicator as argument (also update convert notebook)
# TODO: new default <->


def convert(
    df_orig,
    df_map,
    agg_func="sum",
    drop_not_bridged_index=True,
    ignore_columns=None,
    reindex=None,
):
    """Convert a DataFrame to a new classification.

    Parameters
    ----------
    df_orig : pd.DataFrame
        The DataFrame to process.
        The index/columns levels need to be named (df.index.name
        and df.columns.names needs to be set for all levels).
        All index to be bridged to new names need to be in the index (these are columns
        indicated with two underscores '__' in the mapping dataframe, df_map).
        Other constraining conditions (e.g. regions, sectors) can be either
        in the index or columns. If the same name exists in the
        index and columns, the values in index are preferred.

    df_map : pd.DataFrame
        The DataFrame with the mapping of the old to the new classification.
        This requires a specific structure, which depends on the structure of the
        dataframe to be characterized:

        - Constraining data (e.g. stressors, regions, sectors) can be
          either in the index or columns of df_orig. The need to have the same
          name as the named index or column in df_orig. The algorithm searches
          for matching data in df_orig based on all constraining columns in df_map.

        - Bridge columns are columns with '__' in the name. These are used to
          map (bridge) some/all of the constraining columns in df_orig to the new
          classification.

        - One column "factor", which gives the multiplication factor for the
          conversion. If it is missing, it is set to 1.


        This is better explained with an example.
        Assuming a original dataframe df_orig with
        index names 'stressor' and 'compartment' and column name 'region',
        the characterizing dataframe could have the following structure (column names):

        stressor ... original index name
        compartment ... original index name
        region ... original column name
        factor ... the factor for multiplication/characterization
            If no factor is given, the factor is assumed to be 1.
            This can be used, to simplify renaming/aggregation mappings.
        impact__stressor ... the new index name,
            replacing the previous index name "stressor".
            Thus here "stressor" will be renamed to "impact", and the row index
            will be renamed by the entries here.
        compartment__compartment ... the new compartment,
            replacing the original compartment. No rename of column happens here,
            still row index will be renamed as given here.

        the columns with __ are called bridge columns, they are used
        to match the original index. The new dataframe with have index names
        based on the first part of the bridge column, in the order
        in which the bridge columns are given in the mapping dataframe.

        "region" is constraining column, these can either be for the index or column
        in df_orig. In case both exist, the one in index is preferred.


    agg_func : str or func
        the aggregation function to use for multiple matchings (summation by default)

    drop_not_bridged_index : bool, optional
        What to do with index levels in df_orig not appearing in the bridge columns.
        If True, drop them after aggregation across these, if False,
        pass them through to the result.

        *Note:* Only index levels will be dropped, not columns.

        In case some index levels need to be dropped, and some not
        make a bridge column for the ones to be dropped and map all to the same name.
        Then drop this index level after the conversion.

    ignore_columns : list, optional
        List of column names in df_map which should be ignored.
        These could be columns with additional information, unit columns, etc.

    reindex: str, None or collection
        Wrapper for pandas' reindex method to control return order.
        - If None: sorts the index alphabetically.
        - If str: uses the unique value order from the bridge column as the index order.
        - For other types (e.g., collections): passes directly to pandas.reindex.

    """
    bridge_columns = [col for col in df_map.columns if "__" in col]

    # groupby breaks with NaNs or None, fix it here
    df_map.loc[:, bridge_columns] = df_map.loc[:, bridge_columns].fillna("")

    unique_new_index = df_map.loc[:, bridge_columns].drop_duplicates().set_index(bridge_columns).index

    bridge_components = namedtuple("bridge_components", ["new", "orig", "raw"])
    bridges = []

    if not ignore_columns:
        ignore_columns = []

    if isinstance(df_orig, pd.Series):
        df_orig = pd.DataFrame(df_orig)

    # some consistency checks of arguments and restructuring if everything is ok
    if len(bridge_columns) == 0:
        raise ValueError("No columns with '__' in the mapping DataFrame")
    for col in bridge_columns:
        if col.count("__") == 1:
            bridge = bridge_components(*col.split("__"), col)
        else:
            raise ValueError(f"Column {col} contains more then one '__'")
        if bridge.orig not in df_map.columns:
            raise ValueError(f"Column {bridge.orig} not in df_map")
        if (bridge.orig not in df_orig.index.names) and (bridge.orig not in df_orig.columns.names):
            raise ValueError(f"Column {bridge.orig} not in df_orig")
        bridges.append(bridge)

    orig_index_not_bridged = [ix for ix in df_orig.index.names if ix not in [b.orig for b in bridges]]

    df_map = df_map.set_index(bridge_columns)

    stacked_columns = []
    orig_column_index = df_orig.columns
    for col in df_map.columns:
        if col in (["factor"] + ignore_columns):
            continue
        if col not in df_orig.index.names:
            if col in df_orig.columns.names:
                df_orig = df_orig.stack(col, future_stack=True)
                stacked_columns.append(col)
                if isinstance(df_orig, pd.Series):
                    df_orig.name = "FOO_CONVERT_REMOVE"
                    df_orig = pd.DataFrame(df_orig)
            else:
                print("TODO: log warning for missing column")

    res_collector = []

    # loop over each new impact/characterized value
    # and collect entries, multiply and rename
    for entry in unique_new_index:
        df_cur_map = df_map.loc[[entry]]
        collector = []

        # the loop for getting all (potential regex) matches and multiplication
        for row in df_cur_map.iterrows():
            matched_entries = index_fullmatch(df_ix=df_orig, **row[1].to_dict())
            try:
                mul_entries = matched_entries * row[1].factor
            except AttributeError:
                mul_entries = matched_entries
            collector.append(mul_entries)

        df_collected = pd.concat(collector, axis=0)

        # renaming part, checks if the old name (bridge.orig) is in the current index
        # and renames by the new one (bridge.new)

        already_renamed = {}

        for bridge in bridges:
            # encountering a bridge with the same orig name but which should
            # lead to two new index levels
            if bridge.orig in already_renamed:
                # already renamed the index to another one previously,
                # but we need to create more index levels for the
                # same original index level
                new_index_value = df_cur_map.index.get_level_values(bridge.raw)[0]
                _old_index = df_collected.index.to_frame()
                # as we go along in order, we add them to the end of the index
                _old_index.insert(len(_old_index.columns), bridge.new, new_index_value)
                df_collected.index = pd.MultiIndex.from_frame(_old_index)

            else:
                for idx_old_names in df_collected.index.names:
                    if bridge.orig in idx_old_names:
                        # rename the index names
                        if isinstance(df_collected.index, pd.MultiIndex):
                            df_collected.index = df_collected.index.set_names(bridge.new, level=idx_old_names)
                        else:
                            df_collected.index = df_collected.index.set_names(bridge.new, level=None)

                        # rename the actual index values
                        df_collected = df_collected.reset_index(level=bridge.new)
                        for row in df_cur_map.reset_index().iterrows():
                            new_row_name = row[1][bridge.raw]
                            old_row_name = row[1][bridge.orig]
                            df_collected.loc[:, bridge.new] = df_collected.loc[:, bridge.new].str.replace(
                                pat=old_row_name, repl=new_row_name, regex=True
                            )

                        # put the index back
                        if df_collected.index.name is None:
                            # The case with a single index where the
                            # previous reset index
                            # left only a numerical index
                            df_collected = df_collected.set_index(bridge.new, drop=True, append=False)
                        else:
                            df_collected = df_collected.set_index(bridge.new, drop=True, append=True)

                        already_renamed[bridge.orig] = bridge

        res_collector.append(df_collected.groupby(by=df_collected.index.names).agg(agg_func))

    all_result = pd.concat(res_collector, axis=0)

    if len(stacked_columns) > 0:
        all_result = all_result.unstack(stacked_columns)
        try:
            all_result = all_result.loc[:, "FOO_CONVERT_REMOVE"]
        except KeyError:
            pass
        if len(orig_column_index.names) > 1:
            all_result = all_result.reorder_levels(orig_column_index.names, axis=1)
        all_result = all_result.reindex(columns=orig_column_index)

    if drop_not_bridged_index:
        all_result = all_result.reset_index(level=orig_index_not_bridged, drop=True)
    else:
        # move the not bridged index levels to the end of the index
        new_index = [ix for ix in all_result.index.names if ix not in orig_index_not_bridged]
        try:
            all_result = all_result.reorder_levels(new_index + orig_index_not_bridged)
        except TypeError:  # case where there is only one index level
            pass

    grouped = all_result.groupby(by=all_result.index.names).agg(agg_func)

    if reindex is not None:
        if isinstance(reindex, str):
            df_map = df_map.reset_index()
            if reindex in bridge_columns:
                grouped_order = grouped.reindex(index=df_map.loc[:, reindex].unique())
            else:
                raise ValueError(
                    f"Reindexing by {reindex} is not possible, it is not a bridge column in the mapping DataFrame."
                )
        else:
            grouped_order = grouped.reindex(index=reindex)
    else:
        grouped_order = grouped.sort_index()

    return grouped_order
