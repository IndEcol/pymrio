"""Structural path analysis of demand-driven environmental footprints."""

import heapq
from dataclasses import dataclass
from numbers import Integral, Real
from typing import Optional

import numpy as np
import pandas as pd

from pymrio.tools.iomath import _align_axis


@dataclass
class SPAResult:
    """Results of structural path analysis for one indicator.

    Attributes
    ----------
    paths : pandas.DataFrame
        Retained paths, ranked by decreasing absolute contribution. ``path``
        is a tuple of industry labels ordered from the producer for final
        demand towards upstream suppliers. ``depth`` counts intermediate
        transactions. ``final_demand`` preserves the consumer column label.
        ``contribution`` is signed; ``share_of_total`` uses that consumer's
        full footprint, with NaN for a zero denominator.
    tiers : pandas.DataFrame
        Exact signed totals by depth (rows) and final-demand column, independent
        of pruning and ranking. Row k equals
        ``S @ numpy.linalg.matrix_power(A, k) @ Y``.
    totals : pandas.DataFrame
        Per-consumer ``total`` (full Leontief footprint), ``within_depth``,
        ``reported`` (retained paths), ``depth_residual``, ``omitted`` (within
        depth but not retained), ``residual`` (total minus reported), and
        ``coverage`` (reported divided by total, or NaN for zero total).
        Residuals and coverage are signed and can reflect cancellation.
    visited_nodes : int
        Number of examined path prefixes, including pruned prefixes.
    max_depth : int
        Maximum number of intermediate transactions.
    cutoff : float
        Minimum absolute contribution of a retained path.
    top_n : int or None
        Maximum number of paths retained across all demand columns.
    indicator : object, optional
        Selected indicator label, when provided by a pandas input.
    unit : object, optional
        Indicator unit, set by :meth:`pymrio.IOSystem.calc_spa` when available.
    """

    paths: pd.DataFrame
    tiers: pd.DataFrame
    totals: pd.DataFrame
    visited_nodes: int
    max_depth: int
    cutoff: float
    top_n: Optional[int]
    indicator: object = None
    unit: object = None


def _check_integer(value, name, minimum, allow_none=False):
    """Validate an integer work, output, or depth limit without truncation."""
    if allow_none and value is None:
        return
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral) or value < minimum:
        suffix = " or None" if allow_none else ""
        raise ValueError(f"{name} must be an integer >= {minimum}{suffix}")


def _numeric(value, name):
    """Convert to a finite real array, rejecting complex coefficients."""
    if np.iscomplexobj(value):
        raise ValueError(f"{name} must contain finite real numbers")
    try:
        result = np.asarray(value, dtype=float)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{name} must contain finite real numbers") from exc
    if not np.isfinite(result).all():
        raise ValueError(f"{name} must contain finite real numbers")
    return result


def _prepare_inputs(A, S, Y):
    """Align labeled matrices and normalize one indicator and demand bundles."""
    labeled = isinstance(A, pd.DataFrame)
    if labeled:
        A = _align_axis(A, A.index, axis=1)
        industries = A.index
    values = _numeric(A, "A")
    if values.ndim != 2 or values.shape[0] != values.shape[1] or not values.shape[0]:
        raise ValueError("A must be a nonempty square matrix")
    if not labeled:
        industries = pd.RangeIndex(values.shape[0])

    indicator = None
    if isinstance(S, pd.DataFrame):
        if S.shape[0] != 1:
            raise ValueError("S must contain exactly one indicator row")
        indicator = S.index[0]
        S = S.iloc[0]
    if isinstance(S, pd.Series):
        indicator = S.name
        if labeled:
            S = _align_axis(S, industries)
    intensity = _numeric(S, "S")
    if intensity.ndim == 2 and intensity.shape[0] == 1:
        intensity = intensity[0]
    if intensity.shape != (len(industries),):
        raise ValueError("S must be a vector or a single row with one value per industry")

    if isinstance(Y, pd.Series):
        Y = Y.to_frame(name=Y.name if Y.name is not None else "final_demand")
    if isinstance(Y, pd.DataFrame):
        if labeled:
            Y = _align_axis(Y, industries)
        consumers = Y.columns
        if not consumers.is_unique:
            raise ValueError("Final-demand column labels must be unique")
    else:
        consumers = None
    demand = _numeric(Y, "Y")
    if demand.ndim == 1:
        demand = demand[:, None]
    if demand.ndim != 2 or demand.shape[0] != len(industries) or not demand.shape[1]:
        raise ValueError("Y must have one row per industry and at least one demand column")
    if consumers is None:
        consumers = pd.RangeIndex(demand.shape[1], name="final_demand")
    return values, intensity, demand, industries, consumers, indicator


