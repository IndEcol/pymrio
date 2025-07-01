"""Testing core functionality of pymrio."""

import os
import sys
from pathlib import Path

import numpy.testing as npt
import pandas as pd
import pandas.testing as pdt
import pytest

TESTPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(TESTPATH, ".."))

import pymrio  # noqa
from pymrio.core.constants import PYMRIO_PATH  # noqa


@pytest.fixture()
def fix_testmrio():
    """Single point to load the test mrio."""

    class TestMRIO:
        testmrio = pymrio.load_test()
        sectors = [
            "food",
            "mining",
            "manufactoring",
            "electricity",
            "construction",
            "trade",
            "transport",
            "other",
        ]
        regions = ["reg1", "reg2", "reg3", "reg4", "reg5", "reg6"]

        Y_cat = [
            "Final consumption expenditure by households",
            "Final consumption expenditure by non-profit organisations serving households (NPISH)",
            "Final consumption expenditure by government",
            "Gross fixed capital formation",
            "Changes in inventories",
            "Changes in valuables",
            "Export",
        ]

    return TestMRIO


def test_copy(fix_testmrio):
    """Testing the deep copy functionality + naming."""
    tt = fix_testmrio.testmrio
    tt_copy = tt.copy()
    assert tt_copy.name == tt.name + "_copy"
    assert all(tt_copy.Z == tt.Z)
    assert all(tt_copy.emissions.F == tt.emissions.F)
    tt_copy.emissions.F = tt_copy.emissions.F + 2
    tt_copy.Z = tt_copy.Z + 2
    assert all(tt_copy.Z != tt.Z)
    assert all(tt_copy.emissions.F != tt.emissions.F)
    tt_new = tt.copy("new")
    assert tt_new.name == "new"
    e_new = tt.emissions.copy("new")
    assert e_new.name == "new"


def test_get_gross_trade(fix_testmrio):
    """Test gross_trade function."""
    tt = fix_testmrio.testmrio
    gross_trade = tt.get_gross_trade()
    flows = gross_trade.bilat_flows
    totals = gross_trade.totals

    reg2mining_exports = (
        tt.Z.loc[("reg2", "mining"), :].sum()
        - tt.Z.loc[("reg2", "mining"), "reg2"].sum()
        + tt.Y.loc[("reg2", "mining"), :].sum()
        - tt.Y.loc[("reg2", "mining"), "reg2"].sum()
    )

    assert reg2mining_exports == pytest.approx(totals.exports.loc["reg2", "mining"])

    for reg in tt.get_regions():
        assert flows.loc[reg, reg].sum().sum() == 0

    reg3trade_imports_from_reg2 = tt.Z.loc[("reg2", "trade"), "reg3"].sum() + tt.Y.loc[("reg2", "trade"), "reg3"].sum()
    assert reg3trade_imports_from_reg2 == pytest.approx(flows.loc[("reg2", "trade"), "reg3"])


@pytest.mark.parametrize(
    "names, data, instance_names, result",
    [
        (["Emissions"], False, False, ["Emissions"]),
        (["Emissions"], False, True, ["emissions"]),
        (["Factor Inputs"], False, True, ["factor_inputs"]),
        (None, False, True, ["factor_inputs", "emissions"]),
        (None, False, True, ["emissions", "factor_inputs"]),
        (None, False, False, ["Emissions", "Factor Inputs"]),
        (["Emissions", "Factor Inputs"], False, False, ["Emissions", "Factor Inputs"]),
        (["Emissions", "Factor Inputs"], False, True, ["emissions", "factor_inputs"]),
        (["Emissions", "factor_inputs"], False, True, ["emissions", "factor_inputs"]),
        (["emissions", "factor_inputs"], False, False, ["Emissions", "Factor Inputs"]),
        (
            ["emissions", "factor_inputs", "emissions"],
            False,
            False,
            ["Emissions", "Factor Inputs", "Emissions"],
        ),
    ],
)
def test_get_extensions(fix_testmrio, names, data, instance_names, result):
    """Testing getting extensions."""
    tt = fix_testmrio.testmrio
    exts = list(tt.get_extensions(names=names, data=data, instance_names=instance_names))
    assert sorted(exts) == sorted(result)


def test_get_extension_raise(fix_testmrio):
    """Testing raising exceptions for wrong extension request."""
    tt = fix_testmrio.testmrio
    with pytest.raises(ValueError):
        list(tt.get_extensions(names=["emissions", "foo"], data=False, instance_names=True))


def test_get_index(fix_testmrio):
    """Testing the different options for get_index in core.mriosystem."""
    tt = fix_testmrio.testmrio
    assert all(tt.emissions.F.index == tt.emissions.get_index(as_dict=False))

    F_dict = {ki: ki for ki in tt.emissions.F.index}
    idx_dict = {ki: ki for ki in tt.emissions.get_index(as_dict=True)}
    assert F_dict == idx_dict

    pat1 = {("emis.*", "air"): ("emission alternative", "air")}
    pat1index = tt.emissions.get_index(as_dict=True, grouping_pattern=pat1)
    assert pat1index[tt.emissions.F.index[0]] == list(pat1.values())[0]
    assert pat1index[tt.emissions.F.index[1]] == tt.emissions.F.index[1]

    pat2 = {("emis.*", ".*"): "r"}

    pat2index = tt.emissions.get_index(as_dict=True, grouping_pattern=pat2)
    assert all(v == "r" for v in pat2index.values())

    # test one level index

    # pat_single_tpl = {('Value Added',): 'va'}
    pat_single_str = {"Value Added": "va"}
    pat_single_index = tt.factor_inputs.get_index(as_dict=True, grouping_pattern=pat_single_str)
    assert pat_single_str == pat_single_index


def test_set_index(fix_testmrio):
    """Test setting index across extensions."""
    tt = fix_testmrio.testmrio
    new_index = ["a", "b"]
    tt.emissions.set_index(new_index)
    assert tt.emissions.get_index()[0] == new_index[0]
    assert tt.emissions.get_index()[1] == new_index[1]


def test_properties(fix_testmrio):
    """Test the convinience properties of the MRIO system."""
    tt = fix_testmrio.testmrio
    assert all(tt.sectors == tt.get_sectors())
    assert all(tt.regions == tt.get_regions())
    assert all(tt.emissions.sectors == tt.get_sectors())
    assert all(tt.emissions.regions == tt.get_regions())
    assert all(tt.Y_categories == tt.get_Y_categories())
    assert all(tt.emissions.Y_categories == tt.get_Y_categories())
    assert all(tt.emissions.rows == tt.emissions.get_rows())
    assert tt.DataFrames == list(tt.get_DataFrame(data=False))
    assert tt.factor_inputs.DataFrames == list(tt.factor_inputs.get_DataFrame(data=False))
    assert tt.extensions == list(tt.get_extensions(data=False, instance_names=False))
    assert tt.extensions_instance_names == list(tt.get_extensions(data=False, instance_names=True))


