###########
Terminology
###########

Notation varies between input-output models. The tables below describe pymrio's
attributes and show alternative notation used in other sources. These
alternatives describe analogous quantities; they are not additional pymrio
attribute names.

Matrix dimensions
=================

For a system with :math:`r` producing regions and :math:`s` sectors per region:

- :math:`n = r s` is the total number of producing industries (region-sector pairs).
- :math:`c` is the number of final-demand columns, usually consuming
  region-category pairs.
- :math:`r_Y` is the number of consuming regions represented in final demand.
  This can differ from :math:`r`, for example when a database includes a
  statistical-discrepancy column.
- :math:`h` is the number of rows in an extension: stressors, factors of
  production, or characterized impact categories.

Shapes below are **rows by columns**. The :doc:`mathematical background <math>`
describes the corresponding equations.

.. list-table:: Core matrices and extension accounts
   :header-rows: 1
   :widths: 10 22 15 16 37

   * - Variable
     - Meaning
     - Other notation
     - Shape
     - Description
   * - ``Z``
     - Transactions
     - T
     - :math:`n \times n`
     - Flows from producing industries in rows to using industries in columns.
   * - ``A``
     - Direct input coefficients
     -
     - :math:`n \times n`
     - Inputs per unit of output of the industry in each column.
   * - ``B``
     - Direct allocation coefficients
     -
     - :math:`n \times n`
     - Transactions divided by the output of the industry in each row.
   * - ``L``
     - Leontief inverse
     - B in some IO literature
     - :math:`n \times n`
     - Total input requirements, including direct and indirect inputs.
   * - ``G``
     - Ghosh inverse
     -
     - :math:`n \times n`
     - Total output-allocation requirements.
   * - ``Y``
     - Final demand
     - H; y for a vector
     - :math:`n \times c`
     - Producing industries in rows; consuming region-category pairs in columns.
   * - ``x``
     - Industry output
     - q, gross output
     - :math:`n \times 1`
     - Total output of each producing industry, stored as a column vector.
   * - ``F``
     - Direct extension totals
     - E in USEEIO
     - :math:`h \times n`
     - Direct environmental flows, factor inputs, or characterized impacts
       associated with each producing industry.
   * - ``F_Y``
     - Direct final-demand extension totals
     - yF, Fhh
     - :math:`h \times c`
     - Direct flows associated with final use, such as household emissions.
   * - ``S``
     - Direct extension coefficients
     - D; B in USEEIO
     - :math:`h \times n`
     - Direct extension totals per unit of industry output.
   * - ``S_Y``
     - Direct final-demand extension coefficients
     - DY, yD, Shh
     - :math:`h \times c`
     - Direct final-use flows per unit of final demand.
   * - ``M``
     - Total extension multipliers
     - m
     - :math:`h \times n`
     - Direct and indirect extension requirements per unit of final demand,
       calculated as :math:`S L`.
   * - ``M_down``
     - Downstream multipliers
     -
     - :math:`h \times n`
     - Downstream extension requirements, calculated as :math:`S(G^T-I)`.
   * - ``D_cba``
     - Consumption-based accounts
     - fp, con, footprints
     - :math:`h \times (r_Y s)`
     - Impacts attributed to each consuming region and demanded sector.
   * - ``D_pba``
     - Production-based accounts
     - terr, territorial accounts
     - :math:`h \times n`
     - Direct impacts attributed to each producing region and sector.
   * - ``D_imp``
     - Import accounts
     - imp
     - :math:`h \times (r_Y s)`
     - Impacts occurring abroad to satisfy demand in each consuming region
       and demanded sector.
   * - ``D_exp``
     - Export accounts
     - exp
     - :math:`h \times n`
     - Impacts in each producing region and sector serving final demand abroad.

The economic core belongs to an ``IOSystem``; the extension tables belong to an
``Extension``. Each extension has its own rows and units, so :math:`h` can differ
between extensions.

For ``F_Y`` and ``S_Y``, the table gives the shape before aggregation of
final-demand categories. These accounts can also be supplied with one column
per consuming region, giving shape :math:`h \times r_Y`.

The account suffix ``_reg`` indicates totals across sectors for each region.
The suffix ``_cap`` indicates the corresponding regional totals divided by
population. For ``D_cba_reg`` and ``D_pba_reg``, the totals also include direct
final-use flows from ``F_Y``. Import and export accounts exclude these direct
final-use flows.

Comparison with USEEIO
======================

The `USEEIO v2 methodology <https://doi.org/10.1038/s41597-022-01293-7>`_
uses different symbols for several extension matrices:

.. list-table:: USEEIO and pymrio extension notation
   :header-rows: 1
   :widths: 15 45 40

   * - USEEIO symbol
     - Quantity
     - Corresponding pymrio attribute
   * - E
     - Direct environmental totals by industry
     - ``F`` in a physical-flow extension
   * - B
     - Direct environmental-flow coefficients
     - ``S`` in a physical-flow extension
   * - M
     - Direct and indirect environmental-flow coefficients
     - ``M`` in a physical-flow extension
   * - D
     - Direct characterized impact coefficients
     - ``S`` in a characterized extension
   * - N
     - Direct and indirect characterized impact coefficients
     - ``M`` in a characterized extension

Pymrio stores physical flows and characterized impacts in the same
``Extension`` structure, so both use the attribute names ``F``, ``S``, and
``M``. In particular, USEEIO's environmental-coefficient matrix B corresponds
to pymrio's ``S``; pymrio's economic-core ``B`` is the allocation-coefficient
matrix used for Ghosh calculations.

System classifications
======================

The labels ``pxp`` (also mxm) and ``ixi`` (also nxn) identify product-by-product
and industry-by-industry systems respectively. They describe the classification
of the economic tables rather than additional matrices.
