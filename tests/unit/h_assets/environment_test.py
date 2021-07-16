from configparser import ConfigParser
from unittest.mock import sentinel

import pytest

from h_assets.environment import Environment


class TestEnvironment:
    def test_initialisation(self, CachedINIFile, CachedJSONFile):
        environment = Environment(
            assets_base_url=sentinel.assets_base_url,
            bundle_config_path=sentinel.bundle_ini,
            manifest_path=sentinel.manifest_json,
            auto_reload=sentinel.auto_reload,
        )

        assert environment.assets_base_url == sentinel.assets_base_url
        CachedINIFile.assert_called_once_with(
            sentinel.bundle_ini, auto_reload=sentinel.auto_reload
        )
        assert environment.bundle_file == CachedINIFile.return_value
        CachedJSONFile.assert_called_once_with(
            sentinel.manifest_json, auto_reload=sentinel.auto_reload
        )
        assert environment.manifest_file == CachedJSONFile.return_value

    def test_files(self, environment):
        assert environment.files("app_js") == ["app.bundle.js", "vendor.bundle.js"]

    def test_asset_root(self, environment):
        environment.manifest_file.path = "/some_path/file.name"
        assert environment.asset_root() == "/some_path"

    @pytest.mark.parametrize(
        "path,query,is_valid",
        (
            ("app.bundle.js", "hash_app", True),
            ("/assets/app.bundle.js", "hash_app", True),
            ("app.bundle.js", "WRONG", False),
            ("vendor.bundle.js", "hash_vendor", True),
            ("vendor.bundle.js", "WRONG", False),
            ("not_a_file", "*any*", False),
        ),
    )
    def test_check_cache_buster(self, environment, path, query, is_valid):
        assert environment.check_cache_buster(path, query) == is_valid

    @pytest.mark.parametrize(
        "path,expected",
        (
            ("app.bundle.js", "/assets/app.bundle.js?hash_app"),
            ("vendor.bundle.js", "/assets/vendor.bundle.js?hash_vendor"),
        ),
    )
    def test_url(self, environment, path, expected):
        assert environment.url(path) == expected

    def test_urls(self, environment):
        assert environment.urls("app_js") == [
            "/assets/app.bundle.js?hash_app",
            "/assets/vendor.bundle.js?hash_vendor",
        ]

    @pytest.fixture
    def environment(self):
        return Environment(
            "/assets",
            bundle_config_path=sentinel.bundle_ini,
            manifest_path=sentinel.manifest_json,
            auto_reload=sentinel.auto_reload,
        )

    @pytest.fixture(autouse=True)
    def CachedINIFile(self, patch):
        CachedINIFile = patch("h_assets.environment.CachedINIFile")

        parser = ConfigParser()
        parser.read_dict(
            {
                "bundles": {
                    "app_js": "app.bundle.js\nvendor.bundle.js",
                }
            }
        )

        CachedINIFile.return_value.load.return_value = parser

        return CachedINIFile

    @pytest.fixture(autouse=True)
    def CachedJSONFile(self, patch):
        CachedJSONFile = patch("h_assets.environment.CachedJSONFile")

        CachedJSONFile.return_value.load.return_value = {
            "app.bundle.js": "app.bundle.js?hash_app",
            "vendor.bundle.js": "vendor.bundle.js?hash_vendor",
        }

        return CachedJSONFile