def test_get_sectors(fix_testmrio):
    """Test getting sectors."""
    assert list(fix_testmrio.testmrio.get_sectors()) == fix_testmrio.sectors
    assert (
        fix_testmrio.testmrio.get_sectors(["construction", "food", "a"])[fix_testmrio.sectors.index("construction")]
        == "construction"
    )
    assert (
        fix_testmrio.testmrio.get_sectors(["construction", "food", "a"])[fix_testmrio.sectors.index("food")] == "food"
    )
    assert fix_testmrio.testmrio.get_sectors("food") == [e if e == "food" else None for e in fix_testmrio.sectors]
    assert (
        fix_testmrio.testmrio.get_sectors(["construction", "food", "a"])[1] == None  # noqa
    )


def test_get_regions(fix_testmrio):
    """Test getting regions."""
    assert list(fix_testmrio.testmrio.get_regions()) == fix_testmrio.regions

    assert fix_testmrio.testmrio.get_regions(fix_testmrio.regions[:]) == fix_testmrio.regions

    assert fix_testmrio.testmrio.get_regions("reg4") == [e if e == "reg4" else None for e in fix_testmrio.regions]


def test_get_Y_categories(fix_testmrio):
    """Test getting finald demand categories."""
    assert list(fix_testmrio.testmrio.get_Y_categories()) == fix_testmrio.Y_cat

    assert fix_testmrio.testmrio.get_Y_categories(fix_testmrio.Y_cat[:]) == fix_testmrio.Y_cat

    assert fix_testmrio.testmrio.get_Y_categories("Export") == [
        e if e == "Export" else None for e in fix_testmrio.Y_cat
    ]


def test_rename_regions(fix_testmrio):
    """Test renaming."""
    new_reg_name = "New Region 1"
    new_reg_list = ["a1", "a2", "a3", "a4", "a5", "a6"]
    fix_testmrio.testmrio.rename_regions({"reg1": new_reg_name})
    assert fix_testmrio.testmrio.get_regions()[0] == new_reg_name
    fix_testmrio.testmrio.rename_regions(new_reg_list)
    assert fix_testmrio.testmrio.get_regions()[0] == new_reg_list[0]
    assert fix_testmrio.testmrio.get_regions()[2] == new_reg_list[2]


def test_rename_random_sectors(fix_testmrio):
    """Test renaming sectors."""
    new_sec_name = "yummy"
    new_sec_list = ["s1", "s2", "s3", "s4", "s5", "s6"]
    fix_testmrio.testmrio.rename_sectors({"food": new_sec_name})
    assert fix_testmrio.testmrio.get_sectors()[0] == new_sec_name
    fix_testmrio.testmrio.rename_sectors(new_sec_list)
    assert fix_testmrio.testmrio.get_sectors()[0] == new_sec_list[0]
    assert fix_testmrio.testmrio.get_sectors()[4] == new_sec_list[4]


def test_rename_sector_with_io_info(fix_testmrio):
    """Test renaming with io info."""
    with pytest.raises(ValueError):
        _ = pymrio.get_classification("foo")

    classdata = pymrio.get_classification("test")
    corr_dict = classdata.get_sector_dict(orig="TestMrioName", new="TestMrioCode")
    corr_dict2 = classdata.get_sector_dict(orig=fix_testmrio.testmrio.get_sectors(), new="TestMrioCode")

    assert corr_dict == corr_dict2

    fix_testmrio.testmrio.rename_sectors(corr_dict)

    assert fix_testmrio.testmrio.get_sectors()[3] == classdata.sectors.iloc[3, :].loc["TestMrioCode"]


def test_rename_Ycat(fix_testmrio):
    """Test renaming final demand categories."""
    new_cat_name = "HouseCons"
    new_cat_list = ["y1", "y2", "y3", "y4", "y5", "y6", "y7"]
    fix_testmrio.testmrio.rename_Y_categories({fix_testmrio.Y_cat[0]: new_cat_name})
    assert fix_testmrio.testmrio.get_Y_categories()[0] == new_cat_name
    fix_testmrio.testmrio.rename_Y_categories(new_cat_list)
    assert fix_testmrio.testmrio.get_Y_categories()[0] == new_cat_list[0]
    assert fix_testmrio.testmrio.get_Y_categories()[-1] == new_cat_list[-1]


def test_copy_and_extensions(fix_testmrio):
    """Test copy extensions."""
    tcp = fix_testmrio.testmrio.copy()
    tcp.remove_extension("Emissions")
    assert len(list(tcp.get_extensions())) == 1
    with pytest.raises(TypeError):
        tcp.remove_extension()
    tcnew = fix_testmrio.testmrio.copy()
    tcnew.remove_extension(tcnew.get_extensions())
    assert len(list(tcnew.get_extensions())) == 0


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_extract(fix_testmrio):
    """Test extracting data."""
    tt = fix_testmrio.testmrio.copy().calc_all()

    all_index = tt.emissions.get_index()
    new_all = tt.emissions.extract(all_index, return_type="new_all")

    assert new_all.name == "new_all"
    for df in tt.emissions.get_DataFrame():
        assert df in new_all.get_DataFrame()

    name_check = tt.emissions.extract(all_index, return_type="ext")
    assert name_check.name == "Emissions_extracted"
    for df in tt.emissions.get_DataFrame():
        assert df in name_check.get_DataFrame()

    id_air = tt.emissions.match(compartment="air")
    new_air = tt.emissions.extract(index=id_air, return_type="new_air")

    assert "F" in new_air.get_DataFrame()
    assert "S" in new_air.get_DataFrame()
    assert "S_Y" in new_air.get_DataFrame()

    with_missing = tt.emissions.extract(index=id_air, dataframes=["F", "FOO"])
    assert "F" in with_missing
    assert "FOO" not in with_missing

    # Test for correct shape when extracting one row
    assert tt.factor_inputs.extract("Value Added", return_type="ext").F.index == tt.factor_inputs.get_rows()
    assert tt.factor_inputs.extract(("Value Added"), return_type="ext").F.index == tt.factor_inputs.get_rows()
    assert tt.factor_inputs.extract(["Value Added"], return_type="ext").F.index == tt.factor_inputs.get_rows()

    assert (
        tt.factor_inputs.extract(tt.factor_inputs.get_rows(), return_type="ext").F.index == tt.factor_inputs.get_rows()
    )
    pdt.assert_index_equal(
        tt.emissions.extract(tt.emissions.get_rows(), return_type="ext").F.index,
        tt.emissions.get_rows(),
    )
    assert tt.emissions.extract(tt.emissions.get_rows()[0], return_type="ext").F.index == tt.emissions.get_rows()[0]


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_extension_extract(fix_testmrio):
    """Test extracting extension data."""
    tt = fix_testmrio.testmrio

    match_air = tt.extension_match(find_all="air")

    dfa = tt.extension_extract(match_air, dataframes=["F", "F_Y"], include_empty=True)
    assert dfa["Factor Inputs"]["F"].shape[0] == 0

    exta = tt.extension_extract(match_air, dataframes=["F", "F_Y"], include_empty=True, return_type="extension")
    assert exta["Factor Inputs"].F.shape[0] == 0
    assert exta["Factor Inputs"].name == "Factor Inputs_extracted"
    assert exta["Emissions"].name == "Emissions_extracted"

    dfr = tt.extension_extract(match_air, dataframes=["F", "F_Y"], include_empty=False)
    extr = tt.extension_extract(
        match_air,
        dataframes=["F", "F_Y"],
        include_empty=False,
        return_type="ext",
    )
    assert dfr["Emissions"]["F"].index[0] == ("emission_type1", "air")
    assert extr["Emissions"].F.index[0] == ("emission_type1", "air")

    match_more = tt.extension_match(find_all="air|Value")
    tt.calc_all()
    dfm = tt.extension_extract(match_more, include_empty=True, return_type="new")
    assert dfm.name == "new"
    assert ("emission_type1", "air") in dfm.F.index
    assert ("Value Added") in dfm.F.index
    assert ("emission_type1", "air") in dfm.F_Y.index
    assert ("Value Added") in dfm.F_Y.index
    assert dfm.F_Y.loc["Value Added", :].sum().sum() == 0
    assert all(dfm.get_regions() == tt.get_regions())
    assert all(dfm.get_sectors() == tt.get_sectors())


