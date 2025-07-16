"""Test cases for all util functions."""

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
    convert,
    diagonalize_blocks,
    diagonalize_columns_to_sectors,
    extend_rows,
    filename_from_url,
    find_first_number,
    index_contains,
    index_fullmatch,
    index_match,
    set_block,
    sniff_csv_format,
)


@pytest.fixture()
def csv_test_files_content():
    """Get the content of csv test."""
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
    """Some tests for finding the first number in a sequence."""
    assert find_first_number([0, 1, 2, 3]) == 0
    assert find_first_number(["a", 1, 2, 3]) == 1
    assert find_first_number(["a", 1, "c", 3]) == 1
    assert find_first_number([None, 1, "c", 3]) == 1
    assert find_first_number(["a", "b"]) == None  # noqa
    assert find_first_number([]) == None  # noqa


def test_dev_read(csv_test_files_content):
    """Tests the csv sniffer."""
    for tests in csv_test_files_content.test_contents:
        with patch("builtins.open", mock_open(read_data=tests.text), create=False) as _:  # noqa
            res = sniff_csv_format("foo")
        assert res["sep"] == tests.sep
        assert res["nr_index_col"] == tests.index_col
        assert res["nr_header_row"] == tests.header_rows


def test_build_agg_matrix():
    """Tests building the aggreagation matrix."""
    am_num = build_agg_matrix([1, 0, 0, 1, 0])
    expected = np.array([[0.0, 1.0, 1.0, 0.0, 1.0], [1.0, 0.0, 0.0, 1.0, 0.0]])
    am_str = build_agg_matrix(["r2", "r1", "r1", "r2", "r1"], pos_dict={"r1": 0, "r2": 1})

    np.testing.assert_allclose(am_num, expected)
    np.testing.assert_allclose(am_str, expected)


def test_build_agg_vec():
    """Simple test based on the test mrio."""
    vec = build_agg_vec(["OECD", "EU"], path="test", miss="RoW")
    expected = ["OECD", "EU", "OECD", "OECD", "RoW", "RoW"]
    assert vec == expected


def test_diagonalize_blocks():
    """Tests the numpy implementation of diagonalize_blocks."""
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
    """Test the diagonalize_columns_to_sectors function for correct behavior."""
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
    reg_sec_index = pd.MultiIndex.from_product([regions, sectors], names=["region", "sector"])

    inp_df = pd.DataFrame(data=inp_array, index=reg_sec_index, columns=regions)
    inp_df.columns.names = ["region"]

    out_df = pd.DataFrame(data=out_array, index=inp_df.index, columns=reg_sec_index)

    diag_df = diagonalize_columns_to_sectors(inp_df)
    pdt.assert_frame_equal(diag_df, out_df)


def test_set_block():
    """Set block util function."""
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
    """Getting filename from url tests."""
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

    for filename in test_urls:
        assert filename_from_url(test_urls[filename]) == filename


def test_util_regex():
    """Test regex matching."""
    test_index = pd.MultiIndex.from_product(
        [["a1", "b1", "c2", "b2"], ["aa", "bb", "cc", "dd"]],
        names=["region", "sector"],
    )

    test_df = pd.DataFrame(data=np.random.random((16, 2)), index=test_index, columns=["foo", "bar"])

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

    assert len(mdx_match.get_level_values("region").unique().difference({"c2", "b2"})) == 0

    test_ds = test_df.foo
    ds_match = index_fullmatch(test_ds, sector="aa")

    assert ds_match.index.get_level_values("sector").unique() == ["aa"]
    assert all(ds_match.index.get_level_values("region").unique() == ["a1", "b1", "c2", "b2"])

    idx_match = index_fullmatch(test_index.get_level_values("region"), region=".*2")
    assert len(idx_match.get_level_values("region").unique().difference({"c2", "b2"})) == 0

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
    assert all(df_match_contains.index.get_level_values("region").unique() == ["a1", "b1"])
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

    df_some_match = index_match(test_df, region="a.*", sector=".*b.*", not_present_column="abc")
    assert df_some_match.index.get_level_values("region").unique() == ["a1"]
    assert df_some_match.index.get_level_values("sector").unique() == ["bb"]

    df_none_match = index_match(test_df, not_present_column="abc")
    df_none_match_index = index_contains(test_index, not_present_column="abc")
    assert len(df_none_match) == 0
    assert len(df_none_match_index) == 0


