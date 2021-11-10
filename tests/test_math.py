""" test cases for all mathematical functions """

import os
import sys

import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt
import pytest

TESTPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(TESTPATH, ".."))


# the function which should be tested here
from pymrio.tools.iomath import calc_A  # noqa
from pymrio.tools.iomath import calc_accounts  # noqa
from pymrio.tools.iomath import calc_e  # noqa
from pymrio.tools.iomath import calc_F  # noqa
from pymrio.tools.iomath import calc_F_Y  # noqa
from pymrio.tools.iomath import calc_gross_trade  # noqa
from pymrio.tools.iomath import calc_L  # noqa
from pymrio.tools.iomath import calc_M  # noqa
from pymrio.tools.iomath import calc_S  # noqa
from pymrio.tools.iomath import calc_S_Y  # noqa
from pymrio.tools.iomath import calc_x  # noqa
from pymrio.tools.iomath import calc_x_from_L  # noqa
from pymrio.tools.iomath import calc_Z  # noqa


# test data
@pytest.fixture()
def td_IO_Data_Miller():
    """This data is from the chapter 2 of
    Input-output analysis: foundations and extensions -- Miller, Ronald E
    and Blair, Peter D -- 2009 (ISBN: 9780521517133)
    """

    class IO_Data_Miller:
        # Table 2.3 of the Book
        Z_arr = np.array([[150, 500], [200, 100]]).astype("float")
        Z_df = pd.DataFrame(
            data=Z_arr,
            index=["sec1", "sec2"],
            columns=["sec1", "sec2"],
        )

        # Table 2.4 of the Book
        A_arr = np.array([[0.15, 0.25], [0.20, 0.05]]).astype("float")
        A_df = pd.DataFrame(
            data=A_arr,
            index=["sec1", "sec2"],
            columns=["sec1", "sec2"],
        )

        # Table 2.3 of the Book
        fd_arr = np.array([[350], [1700]]).astype("float")
        fd_df = pd.DataFrame(
            data=fd_arr,
            index=["sec1", "sec2"],
            columns=["fi"],
        )

        # Table 2.3 of the Book
        x_arr = np.array([[1000], [2000]]).astype("float")
        x_df = pd.DataFrame(
            data=x_arr,
            index=["sec1", "sec2"],
            columns=["indout"],
        )

        # At the example following Table 2.3, additional
        # decimals where calculated
        L_arr = np.array([[1.25412541, 0.330033], [0.2640264, 1.12211221]]).astype(
            "float"
        )
        L_df = pd.DataFrame(
            data=L_arr,
            index=["sec1", "sec2"],
            columns=["sec1", "sec2"],
        )

        # Example epsilon from chapter 2, it uses the new x
        xnew_arr = np.array([[1247.5], [1841.6]]).astype("float")
        xnew_df = pd.DataFrame(
            data=xnew_arr,
            index=["sec1", "sec2"],
            columns=["indout"],
        )

        labcoeff_arr = np.array(
            [
                [0.3, 0.25],
            ]
        )
        labcoeff_df = pd.DataFrame(
            data=labcoeff_arr,
            index=["total labor"],
            columns=["sec1", "sec2"],
        )

        labtot_arr = np.array(
            [
                [374.25, 460.4],
            ]
        )  # .25 because of rounding
        labtot_df = pd.DataFrame(
            data=labtot_arr,
            index=["total labor"],
            columns=["sec1", "sec2"],
        )

    return IO_Data_Miller


