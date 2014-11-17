""" Testing functions for the full run based on 
the small MRIO given within pymrio. These can potentially
take longer than the specific unit tests. Because of the file
name these test only run when specifically called with

py.test full_run.py

TODO: This is work in progress. Testing function here should
include

- calculations
- aggregation
- load from txt,pickle
- save from txt,pickle

"""

import sys, os
import numpy as np
import pandas as pd
import pytest
import numpy.testing as npt
import pandas.util.testing as pdt

_pymriopath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _pymriopath + '/../../')

import pymrio

@pytest.fixture()
def td_testmrio():
    """ Results from the test mrio calculation.
    
    This works with the test system given in pymrio.
    
    """
    class results():
        class factor_inputs():
            D_imp_values = np.array([
                    [2382767.5387909594,2393134.584113787,2972317.803194902,4201655.226133792,1428782.8385865367,6693276.934870526]
                    ]
                    )
    return results

def test_all(td_testmrio):
    mr = pymrio.load_test()
    mr.calc_all()
    npt.assert_allclose(
            td_testmrio.factor_inputs.D_imp_values,
            mr.factor_inputs.D_imp_reg.values,
            rtol = 1e-5
            )

