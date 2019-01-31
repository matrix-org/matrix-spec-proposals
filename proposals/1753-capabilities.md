# MSC1753: client-server capabilities API

A mechanism is needed for clients to interrogate servers to establish whether
particular operations can be performed.

For example, users may not be able to change their password if a server is
configured to authenticate against a separate system, in which case it is
nonsensical to offer the user such an option.

## Proposal

### `GET /_matrix/client/r0/capabilities`

We will add a new endpoint to the client-server API: `GET
/_matrix/client/r0/capabilities`. The endpoint will be authenticated as normal
via an access token.

The server should reply with a list of supported features, as shown:

```json
{
    "capabilities": {
        "m.capability_one": {}
    }
}
```

The keys of the `capabilities` object are capability identifiers. As with
other identifiers in the Matrix protocol, the `m.` prefix is reserved for
definition in the Matrix specification; other values can be used within an
organisation following the Java package naming conventions.

The values of the `capabilities` object will depend on the capability
identifier, though in general the empty object will suffice.

### Initial capability identifiers

As a starting point, a single capability identifier is proposed:
`m.change_password`, which should be considered supported if it is possible to
change the user's password via the `POST /_matrix/client/r0/account/password`
API.

The value of the `capabilities` object in the response should contain a single
boolean flag, `enabled`, to indicate whether a password change is possible. If
the capability is not listed, the client should assume that password changes
are possible.

### Fallback behaviour

Clients will need to be aware of servers which do not support the new endpoint,
and fall back to their current behaviour if they receive a 404 response.

### Suitable applications

In general, capabilities advertised via this endpoint should depend in some way
on the state of the user or server - in other words, they will be inherently
"optional" features in the API.

This endpoint should *not* be used to advertise support for experimental or
unstable features, which is better done via `/client/versions` (see
[MSC1497](https://github.com/matrix-org/matrix-doc/issues/1497)).

Examples of features which might reasonably be advertised here include:

 * Whether the server supports user presence.

 * Whether the server supports other optional features. The following could be
   made optional via this mechanism:
   * Room directory
   * URL previews

 * Policy restricitions, such as:
   * Whether certain types of content are permitted on this server.
   * The number of rooms you are allowed in.
   * Configured ratelimits.

Features which might be better advertised elsewhere include:

 * Support for e2e key backups
   ([MSC1219](https://github.com/matrix-org/matrix-doc/issues/1219)) - list in
   `/client/versions`.

 * Support for lazy-loading of room members - list in `/client/versions`.

 * Media size limits - list in `/media/r0/config`, because the media server may
   be a separate process.

 * Optional transports/encodings for the CS API - probably better handled via
   HTTP headers etc.

 * Variations in room state resolution - this is implied via the room version
   (which is in the `m.room.create` event).

## Tradeoffs

One alternative would be to provide specific ways of establishing support for
each operation: for example, a client might send an `GET
/_matrix/client/r0/account/password` request to see if the user can change
their password. The concern with this approach is that this could require a
large number of requests to establish which entries should appear on a menu or
dialog box.

Another alternative is to provide a generic query mechanism where the client
can query for specific capabilities it is interested in. However, this adds
complication and makes it harder to discover capability identifiers.

## Potential issues

None yet identified.

## Security considerations

None yet identified.

## Conclusion

We propose adding a new endpoint to the Client-Server API, which will allow
clients to query for supported operations so that they can decide whether to
expose them in their user-interface.
