""""

A function for checking the balance of an IO system.

The balance is checked by:
1- Making sure that the matrix shapes are compatible 
2- Checks if total inputs = total outputs (Given tolerance)
3- Checks sector/product balance (sector/product inputs must = outputs)

"""

# %%
# import packages

import numpy as np
import pandas as pd

# Error message for wrong matrix shape
class MatrixNotCompatibleError(Exception):
    """ Error when sum of the matrix shapes are not compatible"""
    def __init__(
        self, message="Matrix/Vector shape is not compatible with InterIndustry Matrix"
    ):
        self.message = message
        super().__init__(self.message)

# error message for unbalanced system
class SystemNotBalancedError(Exception):
    """ Error when sum of the system input and outputs are not equal"""
    def __init__(
        self,
        message="The system is not Balanced (Sum of system Inputs does not equal sum of Outputs)",
    ):
        self.message = message
        super().__init__(self.message)


# error message for unbalanced sectors
class SectorsNotBalancedError(Exception):
    """Error for when sector inputs do not equal outputs    """
    def __init__(
        self,
        message="Sectors are not balanced (Sum of sector Inputs does not equal sum of Outputs)",
    ):
        self.message = message
        super().__init__(self.message)


# error message for incorrect total output
class TotalOutputError(Exception):
    """Error for when total output does not equal sum of inter-industry and final demand"""
    def __init__(
        self,
        message="Total Output does not Equal sum of inter-industry and final demand outputs",
    ):
        self.message = message
        super().__init__(self.message)


# %%

def system_is_balanced(
    Z: pd.DataFrame, VA: pd.DataFrame, Y: pd.DataFrame, x: pd.DataFrame, tolerance=0.01
):
    """Checks if the entire system is balanced by:

    1) First checks the shapes and makes sure they are correct
    2) Then checks if the system is balanced
    3) The checks if sector by sector is balanced

    Note: It has a one percent tolerance for balance

    Parameters
    ----------
        Z: (pd.DataFrame)
            InterIndustry exchange matrix (Z)
        VA: (pd.DataFrame)
            Value Added vector (VA)
        Y: (pd.DataFrame)
            Final demand (Y)
        x: (pd.DataFrame)
            Total Output Vector (X)
        tolerance:
            sets tolerance for IO balance checks; defaults to 1%

    Returns:
        True: If all conditions are met
        Error: If at least one condition is not met

    """
   # Check shape of Inter industry is square
    if isinstance(Z, pd.DataFrame):
        num_rows_z, num_cols_z = Z.shape
        if num_rows_z == num_cols_z:
            pass
        else:
            raise NotSquareDataFrameError("Number of rows does not equal columns")
    else:
        pass

    # Check shape of other matrices

    # Value Added
    if isinstance(VA, pd.DataFrame):
        num_rows_va, num_cols_va = VA.shape
        if num_cols_va == num_cols_z:
            pass
        else:
            raise MatrixNotCompatibleError(
                "Value Added shape is not compatible with InterIndustry Matrix"
            )
    else:
        pass

    # Check Final Demand
    if isinstance(Y, pd.DataFrame):
        num_rows_y, num_cols_y = Y.shape
        if num_rows_y == num_rows_z:
            pass
        else:
            raise MatrixNotCompatibleError(
                "Final Demand shape is not compatible with InterIndustry Matrix"
            )
    else:
        pass

    # Check Total Output
    if isinstance(x, pd.DataFrame):
        num_rows_x, num_cols_x = x.shape
        if num_rows_x == num_rows_z:
            pass
        else:
            raise MatrixNotCompatibleError(
                "Total Output shape is not compatible with InterIndustry Matrix"
            )
    else:
        pass

    # check if total Output is the sum of Industry and final demand outputs
    for i in range(len(Z)):
        inter_industry_sum = Z.iloc[i].sum()
        final_demand_sum = Y.iloc[i].sum()
        total = inter_industry_sum + final_demand_sum

        if np.isclose(total, float(x.iloc[i]), atol=tolerance):
            pass
        else:
            raise TotalOutputError(
                "Total output does not equal sum of intermediate and final demand consumption"
            )

    # check if system totals are balanced by summing total output and value added + InterIndustry

    x_sum = x.sum(axis=0)  # Total Output sum
    z_sum_vertical = Z.sum(
        axis=0
    ).sum()  # Input Matrix sum (vertical sum of InterIndustry)
    va_sum = VA.sum(axis=0).sum()  # Value Added sum

    input = z_sum_vertical + va_sum
    output = x_sum

    # round to the nearest thousands decimal
    if np.isclose(input, output, atol=tolerance):
        pass
    else:
        raise SystemNotBalancedError(
            "The IO System is not Balanced: Sum of Inputs does not Equal sum of outputs"
        )

    # check if each sector in each region is balanced
    for i in range(len(Z)):
        # first check if the value added is multi-dimensional
        if VA.ndim > 1:
            # if yes then sum vertically and return a single dimensional array
            VA = VA.sum(axis=0)

        else:
            pass

        sector_input_sum = float(Z.iloc[:, i].sum()) + float(VA.iloc[i].sum(axis=0))
        sector_output_sum = float(x.iloc[i])

        if np.isclose(sector_input_sum, sector_output_sum, atol=tolerance):
            pass

        else:
            raise SectorsNotBalancedError(
                "Sectors are not balanced: Sum of Sector Inputs does not Equal Sum of sector output"
            )

    # if all matrices are the correct shape, total input equal total output, and sector inputs equal sector outputs
    # It returns "True"
    return True


# %%
