""" Testing core functionality of pymrio
"""

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
    """Single point to load the test mrio"""

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
            "Final consumption expenditure by non-profit "
            "organisations serving households (NPISH)",
            "Final consumption expenditure by government",
            "Gross fixed capital formation",
            "Changes in inventories",
            "Changes in valuables",
            "Export",
        ]

    return TestMRIO


def test_copy(fix_testmrio):
    """Testing the deep copy functionality + naming"""
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

    reg3trade_imports_from_reg2 = (
        tt.Z.loc[("reg2", "trade"), "reg3"].sum()
        + tt.Y.loc[("reg2", "trade"), "reg3"].sum()
    )
    assert reg3trade_imports_from_reg2 == pytest.approx(
        flows.loc[("reg2", "trade"), "reg3"]
    )


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
    tt = fix_testmrio.testmrio
    exts = list(
        tt.get_extensions(names=names, data=data, instance_names=instance_names)
    )
    assert sorted(exts) == sorted(result)


def test_get_extension_raise(fix_testmrio):
    tt = fix_testmrio.testmrio
    with pytest.raises(ValueError):
        list(
            tt.get_extensions(
                names=["emissions", "foo"], data=False, instance_names=True
            )
        )


def test_get_index(fix_testmrio):
    """Testing the different options for get_index in core.mriosystem"""
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
    assert all([True if v == "r" else False for v in pat2index.values()])

    # test one level index

    # pat_single_tpl = {('Value Added',): 'va'}
    pat_single_str = {"Value Added": "va"}
    pat_single_index = tt.factor_inputs.get_index(
        as_dict=True, grouping_pattern=pat_single_str
    )
    assert pat_single_str == pat_single_index


def test_set_index(fix_testmrio):
    tt = fix_testmrio.testmrio
    new_index = ["a", "b"]
    tt.emissions.set_index(new_index)
    assert tt.emissions.get_index()[0] == new_index[0]
    assert tt.emissions.get_index()[1] == new_index[1]


def test_get_sectors(fix_testmrio):
    assert list(fix_testmrio.testmrio.get_sectors()) == fix_testmrio.sectors
    assert (
        fix_testmrio.testmrio.get_sectors(["construction", "food", "a"])[
            fix_testmrio.sectors.index("construction")
        ]
        == "construction"
    )
    assert (
        fix_testmrio.testmrio.get_sectors(["construction", "food", "a"])[
            fix_testmrio.sectors.index("food")
        ]
        == "food"
    )
    assert fix_testmrio.testmrio.get_sectors("food") == [
        e if e == "food" else None for e in fix_testmrio.sectors
    ]
    assert (
        fix_testmrio.testmrio.get_sectors(["construction", "food", "a"])[1] == None
    )  # noqa


def test_get_regions(fix_testmrio):
    assert list(fix_testmrio.testmrio.get_regions()) == fix_testmrio.regions

    assert (
        fix_testmrio.testmrio.get_regions(fix_testmrio.regions[:])
        == fix_testmrio.regions
    )

    assert fix_testmrio.testmrio.get_regions("reg4") == [
        e if e == "reg4" else None for e in fix_testmrio.regions
    ]


def test_get_Y_categories(fix_testmrio):
    assert list(fix_testmrio.testmrio.get_Y_categories()) == fix_testmrio.Y_cat

    assert (
        fix_testmrio.testmrio.get_Y_categories(fix_testmrio.Y_cat[:])
        == fix_testmrio.Y_cat
    )

    assert fix_testmrio.testmrio.get_Y_categories("Export") == [
        e if e == "Export" else None for e in fix_testmrio.Y_cat
    ]


def test_rename_regions(fix_testmrio):
    new_reg_name = "New Region 1"
    new_reg_list = ["a1", "a2", "a3", "a4", "a5", "a6"]
    fix_testmrio.testmrio.rename_regions({"reg1": new_reg_name})
    assert fix_testmrio.testmrio.get_regions()[0] == new_reg_name
    fix_testmrio.testmrio.rename_regions(new_reg_list)
    assert fix_testmrio.testmrio.get_regions()[0] == new_reg_list[0]
    assert fix_testmrio.testmrio.get_regions()[2] == new_reg_list[2]


