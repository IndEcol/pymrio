# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.4
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Exploring MRIOs with Pymrio

# %% [markdown]
# The first step when working with a new MRIO data set is to familiarize yourself with the data.
# This notebook shows how to use the `pymrio` package to explore the data.
# We use the test data set that is included in the `pymrio` package.
# This is a completely artificial, very small MRIO.
# It is not meant to be realistic, but it is useful for developing, testing and learning.


# %% [markdown]
# First we import the required packages:

# %%
import pymrio

# %% [markdown]
# We can now load the test data set with the `load_test` function. We can call
# the MRIO whatever we want, here we use mrio.

# %%
mrio = pymrio.load_test()

# %% [markdown]
# We can get some first information about the MRIO by printing it.

# %%
print(mrio)

# %% [markdown]
# This tells us what the MRIO data we just loaded contains.
# We find a Z and Y matrix, some unit information and two satellite accounts, factor_inputs and emissions.

# %% [markdown]
# To get more specific data we can ask pymrio for regions, sectors, products, etc.

# %%
mrio.name

# %%
mrio.get_regions()

# %%
mrio.get_sectors()

# %%
mrio.get_Y_categories()

# %% [markdown]
# The same methods can be used to explore one of the satellite accounts.

# %%
print(mrio.emissions)

# %%
mrio.emissions.name
# %%
mrio.emissions.get_regions()


# %% [markdown]
# The satellite accounts also have a special method to get index (rows) of the acccounts.

# %%
mrio.emissions.get_rows()

# %% [markdown]
# # Searching through the MRIO

# %% [markdown]
# Several methods are available to search through the whole MRIO.
# These generally accept [regular expressions](https://docs.python.org/3/howto/regex.html) as search terms.

# %% [markdown]
# The most general method is 'find'. This can be used for a quick overview where a specific term appears in the MRIO.


# %%
mrio.find("air")

# %%
mrio.find("trade")

# %% [markdown]
# Not that 'find' (and all other search methods) a case sensitive.
# Do make a case insensitive search, add the regular expression flag `(?i)` to the search term.

# %%
mrio.find("value")

# %%
mrio.find("(?i)value")

# %% [markdown]
# ## Specific search methods: contains, match, fullmatch,

# %% [markdown]
# The MRIO class also contains a set of specific regular expresion search methods, mirroring the 'contains', 'match' and 'fullmatch'
# methods of the pandas DataFrame str column type. See the pandas documentation for details, in short:
#
#   - 'contains' looks for a match anywhere in the string
#   - 'match' looks for a match at the beginning of the string
#   - 'fullmatch' looks for a match of the whole string
#
# These methods are available for all index columns of the MRIO and have a similar signature:
#
#   1. As for 'find_all', the search term is case sensitive. To make it case insensitive, add the regular expression flag `(?i)` to the search term.
#   2. The search term can be passed to the keyword argument 'find_all' or as the first positional argument to search in all index levels.
#   3. Alternativels, the search term can be passed to the keyword argument with the level name to search only in that index level.
#
# The following examples show how to use these methods.

# %%
mrio.contains(find_all="ad")
mrio.contains("ad")  # find_all is the default argument

# %%
mrio.match("ad")

# %%
mrio.match("trad")

# %%
mrio.fullmatch("trad")

# %%
mrio.fullmatch("trade")

# %%
mrio.fullmatch("(?i).*AD.*")

# %% [markdown]
# For the rest of the notebook, we will do the examples with the 'contains' method, but the same applies to the other methods.

# %% [markdown]
# To search only at one specific level, pass the search term to the keyword argument with the level name.

# %%
mrio.contains(region="trade")

# %%
mrio.contains(sector="trade")

# %% [markdown]
# And of course, the method are also available for the satellite accounts.

# %%
mrio.emissions.contains(compartment="air")

# %% [markdown]
# Passing a non-existing level to the keyword argument is silently ignored.

# %%
mrio.factor_inputs.contains(compartment="trade")

# %% [markdown]
# This allows to search for terms that are only in some index levels.
# Logically, this is an 'or' search.
# %%
mrio.factor_inputs.contains(compartment="air", inputtype="Value")

# %% [markdown]
# But note, that if both levels exist, both must match (so it becomes a logical 'and').

# %%
mrio.emissions.contains(stressor="emission", compartment="air")

# %% [markdown]
# ## Search through all extensions

# %% [markdown]
# All three search methods are also available to loop through all extensions of the MRIO.

# %%
mrio.extension_contains(stressor="emission", compartment="air")

# %% [markdown]
# If only a subset of extensions should be searched, pass the extension names to the keyword argument 'extensions'.

# %% [markdown]
# ## Generic search method for any dataframe index

# %% [markdown]
# Internally, the class methods 'contains', 'match' and 'fullmatch' all the
# 'index_contains', 'index_match' and 'index_fullmatch' methods of ioutil module.
# This function can be used to search through index of any pandas DataFrame.

# %%
df = mrio.Y

# %% [markdown]
# Depending if a dataframe or an index is passed, the return is either the dataframe or the index.

# %%
pymrio.index_contains(df, "trade")

# %%
pymrio.index_contains(df.index, "trade")

# %%
pymrio.index_fullmatch(df, region="reg[2,4]", sector="m.*")

# %% [markdown]
# All search methods can easily be combined with the extract methods to extract the data that was found.
# For more information on this, see the [extract_data](./extract_data.ipynb) notebook.