@pytest.fixture()
def td_small_MRIO():
    """A small MRIO with three sectors and two regions.
    The testdata here just consists of pandas DataFrames, the functionality
    with numpy arrays gets tested with td_IO_Data_Miller.
    """

    class IO_Data:

        _sectors = ["sector1", "sector2", "sector3"]
        _regions = ["reg1", "reg2"]
        _Z_multiindex = pd.MultiIndex.from_product(
            [_regions, _sectors], names=[u"region", u"sector"]
        )

        Z = pd.DataFrame(
            data=[
                [10, 5, 1, 6, 5, 7],
                [0, 2, 0, 0, 5, 3],
                [10, 3, 20, 4, 2, 0],
                [5, 0, 0, 1, 10, 9],
                [0, 10, 1, 0, 20, 1],
                [5, 0, 0, 1, 10, 10],
            ],
            index=_Z_multiindex,
            columns=_Z_multiindex,
            dtype=("float64"),
        )

        _categories = ["final demand"]
        _Y_multiindex = pd.MultiIndex.from_product(
            [_regions, _categories], names=[u"region", u"category"]
        )
        Y = pd.DataFrame(
            data=[[14, 3], [2.5, 2.5], [13, 6], [5, 20], [10, 10], [3, 10]],
            index=_Z_multiindex,
            columns=_Y_multiindex,
            dtype=("float64"),
        )

        F = pd.DataFrame(
            data=[[20, 1, 42, 4, 20, 5], [5, 4, 11, 8, 2, 10]],
            index=["ext_type_1", "ext_type_2"],
            columns=_Z_multiindex,
            dtype=("float64"),
        )

        F_Y = pd.DataFrame(
            data=[[50, 10], [100, 20]],
            index=["ext_type_1", "ext_type_2"],
            columns=_Y_multiindex,
            dtype=("float64"),
        )

        S_Y = pd.DataFrame(
            data=[
                [1.0526315789473684, 0.1941747572815534],
                [2.1052631578947367, 0.3883495145631068],
            ],
            index=["ext_type_1", "ext_type_2"],
            columns=_Y_multiindex,
            dtype=("float64"),
        )

        A = pd.DataFrame(
            data=[
                [
                    0.19607843137254902,
                    0.3333333333333333,
                    0.017241379310344827,
                    0.12,
                    0.09615384615384616,
                    0.1794871794871795,
                ],  # noqa
                [
                    0.0,
                    0.13333333333333333,
                    0.0,
                    0.0,
                    0.09615384615384616,
                    0.07692307692307693,
                ],  # noqa
                [
                    0.19607843137254902,
                    0.2,
                    0.3448275862068966,
                    0.08,
                    0.038461538461538464,
                    0.0,
                ],  # noqa
                [
                    0.09803921568627451,
                    0.0,
                    0.0,
                    0.02,
                    0.19230769230769232,
                    0.23076923076923075,
                ],  # noqa
                [
                    0.0,
                    0.6666666666666666,
                    0.017241379310344827,
                    0.0,
                    0.38461538461538464,
                    0.02564102564102564,
                ],  # noqa
                [
                    0.09803921568627451,
                    0.0,
                    0.0,
                    0.02,
                    0.19230769230769232,
                    0.2564102564102564,
                ],  # noqa
            ],
            index=_Z_multiindex,
            columns=_Z_multiindex,
        )

        L = pd.DataFrame(
            data=[
                [
                    1.3387146304736708,
                    0.9689762471208287,
                    0.05036622549592462,
                    0.17820960407435948,
                    0.5752019383714646,
                    0.4985179148178926,
                ],  # noqa
                [
                    0.02200779585580331,
                    1.3716472861392823,
                    0.0076800357678581885,
                    0.006557415453762468,
                    0.2698335633228079,
                    0.15854643902810828,
                ],  # noqa
                [
                    0.43290422861412026,
                    0.8627066565439678,
                    1.5492942759220427,
                    0.18491657196329184,
                    0.44027825642348534,
                    0.26630955082840885,
                ],  # noqa
                [
                    0.18799498787612925,
                    0.5244084722329316,
                    0.020254008037620782,
                    1.0542007368783255,
                    0.5816573175534603,
                    0.44685014763069275,
                ],  # noqa
                [
                    0.04400982046095892,
                    1.5325472495862535,
                    0.05259311578831879,
                    0.014602513642445088,
                    1.9545285794951548,
                    0.2410917825607805,
                ],  # noqa
                [
                    0.19294222439918532,
                    0.5382086951864299,
                    0.020787008249137116,
                    0.05562707205933412,
                    0.596964089068025,
                    1.4849251515157111,
                ],  # noqa
            ],
            index=_Z_multiindex,
            columns=_Z_multiindex,
        )

        x = pd.DataFrame(
            data=[
                [51],
                [15],
                [58],
                [50],
                [52],
                [39],
            ],
            columns=["indout"],
            index=_Z_multiindex,
            dtype=("float64"),
        )
        S = pd.DataFrame(
            data=[
                [
                    0.39215686274509803,
                    0.06666666666666667,
                    0.7241379310344828,
                    0.08,
                    0.38461538461538464,
                    0.1282051282051282,
                ],  # noqa
                [
                    0.09803921568627451,
                    0.26666666666666666,
                    0.1896551724137931,
                    0.16,
                    0.038461538461538464,
                    0.2564102564102564,
                ],  # noqa
            ],
            index=["ext_type_1", "ext_type_2"],
            columns=_Z_multiindex,
        )

        M = pd.DataFrame(
            data=[
                [
                    0.896638324101429,
                    1.7965474933011258,
                    1.1666796580507097,
                    0.3013124703668342,
                    1.4371886818255364,
                    0.7177624711634629,
                ],  # noqa
                [
                    0.3004620527704837,
                    0.9052387706892087,
                    0.311411003349379,
                    0.23778766312079253,
                    0.5331560745059157,
                    0.6031791628984159,
                ],  # noqa
            ],
            index=["ext_type_1", "ext_type_2"],
            columns=_Z_multiindex,
        )

        D_cba = pd.DataFrame(
            data=[
                [
                    14.059498889254174,
                    18.863255551508175,
                    17.32012296814962,
                    8.71616437964097,
                    18.863255551508175,
                    14.17770265993889,
                ],  # noqa
                [
                    5.395407054390734,
                    7.594657671782178,
                    5.857880532237175,
                    5.657139420727301,
                    7.594657671782178,
                    7.900257649080434,
                ],  # noqa
            ],
            index=["ext_type_1", "ext_type_2"],
            columns=_Z_multiindex,
        )

        D_pba = pd.DataFrame(
            data=[
                [20.000000000000004, 1.0, 42.00000000000001, 4.0, 20.0, 5.0],  # noqa
                [5.000000000000001, 4.0, 11.0, 8.0, 1.9999999999999998, 10.0],  # noqa
            ],
            index=["ext_type_1", "ext_type_2"],
            columns=_Z_multiindex,
        )

        D_imp = pd.DataFrame(
            data=[
                [
                    1.2792573306446737,
                    10.499069649181388,
                    1.2752266807875912,
                    6.604374747509535,
                    8.364185902326788,
                    10.842115601865368,
                ],  # noqa
                [
                    2.054905005956757,
                    3.9151998960771452,
                    1.522271392125981,
                    1.743464577633809,
                    3.6794577757050337,
                    3.221508682410955,
                ],  # noqa
            ],
            index=["ext_type_1", "ext_type_2"],
            columns=_Z_multiindex,
        )

        D_exp = pd.DataFrame(
            data=[
                [
                    8.251832343364468,
                    0.5304113433404783,
                    17.02843256499675,
                    1.3307504334524414,
                    9.797226856351275,
                    1.9255763708099365,
                ],  # noqa
                [
                    2.062958085841117,
                    2.1216453733619134,
                    4.459827576546767,
                    2.6615008669048827,
                    0.9797226856351275,
                    3.851152741619873,
                ],  # noqa
            ],
            index=["ext_type_1", "ext_type_2"],
            columns=_Z_multiindex,
        )

    return IO_Data