def test_convert_rename_singleindex():
    """Testing the renaming of one table with a single index."""
    to_char = pd.DataFrame(data=99.0, index=["em1", "em2", "em3"], columns=["r1", "r2", "r3"])
    to_char.index.name = "em_type"
    to_char.columns.name = "reg"

    rename_bridge_simple = pd.DataFrame(
        columns=["em_type", "stressor__em_type"],
        data=[
            ["em1", "emission1"],
            ["em2", "emission2"],
            ["em3", "emission3"],
        ],
    )

    renamed = convert(to_char, rename_bridge_simple)
    assert all(renamed.columns == renamed.columns)
    assert all(renamed.index == rename_bridge_simple["stressor__em_type"])


def test_convert_rename_multiindex():
    """Testing the renaming of one table with a multiindex."""
    to_char = pd.DataFrame(
        data=99.0,
        index=pd.MultiIndex.from_product([["em1", "em2", "emA"], ["air", "water"]]),
        columns=pd.MultiIndex.from_product([["r1", "c1"], ["r2", "c2"]]),
    )

    to_char.columns.names = ["reg", "sec"]
    to_char.index.names = ["em_type", "compart"]

    rename_bridge_simple = pd.DataFrame(
        columns=["em_type", "stressor__em_type", "factor"],
        data=[
            ["em1", "emission-1", 1],
            ["em2", "emission2", 1],
            ["emA", "emission A", 1],
        ],
    )

    char_res_keep_comp = convert(to_char, rename_bridge_simple, drop_not_bridged_index=False)

    assert all(char_res_keep_comp.columns == to_char.columns)
    assert all(char_res_keep_comp.index.get_level_values("compart") == to_char.index.get_level_values("compart"))
    npt.assert_allclose(char_res_keep_comp.values, to_char.values)

    pdt.assert_index_equal(
        char_res_keep_comp.index.get_level_values("stressor"),
        pd.Index(
            [
                "emission A",
                "emission A",
                "emission-1",
                "emission-1",
                "emission2",
                "emission2",
            ],
            dtype="object",
            name="stressor",
        ),
    )

    char_res_agg_comp = convert(to_char, rename_bridge_simple, drop_not_bridged_index=True)

    assert all(char_res_agg_comp.columns == to_char.columns)
    assert char_res_agg_comp.sum().sum() == to_char.sum().sum()

    pdt.assert_index_equal(
        char_res_agg_comp.index,
        pd.Index(
            [
                "emission A",
                "emission-1",
                "emission2",
            ],
            dtype="object",
            name="stressor",
        ),
    )

    # without factor should give the same result
    rename_bridge_simple_wo_factor = pd.DataFrame(
        columns=["em_type", "stressor__em_type"],
        data=[
            ["em1", "emission-1"],
            ["em2", "emission2"],
            ["emA", "emission A"],
        ],
    )

    char_res_keep_comp_wo_factor = convert(to_char, rename_bridge_simple_wo_factor, drop_not_bridged_index=False)

    pdt.assert_frame_equal(char_res_keep_comp_wo_factor, char_res_keep_comp)


