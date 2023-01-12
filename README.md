<a href="https://github.com/hypothesis/h-assets/actions/workflows/ci.yml?query=branch%3Amain"><img src="https://img.shields.io/github/actions/workflow/status/hypothesis/h-assets/ci.yml?branch=main"></a>
<a href="https://pypi.org/project/h-assets"><img src="https://img.shields.io/pypi/v/h-assets"></a>
<a><img src="https://img.shields.io/badge/python-3.9 | 3.8-success"></a>
<a href="https://github.com/hypothesis/h-assets/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-BSD--2--Clause-success"></a>
<a href="https://github.com/hypothesis/cookiecutters/tree/main/pypackage"><img src="https://img.shields.io/badge/cookiecutter-pypackage-success"></a>
<a href="https://black.readthedocs.io/en/stable/"><img src="https://img.shields.io/badge/code%20style-black-000000"></a>

# h-assets

Pyramid views for serving collections of compiled static assets (eg. bundles of JavaScript and CSS).

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

## Setting up Your h-assets Development Environment

First you'll need to install:

* [Git](https://git-scm.com/).
  On Ubuntu: `sudo apt install git`, on macOS: `brew install git`.
* [GNU Make](https://www.gnu.org/software/make/).
  This is probably already installed, run `make --version` to check.
* [pyenv](https://github.com/pyenv/pyenv).
  Follow the instructions in pyenv's README to install it.
  The **Homebrew** method works best on macOS.
  The **Basic GitHub Checkout** method works best on Ubuntu.
  You _don't_ need to set up pyenv's shell integration ("shims"), you can
  [use pyenv without shims](https://github.com/pyenv/pyenv#using-pyenv-without-shims).

Then to set up your development environment:

```terminal
git clone https://github.com/hypothesis/h-assets.git
cd h-assets
make help
```

## Releasing a New Version of the Project

1. First, to get PyPI publishing working you need to go to:
   <https://github.com/organizations/hypothesis/settings/secrets/actions/PYPI_TOKEN>
   and add h-assets to the `PYPI_TOKEN` secret's selected
   repositories.

2. Now that the h-assets project has access to the `PYPI_TOKEN` secret
   you can release a new version by just [creating a new GitHub release](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).
   Publishing a new GitHub release will automatically trigger
   [a GitHub Actions workflow](.github/workflows/pypi.yml)
   that will build the new version of your Python package and upload it to
   <https://pypi.org/project/h-assets>.

## Changing the Project's Python Versions

To change what versions of Python the project uses:

1. Change the Python versions in the
   [cookiecutter.json](.cookiecutter/cookiecutter.json) file. For example:

   ```json
   "python_versions": "3.10.4, 3.9.12",
   ```

2. Re-run the cookiecutter template:

   ```terminal
   make template
   ```

3. Commit everything to git and send a pull request

## Changing the Project's Python Dependencies

To change the production dependencies in the `setup.cfg` file:

1. Change the dependencies in the [`.cookiecutter/includes/setuptools/install_requires`](.cookiecutter/includes/setuptools/install_requires) file.
   If this file doesn't exist yet create it and add some dependencies to it.
   For example:

   ```
   pyramid
   sqlalchemy
   celery
   ```

2. Re-run the cookiecutter template:

   ```terminal
   make template
   ```

3. Commit everything to git and send a pull request

To change the project's formatting, linting and test dependencies:

1. Change the dependencies in the [`.cookiecutter/includes/tox/deps`](.cookiecutter/includes/tox/deps) file.
   If this file doesn't exist yet create it and add some dependencies to it.
   Use tox's [factor-conditional settings](https://tox.wiki/en/latest/config.html#factors-and-factor-conditional-settings)
   to limit which environment(s) each dependency is used in.
   For example:

   ```
   lint: flake8,
   format: autopep8,
   lint,tests: pytest-faker,
   ```

2. Re-run the cookiecutter template:

   ```terminal
   make template
   ```

3. Commit everything to git and send a pull request