def test_diag_stressor(fix_testmrio):
    """Test diagonalizing stressors."""
    stressor_name = ("emission_type1", "air")
    stressor_number = 0
    ext = fix_testmrio.testmrio.emissions
    dext_name = ext.diag_stressor(stressor_name)
    dext_number = ext.diag_stressor(stressor_number)
    pdt.assert_frame_equal(dext_name.F, dext_number.F)

    assert dext_name.F.iloc[0, 0] == ext.F.iloc[stressor_number, 0]
    assert dext_name.F.iloc[1, 1] == ext.F.iloc[stressor_number, 1]
    assert sum(dext_name.F.iloc[0, 1:-1]) == 0
    assert sum(dext_name.F.iloc[1:-1, 0]) == 0


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_characterize_extension_general(fix_testmrio):
    """Testing 'standard' characterisation.

    - general (non regional specific) characterisation factors
    - testing unit fix
    - testing missing data
    """
    factors = pd.read_csv(
        Path(PYMRIO_PATH["test_mrio"] / Path("concordance") / "emissions_charact.tsv"),
        sep="\t",
    )

    t_uncalc = fix_testmrio.testmrio
    t_calc = fix_testmrio.testmrio.calc_all()
    uncalc_name = "emissions_charact_uncalc"
    ex_uncalc = t_uncalc.emissions.characterize(factors, name=uncalc_name).extension
    ex_calc = t_uncalc.emissions.characterize(factors).extension

    assert ex_uncalc.name == uncalc_name
    assert ex_calc.name == t_calc.emissions.name + "_characterized"

    # The test characterization matrix is all in t, the emissions in test are
    # all in kg
    assert ex_calc.unit.loc["total air emissions", "unit"] == "t"
    npt.assert_allclose(
        ex_uncalc.F.loc["total air emissions"].sum(),
        (t_calc.emissions.F.loc[("emission_type1", "air"), :] / 1000).sum(),
    )
    npt.assert_allclose(
        ex_calc.S.loc["total air emissions"].sum(),
        (t_calc.emissions.S.loc[("emission_type1", "air"), :] / 1000).sum(),
    )
    npt.assert_allclose(
        ex_calc.F_Y.loc["air water impact"].sum(),
        (
            (t_calc.emissions.F_Y.loc[("emission_type1", "air"), :] * 2 / 1000)
            + (t_calc.emissions.F_Y.loc[("emission_type2", "water"), :] * 1 / 1000)
        ).sum(),
    )
    npt.assert_allclose(
        ex_calc.S_Y.loc["air water impact"].sum(),
        (
            (t_calc.emissions.S_Y.loc[("emission_type1", "air"), :] * 2 / 1000)
            + (t_calc.emissions.S_Y.loc[("emission_type2", "water"), :] * 1 / 1000)
        ).sum(),
    )

    # check removal calculated results (important later for region specific agg)

    assert ex_calc.M is None
    assert ex_calc.D_cba is None
    assert ex_calc.D_imp is None
    t_calc.impacts = ex_calc
    t_calc.calc_all()
    pdt.assert_series_equal(
        t_calc.impacts.F.loc["total air emissions", :],
        t_calc.emissions.F.loc[("emission_type1", "air"), :] / 1000,
        check_names=False,
    )
    pdt.assert_series_equal(
        t_calc.impacts.S.loc["total air emissions", :],
        t_calc.emissions.S.loc[("emission_type1", "air"), :] / 1000,
        check_names=False,
    )

    with pytest.raises(ValueError):
        ex_error = t_uncalc.emissions.characterize(factors, characterization_factors_column="foo")
    with pytest.raises(ValueError):
        ex_error = t_uncalc.factor_inputs.characterize(  # noqa: F841
            factors, characterization_factors_column="foo"
        )

    # testing unit mismatch

    fac_mod_stressor_unit = factors.copy()
    # Changing one emission_type2 value and
    # report error for all due to non consitent units
    fac_mod_stressor_unit.loc[3, "stressor_unit"] = "g"

    incon_stressor_unit = t_calc.emissions.characterize(fac_mod_stressor_unit)
    assert incon_stressor_unit.extension is None
    assert incon_stressor_unit.validation.error_unit_stressor.any()

    fac_mod_stressor_unit.loc[:, "stressor_unit"] = "g"

    mis_stressor_unit = t_calc.emissions.characterize(fac_mod_stressor_unit)
    assert mis_stressor_unit.extension is None
    assert mis_stressor_unit.validation.error_unit_stressor.any()


