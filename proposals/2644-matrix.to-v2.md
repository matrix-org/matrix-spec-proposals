# MSC2644: `matrix.to` URI syntax v2

`matrix.to` URIs are used frequently to link to Matrix things (events, rooms,
users, groups) in the ecosystem today. By adjusting and extending them a bit
further, both clients and the interstitial screens hosted at `matrix.to` can
give the user more context and a better experience.

## Proposal

In an attempt to make it easier for the reader to review, this proposal first
summarises the current syntax, then describes the revised syntax, and finally
summaries the changes proposed.

### Current syntax

This summarises the [currently specified matrix.to URI
format](https://matrix.org/docs/spec/appendices#matrix-to-navigation) as an aid
to the reader.

A matrix.to URI has the following format, based upon the specification defined
in RFC 3986:

```
https://matrix.to/#/<identifier>/<extra parameter>?<additional arguments>
```

The `identifier` (required) may be a:

| type | literal value | encoded value |
| ---- | ------------- | ------------- |
| room ID | `!somewhere:example.org` | `!somewhere%3Aexample.org` |
| room alias | `#somewhere:example.org` | `%23somewhere%3Aexample.org` |
| user ID | `@alice:example.org` | `%40alice%3Aexample.org` |
| group ID | `+example:example.org` | `%2Bexample%3Aexample.org` |

The `extra parameter` (optional) is only used in the case of permalinks where an
event ID is referenced:

| type | literal value | encoded value |
| ---- | ------------- | ------------- |
| event ID | `$event:example.org` | `%24event%3Aexample.org` |

The ``<additional arguments>`` and the preceding question mark are optional and
only apply in certain circumstances:

* `via=<server>`
  * One or more servers [should be
    specified](https://matrix.org/docs/spec/appendices#routing) in the format
    `example.org` when linking to a room (including a permalink to an event in a
    room) since room IDs are not currently routable

If multiple ``<additional arguments>`` are present, they should be joined by `&`
characters, as in `https://matrix.to/#/!somewhere%3Aexample.org?via=example.org&via=alt.example.org`

The components of the matrix.to URI (``<identifier>`` and ``<extra parameter>``)
are to be percent-encoded as per RFC 3986.

### Revised syntax

A matrix.to URI has the following format, based upon the specification defined
in RFC 3986:

```
https://matrix.to/#/<identifier>/<extra parameter>?<additional arguments>
```

The `identifier` (required) may be a:

| type | literal value | encoded value |
| ---- | ------------- | ------------- |
| event ID | `$event:example.org` | `%24event%3Aexample.org` |
| room ID | `!somewhere:example.org` | `!somewhere%3Aexample.org` |
| room alias | `#somewhere:example.org` | `%23somewhere%3Aexample.org` |
| user ID | `@alice:example.org` | `%40alice%3Aexample.org` |
| group ID | `+example:example.org` | `%2Bexample%3Aexample.org` |

The `extra parameter` (optional) now only exists for compatibility with existing
v1 links. It can be used when `identifier` is a room ID or room alias as a part
of a permalink that references a specific event, as shown in the table below.
Going forward, this should be considered deprecated, and clients should place
only the event ID in the `identifier` position for new links.

| type | literal value | encoded value |
| ---- | ------------- | ------------- |
| event ID | `$event:example.org` | `%24event%3Aexample.org` |

Since clients currently cannot find a room from the event ID alone, a new
client-server API is added to support the new format with only an event ID.

> TODO: To support this, a new client-server API will be defined which
> allows clients to query the mapping from event ID to room ID. This will be
> defined in a separate MSC.

The ``<additional arguments>`` and the preceding question mark are optional and
only apply in certain circumstances:

* `via=<server>`
  * One or more servers [should be
    specified](https://matrix.org/docs/spec/appendices#routing) in the format
    `example.org` when linking to a room or an event since room IDs are
    not currently routable
* `client=<client URL>`
  * This parameter allows clients to indicate which client shared the URI
  * Clients should identify themselves via a schemeless `https` URL pointing
      to a download / install page, such as:
    * `foo.com`
    * `apps.apple.com/app/foo/id1234`
    * `play.google.com/store/apps/details?id=com.foo.client`
* `federated=false`
  * This parameter allows indicating whether a room exists on a federating
    server (assumed to be the default), or if the client must connect via the
    server identified by the room ID or event ID (when set to `false`)
* `sharer=<MXID>`
  * This parameter allows indicating the MXID of the account which created the
    link, so that clients and interstitial UIs can display more context to the
    user
  * As an example, clients and interstitial UIs could use this to query profile
    data for the sharer's account and display the sharer's avatar and display
    name

If multiple ``<additional arguments>`` are present, they should be joined by `&`
characters, as in `https://matrix.to/!somewhere%3Aexample.org?via=example.org&via=alt.example.org`

The components of the matrix.to URI (``<identifier>`` and ``<extra parameter>``)
are to be percent-encoded as per RFC 3986.

Examples of matrix.to URIs using the revised syntax are:

* Room alias: ``https://matrix.to/#/%23somewhere%3Aexample.org``
* Room alias with client and sharer:
  ``https://matrix.to/#/%23somewhere%3Aexample.org?client=foo.com&sharer=%40alice%3Aexample.org``
* Room: ``https://matrix.to/#/!somewhere%3Aexample.org?via=example.org&via=alt.example.org``
* Event permalink: ``https://matrix.to/#/%24event%3Aexample.org?via=example.org&via=alt.example.org``
* User: ``https://matrix.to/#/%40alice%3Aexample.org``
* Group: ``https://matrix.to/#/%2Bexample%3Aexample.org``

### Summary of changes

* When permalinking to a specific event, the room ID is no longer required and
  event IDs are now permitted in the identifier position, so URIs like
  `https://matrix.to/#/%24event%3Aexample.org` are now acceptable
* Clients should prefer creating URIs with room aliases instead of room IDs
  where possible, as it's more human-friendly and `via` params are not needed
* A new, optional `client` parameter allows clients to indicate
  which client shared the URI
* A new, optional `federated` parameter allows indicating whether a room exists
  on a federating server (assumed to be the default), or if the client must
  connect via the server identified by the room ID or event ID (when set to
  `false`)
* A new, optional `sharer` parameter allows indicating the MXID of the account
  which created the link, in case that is meaningful to include

## Potential issues

This proposal seeks to extend the existing `matrix.to` syntax, but there is also
an open proposal for a [Matrix URI
scheme](https://github.com/matrix-org/matrix-doc/pull/2312). If this proposal
moves forward, the Matrix URI scheme would likely need to be reworked to
accommodate the additions here.

The new `client` parameter implies there are potentially many identifiers that
might be passed that point to a given client. If there are use cases which rely
on a static mapping of client identifier to client name, logo, etc. for some
reason, then that could become a burden to maintain over time. The flexibility
of accepting any URL as an identifier (and thus avoiding the need to register a
client in a centralised place) seems preferable and hopefully outweighs this
concern.

## Alternatives

Instead of extending `matrix.to`, these embellishments could wait for and
extend the future [Matrix URI
scheme](https://github.com/matrix-org/matrix-doc/pull/2312). This proposal
attempts to be pragmatic and tries to extend what is already in use today,
rather than blocking on a new scheme.

## Security considerations

The new `sharer` parameter is not authenticated, so you could make it appear as
if someone had shared something they did not. It is currently assumed that this
is a minor concern.

## Unstable prefix

There's no concept of stability for the matrix.to URI syntax, so no prefix is
used here. Since everything proposed here is purely additive, there should not
be a compatibility issues. At worst, the new pieces are ignored.
