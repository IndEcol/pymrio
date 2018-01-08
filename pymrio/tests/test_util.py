""" test cases for all util functions """

import os
import sys
import numpy as np
from unittest.mock import mock_open, patch
from collections import namedtuple

import pytest

_pymriopath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _pymriopath + '/../../')


from pymrio.tools.ioutil import find_first_number          # noqa
from pymrio.tools.ioutil import sniff_csv_format           # noqa
from pymrio.tools.ioutil import build_agg_matrix           # noqa
from pymrio.tools.ioutil import build_agg_vec           # noqa


@pytest.fixture()
def csv_test_files_content():
    test_para = namedtuple('test_para', ['text',
                                         'sep',
                                         'header_rows',
                                         'index_col'])

    class example_csv_content():
        test_contents = [
            test_para(text=("""idx1,idx2,col1,col2
                               a,b,1,2
                               c,d,2,4\n"""),
                      sep=',',
                      header_rows=1,
                      index_col=2),
            test_para(text=("""idx1,col1,col2
                               a,1,2
                               c,2,4\n"""),
                      sep=',',
                      header_rows=1,
                      index_col=1),
            test_para(text=("""idx1;col1;col2
                               a;1;2
                               c;2;4\n"""),
                      sep=';',
                      header_rows=1,
                      index_col=1),
            test_para(text=(""";col1;col2
                               ;l;d
                               a;1;2
                               c;2;4\n"""),
                      sep=';',
                      header_rows=2,
                      index_col=1),
            test_para(text=("""|col1|col2
                               |l|d
                               a|f|g
                               c|e|l\n"""),
                      sep='|',
                      header_rows=None,
                      index_col=None),
            test_para(text=(""";col1;col2
                               ;l;d
                               a;f;3
                               c;e;l\n"""),
                      sep=';',
                      header_rows=None,
                      index_col=None),
            test_para(text=(""";col1;col2
                               ;l;d
                               a;f;l
                               c;e;3\n"""),
                      sep=';',
                      header_rows=3,
                      index_col=2),
            ]
    return example_csv_content


def test_find_first_number():
    """ Some tests for finding the first number in a sequence"""
    assert find_first_number([0, 1, 2, 3]) == 0
    assert find_first_number(['a', 1, 2, 3]) == 1
    assert find_first_number(['a', 1, 'c', 3]) == 1
    assert find_first_number([None, 1, 'c', 3]) == 1
    assert find_first_number(['a', 'b']) == None  # noqa
    assert find_first_number([]) == None   # noqa


def test_dev_read(csv_test_files_content):
    """ Tests the csv sniffer
    """
    for tests in csv_test_files_content.test_contents:
        with patch('builtins.open',
                   mock_open(read_data=tests.text),
                   create=False) as mo:    # noqa
            res = sniff_csv_format('foo')
        assert res['sep'] == tests.sep
        assert res['nr_index_col'] == tests.index_col
        assert res['nr_header_row'] == tests.header_rows


def test_build_agg_matrix():
    """ Tests building the aggreagation matrix
    """

    am_num = build_agg_matrix([1, 0, 0, 1, 0])
    expected = np.array([[0.,  1.,  1.,  0.,  1.],
                         [1.,  0.,  0.,  1.,  0.]])
    am_str = build_agg_matrix(['r2', 'r1', 'r1', 'r2', 'r1'],
                              pos_dict={'r1': 0, 'r2': 1})

    np.testing.assert_allclose(am_num, expected)
    np.testing.assert_allclose(am_str, expected)


def test_build_agg_vec():
    """ Simple test based on the test mrio
    """
    vec = build_agg_vec(['OECD', 'EU'], path='test', miss='RoW')
    expected = ['OECD', 'EU', 'OECD', 'OECD', 'RoW', 'RoW']
    assert vec == expected
