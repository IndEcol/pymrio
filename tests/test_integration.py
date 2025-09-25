"""Testing functions for the full run.

This is based on
the small MRIO given within pymrio.

This tests the full computation and fileio.

Might be the slowest test to run - make optional if it takes to long.
"""
# %%
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
            M_values = np.array(
                [
                    [
                        0.53905275,
                        0.56458194,
                        0.00522754,
                        0.61727649,
                        0.01795329,
                        0.00576,
                        0.00901308,
                        0.03437755,
                        0.00190124,
                        0.65405409,
                        0.00217839,
                        0.00183373,
                        0.01318255,
                        0.00542445,
                        0.0124986,
                        0.01269937,
                        0.00225489,
                        0.00578084,
                        0.00764994,
                        0.606239,
                        0.06309964,
                        0.06737699,
                        0.03933411,
                        0.17613704,
                        0.0278522,
                        0.47281653,
                        0.00532731,
                        0.00304105,
                        0.33222835,
                        0.00719231,
                        0.00238421,
                        0.01539324,
                        0.57624233,
                        0.67447196,
                        0.0054573,
                        0.0026126,
                        0.50032504,
                        0.00493196,
                        0.03067217,
                        0.02587723,
                        0.00820916,
                        0.81204114,
                        0.0060531,
                        0.7988727,
                        0.16796353,
                        0.05810137,
                        0.00916826,
                        0.01801689,
                    ]
                ]
            )
            M_Ghosh_values = np.array(
                [
                    [0.5225561 ],
                    [0.65756216],
                    [0.00473417],
                    [0.5472355 ],
                    [0.01772519],
                    [0.00568822],
                    [0.00922866],
                    [0.03440748],
                    [0.00188181],
                    [0.75013998],
                    [0.00203768],
                    [0.00142178],
                    [0.01295829],
                    [0.00541751],
                    [0.01268766],
                    [0.01271283],
                    [0.00210632],
                    [0.00713347],
                    [0.0071196 ],
                    [0.58120523],
                    [0.06218467],
                    [0.06532605],
                    [0.04001635],
                    [0.17603932],
                    [0.02800893],
                    [0.49852299],
                    [0.00523151],
                    [0.00280954],
                    [0.32052008],
                    [0.00749766],
                    [0.00255429],
                    [0.01555917],
                    [0.57612848],
                    [0.69293328],
                    [0.00493526],
                    [0.00260152],
                    [0.49634848],
                    [0.00515573],
                    [0.03258598],
                    [0.02620705],
                    [0.00806297],
                    [0.86794689],
                    [0.00481975],
                    [0.64359805],
                    [0.15009733],
                    [0.05766786],
                    [0.00976597],
                    [0.01817829]
                ]
            )

    return results


def test_all_wo_ghosh(td_testmrio):
    """Full integration test, without ghosh.

    Checks:
    -) cba calculations
    -) M calculations
    -) concate extension
    """
    mr_nog = pymrio.load_test()
    mr_nog.calc_all(include_ghosh=False)

    assert "A" in mr_nog.get_DataFrame()
    assert "L" in mr_nog.get_DataFrame()
    assert "G" not in mr_nog.get_DataFrame()
    assert "B" not in mr_nog.get_DataFrame()

    npt.assert_allclose(
        td_testmrio.factor_inputs.D_imp_values,
        mr_nog.factor_inputs.D_imp_reg.values,
        rtol=1e-5,
    )
    npt.assert_allclose(
        td_testmrio.factor_inputs.M_values,
        mr_nog.factor_inputs.M.values,
        rtol=1e-5,
    )

    sat_new = pymrio.extension_concate(mr_nog.emissions, mr_nog.factor_inputs, new_extension_name="sat_new")

    assert len(sat_new.D_cba) == 3
    assert mr_nog.emissions.F.index[0] in sat_new.F.index
    assert mr_nog.factor_inputs.F.index[0] in sat_new.F_Y.index
    assert all(mr_nog.emissions.get_regions() == sat_new.get_regions())
    assert all(mr_nog.emissions.get_sectors() == sat_new.get_sectors())
    assert "M" in sat_new.get_DataFrame()
    assert "M_Ghosh" not in sat_new.get_DataFrame()


