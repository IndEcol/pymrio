"""Regression tests for label alignment in MRIO calculations."""

import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

import pymrio
from pymrio.tools.iomath import recalc_M
from pymrio.tools.ioutil import diagonalize_columns_to_sectors


@pytest.fixture
def labeled_mrio():
    """Provide a small system with distinct outputs and a nontrivial supply chain."""
    index = pd.MultiIndex.from_product([["r1", "r2"], ["s1", "s2"]], names=["region", "sector"])
    Z = pd.DataFrame(np.arange(1, 17, dtype=float).reshape(4, 4), index=index, columns=index)
    x = pd.Series([50.0, 100.0, 150.0, 200.0], index=index, name="indout")
    S = pd.DataFrame([[1.0, 2.0, 3.0, 4.0]], index=["emissions"], columns=index)
    Y = pd.DataFrame([[10.0, 2.0], [3.0, 12.0], [4.0, 8.0], [9.0, 1.0]], index=index)
    Y.columns = pd.Index(["r1", "r2"], name="region")
    return Z, x, S, Y


@pytest.mark.parametrize("as_frame", [False, True])
@pytest.mark.parametrize("function", [pymrio.calc_A, pymrio.calc_Z, pymrio.calc_B, pymrio.calc_S, pymrio.calc_F])
def test_output_vectors_align_by_label(labeled_mrio, function, as_frame):
    """Reordering an output vector must not change the result."""
    Z, x, _, _ = labeled_mrio
    vector = x.to_frame() if as_frame else x
    expected = function(Z, vector)
    pdt.assert_frame_equal(function(Z, vector.iloc[::-1]), expected)


@pytest.mark.parametrize("bad_labels", [["a", "b", "c", "d"], ["a", "a", "b", "c"]])
def test_output_vectors_reject_unmatched_or_duplicate_labels(labeled_mrio, bad_labels):
    """Ambiguous or missing output labels must fail instead of using positions."""
    Z, x, _, _ = labeled_mrio
    x.index = bad_labels
    with pytest.raises(ValueError, match="[Ll]abels"):
        pymrio.calc_A(Z, x)


@pytest.mark.parametrize("change", ["missing", "extra", "duplicate"])
def test_output_vectors_reject_incomplete_classifications(labeled_mrio, change):
    """A labeled output vector must cover the matrix classification exactly once."""
    Z, x, _, _ = labeled_mrio
    if change == "missing":
        x = x.iloc[:-1]
    elif change == "extra":
        x.loc[("r3", "s1")] = 300.0
    else:
        Z.columns = Z.columns.take([0, 0, 2, 3])
    with pytest.raises(ValueError, match="[Ll]abels"):
        pymrio.calc_A(Z, x)


def test_aligned_zero_output_keeps_zero_coefficients(labeled_mrio):
    """Alignment preserves the convention of zero coefficients for zero output."""
    Z, x, _, _ = labeled_mrio
    x.iloc[0] = 0.0
    result = pymrio.calc_A(Z, x.iloc[::-1])
    assert (result.iloc[:, 0] == 0.0).all()
    pdt.assert_frame_equal(result.iloc[:, 1:], Z.iloc[:, 1:].div(x.iloc[1:], axis=1))


def test_calc_x_aligns_final_demand_rows(labeled_mrio):
    """Output totals pair the same producing sectors in Z and Y."""
    Z, _, _, Y = labeled_mrio
    pdt.assert_frame_equal(pymrio.calc_x(Z, Y.iloc[::-1]), pymrio.calc_x(Z, Y))


@pytest.mark.parametrize("function", [pymrio.calc_L, pymrio.calc_G])
def test_inverse_aligns_matrix_axes(labeled_mrio, function):
    """Identity matrices and inverses must refer to matching row and column labels."""
    Z, x, _, _ = labeled_mrio
    A = pymrio.calc_A(Z, x)
    permuted = A.iloc[[2, 0, 3, 1], [1, 3, 0, 2]]
    expected = function(A).reindex(index=permuted.index, columns=permuted.columns)
    pdt.assert_frame_equal(function(permuted), expected, check_exact=False)


@pytest.mark.parametrize("as_frame", [False, True])
def test_ghosh_from_leontief_aligns_output_vectors(labeled_mrio, as_frame):
    """Both axes of a reordered Leontief matrix use the corresponding outputs."""
    Z, x, _, _ = labeled_mrio
    L = pymrio.calc_L(pymrio.calc_A(Z, x))
    expected = pymrio.calc_G(pymrio.calc_B(Z, x))
    permuted = L.iloc[[2, 0, 3, 1], [1, 3, 0, 2]]
    vector = x.to_frame() if as_frame else x
    actual = pymrio.calc_G(None, L=permuted, x=vector.iloc[::-1])
    pdt.assert_frame_equal(actual, expected.reindex(index=permuted.index, columns=permuted.columns), check_exact=False)


