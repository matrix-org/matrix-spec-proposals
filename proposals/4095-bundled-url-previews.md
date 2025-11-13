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

URL previews are primarily meant for text-based message types (`m.text`,
`m.notice`, `m.emote`), but they may be used with any message type, as even
media messages may have captions in the future.

Allowing the omission of `matched_url` is effectively a new feature to send URL
previews without a link in the message text.

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
persistent `mxc://` URI, as well as encrypt it if applicable. A future MSC
could also extend `/preview_url` with a parameter to request a persistent URI.

#### Receiving messages with `m.url_previews`
If an object in the list contains only `matrix:matched_url` or `og:url` (but
not both) and no other fields, receiving clients should fall back to the old
behavior of requesting a preview using `/preview_url`.

Clients may choose to ignore bundled data and ask the homeserver for a preview
even if bundled data is present, as a security measure against faking preview
data.

Clients may also choose to verify that the matched_url is present in the
`body` field before displaying a full preview. However, in order to avoid losing
data, clients SHOULD still display ignored entries somehow, e.g. just rendering
the link (either `og:url` or `matrix:matched_url`) instead of a full preview.

Note: ignoring bundled data does not mean ignoring the `m.url_preview` field:
even when ignoring bundled data and/or verifying that matched_url is present in
`body`, clients should only display previews for URLs that are present in the
list, and should never display previews for URLs that aren't present in the list.

If the `m.url_previews` field is not present at all, clients should fall back
to the old behavior of searching `body`.

The above points effectively make this an alternative for
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

</details>
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
<details>
<summary>Message indicating a preview should be fetched from the homeserver</summary>

```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "https://matrix.org",
    "m.url_previews": [
      {
        "matrix:matched_url": "https://matrix.org"
      }
    ],
    "m.mentions": {}
  }
}
```

</details>
<details>
<summary>Preview in extensible event</summary>

```json
{
  "type": "m.message",
  "content": {
    "m.text": [
      {"body": "matrix.org/support"}
    ],
    "m.url_previews": [
      {
        "matrix:matched_url": "matrix.org/support",
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

As mentioned in the client behavior section, clients may choose to ignore
embedded preview data in unencrypted rooms and always use the `/preview_url`
endpoint, effectively only using `m.url_previews` as a whitelist of URLs to
preview.

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

## Security considerations
Fake preview data as covered in potential issues.

### Visibility in old clients (T&S)
Clients that don't support this MSC will not display any of the data in the
preview field, which could be abused by spammers if all moderators in a room
are using old clients.

### Generating previews will leak IPs
The sender's client will leak its IP when it fetches previews for URLs typed by
the user. This is generally an acceptable tradeoff, as long as clients take
care never to generate previews for links the user did not type.

For example, if a client generates reply fallbacks, it MUST NOT generate
previews for links in the fallback. Clients should also be careful with links
when starting to edit a message, possibly by not generating new previews at
all.

Clients may also provide extra safeguards, such as only offering a button to
generate previews, rather than generating them immediately after the user types
a URL. However, this is a UX decision and is therefore ultimately up to the
client to decide.

Clients could also use a privacy-preserving TCP relay to proxy all URL preview
requests [like Signal does](https://signal.org/blog/i-link-therefore-i-am/).
That way the client wouldn't leak its IP, and the relay wouldn't see previewed
URLs. However, running such a proxy has several potential security issues for
the server administrators, so it is out of scope for this MSC.

### Previewing code must be implemented carefully
When generating URL previews, clients are parsing completely untrusted data.
Parsing responses must be done with care to prevent content-based attacks, such
as the billion laughs attack.

### Local IPs should not be previewed by default
Clients should prevent previewing non-public IP addresses by default. To do
this, clients must check the DNS records of a domain before connecting to the
resolved IP, as public domains may point to private IPs. For web clients, these
limits are generally handled by the browser (see the [Private Network Access
spec](https://wicg.github.io/private-network-access/)).

## Alternatives
### Different generation methods
Previews could be generated by the receiving client, which both doesn't leak
links to the user's homeserver, and prevents fake previews. However, this would
leak the user's IP address to all links they receive, so it is not an
acceptable solution.

The original design notes for URL previews from 2016 also has a list of options
that were considered at the time: <https://github.com/matrix-org/matrix-spec/blob/main/attic/drafts/url_previews.md>.
Option 2 is what was implemented then, and this proposal adds option 4.
The combination of options 2 and 4 is also mentioned as the probably best
solution in that document.

The document also mentions the possibility of an AS or HS scanning messages and
injecting preview data, but that naturally won't function with encryption at all,
and is therefore not an alternative.

The fifth option mentioned in the document, a centralized previewing service
which is configured per-room, could technically work, but would likely be worse
than HS-generated previews in practice: users wouldn't know to configure a
different previewing service, so clients would probably have to automatically
pick one.

## Unstable prefix
Until this MSC is accepted, implementations should apply the following renames:

* `com.beeper.linkpreviews` instead of `m.url_previews`
* `beeper:image:encryption` instead of `matrix:image:encryption`
* `matched_url` instead of `matrix:matched_url`
  * note: this was implemented without a prefix before the MSC was made, which
    is why the "unstable prefix" is no prefix in this case.
