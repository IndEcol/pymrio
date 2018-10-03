""" Mathematical functions for input output calculations

All methods here should follow the functional programming paradigm

Note
----
To avoid namespace pollution everythin here starts with calc_

"""

import pandas as pd
import numpy as np
import scipy.sparse as sp
import warnings
import operator

import pymrio.tools.ioutil as ioutil


def calc_x(Z, Y):
    """ Calculate the industry output x from the Z and Y matrix

    Parameters
    ----------
    Z : pandas.DataFrame or numpy.array
        Symmetric input output table (flows)
    Y : pandas.DataFrame or numpy.array
        final demand with categories (1.order) for each country (2.order)

    Returns
    -------
    pandas.DataFrame or numpy.array
        Industry output x as column vector
        The type is determined by the type of Z. If DataFrame index as Z

    """
    result = np.reshape(np.sum(np.hstack((Z, Y)), 1), (-1, 1))
    if type(Z) is pd.DataFrame:
        result = pd.DataFrame(result, index=Z.index, columns=['indout'])
    return result


def calc_x_from_L(L, y):
    """ Calculate the industry output x from L and a y vector

    Parameters
    ----------
    L : pandas.DataFrame or numpy.array
        Symmetric input output Leontief table
    y : pandas.DataFrame or numpy.array
        a column vector of the total final demand

    Returns
    -------
    pandas.DataFrame or numpy.array
        Industry output x as column vector
        The type is determined by the type of L. If DataFrame index as L

    """
    x = L.dot(y)
    if type(L) is pd.DataFrame:
        x.columns = ['indout']
    return x


def calc_Z(A, x):
    """ calculate the Z matrix (flows) from A and x

    Parameters
    ----------
    A : pandas.DataFrame or numpy.array
        Symmetric input output table (coefficients)
    x : pandas.DataFrame or numpy.array
        Industry output column vector

    Returns
    -------
    pandas.DataFrame or numpy.array
        Symmetric input output table (flows) Z
        The type is determined by the type of A.
        If DataFrame index/columns as A

    """
    if (type(x) is pd.DataFrame) or (type(x) is pd.Series):
        x = x.values
    x = x.reshape((1, -1))   # use numpy broadcasting - much faster
    # (but has to ensure that x is a row vector)
    # old mathematical form:
    # return A.dot(np.diagflat(x))
    if type(A) is pd.DataFrame:
        return pd.DataFrame(A.values * x, index=A.index, columns=A.columns)
    else:
        return A*x


def calc_A(Z, x):
    """ Calculate the A matrix (coefficients) from Z and x

    Parameters
    ----------
    Z : pandas.DataFrame or numpy.array
        Symmetric input output table (flows)
    x : pandas.DataFrame or numpy.array
        Industry output column vector

    Returns
    -------
    pandas.DataFrame or numpy.array
        Symmetric input output table (coefficients) A
        The type is determined by the type of Z.
        If DataFrame index/columns as Z

    """
    if (type(x) is pd.DataFrame) or (type(x) is pd.Series):
        x = x.values
    if (type(x) is not np.ndarray) and (x == 0):
        recix = 0
    else:
        with warnings.catch_warnings():
            # catch the divide by zero warning
            # we deal wit that by setting to 0 afterwards
            warnings.simplefilter('ignore')
            recix = 1/x
        recix[recix == np.inf] = 0
        recix = recix.reshape((1, -1))
    # use numpy broadcasting - factor ten faster
    # Mathematical form - slow
    # return Z.dot(np.diagflat(recix))
    if type(Z) is pd.DataFrame:
        return pd.DataFrame(Z.values * recix, index=Z.index, columns=Z.columns)
    else:
        return Z*recix


def calc_L(A):
    """ Calculate the Leontief L from A

    Parameters
    ----------
    A : pandas.DataFrame or numpy.array
        Symmetric input output table (coefficients)

    Returns
    -------
    pandas.DataFrame or numpy.array
        Leontief input output table L
        The type is determined by the type of A.
        If DataFrame index/columns as A

    """
    I = np.eye(A.shape[0])   # noqa
    if type(A) is pd.DataFrame:
        return pd.DataFrame(np.linalg.inv(I-A),
                            index=A.index, columns=A.columns)
    else:
        return np.linalg.inv(I-A)


