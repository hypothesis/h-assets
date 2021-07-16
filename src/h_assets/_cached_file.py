"""Objects for reading and caching various file formats."""

import json
from configparser import ConfigParser
from os.path import getmtime


class CachedFile:  # pylint:disable=too-few-public-methods
    """Parses content from a file and caches the result."""

    path = None

    def __init__(self, path, auto_reload):
        """
        Create the CachedFile object.

        :param path: Path of the file to load
        :param auto_reload: Reload the contents of the file if they change
            based on last modified time
        """

        self.path = path
        self._auto_reload = auto_reload
        self._last_modified_time = None
        self._cached_content = None

    def load(self):
        """
        Return the content of the file.

        If auto-reload is enabled, this will automatically return the most up
        to date file contents by monitoring the last modified time (mtime).
        """

        current_mtime = getmtime(self.path)

        if not self._cached_content or (
            self._auto_reload and self._last_modified_time < current_mtime
        ):
            with open(self.path) as handle:
                self._cached_content = self._load_handle(handle)

            self._last_modified_time = current_mtime

        return self._cached_content

    @classmethod
    def _load_handle(cls, handle):
        """
        Return the contents of the passed handle.

        This function is to allow customisation by sub-classes.
        """
        return handle.read()


class CachedJSONFile(CachedFile):  # pylint: disable=too-few-public-methods
    """Cached and decode JSON files."""

    @classmethod
    def _load_handle(cls, handle):
        """Parse a JSON file returning the decoded Python data structure."""

        return json.load(handle)


class CachedINIFile(CachedFile):  # pylint: disable=too-few-public-methods
    """Cache and decode an INI file."""

    @classmethod
    def _load_handle(cls, handle) -> ConfigParser:
        """Parse a bundle config ini file."""

        parser = ConfigParser()
        parser.read_file(handle)
        return parser