def test_rename_random_sectors(fix_testmrio):
    new_sec_name = "yummy"
    new_sec_list = ["s1", "s2", "s3", "s4", "s5", "s6"]
    fix_testmrio.testmrio.rename_sectors({"food": new_sec_name})
    assert fix_testmrio.testmrio.get_sectors()[0] == new_sec_name
    fix_testmrio.testmrio.rename_sectors(new_sec_list)
    assert fix_testmrio.testmrio.get_sectors()[0] == new_sec_list[0]
    assert fix_testmrio.testmrio.get_sectors()[4] == new_sec_list[4]


def test_rename_sector_with_io_info(fix_testmrio):
    with pytest.raises(ValueError):
        _ = pymrio.get_classification("foo")

    classdata = pymrio.get_classification("test")
    corr_dict = classdata.get_sector_dict(orig="TestMrioName", new="TestMrioCode")
    corr_dict2 = classdata.get_sector_dict(
        orig=fix_testmrio.testmrio.get_sectors(), new="TestMrioCode"
    )

    assert corr_dict == corr_dict2

    fix_testmrio.testmrio.rename_sectors(corr_dict)

    assert (
        fix_testmrio.testmrio.get_sectors()[3]
        == classdata.sectors.iloc[3, :].loc["TestMrioCode"]
    )


def test_rename_Ycat(fix_testmrio):
    new_cat_name = "HouseCons"
    new_cat_list = ["y1", "y2", "y3", "y4", "y5", "y6", "y7"]
    fix_testmrio.testmrio.rename_Y_categories({fix_testmrio.Y_cat[0]: new_cat_name})
    assert fix_testmrio.testmrio.get_Y_categories()[0] == new_cat_name
    fix_testmrio.testmrio.rename_Y_categories(new_cat_list)
    assert fix_testmrio.testmrio.get_Y_categories()[0] == new_cat_list[0]
    assert fix_testmrio.testmrio.get_Y_categories()[-1] == new_cat_list[-1]


def test_copy_and_extensions(fix_testmrio):
    tcp = fix_testmrio.testmrio.copy()
    tcp.remove_extension("Emissions")
    assert len(list(tcp.get_extensions())) == 1
    with pytest.raises(TypeError):
        tcp.remove_extension()
    tcnew = fix_testmrio.testmrio.copy()
    tcnew.remove_extension(tcnew.get_extensions())
    assert len(list(tcnew.get_extensions())) == 0


def test_extract(fix_testmrio):
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
    assert "F" in with_missing.keys()
    assert "FOO" not in with_missing.keys()


def test_extension_extract(fix_testmrio):
    tt = fix_testmrio.testmrio

    match_air = tt.extension_match(find_all="air")

    dfa = tt.extension_extract(match_air, dataframes=["F", "F_Y"], include_empty=True)
    assert dfa["Factor Inputs"]["F"].shape[0] == 0

    exta = tt.extension_extract(
        match_air, dataframes=["F", "F_Y"], include_empty=True, return_type="extension"
    )
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


