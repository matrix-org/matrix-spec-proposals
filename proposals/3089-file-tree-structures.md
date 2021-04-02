# MSC3089: File trees

Files are currently shared by uploading them to the media repo and putting a reference to that content
in a room message. This is fine for most use cases, such as sharing screenshots or short-lived documents,
however longer term, collaborative, structures are not quite possible.

This MSC defines an approach for defining data trees in Matrix, using a document hierarchy as an example
for how it could be applied.

Reading material:
* [MSC1772 - Spaces](https://github.com/matrix-org/matrix-doc/pull/1772)
* [MSC1840 - Room types](https://github.com/matrix-org/matrix-doc/pull/1840)
* [MSC3088 - Room subtyping](https://github.com/matrix-org/matrix-doc/pull/3088)
* [MSC1767 - Extensible events](https://github.com/matrix-org/matrix-doc/pull/1767)

Optional but useful reading:
* [MSC2326 - Label-based filtering ("threading")](https://github.com/matrix-org/matrix-doc/pull/2326)
* [MSC2674 - Event relationships](https://github.com/matrix-org/matrix-doc/pull/2674)
* [MSC2676 - Message editing](https://github.com/matrix-org/matrix-doc/pull/2676)
* [MSC2946 - Spaces summary](https://github.com/matrix-org/matrix-doc/pull/2946)
* [MSC2962 - Space group access control](https://github.com/matrix-org/matrix-doc/pull/2962)
* [MSC2753 - Proper peeking](https://github.com/matrix-org/matrix-doc/pull/2753)
* [Spec - Withholding encryption keys](https://spec.matrix.org/unstable/client-server-api/#reporting-that-decryption-keys-are-withheld)

## Proposal

*Author's note: This proposal assumes the reader is familiar with the terminology of the reading
materials mentioned above.*

We introduce a new room subtype, `m.data_tree`, to be applied to spaces to denote that they are
data-driven trees. The subtype only needs to be applied to a parent space to affect all subspaces
of that space. For a file hierarchy, the room name for the spaces are the directory names.

Spaces with the `m.data_tree` subtype are called "tree spaces" in this proposal.

The context of the data-driven space denotes how it should be interpretted by a client. The common
case is expected to be that a tree space would be a subspace of some other space, such as a space
representing an organization. Free-standing tree spaces (ie: not subspaces of another space) would
be akin to private/shared personal folders depending on join rules, history visibility, etc.

A limited example of what this would look like is:

```
+ Acme Co.
  + Sales Team
    + 📂 Quarterly objectives
      + 📂 Q1 2021
        + 📄 Targets
        + 📄 End of quarter report
      + 📂 Q2 2021
        + 📄 Targets
      + 📂 Q3 2021
      + 📂 Q4 2021
  + HR
    + 📂 Personnel files
    + 📂 Policies
    + 📂 Contract templates
```

In the example, the sales team has 1 tree under it: a client could reasonably assume that the tree is
for that Sales Team only. Access control would likely be set such that only members of the sales team
can access that tree space. A similar structure is applied to the HR subspace, though with 3 trees
instead of just one - this is to demonstrate that any number of tree spaces are possible under a given
non-tree space.

In both team's cases, clients would not render the trees as browseable in a room list (typically). The
client would likely expose a "View files" button which then takes the user to a file browser of sorts
for the user to explore.

Tree spaces may contain non-space rooms under them to help perform access control. For example:

```
+ 📂 My Folder
  + Regular room 1
  + Regular room 2
  + 📂 Subfolder 1
```

When this happens, the rooms are treated effectively as more buckets under that parent node. In the above
example this would mean that anything posted to either "Regular room" would be listed under "My Folder"
instead. This is expected to be a rare choice of data structure, though can theoretically be used to
group files within a directory for simpler access control.

Files are represented as room events either in the tree room (or in any non-space room under that tree 
space). This is done by exposing a generic `m.leaf` type which is purely intended to be used to encourage 
proper rendering within the extensible events scheme. A file would look something like this:

```json5
{
  "type": "m.file",
  "content": {
    "m.text": "targets.docx (12 KB)",
    "m.file": {
      "url": "mxc://example.org/abc123",
      "name": "targets.docx",
      "mimetype": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      "size": 12000
    },
    "m.leaf": {
      "label": "targets.docx"
    }
  }
}
```

Note that this would allow non-file types to be included in the tree. Clients would filter out anything
that doesn't make sense for their use case, such as ignoring text-only events. Events missing the `m.leaf`
description would be excluded as non-leaf events. `label` is required to be a string.

The `m.leaf` type is intentionally not used as the event type as fundamentally the user is uploading a file,
not a leaf. The leaf is essentially metadata on the event to describe how it could be rendered by clients
behaving in a suitable way. Otherwise, it's deliberate that the event shows up as a regular file upload in
the room.

For some common operations:
* Deleting a file would mean redacting the event.
* Updating a file could mean editing it, or redacting and re-sending.
* Changing view file permissions could mean using an encrypted room and withholding keys.
* Changing upload permissions would mean altering power levels.
* Renaming a file would mean editing the label.
* Moving a file would mean redacting and re-sending in the right tree.
* Comments/notes on a file could be threads off the file.
* Anonymous browsing would be peeking into the various rooms.

Implementation-wise, the following may be useful:
* Using space summaries to render the directory structure.
* Peeking to get file listings.
* Group access controls to control who can (and can't) upload/view files.
* Encryption to protect files and get finer control over visibility.
* History visibility and join rules to manage publicity of the files.
* Room directory for discovering public file shares.

## Potential issues

***TODO***

## Alternatives

***TODO***

## Security considerations

***TODO***

## Unstable prefix

While this MSC is not in a stable version of the specification, implementations should
use `org.matrix.msc3089.` in place of `m.` - this means, for example, `org.matrix.msc3089.leaf`
as an identifier.
