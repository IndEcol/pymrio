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

When both operands have pandas labels, the mathematical routines align their
corresponding rows or columns before calculation. Matching labels may appear in
different orders, but missing, extra, or duplicate labels raise a ``ValueError``
where an alignment would otherwise be ambiguous. NumPy inputs have no labels and
are matched by position, so their ordering must be consistent.

Basic MRIO calculations
------------------------

For the expansion of production footprints into individual supply-chain paths,
see :doc:`structural_path_analysis`.

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


Multipliers (total, direct and indirect, requirement factors for one unit of output) are then obtained by

.. math::
    
    \begin{equation}
        M = SL
    \end{equation}

Total requirements (footprints in case of environmental requirements) for any
given final demand vector :math:`y` are then given by 

.. math::

    \begin{equation}
        D_{cba} = My
    \end{equation}

To attribute impacts to individual demanded sectors, :func:`pymrio.calc_accounts`
first aggregates final-demand categories to one column per consuming country.
It then disaggregates each column by sector into :math:`\widetilde{Y}`: each
resulting column contains the demand for one sector in one consuming country.
The output required throughout the supply chain is

.. math::

    X = L\widetilde{Y}.

The block :math:`X_{i,j}` contains production in country :math:`i` required by
final demand in country :math:`j`. Setting the domestic blocks of this
**output requirements matrix** to zero isolates production abroad:

.. math::

    (X_t)_{i,j} =
    \begin{cases}
        0 & \text{if } i = j, \\
        X_{i,j} & \text{otherwise}.
    \end{cases}

The impacts embodied in imports are then

.. math::

    \begin{equation}
        D_{imp} = SX_t
    \end{equation}

Each column of :math:`D_{imp}` refers to the consuming country and its demanded
sector. The impacts occurring in each producing sector to satisfy final demand
in other countries are

.. math::

    \begin{equation}
        D_{exp} = S\widehat{X_t e}
    \end{equation}

where :math:`e` sums across consuming countries and demanded sectors, and the
hat diagonalizes the resulting output vector. Each column of :math:`D_{exp}`
refers to the producing country and sector.

For example, suppose country 1 consumes 100 units of its own product, each unit
requiring 0.5 units of input from country 2. At direct impact intensities of 1
and 2 in countries 1 and 2 respectively, the imported inputs embody 100 units
of impact. These are country 1's import impacts and country 2's export impacts.
The purchased final product is domestic, so removing domestic final demand
before applying :math:`L` would incorrectly omit these impacts.

If the factor of production represent required environmental impacts, these can
also occur during the final use phase. In that case :math:`F_Y` describe the impacts
associated with final demand (e.g. household emissions).

These need to be added to the total production- and consumption-based accounts to obtain the total impacts per country. 
Production-based accounts (direct territorial requirements) per region `i` are therefore given by summing over the stressors per sector (0 ... `m`) 
plus the stressors occurring due to the final consumption for all final demand categories (0 ... `w`) of that region.

.. math::

   \begin{equation}
        D_{pba}^i = \sum_{s=0}^m F^i_s + \sum_{c=0}^w F^i_{Yc}
   \end{equation}

Similarly, total requirements (footprints in case of environmental requirements) per region `i` are given by summing the detailed footprint accounts and adding the aggregated final demand stressors.

.. math::

   \begin{equation}
        D_{cba}^i = \sum_{s=0}^m D_{cba, s}^{i} + \sum_{c=0}^w F_{Yc}^i
   \end{equation}

Internally, the summation are implemented with the `group-by <https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.groupby.html>`_ functionality provided by the pandas package.



Upstream and Downstream scope 3
--------------------------------

In the context of impact analyses the factors of production are often
categorized into scope 1, 2 and 3, with scope 3 sub-divided into upstream and
downstream.

For a MRIO the scope 1 is the direct impact of the industries. The factors of production scope 1 associated
with some product or service in sector 'i' of monetary value 'r' is given by :math:`S e_i r``, where :math:`e_i`` is the math:`i^{th}`` unit vector.
Scope 2 is the indirect impact through directly consumed energy (mostly electricity). The precise definition of scope 2
in an MRIO depends on the list of MRIO sectors that are classified as scope 2 energy suppliers. Scope 2 is therefore
included in the upstream scope 3, which we refer to as upstream indirect impacts. The upstream multipliers are

.. math::

    \begin{equation}
        M_{up} = S ( L - I ) = M - S.
    \end{equation}

The downstream scope 3 consists of the factors of production associated with the sectors' output
that is input to other sectors. The downstream impact can be attributed with the Ghosh methodology
(`Lenzen, 2010 <https://www.sciencedirect.com/science/article/abs/pii/S092180091000128X>`_ ).

The downstream attribution according to Ghosh is done by the input share matrix

.. math::

    \begin{equation}
        B = \hat{x}^{-1} Z
    \end{equation}

Note that we have defined this matrix in analogy with :math:`A`, meaning that the factors of production coefficient
are given by :math:`S G^{T}` where

.. math::

    \begin{equation}
        G = (\mathrm{I}- B)^{-1} = \hat{x}^{-1} L \hat{x}
    \end{equation}

is the Ghosh inverse matrix.
The pure downstream multiplier (excluding scope 1) is given by


.. math::

    \begin{equation}
        M_{down} = S(G^{T}-I)
    \end{equation}

The sector's total impact multiplier is simply the sum of :math:`M_{up}`, :math:`S` and :math:`M_{down}`.

Aggregation
------------

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