def test_calc_x_df(td_IO_Data_Miller):
    pdt.assert_frame_equal(
        td_IO_Data_Miller.x_df, calc_x(td_IO_Data_Miller.Z_df, td_IO_Data_Miller.fd_df)
    )


def test_calc_x_arr(td_IO_Data_Miller):
    npt.assert_array_equal(
        td_IO_Data_Miller.x_arr,
        calc_x(td_IO_Data_Miller.Z_arr, td_IO_Data_Miller.fd_arr),
    )


def test_calc_Z_df(td_IO_Data_Miller):
    pdt.assert_frame_equal(
        td_IO_Data_Miller.Z_df, calc_Z(td_IO_Data_Miller.A_df, td_IO_Data_Miller.x_df)
    )


def test_calc_Z_arr(td_IO_Data_Miller):
    npt.assert_array_equal(
        td_IO_Data_Miller.Z_arr,
        calc_Z(td_IO_Data_Miller.A_arr, td_IO_Data_Miller.x_arr),
    )


def test_calc_A_df(td_IO_Data_Miller):
    pdt.assert_frame_equal(
        td_IO_Data_Miller.A_df, calc_A(td_IO_Data_Miller.Z_df, td_IO_Data_Miller.x_df)
    )


def test_calc_A_arr(td_IO_Data_Miller):
    npt.assert_array_equal(
        td_IO_Data_Miller.A_arr,
        calc_A(td_IO_Data_Miller.Z_arr, td_IO_Data_Miller.x_arr),
    )


