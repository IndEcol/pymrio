from setuptools import find_packages, setup

exec(open("pymrio/version.py").read())

setup(
    name="pymrio",
    description=(
        "A python module for automating input output "
        "calculations and generating reports"
    ),
    long_description=open("README.rst").read(),
    url="https://github.com/konstantinstadler/pymrio",
    author="Konstantin Stadler",
    author_email="konstantin.stadler@ntnu.no",
    version=__version__,  # noqa
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.7.0",
    package_data={
        "": ["*.txt", "*.dat", "*.doc", "*.rst", "*.json"],
    },
    # This some needs to be here and in requirments.txt (for conda)
    install_requires=[
        "pandas >= 1.0",
        "numpy >= 1.20",
        "matplotlib >= 2.0.0",
        "requests >= 2.18",
        "xlrd > 1.1.0 ",
        "openpyxl >= 3.0.6",
        "docutils >= 0.14",
    ],
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering",
        "Topic :: Utilities",
    ],
)
