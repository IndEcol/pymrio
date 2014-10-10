""" test cases for all mathematical functions """

import sys, os
import numpy as np
import pandas as pd
import numpy.testing as npt
import pandas.util.testing as pdt

_pymriopath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _pymriopath + '/../../')


# the function which should be tested here
from pymrio.tools.iomath import calc_x
from pymrio.tools.iomath import calc_x_from_L
from pymrio.tools.iomath import calc_Z
from pymrio.tools.iomath import calc_A
from pymrio.tools.iomath import calc_L
from pymrio.tools.iomath import calc_S
from pymrio.tools.iomath import calc_F
from pymrio.tools.iomath import calc_M
from pymrio.tools.iomath import calc_e
from pymrio.tools.iomath import calc_accounts


# test data
class IO_Data_Miller():
    """ This data is from the chapter 2 of 
    Input-output analysis: foundations and extensions -- Miller, Ronald E and Blair, Peter D -- 2009 (ISBN: 9780521517133)
    """

    # Table 2.3 of the Book
    Z_arr = np.array([
        [150, 500],
        [200, 100]
        ]).astype('float')
    Z_df = pd.DataFrame(
            data = Z_arr,
            index = ['sec1','sec2'],
            columns = ['sec1','sec2'],
            )

    # Table 2.4 of the Book
    A_arr = np.array([
        [0.15, 0.25],
        [0.20, 0.05]
        ]).astype('float')
    A_df = pd.DataFrame(
            data = A_arr,
            index = ['sec1','sec2'],
            columns = ['sec1','sec2'],
            )

    # Table 2.3 of the Book
    fd_arr = np.array([
        [350],
        [1700]
        ]).astype('float')
    fd_df = pd.DataFrame(
            data = fd_arr,
            index = ['sec1','sec2'],
            columns = ['fi'],
            )

    # Table 2.3 of the Book
    x_arr = np.array([
        [1000],
        [2000]
        ]).astype('float')
    x_df = pd.DataFrame(
            data = x_arr,
            index = ['sec1','sec2'],
            columns = ['indout'],
            )

    # At the example following Table 2.3, additional decimals where calculated
    L_arr = np.array([
        [1.25412541, 0.330033],
        [0.2640264, 1.12211221]
        ]).astype('float')
    L_df = pd.DataFrame(
            data = L_arr,
            index = ['sec1','sec2'],
            columns = ['sec1','sec2'],
            )

    # Example epsilon from chapter 2, it uses the new x 
    xnew_arr = np.array([
        [1247.5],
        [1841.6]
        ]).astype('float')
    xnew_df = pd.DataFrame(
            data = xnew_arr,
            index = ['sec1','sec2'],
            columns = ['indout'],
            )


    labcoeff_arr = np.array([
        [0.3, 0.25],
        ]) 
    labcoeff_df = pd.DataFrame(
            data = labcoeff_arr,
            index = ['total labor'],
            columns = ['sec1','sec2'],
            )

    labtot_arr = np.array([
        [374.25, 460.4],   # .25 because of rounding
        ]) 
    labtot_df = pd.DataFrame(
            data = labtot_arr,
            index = ['total labor'],
            columns = ['sec1','sec2'],
            )


def test_calc_x_df():
    pdt.assert_frame_equal(
            IO_Data_Miller.x_df,
            calc_x(IO_Data_Miller.Z_df, IO_Data_Miller.fd_df)
            )
def test_calc_x_arr():
    npt.assert_array_equal(
            IO_Data_Miller.x_arr,
            calc_x(IO_Data_Miller.Z_arr, IO_Data_Miller.fd_arr)
            )

def test_calc_Z_df():
    pdt.assert_frame_equal(
            IO_Data_Miller.Z_df,
            calc_Z(IO_Data_Miller.A_df, IO_Data_Miller.x_df)
            )
def test_calc_Z_arr():
    npt.assert_array_equal(
            IO_Data_Miller.Z_arr,
            calc_Z(IO_Data_Miller.A_arr, IO_Data_Miller.x_arr)
            )

def test_calc_A_df():
    pdt.assert_frame_equal(
            IO_Data_Miller.A_df,
            calc_A(IO_Data_Miller.Z_df, IO_Data_Miller.x_df)
            )
def test_calc_A_arr():
    npt.assert_array_equal(
            IO_Data_Miller.A_arr,
            calc_A(IO_Data_Miller.Z_arr, IO_Data_Miller.x_arr)
            )

def test_calc_L_df():
    pdt.assert_frame_equal(
            IO_Data_Miller.L_df,
            calc_L(IO_Data_Miller.A_df)
            )

def test_calc_L_arr():
    npt.assert_allclose(
            IO_Data_Miller.L_arr,
            calc_L(IO_Data_Miller.A_arr),
            rtol = 1e-5
            )

def test_calc_x_from_L_df():
    pdt.assert_frame_equal(
            IO_Data_Miller.x_df,
            calc_x_from_L(IO_Data_Miller.L_df, IO_Data_Miller.fd_df),
            )

def test_calc_x_from_L_arr():
    npt.assert_allclose(
            IO_Data_Miller.x_arr,
            calc_x_from_L(IO_Data_Miller.L_arr, IO_Data_Miller.fd_arr),
            rtol = 1e-5
            )

def test_calc_F_arr():
    npt.assert_allclose(
            IO_Data_Miller.labtot_arr,
            calc_F(IO_Data_Miller.labcoeff_arr, IO_Data_Miller.xnew_arr),
            rtol = 1e-5
            )
def test_calc_F_df():
    pdt.assert_frame_equal(
            IO_Data_Miller.labtot_df,
            calc_F(IO_Data_Miller.labcoeff_df, IO_Data_Miller.xnew_df),
            )

def test_calc_S_arr():
    npt.assert_allclose(
            IO_Data_Miller.labcoeff_arr,
            calc_S(IO_Data_Miller.labtot_arr, IO_Data_Miller.xnew_arr),
            rtol = 1e-5
            )
def test_calc_S_df():
    pdt.assert_frame_equal(
            IO_Data_Miller.labcoeff_df,
            calc_S(IO_Data_Miller.labtot_df, IO_Data_Miller.xnew_df),
            )


