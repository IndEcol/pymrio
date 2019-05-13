""" Tests the parsing of different MRIOs """

import os
import sys
import pytest

import pytest

testpath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, testpath + '/../../')

import pymrio  # noqa


@pytest.fixture()
def fix_testmrio_calc():
    """ Single point to load the test mrio
    """
    class TestMRIO:
        testmrio = pymrio.load_test().calc_all()

    return TestMRIO


def test_parse_exio1(fix_testmrio_calc):
    exio1_mockpath = os.path.join(
        testpath, 'mock_mrios', 'exio1_mock')

    test_mrio = fix_testmrio_calc.testmrio

    exio1 = pymrio.parse_exiobase1(exio1_mockpath)
    exio1.calc_all()

    assert (test_mrio.emissions.S.iloc[1, 1] ==
            pytest.approx(exio1.emissions.S.iloc[1, 1]))

    assert (test_mrio.emissions.D_cba.iloc[0, 5] ==
            pytest.approx(exio1.emissions.D_cba.iloc[0, 5]))

    assert exio1.get_regions()[0] == 'reg1'

    with pytest.raises(pymrio.ParserError):
        exio_fail = pymrio.parse_exiobase1('foo')


def test_parse_eora26(fix_testmrio_calc):
    eora_mockpath = os.path.join(
        testpath, 'mock_mrios', 'eora26_mock')

    test_mrio = fix_testmrio_calc.testmrio

    eora_short = pymrio.parse_eora26(eora_mockpath, year=2010)
    eora_full = pymrio.parse_eora26(eora_mockpath, year=2010,
                                    country_names='full')

    eora_short.calc_all()

    assert (test_mrio.emissions.D_cba.iloc[1, 1] ==
            pytest.approx(eora_short.Q.D_cba.iloc[1, 1]))

    assert eora_short.get_regions()[0] == 'reg1'
    assert eora_full.get_regions()[0] == 'Region 1'

    with pytest.raises(pymrio.ParserError):
        eora_fail = pymrio.parse_eora26(eoramockpath, year=2010,
                                        country_names='bogus')
