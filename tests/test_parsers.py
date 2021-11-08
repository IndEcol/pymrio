""" Tests the parsing of different MRIOs """

import os
import sys

import numpy as np
import pandas.testing as pdt
import pytest

try:
    testpath = os.path.dirname(os.path.abspath(__file__))
except NameError:
    testpath = os.getcwd()  # easy run in interpreter
    if "tests" not in testpath:
        testpath = os.path.join(testpath, "tests")


sys.path.append(os.path.join(testpath, ".."))

import pymrio  # noqa


@pytest.fixture()
def fix_testmrio_calc():
    """Single point to load the test mrio"""

    class TestMRIO:
        testmrio = pymrio.load_test().calc_all()

    return TestMRIO


def test_parse_exio1(fix_testmrio_calc):

    exio1_mockpath = os.path.join(testpath, "mock_mrios", "exio1_mock")

    test_mrio = fix_testmrio_calc.testmrio

    exio1 = pymrio.parse_exiobase1(exio1_mockpath)

    exio1.calc_all()

    assert test_mrio.emissions.S.iloc[1, 1] == pytest.approx(
        exio1.emissions.S.iloc[1, 1]
    )

    assert test_mrio.emissions.D_cba.iloc[0, 5] == pytest.approx(
        exio1.emissions.D_cba.iloc[0, 5]
    )

    assert exio1.get_regions()[0] == "reg1"

    with pytest.raises(pymrio.ParserError):
        _ = pymrio.parse_exiobase1("foo")


def test_parse_exio2(fix_testmrio_calc):
    exio2_mockpath = os.path.join(
        testpath,
        "mock_mrios",
        "exio2_mock",
        "mrIOT_PxP_ita_coefficient_version2.2.2.zip",
    )

    test_mrio = fix_testmrio_calc.testmrio

    exio2 = pymrio.parse_exiobase2(exio2_mockpath, popvector=None)
    exio2.calc_all()

    assert test_mrio.emissions.S.iloc[1, 1] == pytest.approx(
        exio2.emissions.S.iloc[1, 1]
    )

    assert test_mrio.emissions.D_cba.iloc[0, 5] == pytest.approx(
        exio2.emissions.D_cba.iloc[0, 5]
    )

    pdt.assert_series_equal(
        exio2.impact.D_cba.loc["total emissions"],
        test_mrio.emissions.D_cba.sum(axis=0),
        check_names=False,
    )

    assert exio2.get_regions()[0] == "reg1"

    with pytest.raises(pymrio.ParserError):
        _ = pymrio.parse_exiobase2("foo")

    with pytest.raises(pymrio.ParserError):
        _ = pymrio.parse_exiobase2("foo.zip")


def test_parse_exio3(fix_testmrio_calc):
    exio3_mockpath = os.path.join(testpath, "mock_mrios", "exio3_mock")

    test_mrio = fix_testmrio_calc.testmrio

    exio3 = pymrio.parse_exiobase3(exio3_mockpath)
    exio3.calc_all()

    assert np.allclose(exio3.A, test_mrio.A)
    assert np.allclose(exio3.satellite.D_cba, test_mrio.emissions.D_cba)

    # Test the renaming of the regions - depends on the correct pseudo
    # naming in the mock mrio
    assert list(exio3.get_regions()) == ["AU", "BR", "FI", "FR", "KR", "WF"]


def test_parse_exio_ext():
    ext_mockpath = os.path.join(testpath, "mock_mrios", "exio_ext_mock")

    col5 = os.path.join(ext_mockpath, "ext_5col.txt")
    col3 = os.path.join(ext_mockpath, "ext_3col.txt")
    col2 = os.path.join(ext_mockpath, "ext_2col.txt")
    col1 = os.path.join(ext_mockpath, "ext_1col.txt")

    ext5 = pymrio.parse_exio12_ext(
        col5, index_col=5, name="col5", sep="\t", drop_compartment=True
    )
    ext3 = pymrio.parse_exio12_ext(
        col3, index_col=3, name="col3", sep="\t", drop_compartment=True
    )
    ext2 = pymrio.parse_exio12_ext(
        col2, index_col=2, name="col2", sep="\t", drop_compartment=True
    )
    ext1 = pymrio.parse_exio12_ext(
        col1, index_col=1, name="col1", sep="\t", drop_compartment=True
    )
    ext5_wcmp = pymrio.parse_exio12_ext(
        col5, index_col=5, name="col5", sep="\t", drop_compartment=False
    )
    ext3_wcmp = pymrio.parse_exio12_ext(
        col3, index_col=3, name="col3", sep="\t", drop_compartment=False
    )
    ext2_wcmp = pymrio.parse_exio12_ext(
        col2, index_col=2, name="col2", sep="\t", drop_compartment=False
    )
    ext1_wcmp = pymrio.parse_exio12_ext(
        col1, index_col=1, name="col1", sep="\t", drop_compartment=False
    )

    assert np.allclose(ext5.F, ext3.F, ext2.F, ext1.F, ext5_wcmp.F)

    assert ext5.F.iloc[1, 1] == 102
    assert ext5.F.iloc[-1, -1] == 148

    assert ext2.name == "col2"

    assert ext1.unit is None
    assert ext1_wcmp.unit is None
    assert ext5_wcmp.unit.iloc[0, 0] == "kg"
    assert ext3.unit.iloc[1, 0] == "kg"

    assert ext5.F.index.name == "stressor"
    assert list(ext5_wcmp.F.index.names) == ["stressor", "compartment"]
    assert list(ext3_wcmp.F.index.names) == ["stressor", "compartment"]
    assert ext2_wcmp.F.index.name == "stressor"


