from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pymrio")
except PackageNotFoundError:
    __version__ = "unknown"
