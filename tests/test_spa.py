"""Independent mathematical and bundled-MRIO checks for structural paths."""

import itertools

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

import pymrio


@pytest.fixture
def small_system():
    """Provide asymmetric coefficients, signed impacts, and two consumers."""
    A = np.array([[0.1, 0.3, 0.0], [0.4, 0.0, 0.2], [0.2, 0.0, 0.0]])
    S = np.array([1.0, 0.0, -2.0])
    Y = np.array([[10.0, -5.0], [0.0, 3.0], [2.0, -2.0]])
    return A, S, Y


def _exhaustive_paths(A, S, Y, depth, cutoff=0.0):
    """Enumerate every industry sequence without using traversal or pruning."""
    expected = {}
    for consumer, tier in itertools.product(range(Y.shape[1]), range(depth + 1)):
        for path in itertools.product(range(len(S)), repeat=tier + 1):
            impact = S[path[-1]] * Y[path[0], consumer]
            for supplier, customer in zip(path[1:], path[:-1]):
                impact *= A[supplier, customer]
            if impact != 0 and abs(impact) >= cutoff:
                expected[consumer, path] = impact
    return expected


def _path_dict(result):
    """Index returned contributions by consumer and complete industry walk."""
    return {(row.final_demand, row.path): row.contribution for row in result.paths.itertuples()}


@pytest.mark.parametrize("depth", [0, 1, 2, 4])
@pytest.mark.parametrize("cutoff", [0.0, 0.1, 2.0, 100.0])
def test_paths_equal_independent_exhaustive_enumeration(small_system, depth, cutoff):
    """Safe pruning keeps exactly every nonzero path meeting the cutoff."""
    A, S, Y = small_system
    result = pymrio.calc_spa(A, S, Y, max_depth=depth, cutoff=cutoff, top_n=None)
    expected = _exhaustive_paths(A, S, Y, depth, cutoff)
    assert _path_dict(result) == pytest.approx(expected)
    expected_tiers = [S @ np.linalg.matrix_power(A, k) @ Y for k in range(depth + 1)]
    np.testing.assert_allclose(result.tiers, expected_tiers, atol=1e-14)
    total = S @ np.linalg.solve(np.eye(len(A)) - A, Y)
    np.testing.assert_allclose(result.totals.total, total)
    np.testing.assert_allclose(result.totals.within_depth, np.sum(expected_tiers, axis=0))
    np.testing.assert_allclose(result.totals.reported + result.totals.residual, total)
    np.testing.assert_allclose(result.totals.depth_residual + result.totals.omitted, result.totals.residual)
    np.testing.assert_allclose(result.totals.coverage, result.totals.reported / total)
    for row in result.paths.itertuples():
        assert row.share_of_total == pytest.approx(row.contribution / total[row.final_demand])


@pytest.mark.parametrize("top_n", [1, 3, 10, 1000])
def test_top_n_matches_global_exhaustive_ranking(small_system, top_n):
    """Ranking caps memory while preserving largest impacts across consumers."""
    A, S, Y = small_system
    expected = sorted((abs(v) for v in _exhaustive_paths(A, S, Y, 4).values()), reverse=True)[:top_n]
    result = pymrio.calc_spa(A, S, Y, max_depth=4, top_n=top_n)
    np.testing.assert_allclose(result.paths.contribution.abs(), expected)
    assert len(result.paths) <= top_n


def test_zero_direct_intensity_and_large_upstream_coefficient():
    """A zero-impact customer cannot hide a larger upstream supplier path."""
    A = np.array([[0.0, 0.0], [4.0, 0.0]])
    result = pymrio.calc_spa(A, [0.0, 3.0], [1.0, 0.0], cutoff=1.0, top_n=1)
    assert _path_dict(result) == {(0, (0, 1)): 12.0}
    assert result.paths.iloc[0].depth == 1
    assert result.totals.iloc[0].residual == 0