def test_all_with_ghosh(td_testmrio):
    """Full integration test, with ghosh calcualtion.

    Checks:
    -) cba calculations
    -) M calculations
    -) concate extension
    """
    mr_wig = pymrio.load_test()
    mr_wig.calc_all(include_ghosh=True)

    assert "A" in mr_wig.get_DataFrame()
    assert "L" in mr_wig.get_DataFrame()
    assert "G" in mr_wig.get_DataFrame()
    assert "B" in mr_wig.get_DataFrame()

    npt.assert_allclose(
        td_testmrio.factor_inputs.D_imp_values,
        mr_wig.factor_inputs.D_imp_reg.values,
        rtol=1e-5,
    )
    npt.assert_allclose(
        td_testmrio.factor_inputs.M_values,
        mr_wig.factor_inputs.M.values,
        rtol=1e-5,
    )
    npt.assert_allclose(
        td_testmrio.factor_inputs.M_Ghosh_values,
        mr_wig.factor_inputs.M_Ghosh.values,
        rtol=1e-5,
    )

    sat_new = pymrio.extension_concate(mr_wig.emissions, mr_wig.factor_inputs, new_extension_name="sat_new")

    assert len(sat_new.D_cba) == 3
    assert mr_wig.emissions.F.index[0] in sat_new.F.index
    assert mr_wig.factor_inputs.F.index[0] in sat_new.F_Y.index
    assert all(mr_wig.emissions.get_regions() == sat_new.get_regions())
    assert all(mr_wig.emissions.get_sectors() == sat_new.get_sectors())
    assert "M" in sat_new.get_DataFrame()
    assert "M_Ghosh" in sat_new.get_DataFrame()


