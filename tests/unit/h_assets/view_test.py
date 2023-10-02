from unittest.mock import create_autospec, sentinel

import pytest
from pyramid.httpexceptions import HTTPNotFound
from pyramid.testing import DummyRequest

from h_assets.environment import Environment
from h_assets.view import assets_view


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

    def test_it_returns_static_view_response_if_cache_buster_missing(
        self, static_view, environment
    ):
        request = DummyRequest(query_string="")
        request.path = "/path"

        response = assets_view(environment)(sentinel.context, request)

        environment.check_cache_buster.assert_not_called()

        static_view.assert_called_once_with(
            environment.asset_root.return_value, cache_max_age=None, use_subpath=True
        )
        static_view.return_value.assert_called_with(sentinel.context, request)
        assert response == static_view.return_value.return_value

    def test_it_returns_404_if_cache_buster_invalid(self, environment, static_view):
        environment.check_cache_buster.return_value = False

        response = assets_view(environment)({}, DummyRequest(query_string="invalid"))

        static_view.return_value.assert_not_called()
        assert isinstance(response, HTTPNotFound)

        # Returns "*" though set to `True`
        assert response.cache_control.no_cache  # pylint: disable=no-member

    @pytest.fixture
    def environment(self):
        return create_autospec(Environment, instance=True, spec_set=True)

    @pytest.fixture(autouse=True)
    def static_view(self, patch):
        return patch("h_assets.view.static_view")