def test_calc_L_df(td_IO_Data_Miller):
    pdt.assert_frame_equal(td_IO_Data_Miller.L_df, calc_L(td_IO_Data_Miller.A_df))


def test_calc_L_arr(td_IO_Data_Miller):
    npt.assert_allclose(
        td_IO_Data_Miller.L_arr, calc_L(td_IO_Data_Miller.A_arr), rtol=1e-5
    )


def test_calc_x_from_L_df(td_IO_Data_Miller):
    pdt.assert_frame_equal(
        td_IO_Data_Miller.x_df,
        calc_x_from_L(td_IO_Data_Miller.L_df, td_IO_Data_Miller.fd_df),
    )


def test_calc_x_from_L_arr(td_IO_Data_Miller):
    npt.assert_allclose(
        td_IO_Data_Miller.x_arr,
        calc_x_from_L(td_IO_Data_Miller.L_arr, td_IO_Data_Miller.fd_arr),
        rtol=1e-5,
    )


def test_calc_F_arr(td_IO_Data_Miller):
    npt.assert_allclose(
        td_IO_Data_Miller.labtot_arr,
        calc_F(td_IO_Data_Miller.labcoeff_arr, td_IO_Data_Miller.xnew_arr),
        rtol=1e-5,
    )


def test_calc_F_df(td_IO_Data_Miller):
    pdt.assert_frame_equal(
        td_IO_Data_Miller.labtot_df,
        calc_F(td_IO_Data_Miller.labcoeff_df, td_IO_Data_Miller.xnew_df),
    )


def test_calc_S_arr(td_IO_Data_Miller):
    npt.assert_allclose(
        td_IO_Data_Miller.labcoeff_arr,
        calc_S(td_IO_Data_Miller.labtot_arr, td_IO_Data_Miller.xnew_arr),
        rtol=1e-5,
    )


def test_calc_S_df(td_IO_Data_Miller):
    pdt.assert_frame_equal(
        td_IO_Data_Miller.labcoeff_df,
        calc_S(td_IO_Data_Miller.labtot_df, td_IO_Data_Miller.xnew_df),
    )


def test_calc_x_MRIO(td_small_MRIO):
    pdt.assert_frame_equal(td_small_MRIO.x, calc_x(td_small_MRIO.Z, td_small_MRIO.Y))


def test_calc_A_MRIO(td_small_MRIO):
    pdt.assert_frame_equal(td_small_MRIO.A, calc_A(td_small_MRIO.Z, td_small_MRIO.x))
    # we also test the different methods to provide x:
    x_values = td_small_MRIO.x.values
    x_Tvalues = td_small_MRIO.x.T.values
    x_series = pd.Series(td_small_MRIO.x.iloc[:, 0])
    pdt.assert_frame_equal(td_small_MRIO.A, calc_A(td_small_MRIO.Z, x_series))
    pdt.assert_frame_equal(td_small_MRIO.A, calc_A(td_small_MRIO.Z, x_values))
    pdt.assert_frame_equal(td_small_MRIO.A, calc_A(td_small_MRIO.Z, x_Tvalues))


