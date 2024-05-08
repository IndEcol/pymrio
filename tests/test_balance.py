""" Testing functions for the full run based on
the small MRIO given within pymrio.

This tests the IO balance function 

"""

#%%%

#import packages
import numpy as np
import pandas as pd
import pytest

import os
import sys
TESTPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(TESTPATH, ".."))


from pymrio.tools.iobalance import system_is_balanced

#%%
#Tests if output for balanced mrio is true
def test_balanced_mock_mrio():
    """
    Test the if mock MRIO is balanced
    
    """
    #Define data
    z_data = [
    [1, 2, 1],
    [2, 1, 1],
    [1, 1, 2]
    ]

    #final demand
    y_data =  [
        [0.5,0.5],
        [0.5,0.5],
        [0.5,0.5]
    ]
    #Value Added
    va_data = [
        [0.5,0.5,0.5],
        [0.5,0.5,0.5],
        [0,0,0]
    ]
    #total output
    x_data =  [
        [5],
        [5],
        [5]
    ]

    balanced_z = pd.DataFrame(z_data, index = ['Sector1','Sector2','Sector3'],
        columns= ['Sector1','Sector2','Sector3'],dtype=float) 

    balanced_y = pd.DataFrame(y_data, index = ['Sector1','Sector2','Sector3'],columns= ['Final Demand_1','Final_Demand_2'],dtype=float)

    balanced_va = pd.DataFrame(va_data, index = ['Value Added_1','Value Added_2','Value Added_2'],columns= ['Sector1','Sector2','Sector3'],dtype=float)

    balanced_x = pd.DataFrame(x_data, index = ['Sector1','Sector2','Sector3'],columns= ['Total Output'],dtype=float)
    
    
    assert system_is_balanced(balanced_z,balanced_va,balanced_y,balanced_x) == True


#%%    
#Tests that unbalanced mock MRIO is not True 


def test_unbalanced_mock_mrio():
    """
    Test the if mock MRIO is balanced
    
    """
    #Define data
    z_data = [
    [1, 2, 1],
    [2, 1, 2],
    [1, 1, 2]
    ]

    #final demand
    y_data =  [
        [0.5,0.5],
        [0.5,0.5],
        [0.5,0.5]
    ]
    #Value Added
    va_data = [
        [0.5,0.5,0.5],
        [0.5,1,0.5],
        [0,0,0]
    ]
    #total output
    x_data =  [
        [5],
        [6],
        [5]
    ]

    unbalanced_z = pd.DataFrame(z_data, index = ['Sector1','Sector2','Sector3'],
        columns= ['Sector1','Sector2','Sector3'],dtype=float) 

    unbalanced_y = pd.DataFrame(y_data, index = ['Sector1','Sector2','Sector3'],columns= ['Final Demand_1','Final_Demand_2'],dtype=float)

    unbalanced_va = pd.DataFrame(va_data, index = ['Value Added_1','Value Added_2','Value Added_2'],columns= ['Sector1','Sector2','Sector3'],dtype=float)

    unbalanced_x = pd.DataFrame(x_data, index = ['Sector1','Sector2','Sector3'],columns= ['Total Output'],dtype=float)
    
    assert not system_is_balanced(unbalanced_z,unbalanced_va,unbalanced_y,unbalanced_x) == True

test_unbalanced_mock_mrio()    
# %%
