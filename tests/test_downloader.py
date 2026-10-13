"""Tests for the downloader, with the network calls replaced by local data."""

import io
import os
import zipfile

import pymrio.tools.iodownloader as iodownloader


class _FakeResponse:
    def __init__(self, content):
        self.content = content

    def iter_content(self, chunk_size):
        for start in range(0, len(self.content), chunk_size):
            yield self.content[start : start + chunk_size]


def _fake_oecd_v2023(url, subfolder="", **kwargs):
    """Return a zip shaped like an OECD v2023 bundle, with one csv per year."""
    bundle = next(yy for yy, uu in iodownloader.OECD_CONFIG["datafiles"]["v2023"].items() if uu == url)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        for year in range(int(bundle[:4]), int(bundle[-4:]) + 1):
            zf.writestr(f"{subfolder}{year}_SML.csv", "data")
    return _FakeResponse(buffer.getvalue())


def test_download_oecd_v2023_repeated(tmp_path, monkeypatch):
    """A second download must neither rename files nor download again (#156)."""
    calls = []

    def fake_ssl_fix(url, **kwargs):
        calls.append(url)
        return _fake_oecd_v2023(url, **kwargs)

    monkeypatch.setattr(iodownloader, "ssl_fix", fake_ssl_fix)

    iodownloader.download_oecd(tmp_path, years="1995-2000")
    expected = {f"ICIO2023_{year}.csv" for year in range(1995, 2001)} | {"download_log.json"}
    assert set(os.listdir(tmp_path)) == expected
    assert len(calls) == 1

    iodownloader.download_oecd(tmp_path, years=[1995, 2001])
    expected |= {f"ICIO2023_{year}.csv" for year in range(2001, 2006)}
    assert set(os.listdir(tmp_path)) == expected
    assert len(calls) == 2

    iodownloader.download_oecd(tmp_path, years="1995-2000", overwrite_existing=True)
    assert set(os.listdir(tmp_path)) == expected
    assert len(calls) == 3


def test_download_oecd_v2023_subfolder(tmp_path, monkeypatch):
    """A zip holding a folder gets the folder renamed, with its files inside."""
    monkeypatch.setattr(iodownloader, "ssl_fix", lambda url, **kw: _fake_oecd_v2023(url, subfolder="data/"))

    iodownloader.download_oecd(tmp_path, years="1995-2000")
    assert set(os.listdir(tmp_path)) == {"ICIO2023_data", "download_log.json"}
    assert len(os.listdir(tmp_path / "ICIO2023_data")) == 6
