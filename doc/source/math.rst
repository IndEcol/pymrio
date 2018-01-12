########################
Mathematical background
########################

This section gives a general overview about the mathematical background of Input-Output calculations.
For a full detail account of this matter please see 
`Miller and Blair 2009 <http://www.cambridge.org/no/academic/subjects/economics/econometrics-statistics-and-mathematical-economics/input-output-analysis-foundations-and-extensions-2nd-edition>`_


Generally, mathematical routines implemented in pymrio follow the equations described below. 
If, however, a more efficient mechanism was available this was prefered.
This was generally the case when `numpy broadcasting <https://docs.scipy.org/doc/numpy-1.13.0/user/basics.broadcasting.html>`_ 
was available for a specific operation, resulting in a substaintal speed up of the calculations.
In this cases the original formula remains as comment in the source code.

Basic MRIO calculations
------------------------

MRIO tables desribe the global interindustries flows within and across countries for :math:`k` countries with a transaction matrix :math:`Z`:

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

Each submatrix on the main diagonal (:math:`Z_{i,i}`) represent the domestic
interactions for each industry :math:`n`. The off diagonal matrices (:math:`Z_{i,j}`)
describe the trade from region :math:`i` to region :math:`j` (with :math:`i, j = 1, \ldots, k`)
for each industry. Accordingly, global final demand can be represented by 

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
(:math:`Y_{i,i}`) and direct import to final demand from country :math:`i` to :math:`j` by
:math:`Y_{i,j}`.

The global economy can thus be described by:

.. math::

    \begin{equation}
        x = Ze + Ye
    \end{equation}

with :math:`e` representing the summation vector (column vector with 1's of
appropriate dimension) and :math:`x` the total industry output. 

The direct requirement matrix :math:`A` is given by multiplication of :math:`Z` with the
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
also occur during the final use phase. In that case :math:`G` describe the impacts
associated with final demand.

The production based accounts (direct territorial requirements) per country are than given by: 

.. math::

    \begin{equation}
        D_{pba} = Fe + Ge
    \end{equation}

Multipliers for :math:`F` are obtained by

.. math::
    
    \begin{equation}
        M = SL
    \end{equation}

Total requirements (footprints in case of environmental requirements) for any
given final demand vector :math:`y` are than given by 

.. math::

    \begin{equation}
        D_{cba} = My
    \end{equation}

Setting the domestically satisfied final demand :math:`Y_{i,i}` to zero (:math:`Y_{t} = Y -
Y_{i,j}\; |\; i = j`) allow to calculate the factor of production occurring
abroad (embodied in imports)

.. math::

    \begin{equation}
        D_{imp} = SMY_{t}
    \end{equation}

The factors of production occurring domestically to satisfy final demand in
other countries is given by:

.. math::

    \begin{equation}
        D_{exp} = S\widehat{MY_{t}e}
    \end{equation}

The total requirement for each country can be obtained by summing over the
sectors for each account (:math:`D_{cba}`, :math:`D_{imp}` and :math:`D_{exp}`).  In case of
:math:`D_{cba}` any impacts associated with the use (:math:`G`) must be added.  Using that
approach, footprints for each country :math:`i` satisfy:

.. math::

    \begin{equation}
        D_{cba}^i = D_{pba}^i + D_{imp}^i  - D_{exp}^i
    \end{equation}

Aggregation
------------

For the aggregation of the MRIO system the matrix :math:`S_k` defines
the aggregation matrix for regions and :math:`S_n` the aggregation matrix
for sectors.

.. math::

    \begin{equation}
        S_k =
        \begin{pmatrix}
          b_{1,1} & b_{1,2} & \cdots & b_{1,k} \\
          b_{2,1} & b_{2,2} & \cdots & b_{2,k} \\
          \vdots  & \vdots  & \ddots & \vdots  \\
          b_{w,1} & b_{w,2} & \cdots & b_{w,k}
        \end{pmatrix}
        S_n =
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
otherwise. The complete aggregation matrix :math:`S` is given by 
the `Kronecker product <https://en.wikipedia.org/wiki/Kronecker_product>`_ 
:math:`\otimes` of :math:`S_k` and :math:`S_n`:

.. math::

    \begin{equation}
        S = S_k \otimes S_n
    \end{equation}

The aggregated IO system can than be obtained by

.. math::

    \begin{equation}
        Z_{agg} = SZS^\mathrm{T} 
    \end{equation}

and

.. math::

    \begin{equation}
        Y_{agg} = SY(S_k \otimes \mathrm{I})^\mathrm{T}
    \end{equation}

with :math:`\mathrm{I}` defined as the identity matrix with the size the final demand
categories per country.

Factor of production are aggregated by

.. math::

    \begin{equation}
        F_{agg} = FS^\mathrm{T} 
    \end{equation}

and final demand impacts by

.. math::

    \begin{equation}
        G_{agg} = G(S_k \otimes \mathrm{I})^\mathrm{T}
    \end{equation}

    