# def test_characterize_extension_reg_spec(fix_testmrio):
#     factors = pd.read_csv(
#         Path(
#             PYMRIO_PATH["test_mrio"]
#             / Path("concordance")
#             / "emissions_charact_reg_spec.tsv"
#         ),
#         sep="\t",
#     )
#     shuffled = factors.sample(len(factors.index), random_state=666, axis=0)
#
#     t_uncalc = fix_testmrio.testmrio
#     t_calc = fix_testmrio.testmrio.calc_all()
#     uncalc_name = "emissions_charact_uncalc"
#
#     # CONT: Until here the new procedure should work already
#     ex_uncalc = t_uncalc.emissions.characterize(factors, name=uncalc_name)
#     ex_calc = t_uncalc.emissions.characterize(factors)
#
#     assert ex_uncalc.name == uncalc_name
#     assert ex_calc.name == t_calc.emissions.name + "_characterized"
#
#     # The test characterization matrix is all in t, the emissions in test are
#     # all in kg
#     assert ex_calc.unit.loc["total air emissions", "unit"] == "t"
#     npt.assert_allclose(
#         ex_uncalc.F.loc["total air emissions"].sum(),
#         (t_calc.emissions.F.loc[("emission_type1", "air"), :] / 1000).sum(),
#     )
#     npt.assert_allclose(
#         ex_calc.D_imp.loc["total air emissions"].sum(),
#         (t_calc.emissions.D_imp.loc[("emission_type1", "air"), :] / 1000).sum(),
#     )
#     npt.assert_allclose(
#         ex_calc.D_exp.loc["air water impact"].sum(),
#         (
#             (t_calc.emissions.D_exp.loc[("emission_type1", "air"), :] * 2 / 1000)
#             + (t_calc.emissions.D_exp.loc[("emission_type2", "water"), :] * 1 / 1000)
#         ).sum(),
#     )
#
#     # coefficients and multipliers can not characterized directly, so these
#     # should be removed and then recalculated
#
#     assert ex_calc.M is None
#     assert ex_calc.S is None
#     t_calc.impacts = ex_calc
#     t_calc.calc_all()
#     pdt.assert_series_equal(
#         t_calc.impacts.M.loc["total air emissions", :],
#         t_calc.emissions.M.loc[("emission_type1", "air"), :] / 1000,
#         check_names=False,
#     )
#     pdt.assert_series_equal(
#         t_calc.impacts.S.loc["total air emissions", :],
#         t_calc.emissions.S.loc[("emission_type1", "air"), :] / 1000,
#         check_names=False,
#     )
#
#     with pytest.raises(ValueError):
#         ex_error = t_uncalc.emissions.characterize(
#             factors, characterization_factors_column="foo"
#         )
#     with pytest.raises(ValueError):
#         ex_error = t_uncalc.factor_inputs.characterize(  # noqa: F841
#             factors, characterization_factors_column="foo"
#         )
#
#     # testing used characterization matrix
#     ret = t_uncalc.emissions.characterize(factors, return_char_matrix=True)
#     assert "emissions_type3" not in ret.factors.index
#
#     # testing characterization which do not cover all stressors
#     factors_short = factors[
#         (factors.stressor == "emission_type1")
#         & (factors.impact == "total air emissions")
#     ]
#     t_calc.short_impacts = t_calc.emissions.characterize(factors_short, name="shorty")
#     t_calc.calc_all()
#
#     pdt.assert_series_equal(
#         t_calc.short_impacts.S.loc["total air emissions", :],
#         t_calc.emissions.S.loc[("emission_type1", "air"), :] / 1000,
#         check_names=False,
#     )
#


def test_characterize_extension(fix_testmrio):
    factors = pd.read_csv(
        Path(PYMRIO_PATH["test_mrio"] / Path("concordance") / "emissions_charact.tsv"),
        sep="\t",
    )

    shuffled = factors.sample(len(factors.index), random_state=666, axis=0)

    t_uncalc = fix_testmrio.testmrio
    t_calc = fix_testmrio.testmrio.calc_all()
    uncalc_name = "emissions_charact_uncalc"
    ex_uncalc = t_uncalc.emissions.characterize(factors, name=uncalc_name)
    ex_calc = t_uncalc.emissions.characterize(factors)

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
        ex_calc.D_imp.loc["total air emissions"].sum(),
        (t_calc.emissions.D_imp.loc[("emission_type1", "air"), :] / 1000).sum(),
    )
    npt.assert_allclose(
        ex_calc.D_exp.loc["air water impact"].sum(),
        (
            (t_calc.emissions.D_exp.loc[("emission_type1", "air"), :] * 2 / 1000)
            + (t_calc.emissions.D_exp.loc[("emission_type2", "water"), :] * 1 / 1000)
        ).sum(),
    )

    # coefficients and multipliers can not characterized directly, so these
    # should be removed and then recalculated

    assert ex_calc.M is None
    assert ex_calc.S is None
    t_calc.impacts = ex_calc
    t_calc.calc_all()
    pdt.assert_series_equal(
        t_calc.impacts.M.loc["total air emissions", :],
        t_calc.emissions.M.loc[("emission_type1", "air"), :] / 1000,
        check_names=False,
    )
    pdt.assert_series_equal(
        t_calc.impacts.S.loc["total air emissions", :],
        t_calc.emissions.S.loc[("emission_type1", "air"), :] / 1000,
        check_names=False,
    )

    with pytest.raises(ValueError):
        ex_error = t_uncalc.emissions.characterize(
            factors, characterization_factors_column="foo"
        )
    with pytest.raises(ValueError):
        ex_error = t_uncalc.factor_inputs.characterize(  # noqa: F841
            factors, characterization_factors_column="foo"
        )

    # testing used characterization matrix
    ret = t_uncalc.emissions.characterize(factors, return_char_matrix=True)
    assert "emissions_type3" not in ret.factors.index

    # testing characterization which do not cover all stressors
    factors_short = factors[
        (factors.stressor == "emission_type1")
        & (factors.impact == "total air emissions")
    ]
    t_calc.short_impacts = t_calc.emissions.characterize(factors_short, name="shorty")
    t_calc.calc_all()

    pdt.assert_series_equal(
        t_calc.short_impacts.S.loc["total air emissions", :],
        t_calc.emissions.S.loc[("emission_type1", "air"), :] / 1000,
        check_names=False,
    )


