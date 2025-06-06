"""
Various constant values

KST 20140903
"""

import os
from pathlib import Path

# path information of the package
__ROOT = Path(os.path.dirname(__file__))
PYMRIO_PATH = {
    "test_mrio": Path(__ROOT / "../mrio_models/test_mrio").absolute(),
    "test_mrio_data": Path(__ROOT / "../mrio_models/test_mrio/mrio_data").absolute(),
    "testmrio": Path(__ROOT / "../mrio_models/test_mrio").absolute(),
    "test": Path(__ROOT / "../mrio_models/test_mrio").absolute(),
    # TODO remove "exio2": just here to keep the tests running
    "exio2": Path(__ROOT / "../mrio_models/exio2_pxp").absolute(),
    "exio2_pxp": Path(__ROOT / "../mrio_models/exio2_pxp").absolute(),
    "exio2_ixi": Path(__ROOT / "../mrio_models/exio2_ixi").absolute(),
    "exio3_pxp": Path(__ROOT / "../mrio_models/exio3_pxp").absolute(),
    "exio3_ixi": Path(__ROOT / "../mrio_models/exio3_ixi").absolute(),
}

# generic names (needed for the aggregation  if no names are given)
GENERIC_NAMES = {
    "sector": "sec",
    "region": "reg",
    "iosys": "IOSystem",
    "ext": "Extension",
}

DEFAULT_FILE_NAMES = {
    "filepara": "file_parameters.json",
    "metadata": "metadata.json",
    "download_log": "download_log.json",
}

MISSING_AGG_ENTRY = {
    "region": "Unspecified region",
    "sector": "Unspecified sector",
}

STORAGE_FORMAT = {
    "txt": ["txt", "tsv", "csv"],
    "parquet": ["parquet", "par", "parq"],
    "pickle": ["pickle", "pkl"],
}

# The default column name for the value column for long table format
LONG_VALUE_NAME = "value"