def test_convert_rename_spread_index():
    """Testing the renaming of one table from an index to an multiindex.

    This is for example needed for the EXIOBASE stressor to GLAM conversion,
    where one stressor level need to be spread to multiple flows/classes.
    """
    # TEST SIMPLE CASE: SPREADING SINGLE INDEX TO MULTIINDEX

    to_char = pd.DataFrame(data=99.0, index=["em1", "em2", "em3"], columns=["r1", "r2", "r3"])
    to_char.index.name = "stressor"
    to_char.columns.name = "reg"

    rename_bridge_simple = pd.DataFrame(
        columns=["stressor", "flow__stressor", "class__stressor", "class2__stressor"],
        data=[
            ["em1", "emission1", "to_air", "to_air (unspecified)"],
            ["em2", "emission2", "to_air", "to_air (specified)"],
            ["em3", "emission3", "to_water", "to_water (unspecified)"],
        ],
    )

    renamed_simple = convert(to_char, rename_bridge_simple)

    assert all(renamed_simple.columns == to_char.columns)
    rename_bridge_indexed = rename_bridge_simple.set_index(["flow__stressor", "class__stressor", "class2__stressor"])
    rename_bridge_indexed.index.names = ["flow", "class", "class2"]
    pdt.assert_index_equal(renamed_simple.index, rename_bridge_indexed.index)

    # TEST WITH COLUMN SPECS

    rename_bridge_with_reg_spec = pd.DataFrame(
        columns=[
            "stressor",
            "reg",
            "flow__stressor",
            "class__stressor",
            "class2__stressor",
            "factor",
        ],
        data=[
            ["em1", "r[1,2]", "emission1", "to_air", "to_air (unspecified)", 1],
            ["em1", "r[3]", "emission1", "to_air", "to_air (unspecified)", 2],
            ["em2", "r[1,2,3]", "emission2", "to_air", "to_air (specified)", 1],
            ["em3", "r[1,2,3]", "emission3", "to_water", "to_water (unspecified)", 1],
        ],
    )

    renamed_region_spec = convert(to_char, rename_bridge_with_reg_spec)
    assert all(renamed_region_spec.columns == to_char.columns)
    pdt.assert_index_equal(renamed_simple.index, renamed_region_spec.index)

    npt.assert_allclose(
        renamed_region_spec.loc[("emission1", "to_air", "to_air (unspecified)"), "r1"],
        99,
    )
    npt.assert_allclose(
        renamed_region_spec.loc[("emission1", "to_air", "to_air (unspecified)"), "r3"],
        99 * 2,
    )
    npt.assert_allclose(
        renamed_region_spec.loc[("emission3", "to_water", "to_water (unspecified)"), "r3"],
        99,
    )

    # TEST WITH EMPTY INDEX

    rename_bridge_missing_string = pd.DataFrame(
        columns=["stressor", "flow__stressor", "class__stressor", "class2__stressor"],
        data=[
            ["em1", "emission1", "to_air", "to_air (unspecified)"],
            ["em2", "emission2", "to_air", "to_air (specified)"],
            [
                "em3",
                "emission3",
                "to_water",
            ],
        ],
    )

    rename_bridge_missing_nan = pd.DataFrame(
        columns=["stressor", "flow__stressor", "class__stressor", "class2__stressor"],
        data=[
            ["em1", "emission1", "to_air", "to_air (unspecified)"],
            ["em2", "emission2", "to_air", "to_air (specified)"],
            ["em3", "emission3", "to_water", np.nan],
        ],
    )

    rename_bridge_missing_none = pd.DataFrame(
        columns=["stressor", "flow__stressor", "class__stressor", "class2__stressor"],
        data=[
            ["em1", "emission1", "to_air", "to_air (unspecified)"],
            ["em2", "emission2", "to_air", "to_air (specified)"],
            ["em3", "emission3", "to_water", None],
        ],
    )

    renamed_missing_string = convert(to_char, rename_bridge_missing_string)
    renamed_missing_nan = convert(to_char, rename_bridge_missing_nan)
    renamed_missing_none = convert(to_char, rename_bridge_missing_none)

    pdt.assert_frame_equal(renamed_missing_string, renamed_missing_nan)
    pdt.assert_frame_equal(renamed_missing_string, renamed_missing_none)

    assert all(renamed_simple.columns == to_char.columns)
    rename_bridge_indexed = rename_bridge_simple.set_index(["flow__stressor", "class__stressor", "class2__stressor"])
    rename_bridge_indexed.index.names = ["flow", "class", "class2"]
    pdt.assert_index_equal(renamed_simple.index, rename_bridge_indexed.index)

    # TEST WITH RENAME IN MUTLIINDEX

    to_char_multi = pd.DataFrame(
        data=99.0,
        index=pd.MultiIndex.from_product([["em1", "em2", "emA"], ["air", "water"]]),
        columns=pd.MultiIndex.from_product([["r1", "c1"], ["r2", "c2"]]),
    )
    to_char_multi.columns.names = ["reg", "sec"]
    to_char_multi.index.names = ["em_type", "compart"]

    rename_bridge_level1 = pd.DataFrame(
        columns=["em_type", "stressor__em_type", "class__em_type", "factor"],
        data=[
            ["em1", "emission-1", "classA", 1],
            ["em2", "emission2", "classA", 1],
            ["emA", "emission A", "classB", 1],
        ],
    )

    ren_multi1_comp = convert(to_char_multi, rename_bridge_level1, drop_not_bridged_index=False)

    ren_multi1_wocomp = convert(to_char_multi, rename_bridge_level1, drop_not_bridged_index=True)

    assert all(ren_multi1_comp.columns == to_char_multi.columns)
    assert all(ren_multi1_wocomp.columns == to_char_multi.columns)

    rename_bridge_level1_indexed = rename_bridge_level1.set_index(["stressor__em_type", "class__em_type"])

    rename_bridge_level1_indexed.index.names = ["stressor", "class"]
    pdt.assert_index_equal(rename_bridge_level1_indexed.index, ren_multi1_wocomp.index, check_order=False)

    assert "compart" in ren_multi1_comp.index.names

    rename_bridge_level2 = pd.DataFrame(
        columns=[
            "em_type",
            "compart",
            "stressor__em_type",
            "comp__compart",
            "class__compart",
            "factor",
        ],
        data=[
            ["em1", "air", "emission-1", "A", "class1", 1],
            ["em1", "water", "emission-1", "B", "class1", 1],
            ["em2", "air", "emission2", "A", "class2", 1],
            ["em2", "water", "emission2", "B", "class2", 1],
            ["emA", "air", "emission A", "A", "class3", 1],
            ["emA", "water", "emission A", "B", "class3", 1],
        ],
    )

    ren_multi2_comp = convert(to_char_multi, rename_bridge_level2)

    npt.assert_allclose(ren_multi2_comp.values, to_char_multi.values)
    rename_bridge_level2_indexed = rename_bridge_level2.set_index(
        ["stressor__em_type", "comp__compart", "class__compart"]
    )
    rename_bridge_level2_indexed.index.names = ["stressor", "comp", "class"]
    pdt.assert_index_equal(rename_bridge_level2_indexed.index, ren_multi2_comp.index, check_order=False)


