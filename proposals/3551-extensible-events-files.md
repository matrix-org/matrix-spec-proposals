# MSC3551: Extensible Events - Files

[MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767) describes Extensible Events in detail,
though deliberately does not include schemas for non-text messaging types. This MSC covers just file
uploads, which is further used as a base for images, videos, etc.

*Rationale*: Splitting the MSCs down into individual parts makes it easier to implement and review in
stages without blocking other pieces of the overall idea. For example, an issue with the way images
are represented should not block the overall schema from going through.

## Proposal

Using [MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767)'s system, a new `m.file` primary
event type is introduced to describe generic file uploads (PDFs, documents, etc).

An example is:

```json5
{
  "type": "m.file",
  "content": {
    "m.text": "Upload: foo.pdf (12 KB)", // or other m.message-like event
    "m.file": {
      "url": "mxc://example.org/abcd1234",
      "name": "foo.pdf",
      "mimetype": "application/pdf",
      "size": 12345
    }
  }
}
```

This incorporates the intended schema for the [`m.file`](https://spec.matrix.org/v1.1/client-server-api/#mfile)
`msgtype` (minus the spurious thumbnail schema).

Note that a file event requires a text fallback of `m.text`, `m.html`, or other `m.message`-compatible
event.

An encrypted file would appear as such:

```json5
{
  "type": "m.file",
  "content": {
    "m.text": "Upload: foo.pdf (12 KB)", // or other m.message-like event
    "m.file": {
      "url": "mxc://example.org/abcd1234",
      "name": "foo.pdf",
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
    }
  }
}
```

The presence of a `key` JWT denotes the file is encrypted.

## Potential issues

The schema duplicates some of the information into the text fallback, though this is unavoidable.

## Alternatives

No significant alternatives known.

## Security considerations

The same considerations which currently apply to files and extensible events also apply here.

## Transition

The same transition introduced by extensible events is also applied here:

```json5
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.file",
    "body": "foo.pdf",
    "info": {
      "size": 774,
      "mimetype": "application/pdf"
    },
    "file": {
      "url": "mxc://example.org/f91dce7b060ed4c8f094cd3ecb498aa621bbe242",
      "key": {
        "kty": "oct",
        "key_ops": ["encrypt", "decrypt"],
        "alg": "A256CTR",
        "k": "TLlG_OpX807zzQuuwv4QZGJ21_u7weemFGYJFszMn9A",
        "ext": true
      },
      "iv": "S22dq3NAX8wAAAAAAAAAAA",
      "hashes": {
        "sha256": "aWOHudBnDkJ9IwaR1Nd8XKoI7DOrqDTwt6xDPfVGN6Q"
      },
      "v": "v2"
    },

    // Extensible Events
    "m.text": "foo.pdf",
    "m.file": {
      "url": "mxc://example.org/f91dce7b060ed4c8f094cd3ecb498aa621bbe242",
      "name": "foo.pdf",
      "mimetype": "application/pdf",
      "size": 774,
      "key": {
        "kty": "oct",
        "key_ops": ["encrypt", "decrypt"],
        "alg": "A256CTR",
        "k": "TLlG_OpX807zzQuuwv4QZGJ21_u7weemFGYJFszMn9A",
        "ext": true
      },
      "iv": "S22dq3NAX8wAAAAAAAAAAA",
      "hashes": {
        "sha256": "aWOHudBnDkJ9IwaR1Nd8XKoI7DOrqDTwt6xDPfVGN6Q"
      },
      "v": "v2"
    }
  }
}
```

The event details are copied and quite verbose, however this is best to ensure compatibility with the
extensible events format.

## Unstable prefix

While this MSC is not considered stable, implementations should use `org.matrix.msc1767.file` in place
of `m.file` throughout this proposal. Note that this uses the namespace of the parent MSC rather than
the namespace of this MSC - this is deliberate.

Example:
```json5
{
  "type": "org.matrix.msc1767.file",
  "content": {
    "org.matrix.msc1767.text": "Upload: foo.pdf (12 KB)", // or other org.matrix.msc1767.message-like event
    "org.matrix.msc1767.file": {
      "url": "mxc://example.org/abcd1234",
      "name": "foo.pdf",
      "mimetype": "application/pdf",
      "size": 12345
    }
  }
}
```