def _tier_totals(A, S, Y, max_depth):
    """Calculate exact tiers, full footprints, and finite-depth pruning bounds."""
    # Solve the adjoint system once rather than constructing the full inverse.
    multipliers = np.linalg.solve((np.eye(len(A)) - A).T, S)
    total = multipliers @ Y
    tiers = []
    intensity = S.copy()
    bounds = [np.abs(S)]
    abs_A = np.abs(A)
    for depth in range(max_depth + 1):
        tiers.append(intensity @ Y)
        if depth < max_depth:
            intensity = intensity @ A
            # Infinite bounds from overflow only reduce pruning; they never
            # justify discarding a branch. No inverse of abs(A) is needed.
            with np.errstate(over="ignore", invalid="ignore"):
                bounds.append(np.abs(S) + abs_A.T @ bounds[-1])
    tiers = np.asarray(tiers)
    if not np.isfinite(total).all() or not np.isfinite(tiers).all():
        raise ValueError("SPA footprint or tier calculation overflowed")
    return tiers, total, bounds


def _walk_paths(A, S, Y, bounds, max_depth, cutoff, top_n, max_nodes):
    """Traverse upstream walks iteratively with safe pruning and bounded ranking."""
    retained = []
    suppliers = {}
    visited = 0
    serial = 0
    for consumer in range(Y.shape[1]):
        for root in np.flatnonzero(Y[:, consumer]):
            stack = [(int(root), float(Y[root, consumer]), (int(root),))]
            while stack:
                node, weight, path = stack.pop()
                visited += 1
                if visited > max_nodes:
                    raise RuntimeError(
                        "SPA exceeded max_nodes; reduce max_depth, increase cutoff, "
                        "select fewer demand columns, or increase max_nodes"
                    )
                depth = len(path) - 1
                threshold = cutoff
                if top_n is not None and len(retained) == top_n:
                    threshold = max(threshold, retained[0][0])
                bound = abs(weight) * bounds[max_depth - depth][node]
                # Strict comparison preserves cutoff boundary values and ties.
                if bound < threshold or bound == 0:
                    continue
                contribution = float(weight * S[node])
                if not np.isfinite(contribution):
                    raise ValueError("SPA path calculation overflowed")
                if contribution != 0 and abs(contribution) >= cutoff:
                    # Earlier visits win ties without comparing arbitrary labels.
                    record = (abs(contribution), -serial, consumer, path, contribution)
                    serial += 1
                    if top_n is None or len(retained) < top_n:
                        heapq.heappush(retained, record)
                    elif record[:2] > retained[0][:2]:
                        heapq.heapreplace(retained, record)
                if depth == max_depth:
                    continue
                if node not in suppliers:
                    suppliers[node] = np.flatnonzero(A[:, node])
                for supplier in reversed(suppliers[node]):
                    next_weight = weight * A[supplier, node]
                    if not np.isfinite(next_weight):
                        raise ValueError("SPA path calculation overflowed")
                    if next_weight != 0:
                        stack.append((int(supplier), float(next_weight), (*path, int(supplier))))
    return sorted(retained, key=lambda record: record[:2], reverse=True), visited


