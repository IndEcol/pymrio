.. _structural-path-analysis:

Structural path analysis
========================

Structural path analysis (SPA) identifies the production chains contributing to
an environmental or socioeconomic footprint. It separates production for final
demand from successive tiers of upstream suppliers. The analysis uses the
technical coefficients ``A``, one row of direct production intensities ``S``,
and selected final demand ``Y``.

Getting started
---------------

Calculate the bundled test MRIO and select one complete indicator label:

.. code-block:: python

    import pymrio

    io = pymrio.load_test().calc_all()
    result = io.calc_spa(
        extension="emissions",
        stressor=("emission_type1", "air"),
        max_depth=3,
        top_n=100,
    )

    result.paths.head()
    result.tiers
    result.totals
    result.indicator  # ("emission_type1", "air")
    result.unit       # "kg"

The result is a :class:`~pymrio.SPAResult`. Its three DataFrames have different
purposes:

* ``paths`` contains retained production paths, ranked by decreasing absolute
  contribution across all selected demand columns.
* ``tiers`` contains exact totals at each depth for every selected consumer
  column, before any cutoff or top-N selection.
* ``totals`` reconciles the full footprint with the retained paths for every
  consumer column.

Each ``path`` is a tuple of industry labels ordered **from the producer for final
demand towards upstream suppliers**. For example,
``(("reg1", "food"), ("reg2", "agriculture"))`` describes agricultural inputs from
reg2 used to produce food in reg1. Its contribution is the direct impact at the
agricultural supplier, multiplied by the input coefficient and the demand for
food. ``final_demand`` identifies the consuming region and category separately.

``depth=0`` means production for final demand, ``depth=1`` adds one intermediate
transaction, and so on. The number of industries in a path is ``depth + 1``.
An industry can appear several times because self-supply and circular production
relationships contribute at successive tiers.

Selecting demand and indicators
--------------------------------

Select demand columns with pandas. Keeping separate columns preserves the
consuming region and category, including signed inventory changes:

.. code-block:: python

    selected_Y = io.Y.loc[:, io.Y.columns.get_level_values("region") == "reg1"]
    regional = io.calc_spa(
        "emissions", ("emission_type1", "air"), Y=selected_Y, max_depth=2,
    )

Aggregate explicitly when the question concerns a combined demand bundle:

.. code-block:: python

    bundle = selected_Y.sum(axis=1).rename("reg1 demand")
    combined = io.calc_spa(
        "emissions", ("emission_type1", "air"), Y=bundle, max_depth=2,
    )

Keep all industry rows in ``Y``. To restrict demand to particular products, set
other industry rows to zero; their upstream suppliers must remain available:

.. code-block:: python

    food_Y = selected_Y.copy()
    food_Y.loc[food_Y.index.get_level_values("sector") != "food", :] = 0
    food = io.calc_spa(
        "emissions", ("emission_type1", "air"), Y=food_Y, max_depth=2,
    )

One call analyses one indicator. Use a complete tuple for a MultiIndex indicator,
including its compartment. To analyse a characterized indicator, pass the name
of the characterized extension and its row label in the same way.

The standalone function accepts a selected intensity row, including NumPy
inputs for small independent models:

.. code-block:: python

    standalone = pymrio.calc_spa(
        A=io.A,
        S=io.emissions.S.loc[("emission_type1", "air")],
        Y=selected_Y,
        max_depth=2,
    )

Pandas industry labels are aligned even when their order differs. Missing,
extra, and duplicate industry labels raise an error. NumPy inputs are matched
by position. The standalone function preserves the indicator label when supplied
by pandas; units are provided by the ``IOSystem`` interface.

Interpreting coverage and residuals
------------------------------------

For each selected final-demand column, ``totals`` reports:

.. list-table:: Footprint accounting
   :header-rows: 1
   :widths: 25 75

   * - Column
     - Meaning
   * - ``total``
     - Full production footprint from the Leontief system.
   * - ``within_depth``
     - Sum of all exact tier totals from zero through ``max_depth``.
   * - ``reported``
     - Sum of contributions in the returned paths for that consumer.
   * - ``depth_residual``
     - ``total - within_depth``: production beyond the requested depth.
   * - ``omitted``
     - ``within_depth - reported``: within-depth impacts excluded by the
       cutoff or ranking.
   * - ``residual``
     - ``total - reported``: the entire unreported production footprint.
   * - ``coverage``
     - ``reported / total``; NaN when the total is zero.

The returned paths and ``residual`` reconcile to the full production footprint.
The two residual components make a shallow search distinguishable from a small
retained-path list. Small floating point differences can occur when summing
large numbers of paths.

Coefficients, intensities, demand, contributions, and residuals retain their
signs. Ranking and cutoff comparisons use absolute contributions. When positive
and negative values cancel, ``coverage`` and ``share_of_total`` are signed
ratios and can fall outside the interval zero to one. They are undefined for a
zero net footprint, even when individual paths have nonzero contributions.

Direct consumer impacts in ``Extension.F_Y`` are excluded. These are household
or other final-demand emissions, rather than production supply-chain paths.
Consequently, the SPA total can differ from a consumption account that includes
``F_Y``. Compare the production footprint with ``S @ L @ selected_Y``.

