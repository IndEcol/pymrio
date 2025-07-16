"""Extract data from MRIO timeseries."""

import re
from collections import OrderedDict
from pathlib import Path

from pymrio.core.fileio import load as mrioload


def apply_method(mrio, method, *args, **kwargs):
    """Apply a method to an object.

    Parameters
    ----------
    mrio : object
        The object to pass as the first argument to the function.
    method : str
        The method to apply.
    *args : tuple
        Additional positional arguments to pass to the function.
    **kwargs : dict
        Keyword arguments to pass to the function.

    Returns
    -------
    Any
        The result of the method call, usually the object
    """
    return getattr(mrio, method)(*args, **kwargs)


def apply_function(mrio, function, *args, **kwargs):
    """Apply a function to an object, passing the object as the first argument.

    Parameters
    ----------
    mrio : object
        The object to pass as the first argument to the function.
    function : callable
        The function to call.
    *args : tuple
        Additional positional arguments to pass to the function.
    **kwargs : dict
        Keyword arguments to pass to the function.

    Returns
    -------
    Any
        The result of the function call.
    """
    return function(mrio, *args, **kwargs)


def extract_from_mrioseries(mrios, key_naming, extension, account, index, columns):
    """Extract data from a MRIO timeseries.

    Loops through the data in folder and extracts data into a dict.

    Parameters
    ----------
    mrios: list of pathlib.Path or str
        List of mrios (file path) to extract data.

    key_naming: str or lambda function
        Naming of the dict keys.
        Possible values:
            - None: keys after the file/folder name of the mrio
            - "year": search for 4 digits in the folder/file
            - function: which except mrio name

    extension: str
        If None or str "core", extract from MRIO core (e.g. Z, Y, etc)
        Else, str to folder name of the extension

    account: str
        Which MRIO account to extract (e.g. D_cba, Z)

    index: valid pandas index
        Index to apply for account

    columns: valid pandas column index

    Returns
    -------
    OrderedDict
        with order as in MRIOs, and extracted data (pd.DataFrames) as values.

    """
    if type(mrios) in (Path, str):
        mrios = [mrios]

    mrios = [Path(mrio) for mrio in mrios]

    if type(account) is not str:
        raise TypeError(f"Account must be a string, got {str(type(account))}")

    if key_naming is None:
        mrdata = OrderedDict((m.name, m) for m in mrios)
    elif (type(key_naming) is str) and (key_naming.lower() == "year"):
        mrdata = OrderedDict((re.findall(r"\d{4}", m.name)[0], m) for m in mrios)
    else:
        mrdata = OrderedDict((key_naming(m.name), m) for m in mrios)

    if index is None or index == ":":
        index = slice(None)
    if columns is None or columns == ":":
        columns = slice(None)

    for key, val in mrdata.items():
        if extension is None or extension.lower() == "core":
            mrdata[key] = mrioload(val, subset=[account]).__dict__[account].loc[index, columns]
        else:
            if val.suffix == ".zip":
                mrdata[key] = (
                    mrioload(val, path_in_arc=extension, subset=[account]).__dict__[account].loc[index, columns]
                )
            else:
                mrdata[key] = mrioload(val / extension, subset=[account]).__dict__[account].loc[index, columns]
    return mrdata
