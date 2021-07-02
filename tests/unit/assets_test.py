from io import StringIO

import pytest
from pyramid.httpexceptions import HTTPNotFound
from pyramid.testing import DummyRequest

from h_assets import Environment, assets_view


class TestEnvironment:
    def test_files_lists_bundle_files(self, mtime):
        env = Environment("/assets", "bundles.ini", "manifest.json")

        assert env.files("app_js") == ["app.bundle.js", "vendor.bundle.js"]

    def test_urls_generates_bundle_urls(self, mtime):
        env = Environment("/assets", "bundles.ini", "manifest.json")

        assert env.urls("app_js") == [
            "/assets/app.bundle.js?abcdef",
            "/assets/vendor.bundle.js?1234",
        ]

    def test_url_returns_cache_busted_url(self, mtime):
        env = Environment("/assets", "bundles.ini", "manifest.json")

        assert env.url("app.bundle.js") == "/assets/app.bundle.js?abcdef"

    @pytest.mark.parametrize("auto_reload", [True, False])
    def test_reloads_manifest_on_change(self, mtime, open_file, auto_reload):
        manifest_content = '{"app.bundle.js":"app.bundle.js?oldhash"}'
        bundle_content = "[bundles]\napp_js = \n  app.bundle.js"

        def fake_open(path):
            if path == "bundles.ini":
                return StringIO(bundle_content)
            elif path == "manifest.json":
                return StringIO(manifest_content)

        open_file.side_effect = fake_open

        mtime.return_value = 100
        env = Environment(
            "/assets", "bundles.ini", "manifest.json", auto_reload=auto_reload
        )

        # An initial call to urls() should read and cache the manifest
        env.urls("app_js")

        manifest_content = '{"app.bundle.js":"app.bundle.js?newhash"}'
        assert env.urls("app_js") == ["/assets/app.bundle.js?oldhash"]

        # Once the manifest's mtime changes, the Environment should re-read
        # the manifest
        mtime.return_value = 101

        if auto_reload:
            assert env.urls("app_js") == ["/assets/app.bundle.js?newhash"]
        else:
            assert env.urls("app_js") == ["/assets/app.bundle.js?oldhash"]

    @pytest.mark.parametrize(
        "path,query,valid",
        [
            # Valid path and correct cache-buster
            ("/assets/app.bundle.js", "abcdef", True),
            # Valid path, but incorrect or missing cache-buster
            ("/assets/app.bundle.js", "wrong", False),
            ("/assets/app.bundle.js", "", False),
            # Invalid path
            ("/assets/does-not-exist.js", "whatever", False),
        ],
    )
    def test_check_cache_buster_returns_True_if_valid(self, path, query, valid):
        env = Environment("/assets", "bundles.ini", "manifest.json")
        assert env.check_cache_buster(path, query) is valid


class TestAssetsView:
    def test_it_returns_static_view_response_if_cache_buster_valid(self, static_view):
        env = Environment("/assets", "bundles.ini", "manifest.json")
        view = assets_view(env)
        static_view_callable = static_view.return_value
        request = DummyRequest(path="/assets/app.bundle.js", query_string="abcdef")

        response = view({}, request)

        static_view_callable.assert_called_with({}, request)
        assert response == static_view_callable.return_value

    def test_it_returns_404_if_cache_buster_invalid(self, static_view):
        env = Environment("/assets", "bundles.ini", "manifest.json")
        static_view_callable = static_view.return_value
        view = assets_view(env)

        response = view({}, DummyRequest("/assets/app.bundle.js", query_string="wrong"))
        static_view_callable.assert_not_called()

        assert isinstance(response, HTTPNotFound)

    def test_it_returns_404_if_path_invalid(self, static_view):
        env = Environment("/assets", "bundles.ini", "manifest.json")
        static_view_callable = static_view.return_value
        view = assets_view(env)

        response = view({}, DummyRequest("/assets/invalid.js"))
        static_view_callable.assert_not_called()

        assert isinstance(response, HTTPNotFound)

    @pytest.fixture(autouse=True)
    def static_view(self, patch):
        return patch("h_assets.assets.static_view")


@pytest.fixture(autouse=True)
def mtime(patch):
    return patch("h_assets.assets.getmtime")


@pytest.fixture(autouse=True)
def open_file(patch):
    bundle_content = """
    [bundles]
    app_js =
      app.bundle.js
      vendor.bundle.js
    """

    manifest_content = """
    {
        "app.bundle.js": "app.bundle.js?abcdef",
        "vendor.bundle.js": "vendor.bundle.js?1234"
    }
    """

    def fake_open(path):
        if path == "bundles.ini":
            return StringIO(bundle_content)
        elif path == "manifest.json":
            return StringIO(manifest_content)

    # nb. `autospec=False` is required when patching a builtin to avoid conflict
    # with implicitly added `create=True`.
    return patch("h_assets.assets.open", autospec=False, side_effect=fake_open)
