""" Tests the parsing of different MRIOs """

import os
import sys

import pytest

testpath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, testpath + '/../../')

import pymrio  # noqa


def test_parse_eora26():
    eoramockpath = os.path.join(
        testpath, 'mock_mrios', 'eora26_mock')

    test = pymrio.load_test()
    eora_short = pymrio.parse_eora26(eoramockpath, year=2010)
    eora_full = pymrio.parse_eora26(eoramockpath, year=2010,
                                    country_names='full')

    test.calc_all()
    eora_short.calc_all()

    assert (test.emissions.D_cba.iloc[1, 1] ==
            eora_short.Q.D_cba.iloc[1, 1])

    assert eora_short.get_regions()[0] == 'reg1'
    assert eora_full.get_regions()[0] == 'Region 1'

    with pytest.raises(pymrio.ParserError):
        eora_fail = pymrio.parse_eora26(eoramockpath, year=2010,
                                        country_names='bogus')
