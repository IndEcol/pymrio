"""
Utility function for pymrio

KST 20140502
"""
import json
import logging
import os
import zipfile
from collections import namedtuple
from pathlib import Path

import numpy as np

from pymrio.core.constants import DEFAULT_FILE_NAMES, PYMRIO_PATH


def is_vector(inp):
    """Returns true if the input can be interpreted as a 'true' vector

    Note
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
    if nr_dim == 1:
        return True
    elif (nr_dim == 2) and (1 in inp.shape):
        return True
    else:
        return False


def get_repo_content(path):
    """List of files in a repo (path or zip)


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
    """Generic method to read the file parameter file

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
                para_file_full_path = (
                    para_file_folder + "/" + DEFAULT_FILE_NAMES["filepara"]
                ).replace("//", "/")
            else:
                para_file_full_path = DEFAULT_FILE_NAMES["filepara"]

        else:
            para_file_full_path = os.path.join(
                para_file_folder, DEFAULT_FILE_NAMES["filepara"]
            )
    else:
        para_file_full_path = para_file_folder
        para_file_folder = os.path.dirname(para_file_full_path)

    if para_file_full_path not in files:
        raise FileNotFoundError(
            "File parameter file {} not found".format(para_file_full_path)
        )

    if zipfile.is_zipfile(str(path)):
        with zipfile.ZipFile(file=str(path)) as zf:
            para_file_content = json.loads(zf.read(para_file_full_path).decode("utf-8"))
    else:
        with open(para_file_full_path, "r") as pf:
            para_file_content = json.load(pf)

    return namedtuple("file_parameter", ["folder", "name", "content"])(
        para_file_folder, os.path.basename(para_file_full_path), para_file_content
    )


def build_agg_matrix(agg_vector, pos_dict=None):
    """Agg. matrix based on mapping given in input as numerical or str vector.

    The aggregation matrix has the from nxm with

    -n  new classificaction
    -m  old classification

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

    Example 1:
        input vector: np.array([0, 1, 1, 2]) or ['a', 'b', 'b', 'c']

        agg matrix:

           m0  m1  m2  m3
        n0 1   0   0   0
        n1 0   1   1   0
        n2 0   0   0   1

    Example 2:
        input vector: np.array([1, 0, 0, 2]) or
                      (['b', 'a', 'a', 'c'], dict(a=0,b=1,c=2))

        agg matrix:

           m0  m1  m2  m3
        n0 0   1   1   0
        n1 1   0   0   0
        n2 0   0   0   1
    """
    if isinstance(agg_vector, np.ndarray):
        agg_vector = agg_vector.flatten().tolist()

    if type(agg_vector[0]) == str:
        str_vector = agg_vector
        agg_vector = np.zeros(len(str_vector))
        if pos_dict:
            if len(pos_dict.keys()) != len(set(str_vector)):
                raise ValueError(
                    "Posistion elements inconsistent with aggregation vector"
                )
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


def diagonalize_blocks(arr, blocksize):
    """Diagonalize sections of columns of an array for the whole array

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

    Example
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
        raise ValueError(
            "Number of rows of input array must be a multiple of blocksize"
        )

    arr_diag = np.zeros((nr_row, blocksize * nr_col))

    for col_ind, col_val in enumerate(arr.T):
        col_start = col_ind * blocksize
        col_end = blocksize + col_ind * blocksize
        for _ind in range(int(nr_row / blocksize)):
            row_start = _ind * blocksize
            row_end = blocksize + _ind * blocksize
            arr_diag[row_start:row_end, col_start:col_end] = np.diag(
                col_val[row_start:row_end]
            )

    return arr_diag


