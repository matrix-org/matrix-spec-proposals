<!-- Note: This is a markdown file so the build script's RST processing doesn't grab it -->

# Changelogs

[Towncrier](https://github.com/hawkowl/towncrier) is used to manage the changelog and
keep it up to date. Because of this, updating a changelog is really easy.

## How to update a changelog when releasing an API

1. Ensure you're in your Python 3 virtual environment
2. `cd` your way to the API you're releasing (eg: `cd changelogs/client_server`)
3. Run `towncrier --version "r0.4.0" --name "client-server" --yes` substituting the
   variables as approprite. Note that `--name` is required although the value is ignored.
4. Commit the changes and finish the release process.

## How to prepare a changelog for a new API

For this example, we're going to pretend that the `server_server` API doesn't exist.

1. Create the file `changelogs/server_server.rst`
2. Create the folder `changelogs/server_server`
3. In the new folder, create a `pyproject.toml` file with these contents:
   ```toml
   [tool.towncrier]
    filename = "../server_server.rst"
    directory = "newsfragments"
    issue_format = "`#{issue} <https://github.com/matrix-org/matrix-doc/issues/{issue}>`_"
    title_format = "{version}"

    [[tool.towncrier.type]]
        directory = "breaking"
        name = "Breaking Changes"
        showcontent = true

    [[tool.towncrier.type]]
        directory = "deprecation"
        name = "Deprecations"
        showcontent = true

    [[tool.towncrier.type]]
        directory = "new"
        name = "New Endpoints"
        showcontent = true

    [[tool.towncrier.type]]
        directory = "removal"
        name = "Removed Endpoints"
        showcontent = true

    [[tool.towncrier.type]]
        directory = "feature"
        name = "Backwards Compatible Changes"
        showcontent = true

    [[tool.towncrier.type]]
        directory = "clarification"
        name = "Spec Clarifications"
        showcontent = true
   ```
4. Create a `.gitignore` in `changelogs/server_server/newsfragments` with the contents `!.gitignore`
