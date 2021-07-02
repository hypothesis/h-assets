# h-assets

This package provides Pyramid views for serving collections of compiled static
assets (eg. bundles of JavaScript and CSS).

**TODO:** Add some notes here about how h-assets differs from Pyramid's built-in
static views.

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
    that maps asset paths to URLs with cache-busting query strings.

   ```json
   {
     "scripts/app.bundle.js": "scripts/app.bundle.js?abcdef",
     "scripts/vendor.bundle.js": "scripts/vendor.bundle.js?xyz123"
   }
   ```

   Any format is allowed for the cache-buster. Hypothesis projects typically use
   the first few characters of a hash (eg. SHA-1) of the file's contents.

3. Create an INI file (eg. `assets.ini`) that defines collections ("bundles")
   of assets that are used together.

   ```ini
   [bundles]

   frontend_apps_js =
     scripts/browser_check.bundle.js
     scripts/frontend_apps.bundle.js

   frontend_apps_css =
     styles/frontend_apps.css
   ```

### Registering a Pyramid view to serve assets

To serve asses using h-assets, a Pyramid view needs to be created using the
`assets_view` function.

In the Pyramid app configuration, define a route where the URL is a base URL
followed by a `*subpath`:

```py
def includeme(config):
    config.add_route("assets", "/assets/*subpath")
```

To define the associated view, an asset `Environment` needs to be created which
handles generation of cache-busted asset URLs based on the bundle
configuration. Then a Pyramid view is defined which uses `assets_view` to
generate the view callable:

```py
import os.path

from h_assets import Environment, assets_view


def includeme(config):
    root_dir = os.path.dirname(__file__)

    assets_env = Environment(
        assets_base_url="/assets",
        bundle_config_path=f"{root_dir}/assets.ini",
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
in the templating engine being used to generate HTML responses. For example,
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

## Hacking

### Installing h-assets in a development environment

#### You will need

- [Git](https://git-scm.com/)

- [pyenv](https://github.com/pyenv/pyenv)
  Follow the instructions in the pyenv README to install it.
  The Homebrew method works best on macOS.
  On Ubuntu follow the Basic GitHub Checkout method.

#### Clone the git repo

```terminal
git clone https://github.com/hypothesis/h-assets.git
```

This will download the code into a `h-assets` directory
in your current working directory. You need to be in the
`h-assets` directory for the rest of the installation
process:

```terminal
cd h-assets
```

#### Run the tests

```terminal
make test
```

**That's it!** You’ve finished setting up your h-assets
development environment. Run `make help` to see all the commands that're
available for linting, code formatting, packaging, etc.

### Updating the Cookiecutter scaffolding

This project was created from the
https://github.com/hypothesis/h-cookiecutter-pypackage/ template.
If h-cookiecutter-pypackage itself has changed since this project was created, and
you want to update this project with the latest changes, you can "replay" the
cookiecutter over this project. Run:

```terminal
make template
```

**This will change the files in your working tree**, applying the latest
updates from the h-cookiecutter-pypackage template. Inspect and test the
changes, do any fixups that are needed, and then commit them to git and send a
pull request.

If you want `make template` to skip certain files, never changing them, add
these files to `"options.disable_replay"` in
[`.cookiecutter.json`](.cookiecutter.json) and commit that to git.

If you want `make template` to update a file that's listed in `disable_replay`
simply delete that file and then run `make template`, it'll recreate the file
for you.
