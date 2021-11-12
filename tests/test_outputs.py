""" Test for producing graphical outputs

    The report functionality is tested separately
    in test_integration

    Note
    ----

    Here we use the values returned from the plotted graph
    for testing. Regression tests against plotted graphs,
    as provided by image_comparison decorator of matplotlib,
    are not used since this is deprecated and also not consistent
    across different plotting engines.

"""


import os
import sys

import pytest

TESTPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(TESTPATH, ".."))

import pymrio  # noqa


@pytest.fixture()
def fix_testmrio_calc():
    """Single point to load the test mrio"""

    class TestMRIO:
        testmrio = pymrio.load_test().calc_all()

    return TestMRIO


def test_graphs_totals(fix_testmrio_calc):
    """Testing graph totals"""
    stressor = ("emission_type1", "air")
    tt = fix_testmrio_calc.testmrio
    ax = tt.emissions.plot_account(row=stressor)

    assert stressor[0] in str(ax.title)

    # In the plotting method data is extracted
    # for each account from all regions. Thus
    # the order of drawn patches is for each account
    # (cba, pba, imp, exp) for each region
    assert ax.patches[0].get_height() == tt.emissions.D_cba_reg.loc[stressor, "reg1"]
    assert ax.patches[1].get_height() == tt.emissions.D_cba_reg.loc[stressor, "reg2"]
    assert ax.patches[6].get_height() == tt.emissions.D_pba_reg.loc[stressor, "reg1"]

    with pytest.raises(ValueError):
        ax = tt.emissions.plot_account(row=stressor, per_capita=5)

    with pytest.raises(ValueError):
        ax = tt.emissions.plot_account(row=stressor, sector="food", per_capita=True)


def test_graphs_population_sector(fix_testmrio_calc):
    """Testing graph per population for a specific sector"""
    stressor = ("emission_type2", "water")
    sector = "mining"

    tt = fix_testmrio_calc.testmrio
    ax = tt.emissions.plot_account(
        row=stressor, per_capita=True, population=tt.population, sector=sector
    )

    assert stressor[0] in str(ax.title)
    assert stressor[1] in str(ax.title)
    assert sector in str(ax.title)
    assert "capita" in str(ax.title)

    # In the plotting method data is extracted
    # for each account from all regions. Thus
    # the order of drawn patches is for each account
    # (cba, pba, imp, exp) for each region
    sec_reg1_pop = (
        tt.emissions.D_cba.loc[stressor, ("reg1", sector)] / tt.population.reg1
    )[0]

    assert ax.patches[0].get_height() == sec_reg1_pop


def test_graphs_population_total(fix_testmrio_calc):
    """Testing total per population accounts"""
    stressor = ("emission_type2", "water")

    tt = fix_testmrio_calc.testmrio
    ax = tt.emissions.plot_account(row=stressor, per_capita=True)

    assert stressor[0] in str(ax.title)
    assert stressor[1] in str(ax.title)
    assert "capita" in str(ax.title)

    # In the plotting method data is extracted
    # for each account from all regions. Thus
    # the order of drawn patches is for each account
    # (cba, pba, imp, exp) for each region

    assert ax.patches[0].get_height() == tt.emissions.D_cba_cap.loc[stressor, "reg1"]
    assert ax.patches[1].get_height() == tt.emissions.D_cba_cap.loc[stressor, "reg2"]
    assert ax.patches[6].get_height() == tt.emissions.D_pba_cap.loc[stressor, "reg1"]
