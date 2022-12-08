Compared to Pyramid's builtin [static asset
functionality](https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/assets.html)
, this provides a convenient way to serve assets based on certain assumptions
about how assets are generated and opinions about how they should be served:

- The assets are assumed to be compiled artefacts in an output directory
  populated by frontend build tooling, rather than source files inside the
  Python package. Typically Hypothesis applications use a `build` directory in
  the root of the repository.
- Cache busting is always enabled and is done via query strings. These query
  strings are checked, if present, when serving a request to avoid responses
  being stored under the wrong keys in downstream caches.
- It is assumed that compressing bytes (eg. with gzip or Brotli) will be
  handled by a service like Cloudflare, not the Python application.

Additionally h-assets provides a way to define collections (_bundles_) of
assets and methods to generate cache-busted URLs for all assets in the bundle.
This is useful for example to render all the `<script>` or `<style>` tags that
are needed by a certain part of a site.

## Usage

Using h-assets in a Pyramid project involves three steps:

 1. Prepare the compiled assets for use with h-assets
 2. During Pyramid application configuration, create an asset `Environment`
    to handle asset URL generation and register a view to serve assets from that
    environment
 3. Expose the URL-generation methods from the asset `Environment` to your
    templating system so that templates can generate asset URLs

### Preparing assets for use with h-assets

1. Set up a process to compile or copy assets from source files into an
   output directory. Conventionally Hypothesis projects use a folder called
   `build` in the repository root.
2. In the output directory generate a JSON manifest file (eg. `manifest.json`)
    that maps asset paths to URLs with cache-busting query strings. Example content:

   ```json
   {
     "scripts/app.bundle.js": "scripts/app.bundle.js?abcdef",
     "scripts/vendor.bundle.js": "scripts/vendor.bundle.js?xyz123"
   }
   ```

   Any format is allowed for the cache-buster. Hypothesis projects typically use
   the first few characters of a hash (eg. SHA-1) of the file's contents.

3. Create an INI file (eg. `assets.ini`) that defines collections ("bundles")
   of assets that are used together. Example content:

   ```ini
   [bundles]

   frontend_apps_js =
     scripts/browser_check.bundle.js
     scripts/frontend_apps.bundle.js

   frontend_apps_css =
     styles/frontend_apps.css
   ```

### Registering a Pyramid view to serve assets

To serve assets using h-assets, a Pyramid view needs to be created using the
`assets_view` function.

In the Pyramid app configuration, define a route where the URL is a base URL
followed by a `*subpath`:

```py
def includeme(config):
    config.add_route("assets", "/assets/*subpath")
```

To register the view associated with this route, first create an `Environment`
to handle generation of asset URLs. Then use `assets_view` to create the view
callable for use with `config.add_view`:

```py
import os.path

from h_assets import Environment, assets_view


def includeme(config):
    # This assumes the following repository structure:
    #   build/ - Compiled frontend assets
    #     manifest.json
    #   projectname/
    #     assets.py - This module
    #     routes.py - Route definitions
    #     assets.ini
    root_dir = os.path.dirname(__file__)

    assets_env = Environment(
        assets_base_url="/assets",
        bundle_config_path="{root_dir}/assets.ini",
        manifest_path=f"{root_dir}/../build/manifest.json",
    )

    # Store asset environment in registry for use in registering `asset_urls`
    # Jinja2 helper in `app.py`.
    config.registry["assets_env"] = assets_env

    config.add_view(route_name="assets", view=assets_view(assets_env))
```

### Referencing assets in templates

To get a list of asset URLs for assets in a bundle, use the `urls` method of the
asset `Environment`. A common pattern is to expose these methods as global helpers
in the templating environment being used to generate HTML responses. For example,
in a project using `pyramid_jinja2`:

```py
jinja2_env = config.get_jinja2_environment()
jinja2_env.globals["asset_url"] = config.registry["assets_env"].url
jinja2_env.globals["asset_urls"] = config.registry["assets_env"].urls
```

Then a template can generate URLs using:

```jinja2
{% for url in asset_urls("frontend_apps_js") %}
  <script async defer src="{{ url }}"></script>
{% endfor %}
```