def calc_S(F, x):
    """ Calculate extensions/factor inputs coefficients

    Parameters
    ----------
    F : pandas.DataFrame or numpy.array
        Total direct impacts
    x : pandas.DataFrame or numpy.array
        Industry output column vector

    Returns
    -------
    pandas.DataFrame or numpy.array
        Direct impact coefficients S
        The type is determined by the type of F.
        If DataFrame index/columns as F

    """
    return calc_A(F, x)


def calc_F(S, x):
    """ Calculate total direct impacts from the impact coefficients

    Parameters
    ----------
    S : pandas.DataFrame or numpy.array
        Direct impact coefficients S
    x : pandas.DataFrame or numpy.array
        Industry output column vector

    Returns
    -------
    pandas.DataFrame or numpy.array
        Total direct impacts F
        The type is determined by the type of S.
        If DataFrame index/columns as S

    """
    return calc_Z(S, x)


def calc_M(S, L):
    """ Calculate multipliers of the extensions

    Parameters
    ----------
    L : pandas.DataFrame or numpy.array
        Leontief input output table L
    S : pandas.DataFrame or numpy.array
        Direct impact coefficients

    Returns
    -------
    pandas.DataFrame or numpy.array
        Multipliers M
        The type is determined by the type of D.
        If DataFrame index/columns as D

    """
    return S.dot(L)


def calc_e(M, Y):
    """ Calculate total impacts (footprints of consumption Y)

    Parameters
    ----------
    M : pandas.DataFrame or numpy.array
        Multipliers
    Y : pandas.DataFrame or numpy.array
        Final consumption

    TODO - this must be completely redone (D, check for dataframe, ...)

    Returns
    -------
    pandas.DataFrame or numpy.array
        Multipliers m
        The type is determined by the type of M.
        If DataFrame index/columns as M
    The calcubased on multipliers M and finald demand Y """

    return M.dot(Y)


def recalc_M(S, D_cba, Y, nr_sectors):
    """ Calculate Multipliers based on footprints.

    Parameters
    ----------
    D_cba : pandas.DataFrame or numpy array
        Footprint per sector and country
    Y : pandas.DataFrame or numpy array
        Final demand: aggregated across categories or just one category, one
        column per country. This will be diagonalized per country block.
        The diagonolized form must be invertable for this method to work.
    nr_sectors : int
        Number of sectors in the MRIO

    Returns
    -------

    pandas.DataFrame or numpy.array
        Multipliers M
        The type is determined by the type of D_cba.
        If DataFrame index/columns as D_cba


    """

    Y_diag = ioutil.diagonalize_blocks(Y.values, blocksize=nr_sectors)
    Y_inv = np.linalg.inv(Y_diag)
    M = D_cba.dot(Y_inv)
    if type(D_cba) is pd.DataFrame:
        M.columns = D_cba.columns
        M.index = D_cba.index

    return M


def calc_accounts(S, L, Y, nr_sectors):
    """ Calculate sector specific cba and pba based accounts, imp and exp accounts

    The total industry output x for the calculation
    is recalculated from L and y

    Parameters
    ----------
    L : pandas.DataFrame
        Leontief input output table L
    S : pandas.DataFrame
        Direct impact coefficients
    Y : pandas.DataFrame
        Final demand: aggregated across categories or just one category, one
        column per country
    nr_sectors : int
        Number of sectors in the MRIO


    Returns
    -------
    Tuple
        (D_cba, D_pba, D_imp, D_exp)

        Format: D_row x L_col (=nr_countries*nr_sectors)

        - D_cba        Footprint per sector and country
        - D_pba      Total factur use per sector and country
        - D_imp       Total global factor use to satisfy total final demand in
                      the country per sector
        - D_exp       Total factor use in one country to satisfy final demand
                      in all other countries (per sector)
    """
    # diagonalize each sector block per country
    # this results in a disaggregated y with final demand per country per
    # sector in one column
    Y_diag = ioutil.diagonalize_blocks(Y.values, blocksize=nr_sectors)
    x_diag = L.dot(Y_diag)
    x_tot = x_diag.values.sum(1)
    del Y_diag

    D_cba = pd.DataFrame(S.values.dot(x_diag),
                         index=S.index,
                         columns=S.columns)
    # D_pba = S.dot(np.diagflat(x_tot))
    # faster broadcasted calculation:
    D_pba = pd.DataFrame(S.values*x_tot.reshape((1, -1)),
                         index=S.index,
                         columns=S.columns)

    # for the traded accounts set the domestic industry output to zero
    dom_block = np.zeros((nr_sectors, nr_sectors))
    x_trade = ioutil.set_block(x_diag.values, dom_block)
    D_imp = pd.DataFrame(S.values.dot(x_trade),
                         index=S.index,
                         columns=S.columns)

    x_exp = x_trade.sum(1)
    # D_exp = S.dot(np.diagflat(x_exp))
    # faster broadcasted version:
    D_exp = pd.DataFrame(S.values * x_exp.reshape((1, -1)),
                         index=S.index,
                         columns=S.columns)

    return (D_cba, D_pba, D_imp, D_exp)

