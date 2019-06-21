""" Tests the parsing of different MRIOs """

import os
import sys

import pandas.util.testing as pdt
import pytest

import numpy as np

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
        _ = pymrio.parse_exiobase1('foo')


def test_parse_exio2(fix_testmrio_calc):
    exio2_mockpath = os.path.join(testpath, 'mock_mrios', 'exio2_mock',
                                  'mrIOT_PxP_ita_coefficient_version2.2.2.zip')

    test_mrio = fix_testmrio_calc.testmrio

    exio2 = pymrio.parse_exiobase2(exio2_mockpath, popvector=None)
    exio2.calc_all()

    assert (test_mrio.emissions.S.iloc[1, 1] ==
            pytest.approx(exio2.emissions.S.iloc[1, 1]))

    assert (test_mrio.emissions.D_cba.iloc[0, 5] ==
            pytest.approx(exio2.emissions.D_cba.iloc[0, 5]))

    pdt.assert_series_equal(
        exio2.impact.D_cba.loc['total emissions'],
        test_mrio.emissions.D_cba.sum(axis=0), check_names=False)

    assert exio2.get_regions()[0] == 'reg1'

    with pytest.raises(pymrio.ParserError):
        _ = pymrio.parse_exiobase2('foo')

    with pytest.raises(pymrio.ParserError):
        _ = pymrio.parse_exiobase2('foo.zip')


def test_parse_exio3(fix_testmrio_calc):
    exio3_mockpath = os.path.join(testpath, 'mock_mrios', 'exio3_mock')

    test_mrio = fix_testmrio_calc.testmrio

    exio3 = pymrio.parse_exiobase3(exio3_mockpath)
    exio3.calc_all()

    assert np.allclose(exio3.A, test_mrio.A)
    assert np.allclose(exio3.satellite.D_cba,
                       test_mrio.emissions.D_cba)

    # Test the renaming of the regions - depends on the correct pseudo
    # naming in the mock mrio
    assert list(exio3.get_regions()) == ['AU', 'BR', 'FI', 'FR', 'KR', 'WF']


def test_parse_exio_ext():

    ext_mockpath = os.path.join(testpath, 'mock_mrios', 'exio_ext_mock')
    col5 = os.path.join(ext_mockpath, 'ext_5col.txt')
    col3 = os.path.join(ext_mockpath, 'ext_3col.txt')
    col2 = os.path.join(ext_mockpath, 'ext_2col.txt')
    col1 = os.path.join(ext_mockpath, 'ext_1col.txt')

    ext5 = pymrio.parse_exio12_ext(col5, index_col=5, name='col5',
                                   sep='\t', drop_compartment=True)
    ext3 = pymrio.parse_exio12_ext(col3, index_col=3, name='col3',
                                   sep='\t', drop_compartment=True)
    ext2 = pymrio.parse_exio12_ext(col2, index_col=2, name='col2',
                                   sep='\t', drop_compartment=True)
    ext1 = pymrio.parse_exio12_ext(col1, index_col=1, name='col1',
                                   sep='\t', drop_compartment=True)
    ext5_wcmp = pymrio.parse_exio12_ext(col5, index_col=5, name='col5',
                                        sep='\t', drop_compartment=False)
    ext3_wcmp = pymrio.parse_exio12_ext(col3, index_col=3, name='col3',
                                        sep='\t', drop_compartment=False)
    ext2_wcmp = pymrio.parse_exio12_ext(col2, index_col=2, name='col2',
                                        sep='\t', drop_compartment=False)
    ext1_wcmp = pymrio.parse_exio12_ext(col1, index_col=1, name='col1',
                                        sep='\t', drop_compartment=False)

    assert np.allclose(ext5.F, ext3.F, ext2.F, ext1.F, ext5_wcmp.F)

    assert ext5.F.iloc[1, 1] == 102
    assert ext5.F.iloc[-1, -1] == 148

    assert ext2.name == 'col2'

    assert ext1.unit is None
    assert ext1_wcmp.unit is None
    assert ext5_wcmp.unit.iloc[0, 0] == 'kg'
    assert ext3.unit.iloc[1, 0] == 'kg'

    assert ext5.F.index.name == 'stressor'
    assert list(ext5_wcmp.F.index.names) == ['stressor', 'compartment']
    assert list(ext3_wcmp.F.index.names) == ['stressor', 'compartment']
    assert ext2_wcmp.F.index.name == 'stressor'


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
        eora_fail = pymrio.parse_eora26(eora_mockpath, year=2010,
                                        country_names='bogus')
