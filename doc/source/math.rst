########################
Mathematical background
########################

This section gives a general overview about the mathematical background of Input-Output calculations.
For a full detail account of this matter please see 
`Miller and Blair 2009 <http://www.cambridge.org/no/academic/subjects/economics/econometrics-statistics-and-mathematical-economics/input-output-analysis-foundations-and-extensions-2nd-edition>`_


Generally, mathematical routines implemented in pymrio follow the equations described below. 
If, however, a more efficient mechanism was available this was preferred.
This was generally the case when `numpy broadcasting <https://docs.scipy.org/doc/numpy-1.13.0/user/basics.broadcasting.html>`_ 
was available for a specific operation, resulting in a substantial speed up of the calculations.
In these cases the original formula remains as comment in the source code.

Basic MRIO calculations
=======================

Core tables
------------

MRIO tables describe the global inter-industries flows within and across countries for :math:`k` countries with a transaction matrix :math:`Z`:

.. math::

    \begin{equation}
    Z = 
    \begin{pmatrix}
      Z_{1,1} & Z_{1,2} & \cdots & Z_{1,k} \\
      Z_{2,1} & Z_{2,2} & \cdots & Z_{2,k} \\
      \vdots  & \vdots  & \ddots & \vdots  \\
      Z_{k,1} & Z_{k,2} & \cdots & Z_{k,k}
    \end{pmatrix}
    \end{equation}

Each submatrix on the main diagonal (:math:`Z_{i,i}`) represents the domestic
interactions for each sector :math:`n`. The off diagonal matrices (:math:`Z_{i,j}`)
describe the trade from region :math:`i` to region :math:`j` (with :math:`i, j = 1, \ldots, k`)
for each sector. 

Global final demand can be represented by 

.. math::
    
    \begin{equation}
        Y =
        \begin{pmatrix}
          Y_{1,1} & Y_{1,2} & \cdots & Y_{1,k} \\
          Y_{2,1} & Y_{2,2} & \cdots & Y_{2,k} \\
          \vdots  & \vdots  & \ddots & \vdots  \\
          Y_{k,1} & Y_{k,2} & \cdots & Y_{k,k}
        \end{pmatrix}
    \end{equation}

with final demand satisfied by domestic production in the main diagonal
(:math:`Y_{i,i}`) and direct import to final demand from region :math:`i` to :math:`j` by
:math:`Y_{i,j}`.

Similarly, the global value-added (primary inputs) can be represented by

.. math::
    
    \begin{equation}
        v =
        \begin{pmatrix}
          V_{1} & V_{2} & \cdots & V_{k} \\
        \end{pmatrix}
    \end{equation}

with the value-added for each region :math:`i` as :math:`V_i` (with :math:`i = 1, \ldots, k`). 


The global economy can thus be described by either:

.. math::

    \begin{equation}
        x = Ze + Ye
    \end{equation}

or equivalently 

.. math::

    \begin{equation}
        x' = e'Z + v'
    \end{equation}

with :math:`e` representing the summation vector (column vector with 1's of
appropriate dimension), and the :math:`'` indicating the transpose matrix, 
and :math:`x` the total industry input/output (which are necessarily equal). 


The global multi regional IO system can be extended with various factors of
production :math:`f_{h,i}`. These can represent among others value added, employment
and social factors (:math:`h`, with :math:`h = 1, \ldots, r`) per country. The row vectors
of factors can be summarised in a factor of production matrix :math:`F`:

.. math::

    \begin{equation}
        F =
        \begin{pmatrix}
          f_{1,1} & f_{1,2} & \cdots & f_{1,k} \\
          f_{2,1} & f_{2,2} & \cdots & f_{2,k} \\
          \vdots  & \vdots  & \ddots & \vdots  \\
          f_{r,1} & f_{r,2} & \cdots & f_{r,k}
        \end{pmatrix}
    \end{equation}

with the factor of production coefficients :math:`S` given by