def test_signed_cancellation_does_not_prune_large_paths():
    """Zero net totals still contain significant positive and negative paths."""
    A = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 0.0, 0.0]])
    result = pymrio.calc_spa(A, [0.0, 2.0, -2.0], [1.0, 0.0, 0.0], cutoff=1.0)
    assert sorted(result.paths.contribution) == [-2.0, 2.0]
    assert result.totals.iloc[0].total == 0
    assert np.isnan(result.totals.iloc[0].coverage)
    assert result.paths.share_of_total.isna().all()


def test_signed_matrix_needs_no_convergent_absolute_inverse():
    """Finite-depth bounds work when rho(A) < 1 but rho(abs(A)) > 1."""
    A = np.array([[0.8, 0.8], [-0.8, -0.8]])
    S = np.array([1.0, -2.0])
    Y = np.array([[1.0], [2.0]])
    result = pymrio.calc_spa(A, S, Y, max_depth=5, cutoff=0.05, top_n=None)
    assert _path_dict(result) == pytest.approx(_exhaustive_paths(A, S, Y, 5, 0.05))


def test_cycles_and_self_supply_follow_geometric_series():
    """Repeated sectors contribute at every tier and leave the expected tail."""
    depth = 10
    result = pymrio.calc_spa([[0.5]], [2.0], [3.0], max_depth=depth, top_n=None)
    np.testing.assert_allclose(result.tiers.iloc[:, 0], 6 * 0.5 ** np.arange(depth + 1))
    assert max(len(path) for path in result.paths.path) == depth + 1
    assert result.totals.iloc[0].total == 12
    assert result.totals.iloc[0].residual == pytest.approx(12 * 0.5 ** (depth + 1))


def test_iterative_traversal_is_not_limited_by_python_recursion():
    """A deep one-industry chain completes without recursive calls."""
    result = pymrio.calc_spa([[0.999]], [1.0], [1.0], max_depth=1100, top_n=None, max_nodes=1101)
    assert len(result.paths) == 1101
    assert result.visited_nodes == 1101


def test_cutoff_boundary_is_inclusive_and_ties_are_stable():
    """Equal impacts follow consumer then industry order without label sorting."""
    A = pd.DataFrame(np.zeros((2, 2)), index=["a", 7], columns=["a", 7])
    Y = pd.DataFrame(np.ones((2, 2)), index=A.index, columns=["first", "second"])
    result = pymrio.calc_spa(A, [1, 1], Y, max_depth=0, cutoff=1, top_n=2)
    assert result.paths.path.tolist() == [("a",), (7,)]
    assert result.paths.final_demand.tolist() == ["first", "first"]
    np.testing.assert_allclose(result.totals.reported, [2, 0])


@pytest.mark.parametrize("zero", ["S", "Y", "cutoff"])
def test_empty_paths_keep_complete_accounting(small_system, zero):
    """No retained paths still yields defined columns, tiers, and residuals."""
    A, S, Y = small_system
    cutoff = 0
    if zero == "S":
        S = np.zeros_like(S)
    elif zero == "Y":
        Y = np.zeros_like(Y)
    else:
        cutoff = 1e20
    result = pymrio.calc_spa(A, S, Y, cutoff=cutoff)
    assert result.paths.empty
    assert result.paths.depth.dtype == np.dtype("int64")
    assert result.paths.contribution.dtype == np.dtype("float64")
    assert result.paths.columns.tolist() == ["path", "final_demand", "depth", "contribution", "share_of_total"]
    np.testing.assert_array_equal(result.totals.reported, 0)
    np.testing.assert_allclose(result.totals.residual, result.totals.total)