def sorted_series(series): 
    '''
    Returns the sorted panda series, grouped by group_by if it is not None, and indexed by index (the default index is that of regions x sectors)
    '''
    return(sorted(series.items(), reverse=True, key=operator.itemgetter(1)))

def approx_solution(A, y, n=10):
    '''
    Returns the approximate solution x of the sparse matrix equation: (1-A).x=y, by computing the series of A^k.y, with k<n
    '''
    s, x = sp.csc_matrix(y).transpose(), sp.csc_matrix(y).transpose()
    for i in range(n):
        x = A.dot(x)
        s += x
    return(s)

def div0(a, b, replace_by=0):
    '''
    Returns the Hadamard division of the arrays (or matrices) of same shape a and b, where elements of the results are 0 in locations where those of b are 0.
    '''
    if sp.issparse(b): 
        b = np.array(b.toarray(), dtype='float')
        sparse = True
    else: sparse = False
    if type(a)==int or type(a)==float: a = a*np.ones_like(b)
    if sp.issparse(a): a = a.toarray()
    a = np.array(a, dtype='float')
#     b = np.array(b, dtype='float')
    div = np.divide(a, b, out=np.array(replace_by*np.ones_like(a)), where=b!=0)
    if sparse: return(sp.csc_matrix(div)) # TODO: a true sparse division, not through dense matrix
    else: return(div)

def mult_rows(mat, vec):
    '''
    Multiply (each element of) the k-th row of matrix by k-th element of vector for all k, returns the resulting matrix.
    '''
    if sp.issparse(mat): #         return(matrix.toarray() * sp.diags([vector]).dot(np.ones(matrix.shape))) 
        nb_r, nb_c = mat.shape
        if sp.issparse(vec): vec = vec.toarray()
        return(mat.multiply(sp.csc_matrix((np.tile(vec.data,nb_c).flatten(), np.tile(np.arange(nb_r),nb_c), np.arange(0,nb_c*np.max(vec.shape)+1,nb_r)), \
                                          shape=mat.shape)))
    else: return(matrix * np.diag(vec).dot(np.ones(mat.shape))) 

def mult_cols(mat, vec): 
    '''
    Multiply (each element of) the k-th column of matrix by k-th element of vector for all k, returns the resulting matrix.
    '''
    if sp.issparse(mat): #         return(matrix.toarray() * (np.ones(matrix.shape)).dot(sp.diags([vector])))
        nb_r, nb_c = mat.shape
        if sp.issparse(vec): vec = vec.toarray()
        return(mat.multiply(sp.csc_matrix((np.repeat(vec.data, nb_r).flatten(),np.tile(np.arange(nb_r),nb_c),np.arange(0,nb_r*np.max(vec.shape)+1,nb_r)),\
                                          shape=mat.shape)))
    else: return(matrix * (np.ones(mat.shape)).dot(np.diag(vec)))
        
def inter_secs(secs1, secs2): 
    '''
    Returns the intersection of lists secs1 and secs2.
    '''
    return(list(np.array(secs1)[np.where([sec in secs2 for sec in secs1])[0]]))
    
def gras(A, new_row_sums = None, new_col_sums = None, max_iter=1e2, criterion='relative', tol=1e0): 
    '''
    GRAS algorithm, which balances a matrix A in order to respect new_row_sums and new_col_sums (see Junius & Oosterhaven, 2003).
    FOR DENSE MATRIX
    criterion can be: 'absolute', 'relative' (default), or 'convergence': in the latter, it stops when improvement falls below tol.
    
    Algorithm directly transcripted from matlab: results are the same as in matlab; I haven't checked that the code is valid but it seems.
    Original program of Bertus Talsma, adapted by Dirk Stelder in Gauss, transferred to Matlab by Maaike Bouwmeester.
    Matlab code can be found in /util/gras.m at https://cecilia2050.eu/system/files/cecilia_scenario_tool_version1.zip
    '''
    if sp.issparse(A): print('Your matrix is sparse: use grasp() instead.')
    if new_row_sums is None: u = A.sum(axis=1)
    else: u = np.array(new_row_sums)
    if new_col_sums is None: v = A.sum(axis=0)
    else: v = np.array(new_col_sums)
    nb_rows, nb_cols = A.shape
    sm = 0.00000000000000001
    converged = False
    P, N = np.clip(A, 0, None), np.clip(-np.array(A), 0, None)
    r, s = np.ones(nb_rows), np.ones(nb_cols)
