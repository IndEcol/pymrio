# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.1
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Using the aggregation functionality of pymrio

# %% [markdown]
# Pymrio offers various possibilities to achieve an aggregation of a existing MRIO system.
# The following section will present all of them in turn, using the test MRIO system included in pymrio.
# The same concept can be applied to real life MRIOs.

# %% [markdown]
# Some of the examples rely in the [country converter coco](https://github.com/konstantinstadler/country_converter). The minimum version required is coco >= 0.6.3 - install the latest version with
# ```
# pip install country_converter --upgrade
# ```
# Coco can also be installed from the Anaconda Cloud - see the coco readme for further infos.

# %% [markdown]
# ## Loading the test mrio

# %% [markdown]
# First, we load and explore the test MRIO included in pymrio:

# %%
import numpy as np

import pymrio

# %%
io = pymrio.load_test()
io.calc_all()

# %%
print(
    "Sectors: {sec},\nRegions: {reg}".format(
        sec=io.get_sectors().tolist(), reg=io.get_regions().tolist()
    )
)

# %% [markdown]
# ## Aggregation using a numerical concordance matrix

# %% [markdown]
# This is the standard way to aggregate MRIOs when you work in Matlab.
# To do so, we need to set up a concordance matrix in which the columns correspond to the orignal classification and the rows to the aggregated one.

# %%
sec_agg_matrix = np.array(
    [[1, 0, 0, 0, 0, 0, 0, 0], [0, 1, 1, 1, 1, 0, 0, 0], [0, 0, 0, 0, 0, 1, 1, 1]]
)

reg_agg_matrix = np.array([[1, 1, 1, 0, 0, 0], [0, 0, 0, 1, 1, 1]])

# %%
io.aggregate(region_agg=reg_agg_matrix, sector_agg=sec_agg_matrix)

# %%
print(
    "Sectors: {sec},\nRegions: {reg}".format(
        sec=io.get_sectors().tolist(), reg=io.get_regions().tolist()
    )
)

# %%
io.calc_all()

# %%
io.emissions.D_cba

# %% [markdown]
# To use custom names for the aggregated sectors or regions, pass a list of names in order of rows in the concordance matrix:

# %%
io = (
    pymrio.load_test()
    .calc_all()
    .aggregate(
        region_agg=reg_agg_matrix,
        region_names=["World Region A", "World Region B"],
        inplace=False,
    )
)

# %%
io.get_regions()

# %% [markdown]
# ## Aggregation using a numerical vector

# %% [markdown]
# Pymrio also accepts the aggregatio information as numerical or string vector.
# For these, each entry in the vector assignes the sector/region to a aggregation group.
# Thus the two aggregation matrices from above (*sec_agg_matrix* and *reg_agg_matrix*) can also be represented as numerical or string vectors/lists:

# %%
sec_agg_vec = np.array([0, 1, 1, 1, 1, 2, 2, 2])
reg_agg_vec = ["R1", "R1", "R1", "R2", "R2", "R2"]

# %% [markdown]
# can also be represented as aggregation vector:

# %%
io_vec_agg = (
    pymrio.load_test()
    .calc_all()
    .aggregate(region_agg=reg_agg_vec, sector_agg=sec_agg_vec, inplace=False)
)

# %%
print(
    "Sectors: {sec},\nRegions: {reg}".format(
        sec=io_vec_agg.get_sectors().tolist(), reg=io_vec_agg.get_regions().tolist()
    )
)

# %%
io_vec_agg.emissions.D_cba_reg

# %% [markdown]
# ## Regional aggregation using the country converter coco

# %% [markdown]
# The previous examples are best suited if you want to reuse existing aggregation information.
# For new/ad hoc aggregation, the most user-friendly solution is to build the concordance with the [country converter coco](https://github.com/konstantinstadler/country_converter). The minimum version of coco required is 0.6.2. You can either use coco to build independent aggregations (first case below) or use the predefined classifications included in coco (second case - Example WIOD below).

# %%
import country_converter as coco

# %% [markdown]
# ### Independent aggregation

# %%
io = pymrio.load_test().calc_all()

# %%
reg_agg_coco = coco.agg_conc(
    original_countries=io.get_regions(),
    aggregates={
        "reg1": "World Region A",
        "reg2": "World Region A",
        "reg3": "World Region A",
    },
    missing_countries="World Region B",
)

# %%
io.aggregate(region_agg=reg_agg_coco)

# %%
print(
    "Sectors: {sec},\nRegions: {reg}".format(
        sec=io.get_sectors().tolist(), reg=io.get_regions().tolist()
    )
)

# %% [markdown]
# This can be passed directly to pymrio:

# %%
io.emissions.D_cba_reg

# %% [markdown]
# A pandas DataFrame corresponding to the output from *coco* can also be passed to *sector_agg* for aggregation.
# A sector aggregation package similar to the country converter is planned.

# %% [markdown]
# ### Using the build-in classifications - WIOD example

# %% [markdown]
# The country converter is most useful when you work with a MRIO which is included in coco. In that case you can just pass the desired country aggregation to coco and it returns the required aggregation matrix:

# %% [markdown]
# For the example here, we assume that a raw WIOD download is available at:

# %%
wiod_raw = "/tmp/mrios/WIOD2013"

# %% [markdown]
# We will parse the year 2000 and calculate the results:

# %%
wiod_orig = pymrio.parse_wiod(path=wiod_raw, year=2000).calc_all()

# %% [markdown]
# and then aggregate the database to first the EU countries and group the remaining countries based on OECD membership. In the example below, we single out Germany (DEU) to be not included in the aggregation:

# %%
wiod_agg_DEU_EU_OECD = wiod_orig.aggregate(
    region_agg=coco.agg_conc(
        original_countries="WIOD",
        aggregates=[{"DEU": "DEU"}, "EU", "OECD"],
        missing_countries="Other",
        merge_multiple_string=None,
    ),
    inplace=False,
)

# %% [markdown]
# We can then rename the regions to make the membership clearer:

# %%
wiod_agg_DEU_EU_OECD.rename_regions({"OECD": "OECDwoEU", "EU": "EUwoGermany"})

# %% [markdown]
# To see the result for the air emission footprints:

# %%
wiod_agg_DEU_EU_OECD.AIR.D_cba_reg

# %% [markdown]
# For further examples on the capabilities of the country converter see the [coco tutorial notebook](http://nbviewer.jupyter.org/github/konstantinstadler/country_converter/blob/master/doc/country_converter_aggregation_helper.ipynb)

# %% [markdown]
# ## Aggregation by renaming

# %% [markdown]
# One alternative method for aggregating the MRIO system is to rename specific regions and/or sectors to duplicated names.
# Duplicated sectors and regions can then be automatically aggregated. This makes most sense when having some categories of some kind (e.g. consumption categories) or detailed classification which can easily be broadened (e.g. A01, A02, which could be renamed all to A).
# In the example below, we will aggregate sectors to consumption categories using some predefined categories included in pymrio. Check the [Adjusting, Renaming and Restructuring notebook for more details.](adjusting.ipynb)

# %%
mrio = pymrio.load_test()

# %%
class_info = pymrio.get_classification("test")
rename_dict = class_info.get_sector_dict(
    orig=class_info.sectors.TestMrioName, new=class_info.sectors.Type
)

# %% [markdown]
# If we take a look at the rename_dict, we see that it maps several sectors of the original MRIO to combined regions (technically a many to one mapping).

# %%
rename_dict

# %% [markdown]
# Using this dict to rename sectors leads to an index with overlapping labels.

# %%
mrio.rename_sectors(rename_dict)
mrio.Z

# %% [markdown]
# Which can then be aggregated with

# %%
mrio.aggregate_duplicates()
mrio.Z

# %% [markdown]
# This method also comes handy when aggregating parts of the MRIO regions. E.g.:

# %%
region_convert = {"reg1": "Antarctica", "reg2": "Antarctica"}
mrio.rename_regions(region_convert).aggregate_duplicates()
mrio.Z

# %% [markdown]
# Which lets us calculate the footprint of the consumption category 'eat' in 'Antarctica':


# %%
mrio.calc_all()
mrio.emissions.D_cba.loc[:, ("Antarctica", "eat")]


# %% [markdown]
# ## Aggregation to one total sector / region

# %% [markdown]
# Both, *region_agg* and *sector_agg*, also accept a string as argument. This leads to the aggregation to one total region or sector for the full IO system.

# %%
pymrio.load_test().calc_all().aggregate(
    region_agg="global", sector_agg="total"
).emissions.D_cba


# %% [markdown]
# ## Pre- vs post-aggregation account calculations

# %% [markdown]
# It is generally recommended to calculate MRIO accounts with the highest detail possible and aggregated the results afterwards (post-aggregation - see for example [Steen-Olsen et al 2014](http://dx.doi.org/10.1080/09535314.2014.934325), [Stadler et al 2014](https://zenodo.org/record/1137670#.WlOSOhZG1O8) or [Koning et al 2015](https://doi.org/10.1016/j.ecolecon.2015.05.008).
#
# Pre-aggregation, that means the aggregation of MRIO sectors and regions before calculation of footprint accounts, might be necessary when dealing with MRIOs on computers with limited RAM resources. However, one should be aware that the results might change.
#
# Pymrio can handle both cases and can be used to highlight the differences. To do so, we use the two  concordance matrices defined at the beginning (*sec_agg_matrix* and *reg_agg_matrix*) and aggregate the test system before and after the calculation of the accounts:

# %%
io_pre = (
    pymrio.load_test()
    .aggregate(region_agg=reg_agg_matrix, sector_agg=sec_agg_matrix)
    .calc_all()
)
io_post = (
    pymrio.load_test()
    .calc_all()
    .aggregate(region_agg=reg_agg_matrix, sector_agg=sec_agg_matrix)
)

# %%
io_pre.emissions.D_cba

# %%
io_post.emissions.D_cba

# %% [markdown]
# The same results as in io_pre are obtained for io_post, if we recalculate the footprint accounts based on the aggregated system:

# %%
io_post.reset_all_full().calc_all().emissions.D_cba
