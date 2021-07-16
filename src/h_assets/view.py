"""View helpers."""

from pyramid.httpexceptions import HTTPNotFound
from pyramid.static import static_view

from h_assets.environment import Environment


def assets_view(environment: Environment):
    """Return a Pyramid view which serves static assets from `environment`."""

    static = static_view(environment.asset_root(), cache_max_age=None, use_subpath=True)

    def wrapper(context, request):
        if not environment.check_cache_buster(request.path, request.query_string):
            return HTTPNotFound()

        return static(context, request)

    return wrapper
