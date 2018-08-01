""" Testing core functionality of pymrio
"""

import sys
import os
import pytest

_pymriopath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _pymriopath + '/../../')

import pymrio  # noqa


@pytest.fixture()
def fix_testmrio():
    """ Single point to load the test mrio
    """
    class TestMRIO:
        testmrio = pymrio.load_test()
        sectors = ['food',
                   'mining',
                   'manufactoring',
                   'electricity',
                   'construction',
                   'trade',
                   'transport',
                   'other']
        regions = ['reg1', 'reg2', 'reg3', 'reg4', 'reg5', 'reg6']

    return TestMRIO


def test_copy(fix_testmrio):
    """ Testing the deep copy functionality + naming
    """
    tt = fix_testmrio.testmrio
    tt_copy = tt.copy()
    assert tt_copy.name == tt.name + '_copy'
    assert all(tt_copy.Z == tt.Z)
    assert all(tt_copy.emissions.F == tt.emissions.F)
    tt_copy.emissions.F = tt_copy.emissions.F + 2
    tt_copy.Z = tt_copy.Z + 2
    assert all(tt_copy.Z != tt.Z)
    assert all(tt_copy.emissions.F != tt.emissions.F)
    tt_new = tt.copy('new')
    assert tt_new.name == 'new'
    e_new = tt.emissions.copy('new')
    assert e_new.name == 'new'


def test_get_index(fix_testmrio):
    """ Testing the different options for get_index in core.mriosystem
    """
    tt = fix_testmrio.testmrio
    assert all(tt.emissions.F.index == tt.emissions.get_index(as_dict=False))

    F_dict = {ki: ki for ki in tt.emissions.F.index}
    idx_dict = {ki: ki for ki in tt.emissions.get_index(as_dict=True)}
    assert F_dict == idx_dict

    pat1 = {('emis.*', 'air'): ('emission alternative', 'air')}
    pat1index = tt.emissions.get_index(as_dict=True,
                                       grouping_pattern=pat1)
    assert pat1index[tt.emissions.F.index[0]] == list(pat1.values())[0]
    assert pat1index[tt.emissions.F.index[1]] == tt.emissions.F.index[1]

    pat2 = {('emis.*', '.*'): 'r'}

    pat2index = tt.emissions.get_index(as_dict=True,
                                       grouping_pattern=pat2)
    assert all([True if v == 'r' else False for v in pat2index.values()])

    # test one level index

    # pat_single_tpl = {('Value Added',): 'va'}
    pat_single_str = {'Value Added': 'va'}
    pat_single_index = tt.factor_inputs.get_index(
        as_dict=True, grouping_pattern=pat_single_str)
    assert pat_single_str == pat_single_index


def test_set_index(fix_testmrio):
    tt = fix_testmrio.testmrio
    new_index = ['a', 'b']
    tt.emissions.set_index(new_index)
    assert tt.emissions.get_index()[0] == new_index[0]
    assert tt.emissions.get_index()[1] == new_index[1]


def test_get_sectors(fix_testmrio):
    assert list(fix_testmrio.testmrio.get_sectors()) == fix_testmrio.sectors
    assert fix_testmrio.testmrio.get_sectors(
        ['construction', 'food', 'a'])[
            fix_testmrio.sectors.index('construction')] == 'construction'
    assert fix_testmrio.testmrio.get_sectors(
        ['construction', 'food', 'a'])[
            fix_testmrio.sectors.index('food')] == 'food'
    assert fix_testmrio.testmrio.get_sectors(
        ['construction', 'food', 'a'])[1] == None  # noqa


def test_get_regions(fix_testmrio):
    assert list(fix_testmrio.testmrio.get_regions()) == fix_testmrio.regions


def test_copy_and_extensions(fix_testmrio):
    tcp = fix_testmrio.testmrio.copy()
    tcp.remove_extension(tcp.get_extensions())
    assert len(list(tcp.get_extensions())) == 0
    assert len(list(
        fix_testmrio.testmrio.get_extensions())) == 2


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


def test_reset_to_coefficients(fix_testmrio):
    tt = fix_testmrio.testmrio
    tt.calc_all()
    tt.reset_all_to_coefficients()
    assert tt.Z is None
    assert tt.emissions.F is None