def test_calc_Z_MRIO(td_small_MRIO):
    pdt.assert_frame_equal(td_small_MRIO.Z, calc_Z(td_small_MRIO.A, td_small_MRIO.x))
    # we also test the different methods to provide x:
    x_values = td_small_MRIO.x.values
    x_Tvalues = td_small_MRIO.x.T.values
    x_series = pd.Series(td_small_MRIO.x.iloc[:, 0])
    pdt.assert_frame_equal(td_small_MRIO.Z, calc_Z(td_small_MRIO.A, x_series))
    pdt.assert_frame_equal(td_small_MRIO.Z, calc_Z(td_small_MRIO.A, x_values))
    pdt.assert_frame_equal(td_small_MRIO.Z, calc_Z(td_small_MRIO.A, x_Tvalues))


def test_calc_L_MRIO(td_small_MRIO):
    pdt.assert_frame_equal(td_small_MRIO.L, calc_L(td_small_MRIO.A))


def test_calc_S_MRIO(td_small_MRIO):
    pdt.assert_frame_equal(td_small_MRIO.S, calc_S(td_small_MRIO.F, td_small_MRIO.x))


def test_calc_S_Y_MRIO(td_small_MRIO):
    pdt.assert_frame_equal(
        td_small_MRIO.S_Y, calc_S_Y(td_small_MRIO.F_Y, td_small_MRIO.Y.sum(axis=0))
    )


def test_calc_F_Y_MRIO(td_small_MRIO):
    S_Y = calc_S_Y(td_small_MRIO.F_Y, td_small_MRIO.Y.sum(axis=0))
    pdt.assert_frame_equal(
        td_small_MRIO.F_Y, calc_F_Y(S_Y, td_small_MRIO.Y.sum(axis=0))
    )


def test_calc_M_MRIO(td_small_MRIO):
    pdt.assert_frame_equal(td_small_MRIO.M, calc_M(td_small_MRIO.S, td_small_MRIO.L))


def test_calc_gross_trade_MRIO(td_small_MRIO):
    gt = calc_gross_trade(td_small_MRIO.Z, td_small_MRIO.Y)

    reg1sec2trade = (
        td_small_MRIO.Z.loc[("reg1", "sector2"), "reg2"].sum()
        + td_small_MRIO.Y.loc[("reg1", "sector2"), "reg2"].sum()
    )

    total_exports_reg1 = td_small_MRIO.Z.loc["reg1", "reg2"].sum(
        axis=1
    ) + td_small_MRIO.Y.loc["reg1", "reg2"].sum(axis=1)

    assert gt.bilat_flows.loc[("reg1", "sector2"), "reg2"] == reg1sec2trade
    pdt.assert_series_equal(
        gt.totals.loc["reg1", "exports"],
        total_exports_reg1,
        check_names=False,
    )


def test_calc_accounts_MRIO(td_small_MRIO):
    # calc the accounts
    nD_cba, nD_pba, nD_imp, nD_exp = calc_accounts(
        td_small_MRIO.S,
        td_small_MRIO.L,
        td_small_MRIO.Y.groupby(level="region", axis=1, sort=False).sum(),
    )
    # test all

    pdt.assert_frame_equal(
        td_small_MRIO.D_cba,
        nD_cba,
    )
    pdt.assert_frame_equal(
        td_small_MRIO.D_pba,
        nD_pba,
    )
    pdt.assert_frame_equal(
        td_small_MRIO.D_imp,
        nD_imp,
    )
    pdt.assert_frame_equal(
        td_small_MRIO.D_exp,
        nD_exp,
    )
    # test if fp = terr + imp - exp on the total level
    # that tests if imp == exp and fp == terr
    pdt.assert_series_equal(
        nD_cba.sum(axis=1),
        nD_pba.sum(axis=1) + nD_imp.sum(axis=1) - nD_exp.sum(axis=1),
    )
