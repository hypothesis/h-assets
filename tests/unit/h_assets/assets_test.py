from configparser import ConfigParser
from unittest.mock import create_autospec, sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound
from pyramid.testing import DummyRequest

from h_assets.assets import Environment, assets_view


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
        CachedINIFile = patch("h_assets.assets.CachedINIFile")

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
        CachedJSONFile = patch("h_assets.assets.CachedJSONFile")

        CachedJSONFile.return_value.load.return_value = {
            "app.bundle.js": "app.bundle.js?hash_app",
            "vendor.bundle.js": "vendor.bundle.js?hash_vendor",
        }

        return CachedJSONFile


class TestAssetsView:
    def test_it_returns_static_view_response_if_cache_buster_valid(
        self, static_view, environment
    ):
        environment.check_cache_buster.return_value = True
        request = DummyRequest(query_string=sentinel.query)
        request.path = "/path"

        response = assets_view(environment)(sentinel.context, request)

        environment.check_cache_buster.assert_called_once_with("/path", sentinel.query)

        static_view.assert_called_once_with(
            environment.asset_root.return_value, cache_max_age=None, use_subpath=True
        )
        static_view.return_value.assert_called_with(sentinel.context, request)
        assert response == static_view.return_value.return_value

    def test_it_returns_404_if_cache_buster_invalid(self, environment, static_view):
        environment.check_cache_buster.return_value = False

        response = assets_view(environment)({}, DummyRequest())

        static_view.return_value.assert_not_called()
        assert isinstance(response, HTTPNotFound)

    @pytest.fixture
    def environment(self):
        return create_autospec(Environment, instance=True, spec_set=True)

    @pytest.fixture(autouse=True)
    def static_view(self, patch):
        return patch("h_assets.assets.static_view")
