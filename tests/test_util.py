""" test cases for all util functions """

import os
import string
import sys
from collections import namedtuple
from unittest.mock import mock_open, patch

import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt
import pytest
from faker import Faker

TESTPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(TESTPATH, ".."))

from pymrio.tools.ioutil import (  # noqa
    build_agg_matrix,
    build_agg_vec,
    diagonalize_blocks,
    find_first_number,
    set_block,
    sniff_csv_format,
    diagonalize_columns_to_sectors,  # noqa
    filename_from_url,
    index_contains,
    index_fullmatch,
    index_match,
    match_and_convert,
)


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


def test_filename_from_url():
    letters = np.array(list(string.printable))
    fake = Faker()
    for _ in range(100):
        filename = fake.file_name()
        url = fake.url() + filename
        if np.random.rand() > 0.5:
            url += np.random.choice(np.array(["?", "&"])) + "".join(
                np.random.choice(letters, size=np.random.randint(1))
            )

    assert filename_from_url(url) == filename

    test_urls = {
        "Democrat.odp": "https://www.arnold-mann.net/Democrat.odp?refvlmw",
        "heavy.numbers": "http://www.maldonado-mccullough.net/heavy.numbers&dbfgbds",
        "prove.js": "frazier.com/prove.js&vsdfvwevr",
        "conference.pdf": "http://www.dennis.com/conference.pdf&34gegrt4",
    }

    for filename in test_urls.keys():
        assert filename_from_url(test_urls[filename]) == filename


def test_util_regex():
    """Test regex matching"""

    test_index = pd.MultiIndex.from_product(
        [["a1", "b1", "c2", "b2"], ["aa", "bb", "cc", "dd"]],
        names=["region", "sector"],
    )

    test_df = pd.DataFrame(
        data=np.random.random((16, 2)), index=test_index, columns=["foo", "bar"]
    )

    # 1. Full functionality test with fullmatch

    df_match = index_fullmatch(test_df, region="a.*", sector=".*b.*")

    assert df_match.index.get_level_values("region").unique() == ["a1"]
    assert df_match.index.get_level_values("sector").unique() == ["bb"]

    df_match2 = index_fullmatch(
        test_df,
        region="a.*",
        sector=".*b.*",
        not_present_column="abc",
        another_column=".*",
    )
    assert df_match2.index.get_level_values("region").unique() == ["a1"]
    assert df_match2.index.get_level_values("sector").unique() == ["bb"]

    mdx_match = index_fullmatch(test_index, region=".*2", sector="cc")

    assert (
        len(mdx_match.get_level_values("region").unique().difference({"c2", "b2"})) == 0
    )

    test_ds = test_df.foo
    ds_match = index_fullmatch(test_ds, sector="aa")

    assert ds_match.index.get_level_values("sector").unique() == ["aa"]
    assert all(
        ds_match.index.get_level_values("region").unique() == ["a1", "b1", "c2", "b2"]
    )

    idx_match = index_fullmatch(test_index.get_level_values("region"), region=".*2")
    assert (
        len(idx_match.get_level_values("region").unique().difference({"c2", "b2"})) == 0
    )

    # test with empty dataframes
    test_empty = pd.DataFrame(index=test_index)
    df_match_empty = index_fullmatch(test_empty, region=".*b.*", sector=".*b.*")

    assert all(df_match_empty.index.get_level_values("region").unique() == ["b1", "b2"])
    assert df_match_empty.index.get_level_values("sector").unique() == ["bb"]

    # test with empty index
    empty_index = pd.MultiIndex.from_product([[], []], names=["region", "sector"])

    assert len(index_fullmatch(empty_index, region=".*", sector="cc")) == 0

    # 2. test the contains functionality

    df_match_contains = index_contains(test_df, region="1", sector="c")
    assert all(
        df_match_contains.index.get_level_values("region").unique() == ["a1", "b1"]
    )
    assert df_match_contains.index.get_level_values("sector").unique() == ["cc"]

    # 3. test the match functionality
    df_match_match = index_match(test_df, region="b")
    assert all(df_match_match.index.get_level_values("region").unique() == ["b1", "b2"])

    # 4. test the findall functionality
    df_match_findall = index_contains(test_df, find_all="c")
    for id_row in df_match_findall.index:
        assert "c" in id_row[0] or "c" in id_row[1]

    # 5. test wrong input
    with pytest.raises(ValueError):
        index_fullmatch("foo", region="a.*", sector=".*b.*", not_present_column="abc")

    # 6. test with all kwargs not present

    df_some_match = index_match(
        test_df, region="a.*", sector=".*b.*", not_present_column="abc"
    )
    assert df_some_match.index.get_level_values("region").unique() == ["a1"]
    assert df_some_match.index.get_level_values("sector").unique() == ["bb"]

    df_none_match = index_match(test_df, not_present_column="abc")
    df_none_match_index = index_contains(test_index, not_present_column="abc")
    assert len(df_none_match) == 0
    assert len(df_none_match_index) == 0


def test_char_table():
    """ Testing the characterization of one table """

    to_char = pd.DataFrame(
        data=5,
        index=pd.MultiIndex.from_product([["em1", "em2"], ["air", "water"]]),
        columns=pd.MultiIndex.from_product([["r1", "c1"], ["r2", "c2"]]),
    )
    to_char.columns.names = ["reg", "sec"]
    to_char.index.names = ["em_type", "compart"] 

    mapping = pd.DataFrame(
        columns=["em_type", "compart", "total__em_type", "factor"],
        data=[["em.*", "air|water", "total_regex", 2], 

              ["em1", "air", "total_sum", 2], 
              ["em1", "water", "total_sum", 2], 
              ["em2", "air", "total_sum", 2], 
              ["em2", "water", "total_sum", 2], 

              ["em1", "air", "all_air", 0.5], 
              ["em2", "air", "all_air", 0.5]],
    )

    exp_res = pd.DataFrame(
        columns = to_char.columns,
        index = ["total_regex", "total_sum", "all_air"])
    exp_res.loc['all_air'] = to_char.loc[("em1", "air")] * 0.5 + to_char.loc[("em2", "air")] * 0.5
    exp_res.loc['total_regex'] = (to_char.sum(axis=1) * 2).values
    exp_res.loc['total_sum'] = (to_char.sum(axis=1) * 2).values
    exp_res = exp_res.astype(float)
    exp_res.sort_index(inplace=True)

    res = match_and_convert(to_char, mapping, agg_func="sum")
    res.sort_index(inplace=True)

    exp_res.index.names = res.index.names
    exp_res.columns.names = res.columns.names

    pdt.assert_frame_equal(res, exp_res)


