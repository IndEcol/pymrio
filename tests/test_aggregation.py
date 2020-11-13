""" Tests the aggregation functionality in pymrio

This only test the top-level aggregation function.
For the low-level function 'build_agg_vec' and 'build_agg_matrix'
see test_util.py
"""

import os
import sys

import numpy as np
import pandas as pd
import pytest

TESTPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(TESTPATH, ".."))

import pymrio  # noqa


def test_aggreation_regions():
    """Testing aggregation of regions in various ways"""
    # All these representations should lead to the same results
    reg_agg_matrix = np.array([[1, 1, 1, 0, 0, 0], [0, 0, 0, 1, 1, 1]])

    reg_agg_vec1 = np.array([0, 0, 0, 1, 1, 1])
    reg_agg_vec2 = [0, 0, 0, 1, 1, 1]
    reg_agg_vec3 = ["a", "a", "a", "b", "b", "b"]

    reg_agg_df = pd.DataFrame(
        data=[
            ("reg1", "a"),
            ("reg5", "b"),
            ("reg3", "a"),
            ("reg4", "b"),
            ("reg2", "a"),
            ("reg6", "b"),
        ],
        index=range(6),
        columns=["original", "aggregated"],
    )

    io = pymrio.load_test()
    io.calc_all()
    manual_agg = (
        io.emissions.D_cba_reg.reg1
        + io.emissions.D_cba_reg.reg2
        + io.emissions.D_cba_reg.reg3
    )

    io_agg_wo_names = io.aggregate(region_agg=reg_agg_matrix, inplace=False)
    np.testing.assert_allclose(
        manual_agg.values, io_agg_wo_names.emissions.D_cba_reg.reg0
    )

    assert ["reg0", "reg1"] == io_agg_wo_names.get_regions().tolist()

    io_agg_with_names = io.aggregate(
        region_agg=reg_agg_matrix, region_names=["a", "b"], inplace=False
    )
    np.testing.assert_allclose(
        manual_agg.values, io_agg_with_names.emissions.D_cba_reg.a
    )

    assert ["a", "b"] == io_agg_with_names.get_regions().tolist()

    io_vec1 = io.aggregate(region_agg=reg_agg_vec1, inplace=False)
    io_vec2 = io.aggregate(region_agg=reg_agg_vec2, inplace=False)
    io_vec3 = io.aggregate(region_agg=reg_agg_vec3, inplace=False)
    np.testing.assert_allclose(manual_agg.values, io_vec1.emissions.D_cba_reg.reg0)
    np.testing.assert_allclose(manual_agg.values, io_vec2.emissions.D_cba_reg.reg0)
    np.testing.assert_allclose(manual_agg.values, io_vec3.emissions.D_cba_reg.a)

    io_df = io.aggregate(region_agg=reg_agg_df, inplace=False)
    np.testing.assert_allclose(manual_agg.values, io_df.emissions.D_cba_reg.a)

    assert ["a", "b"] == io_df.get_regions().tolist()


def test_numerical_aggreation_sectors():
    """Testing aggregation of sectors with a numeric array"""
    sec_agg = np.array(
        [[1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 1, 1, 1, 0, 0, 0], [0, 0, 0, 0, 0, 1, 1, 1]]
    )

    io = pymrio.load_test()
    io.calc_all()

    manual_agg = (
        io.emissions.D_pba.xs("trade", level="sector", axis=1)
        + io.emissions.D_pba.xs("transport", level="sector", axis=1)
        + io.emissions.D_pba.xs("other", level="sector", axis=1)
    )

    io.aggregate(sector_agg=sec_agg)

    np.testing.assert_allclose(
        manual_agg.values, io.emissions.D_pba.xs("sec2", level="sector", axis=1)
    )


def test_wrong_inputs():
    """Tests if correct Exceptions are raised for wrong shaped input arguments"""
    io = pymrio.load_test().calc_all()

    with pytest.raises(ValueError) as VA_sector_number:
        sec_agg = range(len(io.get_sectors()) - 1)
        _ = io.aggregate(sector_agg=sec_agg, inplace=False)
    assert "sector aggregation" in str(VA_sector_number.value).lower()

    with pytest.raises(ValueError) as VA_region_number:
        reg_agg = range(len(io.get_regions()) + 13)
        _ = io.aggregate(region_agg=reg_agg, inplace=False)
    assert "region aggregation" in str(VA_region_number.value).lower()

    with pytest.raises(ValueError) as VA_sector_name:
        sec_agg = range(len(io.get_sectors()))
        _ = io.aggregate(sector_agg=sec_agg, sector_names="C", inplace=False)
    assert "sector aggregation" in str(VA_sector_name.value).lower()

    with pytest.raises(ValueError) as VA_region_name:
        reg_agg = range(len(io.get_regions()))
        _ = io.aggregate(
            region_agg=reg_agg, region_names=["a", "b"], inplace=False  # noqa
        )
    assert "region aggregation" in str(VA_region_name.value).lower()


def test_total_agg():
    """Testing aggregation to total values"""
    io = pymrio.load_test().calc_all()
    np.testing.assert_allclose(
        io.emissions.D_cba.sum(axis=1).to_frame().values,
        io.aggregate(region_agg="global", sector_agg="total").emissions.D_cba.values,
    )


def test_underdefined_agg():
    """Testing correct error message for underdefined aggregation"""
    io = pymrio.load_test().calc_all()
    io.reset_all_to_coefficients()
    with pytest.raises(pymrio.core.mriosystem.AggregationError):
        io.aggregate(region_agg="global", sector_agg="total")