@pytest.mark.parametrize("as_frame", [False, True])
def test_pandas_alignment_and_complete_multiindex_paths(small_system, as_frame):
    """Independent row/column permutations align by labels without mutation."""
    A, S, Y = small_system
    industries = pd.MultiIndex.from_tuples([("r1", "s1"), ("r2", "s1"), ("r2", "s2")], names=["region", "sector"])
    consumers = pd.MultiIndex.from_tuples([("r1", "households"), ("r2", "stocks")], names=["region", "category"])
    A = pd.DataFrame(A, index=industries, columns=industries)
    S = pd.Series(S, index=industries, name=("CO2", "air"))
    Y = pd.DataFrame(Y, index=industries, columns=consumers)
    if as_frame:
        S = S.to_frame().T
    before = [item.copy(deep=True) for item in (A, S, Y)]
    expected = pymrio.calc_spa(A, S, Y, max_depth=2, top_n=None)
    shuffled = pymrio.calc_spa(
        A.iloc[:, ::-1], S.iloc[:, ::-1] if as_frame else S.iloc[::-1], Y.iloc[::-1], max_depth=2, top_n=None
    )
    pdt.assert_frame_equal(shuffled.paths, expected.paths)
    pdt.assert_frame_equal(shuffled.tiers, expected.tiers)
    pdt.assert_frame_equal(shuffled.totals, expected.totals)
    assert expected.indicator == ("CO2", "air")
    assert expected.totals.index.equals(consumers)
    for item, original in zip((A, S, Y), before):
        if isinstance(item, pd.DataFrame):
            pdt.assert_frame_equal(item, original)
        else:
            pdt.assert_series_equal(item, original)


@pytest.mark.parametrize("name", [None, "bundle", ("r1", "households")])
def test_series_demand_preserves_name_and_matches_explicit_aggregation(small_system, name):
    """An aggregated demand vector is one bundle with its supplied label."""
    A, S, Y = small_system
    demand = pd.Series(Y.sum(axis=1), name=name)
    result = pymrio.calc_spa(A, S[None, :], demand, max_depth=2, top_n=None)
    np.testing.assert_allclose(result.totals.total, S @ np.linalg.solve(np.eye(3) - A, Y.sum(axis=1)))
    assert result.paths.final_demand.iloc[0] == ("final_demand" if name is None else name)


@pytest.mark.parametrize("operand", ["A rows", "A columns", "S", "Y rows", "Y columns"])
@pytest.mark.parametrize("problem", ["duplicate", "missing", "extra", "wrong"])
def test_invalid_pandas_labels_are_rejected(small_system, operand, problem):
    """Incomplete or ambiguous classifications cannot silently match positions."""
    A, S, Y = small_system
    A = pd.DataFrame(A, index=list("abc"), columns=list("abc"))
    S = pd.Series(S, index=A.index)
    Y = pd.DataFrame(Y, index=A.index, columns=["x", "y"])
    target = {"A": A, "S": S, "Y": Y}[operand.split()[0]]
    axis = 1 if "columns" in operand else 0
    if problem == "duplicate":
        if axis == 1:
            target.columns = ["same"] * target.shape[axis]
        else:
            target.index = ["same"] * target.shape[axis]
    elif problem == "wrong":
        if axis == 1:
            target.columns = [f"wrong{i}" for i in range(target.shape[axis])]
        else:
            target.index = [f"wrong{i}" for i in range(target.shape[axis])]
    elif problem == "missing":
        if axis == 1:
            target = target.drop(columns=target.columns[-1])
        else:
            target = target.drop(index=target.index[-1])
    else:
        if axis == 1:
            target["extra"] = 0
        elif operand == "S":
            S.loc["extra"] = 0
        else:
            target.loc["extra"] = 0
    operands = {"A": A, "S": S, "Y": Y}
    operands[operand.split()[0]] = target
    # Consumer columns may be freely selected and named; only duplicates fail.
    if operand == "Y columns" and problem != "duplicate":
        pymrio.calc_spa(**operands)
    else:
        with pytest.raises(ValueError, match="[Ll]abels|square"):
            pymrio.calc_spa(**operands)


@pytest.mark.parametrize(
    "parameter,bad",
    [
        ("max_depth", -1),
        ("max_depth", 1.2),
        ("max_depth", True),
        ("max_depth", None),
        ("top_n", 0),
        ("top_n", -1),
        ("top_n", 1.2),
        ("top_n", True),
        ("max_nodes", 0),
        ("max_nodes", 2.5),
        ("max_nodes", False),
        ("max_nodes", None),
        ("cutoff", -1),
        ("cutoff", np.nan),
        ("cutoff", np.inf),
        ("cutoff", "1"),
        ("cutoff", True),
        ("cutoff", 1j),
    ],
)
def test_invalid_limits_raise_clear_errors(small_system, parameter, bad):
    """Limits reject truncating conversions, booleans, and nonfinite cutoffs."""
    with pytest.raises(ValueError, match=parameter):
        pymrio.calc_spa(*small_system, **{parameter: bad})


