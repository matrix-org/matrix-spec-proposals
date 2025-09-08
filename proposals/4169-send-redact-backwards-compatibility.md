# MSC4169: Backwards-compatible redaction sending using `/send`
[MSC2174] moved the `redacts` key from the top level to inside `content`. It
also defined forwards- and backwards-compatibility for receiving by defining
that servers will copy the key to both locations when serving events to clients.
The `/redact` endpoint is also forwards-compatible because it works in all room
versions. However, `/send` was not made backwards-compatible. This means that
clients can't switch to using `/send` unless they keep track of room versions.

Additionally, [MSC4140] currently only defines delaying events for `/send`.
While it could be extended to support `/redact` for self-destructing messages,
the MSC can also work as-is if `/send` supported redactions in all room
versions.

[MSC4140]: https://github.com/matrix-org/matrix-spec-proposals/pull/4140
[MSC2174]: https://github.com/matrix-org/matrix-spec-proposals/pull/2174

## Proposal
The proposed solution is to have the server move the `redacts` key from the
content to the top level of the event when `/send/m.room.redaction` is called
in a pre-v11 room.

Additionally, the `/redact` endpoint is deprecated, as there is no longer any
reason to use it.

## Potential issues
Servers that don't support this MSC may behave unexpectedly if a client tries
to redact using `/send` in an old room. Synapse currently throws an assertion
error (which turns into HTTP 500) when trying to redact with /send in a pre-v11
room, which shouldn't cause any issues other than the request failing. Clients
can avoid issues by confirming server support using `/versions` first.

## Alternatives
### Client-side switching
Clients could remember room versions themselves and adjust the endpoint based
on that. This works fine for thick clients which cache data locally anyway, but
does not work for things like bots which have minimal local state.

### Just use `/redact`
`/redact` works fine for all room versions. We could discourage using `/send`
for redactions and prefer `/redact` instead.

## Security considerations
This allows clients to send arbitrary content in pre-v11 redaction events.
It shouldn't cause any security issues, as it's already possible in v11+ rooms
or with a modified server.

## Unstable prefix
The endpoint itself has no unstable prefix as it can already be used to send
redactions in v11+ rooms. Support for the transformation in old room versions
can be detected using the `com.beeper.msc4169` unstable feature flag in the
`/versions` response. The feature flag should continue to be advertised after
the MSC is accepted until the server advertises support for the stable spec
release that includes this MSC.

## Dependencies
None.
