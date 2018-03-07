""" Testing core functionality of pymrio
"""

import sys
import os

_pymriopath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _pymriopath + '/../../')

import pymrio  # noqa


def test_get_index():
    tt = pymrio.load_test()
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
