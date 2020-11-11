""" Testing functions for the full run based on
the small MRIO given within pymrio.

This tests the full computation and fileio.

Might be the slowest test to run - make optional if it takes to long.
"""

import os
import sys

import numpy as np
import numpy.testing as npt
import pytest

TESTPATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(TESTPATH, ".."))

import pymrio  # noqa


@pytest.fixture()
def td_testmrio():
    """Results from the test mrio calculation.

    This works with the test system given in pymrio.

    """

    class results:
        class factor_inputs:
            D_imp_values = np.array(
                [
                    [
                        2382767.5387909594,
                        2393134.584113787,
                        2972317.803194902,
                        4201655.226133792,
                        1428782.8385865367,
                        6693276.934870526,
                    ]  # noqa
                ]
            )

    return results


def test_all(td_testmrio):
    """Full integration test

    Checks:
    1) the cba calculation
    2) concate extension
    """
    mr = pymrio.load_test()
    mr.calc_all()
    npt.assert_allclose(
        td_testmrio.factor_inputs.D_imp_values,
        mr.factor_inputs.D_imp_reg.values,
        rtol=1e-5,
    )
    sat_new = pymrio.concate_extension(mr.emissions, mr.factor_inputs, name="sat_new")

    assert len(sat_new.D_cba) == 3
    assert mr.emissions.F.index[0] in sat_new.F.index
    assert mr.factor_inputs.F.index[0] in sat_new.F_Y.index
    assert all(mr.emissions.get_regions() == sat_new.get_regions())
    assert all(mr.emissions.get_sectors() == sat_new.get_sectors())


def test_fileio(tmpdir):
    """Round trip with saving and loading the testmrio

    Also tests some fileio related util functions
    """
    mr = pymrio.load_test()

    save_path = str(tmpdir.mkdir("pymrio_test"))

    with pytest.raises(ValueError):
        mr.save_all(save_path, table_format="nan")

    mr.save_all(save_path)

    # Testing getting the repo content, some random sample test
    fc = pymrio.get_repo_content(save_path)
    assert fc.iszip is False
    assert "Z.txt" in [os.path.basename(f) for f in fc.filelist]
    assert "F_Y.txt" in [os.path.basename(f) for f in fc.filelist]
    assert "unit.txt" in [os.path.basename(f) for f in fc.filelist]

    mr2 = pymrio.load_all(save_path)
    npt.assert_allclose(mr.Z.values, mr2.Z.values, rtol=1e-5)

    # Testing the zip archive functions
    zip_arc = os.path.join(save_path, "test_mrio.zip")
    if os.path.exists(zip_arc):
        os.remove(zip_arc)

    with pytest.raises(FileExistsError):
        pymrio.archive(
            source=fc.filelist,
            archive=zip_arc,
            remove_source=False,
            path_in_arc="test_duplicates",
        )

        pymrio.archive(
            source=fc.filelist,
            archive=zip_arc,
            remove_source=False,
            path_in_arc="test_duplicates",
        )

    if os.path.exists(zip_arc):
        os.remove(zip_arc)

    pymrio.archive(
        source=save_path, archive=zip_arc, remove_source=True, path_in_arc="test"
    )

    fc = pymrio.get_repo_content(zip_arc)
    assert fc.iszip is True
    assert "Z.txt" in [os.path.basename(f) for f in fc.filelist]
    assert "F_Y.txt" in [os.path.basename(f) for f in fc.filelist]
    assert "unit.txt" in [os.path.basename(f) for f in fc.filelist]

    emissions = pymrio.load(zip_arc, path_in_arc="test/emissions")
    npt.assert_allclose(mr.emissions.F.values, emissions.F.values, rtol=1e-5)

    mr3 = pymrio.load_all(zip_arc)
    npt.assert_allclose(mr.Z.values, mr3.Z.values, rtol=1e-5)

    with pytest.raises(pymrio.ReadError):
        pymrio.load_all(zip_arc, path_in_arc="./foo")

    with pytest.raises(pymrio.ReadError):
        pymrio.load(path="./foo")


def test_reports(tmpdir):
    """Tests the reporting function

    Here, only the correct file and folder structure
    is tested. The actual graphical output gets tested
    in test_outputs.
    """
    mr = pymrio.load_test().calc_all()

    save_path = str(tmpdir.mkdir("pymrio_test_reports"))

    with pytest.raises(ValueError):
        mr.report_accounts(
            path=save_path, per_capita=False, per_region=False, format="html"
        )

    mr.report_accounts(path=save_path, per_capita=True, format="html")

    file_content = os.listdir(save_path)
    for ext in mr.get_extensions(data=True):
        assert ext.name.replace(" ", "_") + "_per_capita.html" in file_content
        assert ext.name.replace(" ", "_") + "_per_region.html" in file_content

        cap_pic_file_content = os.listdir(
            os.path.join(save_path, ext.name.replace(" ", "_") + "_per_capita")
        )
        reg_pic_file_content = os.listdir(
            os.path.join(save_path, ext.name.replace(" ", "_") + "_per_region")
        )

        assert "png" in cap_pic_file_content[0]
        assert "png" in reg_pic_file_content[0]
