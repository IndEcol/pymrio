"""Test the time series functionalities."""

import os
import sys
import zipfile

import pandas as pd
import pandas.testing as pdt
import pytest

TESTPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(TESTPATH, ".."))

import pymrio  # noqa


def test_extract_from_mrioseries(tmpdir):
    """Comprehensive test for extract_from_mrioseries function."""
    # Create test MRIO systems
    test_mrio = pymrio.load_test()
    test_mrio.calc_all()

    test_mrio_doubled = test_mrio.copy()
    test_mrio_doubled.Z = test_mrio_doubled.Z * 2
    test_mrio_doubled.Y = test_mrio_doubled.Y * 2
    test_mrio_doubled.x = test_mrio_doubled.x * 2

    for ext in test_mrio_doubled.get_extensions(data=True):
        for acc_name in ext.get_DataFrame(with_unit=False):
            ext.__dict__[acc_name] = ext.__dict__[acc_name] * 2

    # Test 1: Regular directory extraction
    test_1999_dir = tmpdir.mkdir("test_1999")
    test_2000_dir = tmpdir.mkdir("test_2000")

    test_mrio.save_all(str(test_1999_dir))
    test_mrio_doubled.save_all(str(test_2000_dir))

    mrio_list = sorted(tmpdir.listdir("test_*"))

    # Test basic extraction with year key naming
    result = pymrio.extract_from_mrioseries(
        mrios=mrio_list, key_naming="year", extension="emissions", account="D_cba", index=None, columns=["reg1"]
    )

    assert len(result) == 2
    assert "1999" in result
    assert "2000" in result
    assert result["1999"].shape[1] == 8  # reg1 has 8 sectors
    assert result["2000"].shape[1] == 8

    pdt.assert_frame_equal(result["1999"] * 2, result["2000"])

    # Test with specific index selection
    result_indexed = pymrio.extract_from_mrioseries(
        mrios=mrio_list,
        key_naming="year",
        extension="emissions",
        account="D_cba",
        index=("emission_type1", "air"),
        columns=["reg1"],
    )

    assert result_indexed["1999"].shape == test_mrio.emissions.D_cba.loc[("emission_type1", "air"), "reg1"].shape
    pdt.assert_series_equal(result_indexed["1999"] * 2, result_indexed["2000"])

    # Test with slice to get multiple rows
    result_multirow = pymrio.extract_from_mrioseries(
        mrios=mrio_list, key_naming="year", extension="emissions", account="D_cba", index=slice(None), columns=["reg1"]
    )

    assert result_multirow["1999"].shape == test_mrio.emissions.D_cba.loc[:, "reg1"].shape
    pdt.assert_frame_equal(result_multirow["1999"] * 2, result_multirow["2000"])

    # Test core system extraction
    result_core = pymrio.extract_from_mrioseries(
        mrios=mrio_list, key_naming="year", extension=None, account="Z", index=None, columns=None
    )

    assert len(result_core) == 2
    assert isinstance(result_core["1999"], pd.DataFrame)
    assert isinstance(result_core["2000"], pd.DataFrame)

    # Test with custom key naming function
    def custom_key(name):
        return f"custom_{name}"

    result_custom = pymrio.extract_from_mrioseries(
        mrios=mrio_list, key_naming=custom_key, extension="emissions", account="D_cba", index=None, columns=["reg1"]
    )

    assert "custom_test_1999" in result_custom
    assert "custom_test_2000" in result_custom

    # Test with None key naming (uses folder names)
    result_none = pymrio.extract_from_mrioseries(
        mrios=mrio_list, key_naming=None, extension="emissions", account="D_cba", index=None, columns=["reg1"]
    )

    assert "test_1999" in result_none
    assert "test_2000" in result_none

    # Test 2: ZIP file extraction
    zip_1999 = tmpdir.join("test_1999.zip")
    zip_2000 = tmpdir.join("test_2000.zip")

    # Create ZIP files
    with zipfile.ZipFile(str(zip_1999), "w") as zf:
        for root, _dirs, files in os.walk(str(test_1999_dir)):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, str(test_1999_dir))
                zf.write(file_path, arc_path)

    with zipfile.ZipFile(str(zip_2000), "w") as zf:
        for root, _dirs, files in os.walk(str(test_2000_dir)):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, str(test_2000_dir))
                zf.write(file_path, arc_path)

    zip_list = [str(zip_1999), str(zip_2000)]

    result_zip = pymrio.extract_from_mrioseries(
        mrios=zip_list, key_naming="year", extension="emissions", account="D_cba", index=None, columns=["reg1"]
    )

    assert len(result_zip) == 2
    assert "1999" in result_zip
    assert "2000" in result_zip
    pdt.assert_frame_equal(result_zip["1999"] * 2, result_zip["2000"])

    # Test 3: Error handling for wrong argument types
    with pytest.raises(TypeError):
        pymrio.extract_from_mrioseries(
            mrios=mrio_list,
            key_naming="year",
            extension="emissions",
            account=123,  # Should be string
            index=None,
            columns=["reg1"],
        )

    # Test 4: Single MRIO input (string/Path)
    result_single = pymrio.extract_from_mrioseries(
        mrios=str(mrio_list[0]), key_naming="year", extension="emissions", account="D_cba", index=None, columns=["reg1"]
    )

    assert len(result_single) == 1
    assert "1999" in result_single

    # Test 5: Slice notation for index and columns
    result_slice = pymrio.extract_from_mrioseries(
        mrios=mrio_list, key_naming="year", extension="emissions", account="D_cba", index=":", columns=":"
    )

    assert len(result_slice) == 2
    assert isinstance(result_slice["1999"], pd.DataFrame)

    # Test 6: Different file formats (arquet) - create mock files
    parquet_dir = tmpdir.mkdir("parquet_test")

    # Save as parquet
    test_mrio.save_all(str(parquet_dir), table_format="parquet")

    # Test parquet extraction
    result_parquet = pymrio.extract_from_mrioseries(
        mrios=[str(parquet_dir)], key_naming=None, extension="emissions", account="D_cba", index=None, columns=["reg1"]
    )

    assert len(result_parquet) == 1
    assert "parquet_test" in result_parquet
    assert isinstance(result_parquet["parquet_test"], pd.DataFrame)


