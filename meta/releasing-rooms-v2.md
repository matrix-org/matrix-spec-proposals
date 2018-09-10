# How to release Room Version 2

Room versions are a bit special for the release given they have been
introduced at v2 rather than ever getting a v1 release. Additionally,
room versions have different release requirements due to the in-project
versioning of documents rather than relying on matrix.org to maintain
old generated output of specifications.

As of writing, the project is structured to support 3 logical versions
for rooms: v1, v2, and unstable. Unstable is currently pointed at v2
in order to aid development. After v2 is released, unstable may wish
to be left as an independent version or similarly be pointed at a "v3"
document.

Due to room versions being versioned in-project, the generated output
from a release is not to be sent off to matrix-doc/matrix.org. Instead,
in `gendoc.py` the default value for `--room_version` should be set to
the current release (`v2`, for example) so the index renders the right
edition in the table.

After editing `gendoc.py`, the changelog should be generated according
to the towncrier instructions. You may need to fix the `.. version: v2`
comment located in the `rooms.rst` changelog to be just underneath the
title instead of at the end of the section.

The `targets.yaml` file needs to be set up to point unstable to the
right set of files. Ensure that `unstable.rst` is referenced instead
of `v2.rst`, and that `unstable.rst` has appropriate contents.

Finally, in the `intro.rst` for room versions, re-add unstable to the
list of available versions. It is currently commented out to avoid
confusing people, so it should be possible to uncomment it and put it
back into the list.

From there, the standard process of using a release branch, tagging it,
and announcing it to the world should be followed. If required, the
various other APIs should be updated to better support the new room
version.