def test_convert_characterize():
    """Testing the characterization of one table."""
    to_char = pd.DataFrame(
        data=5,
        index=pd.MultiIndex.from_product([["em1", "em2"], ["air", "water"]]),
        columns=pd.MultiIndex.from_product([["r1", "c1"], ["r2", "c2"]]),
    )
    to_char.columns.names = ["reg", "sec"]
    to_char.index.names = ["em_type", "compart"]

    # TEST1A: with only impact (one index level in the result)
    # sum over compartments as the compartment gets dropped in the argument

    map_test1 = pd.DataFrame(
        columns=["em_type", "compart", "total__em_type", "factor"],
        data=[
            ["em.*", "air|water", "total_regex", 2],
            ["em1", "air", "total_sum", 2],
            ["em1", "water", "total_sum", 2],
            ["em2", "air", "total_sum", 2],
            ["em2", "water", "total_sum", 2],
            ["em1", "air", "all_air", 0.5],
            ["em2", "air", "all_air", 0.5],
        ],
    )

    # alternative way to calculated the expected result
    exp_res1A = pd.DataFrame(columns=to_char.columns, index=["total_regex", "total_sum", "all_air"])
    exp_res1A.loc["all_air"] = to_char.loc[("em1", "air")] * 0.5 + to_char.loc[("em2", "air")] * 0.5
    exp_res1A.loc["total_regex"] = (to_char.sum(axis=1) * 2).to_numpy()
    exp_res1A.loc["total_sum"] = (to_char.sum(axis=1) * 2).to_numpy()
    exp_res1A = exp_res1A.astype(float)
    exp_res1A = exp_res1A.sort_index()

    res1A = convert(to_char, map_test1, drop_not_bridged_index=True, reindex=None)

    exp_res1A.index.names = res1A.index.names
    exp_res1A.columns.names = res1A.columns.names

    pdt.assert_frame_equal(res1A, exp_res1A)

    # test reordering (alphabetic already checked with passing None before)
    res1A_co = convert(to_char, map_test1, drop_not_bridged_index=True, reindex="total__em_type")
    exp_res1A_co = exp_res1A.reindex(["total_regex", "total_sum", "all_air"])

    pdt.assert_frame_equal(res1A_co, exp_res1A_co)

    with pytest.raises(ValueError):
        convert(to_char, map_test1, drop_not_bridged_index=True, reindex="non_existing")

    res1A_co2 = convert(
        to_char,
        map_test1,
        drop_not_bridged_index=True,
        reindex=["total_sum", "total_regex", "all_air"],
    )
    exp_res1A_co2 = exp_res1A.reindex(["total_sum", "total_regex", "all_air"])
    pdt.assert_frame_equal(res1A_co2, exp_res1A_co2)

    # TEST1B: with only impact (one index level in the result) ,
    # keep compartments as these are not dropped now

    res1B = convert(to_char, map_test1, drop_not_bridged_index=False)

    exp_res1B = pd.DataFrame(
        columns=to_char.columns,
        index=pd.MultiIndex.from_tuples(
            [
                ("all_air", "air"),
                ("total_regex", "air"),
                ("total_regex", "water"),
                ("total_sum", "air"),
                ("total_sum", "water"),
            ]
        ),
        data=[
            [5, 5, 5, 5],
            [20, 20, 20, 20],
            [20, 20, 20, 20],
            [20, 20, 20, 20],
            [20, 20, 20, 20],
        ],
    )
    exp_res1B = exp_res1B.astype(float)
    exp_res1B.index.names = res1B.index.names

    pdt.assert_frame_equal(res1B, exp_res1B)

    # TEST2 with impact per compartment (two index levels in the result)

    map_test2 = pd.DataFrame(
        columns=["em_type", "compart", "total__em_type", "compart__compart", "factor"],
        data=[
            ["em.*", "air|water", "total_regex", "all", 2],
            ["em1", "air", "total_sum", "all", 2],
            ["em1", "water", "total_sum", "all", 2],
            ["em2", "air", "total_sum", "all", 2],
            ["em2", "water", "total_sum", "all", 2],
            ["em1", "air", "all_air", "air", 0.5],
            ["em2", "air", "all_air", "air", 0.5],
        ],
    )

    # alternative way to calculated the expected result
    exp_res2 = pd.DataFrame(
        columns=to_char.columns,
        index=pd.MultiIndex.from_tuples([("total_regex", "all"), ("total_sum", "all"), ("all_air", "air")]),
    )
    exp_res2.loc[("all_air", "air")] = to_char.loc[("em1", "air")] * 0.5 + to_char.loc[("em2", "air")] * 0.5
    exp_res2.loc[("total_regex", "all")] = (to_char.sum(axis=1) * 2).to_numpy()
    exp_res2.loc[("total_sum", "all")] = (to_char.sum(axis=1) * 2).to_numpy()
    exp_res2 = exp_res2.astype(float)
    exp_res2 = exp_res2.sort_index()

    res2 = convert(to_char, map_test2)
    res2 = res2.sort_index()

    exp_res2.index.names = res2.index.names
    exp_res2.columns.names = res2.columns.names

    pdt.assert_frame_equal(res2, exp_res2)

    # TEST3 with passing through one index to the results
    # Done for compartment here

    map_test3 = pd.DataFrame(
        columns=["em_type", "compart", "total__em_type", "compart__compart", "factor"],
        data=[
            ["em.*", "air|water", "total_regex", "all", 2],
            ["em1", "air", "total_sum", "all", 2],
            ["em1", "water", "total_sum", "all", 2],
            ["em2", "air", "total_sum", "all", 2],
            ["em2", "water", "total_sum", "all", 2],
            ["em1", "air", "all_air", "air", 0.5],
            ["em2", "air", "all_air", "air", 0.5],
        ],
    )

    # alternative way to calculated the expected result
    exp_res3 = pd.DataFrame(
        columns=to_char.columns,
        index=pd.MultiIndex.from_tuples([("total_regex", "all"), ("total_sum", "all"), ("all_air", "air")]),
    )
    exp_res3.loc[("all_air", "air")] = to_char.loc[("em1", "air")] * 0.5 + to_char.loc[("em2", "air")] * 0.5
    exp_res3.loc[("total_regex", "all")] = (to_char.sum(axis=1) * 2).to_numpy()
    exp_res3.loc[("total_sum", "all")] = (to_char.sum(axis=1) * 2).to_numpy()
    exp_res3 = exp_res3.astype(float)
    exp_res3 = exp_res3.sort_index()

    res3 = convert(to_char, map_test3)
    res3 = res3.sort_index()

    exp_res3.index.names = res3.index.names
    exp_res3.columns.names = res3.columns.names

    pdt.assert_frame_equal(res3, exp_res3)

    # TEST 4, with one constraints in the columns

    map_test4 = pd.DataFrame(
        columns=["Region1", "Region2", "Region3"],
        index=[
            "Wheat",
            "Maize",
            "Rice",
            "Pasture",
            "Forest extensive",
            "Forest intensive",
        ],
        data=[
            [3, 10, 1],
            [5, 20, 3],
            [0, 12, 34],
            [12, 34, 9],
            [32, 27, 11],
            [43, 17, 24],
        ],
    )
    map_test4.index.names = ["stressor"]
    map_test4.columns.names = ["region"]

    char4 = pd.DataFrame(
        columns=["stressor", "BioDiv__stressor", "region", "factor"],
        data=[
            ["Wheat|Maize", "BioImpact", "Region1", 3],
            ["Wheat", "BioImpact", "Region[2,3]", 4],
            ["Maize", "BioImpact", "Region[2,3]", 7],
            ["Rice", "BioImpact", "Region1", 12],
            ["Rice", "BioImpact", "Region2", 12],
            ["Rice", "BioImpact", "Region3", 12],
            ["Pasture", "BioImpact", "Region[1,2,3]", 12],
            ["Forest.*", "BioImpact", "Region1", 2],
            ["Forest.*", "BioImpact", "Region2", 3],
            ["Forest ext.*", "BioImpact", "Region3", 1],
            ["Forest int.*", "BioImpact", "Region3", 3],
        ],
    )

    expected4 = pd.DataFrame(
        columns=["Region1", "Region2", "Region3"],
        index=["BioImpact"],
        data=[
            [
                3 * 3 + 5 * 3 + 0 * 12 + 12 * 12 + 32 * 2 + 43 * 2,
                10 * 4 + 20 * 7 + 12 * 12 + 34 * 12 + 27 * 3 + 17 * 3,
                1 * 4 + 3 * 7 + 34 * 12 + 9 * 12 + 11 * 1 + 24 * 3,
            ]
        ],
    )
    expected4.columns.names = ["region"]
    expected4.index.names = ["BioDiv"]

    char4_calc_nostack = convert(map_test4, char4)

    pdt.assert_frame_equal(char4_calc_nostack, expected4)

    map_test4_stack = map_test4.stack(level="region")

    char4_calc_stack = convert(map_test4_stack, char4, drop_not_bridged_index=False).unstack(level="region")[0]

    pdt.assert_frame_equal(char4_calc_nostack, char4_calc_stack)

    # TEST 4, with sectors in addition

    map_test5 = pd.DataFrame(
        columns=pd.MultiIndex.from_product([["Region1", "Region2", "Region3"], ["SecA", "SecB"]]),
        index=[
            "Wheat",
            "Maize",
            "Rice",
            "Pasture",
            "Forest extensive",
            "Forest intensive",
        ],
        data=[
            [1.2, 1.8, 7, 3, 1, 0],
            [5, 0, 12, 8, 1.5, 1.5],
            [0, 0, 6, 6, 30, 4],
            [10, 2, 14, 20, 6, 3],
            [30, 2, 20, 7, 10, 1],
            [23, 20, 7.0, 10.0, 14, 10],
        ],
    )
    map_test5.index.names = ["stressor"]
    map_test5.columns.names = ["region", "sector"]

    char5_res = convert(map_test5, char4)
    pdt.assert_frame_equal(char5_res.T.groupby(level="region").sum().T, char4_calc_nostack.astype("float"))

    # TODO: test case for multindex characterization on one of teh inner levels
    # does not work in the GLAM example


