""" Mathematical functions for input output calculations

All methods here should follow the functional programming paradigm

Note
----
To avoid namespace pollution everythin here starts with calc_

"""

import typing
import warnings
from collections import namedtuple

import numpy as np
import pandas as pd

import pymrio.tools.ioutil as ioutil


def calc_x(Z, Y):
    """Calculate the industry output x from the Z and Y matrix

    industry output (x) = flows (sum_columns(Z)) + final demand (sum_columns(Y))

    Parameters
    ----------
    Z : pandas.DataFrame or numpy.array
        Symmetric input output table (flows)
    Y : pandas.DataFrame or numpy.array
        final demand with categories (1.order) for each country (2.order)

    Returns
    -------
    pandas.DataFrame or numpy.array
        Industry output x as column vector
        The type is determined by the type of Z. If DataFrame index as Z

    """
    x = np.reshape(np.sum(np.hstack((Z, Y)), 1), (-1, 1))
    if type(Z) is pd.DataFrame:
        x = pd.DataFrame(x, index=Z.index, columns=["indout"])
    if type(x) is pd.Series:
        x = pd.DataFrame(x)
    if type(x) is pd.DataFrame:
        x.columns = ["indout"]
    return x


def calc_x_from_L(L, y):
    """Calculate the industry output x from L and a y vector

    x = Ly

    The industry output x is computed from a demand vector y

    Parameters
    ----------
    L : pandas.DataFrame or numpy.array
        Symmetric input output Leontief table
    y : pandas.DataFrame or numpy.array
        a column vector of the total final demand

    Returns
    -------
    pandas.DataFrame or numpy.array
        Industry output x as column vector
        The type is determined by the type of L. If DataFrame index as L

    """
    x = L.dot(y)
    if type(x) is pd.Series:
        x = pd.DataFrame(x)
    if type(x) is pd.DataFrame:
        x.columns = ["indout"]
    return x


def calc_Z(A, x):
    """calculate the Z matrix (flows) from A and x

    A = Z / x[None, :]  =>  Z = A * x[None, :]

    By definition, the coefficient matrix A is basically the normalized flows
    So Z is just derived from A by un-normalizing using the industrial output x

    Parameters
    ----------
    A : pandas.DataFrame or numpy.array
        Symmetric input output table (coefficients)
    x : pandas.DataFrame or numpy.array
        Industry output column vector

    Returns
    -------
    pandas.DataFrame or numpy.array
        Symmetric input output table (flows) Z
        The type is determined by the type of A.
        If DataFrame index/columns as A

    """
    if (type(x) is pd.DataFrame) or (type(x) is pd.Series):
        x = x.values
    x = x.reshape((1, -1))  # use numpy broadcasting - much faster
    # (but has to ensure that x is a row vector)
    # old mathematical form:
    # return A.dot(np.diagflat(x))
    if type(A) is pd.DataFrame:
        return pd.DataFrame(A.values * x, index=A.index, columns=A.columns)
    else:
        return A * x


def calc_A(Z, x):
    """Calculate the A matrix (coefficients) from Z and x

    A is a normalized version of the industrial flows Z

    Parameters
    ----------
    Z : pandas.DataFrame or numpy.array
        Symmetric input output table (flows)
    x : pandas.DataFrame or numpy.array
        Industry output column vector

    Returns
    -------
    pandas.DataFrame or numpy.array
        Symmetric input output table (coefficients) A
        The type is determined by the type of Z.
        If DataFrame index/columns as Z

    """
    if (type(x) is pd.DataFrame) or (type(x) is pd.Series):
        x = x.values
    if (type(x) is not np.ndarray) and (x == 0):
        recix = 0
    else:
        with warnings.catch_warnings():
            # catch the divide by zero warning
            # we deal wit that by setting to 0 afterwards
            warnings.simplefilter("ignore")
            recix = 1 / x
        recix[recix == np.inf] = 0
        recix = recix.reshape((1, -1))
    # use numpy broadcasting - factor ten faster
    # Mathematical form - slow
    # return Z.dot(np.diagflat(recix))
    if type(Z) is pd.DataFrame:
        return pd.DataFrame(Z.values * recix, index=Z.index, columns=Z.columns)
    else:
        return Z * recix


def calc_L(A):
    """Calculate the Leontief L from A

    L = inverse matrix of (I - A)

    Where I is an identity matrix of same shape as A

    Comes from:
        x = Ax + y  =>  (I-A)x = y
    Where:
        A: coefficient input () - output () table
        x: output vector
        y: final demand vector

    Hence, L allows to derive a required output vector x for a given demand y

    Parameters
    ----------
    A : pandas.DataFrame or numpy.array
        Symmetric input output table (coefficients)

    Returns
    -------
    pandas.DataFrame or numpy.array
        Leontief input output table L
        The type is determined by the type of A.
        If DataFrame index/columns as A

    """
    I = np.eye(A.shape[0])  # noqa
    if type(A) is pd.DataFrame:
        return pd.DataFrame(np.linalg.inv(I - A), index=A.index, columns=A.columns)
    else:
        return np.linalg.inv(I - A)