@pytest.mark.parametrize(
    "operand,bad",
    [
        (0, np.zeros((2, 3))),
        (0, np.zeros((0, 0))),
        (0, np.zeros(3)),
        (1, np.zeros((2, 3))),
        (1, pd.DataFrame(np.zeros((2, 3)))),
        (1, np.zeros((3, 1))),
        (2, np.zeros((2, 2))),
        (2, np.zeros((3, 0))),
        (2, np.zeros((3, 1, 1))),
    ],
)
def test_invalid_shapes_are_rejected(small_system, operand, bad):
    """Input dimensions must describe one intensity and complete demand rows."""
    values = list(small_system)
    values[operand] = bad
    with pytest.raises(ValueError, match="A|S|Y"):
        pymrio.calc_spa(*values)


@pytest.mark.parametrize("operand", [0, 1, 2])
@pytest.mark.parametrize("bad", [np.nan, np.inf, 1j, "invalid"])
def test_invalid_numeric_inputs_are_rejected(small_system, operand, bad):
    """Nonfinite, complex, and nonnumeric values never enter the traversal."""
    values = list(small_system)
    dtype = complex if bad == 1j else object
    values[operand] = values[operand].astype(dtype)
    values[operand].flat[0] = bad
    with pytest.raises(ValueError, match="finite real"):
        pymrio.calc_spa(*values)


def test_work_limit_raises_instead_of_returning_partial_ranking(small_system):
    """Large path trees require an explicit increase of the work limit."""
    with pytest.raises(RuntimeError, match="exceeded max_nodes"):
        pymrio.calc_spa(*small_system, max_nodes=1)


def test_singular_leontief_system_is_rejected():
    """A singular system has no full footprint for residual accounting."""
    with pytest.raises(np.linalg.LinAlgError):
        pymrio.calc_spa([[1.0]], [1.0], [1.0])


@pytest.mark.parametrize("case", ["footprint", "path contribution", "path weight"])
def test_nonfinite_calculations_fail_explicitly(case):
    """Finite inputs cannot silently produce infinite reported impacts."""
    if case == "footprint":
        A, S, Y = [[0.0]], [1e308], [2.0]
        message = "footprint or tier"
    elif case == "path contribution":
        # s @ A cancels before Y is applied, giving finite tier totals, while
        # individual paths can overflow. Tier checks alone cannot detect this.
        A, S, Y = [[2.0, 2.0], [-2.0, -2.0]], [2.0, 2.0], [5e307, -5e307]
        message = "path calculation"
    else:
        # The complete impact is finite but the monetary prefix overflows.
        A, S, Y = [[0.0, 0.0], [1e308, 0.0]], [0.0, 1e-308], [2.0, 0.0]
        message = "path calculation"
    with np.errstate(over="ignore", invalid="ignore"), pytest.raises(ValueError, match=message):
        pymrio.calc_spa(A, S, Y, max_depth=1)


def test_numpy_integer_options_are_supported():
    """Integer scalar types follow the same validation as Python integers."""
    result = pymrio.calc_spa([[0.0]], [1.0], [2.0], max_depth=np.int64(0), top_n=np.int64(1))
    assert result.paths.iloc[0].contribution == 2


def test_ranked_signed_sums_cannot_return_infinite_accounting():
    """Sorting finite signed paths must not silently overflow their subtotal."""
    demand = [1e308, -9e307, 1e308, -9e307]
    with np.errstate(over="ignore", invalid="ignore"), pytest.raises(ValueError, match="accounting overflowed"):
        pymrio.calc_spa(np.zeros((4, 4)), np.ones(4), demand, max_depth=0)


@pytest.fixture(scope="module")
def test_mrio():
    """Calculate the bundled test MRIO once for all integration checks."""
    return pymrio.load_test().calc_all()