def set_block(arr, arr_block):
    """Sets the diagonal blocks of an array to an given array

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
        raise ValueError(
            "Number of rows/columns of the input array "
            "must be a multiple of block shape"
        )
    if nr_row / nr_row_block != nr_col / nr_col_block:
        raise ValueError(
            "Block array can not be filled as " "diagonal blocks in the given array"
        )

    arr_out = arr.copy()

    for row_ind in range(int(nr_row / nr_row_block)):
        row_start = row_ind * nr_row_block
        row_end = nr_row_block + nr_row_block * row_ind
        col_start = row_ind * nr_col_block
        col_end = nr_col_block + nr_col_block * row_ind

        arr_out[row_start:row_end, col_start:col_end] = arr_block

    return arr_out


def unique_element(ll):
    """ returns unique elements from a list preserving the original order """
    seen = {}
    result = []
    for item in ll:
        if item in seen:
            continue
        seen[item] = 1
        result.append(item)
    return result


def build_agg_vec(agg_vec, **source):
    """Builds an combined aggregation vector based on various classifications

    This function build an aggregation vector based on the order in agg_vec.
    The naming and actual mapping is given in source, either explicitly or by
    pointing to a folder with the mapping.

    >>> build_agg_vec(['EU', 'OECD'], path = 'test')
    ['EU', 'EU', 'EU', 'OECD', 'REST', 'REST']

    >>> build_agg_vec(['OECD', 'EU'], path = 'test', miss='RoW')
    ['OECD', 'EU', 'OECD', 'OECD', 'RoW', 'RoW']

    >>> build_agg_vec(['EU', 'orig_regions'], path = 'test')
    ['EU', 'EU', 'EU', 'reg4', 'reg5', 'reg6']

    >>> build_agg_vec(['supreg1', 'other'], path = 'test',
    >>>        other = [None, None, 'other1', 'other1', 'other2', 'other2'])
    ['supreg1', 'supreg1', 'other1', 'other1', 'other2', 'other2']


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
    list (aggregation vector)

    """

    # build a dict with aggregation vectors in source and folder
    if type(agg_vec) is str:
        agg_vec = [agg_vec]
    agg_dict = dict()
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
                        agg_dict[entry] = [
                            None if ee == "None" else ee for ee in _tmp.tolist()
                        ]
                    else:
                        agg_dict[entry] = [
                            None if ee == "None" else ee for ee in _tmp[:, -1].tolist()
                        ]
                    break
            else:
                logging.error(
                    "Aggregation vector -- {} -- not found".format(str(entry))
                )

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
            logging.warn("Inconsistent vector length")
        [_rep(out, ind, val) for ind, val in enumerate(currvec) if not out[ind]]

    [_rep(out, ind, miss_val) for ind, val in enumerate(out) if not val]

    return out


def find_first_number(ll):
    """ Returns nr of first entry parseable to float in ll, None otherwise"""
    for nr, entry in enumerate(ll):
        try:
            float(entry)
        except (ValueError, TypeError) as e:
            pass
        else:
            return nr
    return None


def sniff_csv_format(
    csv_file,
    potential_sep=["\t", ",", ";", "|", "-", "_"],
    max_test_lines=10,
    zip_file=None,
):
    """Tries to get the separator, nr of index cols and header rows in a csv file

    Parameters
    ----------

    csv_file: str
        Path to a csv file

    potential_sep: list, optional
        List of potential separators (delimiters) to test.
        Default: '\t', ',', ';', '|', '-', '_'

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

    def read_first_lines(filehandle):
        lines = []
        for i in range(max_test_lines):
            line = ff.readline()
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
        with open(csv_file, "r") as ff:
            test_lines = read_first_lines(ff)

    sep_aly_lines = [
        sorted(
            [(line.count(sep), sep) for sep in potential_sep if line.count(sep) > 0],
            key=lambda x: x[0],
            reverse=True,
        )
        for line in test_lines
    ]

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
            for nr_header_row, line in enumerate(lines_with_sep):
                if find_first_number(line.split(sep)) == nr_index_col:
                    break

    return dict(sep=sep, nr_header_row=nr_header_row, nr_index_col=nr_index_col)
