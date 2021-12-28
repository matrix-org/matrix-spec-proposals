# Changelogs

[Towncrier](https://github.com/hawkowl/towncrier) is used to manage the changelog and
keep it up to date. Because of this, updating a changelog is really easy.

## Generating the changelog

Please see the [release docs](../meta/releasing.md) for more information.

## Creating a new changelog

There are a few places you'll have to update:
* `/layouts/shortcodes/changelog/changelog-changes.html` to account for the new changelog.
* `/scripts/generate-changelog.sh` to render the changelog for releases.
* Supporting documentation such as the contributing guidelines.