@pytest.mark.parametrize("column_vector", [False, True])
def test_ghosh_numpy_fast_path_matches_direct_inverse(labeled_mrio, column_vector):
    """One- and two-dimensional output arrays give the same Ghosh inverse."""
    Z, x, _, _ = labeled_mrio
    L = pymrio.calc_L(pymrio.calc_A(Z, x)).to_numpy()
    expected = pymrio.calc_G(pymrio.calc_B(Z, x)).to_numpy()
    output = x.to_numpy().reshape((-1, 1)) if column_vector else x.to_numpy()
    np.testing.assert_allclose(pymrio.calc_G(None, L=L, x=output), expected)


@pytest.mark.parametrize("as_frame", [False, True])
def test_final_demand_vectors_support_labeled_subsets(labeled_mrio, as_frame):
    """Series and DataFrame final-demand vectors select the same subset of columns."""
    _, _, _, Y = labeled_mrio
    F_Y = pd.DataFrame([[1.0, 2.0]], index=["emissions"], columns=Y.columns)
    y = Y.sum().iloc[[1]]
    vector = y.to_frame() if as_frame else y
    expected = F_Y.loc[:, y.index].div(y, axis=1)
    S_Y = pymrio.calc_S_Y(F_Y, vector)
    pdt.assert_frame_equal(S_Y, expected)
    pdt.assert_frame_equal(pymrio.calc_F_Y(F_Y, vector), F_Y.loc[:, y.index].mul(y, axis=1))


def test_downstream_multipliers_align_identity(labeled_mrio):
    """Subtracting the identity from G uses labels even when its axes differ in order."""
    Z, x, S, _ = labeled_mrio
    G = pymrio.calc_G(pymrio.calc_B(Z, x))
    expected = pymrio.calc_M_down(S, G)
    permuted = G.iloc[[2, 0, 3, 1], [1, 3, 0, 2]]
    actual = pymrio.calc_M_down(S, permuted)
    pdt.assert_frame_equal(actual.reindex(columns=expected.columns), expected, check_exact=False)


def test_diagonalized_demand_uses_sector_labels(labeled_mrio):
    """Shuffled demand rows stay assigned to the same sector after diagonalization."""
    _, _, _, Y = labeled_mrio
    permuted = Y.iloc[[2, 0, 3, 1]]
    expected = diagonalize_columns_to_sectors(Y).reindex(index=permuted.index)
    pdt.assert_frame_equal(diagonalize_columns_to_sectors(permuted), expected)


def test_accounts_align_shuffled_inputs(labeled_mrio):
    """Consumption, production and traded accounts are invariant to input ordering."""
    Z, x, S, Y = labeled_mrio
    L = pymrio.calc_L(pymrio.calc_A(Z, x))
    expected = pymrio.calc_accounts(S, L, Y)
    order = [2, 0, 3, 1]
    actual = pymrio.calc_accounts(S.iloc[:, ::-1], L.iloc[order, order], Y.iloc[order])
    for before, after in zip(expected, actual):
        pdt.assert_frame_equal(after.reindex(index=before.index, columns=before.columns), before, check_exact=False)


def test_recalculated_multipliers_align_footprint_columns(labeled_mrio):
    """Recovering multipliers aligns consumption accounts to the demand matrix."""
    Z, x, S, Y = labeled_mrio
    L = pymrio.calc_L(pymrio.calc_A(Z, x))
    footprint = pymrio.calc_accounts(S, L, Y)[0]
    actual = recalc_M(S, footprint.iloc[:, ::-1], Y)
    pdt.assert_frame_equal(actual.reindex(columns=L.columns), S.dot(L), check_exact=False)


def test_trade_accounts_include_imported_inputs_to_domestic_final_demand():
    """Domestic final demand can embody foreign impacts through intermediate inputs."""
    index = pd.MultiIndex.from_product([["r1", "r2"], ["s1"]], names=["region", "sector"])
    A = pd.DataFrame([[0.0, 0.0], [0.5, 0.0]], index=index, columns=index)
    S = pd.DataFrame([[1.0, 2.0]], index=["emissions"], columns=index)
    Y = pd.DataFrame([[100.0, 0.0], [0.0, 0.0]], index=index, columns=pd.Index(["r1", "r2"], name="region"))
    D_cba, D_pba, D_imp, D_exp = pymrio.calc_accounts(S, pymrio.calc_L(A), Y)
    for actual, values in zip((D_cba, D_pba, D_imp, D_exp), ([200.0, 0.0], [100.0, 100.0], [100.0, 0.0], [0.0, 100.0])):
        pdt.assert_frame_equal(actual, pd.DataFrame([values], index=S.index, columns=index))
