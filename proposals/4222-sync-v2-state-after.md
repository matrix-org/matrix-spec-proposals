# MSC4222: Adding `state_after` to `/sync`

The current [`/sync`](https://spec.matrix.org/v1.14/client-server-api/#get_matrixclientv3sync) API does not
differentiate between state events in the timeline and updates to state, and so can cause the client's view
of the current state of the room to diverge from the actual state of the room as seen by the server.

The fundamental issue is that clients need to know the current authoritative room state, but the current model
lacks an explicit representation of that. Clients derive state by assuming a linear application of events, for
example:

```
state_before + timeline => state_after
```

However, room state evolves as a DAG (Directed Acyclic Graph), not a linear chain. A simple example illustrates:
```diagram
   A
   |
   B
  / \
 C   D

```
Each of A, B, C, and D are non-conflicting state events.
- State after C = `{A, B, C}`
- State after D = `{A, B, D}`
- Current state = `{A, B, C, D}`

In this case, both C and D are concurrent, so the correct current state includes both. Clients that try to reconstruct
state from a timeline such as `[A, B, C, D]` or `[A, B, D, C]` might trivially compute a union — and for non-conflicting
cases, this works.

However, once conflicting state enters, resolution is needed. Consider this more complex example:
```diagram
   A
   |
   B
  / \
 C   C'   <-- C' wins via state resolution
  \ / \
   D   E
```
Here, C and C' are conflicting state events — for example, both might define a different `m.room.topic`. Let's say C' wins
according to the server's state resolution rules. Then D and E are independent non-conflicting additions.
- State after C = `{A, B, C}`
- State after D = `{A, B, C'}`
- State after E = `{A, B, C', E}`
- Current state = `{A, B, C', D, E}`

Now suppose the client first receives timeline events `[A, B, C', E]`. The state it constructs is:
```
{A, B, C', E}  ← Correct so far
```
Then it receives a subsequent sync with timeline `[C, D]`, and the state block includes only `{B}`. Under the current
`/sync` behavior:
- The timeline includes state event C, which incorrectly replaces C'.
- The client ends up with `{A, B, C, D, E}`, which is **invalid** — it prefers the wrong version of C.
This happens because the client re-applies C from the timeline, unaware that C' had already been resolved and accepted
earlier. There's no way for the client to know that C' is supposed to win, based solely on the timeline.

In [MSC4186 - Simplified Sliding Sync](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) this problem is
solved by the equivalent `required_state` section including all state changes between the previous sync and the end of
the current sync, and clients do not update their view of state based on entries in the timeline.


## Proposal

This change is gated behind the client adding a `?use_state_after=true` (the unstable name is
`org.matrix.msc4222.use_state_after`) query param.

When enabled, the Homeserver will **omit** the `state` section in the room response sections. This is replaced by
`state_after` (the unstable field name is `org.matrix.msc4222.state_after`), which will include all state changes between the
previous sync and the *end* of the timeline section of the current sync. This is in contrast to the old `state` section
that only included state changes between the previous sync and the *start* of the timeline section. Note that this does
mean that a new state event will (likely) appear in both the timeline and state sections of the response.

This is basically the same as how state is returned in [MSC4186 - Simplified Sliding
Sync](https://github.com/matrix-org/matrix-spec-proposals/pull/4186).

Clients **MUST** only update their local state using `state_after` and **NOT** consider the events that appear in the timeline section of `/sync`.

Clients can tell if the server supports this change by whether it returns a `state` or `state_after` section in the
response. Servers that support this change **MUST** return the `state_after` property, even if empty.

### Examples

#### Example 1 \- Common case

Let’s take a look at the common case of a state event getting sent down an incremental sync, which is non-gappy.

<table>
<tr><th>Previously</th><th>Proposed</th></tr>
<tr>
<td>

```json
{
  "timeline": {
    "events": [ {
      "type": "org.matrix.example",
      "state_key": ""
    } ],
    "limited": false,
  },
  "state": {
    "events": []
  }
}
```

</td>
<td>

```json
{
  "timeline": {
    "events": [ {
      "type": "org.matrix.example",
      "state_key": ""
    } ],
    "limited": false,
  },
  "state_after": {
    "events": [ {
      "type": "org.matrix.example",
      "state_key": ""
    } ]
  }
}
```

</td>
</tr>
</table>

Since the current state of the room will include the new state event, it's included in the `state_after` section.

> [!NOTE]
> In the proposed API the state event comes down both in the timeline section *and* the state section.


#### Example 2 - Receiving “outdated” state

Next, let’s look at what would happen if we receive a state event that does not take effect, i.e. that shouldn’t cause the client to update its state.

<table>
<tr><th>Previously</th><th>Proposed</th></tr>
<tr>
<td>

```json
{
  "timeline": {
    "events": [ {
      "type": "org.matrix.example",
      "state_key": ""
    } ],
    "limited": false,
  },
  "state": {
    "events": []
  }
}
```

</td>
<td>

```json
{
  "timeline": {
    "events": [ {
      "type": "org.matrix.example",
      "state_key": ""
    } ],
    "limited": false,
  },
  "state_after": {
    "events": []
  }
}
```

</td>
</tr>
</table>

Since the current state of the room does not include the new state event, it's excluded from the `state_after` section.

> [!IMPORTANT]
> Even though both responses look very similar, the client **MUST NOT** update its state with the event from the timeline section when using `state_after`.


## Potential issues

With the proposed API the common case for receiving a state update will cause the event to come down in both the
`timeline` and `state_after` sections, potentially increasing bandwidth usage. However, it is common for the HTTP responses to
be compressed, heavily reducing the impact of having duplicated data.

Both before and after this proposal, clients are not able to calculate reliably exactly when in the
timeline the state changed (e.g. to figure out which message should show a user's previous/updated
display name - note that some clients e.g. Element have moved away from this UX). This is because
the accurate picture of the current state at an event is calculated by the server based on the room
DAG, including the state resolution process, and not based on a linear list of state updates.

This proposal ensures that the client has a more accurate view of the room state *after the sync has
finished*, but it does not provide any more information about the *history of state* as it relates
to events in the timeline. Clients attempting to build a best-effort view of this history by walking
the timeline may still do so, with the same caveats as before about correctness, but they should be
sure to make their view of the final state consistent with the changes provided in `state_after`.

The format of returned state in `state_after` in this proposal is a list of events. This
does not allow the server to indicate if an entry has been removed from the state. As with
[MSC4186 - Simplified Sliding Sync](https://github.com/matrix-org/matrix-spec-proposals/pull/4186),
this limitation is acknowledged but not addressed here. This is not a new issue and is left for
resolution in a future MSC.


## Alternatives

There are a number of options for encoding the same information in different ways, for example the response could
include both the `state` and a `state_delta` section, where `state_delta` would be any changes that needed to be applied
to the client calculated state to correct it. However, since
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) is likely to replace the current `/sync` API, we may as
well use the same mechanism. This also has the benefit of showing that the proposed API shape can be successfully
implemented by clients, as the MSC is implemented and in use by clients.

Another option would be for server implementations to try and fudge the state and timeline responses to ensure that
clients came to the correct view of state. For example, if the server detects that a sync response will cause the client
to come to an incorrect view of state it could either a) "fixup" the state in the `state` section of the *next* sync
response, or b) remove or add old state events to the timeline section. While both these approaches are viable, they're
both suboptimal to just telling the client the correct information in the first place. Since clients will need to be
updated to handle the new behavior for future sync APIs anyway, there is little benefit from not updating clients now.

We could also do nothing, and instead wait for [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186)
(or equivalent) to land and for clients to update to it.


## Security considerations

There are no security concerns with this proposal, as it simply encodes the same information sent to clients in a
different way

## Unstable prefix

| Name | Stable prefix | Unstable prefix |
| - | - | - |
| Query param | `use_state_after` | `org.matrix.msc4222.use_state_after` |
| Room response field | `state_after` | `org.matrix.msc4222.state_after` |

## Dependencies

None
