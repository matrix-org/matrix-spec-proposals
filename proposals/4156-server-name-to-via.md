# MSC4156: Migrate `server_name` to `via`

Room IDs in Matrix are generally not routable on their own. In the [room ID grammar] `!opaque_id:domain`,
the `domain` is the server that created the room. There is, however, no guarantee that this server is
still joined to the room at a later time. Therefore, room IDs don't provide a reliable resident server
to send requests to. Critically, the `domain` is not to be used as a routing server. It is purely a namespace.

The spec partially addresses this issue by defining a [`via`] query parameter on room URIs that can be
used to list servers that have a high probability of being in the room in the distant future. Additionally,
some APIs such as [`/_matrix/client/v3/join/{roomIdOrAlias}`] can take a `server_name` query parameter
that has the same effect as `via`.

The terminology difference between `server_name` and `via` can be slightly confusing which is why this
proposal attempts to standardize on `via`.


## Proposal

The `server_name` query parameter on [`/_matrix/client/v3/join/{roomIdOrAlias}`] and
[`/_matrix/client/v3/knock/{roomIdOrAlias}`] is deprecated and a new parameter `via: [string]` is
introduced.

Clients SHOULD use `via` when the homeserver they're talking to supports it. To do this, they MAY either
detect server support through the supported spec versions in [`/_matrix/client/versions`] or always include
both parameters (with identical values).

Homeservers MUST ignore all `server_name` parameters if any `via` parameters are supplied.


## Potential issues

As with any migration, some effort will be required to update client and server implementations. Additionally,
while the transitions isn't completed, the concurrent existence of both query parameters might lead to further
confusion.


## Alternatives

None other than accepting status quo.


## Security considerations

A client that supplies different `via` and `server_name` parameters could be served a different room depending
on which set of parameters the server uses to resolve the room ID. Tricking a client into doing this seems very
difficult though because [Matrix URIs], for instance, only have a single documented `via` parameter.


## Unstable prefix

Until this proposal is accepted into the spec, implementations SHOULD refer to `via` as `org.matrix.msc4156.via`.


## Dependencies

None.


[Matrix URIs]: https://spec.matrix.org/v1.11/appendices/#matrix-uri-scheme
[room ID grammar]: https://spec.matrix.org/v1.10/appendices/#room-ids
[`via`]: https://spec.matrix.org/v1.10/appendices/#routing
[`/_matrix/client/v3/join/{roomIdOrAlias}`]: https://spec.matrix.org/v1.10/client-server-api/#post_matrixclientv3joinroomidoralias
[`/_matrix/client/v3/knock/{roomIdOrAlias}`]: https://spec.matrix.org/v1.10/client-server-api/#post_matrixclientv3knockroomidoralias
[`/_matrix/client/versions`]: https://spec.matrix.org/v1.10/client-server-api/#get_matrixclientversions
