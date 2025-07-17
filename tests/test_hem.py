"""Test cases for HEM calculations."""

import os
import shutil
import sys

import pandas as pd
import pandas.testing as pdt
import pytest

import pymrio

# the function which should be tested here
from pymrio.core.mriosystem import Extension, IOSystem
from pymrio.tools.iohem import HEM, load_extraction
from pymrio.tools.iomath import calc_S

TESTPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(TESTPATH, ".."))


@pytest.fixture()
def td_small_MRIO():
    """Small MRIO with three sectors and two regions.

    The testdata here just consists of pandas DataFrames, the functionality
    with numpy arrays gets tested with td_IO_Data_Miller.
    """
    _sectors = ["sector1", "sector2", "sector3"]
    _regions = ["reg1", "reg2"]
    _Z_multiindex = pd.MultiIndex.from_product([_regions, _sectors], names=["region", "sector"])

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
    _Y_multiindex = pd.MultiIndex.from_product([_regions, _categories], names=["region", "category"])
    Y = pd.DataFrame(
        data=[[14, 3], [2.5, 2.5], [13, 6], [5, 20], [10, 10], [3, 10]],
        index=_Z_multiindex,
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

    IO_object = IOSystem(Z=Z, A=A, Y=Y, x=x, L=L)

    F_one = pd.DataFrame(
        data=[[20, 1, 42, 4, 20, 5], [5, 4, 11, 8, 2, 10]],
        index=["ext_type_11", "ext_type_12"],
        columns=_Z_multiindex,
        dtype=("float64"),
    )

    F_Y_one = pd.DataFrame(
        data=[[50, 10], [100, 20]],
        index=["ext_type_11", "ext_type_12"],
        columns=_Y_multiindex,
        dtype=("float64"),
    )

    F_two = pd.DataFrame(
        data=[[20, 1, 42, 4, 20, 5], [5, 4, 11, 8, 2, 10]],
        index=["ext_type_21", "ext_type_22"],
        columns=_Z_multiindex,
        dtype=("float64"),
    )

    F_Y_two = pd.DataFrame(
        data=[[50, 10], [100, 20]],
        index=["ext_type_21", "ext_type_22"],
        columns=_Y_multiindex,
        dtype=("float64"),
    )

    IO_object.extensions_one = Extension(
        name="extensions_one",
        F=F_one,
        F_Y=F_Y_one,
    )
    IO_object.extensions_two = Extension(
        name="extensions_two",
        F=F_two,
        F_Y=F_Y_two,
    )

    return IO_object


def test_hem_extraction(td_small_MRIO):
    """Test the extraction of HEM data from a small MRIO."""
    HEM_object = HEM(
        IOSystem=None,
        Y=td_small_MRIO.Y,
        A=td_small_MRIO.A,
        x=td_small_MRIO.x,
        L=td_small_MRIO.L,
        IOSystem_meta=None,
        save_path=None,
    )
    HEM_object.make_extraction(
        regions=["reg1"], sectors=["sector1", "sector2"], extraction_type="1.2", multipliers=True
    )
    pdt.assert_series_equal(
        left=td_small_MRIO.x.loc[HEM_object.index_extraction, "indout"],
        right=HEM_object.production.sum(axis=1).rename("indout"),
    )


def test_hem_extraction_impacts(td_small_MRIO):
    """Test the extraction of HEM data from a small MRIO."""
    HEM_object = HEM(
        IOSystem=None,
        Y=td_small_MRIO.Y,
        A=td_small_MRIO.A,
        x=td_small_MRIO.x,
        L=td_small_MRIO.L,
        IOSystem_meta=None,
        save_path=None,
    )
    HEM_object.make_extraction(
        regions=["reg1"], sectors=["sector1", "sector2"], extraction_type="1.2", multipliers=True
    )
    intensities = calc_S(td_small_MRIO.extensions_one.F, td_small_MRIO.x)
    HEM_object.calculate_impacts(intensities)

    pdt.assert_series_equal(
        left=td_small_MRIO.extensions_one.F.loc[:, HEM_object.index_extraction].sum(axis=1),
        right=HEM_object.impact_production.sum(axis=1),
    )


def test_hem_io_system_minimum(td_small_MRIO):
    """Test the HEM calculation with minimum parameters."""
    IO_object = td_small_MRIO
    IO_object.calc_system()
    IO_object.apply_HEM(
        regions=["reg1"],
        sectors=["sector1", "sector2"],
        extraction_type="1.2",
        multipliers=False,
        downstream_allocation_matrix="A12",
        save_extraction=False,
        save_path=None,
        calculate_impacts=False,
        extension="all",
        specific_impact=None,
        save_impacts=False,
        save_core_IO=False,
        save_details=False,
        return_results=False,
    )


def test_hem_io_system_multipliers(td_small_MRIO):
    """Test the HEM calculation with multipliers."""
    IO_object = td_small_MRIO
    IO_object.calc_system()
    IO_object.apply_HEM(
        regions=["reg1"],
        sectors=["sector1", "sector2"],
        extraction_type="1.2",
        multipliers=True,
        downstream_allocation_matrix="A12",
        save_extraction=False,
        save_path=None,
        calculate_impacts=True,
        extension="all",
        specific_impact=None,
        save_impacts=False,
        save_core_IO=False,
        save_details=False,
        return_results=False,
    )


def test_hem_io_system_impact(td_small_MRIO):
    """Test the HEM calculation with impact calculation."""
    IO_object = td_small_MRIO
    IO_object.calc_system()
    IO_object.apply_HEM(
        regions=["reg1"],
        sectors=["sector1", "sector2"],
        extraction_type="1.2",
        multipliers=False,
        downstream_allocation_matrix="A12",
        save_extraction=False,
        save_path=None,
        calculate_impacts=True,
        extension="all",
        specific_impact=None,
        save_impacts=False,
        save_core_IO=False,
        save_details=False,
        return_results=False,
    )


def test_hem_io_system_impact_multipliers(td_small_MRIO):
    """Test the HEM calculation with impact calculation and multipliers."""
    IO_object = td_small_MRIO
    IO_object.calc_system()
    IO_object.apply_HEM(
        regions=["reg1"],
        sectors=["sector1", "sector2"],
        extraction_type="1.2",
        multipliers=True,
        downstream_allocation_matrix="A12",
        save_extraction=False,
        save_path=None,
        calculate_impacts=True,
        extension="all",
        specific_impact=None,
        save_impacts=False,
        save_core_IO=False,
        save_details=False,
        return_results=False,
    )


def test_hem_io_system_impact_all_specific(td_small_MRIO):
    """Test the HEM calculation with impact calculation and specific impact."""
    IO_object = td_small_MRIO
    IO_object.calc_system()
    with pytest.raises(ValueError, match="If specific_impact is given, extension must not be 'all'."):
        IO_object.apply_HEM(
            regions=["reg1"],
            sectors=["sector1", "sector2"],
            extraction_type="1.2",
            multipliers=False,
            downstream_allocation_matrix="A12",
            save_extraction=False,
            save_path=None,
            calculate_impacts=True,
            extension="all",
            specific_impact="ext_type_11",
            save_impacts=False,
            save_core_IO=False,
            save_details=False,
            return_results=False,
        )


def test_hem_io_system_extension_specific(td_small_MRIO):
    """Test the HEM calculation with impact account and specific impact."""
    IO_object = td_small_MRIO
    IO_object.calc_system()
    IO_object.apply_HEM(
        regions=["reg1"],
        sectors=["sector1", "sector2"],
        extraction_type="1.2",
        multipliers=False,
        downstream_allocation_matrix="A12",
        save_extraction=False,
        save_path=None,
        calculate_impacts=True,
        extension="extensions_one",
        specific_impact="ext_type_11",
        save_impacts=False,
        save_core_IO=False,
        save_details=False,
        return_results=False,
    )


def test_hem_io_system_extension(td_small_MRIO):
    """Test the HEM calculation with impact account."""
    IO_object = td_small_MRIO
    IO_object.calc_system()
    IO_object.apply_HEM(
        regions=["reg1"],
        sectors=["sector1", "sector2"],
        extraction_type="1.2",
        multipliers=False,
        downstream_allocation_matrix="A12",
        save_extraction=False,
        save_path=None,
        calculate_impacts=True,
        extension="extensions_one",
        specific_impact=None,
        save_impacts=False,
        save_core_IO=False,
        save_details=False,
        return_results=False,
    )


def test_hem_io_system_L12_allocation(td_small_MRIO):
    """Test the HEM calculation with L12 allocation."""
    IO_object = td_small_MRIO
    IO_object.calc_system()
    IO_object.apply_HEM(
        regions=["reg1"],
        sectors=["sector1", "sector2"],
        extraction_type="1.2",
        multipliers=False,
        downstream_allocation_matrix="L12",
        save_extraction=False,
        save_path=None,
        calculate_impacts=False,
        extension="all",
        specific_impact=None,
        save_impacts=False,
        save_core_IO=False,
        save_details=False,
        return_results=False,
    )


def test_hem_io_system_one_region(td_small_MRIO):
    """Test the HEM calculation with one region."""
    IO_object = td_small_MRIO
    IO_object.calc_system()
    IO_object.apply_HEM(
        regions=["reg1"],
        sectors=None,
        extraction_type="1.2",
        multipliers=False,
        downstream_allocation_matrix="A12",
        save_extraction=False,
        save_path=None,
        calculate_impacts=False,
        extension="all",
        specific_impact=None,
        save_impacts=False,
        save_core_IO=False,
        save_details=False,
        return_results=False,
    )


def test_hem_io_system_one_sector(td_small_MRIO):
    """Test the HEM calculation with one sector."""
    IO_object = td_small_MRIO
    IO_object.calc_system()
    IO_object.apply_HEM(
        regions=None,
        sectors=["sector1"],
        extraction_type="1.2",
        multipliers=False,
        downstream_allocation_matrix="A12",
        save_extraction=False,
        save_path=None,
        calculate_impacts=False,
        extension="all",
        specific_impact=None,
        save_impacts=False,
        save_core_IO=False,
        save_details=False,
        return_results=False,
    )


def test_hem_io_system_save_all(save_path="./tests/hem_save_test_all", cleanup=False):
    """Test the HEM calculation with all save options."""
    IO_object = pymrio.load_test()
    extract_regions = [IO_object.regions[0]]
    extract_sectors = list(IO_object.sectors[:2])
    IO_object.calc_system()
    IO_object.apply_HEM(
        regions=extract_regions,
        sectors=extract_sectors,
        extraction_type="1.2",
        multipliers=True,
        downstream_allocation_matrix="A12",
        save_extraction=True,
        save_path=save_path,
        calculate_impacts=True,
        extension="all",
        specific_impact=None,
        save_impacts=True,
        save_core_IO=True,
        save_details=True,
        return_results=False,
    )
    if cleanup:
        shutil.rmtree(save_path)


def test_hem_io_system_save_specific(save_path="./tests/hem_save_test_specific", cleanup=True):
    """Test the HEM calculation with specific save options."""
    IO_object = pymrio.load_test()
    extract_regions = [IO_object.regions[0]]
    extract_sectors = list(IO_object.sectors[:2])
    extension = list(IO_object.get_extensions())[0]
    specific_impact = [list(IO_object.get_extensions(data=True))[0].get_index()[0]]
    IO_object.calc_system()
    IO_object.apply_HEM(
        regions=extract_regions,
        sectors=extract_sectors,
        extraction_type="1.2",
        multipliers=True,
        downstream_allocation_matrix="A12",
        save_extraction=True,
        save_path=save_path,
        calculate_impacts=True,
        extension=extension,
        specific_impact=specific_impact,
        save_impacts=True,
        save_core_IO=True,
        save_details=True,
        return_results=False,
    )
    if cleanup:
        shutil.rmtree(save_path)

def test_hem_load(save_path="./tests/hem_load_test", cleanup=True):
    """Test the HEM calculation with all save options."""
    IO_object = pymrio.load_test()
    extract_regions = [IO_object.regions[0]]
    extract_sectors = list(IO_object.sectors[:2])
    IO_object.calc_system()
    IO_object.apply_HEM(
        regions=extract_regions,
        sectors=extract_sectors,
        extraction_type="1.2",
        multipliers=True,
        downstream_allocation_matrix="A12",
        save_extraction=True,
        save_path=save_path,
        calculate_impacts=True,
        extension="all",
        specific_impact=None,
        save_impacts=True,
        save_core_IO=True,
        save_details=True,
        return_results=False,
    )

    HEM_extraction = load_extraction(
        extraction_path=f"{save_path}/{IO_object.regions[0]}",
        load_multipliers=True,
        load_core=True,
        load_details=True,
    )

    if cleanup:
        shutil.rmtree(save_path)

def test_hem_load_calculate(save_path="./tests/hem_load_test", cleanup=True):
    """Test the HEM calculation with all save options."""
    IO_object = pymrio.load_test()
    extract_regions = [IO_object.regions[0]]
    extract_sectors = list(IO_object.sectors[:2])
    IO_object.calc_system()
    HEM_initial = IO_object.apply_HEM(
        regions=extract_regions,
        sectors=extract_sectors,
        extraction_type="1.2",
        multipliers=True,
        downstream_allocation_matrix="A12",
        save_extraction=True,
        save_path=save_path,
        calculate_impacts=True,
        extension="all",
        specific_impact=None,
        save_impacts=True,
        save_core_IO=True,
        save_details=True,
        return_results=True,
    )

    HEM_object = load_extraction(
        extraction_path=HEM_initial[0].extraction_save_path,
        load_multipliers=True,
        load_core=True,
        load_details=True,
    )

    HEM_object.calculate_impacts(
        intensities=next(IO_object.get_extensions(data=True), None).S
    )

    if cleanup:
        shutil.rmtree(save_path)

def test_hem_load_calculate_save(save_path="./tests/hem_load_calculate_save", cleanup=True):
    """Test the HEM calculation with all save options."""
    IO_object = pymrio.load_test()
    extract_regions = [IO_object.regions[1]]
    extract_sectors = list(IO_object.sectors[:2])
    IO_object.calc_system()
    HEM_initial = IO_object.apply_HEM(
        regions=extract_regions,
        sectors=extract_sectors,
        extraction_type="1.2",
        multipliers=True,
        downstream_allocation_matrix="A12",
        save_extraction=True,
        save_path=save_path,
        calculate_impacts=False,
        extension="all",
        specific_impact=None,
        save_impacts=False,
        save_core_IO=True,
        save_details=True,
        return_results=True,
    )[0]

    HEM_object = load_extraction(
        extraction_path=HEM_initial.extraction_save_path,
        load_multipliers=True,
        load_core=True,
        load_details=True,
    )

    extension = next(IO_object.get_extensions(data=True), None)
    extension_name = next(IO_object.get_extensions(data=False), None)
    intensities = calc_S(
        extension.F, IO_object.x
    )

    HEM_object.calculate_impacts(
        intensities=intensities
    )

    HEM_object.save_impacts(
        extension=extension_name,
        specific_impact=None,
    )

    if cleanup:
        shutil.rmtree(save_path)
