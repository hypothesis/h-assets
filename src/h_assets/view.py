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
            response = HTTPNotFound()

            # Disable downstream caching of failed responses, in case this
            # happened due to version skew during a deployment. See
            # https://github.com/hypothesis/h-assets/issues/27.
            response.cache_control.no_cache = True

            return response

        return static(context, request)

    return wrapper
