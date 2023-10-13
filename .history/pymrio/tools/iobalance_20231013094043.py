""""

A function for checking the balance of an IO system.

The balance is checked by:
1- Making sure that the matrix shapes are compatible 
2- Checks if total inputs = total outputs
3- Checks sector/product balance (sector/product inputs must = outputs)

"""

#%%
#import packages

import pymrio
import pandas as pd
import numpy as np


#%%

def system_is_balanced(Inter_industry: pd.DataFrame, value_added: pd.DataFrame, final_demand: pd.DataFrame, total_output:pd.DataFrame):
    """Checks if the entire system is balanced by:
    
    1) First checks the shapes and makes sure they are correct
    2) Then checks if the system is balanced
    3) The checks if sector by sector is balanced
    
    Note: It has a one percent tolerance for balance

    Parameters
    ----------
        Inter_industry: (pd.DataFrame)
            InterIndustry exchange matrix (Z)
        value_added: (pd.DataFrame) 
            Value Added vector (VA)
        final_demand: (pd.DataFrame)
            Final demand (Y)
        total_output: (pd.DataFrame)
            Total Output Vector (X)
    
    Returns:
        True: If all conditions are met
        Error: If at least one condition is not met
                  
    """
    
    #Error message for wrong matrix shape  
    class MatrixNotCompatibleError(Exception):
        def __init__(self, message="Matrix/Vector shape is not compatible with InterIndustry Matrix"):
            self.message = message
            super().__init__(self.message)

    #error message for unbalanced system
    class SystemNotBalancedError(Exception):
        def __init__(self, message="The system is not Balanced (Sum of system Inputs does not equal sum of Outputs)"):
            self.message = message
            super().__init__(self.message)            


    #error message for unbalanced sectors
    class SectorsNotBalancedError(Exception):
        def __init__(self, message="Sectors are not balanced (Sum of sector Inputs does not equal sum of Outputs)"):
            self.message = message
            super().__init__(self.message)  

    #error message for incorrect total output
    class TotalOutputError(Exception):
        def __init__(self, message="Total Output does not Equal sum of inter-industry and final demand outputs"):
            self.message = message
            super().__init__(self.message)              
              
    
    # Check shape of Inter industry is square
    if isinstance(Inter_industry, pd.DataFrame):
        num_rows_Z, num_cols_Z = Inter_industry.shape
        if num_rows_Z == num_cols_Z:
            pass
        else:
            raise NotSquareDataFrameError("Number of rows does not equal columns")
    else:
        pass
    
    #Check shape of other matrices
    
    #Value Added
    if isinstance(value_added, pd.DataFrame):
        num_rows_VA, num_cols_VA = value_added.shape
        if num_cols_VA == num_cols_Z:
            pass
        else:
            raise MatrixNotCompatibleError("Value Added shape is not compatible with InterIndustry Matrix")
    else:
        pass    
    
    #Check Final Demand
    if isinstance(final_demand, pd.DataFrame):
        num_rows_Y, num_cols_Y = final_demand.shape
        if num_rows_Y == num_rows_Z:
            pass
        else:
            raise MatrixNotCompatibleError("Final Demand shape is not compatible with InterIndustry Matrix")
    else:
        pass    
        
    
    #Check Total Output
    if isinstance(total_output, pd.DataFrame):
        num_rows_X, num_cols_X = total_output.shape
        if num_rows_X == num_rows_Z:
            pass
        else:
            raise MatrixNotCompatibleError("Total Output shape is not compatible with InterIndustry Matrix")
    else:
        pass

    print("Matrices Shapes are compatible")
    
    
    #check if total Output is the sum of Industry and final demand outputs
    for i in range(len(Inter_industry)):
        
        
        Inter_industry_sum = Inter_industry.iloc[i].sum()
        Final_demand_sum = final_demand.iloc[i].sum() 
        total= Inter_industry_sum+Final_demand_sum
        
        
        if round(total) == round(float(total_output.iloc[i])):
            pass
        else:
            raise TotalOutputError('Total output does not equal sum of intermediate and final demand consumption')
    
    #check if system totals are balanced by summing total output and value added + InterIndustry
    
    X_sum = total_output.sum(axis=0) #Total Output sum
    Z_sum_vertical = Inter_industry.sum(axis=0).sum() #Input Matrix sum (vertical sum of InterIndustry)
    VA_sum = value_added.sum(axis=0).sum() #Value Added sum
    
    Input = Z_sum_vertical + VA_sum
    Output = X_sum 
    
    #round to the nearest thousands decimal
    if (Input/Output < 1.01).all() and (Input/Output > 0.99).all():
        pass
    else:
        raise SystemNotBalancedError('The IO System is not Balanced: Sum of Inputs does not Equal sum of outputs')
    
    print('IO System is Balanced: Total Inputs equal Total Outputs')
    
    
    #check if each sector in each region is balanced
    for i in range(len(Inter_industry)):    
        
        #first check if the value added is multi-dimensional         
        if value_added.ndim> 1:
            #if yes then sum vertically and return a single dimensional array
            value_added =value_added.sum(axis=0)
        
        else:
            pass
        
        sector_Input_sum = float(Inter_industry.iloc[:, i].sum()) + float(value_added.iloc[i].sum(axis=0))
        sector_output_sum = float(total_output.iloc[i])
        
        if int(sector_output_sum) == int(sector_Input_sum):
            pass
        
        elif round(sector_output_sum) == round(sector_Input_sum):
            pass
        
        #Here I allow for a 1% difference between sector Inputs and sector outputs
        elif sector_Input_sum/sector_output_sum < 1.01 and sector_Input_sum/sector_output_sum > 0.99:
            pass
                
        else:
            print('Sector at column', i, 'is not balanced. The sum of the inputs is',sector_Input_sum,'While the sum of the outputs is',sector_output_sum ) 
            raise SectorsNotBalancedError('Sectors are not balanced: Sum of Sector Inputs does not Equal Sum of sector output')
        
    print('All Sectors are Balanced ±1 %')
    
    #if all matrices are the correct shape, total input equal total output, and sector inputs equal sector outputs
    # It returns "True"
    return True    

     

    
# %%
