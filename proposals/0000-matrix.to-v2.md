# MSC0000: matrix.to URI syntax v2

TODO: A general summary

## Proposal

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
characters, as in `https://matrix.to/!somewhere%3Aexample.org?via=example.org&via=alt.example.org`

The components of the matrix.to URI (``<identifier>`` and ``<extra parameter>``)
are to be percent-encoded as per RFC 3986.

Examples of matrix.to URIs are:

* Room alias: ``https://matrix.to/#/%23somewhere%3Aexample.org``
* Room: ``https://matrix.to/#/!somewhere%3Aexample.org?via=example.org&via=alt.example.org``
* Permalink by room: ``https://matrix.to/#/!somewhere%3Aexample.org/%24event%3Aexample.org?via=example.org&via=alt.example.org``
* Permalink by room alias: ``https://matrix.to/#/%23somewhere:example.org/%24event%3Aexample.org``
* User: ``https://matrix.to/#/%40alice%3Aexample.org``
* Group: ``https://matrix.to/#/%2Bexample%3Aexample.org``

## Potential issues

## Alternatives

## Security considerations

## Unstable prefix
