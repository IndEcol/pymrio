from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("pymrio")
except PackageNotFoundError:
    __version__ = "unknown"