#  Download links for Gloria MRIO files
GLORIA_URLS = {
    "053": [
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACPnp0qOD1N7CSjv0reFKSba/previous_releases/053/MRIO/GLORIA_MRIOs_53_2006.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACD6UmIBqbmkAQiAOfX7U_fa/previous_releases/053/MRIO/GLORIA_MRIOs_53_1997.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAD6y_13ul9SZnJkPV1GhZCza/previous_releases/053/MRIO/GLORIA_MRIOs_53_2013.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAA5bFH6uzjqhm6fowdMlkyLa/previous_releases/053/MRIO/GLORIA_MRIOs_53_1996.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAB3PLbnxPHIP2MGN8S36ZUBa/previous_releases/053/MRIO/GLORIA_MRIOs_53_2007.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABIfGIVZkelhq58Ij1DKO1Va/previous_releases/053/MRIO/GLORIA_MRIOs_53_2012.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAqOhcAo8jFU_GhTu1fzOKWa/previous_releases/053/MRIO/GLORIA_MRIOs_53_2010.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABspySp6y4Jh2OaLrTlSeY_a/previous_releases/053/MRIO/GLORIA_MRIOs_53_1994.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABAXczzTGbWj8i-ho0fSTsLa/previous_releases/053/MRIO/GLORIA_MRIOs_53_2005.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABK94uXvjIdWzrgCP5uxk6Wa/previous_releases/053/MRIO/GLORIA_MRIOs_53_2019.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABTfP3rpj_QkIPyPIJqVo62a/previous_releases/053/MRIO/GLORIA_MRIOs_53_2018.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABW9BpSx6h83gpmyCnVfKZ-a/previous_releases/053/MRIO/GLORIA_MRIOs_53_2011.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AADvhpsqMor0wvNFLD-zWcRAa/previous_releases/053/MRIO/GLORIA_MRIOs_53_2004.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AADS3ffwpUxjkoLlQneJrrUDa/previous_releases/053/MRIO/GLORIA_MRIOs_53_1995.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABdMfXMCF6b3HqTJEjyQkTsa/previous_releases/053/MRIO/GLORIA_MRIOs_53_2009.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAfHBfF-5N0ZaYr-gwfJKSya/previous_releases/053/MRIO/GLORIA_MRIOs_53_1998.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AADWa9MT3qH_YAVwlqb2-eEBa/previous_releases/053/MRIO/GLORIA_MRIOs_53_2015.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABT4WkwUQt_5KbPsWMgUUFba/previous_releases/053/MRIO/GLORIA_MRIOs_53_1991.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABfxaEEsKc8MKndscJMxilha/previous_releases/053/MRIO/GLORIA_MRIOs_53_2000.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAB7j7bikNb1q3RhTyyLB9mQa/previous_releases/053/MRIO/GLORIA_MRIOs_53_2014.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABrkCHIOdLU5zUmHuI8nDKma/previous_releases/053/MRIO/GLORIA_MRIOs_53_2001.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAW_BEqaeIvAzmFE6oYz8rKa/previous_releases/053/MRIO/GLORIA_MRIOs_53_1990.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAB2ktuivgPwclQXVNQbh_Afa/previous_releases/053/MRIO/GLORIA_MRIOs_53_1999.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AADyg36facQvwueC6r85yEY8a/previous_releases/053/MRIO/GLORIA_MRIOs_53_2008.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAA7Z0xEExKNK91GvinGGk9va/previous_releases/053/MRIO/GLORIA_MRIOs_53_2003.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAD1rYcXCwCvNxC4wV8apUFCa/previous_releases/053/MRIO/GLORIA_MRIOs_53_1992.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAD-J1n98SSYniRLSNfEe0kJa/previous_releases/053/MRIO/GLORIA_MRIOs_53_2016.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAQc9jieTHGraE9nRGha1g4a/previous_releases/053/MRIO/GLORIA_MRIOs_53_1993.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAzRQsWiNc6Wu_5mOXAV1YIa/previous_releases/053/MRIO/GLORIA_MRIOs_53_2002.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AADPrsw4iWytQ9ItCpJ8ZqwIa/previous_releases/053/MRIO/GLORIA_MRIOs_53_2017.zip?dl=0",
    ],
    "054": [
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAC7K5dfdnOA3I_CJm4Bu0nHa/previous_releases/054/MRIO/GLORIA_MRIOs_54_2016.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACO5ce_FtnXN-w8ZykcqrCYa/previous_releases/054/MRIO/GLORIA_MRIOs_54_2003.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACvnqqeofEQPAG0X-BWxNRta/previous_releases/054/MRIO/GLORIA_MRIOs_54_1992.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABXuHtPoMajYNR5YH18Frf_a/previous_releases/054/MRIO/GLORIA_MRIOs_54_2017.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACOfDR7Jtk83cEzFQwktbGja/previous_releases/054/MRIO/GLORIA_MRIOs_54_1993.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACmf_zQswJz60ZWzorQ6Bpua/previous_releases/054/MRIO/GLORIA_MRIOs_54_2002.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AADXNVDIgSjiTq2XYZBOp3TXa/previous_releases/054/MRIO/GLORIA_MRIOs_54_1991.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABpxrh-7mFDL6va4d6Z3E_za/previous_releases/054/MRIO/GLORIA_MRIOs_54_2000.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACwD1DOvsiLNxsMreU3Vo3ua/previous_releases/054/MRIO/GLORIA_MRIOs_54_2015.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABlYAdTmli3iDfM3li2OAxxa/previous_releases/054/MRIO/GLORIA_MRIOs_54_2009.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAB-HUu421eE7VkH0yQV6KwAa/previous_releases/054/MRIO/GLORIA_MRIOs_54_1998.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACqNzqTjYXrR6cJ7fpp2-_ua/previous_releases/054/MRIO/GLORIA_MRIOs_54_1999.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABPAFDyayr8LUfTr1R8F6DAa/previous_releases/054/MRIO/GLORIA_MRIOs_54_2008.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAB1In5emdB928-a0B1j_Uo0a/previous_releases/054/MRIO/GLORIA_MRIOs_54_2001.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABHnhwWKGOYcSMyXFxCS7Dfa/previous_releases/054/MRIO/GLORIA_MRIOs_54_1990.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AADZ2etvFvgEUOoCWRHgfUcNa/previous_releases/054/MRIO/GLORIA_MRIOs_54_2014.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAB5bz-aVrQVkj5ZSuAuGhuAa/previous_releases/054/MRIO/GLORIA_MRIOs_54_2019.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACHEcV9TmcUUIXxd2trwzj0a/previous_releases/054/MRIO/GLORIA_MRIOs_54_1994.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAADEQMUbcrbfItvHEgs9Tqxa/previous_releases/054/MRIO/GLORIA_MRIOs_54_2005.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAAC8oUPc0Bf_xpiS-vMeWNa/previous_releases/054/MRIO/GLORIA_MRIOs_54_2010.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACiG4RqHNhtOTvNkqPGvFEsa/previous_releases/054/MRIO/GLORIA_MRIOs_54_2004.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAA7I_SrhI8gklR7Za2drsNFa/previous_releases/054/MRIO/GLORIA_MRIOs_54_1995.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACmGlhuY9zeijQCdllbwkdpa/previous_releases/054/MRIO/GLORIA_MRIOs_54_2011.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAD8snAscs6LFBF4mRlo7qsfa/previous_releases/054/MRIO/GLORIA_MRIOs_54_2018.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACr37Rp_r7nbxaUgv8TzvlHa/previous_releases/054/MRIO/GLORIA_MRIOs_54_2013.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAujo-1iMVSz7N3ozLLN3Zga/previous_releases/054/MRIO/GLORIA_MRIOs_54_2006.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAt3nE7WeWQxzkeVtabsm4Sa/previous_releases/054/MRIO/GLORIA_MRIOs_54_1997.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABFO3rlAXAI9MuZfd-KQ-9ia/previous_releases/054/MRIO/GLORIA_MRIOs_54_2012.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAB4j8NBysXu4MkgvZYmrSwfa/previous_releases/054/MRIO/GLORIA_MRIOs_54_1996.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAC-XyiKcDOn9TYmeDPKjyfna/previous_releases/054/MRIO/GLORIA_MRIOs_54_2007.zip?dl=0",
    ],
    "055": [
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACmYOJiT8mK1uHLQlCgn4Oya/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_1990.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAD11mTRGEtcqf1dRMFtQrYza/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_1991.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAljBvDe2kgEL7AjDOPfF5Ca/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_1992.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACdxKvPfZo8JzkQIJxbo3rxa/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_1993.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACFPwnkn4sWCdzmxXTXNLJKa/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_1994.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABnBRFa0IY4iS8yU3U3bQ-ca/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_1995.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAC1Ms5inScRNGD_UtqRZ4cba/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_1996.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABzqn-iNshbGn3PV2rDgOEma/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_1997.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAfXq94cK9HgqDGRw0Av51Ra/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_1998.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABPCBRPcNkDgIKV0f4Aoh-aa/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_1999.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABeYfN4oPwiHGMVvrdM2H7ia/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2000.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABbWD78TEiNbnZs5pZkMNSaa/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2001.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AADwlWrpZShpxWm0frKPU3Aja/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2002.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACFSmp0PcO7UeRmC8xokRwea/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2003.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAc6MD3-u6nvoPgg3cL9tvoa/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2004.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAC2cg37BrUzSg3pQg3CxnLDa/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2005.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACF6A0mQQ9UwvsBKCU05z0va/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2006.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAATYbJBOR6XHN6H4QRAC6tFa/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2007.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAJ-gud5eL1kgvJvXAT-3zja/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2008.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAA5EQmc0cDiVe6KfOsnZXesa/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2009.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACTtJbqQWeSNVe1Z0jYJ_rra/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2010.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AADttP2Z4KGdU4mnd58f0w2Sa/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2011.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AADS7y82yMnifEnpPHPuoxITa/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2012.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACSkVqnHjhc1k9NY_3uDgJFa/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2013.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AADxMiz9payAd6cpgxoUDIw4a/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2014.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAC9BjOyOaaSENX_DfMcIU-qa/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2015.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAD3y0caXYJPtvvZezhXEQUUa/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2016.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAF9FaRBH7Hk1r48GYcilfGa/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2017.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACyvsy2YPCAFqBgHC2YZWaba/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2018.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AADSHS7zJ05U5Zm4FUtrldpRa/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2019.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAA_hJiYUEo8gVZbqp7HCgMPa/previous_releases/055/GLORIA_MRIO_Loop055_part_I_MRIOdatabase/GLORIA_MRIOs_55_2020.zip?dl=0",
    ],
    "057": [
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAILpkD09rQ_bAeeWDZuE3aa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_1990.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABt_nByH1FuML746fiALCEAa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_1991.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACUtfp-ZS1SbjF7bdILg_ZAa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_1992.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAW5l8EqE9_Ejreqb5_qLdUa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_1993.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAU4AFSGoeYUJQhZC5_u_lha/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_1994.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACK97tQE7V1OYpJ9wa7ab7da/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_1995.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACXilhQsMeCgsupXjohYpEma/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_1996.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAB_C_8kESAFr4770dhhV51Ya/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_1997.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABmQag5TZCeaouETVKbFsppa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_1998.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABQ_-L9l_7wJWF50QTdOCZTa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_1999.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACh7azwKIUvyyOgTM4K5A9Ta/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2000.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAClJDe_V5KD6j-bq0ImrZda/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2001.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAC1j_FPoic70F6G5Kuaw3fUa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2002.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAK11s6S112EKxUwWPgbHxVa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2003.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AADC0tZBKH_kp5sxvkK_hQC8a/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2004.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAj-vEmgmrbfFEhN6rNi8D0a/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2005.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAB0UtTXqf5xH2zqBxvrrA8za/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2006.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AADw_eRYFWulRfLkQwFVmryNa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2007.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAC2346imGfZo88BZFwmIqEga/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2008.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAhfCAMfMyxOqHC4R5m1Mzqa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2009.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACaJ9PVcSxSS0lYjG01Wb0Ga/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2010.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AADMPuCtsivFzTMcNhH9H15Ia/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2011.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABbw6LJJSPmuZGobw2vffpDa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2012.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACyvVf4ZaCtUJ6YfZsbITYwa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2013.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACposoILlF8OETb20yh4st7a/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2014.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAE0UCMywuaUk72q15STq7Qa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2015.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AADOL4JYoO9WFKKij1h27m4fa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2016.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACyDpP4C4juFk7n1LOJyq5fa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2017.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACvB106Cw7vxUEiu_un5WYAa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2018.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAD_3uLb7NYSKnZhg6YyWSSna/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2019.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAdrXgf7Ie4K8wE3WxgMhKVa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2020.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACOZnEwhznnyneXanq_QEvia/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2021.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAAuKImX1cnJBAWzke3Mv4BRa/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2022.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AADN-i7oupC0I7hmQmXMwrSia/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2023.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AABt_-yvC5HxFclnWomiBmZ3a/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2024.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAB9JR7HbgkHPUtO5TwVcPvva/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2025.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AAASkSkOcuLYyx7J9Rby_xo1a/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2026.zip?dl=0",
        "https://dl.dropboxusercontent.com/sh/o4fxq94n7grvdbk/AACp-7VsPPfwlnjMOY3uZ2Gna/latest_release/057/GLORIA_MRIO_Loop057_part_I_MRIOdatabase/GLORIA_MRIOs_57_2027.zip?dl=0",
    ],
}
