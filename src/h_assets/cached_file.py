import configparser
import json
from os.path import getmtime

from pyramid.settings import aslist


class CachedFile:  # pylint:disable=too-few-public-methods
    """
    Parses content from a file and caches the result.

    _CachedFile reads a file at a given path and parses the content using a
    provided loader.
    """

    def __init__(self, path, loader, auto_reload):
        """
        Create the CachedFile object.

        :param path: The path to the file to load
        :param loader: A callable that parses content from a file
        :param auto_reload: If True, the parsed content is discarded if the
            mtime of the file changes.
        """

        self.path = path
        self._loader = loader
        self._auto_reload = auto_reload
        self._last_modified_time = None
        self._cached_content = None

    def load(self):
        """
        Return the content of the file parsed with the loader.

        The file is parsed when this is called for the first time and, if
        auto-reload is enabled, when the mtime of the file changes.
        """
        if self._cached_content and not self._auto_reload:
            return self._cached_content

        current_mtime = getmtime(self.path)
        if not self._cached_content or self._last_modified_time < current_mtime:
            with open(self.path) as handle:
                self._cached_content = self._loader(handle)

            self._last_modified_time = current_mtime

        return self._cached_content


class CachedJSONFile(CachedFile):
    def __init__(self, path, auto_reload):
        def load_manifest(file_):
            return json.load(file_)

        super().__init__(path=path, loader=load_manifest, auto_reload=auto_reload)


class CachedBundleFile(CachedFile):
    def __init__(self, path, auto_reload):
        super().__init__(path=path, loader=self._load_bundles, auto_reload=auto_reload)

    @classmethod
    def _load_bundles(cls, handle):
        """
        Parse a bundle config ini file.

        Returns a mapping of bundle name to files that make up the bundle.
        """

        parser = configparser.ConfigParser()
        parser.read_file(handle)
        return {k: aslist(v) for k, v in parser.items("bundles")}