@pytest.mark.filterwarnings("ignore:Extension data")
def test_parse_wiod():
    wiod_mockpath = os.path.join(testpath, "mock_mrios", "wiod_mock")
    ww_path = pymrio.parse_wiod(path=wiod_mockpath, year=2009)
    ww_file = pymrio.parse_wiod(
        path=os.path.join(wiod_mockpath, "wiot09_row_sep12.xlsx")
    )

    ww_path.calc_all()
    ww_file.calc_all()

    pdt.assert_frame_equal(ww_path.Z, ww_file.Z)
    pdt.assert_frame_equal(ww_path.lan.D_cba, ww_file.lan.D_cba)
    pdt.assert_frame_equal(ww_path.SEA.D_pba, ww_file.SEA.D_pba)
    pdt.assert_frame_equal(ww_path.AIR.D_imp, ww_file.AIR.D_imp)

    assert ww_file.AIR.F_Y.loc["NOX", ("LUX", "c37")] == 999
    assert ww_file.SEA.F.loc["EMP", ("RoW", "19")] == 0


def test_oecd_2016():

    oecd_mockpath = os.path.join(testpath, "mock_mrios", "oecd_mock")
    oecd_IO_file = os.path.join(oecd_mockpath, "ICIO2016_2003.csv")

    oecd_file = pymrio.parse_oecd(path=oecd_IO_file)
    oecd_year = pymrio.parse_oecd(path=oecd_mockpath, year=2003)

    assert oecd_file == oecd_year

    with pytest.raises(FileNotFoundError):
        _ = pymrio.parse_oecd(oecd_mockpath, year=1077)
    with pytest.raises(pymrio.ParserError):
        _ = pymrio.parse_oecd(oecd_mockpath)

    oecd = oecd_file
    oecd.calc_all()

    # Test standard values
    assert np.allclose(
        oecd.Z.loc[("AUS", "C01T05AGR"), ("AUS", "C01T05AGR")], 23697.221
    )
    assert np.allclose(oecd.Z.loc[("NZL", "C23PET"), ("AUS", "C20WOD")], 684.49784)
    assert np.allclose(oecd.Y.loc[("NZL", "C23PET"), ("PER", "DIRP")], 14822221.0)

    # Test aggregation
    assert "CHN" in oecd.get_regions()
    assert "CN1" not in oecd.get_regions()
    assert "CN2" not in oecd.get_regions()

    assert oecd.Z.shape == (32, 32)

    assert np.allclose(
        oecd.Z.loc[("CHN", "C01T05AGR"), ("AUS", "C15T16FOD")], 6932.1858
    )
    assert np.allclose(
        oecd.Z.loc[("CHN", "C01T05AGR"), ("AUS", "C15T16FOD")], 6932.1858
    )
    assert np.allclose(oecd.Y.loc[("CHN", "C23PET"), ("NZL", "HFCE")], 24074818)
    assert np.allclose(
        oecd.factor_inputs.F.loc["VA+TAXSUB", ("CHN", "C20WOD")], 569612.84
    )


def test_oecd_2018():
    oecd_mockpath = os.path.join(testpath, "mock_mrios", "oecd_mock")
    oecd_IO_csv = os.path.join(oecd_mockpath, "ICIO2018_2010.CSV")
    oecd_IO_zip = os.path.join(oecd_mockpath, "ICIO2018_2010.zip")

    oecd_csv = pymrio.parse_oecd(path=oecd_IO_csv)
    oecd_zip = pymrio.parse_oecd(path=oecd_IO_zip)
    oecd_year = pymrio.parse_oecd(path=oecd_mockpath, year=2010)

    assert oecd_csv == oecd_zip == oecd_year

    oecd = oecd_zip

    # Test aggregation
    assert "MEX" in oecd.get_regions()
    assert "MX1" not in oecd.get_regions()

    assert np.allclose(oecd.Z.loc[("BEL", "16"), ("AUS", "05T06")], 150.89421)
    assert np.allclose(oecd.Y.loc[("BRA", "09"), ("COL", "GGFC")], 11211977)
    assert np.allclose(oecd.factor_inputs.F.loc["VALU", ("MEX", "01T03")], 284552.21)
    assert np.allclose(
        oecd.factor_inputs.F.loc["MEX_TAXSUB", ("BEL", "16")], 1.66161232097811
    )


def test_parse_eora26(fix_testmrio_calc):
    eora_mockpath = os.path.join(testpath, "mock_mrios", "eora26_mock")

    test_mrio = fix_testmrio_calc.testmrio

    eora_short = pymrio.parse_eora26(eora_mockpath, year=2010)
    eora_full = pymrio.parse_eora26(eora_mockpath, year=2010, country_names="full")

    eora_short.calc_all()

    assert test_mrio.emissions.D_cba.iloc[1, 1] == pytest.approx(
        eora_short.Q.D_cba.iloc[1, 1]
    )

    assert eora_short.get_regions()[0] == "reg1"
    assert eora_full.get_regions()[0] == "Region 1"

    with pytest.raises(pymrio.ParserError):
        _ = pymrio.parse_eora26(eora_mockpath, year=2010, country_names="bogus")


if __name__ == "__main__":
    test_oecd_2016()
