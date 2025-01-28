# MSC3551: Extensible Events - Files

[MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767) describes Extensible Events in detail,
though deliberately does not include schemas for some messaging types. This MSC covers only regular
file uploads.

*Rationale*: Splitting the MSCs down into individual parts makes it easier to implement and review in
stages without blocking other pieces of the overall idea. For example, an issue with the way files
are represented should not block the overall schema from going through.

## Proposal

Using [MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767)'s system, a new `m.file`
event type is introduced to describe generic file uploads (PDFs, documents, etc).

An example is:

```json5
{
  "type": "m.file",
  "content": {
    "m.text": [
      // Format of the fallback is not defined, but should have enough information for a text-only
      // client to do something with the file.
      {"body": "matrix.pdf (12 KB) https://example.org/_matrix/media/v3/download/example.org/abcd1234"}
    ],
    "m.file": {
      "url": "mxc://example.org/abcd1234",
      "name": "matrix.pdf",
      "mimetype": "application/pdf",
      "size": 12345,

      // These are all from EncryptedFile: https://spec.matrix.org/v1.1/client-server-api/#sending-encrypted-attachments
      "key": {
        "kty": "oct",
        "key_ops": ["encrypt", "decrypt"],
        "alg": "A256CTR",
        "k": "aWF6-32KGYaC3A_FEUCk1Bt0JA37zP0wrStgmdCaW-0",
        "ext": true
      },
      "iv": "w+sE15fzSc0AAAAAAAAAAA",
      "hashes": {
        "sha256": "fdSLu/YkRx3Wyh3KQabP3rd6+SFiKg5lsJZQHtkSAYA"
      },
      "v": "v2"
    },
    "m.caption": { // optional - goes above/below file
      "m.text": [{"body": "Look at this cool Matrix document"}]
    },
  }
}
```

The reusable `m.file` content block describes the actual file, with the following properties:

* `uri` - Required MXC URI for the file itself.
* `name` - Required name of the file, with extension (if applicable).
* `mimetype` - Optional (but recommended) mimetype for the file that was uploaded.
* `size` - Optional (but recommended) size in bytes for the file that was uploaded.

If the file is encrypted, the following fields additionally apply. All fields are to support the
`EncryptedFile` object described by the [encryption module](https://spec.matrix.org/v1.1/client-server-api/#sending-encrypted-attachments).

* `key` - Required JSON Web Key. The presence of this field indicates the file is encrypted.
* `iv` - Required serialized initialization vector.
* `hashes` - Required hashes object.
* `v` - Required version string.

This structure covers the existing [`m.file`](https://spec.matrix.org/v1.1/client-server-api/#mfile)
`msgtype` (minus the spurious thumbnail schema).

Additionally, the following content blocks are defined:

* `m.caption` - A message to place above or below the rendered content (in this case, a file).
  Currently requires an `m.text` content block to be nested within it.

Together with content blocks from other proposals, an `m.file` is described as:

* **Required** - An `m.text` block to act as a fallback for clients which can't process files.
* **Required** - An `m.file` to describe the actual file.
* **Optional** - An `m.caption` block to represent any text that should be shown above or below the
  file. Currently this MSC does not describe a way to pick whether the text goes above or below,
  leaving this as an implementation detail. A future MSC may investigate ways of representing this,
  if needed.

The above describes the minimum requirements for sending an `m.file` event. Senders can add additional
blocks, however as per the extensible events system, receivers which understand file events should not
honour them.

## Potential issues

The schema duplicates some of the information into the text fallback, though this is unavoidable
and intentional for fallback considerations.

## Alternatives

No significant alternatives known.

## Security considerations

The same considerations which currently apply to files and extensible events also apply here.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc1767.*` as a prefix in
place of `m.*` throughout this proposal. Note that this uses the namespace of the parent MSC rather than
the namespace of this MSC - this is deliberate.

Note that extensible events should only be used in an appropriate room version as well.
