# MSCXXXX: Reliable call membership

In [MSC3401](https://github.com/matrix-org/matrix-spec-proposals/pull/3401), clients announce their participation in a
call by sending a state event of type `m.call.member`, with their user ID as the state key. This approach is generally
viable, but leaves some reliability issues unsolved:

- If a client goes offline while participating in a call, they will be unable to update their call membership state to tell others that they have left.
  - This prevents clients from showing an accurate preview of who's connected to a call.
  - In a product like Element Call, where users often join calls with burner accounts and leave them by closing the browser tab, stale call members can build up until a room becomes unusable, since clients joining the call will end up sending out many many to-device messages to invite stale users.
- There's no way for clients to atomically update their call membership state.
  - If a user tries to switch devices mid-call, the device that's hanging up may race with the device that's joining as they both try to update the same room state, resulting in one of the updates overwriting the other.

In other group VoIP systems, this is typically solved by having a central application server which tracks each
participant's connectivity and acts as the source of truth for who's on the call. In Matrix, the closest thing we have
is a homeserver.

## Proposal

Since homeservers are less likely to go offline unexpectedly than clients, we propose that homeservers should manage
call member state on behalf of clients. If a user's device goes offline (i.e. disconnects from all event streams), the
homeserver should update the `m.devices` lists of any `m.call.member` state associated with that user, to remove entries
with a matching `device_id`.

To facilitate atomic updates to call member state, we also propose two new CS API endpoints:

### `PUT /_matrix/client/v3/rooms/{roomId}/calls/{callId}/member`

A request to this endpoint instructs the homeserver to set or update the entry for the requesting device in the user's
`m.call.member` state for the given room and call. The request body is the new device entry, but with the `device_id`
field omitted.

For example, if Alice starts with an `m.call.member` state of `{}` and calls
`PUT /_matrix/client/v3/rooms/!aaa:example.org/calls/111/member` with the following request body:

```jsonc
{
  "session_id": "GHKJFKLJLJ",
  "feeds": [
    // ...
  ]
}
```

then her `m.call.member` state would be updated to:

```jsonc
{
  "m.calls": [
    {
      "m.call_id": "111",
      "m.devices": [
        {
          "device_id": "ASDUHDGFYUW",
          "session_id": "GHKJFKLJLJ",
          "feeds": [
            // ...
          ]
        }
      ]
    }
  ]
}
```

### `DELETE /_matrix/client/v3/rooms/{roomId}/calls/{callId}/member`

A request to this endpoint removes the entry for the requesting device. If, after the previous example, Alice made a
request to `DELETE /_matrix/client/v3/rooms/!aaa:example.org/calls/111/member`, her `m.call.member` state for that room
would return to being `{}`.

## Potential issues

This proposal assumes that homeservers never go offline during calls, but in reality they can. Homeserver developers
should consider the implications of their server restarting or experiencing downtime during calls, but the specifics of
what they do with call member state in these scenarios is left as an implementation detail.

## Alternatives

A previous version of [MSC3401](https://github.com/matrix-org/matrix-spec-proposals/pull/3401) put expiration timestamps
on device entries in call member state, as a simple way of keeping call members from sticking around indefinitely if
they go offline. But because room state in Matrix is not well equipped for frequent updates, in practice clients had to
set the expiration time to ~1 hour, which is far too long; ideally, a participant should appear to leave the call within
10 seconds of going offline, to avoid confusing users. A timestamp-based approach also caused calls to break down if any
participant had a significantly desynced clock.

The `/_matrix/client/v3/rooms/{roomId}/calls/{callId}/member` endpoints should arguably be replaced by a more general
mechanism to atomically update data structures in room state, since power levels are another example of state that
suffers from races when updates overlap. But unlike power levels, call member state has the property that there will
generally only be one server producing updates to any given key, since those keys are user IDs. Such a mechanism for
atomic updates would be less useful in the case of power levels, since updates coming from across federation could
easily clobber one homeserver's update anyways.

## Security considerations

This change shouldn't have any security implications.

## Unstable prefix

While this feature is in development, the endpoints `PUT/DELETE /_matrix/client/v3/rooms/{roomId}/calls/{callId}/member`
should instead be exposed as
`PUT/DELETE /_matrix/client/unstable/town.robin.mscXXXX/rooms/{roomId}/calls/{callId}/member`.

### While the MSC is unstable

During this period, to detect server support clients should check for the presence of
the `town.robin.mscXXXX` flag in `unstable_features` on `/versions`. Servers are also
required to use the unstable prefixes (see [unstable prefix](#unstable-prefix)) during
this time.

### Once the MSC is merged but not in a spec version

Once this MSC is merged, but is not yet part of the spec, clients should rely on the
presence of the `town.robin.mscXXXX.stable` flag in `unstable_features` to determine
server support. If the flag is present, clients may use the stable prefixes.

### Once the MSC is in a spec version

Once this MSC becomes a part of a spec version, clients should rely on the presence of
the spec version that supports the MSC, in `versions` on `/versions`, to determine
support. Servers are encouraged to keep the `town.robin.mscXXXX.stable` flag around for
a reasonable amount of time to help smooth over the transition for clients. "Reasonable"
is intentionally left as an implementation detail, however the MSC process currently
recommends *at most* 2 months from the date of spec release.

## Dependencies

This MSC builds on [MSC3401](https://github.com/matrix-org/matrix-spec-proposals/pull/3401) (which at the time of
writing has not yet been accepted into the spec).
