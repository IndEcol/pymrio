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
    mr = pymrio.load_test()
    mr.calc_all()
    npt.assert_allclose(
            td_testmrio.factor_inputs.D_imp_values,
            mr.factor_inputs.D_imp_reg.values,
            rtol=1e-5
            )


def test_fileio(tmpdir):
    """ Round trip with saving and loading the testmrio
    """
    mr = pymrio.load_test()
    save_path = str(tmpdir.mkdir('pymrio_test'))
    mr.save_all(save_path)
    mr2 = pymrio.load_all(save_path)
    npt.assert_allclose(
            mr.Z.values,
            mr2.Z.values,
            rtol=1e-5
            )