.. math::

    \begin{equation}
        S = F\hat{x}^{-1}
    \end{equation}

If the factor of production represent required environmental impacts, these can
also occur during the final use phase. In that case :math:`F_Y` describe the impacts
associated with final demand (e.g. household emissions).


Leontief demand model
---------------------

The Leontief demand model assumes that final demand drives economic production and environmental impacts.

To derive the model, one must first calculate the direct input requirement matrix :math:`A`.
It is given by multiplication of :math:`Z` with the
diagonalised and inverted industry output :math:`x`:

.. math::

    \begin{equation}
        A = Z\hat{x}^{-1}
    \end{equation}

Based on the linear economy assumption of the IO model and 
the classic Leontief_ demand-style modeling 
(see `Leontief 1970 <https://www.jstor.org/stable/1926294?seq=1#page_scan_tab_contents>`_), 
total industry output :math:`x` can be calculated for any arbitrary vector of 
final demand :math:`y` by multiplying with the total requirement matrix (Leontief matrix) :math:`L`. 

.. _Leontief: https://en.wikipedia.org/wiki/Wassily_Leontief

.. math::

    \begin{equation}
        x = (\mathrm{I}- A)^{-1}y = Ly 
    \end{equation}

with :math:`\mathrm{I}` defined as the identity matrix with the size of :math:`A`.


Leontief multipliers (total direct and indirect output needed in each sector to satisfy one unit of final demand) are then obtained by

.. math::
    
    \begin{equation}
        M = SL
    \end{equation}

If one wants to only extract the indirect output needed, one can calculate it as:
.. math::
    
    \begin{equation}
        M_{Leontief indirect} = S ( L - I ) = M - S
    \end{equation}

Total requirements (footprints in case of environmental requirements) 
for any given final demand vector :math:`y` are then given by 

.. math::

    \begin{equation}
        D_{cba} = My
    \end{equation}

Setting the domestically satisfied final demand :math:`Y_{i,i}` to zero (:math:`Y_{t} = Y -
Y_{i,j}\; |\; i = j`) allows to calculate the factor of production occurring
abroad (embodied in imports)

.. math::

    \begin{equation}
        D_{imp} = SLY_{t}
    \end{equation}

The factors of production occurring domestically to satisfy final demand in
other countries is given by:

.. math::

    \begin{equation}
        D_{exp} = S\widehat{LY_{t}e}
    \end{equation}

with the hat indicating diagonalization of the resulting column-vector of the term underneath.



Ghosh supply model
---------------------

The Ghosh supply model assumes that primary inputs (value-added) drives economic production and environmental impacts.
See `Ghosh Model <https://www.openriskmanual.org/wiki/Ghosh_Model>`_ for more information.

To derive the model, one must first calculate the direct output requirement matrix :math:`B`.
It is given by multiplication of the diagonalised 
and inverted industry output :math:`x`: with :math:`Z`

.. math::

    \begin{equation}
        B = \hat{x}^{-1} Z
    \end{equation}


Similarly, the Ghosh inverse matrix :math:`G` is defined as the inverse of the identity matrix minus the output requirement matrix :math:`B`

.. math::

    \begin{equation}
        G = (\mathrm{I}- B)^{-1} = \hat{x} L \hat{x}^{-1}
    \end{equation}

with :math:`\mathrm{I}` defined as the identity matrix with the size of :math:`B`.

Ghosh multipliers (total direct and indirect outputs generated in response to one unit of value-added supplied to a sector) are then obtained by

.. math::
    
    \begin{equation}
        M_{Ghosh} = G S
    \end{equation}

If one wants to only extract the indirect output generated in response to one unit of value-added supplied to a sector, one can calculate it as:
.. math::
    
    \begin{equation}
        M_{Ghosh indirect} = S ( G - I ) = M_{Ghosh} - S
    \end{equation}

Total requirements for any given value added vector :math:`v` are then given by 

