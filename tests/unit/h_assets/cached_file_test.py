import pytest

from h_assets.cached_file import CachedFile


class TestCachedFile:
    @pytest.mark.parametrize("auto_reload", (True, False))
    def test_it_loads_the_file_content(self, file, loader, auto_reload):
        cached_file = CachedFile(file, loader=loader, auto_reload=auto_reload)

        content = cached_file.load()

        assert content == "file-content+loader"

    @pytest.mark.parametrize("auto_reload", (True, False))
    def test_it_reloads_file_content(self, file, loader, auto_reload, getmtime):
        cached_file = CachedFile(file, loader=loader, auto_reload=auto_reload)
        cached_file.load()  # Load once to set the modified time
        getmtime.return_value += 1  # Advance the last modified time
        file.write("new-file-content")

        content = cached_file.load()

        assert (
            content == "new-file-content+loader"
            if auto_reload
            else "file-content+loader"
        )

    @pytest.fixture
    def loader(self):
        def loader(handle):
            return handle.read() + "+loader"

        return loader

    @pytest.fixture
    def file(self, tmpdir):
        file = tmpdir / "filename.txt"
        file.write("file-content")

        return file

    @pytest.fixture(autouse=True)
    def getmtime(self, patch):
        getmtime = patch("h_assets.cached_file.getmtime")
        getmtime.return_value = 1000

        return getmtime