def test_reset_to_flows(fix_testmrio):
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
    tt = fix_testmrio.testmrio
    tt.calc_all()
    tt.reset_all_to_coefficients()
    assert tt.Z is None
    assert tt.emissions.F is None


def test_find(fix_testmrio):
    tt = fix_testmrio.testmrio

    all_found = tt.find(".*")
    assert all(all_found["sectors"] == tt.get_sectors())
    assert all(all_found["regions"] == tt.get_regions())
    assert all(all_found["Y_categories"] == tt.get_Y_categories())
    assert all(all_found["index"] == tt.get_index())

    for ext in tt.get_extensions(data=False):
        assert all(all_found[ext + "_index"] == tt.__dict__[ext].get_index())

    ext_find = tt.find("air")
    assert "sectors" not in ext_find.keys()
    assert "regions" not in ext_find.keys()
    assert "Y_categories" not in ext_find.keys()


def test_contain_match_matchall(fix_testmrio):
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
    inst_match = tt.extension_match(
        extensions=["emissions", "factor_inputs"], stressor="emission_type.*"
    )
    assert len(inst_match["emissions"]) == 2
    assert len(inst_match["factor_inputs"]) == 0

    inst_match2 = tt.extension_match(
        extensions=["emissions"], stressor="emission_type.*"
    )
    assert len(inst_match2["emissions"]) == 2
    assert "factor_inputs" not in inst_match2.keys()

    name_match = tt.extension_contains(extensions=["Factor Inputs"], inputtype="Value")
    assert "factor_inputs" not in name_match.keys()
    assert len(name_match["Factor Inputs"]) == 1


def test_direct_account_calc(fix_testmrio):
    orig = fix_testmrio.testmrio
    orig.calc_all()

    with pytest.raises(ValueError):
        (D_cba, D_pba, D_imp, D_exp) = pymrio.calc_accounts(
            orig.emissions.S, orig.L, orig.Y
        )

    new = orig.copy().rename_regions({"reg3": "ll", "reg4": "aa"})

    Y_agg = new.Y.groupby(axis=1, level="region", sort=False).agg(sum)

    (D_cba, D_pba, D_imp, D_exp) = pymrio.calc_accounts(new.emissions.S, new.L, Y_agg)

    pdt.assert_frame_equal(orig.emissions.D_cba["reg2"], D_cba["reg2"])
    pdt.assert_frame_equal(orig.emissions.D_exp["reg4"], D_exp["aa"])
    pdt.assert_frame_equal(orig.emissions.D_imp["reg3"], D_imp["ll"])


def test_extension_reset_with_rename(fix_testmrio):
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
    pdt.assert_frame_equal(
        orig.emissions.D_imp["reg3"], orig_rename.emissions.D_imp["cd"]
    )
    new_rename = orig_rename.copy().reset_extensions()
    new_rename.Y = new_rename.Y.loc[:, ["reg2", "cd", "ab"]]
    new_rename.calc_all()
    pdt.assert_frame_equal(
        new_rename.emissions.D_imp["reg2"], orig_rename.emissions.D_imp["reg2"]
    )
    pdt.assert_frame_equal(
        new_rename.emissions.D_cba["cd"], orig_rename.emissions.D_cba["cd"]
    )
    pdt.assert_frame_equal(
        new_rename.emissions.D_cba["ab"], orig_rename.emissions.D_cba["ab"]
    )
    pdt.assert_frame_equal(
        orig.emissions.D_cba["reg4"], new_rename.emissions.D_cba["ab"]
    )