def test_apply_method():
    """Test apply_method function from tshelper."""
    # Test with MRIO system and calc_all method
    test_mrio = pymrio.load_test()

    # Ensure calc_all hasn't been called yet
    assert not hasattr(test_mrio, "A") or test_mrio.A is None
    assert not hasattr(test_mrio, "L") or test_mrio.L is None

    # Apply calc_all method using apply_method
    result = pymrio.tools.tshelper.apply_method(test_mrio, "calc_all")

    # Check that calc_all was executed and matrices were calculated
    assert result is test_mrio  # calc_all returns the mrio object
    assert test_mrio.A is not None
    assert test_mrio.L is not None
    assert test_mrio.x is not None
    assert isinstance(test_mrio.A, pd.DataFrame)
    assert isinstance(test_mrio.L, pd.DataFrame)
    assert isinstance(test_mrio.x, pd.DataFrame)

    # Test with pandas DataFrame (additional test case)
    df_ap = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
    result = pymrio.tools.tshelper.apply_method(df_ap, "sum")
    expected = df_ap.sum()
    pdt.assert_series_equal(result, expected)


def test_apply_function():
    """Test apply_function function from tshelper."""
    # Test with MRIO system and function that modifies Z matrix
    test_mrio = pymrio.load_test()

    # Store original Z matrix for comparison
    original_z = test_mrio.Z.copy()

    # Define function that doubles the Z matrix
    def double_z_matrix(mrio):
        mrio.Z = mrio.Z * 2
        return mrio

    # Apply function using apply_function
    result = pymrio.tools.tshelper.apply_function(test_mrio, double_z_matrix)

    # Check that the function was applied and Z was doubled
    assert result is test_mrio  # Function returns the mrio object
    pdt.assert_frame_equal(test_mrio.Z, original_z * 2)

    # Test with built-in function (additional test case)
    result = pymrio.tools.tshelper.apply_function([1, 2, 3], len)
    assert result == 3