def test_characterize_validation(fix_testmrio):
    """Validation of characterization factors sheet before usage."""
    factors_reg_spec = pd.read_csv(
        Path(PYMRIO_PATH["test_mrio"] / Path("concordance") / "emissions_charact_reg_spec.tsv"),
        sep="\t",
    )
    tmrio = fix_testmrio.testmrio
    rep_basic = tmrio.emissions.characterize(factors_reg_spec, only_validation=True).validation

    # Case 1: original factor sheet has more stressor data, should be reported
    assert all(rep_basic[rep_basic.stressor == "emission_type3"].error_missing_stressor)
    assert not any(rep_basic[rep_basic.stressor != "emission_type3"].error_missing_stressor)
    # rest should be fine
    assert not any(rep_basic.error_unit_impact)
    assert not any(rep_basic.error_unit_stressor)
    assert not any(rep_basic.error_missing_region)
    # Case 2: one region missing
    # removing one region from the data
    fac_mis_reg = factors_reg_spec.copy().loc[factors_reg_spec.region != "reg3"]
    rep_reg_miss = tmrio.emissions.characterize(fac_mis_reg, only_validation=True).validation
    assert all(rep_reg_miss[rep_reg_miss.stressor != "emission_type3"].error_missing_region)
    # as stressor 3 is not present, not a region missing error
    assert not any(rep_reg_miss[rep_reg_miss.stressor == "emission_type3"].error_missing_region)
    # other error still present
    assert all(rep_reg_miss[rep_reg_miss.stressor == "emission_type3"].error_missing_stressor)

    # Case 3: one additional region
    new_data = factors_reg_spec.iloc[[0]]
    new_data.loc[:, "region"] = "reg_new"
    fac_add_reg = factors_reg_spec.merge(new_data, how="outer")
    rep_add_reg = tmrio.emissions.characterize(fac_add_reg, only_validation=True).validation
    assert all(rep_add_reg[rep_add_reg.region == "reg_new"].error_missing_region)
    assert not any(rep_add_reg[rep_add_reg.region != "reg_new"].error_missing_region)

    # Case 4: Same error as in Case 1 in the non region specific factors file
    factors_no_reg = pd.read_csv(
        Path(PYMRIO_PATH["test_mrio"] / Path("concordance") / "emissions_charact.tsv"),
        sep="\t",
    )
    rep_basic_no_reg = tmrio.emissions.characterize(factors_no_reg, only_validation=True).validation
    assert all(rep_basic_no_reg[rep_basic_no_reg.stressor == "emission_type3"].error_missing_stressor)
    assert not any(rep_basic_no_reg[rep_basic_no_reg.stressor != "emission_type3"].error_missing_stressor)

    assert not any(rep_basic_no_reg.error_unit_impact)
    assert not any(rep_basic_no_reg.error_unit_stressor)

    # case 5: check if unit errors are reported specifically to the affected row
    fac_wrong_unit = factors_reg_spec.copy().loc[factors_reg_spec.region == "reg3"]
    fac_wrong_unit = factors_reg_spec.copy()
    fac_wrong_unit.loc[
        (fac_wrong_unit.region == "reg4") & (fac_wrong_unit.stressor == "emission_type1"),
        "stressor_unit",
    ] = "s"

    rep_wrong_unit = tmrio.emissions.characterize(fac_wrong_unit, only_validation=True).validation

    assert all(rep_wrong_unit[rep_wrong_unit.stressor_unit == "s"].loc[:, "error_unit_stressor"])
    assert not any(rep_wrong_unit[rep_wrong_unit.stressor_unit != "s"].loc[:, "error_unit_stressor"])

    charact_table_reg = factors_reg_spec.copy()
    charact_table_reg.loc[
        (charact_table_reg.region == "reg2") & (charact_table_reg.stressor == "emission_type2"),
        "region",
    ] = "reg_new"


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_characterize_extension_reg_spec(fix_testmrio):
    """Additional characterization test for region specific cases.

    Characterisation is first benchmarked against the general
    test_characterize_extension_general. The characterization
    matrix is the same, just with regional disaggregation.

    After that, new results are generated by modifying regional characterization.
    """
    factors_reg_spec = pd.read_csv(
        Path(PYMRIO_PATH["test_mrio"] / Path("concordance") / "emissions_charact_reg_spec.tsv"),
        sep="\t",
    )

    factors_no_reg = pd.read_csv(
        Path(PYMRIO_PATH["test_mrio"] / Path("concordance") / "emissions_charact.tsv"),
        sep="\t",
    )

    tmrio = fix_testmrio.testmrio

    # testing same result with regional specs
    ex_reg_spec = tmrio.emissions.characterize(factors_reg_spec).extension
    ex_no_reg = tmrio.emissions.characterize(factors_no_reg).extension

    pdt.assert_frame_equal(ex_no_reg.F, ex_reg_spec.F)
    pdt.assert_frame_equal(ex_no_reg.F_Y, ex_reg_spec.F_Y)
    pdt.assert_frame_equal(ex_no_reg.unit, ex_reg_spec.unit)

    # testing correct doubling of one region
    factors_reg_spec.loc[factors_reg_spec.region == "reg2", "factor"] = (
        factors_reg_spec.loc[factors_reg_spec.region == "reg2", "factor"] * 2
    )

    double = tmrio.emissions.characterize(factors_reg_spec).extension

    pdt.assert_frame_equal(double.F.reg2, ex_reg_spec.F.reg2 * 2)
    pdt.assert_frame_equal(double.F_Y.reg2, ex_reg_spec.F_Y.reg2 * 2)

    pdt.assert_frame_equal(double.F.reg6, ex_reg_spec.F.reg6)
    pdt.assert_frame_equal(double.F_Y.reg5, ex_reg_spec.F_Y.reg5)

    # testing that NaN are assumed 0
    factors_reg_spec.loc[factors_reg_spec.region == "reg2", "factor"] = pd.NA
    nnaa = tmrio.emissions.characterize(factors_reg_spec).extension

    assert nnaa.F.reg2.sum().sum() == 0
    assert nnaa.F_Y.reg2.sum().sum() == 0
    pdt.assert_frame_equal(nnaa.F.reg1, ex_reg_spec.F.reg1)
    pdt.assert_frame_equal(nnaa.F_Y.reg3, ex_reg_spec.F_Y.reg3)

    # testing complete missing are assumed 0
    fac_reg2_missing = factors_reg_spec.dropna()
    res_reg2_missing = tmrio.emissions.characterize(fac_reg2_missing)
    assert any(res_reg2_missing.validation.error_missing_region)
    pdt.assert_frame_equal(nnaa.F, res_reg2_missing.extension.F)
    pdt.assert_frame_equal(nnaa.F_Y, res_reg2_missing.extension.F_Y)

    # testing passing multiple impact columns

    fac_split = fac_reg2_missing.copy()
    fac_split.loc[:, "impact2"] = fac_split.loc[:, "impact"].str.split().str[-1]
    res_split = tmrio.emissions.characterize(fac_split, characterized_name_column=["impact", "impact2"])

    assert "impact" in res_split.validation.columns
    assert "impact2" in res_split.validation.columns
    assert "char_name_col_merged" not in res_split.validation.columns

    npt.assert_array_equal(res_split.extension.F.values, nnaa.F.values)
    npt.assert_array_equal(res_split.extension.F_Y.values, nnaa.F_Y.values)

    assert res_split.extension.get_index().names[0] == "impact"
    assert res_split.extension.get_index().names[1] == "impact2"


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_characterize_extension_over_extensions(fix_testmrio):
    """Testing characterisation over multiple extensions."""
    f_wo_ext = pd.read_csv(
        Path(PYMRIO_PATH["test_mrio"] / Path("concordance") / "emissions_charact.tsv"),
        sep="\t",
    )
    f_with_ext = f_wo_ext.copy()
    f_with_ext.loc[:, "extension"] = "Emissions"

    tt = fix_testmrio.testmrio

    # Test with same extension
    ex_wo_ext_full = tt.emissions.characterize(f_wo_ext, name="new_wo")
    only_val = pymrio.extension_characterize(tt.emissions, factors=f_with_ext, only_validation=True)
    ex_with_ext_full = pymrio.extension_characterize(tt.emissions, factors=f_with_ext, new_extension_name="new_with")

    assert only_val.extension is None
    pdt.assert_frame_equal(only_val.validation, ex_with_ext_full.validation)
    ex_with_ext = ex_with_ext_full.extension
    ex_wo_ext = ex_wo_ext_full.extension

    pdt.assert_frame_equal(ex_wo_ext.F, ex_with_ext.F)
    pdt.assert_frame_equal(ex_wo_ext.F_Y, ex_with_ext.F_Y)

    # Test for different classifications in extensions
    with pytest.raises(ValueError):
        f_with_fac = f_with_ext.copy()
        f_with_fac.loc[0, "extension"] = "Factor Inputs"
        _tmp_fail = pymrio.extension_characterize(
            tt.emissions,
            tt.factor_inputs,
            factors=f_with_fac,
            new_extension_name="_should_raise",
        )
    # But it should work if the extension is not needed
    _tmp_work = pymrio.extension_characterize(
        tt.emissions,
        tt.factor_inputs,
        factors=f_with_ext,
        new_extension_name="_should_work",
    ).extension
    pdt.assert_frame_equal(_tmp_work.F, ex_with_ext.F)
    pdt.assert_frame_equal(_tmp_work.F_Y, ex_with_ext.F_Y)

    # Test with two extensions and region differentiations
    tt.water = tt.emissions.copy("water")
    tt.air = tt.emissions.copy("air")

    tt.air.F = tt.air.F.loc[[("emission_type1", "air")], :]
    tt.air.F_Y = tt.air.F_Y.loc[[("emission_type1", "air")], :]
    tt.water.F = tt.water.F.loc[[("emission_type2", "water")], :]
    tt.water.F_Y = tt.water.F_Y.loc[[("emission_type2", "water")], :]

    factors_reg_spec = pd.read_csv(
        Path(PYMRIO_PATH["test_mrio"] / Path("concordance") / "emissions_charact_reg_spec.tsv"),
        sep="\t",
    )

    # Throw in some doubling for the testing
    factors_reg_spec.loc[factors_reg_spec.region == "reg2", "factor"] = (
        factors_reg_spec.loc[factors_reg_spec.region == "reg2", "factor"] * 2
    )

    factors_reg_ext = factors_reg_spec.copy()

    factors_reg_ext.loc[:, "extension"] = factors_reg_ext.loc[:, "compartment"]
    factors_reg_ext = factors_reg_ext[factors_reg_ext.compartment != "land"]

    ex_reg_one = tt.emissions.characterize(factors_reg_spec, name="one", characterized_name_column=["impact"]).extension
    ex_reg_multi = pymrio.extension_characterize(
        *list(tt.get_extensions(data=True)),
        factors=factors_reg_ext,
        new_extension_name="multi",
    ).extension

    ex_reg_method = tt.extension_characterize(factors=factors_reg_ext, new_extension_name="multi").extension

    pdt.assert_frame_equal(ex_reg_one.F, ex_reg_multi.F)
    pdt.assert_frame_equal(ex_reg_one.F_Y, ex_reg_multi.F_Y)
    pdt.assert_frame_equal(ex_reg_one.unit, ex_reg_multi.unit)
    pdt.assert_frame_equal(ex_reg_one.F, ex_reg_method.F)
    pdt.assert_frame_equal(ex_reg_one.F_Y, ex_reg_method.F_Y)
    pdt.assert_frame_equal(ex_reg_one.unit, ex_reg_method.unit)