def test_txt_zip_fileio(tmpdir):
    """Round trip with saving and loading the testmrio.

    Txt and zip format

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

    pymrio.archive(source=save_path, archive=zip_arc, remove_source=True, path_in_arc="test")

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


def test_parquet_fileio(tmpdir):
    """Round trip with saving and loading the testmrio in parquet."""
    mr = pymrio.load_test()

    save_path = str(tmpdir.mkdir("pymrio_test_parquet"))

    mr.save_all(save_path, table_format="parquet")

    mr_load = pymrio.load_all(save_path)

    assert mr_load == mr


def test_pickle_fileio(tmpdir):
    """Round trip with saving and loading the testmrio in pickle."""
    mr = pymrio.load_test()

    save_path = str(tmpdir.mkdir("pymrio_test_pickle"))

    mr.save_all(save_path, table_format="pickle")

    mr_load = pymrio.load_all(save_path)

    assert mr_load == mr

    # checking partial read


def test_partial_reads(tmpdir):
    """Test various partial reads possibilities."""
    mr = pymrio.load_test()
    mr.calc_all()

    assert "A" in mr.get_DataFrame()
    assert "Y" in mr.get_DataFrame()
    assert "D_cba" in mr.emissions.get_DataFrame()
    assert "D_pba" in mr.emissions.get_DataFrame()

    save_path = str(tmpdir.mkdir("pymrio_part_csv"))
    mr.save_all(save_path, table_format="csv")

    mr_load = pymrio.load_all(save_path, subset=["Z", "D_cba"])

    assert "Z" in mr_load.get_DataFrame()
    assert "A" not in mr_load.get_DataFrame()
    assert "Y" not in mr_load.get_DataFrame()
    assert "D_cba" in mr_load.emissions.get_DataFrame()
    assert "D_pba" not in mr_load.emissions.get_DataFrame()
    assert "F" not in mr_load.emissions.get_DataFrame()
    assert "D_cba" in mr_load.factor_inputs.get_DataFrame()
    assert "D_pba" not in mr_load.factor_inputs.get_DataFrame()
    assert "F" not in mr_load.factor_inputs.get_DataFrame()

    mr_load_emis = pymrio.load_all(save_path, subfolders="emissions", subset=["Z", "D_cba"])
    mr_load_emis2 = pymrio.load_all(save_path, subfolders=["emissions", "abc"], subset=["Z", "D_cba"])

    assert "Z" in mr_load_emis.get_DataFrame()
    assert "A" not in mr_load_emis.get_DataFrame()
    assert "Y" not in mr_load_emis.get_DataFrame()
    assert "D_cba" in mr_load_emis.emissions.get_DataFrame()
    assert "D_pba" not in mr_load_emis.emissions.get_DataFrame()
    assert "F" not in mr_load_emis.emissions.get_DataFrame()
    assert "factor_inputs" not in mr_load_emis.get_extensions()
    assert "Z" in mr_load_emis2.get_DataFrame()
    assert "A" not in mr_load_emis2.get_DataFrame()
    assert "Y" not in mr_load_emis2.get_DataFrame()
    assert "D_cba" in mr_load_emis2.emissions.get_DataFrame()
    assert "D_pba" not in mr_load_emis2.emissions.get_DataFrame()
    assert "F" not in mr_load_emis2.emissions.get_DataFrame()
    assert "factor_inputs" not in mr_load_emis2.get_extensions()

    mr_load_only_emis = pymrio.load_all(save_path, subfolders="emissions", include_core=False, subset=["Z", "D_cba"])
    assert "Z" not in mr_load_only_emis.get_DataFrame()
    assert "A" not in mr_load_only_emis.get_DataFrame()
    assert "Y" not in mr_load_only_emis.get_DataFrame()
    assert "D_cba" in mr_load_only_emis.emissions.get_DataFrame()
    assert "D_pba" not in mr_load_only_emis.emissions.get_DataFrame()
    assert "F" not in mr_load_only_emis.emissions.get_DataFrame()
    assert "factor_inputs" not in mr_load_only_emis.get_extensions()
    del mr_load_only_emis

    save_path_par = str(tmpdir.mkdir("pymrio_test_part_parquet"))

    mr.save_all(save_path_par, table_format="parquet")
    mr_load_only_emis = pymrio.load_all(
        save_path_par, subfolders="emissions", include_core=False, subset=["Z", "D_cba"]
    )
    assert "Z" not in mr_load_only_emis.get_DataFrame()
    assert "A" not in mr_load_only_emis.get_DataFrame()
    assert "Y" not in mr_load_only_emis.get_DataFrame()
    assert "D_cba" in mr_load_only_emis.emissions.get_DataFrame()
    assert "D_pba" not in mr_load_only_emis.emissions.get_DataFrame()
    assert "F" not in mr_load_only_emis.emissions.get_DataFrame()
    assert "factor_inputs" not in mr_load_only_emis.get_extensions()


def test_reports(tmpdir):
    """Tests the reporting function.

    Here, only the correct file and folder structure
    is tested. The actual graphical output gets tested
    in test_outputs.
    """
    mr = pymrio.load_test().calc_all()

    save_path = str(tmpdir.mkdir("pymrio_test_reports"))

    with pytest.raises(ValueError):
        mr.report_accounts(path=save_path, per_capita=False, per_region=False, format="html")

    mr.report_accounts(path=save_path, per_capita=True, format="html")

    file_content = os.listdir(save_path)
    for ext in mr.get_extensions(data=True):
        assert ext.name.replace(" ", "_") + "_per_capita.html" in file_content
        assert ext.name.replace(" ", "_") + "_per_region.html" in file_content

        cap_pic_file_content = os.listdir(os.path.join(save_path, ext.name.replace(" ", "_") + "_per_capita"))
        reg_pic_file_content = os.listdir(os.path.join(save_path, ext.name.replace(" ", "_") + "_per_region"))

        assert "png" in cap_pic_file_content[0]
        assert "png" in reg_pic_file_content[0]
