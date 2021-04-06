# Matrix Specification

This repository contains the Matrix Specification, rendered at [spec.matrix.org](http://spec.matrix.org/).

Developers looking to use Matrix should join [#matrix-dev:matrix.org](http://matrix.to/#/#matrix-dev:matrix.org)
on Matrix for help.

Spec authors and proposal writers are welcome to join [#matrix-spec:matrix.org](http://matrix.to/#/#matrix-spec:matrix.org). We welcome contributions! See [CONTRIBUTING.rst](./CONTRIBUTING.rst) for details.

## Structure

The Matrix spec is compiled with [Hugo](https://gohugo.io/) (a static site generator) with the following structure:

* `/assets`: assets that need postprocessing using [Hugo Pipes](https://gohugo.io/hugo-pipes/introduction/).
  For example, Sass files would go here.

* `/content`: files that will become pages in the site go here. Typically these are Markdown files with some YAML front
  matter indicating, [among other things](https://gohugo.io/content-management/front-matter/), what layout should be
  applied to this page. The organization of files under `/content` determines the organization of pages in the built
  site.

* `/data`: this can contain TOML, YAML, or JSON files. Files kept here are directly available to template code as
  [data objects](https://gohugo.io/templates/data-templates/), so templates don't need to load them from a file and
  parse them. This is also where our

* `/layouts`: this contains [Hugo templates](https://gohugo.io/templates/). Some templates define the overall layout of
  a page: for example, whether it has header, footer, sidebar, and so on.
    * `/layouts/partials`: these templates can be called from other templates, so they can be used to factor out
      template code that's used in more than one template. An obvious example here is something like a sidebar, where
      several different page layouts might all include the sidebar. But also, partial templates can return values: this
      means they can be used like functions, that can be called by multiple templates to do some common processing.
    * `/layouts/shortcodes`: these templates can be called directly from files in `/content`.

* `/static`: static files which don't need preprocessing. JS or CSS files could live here.

* `/themes`: you can use just Hugo or use it with a theme. Themes primarily provide additional templates, which are
  supplied in a `/themes/$theme_name/layouts` directory. You can use a theme but customise it by providing your own
  versions of any of the theme layouts in the base `/layouts` directory. That is, if a theme provides
  `/themes/$theme_name/layouts/sidebar.html` and you provide `/layouts/sidebar.html`, then your version of the
  template will be used.

It also has the following top-level file:

* `config.toml`: site-wide configuration settings. Some of these are built-in and you can add your own. Config settings
  defined here are available in templates. All these directories above are configurable via `config.toml` settings.

Additionally, the following directories may be of interest:

* `/attic`: Here contains historical sections of specification and legacy drafts for the specification.
* `/changelogs`: Various bits of changelog for the specification areas.
* `/event-schemas`: [JSON Schema](http://json-schema.org/) definitions for the spec.
* `/data-definitions`: Bits of structured data consumable by Matrix implementations.
* `/meta`: Documentation relating to the spec's processes that are otherwise untracked (release instructions, etc).
* `/scripts`: Various scripts for generating the spec and validating its contents.
* `/proposals`: Matrix Spec Change (MSC) proposals. See <https://spec.matrix.org/unstable/proposals/>.

## Authoring changes to the spec

Please read [CONTRIBUTING.rst](./CONTRIBUTING.rst) before authoring a change to the spec. Note that spec authoring takes
place after an MSC has been accepted, not as part of a proposal itself.

1. Install the extended version (often the OS default) of Hugo: <https://gohugo.io/getting-started/installing>
2. Run `git submodule update --init --recursive` for good measure.
3. Run `npm i` to install the dependencies. Note that this will require NodeJS to be installed.
4. Run `npm run get-proposals` to seed proposal data. This is merely for populating the content of the "Spec Change Proposals" page and is not required.
5. Run `hugo serve` to run a local webserver which builds whenever a file change is detected. If watching doesn't appear
   to be working for you, try `hugo serve --disableFastRender` instead.
6. Edit the specification 🙂

We use a highly customized [Docsy](https://www.docsy.dev/) theme for our generated site, which uses Bootstrap and Font
Awesome. If you're looking at making design-related changes to the spec site, please coordinate with us in
[#matrix-docs:matrix.org](https://matrix.to/#/#matrix-docs:matrix.org) before opening a PR.

## Building the specification

If for some reason you're not a CI/CD system and want to render a static version of the spec for yourself, follow the above steps for authoring
changes to the specification and instead of `hugo serve` run `hugo -d "spec"` - this will generate the spec to `/spec`.
If you'd like to serve the spec off a path instead of a domain root (eg: `/unstable`), add `--baseURL "/unstable"` to
the `hugo -d "spec"` command.

For building the swagger definitions, create a python3 virtualenv and activate it. Then run `pip install -r ./scripts/requirements.txt` and finally `python ./scripts/dump-swagger.py` to generate it to `./scripts/swagger/api-docs.json`.
To make use of the generated file, there are a number of options:

* It can be uploaded from your filesystem to an online editor/viewer such as
  http://editor.swagger.io/
* You can run a local HTTP server by running `./scripts/swagger-http-server.py`, and then view the documentation via an
  online viewer; for example, at <http://petstore.swagger.io/?url=http://localhost:8000/api-docs.json>
* You can host the swagger UI yourself. See <https://github.com/swagger-api/swagger-ui#how-to-run> for advice on how to
  do so.

## Issue tracking

Specification issues are tracked on github at <https://github.com/matrix-org/matrix-doc/issues>.

See [meta/github-labels.rst](./meta/github-labels.rst) for information on what the labels mean.