def test_extension_convert_simple(fix_testmrio):
    """Testing the convert function within extensions object."""
    tt_pre = fix_testmrio.testmrio.copy()

    df_map = pd.DataFrame(
        columns=[
            "stressor",
            "compartment",
            "total__stressor",
            "factor",
            "unit_orig",
            "unit_new",
        ],
        data=[
            ["emis.*", "air|water", "total_sum_tonnes", 1e-3, "kg", "t"],
            ["emission_type[1|2]", ".*", "total_sum", 1, "kg", "kg"],
            ["emission_type1", ".*", "air_emissions", 1e-3, "kg", "t"],
            ["emission_type2", ".*", "water_emissions", 1000, "kg", "g"],
            ["emission_type1", ".*", "char_emissions", 2, "kg", "kg_eq"],
            ["emission_type2", ".*", "char_emissions", 10, "kg", "kg_eq"],
        ],
    )

    # check alphabetic order
    tt_pre.pre_calc = tt_pre.emissions.convert(df_map, new_extension_name="emissions_new_pre_calc", reindex=None)
    assert list(tt_pre.pre_calc.get_rows()) == sorted(df_map.loc[:, "total__stressor"].unique())

    # check previous order
    tt_pre.pre_calc = tt_pre.emissions.convert(
        df_map, new_extension_name="emissions_new_pre_calc", reindex="total__stressor"
    )
    assert list(tt_pre.pre_calc.get_rows()) == list(df_map.loc[:, "total__stressor"].unique())

    tt_pre.calc_all()

    pdt.assert_series_equal(
        tt_pre.emissions.D_cba.loc["emission_type1", "air"],
        tt_pre.pre_calc.D_cba.loc["air_emissions"] * 1000,
        check_names=False,
    )
    pdt.assert_series_equal(
        tt_pre.emissions.D_cba.loc["emission_type2", "water"],
        tt_pre.pre_calc.D_cba.loc["water_emissions"] * 1e-3,
        check_names=False,
    )

    pdt.assert_series_equal(
        tt_pre.emissions.D_cba.loc["emission_type1", "air"] * 2
        + tt_pre.emissions.D_cba.loc["emission_type2", "water"] * 10,
        tt_pre.pre_calc.D_cba.loc["char_emissions"],
        check_names=False,
    )

    npt.assert_allclose(
        tt_pre.emissions.D_imp.sum().sum(),
        tt_pre.pre_calc.D_imp.loc["total_sum_tonnes"].sum().sum() * 1000,
        rtol=1e-6,
    )
    npt.assert_allclose(
        tt_pre.emissions.M.sum().sum(),
        tt_pre.pre_calc.M.loc["total_sum"].sum().sum(),
        rtol=1e-6,
    )

    assert tt_pre.pre_calc.unit.loc["total_sum_tonnes", "unit"] == "t"
    assert tt_pre.pre_calc.unit.loc["total_sum", "unit"] == "kg"
    assert tt_pre.pre_calc.unit.loc["air_emissions", "unit"] == "t"
    assert tt_pre.pre_calc.unit.loc["water_emissions", "unit"] == "g"
    assert tt_pre.pre_calc.unit.loc["char_emissions", "unit"] == "kg_eq"

    tt_post = fix_testmrio.testmrio.copy()
    tt_post.calc_all()

    tt_post.post_calc = tt_post.emissions.convert(df_map, new_extension_name="emissions_new_post_calc")

    pdt.assert_series_equal(
        tt_post.emissions.D_cba.loc["emission_type1", "air"],
        tt_post.post_calc.D_cba.loc["air_emissions"] * 1000,
        check_names=False,
    )
    pdt.assert_series_equal(
        tt_post.emissions.D_cba.loc["emission_type2", "water"],
        tt_post.post_calc.D_cba.loc["water_emissions"] * 1e-3,
        check_names=False,
    )

    pdt.assert_series_equal(
        tt_post.emissions.D_cba.loc["emission_type1", "air"] * 2
        + tt_post.emissions.D_cba.loc["emission_type2", "water"] * 10,
        tt_post.post_calc.D_cba.loc["char_emissions"],
        check_names=False,
    )

    npt.assert_allclose(
        tt_post.emissions.D_imp.sum().sum(),
        tt_post.post_calc.D_imp.loc["total_sum_tonnes"].sum().sum() * 1000,
        rtol=1e-6,
    )
    npt.assert_allclose(
        tt_post.emissions.M.sum().sum(),
        tt_post.post_calc.M.loc["total_sum"].sum().sum(),
        rtol=1e-6,
    )

    assert tt_post.post_calc.unit.loc["total_sum_tonnes", "unit"] == "t"
    assert tt_post.post_calc.unit.loc["total_sum", "unit"] == "kg"
    assert tt_post.post_calc.unit.loc["air_emissions", "unit"] == "t"
    assert tt_post.post_calc.unit.loc["water_emissions", "unit"] == "g"
    assert tt_post.post_calc.unit.loc["char_emissions", "unit"] == "kg_eq"


