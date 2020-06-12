# MSC0000: matrix.to URI syntax v2

TODO: A general summary

## Proposal

### Current syntax

A matrix.to URI has the following format, based upon the specification defined
in RFC 3986:

```
https://matrix.to/#/<identifier>/<extra parameter>?<additional arguments>
```

The identifier may be a room ID, room alias, user ID, or group ID. The extra
parameter is only used in the case of permalinks where an event ID is referenced.
The matrix.to URI, when referenced, must always start with ``https://matrix.to/#/``
followed by the identifier.

The ``<additional arguments>`` and the preceeding question mark are optional and
only apply in certain circumstances, documented below.

Clients should not rely on matrix.to URIs falling back to a web server if accessed
and instead should perform some sort of action within the client. For example, if
the user were to click on a matrix.to URI for a room alias, the client may open
a view for the user to participate in the room.

The components of the matrix.to URI (``<identifier>`` and ``<extra parameter>``)
are to be percent-encoded as per RFC 3986.

Examples of matrix.to URIs are:

* Room alias: ``https://matrix.to/#/%23somewhere%3Aexample.org``
* Room: ``https://matrix.to/#/!somewhere%3Aexample.org``
* Permalink by room: ``https://matrix.to/#/!somewhere%3Aexample.org/%24event%3Aexample.org``
* Permalink by room alias: ``https://matrix.to/#/%23somewhere:example.org/%24event%3Aexample.org``
* User: ``https://matrix.to/#/%40alice%3Aexample.org``
* Group: ``https://matrix.to/#/%2Bexample%3Aexample.org``

## Potential issues

## Alternatives

## Security considerations

## Unstable prefix