#     nnn, nn = np.ones(nb_rows), np.ones(nb_cols)
#     ppp, pp = np.ones(nb_rows), np.ones(nb_cols)
#     r_inv = div0(1, r)
    iterator = 1
    while iterator < max_iter:
        s_inv, r_inv = div0(1, s), div0(1, r)
        pp = mult_rows(P, r).sum(axis=0) # pp[col] = (P[:,col] * r).sum()
        nn = mult_rows(N, r_inv).sum(axis=0) # nn[col] = (N[:,col] * r_inv).sum()
        s = (v + (v**2 + 4*pp*nn)**0.5) / (2*pp + sm)
        row_new = (np.diag(r).dot(P).dot(np.diag(s)) - np.diag(r_inv).dot(N).dot(np.diag(s_inv))).dot(np.ones(nb_cols))
        eps1_abs = np.ones(nb_rows).dot(np.abs(row_new - u))
        rel = np.abs(row_new / (u + sm) - 1)
        rel[np.where(u==0)] = 0
        eps1_rel = np.max(rel)
        ppp = mult_cols(P, s).sum(axis=1)
        nnn = mult_cols(N, s_inv).sum(axis=1)
        r = (u + (u**2 + 4*ppp*nnn)**0.5) / (2*ppp + sm)
        ri = div0(1, r)
        col_new = np.ones(nb_rows).dot((np.diag(r).dot(P).dot(np.diag(s)) - np.diag(r_inv).dot(N).dot(np.diag(s_inv))))
        eps2_abs = np.ones(nb_cols).dot(np.abs(col_new - v))
        rel = np.abs(col_new / (v + sm) - 1)
        rel[np.where(v==0)] = 0
        eps2_rel = np.max(rel)
        if criterion == 'relative': tol_current = (eps1_rel + eps2_rel)/2
        else: tol_current = (eps1_abs + eps2_abs)/2
        if iterator > 1: improvement = (tol_previous - tol_current)/tol_previous
        if (criterion in ['relative', 'absolute'] and tol_current < tol) or (criterion=='convergence' and (iterator > 1 and improvement < tol)):
            iterator = max_iter
            converged = True
#             print('converged')
        else: 
            iterator += 1
            tol_previous = tol_current
            if iterator>1: print(time()-time_i)
            time_i = time()
            print(iterator, tol_previous)
    if converged:
#         return(P-N) # why not simply this?
#         P = np.diag(r).dot(A).dot(np.diag(s))
#         N = np.diag(div0(1, r)).dot(A).dot(np.diag(div0(1, s)))
#         N[np.where(P>=0)] = 0
#         X = np.clip(P, 0, None) + N # TODO!: check if + and not -
#         return(X)
        return(np.diag(r).dot(P).dot(np.diag(s))-np.diag(div0(1, r)).dot(N).dot(np.diag(div0(1, s))))
    else: print('did not converged')
        
