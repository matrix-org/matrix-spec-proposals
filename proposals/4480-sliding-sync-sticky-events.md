# MSC4480: Sliding Sync Extension: Sticky Events

[MSC4354] introduces Sticky Events using the existing [`/sync`] API.
This MSC adds support for Sticky Events in Simplified Sliding Sync as per [MSC4186].
The content of this proposal was originally part of [MSC4354] itself, but has
since been split out to avoid [MSC4354] itself depending on [MSC4186].

## Proposal

Over Simplified Sliding Sync, Sticky Events have their own extension `sticky_events`, which follows
the common extension semantics of [MSC4508] and has the following request extension shape:

``` js
{
  "enabled": true,
  "limit": 100, // optional (default 100, min 1): max number of events to return, server MAY override to a lower number
  "lists": ["rooms", "dms"], // optional, as per MSC4508
  "rooms": ["!abcd:example.com"] // optional, as per MSC4508
}
```

and, when enabled, the following response extension shape:

``` js
{
  "rooms": {
      "!726s6s6q:example.com": {
          "events": [{
              "sender": "@bob:example.com",
              "type": "m.foo",
              "sticky": {
                "duration_ms": 300000
              },
              "origin_server_ts": 1757920344000,
              "content": { ... },
              "unsigned": { "sticky_duration_remaining_ms": 289170 }
          }]
      }
  }
}
```

If the extension is enabled, the server MUST include a `sticky_events` section in the `extensions`
response field whenever it has sticky events to send. It MAY omit the section when there are none.

As with regular `/sync`, if a sticky event appears in the `timeline` section of the sync
response, it MUST NOT be included in the Sticky Events extension response.

As with regular `/sync`, no matter whether the sticky event is delivered in the `timeline`
section or the `sticky_events` extension, the server MUST include an `unsigned.sticky_duration_remaining_ms`
property with the authoritative remaining sticky duration in milliseconds.

Clients MUST use this value as the authoritative sticky duration.

In common usage, sticky events are expected to be encrypted and so there is no [state filter]
equivalent provided for sticky events e.g. to filter sticky events by event type.
(We do not anticipate common unencrypted usage to justify specifying such a mechanism at this time.)

As with timeline events, sticky events sent by ignored users MUST NOT be delivered to clients.

Servers MUST treat sticky events the same as timeline events, for the purposes of
calculating which lazy-loaded membership events to include in the sync response. That is, when a
room's combined `required_state` has `lazy_members` set, the senders of sticky events returned for
that room in this extension count as senders of `timeline` events for the purposes of the
lazy-loaded memberships of [MSC4186]. Their membership events are returned in the room's
`required_state`, so the room appears in the `rooms` section of the response even if it has no
other updates.

### Scope

The server MUST include sticky events across all rooms that are in scope for the extension, as defined
by the common per-room extension semantics of [MSC4508]. A room can be in scope without appearing in
the top-level `rooms` section of the response.

As with regular `/sync`, servers MUST only send sticky events for rooms the user is joined to. Rooms
the user was kicked or banned from can still be in scope, as [MSC4186] keeps them in lists, but MUST
NOT have sticky events sent.

Whenever a room enters scope on a connection, the server MUST send all unexpired sticky events for
that room. This applies on an initial sync (no `pos`), when the room first comes into scope on
the connection and when it re-enters scope after having dropped out. In the latter case, the server
MAY instead send only the unexpired sticky events sent while the room was out of scope. On an
incremental sync, an in-scope room is included if sticky events were sent in it since the previous
request's `pos`. When a room drops out of scope, the server stops sending sticky events for it.
Clients keep the sticky events they have, which expire as per their sticky duration.

As with regular `/sync`, when a user joins a room, the server MUST include all unexpired sticky
events for that room in their subsequent sync responses. The server MAY spread them across multiple
sync responses or the server MAY exceed the `limit` specified in the request extension for this
case, depending on implementation preference.

### Pagination

Because sticky events and to-device messages are alike in the way that they should be *reliably*
delivered to clients, without any gaps in the pagination, they follow the [MSC4538: Sliding Sync
Extension: To-Device messages] model for pagination in sliding sync, but without introducing
an additional per-extension pagination token.

In short: when there are too many sticky events to return in one response, the server returns a
limited number of the oldest sticky events that have not yet been delivered.

The server tracks this implicitly using the request-/response-wide `pos` token. A request that
repeats a `pos` returns the same sticky events again, as [MSC4186] requires for the rest of the
response. Clients MUST be prepared to receive a sticky event more than once.

### Connections

Enabling the extension partway through a connection, whether for the first time or after disabling
it, counts as every room in scope entering scope. The server therefore sends all of their unexpired
sticky events, or only those sent while the extension was disabled, as described under [scope]. This
is stricter than [MSC4508] recommends for re-enabling, because reliable delivery is the purpose of
sticky events. While the extension is disabled, no room is in scope for it.

A new connection, including one started after `M_UNKNOWN_POS`, likewise brings every room in scope
into scope. Clients need not discard previously received sticky events, as any that are still
unexpired are delivered again.

### Long-polling

A sticky event sent in an in-scope room counts as an update for the purposes of long-polling. It
causes a waiting sync request to return, even if there is nothing else to send. The same applies
while the server has undelivered sticky events to send, so that clients drain them without waiting
out long polls. Sticky events in rooms out of scope and the expiry of sticky events do not count as
updates.

[scope]: #scope

## Potential issues

Nothing beyond what’s included in [MSC4354].

Notably, the 'flickering' concern from [MSC4354] applies equally to Sliding Sync as it does to v3 Sync.

## Alternatives

Nothing beyond what’s included in [MSC4354].

## Security considerations

Nothing beyond what’s included in [MSC4354].

## Unstable prefix

While this proposal is not considered stable, the extension name `sticky_events` should be referred
to as `org.matrix.msc4354.sticky_events`. Note that this is using the original prefix from [MSC4354]
for historic reasons.

## Dependencies

This MSC builds on [MSC4354], [MSC4186] and [MSC4508].

  [MSC4354]: https://github.com/matrix-org/matrix-spec-proposals/pull/4354
  [`/sync`]: https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientv3sync
  [MSC4186]: https://github.com/matrix-org/matrix-spec-proposals/pull/4186
  [state filter]: https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3useruseridfilter_request_roomeventfilter
  [MSC4538: Sliding Sync Extension: To-Device messages]: https://github.com/matrix-org/matrix-spec-proposals/pull/4538
  [MSC4508]: https://github.com/matrix-org/matrix-spec-proposals/pull/4508
