# MSC3851: Allow custom room presets when creating a room

When a client requests for a room to be created using the [`POST
/_matrix/client/v3/createRoom`](https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3createroom)
endpoint, they are able to specify a "room preset", which can be one of
"private_chat", "public_chat" or "trusted_private_chat". They can also choose
not to specify a preset, in which case the homeserver will choose one for them
based on the room's `visibility` parameter.

The room's preset helps determine the initial state events that will be sent
into the room. This can also be augmented further by setting the
`initial_state` parameter, allowing a client to configure a room to its taste
upon creation. This is useful for a Matrix app that wishes to always send
particular state whenever a room is created.

One can run into friction when putting this system into practice - particularly
when changing what the default state of a room created by a client should be.
Since the `room_preset` and `initial_state` parameters are decided by a client,
you must roll out an update to your clients in order to change this. This can
take time to propagate, and is insufficient if an enterprise policy requires an
immediate rollout. The situation is made worse if you manage multiple, distinct
client implementations.


## Proposal

This proposal advocates for the ability of a client to set a custom, namespaced
string for the `room_preset` field when creating a room. This string identifies
a desired configuration, such as `com.example.room_preset.dm` which the
homeserver would map to a set of initial room state. Such mapping could be
updated immediately without needing to modify client code.

For the spec to allow this, the `preset` parameter of [`POST
/_matrix/client/v3/createRoom`](https://spec.matrix.org/v1.3/client-server-api/#post_matrixclientv3createroom)
is updated to allow arbitrary strings, in addition to the previously specified
values.

If the value of the `room_preset` field is not recognised, an HTTP 400 response
with error code `M_BAD_JSON` MUST be returned by the homeserver. In this case,
a room should not be created. (Note that Synapse will return this error
response if an unspecified room preset is used today. This proposal chooses to
reuse that response shape for convenience).


## Potential issues

This proposal is primarily aimed at those who are building custom Matrix
applications for niche purposes. The proposal does not currently specify a
method for the homeserver to communicate the custom room presets that it
supports to clients. While this is fine if you expect your client to always
connect to a known list of homeservers (which you know will support the custom
room preset), it would be problematic for a client that wishes to make use of
the custom room preset only when the homeserver signals support.

The author of this MSC is interested in potential use cases that fit the
latter.

Adding a new custom room preset for clients to be aware of would still require
rolling out an update to clients - but this is likely to be much less frequent
than modifying a custom room preset already in use.


## Alternatives

Clients could continue to set `initial_state`, and receive updates to what they
should send through a separate mechanism; perhaps a matrix room, or even an
endpoint on a service somewhere. It does complicate the client implementation
however. The proposed solution effectively moves the complexity to the
homeserver, and immediately ensures that all rooms created by clients after the
point of change are using the latest state. If clients are polling for this
information, the poll period may race with the creation of a room.

With this proposal, modifying the `room_preset` an existing client
implementation sends is trivial.


## Security considerations

None.

## Unstable prefix

None.

## Dependencies

None.