def grasp(A, new_row_sums = None, new_col_sums = None, max_iter=1e2, criterion='convergence', tol=1e-5): 
    '''
    GRAS algorithm, which balances a matrix A in order to respect new_row_sums and new_col_sums (see Junius & Oosterhaven, 2003).
    FOR SPARE MATRIX
    criterion can be: 'absolute', 'relative' (default), or 'convergence': in the latter, it stops when improvement falls below tol.
    
    Algorithm directly transcripted from matlab: results are the same as in matlab; I haven't checked that the code is valid but it seems.
    Original program of Bertus Talsma, adapted by Dirk Stelder in Gauss, transferred to Matlab by Maaike Bouwmeester.
    Matlab code can be found in /util/gras.m at https://cecilia2050.eu/system/files/cecilia_scenario_tool_version1.zip
    '''
    if not sp.issparse(A): print('Your matrix is not sparse, you should use gras instead.')
    if new_row_sums is None: u = sp.csc_matrix(A.sum(axis=1))
    else: u = sp.csc_matrix(new_row_sums)
    if new_col_sums is None: v = sp.csc_matrix(A.sum(axis=0))
    else: v = sp.csc_matrix(new_col_sums)
    if u.shape[0]<u.shape[1]: u = u.transpose()
    if v.shape[0]>v.shape[1]: v = v.transpose()
    nb_rows, nb_cols = A.shape
    sm = 0.00000000000000001
    converged = False
    P, N = A.multiply(A > 0), -A.multiply(A < 0)
    r, s = sp.csc_matrix(np.ones(nb_rows)).transpose(), sp.csc_matrix(np.ones(nb_cols)) # r,u,ppp,nnn are columns / s,v,pp,nn are rows
    improvements_saturated, iterator = 0, 1
    while iterator < max_iter:
        s_inv, r_inv = div0(1, s), div0(1, r)
        pp = sp.csc_matrix(mult_rows(P, r).sum(axis=0)) # pp[col] = (P[:,col] * r).sum()
        nn = sp.csc_matrix(mult_rows(N, r_inv).sum(axis=0)) # nn[col] = (N[:,col] * r_inv).sum()
        s = (v + (v.power(2) + 4*pp.multiply(nn)).power(0.5)) / (2*pp + sp.csc_matrix(sm*np.ones(nb_cols)))
        s_inv = sp.csc_matrix(div0(1, s))
        row_new = (mult_rows(sp.eye(nb_rows),r).dot(P).dot(mult_cols(sp.eye(nb_cols),s)) - \
                   mult_rows(sp.eye(nb_rows),r_inv).dot(N).dot(mult_cols(sp.eye(nb_cols), s_inv))).dot(sp.csc_matrix(np.ones(nb_cols)).transpose())
        eps1_abs = np.abs(row_new - u).sum()
        rel = np.abs(row_new / (u + sp.csc_matrix(sm*np.ones(nb_rows)).transpose()) - 1)
        rel[np.where(u.toarray()==0)] = 0
        eps1_rel = np.max(rel)
        ppp = sp.csc_matrix(mult_cols(P, s).dot(np.ones(nb_cols))).transpose() # mult_cols(P, s).sum(axis=1)
        nnn = sp.csc_matrix(mult_cols(N, s_inv).dot(np.ones(nb_cols))).transpose() # mult_cols(N, s_inv).sum(axis=1)
        r = (u + (u.power(2) + 4*ppp.multiply(nnn)).power(0.5)) / (2*ppp + sp.csc_matrix(sm*np.ones(nb_rows)).transpose())
        r_inv = sp.csc_matrix(div0(1, r))
        col_new = sp.csc_matrix(np.ones(nb_rows)).dot((mult_rows(sp.eye(nb_rows),r).dot(P).dot(mult_cols(sp.eye(nb_cols),s)) - \
                                                       mult_rows(sp.eye(nb_rows),r_inv).dot(N).dot(mult_cols(sp.eye(nb_cols),s_inv)))) # mult_rows(...)=diag(s)
        eps2_abs = np.abs(col_new - v).sum()
        rel = np.abs(col_new / (v + sp.csc_matrix(sm*np.ones(nb_cols))) - 1)
        rel[np.where(v.toarray()==0)] = 0
        eps2_rel = np.max(rel)
        if criterion == 'relative': tol_current = (eps1_rel + eps2_rel)/2
        else: tol_current = (eps1_abs + eps2_abs)/2
        if iterator > 1: improvement = (tol_previous - tol_current)/tol_previous
        else: improvement = tol + 1
        if (criterion in ['relative', 'absolute'] and tol_current < tol) or (criterion=='convergence' and iterator > 1 and improvements_saturated > 5):
            iterator = max_iter
            converged = True
#             print('converged')
        else: 
            if improvement < tol: improvements_saturated += 1
            iterator += 1
            tol_previous = tol_current
            if iterator>2: print(time.time()-time_i)
            time_i = time.time()
            print(iterator, tol_previous, improvement)
    if converged:
#         return(P-N) # why not simply this?
#         P = np.diag(r).dot(A).dot(np.diag(s))
#         N = np.diag(div0(1, r)).dot(A).dot(np.diag(div0(1, s)))
#         N[np.where(P>=0)] = 0
#         X = np.clip(P, 0, None) + N # TODO!: check if + and not -
        X = mult_rows(sp.eye(nb_rows),r).dot(P).dot(mult_cols(sp.eye(nb_cols),s))-\
                mult_rows(sp.eye(nb_rows),div0(1, r)).dot(N).dot(mult_cols(sp.eye(nb_cols),div0(1, s)))
        return(X)
    else: print('did not converged')