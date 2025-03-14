# MSC4057: Static Room Directory

A room alias scoped to a domain name is often used to communicate a room as being official or to
improve discoverability of a room. This currently requires a more or less fully fledged homeserver
reachable on the domain. Hosting a homeserver may however be undesired due to the resource and
maintenance requirements.

This proposal aims to simplify hosting a room alias mapping by utilizing existing well-known lookup
infrastructure utilized by matrix, without requiring a full federation API supporting homeserver.

## Proposal

Currently, a homeserver needing to resolve a room alias would need to call out to
[the query directory federation endpoint](https://spec.matrix.org/v1.8/server-server-api/#get_matrixfederationv1querydirectory),
contacting the server by the domain in the alias.

This MSC proposes a new path in the `.well-known/matrix` directory on the domain name of the server (where one
would put `.well-known/matrix/server` for delegated federation) called `.well-known/matrix/rooms`.

As it is expected that a web server administrator has higher privilege than a user of a potential homeserver
on the same domain name, the mapping defined at this path takes precedence over a potential room directory
served over federation.

The following code block is an exemplary static room directory served at `https://example.com/.well-known/matrix/rooms`:

```json
{
    "#hq:example.com": "!OGEhHVWSdvArJzumhm:matrix.org",
    "#matrix:example.com": "!OGEhHVWSdvArJzumhm:matrix.org",
    "#synapse:example.com": "!ehXvUhWNASUkSLvAGP:matrix.org"
}
```

The next example is a room directory served on `https://conduit.rs/.well-known/matrix/rooms`:

```json
{
    "#server:conduit.rs": "!SMloEYlhCiqKwRLAgY:fachschaften.org"
}
```

A static room directory mapping is a JSON string of an object mapping from room aliases as keys to the
corresponding room id as the value.

### Resolving steps

To resolve an room alias `#hq:example.com` with the first example above, a server would first send a
`GET` request using domain from alias `example.com`, `https://example.com/.well-known/matrix/rooms` and
decode the served JSON.

In case the request fails or the JSON doesn't decode (this includes duplicate keys), the server should fall
back to the the federation api room directory lookup.

Otherwise, the server checks if the JSON object contains the room alias to be resolved `#hq:example.com` as
a key. The corresponding value is the resolved room id.

Otherwise, if the JSON object does not contain the room alias, the server falls back to the federation api
room directory lookup (see the second example above).

### Canonical room aliases

The current specification should already cover setting a statically mapped room alias as the canonical alias
for a room, as the client server api requires the server to
[ensure that the alias points to the correct room id](https://spec.matrix.org/v1.8/client-server-api/#put_matrixclientv3roomsroomidstateeventtypestatekey).

## Potential issues

To mitigate performance issues, servers may choose to request both the static and federation room directory
simultaneously or cache the responses.

The lookup could be abused by malicious clients to spam a web server hosted on the room alias domain. As
this already applies to the federation endpoint, servers might also choose to cache responses or apply rate
limits.

As resolving inherently exposes metadata to a third party, caching might also be desireable for privacy reasons.

Users on homeservers that do not support this feature will not be able to resolve room aliases served statically.
A workaround for this could be limiting the ability for setting a statically served room alias as the canonical alias
of a room to a new room version, this could discourage users of using the feature in a state in which few homeservers
support it.

## Alternatives

Instead of defining room alias mappings in a well-known path, the current `.well-known/matrix/server` content
could be extended to include a new field, delegating the room directory for an entire domain to a different home
server. This would also require some sort of permission system to support the use case described in the abstract
however, as otherwise any user on a homeserver would be able to create a room alias.

## Security considerations

For readability, the current schema uses full matrix room ids and full matrix room aliases in strings.
A faulty homeserver implementation could cache the following example response on

`https://example.com/.well-known/matrix/rooms`

```json
{
    "#matrix:matrix.org": "!evilRoomId:evil.com"
}
```

and falsely override an internal mapping of `#matrix:matrix.org` to `!evilRoomId:matrix.org`. Homeservers
should make sure to verify that mappings actually match the domain they were requested on and discard any
others.

## Unstable prefix

[MSC2324](https://github.com/matrix-org/matrix-spec-proposals/pull/2324) describes well-known apis as not being
able to be versioned, however while this proposal is not considered stable, implementations should use
`.well-known/matrix/org.matrix.msc4057.rooms` as the path instead of `.well-known/matrix/rooms`.

## Dependencies

None.