def test_convert_wrong_inputs():
    """Testing wrong inputs for convert function."""
    to_char = pd.DataFrame(
        data=5,
        index=pd.MultiIndex.from_product([["em1", "em2"], ["air", "water"]]),
        columns=pd.MultiIndex.from_product([["r1", "c1"], ["r2", "c2"]]),
    )
    to_char.columns.names = ["reg", "sec"]
    to_char.index.names = ["em_type", "compart"]

    # TEST1, no mapping columns

    map_test1 = pd.DataFrame(
        columns=["em_type", "compart", "total_to_em_type", "factor"],
        data=[
            ["em.*", "air|water", "total_regex", 2],
            ["em1", "air", "total_sum", 2],
            ["em1", "water", "total_sum", 2],
            ["em2", "air", "total_sum", 2],
            ["em2", "water", "total_sum", 2],
            ["em1", "air", "all_air", 0.5],
            ["em2", "air", "all_air", 0.5],
        ],
    )

    with pytest.raises(ValueError):
        _res1 = convert(to_char, map_test1)

    # TEST2, wrong format of mapping columns

    map_test2 = pd.DataFrame(
        columns=["em_type", "compart", "total__to__type", "factor"],
        data=[
            ["em.*", "air|water", "total_regex", 2],
            ["em1", "air", "total_sum", 2],
            ["em1", "water", "total_sum", 2],
            ["em2", "air", "total_sum", 2],
            ["em2", "water", "total_sum", 2],
            ["em1", "air", "all_air", 0.5],
            ["em2", "air", "all_air", 0.5],
        ],
    )

    with pytest.raises(ValueError):
        _res2 = convert(to_char, map_test2)

    # TEST3, wrong name in the bridge columns

    map_test3 = pd.DataFrame(
        columns=["em_type", "compart", "total__foo", "factor"],
        data=[
            ["em.*", "air|water", "total_regex", 2],
            ["em1", "air", "total_sum", 2],
            ["em1", "water", "total_sum", 2],
            ["em2", "air", "total_sum", 2],
            ["em2", "water", "total_sum", 2],
            ["em1", "air", "all_air", 0.5],
            ["em2", "air", "all_air", 0.5],
        ],
    )

    with pytest.raises(ValueError):
        _res3 = convert(to_char, map_test3)

    # TEST4, bridge names to not match the original names

    map_test4 = pd.DataFrame(
        columns=["BAR", "compart", "total__BAR", "factor"],
        data=[
            ["em.*", "air|water", "total_regex", 2],
            ["em1", "air", "total_sum", 2],
            ["em1", "water", "total_sum", 2],
            ["em2", "air", "total_sum", 2],
            ["em2", "water", "total_sum", 2],
            ["em1", "air", "all_air", 0.5],
            ["em2", "air", "all_air", 0.5],
        ],
    )

    with pytest.raises(ValueError):
        _res4 = convert(to_char, map_test4)