# Filter UserWarning as these are thrown by missing an extensions
@pytest.mark.filterwarnings("ignore::UserWarning")
def test_extension_convert_function(fix_testmrio):
    """Testing the convert function for a list of extensions."""
    tt_pre = fix_testmrio.testmrio.copy()

    df_map_double = pd.DataFrame(
        columns=[
            "extension",
            "stressor",
            "compartment",
            "stressor__stressor",
            "compartment__compartment",
            "factor",
            "unit_orig",
            "unit_new",
        ],
        data=[
            [
                "Emissions",
                "emis.*",
                "air|water",
                "total_sum_tonnes",
                "total",
                1e-3,
                "kg",
                "t",
            ],
            [
                "Emissions",
                "emission_type2",
                "water",
                "water_emissions",
                "water",
                1000,
                "kg",
                "g",
            ],
        ],
    )

    # CASE 1: Doing two time the same extension, must double the results
    ext_double = pymrio.extension_convert(
        tt_pre.emissions,
        tt_pre.emissions,
        df_map=df_map_double,
        new_extension_name="emissions_new_pre_calc",
    )

    assert ext_double.unit.loc["total_sum_tonnes", "unit"].to_numpy() == ["t"]
    assert ext_double.unit.loc["water_emissions", "unit"].to_numpy() == ["g"]

    pdt.assert_series_equal(
        ext_double.F.loc[("total_sum_tonnes", "total")],
        tt_pre.emissions.F.sum(axis=0) * 1e-3 * 2,
        check_names=False,
    )

    pdt.assert_series_equal(
        ext_double.F.loc[("water_emissions", "water")],
        tt_pre.emissions.F.loc["emission_type2", :].iloc[0, :] * 1000 * 2,
        check_names=False,
    )

    # CASE 2: convert across 2 extensions
    tt_pre.emission_new = ext_double

    df_map_add_across = pd.DataFrame(
        columns=[
            "extension",
            "stressor",
            "compartment",
            "total__stressor",
            "factor",
            "unit_orig",
            "unit_new",
        ],
        data=[
            ["Emissions", "emission_type2", ".*", "water", 1, "kg", "kg"],
            [
                "emissions_new_pre_calc",
                "water_emissions",
                ".*",
                "water",
                1e-3,
                "g",
                "kg",
            ],
        ],
    )

    df_map_add_across_wrong_name = df_map_add_across.copy()

    df_map_add_across_wrong_name.loc[:, "extension"] = df_map_add_across_wrong_name.extension.str.replace(
        "emissions_new_pre_calc", "foo"
    )

    ext_across_correct = pymrio.extension_convert(
        tt_pre.emissions,
        ext_double,
        df_map=df_map_add_across,
        new_extension_name="add_across",
    )

    ext_across_wrong = pymrio.extension_convert(
        tt_pre.emissions,
        ext_double,
        df_map=df_map_add_across_wrong_name,
        new_extension_name="add_across",
    )

    expected_df_correct_F = (
        tt_pre.emissions.F.loc["emission_type2", :].iloc[0, :] + ext_double.F.loc[("water_emissions", "water")] * 1e-3
    )
    expected_df_wrong_F = tt_pre.emissions.F.loc["emission_type2", :].iloc[0, :]
    expected_df_correct_F_Y = (
        tt_pre.emissions.F_Y.loc["emission_type2", :].iloc[0, :]
        + ext_double.F_Y.loc[("water_emissions", "water")] * 1e-3
    )
    expected_df_wrong_F_Y = tt_pre.emissions.F_Y.loc["emission_type2", :].iloc[0, :]

    pdt.assert_series_equal(
        ext_across_correct.F.loc[("water",)],
        expected_df_correct_F,
        check_names=False,
    )

    pdt.assert_series_equal(
        ext_across_correct.F_Y.loc[("water",)],
        expected_df_correct_F_Y,
        check_names=False,
    )
    pdt.assert_series_equal(
        ext_across_wrong.F.loc[("water",)],
        expected_df_wrong_F,
        check_names=False,
    )
    pdt.assert_series_equal(
        ext_across_wrong.F_Y.loc[("water",)],
        expected_df_wrong_F_Y,
        check_names=False,
    )

    # CASE 3: Test for full calculated system
    tt_post = fix_testmrio.testmrio.copy().calc_all()

    # when one extensions has less calculated parts then the other, these should
    # silently set to None
    ext_test_missing = pymrio.extension_convert(
        tt_post.emissions,
        ext_double,
        df_map=df_map_add_across,
        new_extension_name="add_across",
    )

    assert ext_test_missing.S is None
    assert ext_test_missing.D_cba is None

    tt_post.add_across = ext_double
    tt_post.calc_all()

    ext_test_all = pymrio.extension_convert(
        tt_post.emissions,
        tt_post.add_across,
        df_map=df_map_add_across,
        new_extension_name="add_across",
    )

    expected_df_D_cba = (
        tt_post.emissions.D_cba.loc["emission_type2", :].iloc[0, :]
        + tt_post.add_across.D_cba.loc[("water_emissions", "water")] * 1e-3
    )
    expected_df_S = (
        tt_post.emissions.S.loc["emission_type2", :].iloc[0, :]
        + tt_post.add_across.S.loc[("water_emissions", "water")] * 1e-3
    )
    expected_df_M = (
        tt_post.emissions.M.loc["emission_type2", :].iloc[0, :]
        + tt_post.add_across.M.loc[("water_emissions", "water")] * 1e-3
    )

    pdt.assert_series_equal(
        ext_test_all.D_cba.iloc[0],
        expected_df_D_cba,
        check_names=False,
    )
    pdt.assert_series_equal(
        ext_test_all.S.iloc[0],
        expected_df_S,
        check_names=False,
    )
    pdt.assert_series_equal(
        ext_test_all.M.iloc[0],
        expected_df_M,
        check_names=False,
    )

    # test for the top level method

    ext_test_all_meth = tt_post.extension_convert(
        df_map=df_map_add_across,
        new_extension_name="add_across",
    )
    pdt.assert_series_equal(
        ext_test_all_meth.D_cba.iloc[0],
        expected_df_D_cba,
        check_names=False,
    )
    pdt.assert_series_equal(
        ext_test_all_meth.S.iloc[0],
        expected_df_S,
        check_names=False,
    )
    pdt.assert_series_equal(
        ext_test_all_meth.M.iloc[0],
        expected_df_M,
        check_names=False,
    )

    df_map_order_check = pd.DataFrame(
        columns=[
            "extension",
            "stressor",
            "compartment",
            "total__stressor",
            "factor",
            "unit_orig",
            "unit_new",
        ],
        data=[
            ["Emissions", "emission_type2", ".*", "water", 1, "kg", "kg"],
            ["Emissions", "emission_type2", ".*", "air", 1, "kg", "kg"],
            [
                "emissions_new_pre_calc",
                "water_emissions",
                ".*",
                "water",
                1e-3,
                "g",
                "kg",
            ],
        ],
    )

    ext_test_order_a = tt_post.extension_convert(
        df_map=df_map_order_check, new_extension_name="add_across", reindex=None
    )

    assert list(ext_test_order_a.get_rows()) == ["air", "water"]

    ext_test_order_c = tt_post.extension_convert(
        df_map=df_map_order_check,
        new_extension_name="add_across",
        reindex="total__stressor",
    )

    assert list(ext_test_order_c.get_rows()) == ["water", "air"]