def calc_spa(A, S, Y, *, max_depth=3, cutoff=0.0, top_n=100, max_nodes=1_000_000):
    r"""Extract structural paths for one indicator and selected final demand.

    Decompose :math:`S(I-A)^{-1}Y` into paths from the production-tier expansion
    :math:`SY + SAY + SA^2Y + \cdots`.
    Inputs are not modified. The Leontief series interpretation requires
    spectral radius ``rho(A) < 1``; this precondition is not checked, matching
    :func:`pymrio.calc_L`. Finite-depth path and tier calculations also work for
    other nonsingular systems, but their residual need not converge to zero.

    Parameters
    ----------
    A : pandas.DataFrame or numpy.ndarray
        Square technical coefficients: rows supply inputs to columns. Pandas
        industry labels must be unique and agree on both axes. Matching labels
        may be reordered; other labeled inputs are aligned to ``A.index``.
        NumPy inputs use positional order.
    S : pandas.Series, pandas.DataFrame or numpy.ndarray
        One indicator's direct production intensity, length n or shape (1, n).
        Select a single extension row; do not pass total multipliers.
    Y : pandas.Series, pandas.DataFrame or numpy.ndarray
        Selected final demand, length n or shape (n, m). All n industry rows
        must be present. Each demand column is analysed separately. To analyse
        a combined bundle, sum its columns explicitly before calling.
    max_depth : int, optional
        Maximum number of intermediate transactions, default 3. Zero includes
        only direct production for final demand. Cycles and self-supply are
        included up to this depth.
    cutoff : float, optional
        Minimum absolute retained path contribution, in indicator units,
        default 0. Zero-contribution paths are omitted. Pruning uses a bound on
        all remaining finite-depth contributions, not direct intensity alone.
    top_n : int or None, optional
        Retain at most this many paths across all demand columns, ranked by
        absolute contribution; default 100. None retains all paths above the
        cutoff. Equal magnitudes use stable traversal order: demand columns,
        then industry order, exploring each branch before the next one.
    max_nodes : int, optional
        Maximum number of examined path prefixes, including pruned prefixes,
        default 1,000,000. Exceeding this limit raises RuntimeError without
        returning a partial ranking. Top-N bounds output memory, but does not
        guarantee short runtime.

    Returns
    -------
    SPAResult
        Ranked paths, exact tier totals, and per-consumer footprint accounting.
        Contributions retain their signs. Net-zero footprint shares are NaN;
        signed coverage is not necessarily between zero and one.

    Raises
    ------
    ValueError
        For invalid limits, shapes, labels, nonfinite or complex inputs, or
        nonfinite calculated values.
    numpy.linalg.LinAlgError
        If ``I - A`` is singular.
    RuntimeError
        If traversal exceeds ``max_nodes``.

    Notes
    -----
    Direct final-demand extension flows (``Extension.F_Y``) are excluded.
    They are household/consumer impacts, not production supply-chain paths.
    The implementation requires dense arrays or DataFrames, as used by pymrio;
    it does not accept scipy sparse matrices. Exact totals require a dense
    linear solve, and tier/bound calculations scale with ``max_depth``.

    Examples
    --------
    >>> import pymrio
    >>> io = pymrio.load_test().calc_all()
    >>> result = pymrio.calc_spa(io.A, io.emissions.S.iloc[0], io.Y, max_depth=1)
    >>> result.paths.shape[0]
    100

    See Also
    --------
    pymrio.IOSystem.calc_spa : Select an extension indicator from an IOSystem.
    """
    _check_integer(max_depth, "max_depth", 0)
    _check_integer(top_n, "top_n", 1, allow_none=True)
    _check_integer(max_nodes, "max_nodes", 1)
    if isinstance(cutoff, (bool, np.bool_)) or not isinstance(cutoff, Real) or not np.isfinite(cutoff) or cutoff < 0:
        raise ValueError("cutoff must be a finite real number >= 0")
    A, S, Y, industries, consumers, indicator = _prepare_inputs(A, S, Y)
    tier_values, total, bounds = _tier_totals(A, S, Y, max_depth)
    records, visited = _walk_paths(A, S, Y, bounds, max_depth, cutoff, top_n, max_nodes)
    reported = np.zeros(Y.shape[1])
    rows = []
    for _, _, consumer, path, contribution in records:
        reported[consumer] += contribution
        rows.append(
            {
                "path": tuple(industries[node] for node in path),
                "final_demand": consumers[consumer],
                "depth": len(path) - 1,
                "contribution": contribution,
                "share_of_total": contribution / total[consumer] if total[consumer] != 0 else np.nan,
            }
        )
    paths = pd.DataFrame(rows, columns=["path", "final_demand", "depth", "contribution", "share_of_total"])
    paths = paths.astype({"depth": "int64", "contribution": "float64", "share_of_total": "float64"})
    tiers = pd.DataFrame(tier_values, index=pd.RangeIndex(max_depth + 1, name="depth"), columns=consumers)
    within = tier_values.sum(axis=0)
    totals = pd.DataFrame(
        {
            "total": total,
            "within_depth": within,
            "reported": reported,
            "depth_residual": total - within,
            "omitted": within - reported,
            "residual": total - reported,
            "coverage": np.divide(reported, total, out=np.full_like(total, np.nan), where=total != 0),
        },
        index=consumers,
    )
    if (
        not np.isfinite(totals.drop(columns="coverage").to_numpy()).all()
        or np.isinf(totals.coverage).any()
        or np.isinf(paths.share_of_total).any()
    ):
        raise ValueError("SPA result accounting overflowed")
    return SPAResult(paths, tiers, totals, visited, max_depth, float(cutoff), top_n, indicator)
