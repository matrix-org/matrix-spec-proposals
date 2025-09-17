# MSC4354: Sticky Events

MatrixRTC currently depends on [MSC3757](https://github.com/matrix-org/matrix-spec-proposals/pull/3757)
for sending per-user per-device state. MatrixRTC wants to be able to share a temporary state to all
users in a room to indicate whether the given client is in the call or not. 

The concerns with MSC3757 and using it for MatrixRTC are mainly:

1. In order to ensure other users are unable to modify each other’s state, it proposes using
   string packing for authorization which feels wrong, given the structured nature of events.  
2. Allowing unprivileged users to send arbitrary amounts of state into the room is a potential
   abuse vector, as these states can pile up and can never be cleaned up as the DAG is append-only.  
3. State resolution can cause rollbacks. These rollbacks may inadvertently affect per-user per-device state.

Other proposals have similar problems such as live location sharing which uses state events when it
really just wants per-user last-write-wins behaviour.

There currently exists no good communication primitive in Matrix to send this kind of data. EDUs are
almost the right primitive, but:

* They can’t be sent via clients (there is no concept of EDUs in the Client-Server API\!
  [MSC2477](https://github.com/matrix-org/matrix-spec-proposals/pull/2477) tries to change that)  
* They aren’t extensible.   
* They do not guarantee delivery. Each EDU type has slightly different persistence/delivery guarantees,
  all of which currently fall short of guaranteeing delivery.

This proposal adds such a primitive, called Sticky Events, which provides the following guarantees:

* Eventual delivery (with timeouts) and convergence.  
* Access control tied to the joined members in the room.  
* Extensible, able to be sent by clients.

This new primitive can be used to implement MatrixRTC participation, live location sharing, among other functionality.

## Proposal

Message events can be annotated with a new top-level `sticky` key, which MUST have a `duration_ms`,
which is the number of milliseconds for the event to be sticky. The presence of `sticky.duration_ms`
with a valid value makes the event “sticky”[^stickyobj]. Valid values are the integer range 0-3600000 (1 hour).

```json
{
    "type": "m.rtc.member",
    "sticky": {
        "duration_ms": 600000
    },
    "sender": "@alice:example.com",
    "room_id": "!foo",
    "origin_server_ts": 1757920344000,
    "content": { ... }
}
```

This key can be set by clients in the CS API by a new query parameter `stick_duration_ms`, which is
added to the following endpoints:

* `PUT /_matrix/client/v3/rooms/{roomId}/send/{eventType}/{txnId}`
* `PUT /_matrix/client/v3/rooms/{roomId}/state/{eventType}/{stateKey}`

To calculate if any sticky event is still sticky:

* Calculate the start time:  
  * The start time is `min(now, origin_server_ts)`. This ensures that malicious origin timestamps cannot
    specify start times in the future.  
  * If the event is pushed via `/send`, servers MAY use the current time as the start time. This minimises
    the risk of clock skew causing the start time to be too far in the past. See “Potential issues \> Time”.  
* Calculate the end time as `start_time + min(stick_duration_ms, 3600000)`.  
* If the end time is in the future, the event remains sticky.

Sticky events are like normal message events and are authorised using normal PDU checks. They have the
following _additional_ properties:

* They are eagerly synchronised with all other servers.[^partial]  
* They must appear in the `/sync` response.[^sync]  
* The soft-failure checks MUST be re-evaluated when the membership state changes for a user with unexpired sticky events.[^softfail]

To implement these properties, servers MUST:

* Attempt to send all sticky events to all joined servers, whilst respecting per-server backoff times.
  Large volumes of events to send MUST NOT cause the sticky event to be dropped from the send queue on the server.  
* Ensure all sticky events are delivered to clients via `/sync` in a new section of the sync response,
  regardless of whether the sticky event falls within the timeline limit of the request.  
* When a new server joins the room, the server MUST attempt delivery of all sticky events immediately.  
* Remember sticky events per-user, per-room such that the soft-failure checks can be re-evaluated.

When an event loses its stickiness, these properties disappear with the stickiness. Servers SHOULD NOT
eagerly synchronise such events anymore, nor send them down `/sync`, nor re-evaluate their soft-failure status.
Note: policy servers and other similar antispam techniques still apply to these events.

The new sync section looks like:

```js
{
  "rooms": {
    "join": {
      "!726s6s6q:example.com": {
        "account_data": { ... },
        "ephemeral": { ... },
        "state": { ... },
        "timeline": { ... },
        "sticky": {
            "events": [
                {
                    "sender": "@bob:example.com",
                    "type": "m.foo",
                    "sticky": {
                      "duration_ms": 300000
                    },
                    "origin_server_ts": 1757920344000,
                    "content": { ... }
                },
                {
                    "sender": "@alice:example.com",
                    "type": "m.foo",
                    "sticky": {
                      "duration_ms": 300000
                    },
                    "origin_server_ts": 1757920311020,
                    "content": { ... }
                }
            ]
        }
    }
  }
}

```

Over Simplified Sliding Sync, Sticky Events have their own extension `sticky_events`, which has the following response shape:

```js
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
              "content": { ... }
          }]
      }
  }
}
```

Sticky messages MAY be sent in the timeline section of the `/sync` response, regardless of whether
or not they exceed the timeline limit[^ordering]. If a sticky event is in the timeline, it MAY be
omitted from the `sticky.events` section. This ensures we minimise duplication in the `/sync` response JSON.

Servers SHOULD rate limit sticky events over federation. If the rate limit kicks in, servers MUST
return a non-2xx status code from `/send` such that the sending server *retries the request* in order
to guarantee that the sticky event is eventually delivered. Servers MUST NOT silently drop sticky events
and return 200 OK from `/send`, as this breaks the eventual delivery guarantee.

These messages may be combined with [MSC4140: Delayed Events](https://github.com/matrix-org/matrix-spec-proposals/pull/4140)
to provide heartbeat semantics (e.g required for MatrixRTC). Note that the sticky duration in this proposal
is distinct from that of delayed events. The purpose of the sticky duration in this proposal is to ensure sticky events are cleaned up.

### Implementing a map

MatrixRTC relies on a per-user, per-device map of RTC member events. To implement this, this MSC proposes
a standardised mechanism for determining keys on sticky events, the `content.sticky_key` property:

```js
{
    "type": "m.rtc.member",
    "sticky": {
        "duration_ms": 300000
    },
    "sender": "@alice:example.com",
    "room_id": "!foo",
    "origin_server_ts": 1757920344000,
    "content": {
        "sticky_key": "LAPTOPXX123",
        ...
    }
}
```

`content.sticky_key` is ignored server-side[^encryption] and is purely informational. Clients which
receive a sticky event with a sticky key SHOULD keep a map with keys determined via the 4-uple
`(room_id, sender, type, content.sticky_key)` to track the current values in the map. Nothing stops
users sending multiple events with the same `sticky_key`. To deterministically tie-break, clients which
implement this behaviour MUST:

- pick the one with the highest `origin_server_ts`,  
- tie break on the one with the highest lexicographical event ID (A < Z).

When overwriting keys, clients SHOULD use the same sticky duration as the previous sticky event to avoid clients diverging.
This can happen when a client sends a sticky event with key K with a long timeout, then overwrites it with the same key K’
with a short timeout. If the sticky event K’ fails to be sent to all servers before the short timeout is hit,
some clients will believe the state is K and others will have no state. This will only resolve once the long timeout is hit.

Note that encrypted sticky events will encrypt some parts of the 4-uple. An encrypted sticky event only exposes the room ID and sender to the server:

```js
{
  "content": {
	"algorithm": "m.megolm.v1.aes-sha2",
	"ciphertext": "AwgCEqABubgx7p8AThCNreFNHqo2XJCG8cMUxwVepsuXAfrIKpdo8UjxyAsA50IOYK6T5cDL4s/OaiUQdyrSGoK5uFnn52vrjMI/+rr8isPzl7+NK3hk1Tm5QEKgqbDJROI7/8rX7I/dK2SfqN08ZUEhatAVxznUeDUH3kJkn+8Onx5E0PmQLSzPokFEi0Z0Zp1RgASX27kGVDl1D4E0vb9EzVMRW1PrbdVkFlGIFM8FE8j3yhNWaWE342eaj24NqnnWJ5VG9l2kT/hlNwUenoGJFMzozjaUlyjRIMpQXqbodjgyQkGacTEdhBuwAQ",
	"device_id": "AAvTvsyf5F",
	"sender_key": "KVMNIv/HyP0QMT11EQW0X8qB7U817CUbqrZZCsDgeFE",
	"session_id": "c4+O+eXPf0qze1bUlH4Etf6ifzpbG3YeDEreTVm+JZU"
  },
  "origin_server_ts": 1757948616527,
  "sender": "@alice:example.com",
  "type": "m.room.encrypted",
  "sticky": {
      "duration_ms": 600000
  },
  "event_id": "$lsFIWE9JcIMWUrY3ZTOKAxT_lIddFWLdK6mqwLxBchk",
  "room_id": "!ffCSThQTiVQJiqvZjY:matrix.org"
}
```

The decrypted event would contain the `type` and `content.sticky_key`.

## Potential issues

### Time

Servers who can’t maintain correct clock frequency may expire sticky events at a slightly slower/faster rate
than other servers. As the maximum timeout is relatively low, the total deviation is also reasonably low,
making this less problematic. The alternative of explicitly sending an expiration event would likely cause
more deviation due to retries than deviations due to clocks.

Servers with significant clock skew may set `origin_server_ts` too far in the past or future. If the value
is too far in the past this will cause sticky events to expire quicker than they should, or to always be
treated as expired. If the value is too far in the future, this has no effect as it is bounded by the current time.
As such, this proposal relies somewhat on NTP to ensure clocks over federation are roughly in sync.
As a consequence of this, the sticky duration SHOULD NOT be set to below 5 minutes.[^ttl] 

### Encryption

Encrypted sticky events reduce reliability as in order for a sticky event to be visible to the end user it
requires *both* the sending client to think the receiver is joined (so we encrypt for their devices) and the
receiving server to think the sender is joined (so it passes auth checks). Unencrypted events only strictly
require the receiving server to think the sender is joined.

The lack of historical room key sharing may make some encrypted sticky events undecryptable when new users join the room. 

### Spam

Servers may send every event as a sticky event, causing a higher amount of events to be sent eagerly over federation
and to be sent down `/sync` to clients. The former is already an issue as servers can simply `/send` many events.
The latter is a new abuse vector, as up until this point the `timeline_limit` would restrict the amount of events
that arrive on client devices (only state events are unbounded and setting state is a privileged operation).
This proposal has the following protections in place:

* All sticky events expire, with a hard limit of 1 hour. The hard limit ensures that servers cannot set years-long expiry times.
  This ensures that the data in the `/sync` response can go down and not grow unbounded.  
* All sticky events are subject to normal PDU checks, meaning that the sender must be authorised to send events into the room.  
* Servers sending lots of sticky events may be asked to try again later as a form of rate-limiting.
  Due to data expiring, subsequent requests will gradually have less data.

## Alternatives

### Use state events

We could do [MSC3757](https://github.com/matrix-org/matrix-spec-proposals/pull/3757), but for the
reasons mentioned at the start we don’t really want to do so.

### Make stickiness persistent not ephemeral

There are arguments that, at least for some use cases, we don’t want these sticky events to timeout.
However, that opens the possibility of bloating the `/sync` response with sticky events.

Suggestions for minimizing that have been to have a hard limit on the number of sticky events a user can have per room,
instead of a timeout. However, this has two drawbacks: a) you still may end up with substantial bloat as stale data doesn’t
automatically get reaped (even if the amount of bloat is limited), and b) what do clients do if there are already too many
sticky events? The latter is tricky, as deleting the oldest may not be what the user wants if it happens to be not-stale data,
and asking the user what data it wants to delete vs keep is unergonomic.

Non-expiring sticky events could be added later if the above issues are resolved.

### Have a dedicated ‘ephemeral user state’ section

Early prototypes of this proposal devised a key-value map with timeouts maintained over EDUs rather than PDUs.
This early proposal had much the same feature set as this proposal but with one major difference: equivocation.
Servers could broadcast different values for the same key to different servers, causing the map to not converge:
the Byzantine Broadcast problem. Matrix already has a data structure to agree on shared state: the room DAG.
As such, this led to the prototype to the current proposal. By putting the data into the DAG, other servers
can talk to each other via it to see if they have been told different values. When combined with a simple
conflict resolution algorithm (which works because there is [no need for coordination](https://arxiv.org/abs/1901.01930)),
this provides a way for clients to agree on the same values. Note that in practice this needs servers to *eagerly*
share forward extremities so servers aren’t reliant on unrelated events being sent in order to check for equivocation.
Currently, there is no mechanism for servers to express “these are my latest events, what are yours?” without actually sending another event.

## Security Considerations

Servers may equivocate over federation and send different events to different servers in an attempt to cause
the key-value map maintained by clients to not converge. Alternatively, servers may fail to send sticky events
to their own clients to produce the same outcome. Federation equivocation is mitigated by the events being
persisted in the DAG, as servers can talk to each other to fetch all events. There is no way to protect against
dropped updates for the latter scenario.

## Unstable Prefix

- The `stick_duration_ms` query param is `msc4354_stick_duration_ms`.
- The `sticky` key in the PDU is `msc4354_sticky`.
- The `/sync` response section is `msc4354_sticky_events`.
- The sticky key in the `content` of the PDU is `msc4354_sticky_key`.

[^stickyobj]: The presence of the `sticky` object alone is insufficient.  
[^partial]: Over federation, servers are not required to send all timeline events to every other server.
Servers mostly lazy load timeline events, and will rely on clients hitting `/messages` which in turn
hits`/backfill` to request events from federated servers.  
[^sync]: Normal timeline events do not always appear in the sync response if the event is more than `timeline_limit` events away.  
[^softfail]: Not all servers will agree on soft-failure status due to the check considering the “current state” of the room.
To ensure all servers agree on which events are sticky, we need to re-evaluate this rule when the current room state changes.
This becomes particularly important when room state is rolled back. For example, if Charlie sends some sticky event E and
then Bob kicks Charlie, but concurrently Alice kicks Bob then whether or not a receiving server would accept E would depend
on whether they saw “Alice kicks Bob” or “Bob kicks Charlie”. If they saw “Alice kicks Bob” then E would be accepted. If they
saw “Bob kicks Charlie” then E would be rejected, and would need to be rolled back when they see “Alice kicks Bob”.  
[^ordering]: Sticky events expose gaps in the timeline which cannot be expressed using the current sync API. If sync used
something like [stitched ordering](https://codeberg.org/andybalaam/stitched-order)
or [MSC3871](https://github.com/matrix-org/matrix-spec-proposals/pull/3871) then sticky events could be inserted straight
into the timeline without any additional section, hence “MAY” would enable this behaviour in the future.  
[^encryption]: Previous versions of this proposal had the key be at the top-level of the event JSON so servers could
implement map-like semantics on client’s behalf. However, this would force the key to remain visible to the server and
thus leak metadata. As a result, the key now falls within the encrypted `content` payload, and clients are expected to
implement the map-like semantics should they wish to.  
[^ttl]: Earlier designs had servers inject a new `unsigned.ttl_ms` field into the PDU to say how many milliseconds were left.
This was problematic because it would have to be modified every time the server attempted delivery of the event to another server.
Furthermore, it didn’t really add any more protection because it assumed servers honestly set the value.
Malicious servers could set the TTL to be 0 ~ `sticky.duration_ms` , ensuring maximum divergence
on whether or not an event was sticky. In contrast, using `origin_server_ts` is a consistent reference point
that all servers are guaranteed to see, limiting the ability for malicious servers to cause divergence as all
servers approximately track NTP.