def test_extension_convert_test_unit_fail(fix_testmrio):
    """Test convert with failing due to unit issues."""
    df_fail1 = pd.DataFrame(
        columns=[
            "stressor",
            "compartment",
            "total__stressor",
            "factor",
            "unit_orig",
            "unit_new",
        ],
        data=[
            ["emis.*", "air|water", "total_regex", 1000, "g", "t"],
        ],
    )

    df_fail2 = pd.DataFrame(
        columns=[
            "stressor",
            "compartment",
            "total__stressor",
            "factor",
            "unit_emis",
            "unit_new",
        ],
        data=[
            ["emission_type1", "air", "total_regex", 1, "t", "t"],
        ],
    )

    df_wo_unit = pd.DataFrame(
        columns=["stressor", "compartment", "total__stressor", "factor"],
        data=[
            ["emission_type1", "air", "total_regex", 1],
        ],
    )

    df_new_unit = pd.DataFrame(
        columns=["stressor", "compartment", "total__stressor", "factor", "set_unit"],
        data=[
            ["emission_type1", "air", "total_regex", 1e-3, "t"],
        ],
    )

    with pytest.raises(ValueError):
        fix_testmrio.testmrio.emissions.convert(df_fail1, new_extension_name="emissions_new")

    with pytest.raises(ValueError):
        fix_testmrio.testmrio.emissions.convert(
            df_fail2, new_extension_name="emissions_new", unit_column_orig="unit_emis"
        )

    with pytest.raises(ValueError):
        fix_testmrio.testmrio.emissions.convert(
            df_wo_unit, new_extension_name="emissions_new", unit_column_orig="unit_emis"
        )

    wounit = fix_testmrio.testmrio.emissions.convert(
        df_wo_unit,
        new_extension_name="emissions_new",
        unit_column_orig=None,
        unit_column_new=None,
    )
    assert wounit.unit is None

    with pytest.raises(ValueError):
        fix_testmrio.testmrio.emissions.convert(
            df_new_unit, new_extension_name="emissions_new", unit_column_new="unit_new"
        )

    newunit = fix_testmrio.testmrio.emissions.convert(
        df_new_unit,
        new_extension_name="emissions_new",
        unit_column_orig=None,
        unit_column_new="set_unit",
    )
    assert newunit.unit.loc["total_regex", "unit"] == "t"


def test_reset_to_flows(fix_testmrio):
    """Test reset."""
    tt = fix_testmrio.testmrio
    assert tt.A is None
    tt.calc_all()
    tt.reset_to_flows()
    assert tt.A is None
    tt.Z = None
    with pytest.raises(pymrio.core.mriosystem.ResetError):
        tt.reset_to_flows()
    with pytest.warns(pymrio.core.mriosystem.ResetWarning):
        tt.reset_to_flows(force=True)


def test_reset_all_to_flows(fix_testmrio):
    """Test reset."""
    tt = fix_testmrio.testmrio
    assert tt.A is None
    tt.calc_all()
    tt.reset_all_to_flows()
    assert tt.A is None
    assert tt.emissions.S is None
    tt.Z = None
    with pytest.raises(pymrio.core.mriosystem.ResetError):
        tt.reset_to_flows()
    with pytest.warns(pymrio.core.mriosystem.ResetWarning):
        tt.reset_to_flows(force=True)


def test_reset_full(fix_testmrio):
    """Test reset."""
    tt = fix_testmrio.testmrio
    assert tt.A is None
    tt.calc_all()
    tt.reset_full()
    assert tt.A is None
    tt.Z = None
    with pytest.raises(pymrio.core.mriosystem.ResetError):
        tt.reset_full()
    with pytest.warns(pymrio.core.mriosystem.ResetWarning):
        tt.reset_full(force=True)


def test_reset_all_full(fix_testmrio):
    """Test full reset."""
    tt = fix_testmrio.testmrio
    assert tt.A is None
    assert tt.emissions.S is None
    tt.calc_all()
    tt.reset_all_full()
    assert tt.A is None
    assert tt.emissions.S is None
    assert tt.emissions.D_exp is None
    tt.Z = None
    with pytest.raises(pymrio.core.mriosystem.ResetError):
        tt.reset_all_full()
    with pytest.warns(pymrio.core.mriosystem.ResetWarning):
        tt.reset_all_full(force=True)


def test_reset_to_coefficients(fix_testmrio):
    """Test resting to coefficients."""
    tt = fix_testmrio.testmrio
    tt.calc_all()
    tt.reset_all_to_coefficients()
    assert tt.Z is None
    assert tt.emissions.F is None


def test_find(fix_testmrio):
    """Test finding things."""
    tt = fix_testmrio.testmrio

    all_found = tt.find(".*")
    assert all(all_found["sectors"] == tt.get_sectors())
    assert all(all_found["regions"] == tt.get_regions())
    assert all(all_found["Y_categories"] == tt.get_Y_categories())
    assert all(all_found["index"] == tt.get_index())

    for ext in tt.get_extensions(data=False):
        assert all(all_found[ext + "_index"] == tt.__dict__[ext].get_index())

    ext_find = tt.find("air")
    assert "sectors" not in ext_find
    assert "regions" not in ext_find
    assert "Y_categories" not in ext_find


