# Bundled URL previews
Currently, URL previews in Matrix are generated on the server when requested by
a client using the [`/_matrix/media/v3/preview_url`](https://spec.matrix.org/v1.9/client-server-api/#get_matrixmediav3preview_url)
endpoint. This is a relatively good approach, but a major downside is that the
user's homeserver gets all links the user's client wants to show a preview for,
which means using it in encrypted rooms will effectively leak parts of messages.

## Proposal
The proposed solution is allowing clients to bundle URL preview metadata inside
events.

A new field called `m.url_previews` is added. The field is an array of objects,
where each object contains OpenGraph data representing a single URL to preview,
similar to what the `/preview_url` endpoint currently returns:

* `matrix:matched_url` - The URL that is present in `body` and triggered this preview
  to be generated. This is optional and should be omitted if the link isn't
  present in the body.
* `matrix:image:encryption` - An [EncryptedFile](https://spec.matrix.org/v1.9/client-server-api/#extensions-to-mroommessage-msgtypes)
  object for encrypted thumbnail images. Similar to encrypted image messages,
  the URL is inside this object, and not in `og:image`.
* `matrix:image:size` - The byte size of the image, like in `/preview_url`.
* `og:image` - An `mxc://` URI for unencrypted images, like in `/preview_url`.
* `og:url` - Standard OpenGraph tag for the canonical URL of the previewed page.
* Any other standard OpenGraph tags.

At least one of `matrix:matched_url` and `og:url` MUST be present. All other
fields are optional.

### Extensible events
The definition of `matrix:matched_url` changes from "present in `body`" to
"present in `m.text`", but otherwise the proposal is directly compatible with
extensible events.

### Client behavior
#### Sending preview data
When sending previews to encrypted rooms, clients should encrypt preview images
and put them in the `matrix:image:encryption` field. Other `og:image:*` and the
`matrix:image:size` field can still be used for image metadata, but the
`og:image` field should be omitted for encrypted thumbnails.

If clients use the `/preview_url` endpoint as a helper for generating preview
data, they should reupload the thumbnail image (if there is one) to create a
persistent `mxc://` URI, as well as encrypt it if applicable.

#### Receiving messages with `m.url_previews`
If an object in the list contains only `matrix:matched_url` and no other fields,
receiving clients should fall back to the old behavior of requesting a preview
using `/preview_url`. Clients may also choose to ignore bundled data and ask
the homeserver for a preview even if bundled data is present.

Clients should not search the `body` field for URLs if the `m.url_previews`
field is present, even if they fall back to the old behavior of requesting
preview data from the homeserver. Conversely, if the field is not present,
clients should fall back to the searching behavior.

The two above points effectively make this an alternative for
[MSC2385](https://github.com/matrix-org/matrix-spec-proposals/pull/2385).

### Examples
<details>
<summary>Normal preview</summary>

```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "https://matrix.org",
    "m.url_previews": [
      {
        "matrix:matched_url": "https://matrix.org",
        "matrix:image:size": 16588,
        "og:description": "Matrix, the open protocol for secure decentralised communications",
        "og:image": "mxc://maunium.net/zeHhTqqUtUSUTUDxQisPdwZO",
        "og:image:height": 400,
        "og:image:type": "image/jpeg",
        "og:image:width": 800,
        "og:title": "Matrix.org",
        "og:url": "https://matrix.org/"
      }
    ],
    "m.mentions": {}
  }
}
```

</summary>
<details>
<summary>Preview with encrypted thumbnail image</summary>

```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "https://matrix.org",
    "m.url_previews": [
      {
        "matrix:matched_url": "https://matrix.org",
        "og:url": "https://matrix.org/",
        "og:title": "Matrix.org",
        "og:description": "Matrix, the open protocol for secure decentralised communications",
        "matrix:image:size": 16588,
        "og:image:width": 800,
        "og:image:height": 400,
        "og:image:type": "image/jpeg",
        "matrix:image:encryption": {
          "key": {
            "k": "GRAgOUnbbkcd-UWoX5kTiIXJII81qwpSCnxLd5X6pxU",
            "alg": "A256CTR",
            "ext": true,
            "kty": "oct",
            "key_ops": [
              "encrypt",
              "decrypt"
            ]
          },
          "iv": "kZeoJfx4ehoAAAAAAAAAAA",
          "hashes": {
            "sha256": "WDOJYFegjAHNlaJmOhEPpE/3reYeD1pRvPVcta4Tgbg"
          },
          "v": "v2",
          "url": "mxc://beeper.com/53207ac52ce3e2c722bb638987064bfdc0cc257b"
        }
      }
    ],
    "m.mentions": {}
  }
}
```

</details>
<details>
<summary>Message indicating it should not have any previews</summary>

```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "https://matrix.org",
    "m.url_previews": [],
    "m.mentions": {}
  }
}
```

</details>
<summary>Preview in extensible event</summary>

```json
{
  "type": "m.message",
  "content": {
    "m.text": {
      {"body": "matrix.org/support"}
    ],
    "m.url_previews": [
      {
        "matched_url": "matrix.org/support",
        "matrix:image:size": 16588,
        "og:description": "Matrix, the open protocol for secure decentralised communications",
        "og:image": "mxc://maunium.net/zeHhTqqUtUSUTUDxQisPdwZO",
        "og:image:height": 400,
        "og:image:type": "image/jpeg",
        "og:image:width": 800,
        "og:title": "Support Matrix",
        "og:url": "https://matrix.org/support/"
      }
    ],
    "m.mentions": {}
  }
}
```

</details>

## Potential issues
### Fake preview data
The message sender can fake previews quite trivially. This is considered an
acceptable compromise to achieve non-leaking URL previews in encrypted rooms.

Clients may choose to ignore embedded preview data in unencrypted rooms and
always use the `/preview_url` endpoint.

### More image uploads
Currently previews are generated by the server, which lets the server apply
caching and delete thumbnail images quickly. If the data was embedded in events
instead, the server would not be able to clean up images the same way.

### Web clients
Web clients likely can't generate previews themselves due to CORS and other
such protections.

Clients could use the existing URL preview endpoint to generate a preview and
bundle that data in events, which has the benefit of only leaking the link to
one homeserver (the sender's) instead of all servers. When doing this, clients
would have to download the preview image and reupload it to get a persistent
`mxc://` URI, and possibly encrypt it before uploading.

Alternatively, clients could simply not include preview data at all and have
receiving clients fall back to the old behavior (meaning no previews in
encrypted rooms unless the receiver opts in).

### Security considerations
Fake preview data as covered in potential issues.

## Alternatives
### Different generation methods
Previews could be generated by the receiving client, which both doesn't leak
links to the user's homeserver, and prevents fake previews. However, this would
leak the user's IP address to all links they receive, so it is not an
acceptable solution.

## Unstable prefix
Until this MSC is accepted, implementations should apply the following renames:

* `com.beeper.linkpreviews` instead of `m.url_previews`
* `beeper:image:encryption` instead of `matrix:image:encryption`
* `matched_url` instead of `matrix:matched_url`