.. math::

    \begin{equation}
        D_{iba} = v M_{Ghosh}
    \end{equation}



Production-, Consumption-, and Income-based accounting
======================================================

Production-based accounts (direct territorial requirements) per region `i` are therefore given by summing over the stressors per sector (0 ... `m`) 
plus the stressors occurring due to the final consumption for all final demand categories (0 ... `w`) of that region.

.. math::

   \begin{equation}
        D_{pba}^i = \sum_{s=0}^m F^i_s + \sum_{c=0}^w F^i_{Yc}
   \end{equation}

Consumption-based per region `i` are given by summing the total requirements (footprints) 
as calculated by the Leontief demand model and adding the aggregated final demand stressors.

.. math::

   \begin{equation}
        D_{cba}^i = \sum_{s=0}^m D_{cba, s}^{i} + \sum_{c=0}^w F_{Yc}^i
   \end{equation}

Income-based accounts are given by summing the total requirements (footprints)
as calculated by the Ghosh supply (cost-push) model and adding the aggregated final demand stressors.

.. math::

   \begin{equation}
        D_{iba}^i = \sum_{s=0}^m D_{iba, s}^{i} + \sum_{c=0}^w F_{Yc}^i
   \end{equation}


Internally, the summation are implemented with the `group-by <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.groupby.html>`_ functionality provided by the pandas package.


Aggregation
===========

For the aggregation of the MRIO system the matrix :math:`B_k` defines
the aggregation matrix for regions and :math:`B_n` the aggregation matrix
for sectors.

.. math::

    \begin{equation}
        B_k =
        \begin{pmatrix}
          b_{1,1} & b_{1,2} & \cdots & b_{1,k} \\
          b_{2,1} & b_{2,2} & \cdots & b_{2,k} \\
          \vdots  & \vdots  & \ddots & \vdots  \\
          b_{w,1} & b_{w,2} & \cdots & b_{w,k}
        \end{pmatrix}
        B_n =
        \begin{pmatrix}
          b_{1,1} & b_{1,2} & \cdots & b_{1,n} \\
          b_{2,1} & b_{2,2} & \cdots & b_{2,n} \\
          \vdots  & \vdots  & \ddots & \vdots  \\
          b_{x,1} & b_{x,2} & \cdots & b_{x,n}
        \end{pmatrix}
    \end{equation}

With :math:`w` and :math:`x` defining the aggregated number of countries and sectors,
respectively. Entries :math:`b` are set to 1 if the sector/country of the column
belong to the aggregated sector/region in the corresponding row and zero
otherwise. The complete aggregation matrix :math:`B` is given by 
the `Kronecker product <https://en.wikipedia.org/wiki/Kronecker_product>`_ 
:math:`\otimes` of :math:`B_k` and :math:`B_n`:

.. math::

    \begin{equation}
        B = B_k \otimes B_n
    \end{equation}

This effectively arranges the sector aggregation matrix :math:`B_n` as defined by the 
region aggregation matrix :math:`B_k`. Thus, for each 0 entry in :math:`B_k` a block
:math:`B_n * 0` is inserted in :math:`B` and each 1 corresponds to :math:`B_n * 1` in :math:`B`.


The aggregated IO system can then be obtained by

.. math::

    \begin{equation}
        Z_{agg} = BZB^\mathrm{T} 
    \end{equation}

and

.. math::

    \begin{equation}
        Y_{agg} = BY(B_k \otimes \mathrm{I})^\mathrm{T}
    \end{equation}

with :math:`\mathrm{I}` defined as the identity matrix with the size equal to the number of final demand
categories per country.

Factors of production are aggregated by

.. math::

    \begin{equation}
        F_{agg} = FB^\mathrm{T} 
    \end{equation}

and final demand impacts by

.. math::

    \begin{equation}
        F_{Y, agg} = F_Y(B_k \otimes \mathrm{I})^\mathrm{T}
    \end{equation}