def calc_S(F, x):
    """Calculate extensions/factor inputs coefficients

    Parameters
    ----------
    F : pandas.DataFrame or numpy.array
        Total direct impacts
    x : pandas.DataFrame or numpy.array
        Industry output column vector

    Returns
    -------
    pandas.DataFrame or numpy.array
        Direct impact coefficients S
        The type is determined by the type of F.
        If DataFrame index/columns as F

    """
    return calc_A(F, x)


def calc_S_Y(F_Y, y):
    """Calculate extensions/factor inputs coefficients for the final demand

    Note
    ----
    F_Y will be restricted to the item available in y for the calculation. This
    allows to use a subset of Y (just some regions for example) to be used for
    the calculations. Only works when using pandas DataFrames/Series.


    Parameters
    ----------
    F_Y : pandas.DataFrame or numpy.array
         Final demand impacts
    y : pandas.DataFrame or numpy.array
        Final demand column vector (e.g. mrio.Y.sum())

    Returns
    -------
    pandas.DataFrame or numpy.array
        Direct impact coefficients of final demand S_Y
        The type is determined by the type of F.
        If DataFrame index/columns as F

    """
    if type(F_Y) is pd.DataFrame and type(y) is (pd.Series or pd.DataFrame):
        F_Y_calc = F_Y.loc[:, y.index]
    else:
        F_Y_calc = F_Y
    return calc_A(F_Y_calc, y)


def calc_F(S, x):
    """Calculate total direct impacts from the impact coefficients

    Parameters
    ----------
    S : pandas.DataFrame or numpy.array
        Direct impact coefficients S
    x : pandas.DataFrame or numpy.array
        Industry output column vector

    Returns
    -------
    pandas.DataFrame or numpy.array
        Total direct impacts F
        The type is determined by the type of S.
        If DataFrame index/columns as S

    """
    return calc_Z(S, x)


def calc_F_Y(S_Y, y):
    """Calc. total direct impacts from the impact coefficients of final demand

    Note
    ----
    S_Y will be restricted to the item available in y for the calculation. This
    allows to use a subset of Y (just some regions for example) to be used for
    the calculations. Only works when using pandas DataFrames/Series.

    Parameters
    ----------
    S_Y : pandas.DataFrame or numpy.array
        Direct impact coefficients of final demand
    y : pandas.DataFrame or numpy.array
        Final demand column vector (e.g. mrio.Y.sum())

    Returns
    -------
    pandas.DataFrame or numpy.array
        Total direct impacts of final demand F_Y
        The type is determined by the type of S_Y.
        If DataFrame index/columns as S_Y

    """
    if type(S_Y) is pd.DataFrame and type(y) is (pd.Series or pd.DataFrame):
        S_Y_calc = S_Y.loc[:, y.index]
    else:
        S_Y_calc = S_Y

    return calc_Z(S_Y_calc, y)


def calc_M(S, L):
    """Calculate multipliers of the extensions

    Parameters
    ----------
    L : pandas.DataFrame or numpy.array
        Leontief input output table L
    S : pandas.DataFrame or numpy.array
        Direct impact coefficients

    Returns
    -------
    pandas.DataFrame or numpy.array
        Multipliers M
        The type is determined by the type of D.
        If DataFrame index/columns as D

    """
    return S.dot(L)


def calc_e(M, Y):
    """Calculate total impacts (footprints of consumption Y)

    Parameters
    ----------
    M : pandas.DataFrame or numpy.array
        Multipliers
    Y : pandas.DataFrame or numpy.array
        Final consumption

    TODO - this must be completely redone (D, check for dataframe, ...)

    Returns
    -------
    pandas.DataFrame or numpy.array
        Multipliers m
        The type is determined by the type of M.
        If DataFrame index/columns as M
    The calcubased on multipliers M and finald demand Y"""

    return M.dot(Y)


def recalc_M(S, D_cba, Y):
    """Calculate Multipliers based on footprints.

    Parameters
    ----------
    D_cba : pandas.DataFrame or numpy array
        Footprint per sector and country
    Y : pandas.DataFrame or numpy array
        Final demand: aggregated across categories or just one category, one
        column per country. This will be diagonalized per country block.
        The diagonolized form must be invertable for this method to work.

    Returns
    -------

    pandas.DataFrame or numpy.array
        Multipliers M
        The type is determined by the type of D_cba.
        If DataFrame index/columns as D_cba


    """

    Y_diag = ioutil.diagonalize_columns_to_sectors(Y)
    Y_inv = np.linalg.inv(Y_diag)
    M = D_cba.dot(Y_inv)
    if type(D_cba) is pd.DataFrame:
        M.columns = D_cba.columns
        M.index = D_cba.index

    return M


