""" Testing functions for the full run based on
the small MRIO given within pymrio.

This tests the full computation and fileio.

Might be the slowest test to run - make optional if it takes to long.
"""

import sys
import os
import numpy as np
import pytest
import numpy.testing as npt

_pymriopath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _pymriopath + '/../../')

import pymrio  # noqa


@pytest.fixture()
def td_testmrio():
    """ Results from the test mrio calculation.

    This works with the test system given in pymrio.

    """
    class results():
        class factor_inputs():
            D_imp_values = np.array([
                    [2382767.5387909594, 2393134.584113787, 2972317.803194902, 4201655.226133792, 1428782.8385865367, 6693276.934870526]  # noqa
                    ]
                    )
    return results


def test_all(td_testmrio):
    """ Full integration test

    Checks:
    1) the cba calculation
    2) concate extension
    """
    mr = pymrio.load_test()
    mr.calc_all()
    npt.assert_allclose(
            td_testmrio.factor_inputs.D_imp_values,
            mr.factor_inputs.D_imp_reg.values,
            rtol=1e-5
            )
    sat_new = pymrio.concate_extension(mr.emissions,
                                       mr.factor_inputs,
                                       name='sat_new')

    assert len(sat_new.D_cba) == 3
    assert mr.emissions.F.index[0] in sat_new.F.index
    assert mr.factor_inputs.F.index[0] in sat_new.FY.index
    assert all(mr.emissions.get_regions() == sat_new.get_regions())
    assert all(mr.emissions.get_sectors() == sat_new.get_sectors())


def test_fileio(tmpdir):
    """ Round trip with saving and loading the testmrio

    Also tests some fileio related util functions
    """
    mr = pymrio.load_test()

    save_path = str(tmpdir.mkdir('pymrio_test'))
    mr.save_all(save_path)

    # Testing getting the repo content, some random sample test
    fc = pymrio.get_repo_content(save_path)
    assert fc.iszip is False
    assert 'Z.txt' in [os.path.basename(f) for f in fc.filelist]
    assert 'FY.txt' in [os.path.basename(f) for f in fc.filelist]
    assert 'unit.txt' in [os.path.basename(f) for f in fc.filelist]

    mr2 = pymrio.load_all(save_path)
    npt.assert_allclose(mr.Z.values, mr2.Z.values, rtol=1e-5)

    # Testing the zip archive functions
    zip_arc = os.path.join(save_path, 'test_mrio.zip')
    if os.path.exists(zip_arc):
        os.remove(zip_arc)
    pymrio.archive(
        source=save_path,
        archive=zip_arc,
        remove_source=False,
        path_in_arc='test')

    emissions = pymrio.load(zip_arc, path_in_arc='test/emissions')
    npt.assert_allclose(mr.emissions.F.values, emissions.F.values, rtol=1e-5)

    mr3 = pymrio.load_all(zip_arc)
    npt.assert_allclose(mr.Z.values, mr3.Z.values, rtol=1e-5)