def test_extend_rows():
    """Test basic extend functionality with string values."""
    df_to_extend = pd.DataFrame(
        {
            "region": ["GLO", "GLO", "GLO"],
            "sector": ["A", "B", "C"],
            "value": [1, 2, 3],
        }
    )
    # Test with empty new_values list (shouldn't change the original rows).

    result = extend_rows(df_to_extend, region={"GLO": ["reg1", "reg2"]})
    assert len(result) == 6
    assert set(result["region"].unique()) == {"reg1", "reg2"}

    # Test spreading two columns, one it itself and another column.
    df_to_extend = pd.DataFrame(
        {
            "region": ["GLO", "GLO", "GLO"],
            "sector": ["A", "B", "C"],
            "value": [1, 2, 3],
        }
    )

    result = extend_rows(df_to_extend, region={"GLO": ["reg1", "reg2"]}, sector={"C": ["C", "D"]})
    assert len(result) == 8  # 2 regions * (2 sectors from C + 2 original sectors)
    assert set(result["region"].unique()) == {"reg1", "reg2"}
    assert set(result["sector"].unique()) == {"A", "B", "C", "D"}
    assert all(result[(result.sector == "A") & (result.region == "reg1")].value == 1)
    assert all(result[(result.sector == "D") & (result.region == "reg1")].value == 3)
    assert all(result[(result.sector == "C") & (result.region == "reg1")].value == 3)

    # Tests extending rows for multiple values in the same column.
    df_to_extend = pd.DataFrame(
        {
            "region": ["GLO", "EU", "USA"],
            "sector": ["A", "B", "C"],
            "value": [10, 20, 30],
        }
    )

    result = extend_rows(
        df_to_extend,
        region={"GLO": ["reg1", "reg2"], "EU": ["France", "Germany", "Austria"]},
    )

    # Original had 3 rows, GLO expands to 2 new rows, EU expands to 3 new rows, + 1 USA.
    assert len(result) == 6
    assert set(result["region"].unique()) == {
        "reg1",
        "reg2",
        "France",
        "Germany",
        "USA",
        "Austria",
    }
    assert "GLO" not in result["region"].to_numpy()
    assert "EU" not in result["region"].to_numpy()

    # Check values were properly copied.
    assert all(result[result.region == "reg1"].value == 10)
    assert all(result[result.region == "reg2"].value == 10)
    assert all(result[result.region == "France"].value == 20)
    assert all(result[result.region == "Germany"].value == 20)
    assert all(result[result.region == "Austria"].value == 20)
    assert all(result[result.region == "USA"].value == 30)

    # Test with numerical values.
    df_to_extend = pd.DataFrame(
        {
            "year": [2020, 2020, 2020],
            "id": [1, 2, 3],
            "value": [10, 20, 30],
        }
    )

    result = extend_rows(df_to_extend, year={2020: [2021, 2022]})
    assert len(result) == 6
    assert set(result["year"].unique()) == {2021, 2022}
    assert result["value"].sum() == 2 * (10 + 20 + 30)

    # Test ValueError for non-numerical DataFrame.
    df_with_custom_index = pd.DataFrame(
        {
            "region": ["GLO", "GLO"],
            "value": [1, 2],
        },
        index=["a", "b"],
    )

    with pytest.raises(ValueError, match="DataFrame index must be numerical"):
        extend_rows(df_with_custom_index, region={"GLO": ["reg1"]})

    # Test ValueError for non-existent column.
    with pytest.raises(ValueError, match="Column nonexistent not in DataFrame"):
        extend_rows(df_to_extend, nonexistent={"val": ["new"]})

    # Test ValueError for non-existent value to spread.
    with pytest.raises(ValueError, match="No rows found to spread for value"):
        extend_rows(df_to_extend, year={1999: ["new"]})

    # Test with empty new_values list (shouldn't change the original rows)
    df_to_extend = pd.DataFrame(
        {
            "region": ["GLO", "EU"],
            "value": [1, 2],
        }
    )

    result = extend_rows(df_to_extend, region={"GLO": []})

    assert len(result) == 2
    assert set(result["region"].unique()) == {"GLO", "EU"}
