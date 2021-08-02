"""View helpers."""

from pyramid.httpexceptions import HTTPNotFound
from pyramid.static import static_view

from h_assets.environment import Environment


def assets_view(environment: Environment):
    """Return a Pyramid view which serves static assets from `environment`."""

    static = static_view(environment.asset_root(), cache_max_age=None, use_subpath=True)

    def wrapper(context, request):
        # If a cache-busting query string is provided, verify that it is correct.
        if request.query_string and not environment.check_cache_buster(
            request.path, request.query_string
        ):
            return HTTPNotFound()

        return static(context, request)

    return wrapper
