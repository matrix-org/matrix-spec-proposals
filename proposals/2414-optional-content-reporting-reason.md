# MSC2414: Make `reason` and `score` optional for reporting content

## Proposal
This MSC proposes to remove the `required` flag for both the `reason` and `score`
parameters, as well as the "may be blank" clause in the description of `reason`.

## Rationale

### `reason` Parameter

Currently, the spec says that the `reason` parameter on the content reporting
endpoint is required, but also says that the string "may be blank." This
seems to be a contradiction.

Note that the kicking and banning endpoints already have optional `reason`
parameters. The other membership endpoints mentioned in
[#2367][membership-endpoints] will also add optional `reason` parameters,
so it would be more more consistent with the rest of the spec to make this
optional as well.

### `score` Parameter

The spec also requires the `score` parameter, but its usefulness is limited.
Offensiveness is difficult to measure and is likely not going to be applied
consistently across several rooms. Because of this ambiguity, it seems, many
clients [simply hard-code the integer value][hard-code].

To make this useful, for example, room administrators would need a way to map more
specific values to the integer range and perhaps even instruct the client to
display those mappings to the user. That may be possible to do in a closed
client/homeserver implementation, but not generally across the Matrix protocol.

Making `score` optional would enable this feature to be used in specific contexts
while not forcing clients to support the ambiguity it brings.

## Backwards Compatibility

Since servers currently expect these fields to be sent by all clients, making
them optional is a breaking change. Clients should check the spec versions
the homeserver supports to detect this change.

[membership-endpoints]: https://github.com/matrix-org/matrix-doc/pull/2367
[hard-code]: https://github.com/matrix-org/matrix-react-sdk/pull/3290/files#diff-551ca16d6a8ffb96888b337b5246402dR66