def test_contain_match_matchall(fix_testmrio):
    """Test matching stuff."""
    tt = fix_testmrio.testmrio

    cont_bare = tt.contains("th")
    cont_find_all = tt.contains(find_all="th")
    assert all(cont_bare == cont_find_all)
    assert "other" in cont_bare.get_level_values("sector")
    assert "reg1" in cont_bare.get_level_values("region")
    assert "reg2" in cont_bare.get_level_values("region")
    assert "food" not in cont_bare.get_level_values("sector")

    match_test_empty = tt.match("th")
    fullmatch_test_empty = tt.fullmatch("oth")
    fullmatch_test_empty2 = tt.fullmatch("OTHER")
    assert len(match_test_empty) == 0
    assert len(fullmatch_test_empty) == 0
    assert len(fullmatch_test_empty2) == 0

    match_test = tt.match("oth")
    assert all(match_test == cont_bare)

    fullmatch_test1 = tt.fullmatch("other")
    fullmatch_test2 = tt.fullmatch(".*oth.*")
    fullmatch_test3 = tt.fullmatch("(?i)OTHER")
    fullmatch_test4 = tt.fullmatch("(?i).*THE.*")
    assert all(fullmatch_test1 == cont_bare)
    assert all(fullmatch_test2 == cont_bare)
    assert all(fullmatch_test3 == cont_bare)
    assert all(fullmatch_test4 == cont_bare)

    # check with keywords and extensions
    ext_air = tt.emissions.match(compartment="air")
    ext_air_none = tt.emissions.match(stressor="air")
    assert len(ext_air_none) == 0
    assert len(ext_air) > 0

    ext_all_comp = tt.emissions.match(compartment="air|water")
    assert all(ext_all_comp == tt.emissions.F.index)


def test_extension_match_contain(fix_testmrio):
    """Test match contains."""
    tt = fix_testmrio.testmrio
    match_air = tt.extension_match(find_all="air")
    assert len(match_air["Factor Inputs"]) == 0
    assert len(match_air["Emissions"]) == 1

    contain_value_added = tt.extension_contains(inputtype="dded")
    assert len(contain_value_added["Factor Inputs"]) == 1
    assert len(contain_value_added["Emissions"]) == 0

    fullmatch_0 = tt.extension_fullmatch(emissions="dded")
    assert len(fullmatch_0["Factor Inputs"]) == 0
    assert len(fullmatch_0["Emissions"]) == 0
    fullmatch_1 = tt.extension_fullmatch(stressor="emission_type.*")
    assert len(fullmatch_1["Factor Inputs"]) == 0
    assert len(fullmatch_1["Emissions"]) == 2

    # dual match
    dual_match1 = tt.extension_match(stressor="emission_type.*", compartment="air")
    assert len(dual_match1["Factor Inputs"]) == 0
    assert len(dual_match1["Emissions"]) == 1

    dual_match2 = tt.extension_contains(stressor="1", inputtype="alue")
    assert len(dual_match2["Factor Inputs"]) == 1
    assert len(dual_match2["Emissions"]) == 1

    # Test for extension instance and set names
    inst_match = tt.extension_match(extensions=["emissions", "factor_inputs"], stressor="emission_type.*")
    assert len(inst_match["emissions"]) == 2
    assert len(inst_match["factor_inputs"]) == 0

    inst_match2 = tt.extension_match(extensions=["emissions"], stressor="emission_type.*")
    assert len(inst_match2["emissions"]) == 2
    assert "factor_inputs" not in inst_match2

    name_match = tt.extension_contains(extensions=["Factor Inputs"], inputtype="Value")
    assert "factor_inputs" not in name_match
    assert len(name_match["Factor Inputs"]) == 1


def test_direct_account_calc(fix_testmrio):
    """Test simple account calcs."""
    orig = fix_testmrio.testmrio
    orig.calc_all()

    with pytest.raises(ValueError):
        (D_cba, D_pba, D_imp, D_exp) = pymrio.calc_accounts(orig.emissions.S, orig.L, orig.Y)

    new = orig.copy().rename_regions({"reg3": "ll", "reg4": "aa"})

    Y_agg = new.Y.T.groupby(level="region", sort=False).agg("sum").T

    (D_cba, D_pba, D_imp, D_exp) = pymrio.calc_accounts(new.emissions.S, new.L, Y_agg)

    pdt.assert_frame_equal(orig.emissions.D_cba["reg2"], D_cba["reg2"])
    pdt.assert_frame_equal(orig.emissions.D_exp["reg4"], D_exp["aa"])
    pdt.assert_frame_equal(orig.emissions.D_imp["reg3"], D_imp["ll"])


def test_extension_reset_with_rename(fix_testmrio):
    """Test reset/rename."""
    orig = fix_testmrio.testmrio
    orig.calc_all()

    new = orig.copy()
    new.reset_extensions()
    new.Y = new.Y.loc[:, ["reg2", "reg3"]]
    new.calc_all()

    pdt.assert_frame_equal(new.A, orig.A)

    pdt.assert_frame_equal(new.emissions.D_cba["reg2"], orig.emissions.D_cba["reg2"])
    pdt.assert_frame_equal(new.emissions.D_imp["reg2"], orig.emissions.D_imp["reg2"])

    assert orig.emissions.D_exp_reg.reg1.sum() > new.emissions.D_exp_reg.reg1.sum()

    orig_rename = orig.copy()
    orig_rename.reset_extensions()
    orig_rename.rename_regions({"reg3": "cd", "reg4": "ab"})

    orig_rename.calc_all()
    pdt.assert_frame_equal(orig.emissions.D_imp["reg3"], orig_rename.emissions.D_imp["cd"])
    new_rename = orig_rename.copy().reset_extensions()
    new_rename.Y = new_rename.Y.loc[:, ["reg2", "cd", "ab"]]
    new_rename.calc_all()
    pdt.assert_frame_equal(new_rename.emissions.D_imp["reg2"], orig_rename.emissions.D_imp["reg2"])
    pdt.assert_frame_equal(new_rename.emissions.D_cba["cd"], orig_rename.emissions.D_cba["cd"])
    pdt.assert_frame_equal(new_rename.emissions.D_cba["ab"], orig_rename.emissions.D_cba["ab"])
    pdt.assert_frame_equal(orig.emissions.D_cba["reg4"], new_rename.emissions.D_cba["ab"])


def test_concate_extensions(fix_testmrio):
    """Test concating extensions."""
    tt = fix_testmrio.testmrio

    added_diff = pymrio.extension_concate(*[tt.emissions, tt.factor_inputs], new_extension_name="diff")
    added_same = pymrio.extension_concate(*[tt.emissions, tt.emissions], new_extension_name="same")

    assert added_same.get_rows().names == ["stressor", "compartment"]
    # When names differ, indicator is used
    assert added_diff.get_rows().names == ["indicator", "compartment"]

    assert len(added_same.F) == len(tt.emissions.F) * 2
    assert len(added_same.F_Y) == len(tt.emissions.F) * 2
    assert len(added_diff.F) == len(tt.emissions.F) + len(tt.factor_inputs.F)
    assert len(added_diff.F_Y) == len(tt.emissions.F) + len(tt.factor_inputs.F)

    testF = added_diff.F.reset_index("compartment")
    assert all(testF.loc["Value Added", "compartment"].isna())

    added_meth = tt.extension_concate(new_extension_name="method")
    pdt.assert_frame_equal(added_meth.F, added_diff.F, check_like=True, check_names=True)
    pdt.assert_frame_equal(added_meth.F_Y, added_diff.F_Y, check_like=True, check_names=True)