Search limits and output
-------------------------

``max_depth`` limits the number of intermediate transactions. ``cutoff`` is an
absolute minimum path impact in the indicator's unit; a path exactly at the
cutoff is retained if it falls within ``top_n``. Zero-contribution paths are
omitted, but zero-impact industries are still explored for upstream effects.

``top_n`` bounds the number of paths returned across all consumers, rather than
per consumer. Pass ``None`` to retain all paths meeting the cutoff. Equal
magnitudes use stable traversal order: demand-column order, then industry order,
with each branch explored before the next one. A top-N search returns the
largest paths within the specified depth and cutoff.

The path count can grow exponentially with depth. ``max_nodes`` bounds the
number of examined prefixes, including pruned ones; exceeding it raises
``RuntimeError`` without returning a partial ranking. Select fewer demand
columns, reduce the depth, increase the cutoff, or explicitly raise the limit.
Top-N selection limits result storage but does not guarantee a short search.

The implementation uses dense matrices, a dense linear solve for full
footprints, and matrix-vector calculations for tier totals and pruning bounds.
Large MRIOs still require memory for these matrices. It does not construct an
additional full Leontief inverse, and it does not accept scipy sparse inputs.

Pandas provides export and plotting without an additional SPA plotting API:

.. code-block:: python

    result.paths.to_csv("spa_paths.csv", index=False)
    result.totals.to_csv("spa_totals.csv")

    # Inspect production tiers for the first selected consumer.
    result.tiers.iloc[:, 0].plot.bar(ylabel=result.unit)

Mathematical basis and implementation
--------------------------------------

For one intensity row :math:`s` and demand vector :math:`y`, the production
footprint is

.. math::

    f = s(I-A)^{-1}y = \sum_{k=0}^{\infty} sA^k y.

The series converges when the spectral radius :math:`\rho(A) < 1`. This is a
model precondition, not checked automatically, consistent with
:func:`~pymrio.calc_L`. If :math:`I-A` is singular, the calculation raises
``numpy.linalg.LinAlgError``. For other nonsingular systems finite-depth paths
and tiers can be calculated, but the residual need not approach zero.

The contribution of a path :math:`(i_0, i_1, \ldots, i_k)`, in the order used
by the output, is

.. math::

    c_{i_0,\ldots,i_k} = y_{i_0}
        \left(\prod_{r=1}^{k} a_{i_r,i_{r-1}}\right)s_{i_k}.

Summing all paths of depth :math:`k` gives :math:`sA^k y`. The full total is
computed by solving :math:`(I-A)^T m = s^T`, then multiplying :math:`m^T Y`.
This also supplies the reference total for residual accounting.

Traversal is iterative and follows nonzero supplier coefficients. For safe
finite-depth pruning, define nonnegative column vectors

.. math::

    b_0 = |s|^T, \qquad b_r = |s|^T + |A|^T b_{r-1}.

For a prefix with accumulated monetary weight :math:`w` ending at industry
:math:`j`, :math:`|w|(b_r)_j` bounds the sum of absolute impacts of that prefix
and its descendants within :math:`r` further steps. In particular, it bounds
every individual candidate path. A branch can therefore be skipped when this
bound is below the cutoff or the smallest retained top-N magnitude. This bound
also handles signed coefficients and requires no convergence assumption about
:math:`|A|`. Using only a prefix's direct impact would miss important upstream
paths behind low-impact industries.

References and design sources
-----------------------------

The implementation was written independently. The supplied MARIO example
guided the initial feature discussion. The following literature and tools
informed the mathematical conventions and algorithm choices:

* Treloar, G. J. (1997). *Extracting Embodied Energy Paths from Input-Output
  Tables: Towards an Input-Output-based Hybrid Energy Analysis Method*.
  Economic Systems Research, 9(4), 375-391.
  https://doi.org/10.1080/09535319700000032
* Owen, A., Wood, R., Barrett, J. and Evans, A. (2016). *Explaining value chain
  differences in MRIO databases through structural path decomposition*.
  Economic Systems Research, 28(2), 243-272. Section 1.1 explains the SPA
  expansion and tier convention.
  https://doi.org/10.1080/09535314.2015.1135309
  (`author manuscript <https://eprints.whiterose.ac.uk/id/eprint/94829/9/6-20-2016_Explaining.pdf>`_).
* Wood, R. and Lenzen, M. (2009). *Structural path decomposition*.
  Energy Economics, 31(3), 335-341.
  https://doi.org/10.1016/j.eneco.2008.11.003
  Temporal decomposition, as distinguished from SPA in this paper, is outside
  the scope of this implementation.
* `pyspa <https://github.com/beyondepic/pyspa/blob/master/pyspa.py>`_: nonzero
  supplier traversal, total-requirement thresholds, and remainder accounting.
* `WIOD_SPA <https://github.com/martinbruckner/WIOD_SPA/blob/master/WIOD_SPA.R>`_:
  explicit tier calculations and consumer-specific path output.
* `spaJS <https://www.physics.sydney.edu.au/spajs/doc/index.html>`_: upstream
  scanning and threshold/depth controls, reviewed through its user guide.

See :doc:`math` for the underlying MRIO notation and
:func:`~pymrio.calc_spa` for the complete parameter reference.
