# MSC4222: Adding `state_after` to sync v2

The current sync v2 API does not differentiate between state events in the timeline and updates to state, and so can
cause the client's view of the current state of the room to diverge from the actual state of the room. This is
particularly problematic for use-cases that rely on state being consistent between different clients.

This behavior stems from the fact that the clients update their view of the current state with state events that appear
in the timeline. To handle gappy syncs, the `state` section includes state events that are from *before* the start of
the timeline, and so are replaced by any matching state events in the timeline. This provides little opportunity for the
server to ensure that the clients come to the correct conclusion about the current state of the room.

In [MSC4186 - Simplified Sliding Sync](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) this problem is
solved by the equivalent `required_state` section including all state changes between the previous sync and the end of
the current sync, and clients do not update their view of state based on entries in the timeline.


## Proposal

This change is gated behind the client adding a `?use_state_after=true` (the unstable name is
`org.matrix.use_state_after`) query param.

When enabled, the Homeserver will **omit** the `state` section in the room response sections. This is replaced by
`state_after` (the unstable field name is `org.matrix.state_after`), which will include all state changes between the
previous sync and the *end* of the timeline section of the current sync. This is in contrast to the old `state` section
that only included state changes between the previous sync and the *start* of the timeline section. Note that this does
mean that a new state event will (likely) appear in both the timeline and state sections of the response.

This is basically the same as how state is returned in [MSC4186 - Simplified Sliding
Sync](https://github.com/matrix-org/matrix-spec-proposals/pull/4186).

State events that appear in the timeline section **MUST NOT** update the current state. The current state **MUST** only be
updated with the contents of `state_after`.

Clients can tell if the server supports this change by whether it returns a `state` or `state_after` section in the
response.

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
> Both responses are the same, but the client **MUST NOT** update its state with the event.


## Potential issues

With the proposed API the common case for receiving a state update will cause the event to come down in both the
`timeline` and `state` sections, potentially increasing bandwidth usage. However, it is common for the HTTP responses to
be compressed, heavily reducing the impact of having duplicated data.

Clients will not be able to tell when a state change happened within the timeline. This was used by some clients to
render e.g. display names of users at the time they sent the message (rather than their current display name), though
e.g. Element clients have moved away from this UX. This behavior can be replicated in the same way that clients dealt
with messages received via pagination (i.e. calling `/messages`), by walking the timeline backwards and inspecting the
`unsigned.prev_state` field. While this can lead to incorrect results, this is no worse than the previous situation.


## Alternatives

There are a number of options for encoding the same information in different ways, for example the response could
include both the `state` and a `state_delta` section, where `state_delta` would be any changes that needed to be applied
to the client calculated state to correct it. However, since
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) is likely to replace the sync v2 API, we may as
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

There are no security concerns with this proposal, as it simply encodes the same information sent do clients in a
different way

## Unstable prefix

| Name | Stable prefix | Unstable prefix |
| - | - | - |
| Query param | `use_state_after` | `org.matrix.use_state_after` |
| Room response field | `state_after` | `org.matrix.state_after` |

## Dependencies

None