def test_bundled_mrio_paths_tiers_and_footprints(test_mrio):
    """Real test-MRIO paths reconcile with matrix powers and its Leontief table."""
    io = test_mrio
    indicator = ("emission_type1", "air")
    result = io.calc_spa("emissions", indicator, max_depth=1, top_n=None)
    s = io.emissions.S.loc[indicator]
    np.testing.assert_allclose(result.tiers.iloc[0], s @ io.Y)
    np.testing.assert_allclose(result.tiers.iloc[1], s @ io.A @ io.Y)
    np.testing.assert_allclose(result.totals.total, s @ io.L @ io.Y)
    np.testing.assert_allclose(result.totals.reported, result.tiers.sum(axis=0))
    np.testing.assert_allclose(result.totals.omitted, 0, atol=1e-5)
    assert result.unit == "kg"
    assert result.indicator == indicator
    # Check every reported path via independent labeled coefficient lookups.
    for row in result.paths.itertuples():
        expected = io.Y.loc[row.path[0], row.final_demand] * s.loc[row.path[-1]]
        for supplier, customer in zip(row.path[1:], row.path[:-1]):
            expected *= io.A.loc[supplier, customer]
        assert row.contribution == pytest.approx(expected)


def test_bundled_mrio_separate_consumers_and_explicit_aggregation(test_mrio):
    """Selecting or aggregating columns uses ordinary pandas operations."""
    io = test_mrio
    selected = io.Y.loc[:, io.Y.columns.get_level_values("region") == "reg1"]
    result = io.calc_spa(io.emissions, ("emission_type1", "air"), Y=selected, max_depth=0)
    aggregate = io.calc_spa("emissions", ("emission_type1", "air"), Y=selected.sum(axis=1), max_depth=0)
    assert result.totals.index.equals(selected.columns)
    assert len(aggregate.totals) == 1
    assert aggregate.totals.total.iloc[0] == pytest.approx(result.totals.total.sum())


def test_direct_household_flows_are_excluded(test_mrio):
    """F_Y never enters production-path accounting, even when very large."""
    io = test_mrio.copy()
    expected = io.calc_spa("emissions", ("emission_type1", "air"), max_depth=0)
    io.emissions.F_Y = io.emissions.F_Y.astype(float) + 1e20
    actual = io.calc_spa("emissions", ("emission_type1", "air"), max_depth=0)
    pdt.assert_frame_equal(actual.totals, expected.totals)
    pdt.assert_frame_equal(actual.paths, expected.paths)


@pytest.mark.parametrize("extension", ["missing", "A", None])
def test_invalid_extension_is_rejected(test_mrio, extension):
    """Only extension names or instances are accepted by the convenience API."""
    with pytest.raises(ValueError, match="existing Extension"):
        test_mrio.calc_spa(extension, ("emission_type1", "air"))


@pytest.mark.parametrize("missing", ["A", "S"])
def test_uncalculated_system_requires_explicit_calculation(test_mrio, missing):
    """The analysis does not silently calculate or mutate the MRIO."""
    io = test_mrio.copy()
    if missing == "A":
        io.A = None
    else:
        io.emissions.S = None
    with pytest.raises(ValueError, match="calc_all"):
        io.calc_spa("emissions", ("emission_type1", "air"))


def test_stressor_requires_one_exact_unique_label(test_mrio):
    """Partial, absent, or duplicated indicator labels cannot mix intensities."""
    with pytest.raises(ValueError, match="complete indicator"):
        test_mrio.calc_spa("emissions", "emission_type1")
    with pytest.raises(KeyError):
        test_mrio.calc_spa("emissions", ("missing", "air"))
    ext = test_mrio.emissions.copy()
    ext.S.index = pd.Index(["duplicate", "duplicate"])
    with pytest.raises(ValueError, match="unique"):
        test_mrio.calc_spa(ext, "duplicate")


def test_extension_without_unit_is_supported(test_mrio):
    """Unit metadata is optional for numerical analysis."""
    ext = test_mrio.emissions.copy()
    ext.unit = None
    result = test_mrio.calc_spa(ext, ("emission_type1", "air"), max_depth=0)
    assert result.unit is None
