Structural path analysis implementation plan
============================================

Todo
----

1. [done] Inspect the supplied example and pymrio calculation, label-alignment,
   testing, and Sphinx conventions.
2. [done] Research the SPA literature and independent implementations.
3. [done] Guide the API, demand grouping, and plotting decisions.
4. [done] Implement an independent numerical engine with bounded traversal.
5. [done] Integrate with IOSystem and the public pymrio namespace.
6. [done] Verify with independent examples and the bundled test MRIO; measure
   coverage and run the full test/lint gate.
7. [done] Document mathematics, usage, limits, and research in reStructuredText;
   build the Sphinx documentation.

Research and mathematical conventions
--------------------------------------

SPA expands the demand-driven footprint into direct production paths:

.. math::

   f = s (I-A)^{-1} y = \sum_{k=0}^{\infty} s A^k y.

Tier zero is production for final demand. Tier k includes k intermediate
transactions. For a path ordered from the final producer to its upstream
suppliers, the contribution is
``y[i0] * A[i1, i0] * ... * A[ik, i(k-1)] * s[ik]``.
Repeated sectors and self-supply must be retained: the expansion contains
walks, including cycles, rather than only simple graph paths.
The infinite-series interpretation assumes spectral radius rho(A) < 1.

Literature examined:

* Treloar (1997), *Extracting Embodied Energy Paths from Input-Output Tables*,
  Economic Systems Research 9(4), 375-391.
  https://doi.org/10.1080/09535319700000032
  The publisher abstract motivates extracting paths and treating incomplete
  path coverage explicitly; the full article was not available here.
* Owen, Wood, Barrett and Evans (2016), *Explaining value chain differences in
  MRIO databases through structural path decomposition*, Economic Systems
  Research 28(2), 243-272. The accessible author manuscript, section 1.1 and
  mathematical derivation, establishes the tier and path conventions.
  https://eprints.whiterose.ac.uk/id/eprint/94829/9/6-20-2016_Explaining.pdf
  https://doi.org/10.1080/09535314.2015.1135309
* Wood and Lenzen (2009), *Structural path decomposition*, Energy Economics
  31(3), 335-341. The publisher abstract distinguishes SPA from temporal
  structural path decomposition; temporal decomposition is outside this task.
  https://doi.org/10.1016/j.eneco.2008.11.003

Code and tool references examined:

* ``example/database.py``, ``Database.calc_spa``: useful demand selectors,
  ranking, and footprint metadata. Its direct-impact cutoff also stops
  traversal, which can discard large upstream effects behind a zero-impact
  sector. Its recursion and post-hoc top-N cap do not bound traversal memory.
  It is a guide only; no implementation is copied.
* pyspa 2.4, ``pyspa.py``: ``_get_requirements_dict``,
  ``_get_thresholds_test``, ``_add_extraction_stage``, and remainder handling.
  Traverses nonzero input coefficients, prunes using total requirements,
  and distinguishes direct pathway effects from remainders. Its dynamically
  generated recursive stages and object hierarchy are unnecessary for pymrio.
  GPL code is a research reference only; none is copied.
  https://github.com/beyondepic/pyspa/blob/master/pyspa.py
* WIOD_SPA, ``WIOD_SPA.R``: explicit zero/first/second-tier calculations provide
  an independent view of coefficient orientation and per-consumer reporting.
  Its fixed-depth loops and coefficient cutoffs are not adopted.
  https://github.com/martinbruckner/WIOD_SPA/blob/master/WIOD_SPA.R
* spaJS user guide: upstream scanning, per-indicator analysis, relative
  thresholds, CSV output, and visualisation conventions. Documentation was
  reviewed; its implementation was not inspected.
  https://www.physics.sydney.edu.au/spajs/doc/index.html

Accepted decisions
------------------

The user confirmed all three recommended choices: both interfaces with an
explicit result object, preservation of selected demand columns, and a numerical
API without an integrated plotting interface. The resulting decisions are:

* A standalone ``pymrio.calc_spa`` plus ``IOSystem.calc_spa`` convenience method.
* One indicator per call; preserve pandas industry labels and selected final
  demand columns. Users aggregate explicitly with normal pandas operations.
* An explicit result object containing path and tier DataFrames and footprint,
  reported, and residual totals. Do not rely on fragile DataFrame attrs.
* Numerical analysis first; existing pandas/matplotlib operations can plot
  the returned data without introducing plotting dependencies.
* Signed coefficients, intensities, and final demand retain their signs.
  Rank and apply cutoffs by absolute path impact. Net-zero footprint shares
  are undefined rather than replaced with a misleading denominator.
* Iterative traversal, a maximum depth, bounded top-N storage, and an explicit
  work limit. Exceeding the work limit raises rather than silently returning
  incomplete rankings.
* Safe finite-depth pruning derived independently: let ``b[0] = abs(s)`` and
  ``b[r] = abs(s) + abs(A).T @ b[r-1]``. For a prefix with monetary weight w
  ending at industry j, ``abs(w) * b[remaining][j]`` bounds every descendant
  impact within the remaining depth. A small direct impact alone never stops
  traversal. This bound remains valid for signed inputs and does not assume
  rho(abs(A)) < 1.

Verification contract
---------------------

* Hand-calculated asymmetric chains check supplier/customer orientation.
* For unpruned traversal, tier-k totals equal ``s @ matrix_power(A, k) @ Y``.
* Full footprint equals a separate ``s @ solve(I-A, Y)`` calculation.
* The sum of returned paths plus the residual equals the full footprint.
* Exercise zero direct intensity, self-supply, cycles, negative values,
  cancellation, cutoff boundaries, top-N ranking, work limits, empty results,
  invalid inputs, and shuffled/missing/duplicate pandas labels.
* Use ``pymrio.load_test().calc_all()`` for development and integration checks;
  compare each returned path with its coefficient product and each consumer
  total with the bundled system's independent footprint calculation.

Completed validation
--------------------

* Python 3.11.15: ``poe fulltest`` passed all 310 checks, including Ruff lint
  and formatting checks. This includes 110 SPA tests. The four warnings are
  existing Docutils deprecation warnings in report generation.
* ``pymrio/tools/iospa.py`` has 100% statement coverage (156 statements).
  Full-suite coverage as reported by the repository task is 92%.
* Independent exhaustive enumeration verifies cutoff and top-N results;
  matrix powers verify tiers; a separate Leontief calculation verifies full
  footprints. Bundled test-MRIO paths are individually checked by coefficient
  products. Additional tests cover input validation, nonmutation, cycles,
  signed cancellation, finite-input overflow, and consistent empty outputs.
* All six usage-guide Python blocks executed successfully, including CSV
  exports and the pandas plot. Both API examples passed their doctests
  (eight examples in total).
* ``make -C doc html`` succeeded. No new SPA documentation warnings remain.
  Six existing warnings concern ``recalc_M``, obsolete API names
  ``concate_extension`` and ``convert_to_long``, and unreferenced pages.
* ``git diff --check`` passed. No new dependencies were added.
