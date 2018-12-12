# MSC1753: client-server capabilities API

A mechanism is needed for clients to interrogate servers to establish whether
particular operations can be performed.

For example, users may not be able to change their password if a server is
configured to authenticate against a separate system, in which case it is
nonsensical to offer the user such an option.

## Proposal

### `POST /_matrix/client/r0/capabilities`

We will add a new endpoint to the client-server API: `POST
/_matrix/client/r0/capabilities`. The endpoint will be authenticated as normal
via an access token.

The body of the request will list the capabilities the client is interested
in, as shown:

```json
{
    "capabilities": {
        "m.capability_one": {},
        "com.example.custom_capability": {}
    }
}
```

The keys of the `capabilities` object are capability identifiers. As with
other identifiers in the Matrix protocol, the `m.` prefix is reserved for
definition in the Matrix specification; other values can be used within an
organisation following the Java package naming conventions.

The values of the `capabilities` object will depend on the capability
identifier, though in general the empty object will suffice.

The server should reply with a list of the operations the client may perform,
as shown:

```json
{
    "capabilities": {
        "m.capability_one": {}
    }
}
```

The server should exclude from the list any operations which the client cannot
currently perform. It should also exclude any capabilities it does not
recognise or support, or whose value in the query did not have the expected
form.

Again the values of the `capabilities` object will depend on the capability
identifier.

### Initial capability identifiers

As a starting point, a single capability identifier is proposed:
`m.change_password`, which should be considered supported if it is possible to
change the user's password via the `POST /_matrix/client/r0/account/password`
API.

The values of the `capabilities` object should be the empty object in both the
query and the response.

### Fallback behaviour

Clients will need to be aware of servers which do not support the new endpoint,
and fall back to their current behaviour if they receive a 404 response.

## Tradeoffs

One alternative would be to provide specific ways of establishing support for
each operation: for example, a client might send an `GET
/_matrix/client/r0/account/password` request to see if the user can change
their password. The concern with this approach is that this could require a
large number of requests to establish which entries should appear on a menu or
dialog box.

Another alternative would be a simple `GET /_matrix/client/r0/capabilities`
query, where a server would return all possible supported operations. The
problem with this is that it may add load to the server, and increase network
traffic, by returning a large number of features which the client may have no
interest in.

## Potential issues

None yet identified.

## Security considerations

None yet identified.

## Conclusion

We propose adding a new endpoint to the Client-Server API, which will allow
clients to query for supported operations so that they can decide whether to
expose them in their user-interface.
