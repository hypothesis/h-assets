from configparser import ConfigParser

import pytest

from h_assets._cached_file import CachedFile, CachedINIFile, CachedJSONFile


class TestCachedJSONFile:
    def test_it_parses_json(self, tmpdir):
        json_file = tmpdir / "manifest.json"
        json_file.write('{"a": 1}')

        content = CachedJSONFile(json_file, auto_reload=True).load()

        assert content == {"a": 1}


class TestCachedINIFile:
    def test_it_parses_ini_files(self, tmpdir):
        ini_file = tmpdir / "data.ini"
        ini_file.write("[section]\nkey = value")

        content = CachedINIFile(ini_file, auto_reload=True).load()

        assert isinstance(content, ConfigParser)
        assert content.items("section") == [("key", "value")]


class TestCachedFile:
    @pytest.mark.parametrize("auto_reload", (True, False))
    def test_it_loads_the_file_content(self, file, auto_reload):
        cached_file = CachedFile(file, auto_reload=auto_reload)

        content = cached_file.load()

        assert content == "file-content"

    @pytest.mark.parametrize("auto_reload", (True, False))
    def test_it_reloads_file_content(self, file, auto_reload, getmtime):
        cached_file = CachedFile(file, auto_reload=auto_reload)
        cached_file.load()  # Load once to set the modified time
        getmtime.return_value += 1  # Advance the last modified time
        file.write("new-file-content")

        content = cached_file.load()

        assert content == "new-file-content" if auto_reload else "file-content"

    @pytest.fixture
    def file(self, tmpdir):
        file = tmpdir / "filename.txt"
        file.write("file-content")

        return file

    @pytest.fixture(autouse=True)
    def getmtime(self, patch):
        getmtime = patch("h_assets._cached_file.getmtime")
        getmtime.return_value = 1000

        return getmtime