def calc_accounts(S, L, Y):
    """Calculate sector specific cba and pba based accounts, imp and exp accounts

    The total industry output x for the calculation
    is recalculated from L and y

    Parameters
    ----------
    L : pandas.DataFrame
        Leontief input output table L
    S : pandas.DataFrame
        Direct impact coefficients
    Y : pandas.DataFrame
        Final demand: aggregated across categories or just one category, one
        column per country. Shape: rows as L, Y with just region names

    Returns
    -------
    Tuple
        (D_cba, D_pba, D_imp, D_exp)

        Format: D_row x L_col (=nr_countries*nr_sectors)

        - D_cba        Footprint per sector and country
        - D_pba      Total factur use per sector and country
        - D_imp       Total global factor use to satisfy total final demand in
                      the country per sector
        - D_exp       Total factor use in one country to satisfy final demand
                      in all other countries (per sector)
    """
    # diagonalize each sector block per country
    # this results in a disaggregated y with final demand per country per
    # sector in one column

    if isinstance(Y.columns, pd.MultiIndex):
        raise ValueError(
            "Column index of Y can not be a MultiIndex - aggregate the columns"
        )
    Y_diag = ioutil.diagonalize_columns_to_sectors(Y)
    x_diag = L @ Y_diag

    x_tot = x_diag.values.sum(1)

    del Y_diag

    D_cba = pd.DataFrame(S @ x_diag)

    # D_pba = S.dot(np.diagflat(x_tot))
    # faster broadcasted calculation:
    # NB: D_pba columns might be different to D_cba columns if Y include "regions" which are not in the core. This happens for example for statistical discrepancy in the OECD tables. It is "theoretically" possible to calculate footprints for these "regions", but not PBA accounts.
    D_pba = pd.DataFrame(
        S.values * x_tot.reshape((1, -1)), index=S.index, columns=S.columns
    )

    # for the traded accounts set the domestic industry output to zero
    x_trade = ioutil.set_dom_block(x_diag, value=0)
    D_imp = pd.DataFrame(S @ x_trade)

    x_exp = x_trade.sum(1).values

    # D_exp = S.dot(np.diagflat(x_exp))
    # faster broadcasted version:
    D_exp = pd.DataFrame(
        S.values * x_exp.reshape((1, -1)), index=S.index, columns=S.columns
    )

    return (D_cba, D_pba, D_imp, D_exp)


def calc_gross_trade(
    Z: pd.DataFrame, Y: pd.DataFrame
) -> typing.NamedTuple(
    "gross_trade", [("bilat_flows", pd.DataFrame), ("totals", pd.DataFrame)]
):
    """Calculate the gross bilateral trade flows and totals

    These are the entries of Z and Y with the domestic blocks set to 0.

    Notes
    ----------
    This only works for DataFrame representation of Z and Y following the
    standard pymrio structure (regions on Multiindex level 0 or named 'region',
    sectors/categories on Multiindex level 1 or named 'sector').

    Parameters
    ----------
    Z : pandas.DataFrame
        Symmetric input output table (flows)
    Y : pandas.DataFrame
        final demand with regions (multiindex level 1) and categories (level 2)

    Returns
    -------
    namedtuple (with two DataFrames)
        A NamedTuple with two fields:

            - bilat_flows: df with rows: exporting country and sector,
              columns: importing countries
            - totals: df with gross total imports and exports per sector
              and region


    """

    Z_trade_blocks = ioutil.set_dom_block(Z, value=0)
    Y_trade_blocks = ioutil.set_dom_block(Y, value=0)

    level_spec_Z = "region" if "region" in Z.columns.names else 0
    level_spec_Y = "region" if "region" in Y.columns.names else 0
    Z_trade_agg = Z_trade_blocks.groupby(axis=1, level=level_spec_Z, sort=False).agg(
        sum
    )
    Y_trade_agg = Y_trade_blocks.groupby(axis=1, level=level_spec_Y, sort=False).agg(
        sum
    )

    x_bilat = Z_trade_agg + Y_trade_agg

    level_spec_x = "sector" if "sector" in x_bilat.index.names else 1
    gross_imports = pd.DataFrame(
        x_bilat.groupby(axis=0, level=level_spec_x, sort=False)
        .agg(sum)
        .stack()
        .swaplevel(),
        columns=["imports"],
    )
    gross_exports = pd.DataFrame(x_bilat.sum(axis=1), columns=["exports"])

    # gross_exports first as the swaplevel in gross_imports rearanges sectors!
    gross_totals = gross_exports.join(gross_imports)

    return namedtuple("gross_trade", "bilat_flows totals")(x_bilat, gross_totals)
