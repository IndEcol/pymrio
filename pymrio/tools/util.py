""" 
Utility function for pymrio

KST 20140502
"""

import numpy as np

def is_vector(inp):
    """ Returns true if the input can be interpreted as a 'true' vector

    Note
    ----
    Does only check dimensions, not if type is numeric
   
    Parameters
    ----------
    inp : numpy.ndarray or something that can be converted into ndarray 

    Returns
    -------
    Boolean
        True for vectors: ndim = 1 or ndim = 2 and shape of one axis = 1
        False for all other arrays
        None if inp is not a ndarray and cant be converted to one
    """
    
    if not isinstance(inp, np.ndarray):
        try:
            inp = np.asarray(inp)
        except:
            return None
    nr_dim = np.ndim(inp)
    if nr_dim == 1:
        return True
    elif (nr_dim == 2) and (1 in inp.shape):
        return True
    else: 
        return False

def build_agg_matrix(agg_vector, pos_dict=None):
    """ Builds a aggregation matrix based on mapping given in input as numerical or string vector.

    The aggregation matrix has the from nxm with 

    -n  new classificaction
    -m  old classification

    Parameters
    ----------
        agg_vector : list or vector like numpy ndarray(can be row or column vector)
            length m with position given for n and -1 if values should not be included
            or
            length m with id_string for the aggregation

        pos_dict : dictionary
            (only possible if agg_vector is given as string)
            output order for the new matrix
            must be given as dict with 'string in agg_vector' = pos(as int, -1 if value should not be included in the aggregation)

    Example 1:
        input vector: np.array([0, 1, 1, 2]) or ['a', 'b', 'b', 'c']
    
        agg matrix:

           m0  m1  m2  m3
        n0 1   0   0   0
        n1 0   1   1   0
        n2 0   0   0   1

    Example 2:
        input vector: np.array([1, 0, 0, 2]) or (['b', 'a', 'a', 'c'], dict(a=0,b=1,c=2))
    
        agg matrix:

           m0  m1  m2  m3
        n0 0   1   1   0
        n1 1   0   0   0
        n2 0   0   0   1
    """
    if isinstance(agg_vector, np.ndarray): agg_vector = agg_vector.flatten().tolist()

    if type(agg_vector[0]) == str:
        str_vector = agg_vector
        agg_vector = np.zeros(len(str_vector))
        if pos_dict:
            if len(pos_dict.keys()) != len(set(str_vector)):
                raise ValueError('Posistion elements inconsistent with aggregation vector')
            seen = pos_dict
        else:
            seen = {}
        counter = 0
        for ind,item in enumerate(str_vector):
            if item not in seen: 
                seen[item] = counter
                counter += 1
            agg_vector[ind] = seen[item]
    
    agg_vector = np.array(agg_vector, dtype=int)
    agg_vector = agg_vector.reshape((1,-1))
    row_corr = agg_vector
    col_corr = np.arange(agg_vector.size)

    agg_matrix = np.zeros((row_corr.max()+1,col_corr.max()+1))
    agg_matrix[row_corr,col_corr] = 1

    # set columns with -1 value to 0
    agg_matrix[np.tile(agg_vector==-1,(np.shape(agg_matrix)[0],1))] = 0
    
    return agg_matrix



def diagonalize_blocks(arr, blocksize):
    """ Diagonalize sections of columns of an array for the whole array

    Parameters
    ----------

    arr : numpy array
        Input array

    blocksize : int
        number of rows/colums forming one block

    Returns
    -------
    numpy ndarray with shape (columns 'arr' * blocksize, columns 'arr' * blocksize)

    Example
    --------

    arr:      output: (blocksize = 3)
        3 1     3 0 0 1 0 0 
        4 2     0 4 0 0 2 0
        5 3     0 0 5 0 0 3
        6 9     6 0 0 9 0 0 
        7 6     0 7 0 0 6 0 
        8 4     0 0 8 0 0 4
    """
    
    nr_col = arr.shape[1]
    nr_row = arr.shape[0]

    if np.mod(nr_row,blocksize):
        raise ValueError('Number of rows of the input array must be a multiple of blocksize')

    arr_diag = np.zeros((nr_row,blocksize*nr_col))

    for col_ind, col_val in enumerate(arr.T):
        col_start = col_ind*blocksize
        col_end   = blocksize + col_ind*blocksize
        for _ind in range(int(nr_row/blocksize)):
            row_start = _ind*blocksize
            row_end   = blocksize + _ind*blocksize
            arr_diag[row_start:row_end, col_start:col_end] = np.diag(col_val[row_start:row_end])

    return arr_diag

def set_block(arr, arr_block):
    """ Sets the diagonal blocks of an array to an given array
    
    Parameters
    ----------
    arr : numpy ndarray
        the original array
    block_arr : numpy ndarray 
        the block array for the new diagonal

    Returns 
    -------
    numpy ndarray (the modified array)
    
    """
    nr_col = arr.shape[1]
    nr_row = arr.shape[0]

    nr_col_block = arr_block.shape[1]
    nr_row_block = arr_block.shape[0]

    if np.mod(nr_row,nr_row_block) or np.mod(nr_col,nr_col_block):
        raise ValueError('Number of rows/columns of the input array must be a multiple of block shape')
    if nr_row/nr_row_block != nr_col/nr_col_block:
        raise ValueError('Block array can not be filled as diagonal blocks in the given array')

    col_ind = 0
    arr_out = arr.copy()

    for row_ind in range(int(nr_row/nr_row_block)):
        row_start = row_ind*nr_row_block
        row_end = nr_row_block+nr_row_block*row_ind
        col_start = row_ind*nr_col_block
        col_end = nr_col_block+nr_col_block*row_ind

        arr_out[row_start:row_end, col_start:col_end] = arr_block

    return arr_out

def unique_element(ll):
    """ returns unique elements from a list preserving the original order """
    seen = {}
    result = []
    for item in ll:
        if item in seen: continue
        seen[item] = 1
        result.append(item)
    return result
