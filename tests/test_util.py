""" test cases for all util functions """

import os
import sys
from collections import namedtuple
from unittest.mock import mock_open, patch

import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt
import pytest

TESTPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(TESTPATH, ".."))

from pymrio.tools.ioutil import build_agg_matrix  # noqa
from pymrio.tools.ioutil import build_agg_vec  # noqa
from pymrio.tools.ioutil import diagonalize_blocks  # noqa
from pymrio.tools.ioutil import find_first_number  # noqa
from pymrio.tools.ioutil import set_block  # noqa
from pymrio.tools.ioutil import sniff_csv_format  # noqa
from pymrio.tools.ioutil import diagonalize_columns_to_sectors


@pytest.fixture()
def csv_test_files_content():
    test_para = namedtuple("test_para", ["text", "sep", "header_rows", "index_col"])

    class example_csv_content:
        test_contents = [
            test_para(
                text=(
                    """idx1,idx2,col1,col2
                               a,b,1,2
                               c,d,2,4\n"""
                ),
                sep=",",
                header_rows=1,
                index_col=2,
            ),
            test_para(
                text=(
                    """idx1,col1,col2
                               a,1,2
                               c,2,4\n"""
                ),
                sep=",",
                header_rows=1,
                index_col=1,
            ),
            test_para(
                text=(
                    """idx1;col1;col2
                               a;1;2
                               c;2;4\n"""
                ),
                sep=";",
                header_rows=1,
                index_col=1,
            ),
            test_para(
                text=(
                    """;col1;col2
                               ;l;d
                               a;1;2
                               c;2;4\n"""
                ),
                sep=";",
                header_rows=2,
                index_col=1,
            ),
            test_para(
                text=(
                    """|col1|col2
                               |l|d
                               a|f|g
                               c|e|l\n"""
                ),
                sep="|",
                header_rows=None,
                index_col=None,
            ),
            test_para(
                text=(
                    """;col1;col2
                               ;l;d
                               a;f;3
                               c;e;l\n"""
                ),
                sep=";",
                header_rows=None,
                index_col=None,
            ),
            test_para(
                text=(
                    """;col1;col2
                               ;l;d
                               a;f;l
                               c;e;3\n"""
                ),
                sep=";",
                header_rows=3,
                index_col=2,
            ),
        ]

    return example_csv_content


def test_find_first_number():
    """Some tests for finding the first number in a sequence"""
    assert find_first_number([0, 1, 2, 3]) == 0
    assert find_first_number(["a", 1, 2, 3]) == 1
    assert find_first_number(["a", 1, "c", 3]) == 1
    assert find_first_number([None, 1, "c", 3]) == 1
    assert find_first_number(["a", "b"]) == None  # noqa
    assert find_first_number([]) == None  # noqa


def test_dev_read(csv_test_files_content):
    """Tests the csv sniffer"""
    for tests in csv_test_files_content.test_contents:
        with patch(
            "builtins.open", mock_open(read_data=tests.text), create=False
        ) as mo:  # noqa
            res = sniff_csv_format("foo")
        assert res["sep"] == tests.sep
        assert res["nr_index_col"] == tests.index_col
        assert res["nr_header_row"] == tests.header_rows


def test_build_agg_matrix():
    """Tests building the aggreagation matrix"""

    am_num = build_agg_matrix([1, 0, 0, 1, 0])
    expected = np.array([[0.0, 1.0, 1.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0, 0.0]])
    am_str = build_agg_matrix(
        ["r2", "r1", "r1", "r2", "r1"], pos_dict={"r1": 0, "r2": 1}
    )

    np.testing.assert_allclose(am_num, expected)
    np.testing.assert_allclose(am_str, expected)


def test_build_agg_vec():
    """Simple test based on the test mrio"""
    vec = build_agg_vec(["OECD", "EU"], path="test", miss="RoW")
    expected = ["OECD", "EU", "OECD", "OECD", "RoW", "RoW"]
    assert vec == expected


def test_diagonalize_blocks():
    """Tests the numpy implementation of diagonalize_blocks"""

    # arr (df):  output (df): (blocks = [x, y, z])
    #     (all letters are index or header)
    #       A B     A A A B B B
    #               x y z x y z
    #     a 3 1     3 0 0 1 0 0
    #     b 4 2     0 4 0 0 2 0
    #     c 5 3     0 0 5 0 0 3
    #     d 6 9     6 0 0 9 0 0
    #     e 7 6     0 7 0 0 6 0
    #     f 8 4     0 0 8 0 0 4

    inp_array = np.array(([3, 1], [4, 2], [5, 3], [6, 9], [7, 6], [8, 4]))
    out_array = np.array(
        (
            [3.0, 0.0, 0.0, 1.0, 0.0, 0.0],
            [0.0, 4.0, 0.0, 0.0, 2.0, 0.0],
            [0.0, 0.0, 5.0, 0.0, 0.0, 3.0],
            [6.0, 0.0, 0.0, 9.0, 0.0, 0.0],
            [0.0, 7.0, 0.0, 0.0, 6.0, 0.0],
            [0.0, 0.0, 8.0, 0.0, 0.0, 4.0],
        )
    )
    diag_array = diagonalize_blocks(arr=inp_array, blocksize=3)
    np.testing.assert_allclose(diag_array, out_array)


def test_diagonalize_columns_to_sectors():
    inp_array = np.array(([3, 1], [4, 2], [5, 3], [6, 9], [7, 6], [8, 4]))
    out_array = np.array(
        (
            [3.0, 0.0, 0.0, 1.0, 0.0, 0.0],
            [0.0, 4.0, 0.0, 0.0, 2.0, 0.0],
            [0.0, 0.0, 5.0, 0.0, 0.0, 3.0],
            [6.0, 0.0, 0.0, 9.0, 0.0, 0.0],
            [0.0, 7.0, 0.0, 0.0, 6.0, 0.0],
            [0.0, 0.0, 8.0, 0.0, 0.0, 4.0],
        )
    )

    regions = ["A", "B"]
    sectors = ["x", "y", "z"]
    reg_sec_index = pd.MultiIndex.from_product(
        [regions, sectors], names=["region", "sector"]
    )

    inp_df = pd.DataFrame(data=inp_array, index=reg_sec_index, columns=regions)
    inp_df.columns.names = ["region"]

    out_df = pd.DataFrame(data=out_array, index=inp_df.index, columns=reg_sec_index)

    diag_df = diagonalize_columns_to_sectors(inp_df)
    pdt.assert_frame_equal(diag_df, out_df)


def test_set_block():
    """Set block util function"""
    full_arr = np.random.random((10, 10))
    block_arr = np.zeros((2, 2))

    mod_arr = set_block(full_arr, block_arr)
    npt.assert_array_equal(mod_arr[0:2, 0:2], block_arr)
    npt.assert_array_equal(mod_arr[2:4, 2:4], block_arr)
    npt.assert_array_equal(mod_arr[0:2, 3:-1], full_arr[0:2, 3:-1])

    with pytest.raises(ValueError):
        block_arr = np.zeros((3, 3))
        mod_arr = set_block(full_arr, block_arr)

    with pytest.raises(ValueError):
        full_arr = np.random.random((10, 12))
        block_arr = np.zeros((2, 2))
        mod_arr = set_block(full_arr, block_arr)
