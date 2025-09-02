# MSC4301: Event capability negotiation between clients

Matrix allows clients to exchange both built-in and custom events with other clients in rooms. There
is, however, no way for a client to understand what types of events the other clients in a room are
able to understand. This is problematic as a compatibility mismatch means that the recipient user
might only be able to see a fallback representation of an event or, in the worst case, nothing at
all. At the same time, the sender is left wholly unaware of the recipient's experience.

[MSC4300] partially addresses this problem by enabling clients to communicate the result of
processing a specific event back to the sender. This lets senders determine after the fact whether
the events they have sent were understood by other clients or not.

The present proposal goes a step further and introduces a scheme for clients to query whether other
clients understand an event type *ahead* of actually sending that event. This allows clients to
efficiently negotiate compatible event types resulting in the best possible experience for all
participants.

## Proposal

A new room event type `m.request.event_capability` is introduced to request supported event types
from other clients. These capability requests may be time-sensitive and, in the best case, result in
a capability response from each participating device. For this reason, the processing status request
/ response mechanism from [MSC4300] is reused. `m.request.event_capability` has the following
properties in `content`:

- `m.request.status` (object, required): Generic information about the request as per [MSC4300].
- `m.request.event_capability` (object, required): Information about the event capability request.
  - `types` (array, required): A list of event types for which the sender wishes to request support.

``` json5
{
  "type": "m.request.event_capability",
  "event_id": "$1",
  "content": {
    // Properties from MSC4300
    "m.request.status": {
      "from_device": "RJYKSTBOIE",
      "lifetime": 90_000, // 90s
    },
    // I'd like to send any of these event types into this room.
    // Which of these do you understand?
    "m.request.event_capability": {
      "types": [
        "m.pizza.margherita",
        "m.pizza.salami",
        "m.pizza.hawaii"
      ]
    }
  }
}
```

Recipient clients MAY respond to `m.request.event_capability` within its lifetime with the
`m.response.status` event from [MSC4300] and the following additional properties in `content`:

- `m.response.event_capability` (object, required): Information about the event capability response
  - `types` (array, required): The subset of event types from `m.request.event_capability` that the
    sending device is able to understand.

``` json5
{
  "type": "m.response.status",
  "content": {
    // Properties from MSC4300
    "m.response.status": {
      "from_device": "EIOBTSKYJR",
      "status": "success",
      "messages": [{
        "type": "info",
        "m.text": [{ "body": "Refusing to recognise Hawaii as a Pizza style!" }]
      }]
    },
    "m.relates_to": {
      "event_id": "$1",
      "rel_type": "m.reference",
    },
    // These are the event types I understand.
    "m.response.event_capability": {
      "types": [
        "m.pizza.margherita",
        "m.pizza.salami",
      ]
    }
  }
}
```

## Potential issues

None.

## Alternatives

Instead of querying event capabilities ad-hoc, clients could statically advertise the types of
events that they are able to understand, for instance, via profiles or state events in a room. This
would simplify looking up capabilities but comes with its own technical challenges such as scoping
profiles to devices and rooms or being able to send state events in a room.

## Security considerations

The concerns and remedies around leaking metadata from [MSC4300] apply to this proposal as well.

## Unstable prefix

While this MSC is not considered stable, `m.request.event_capability` (the event type) and
`m.response.event_capability` should be referred to as `de.gematik.msc4301.request.event_capability`
and `de.gematik.msc4301.response.event_capability`, respectively. Properties inherited from
[MSC4300] have their own prefixing requirements.

## Dependencies

This proposal builds on [MSC4300] which at the time of writing has not yet been accepted into the
spec.

  [MSC4300]: https://github.com/matrix-org/matrix-spec-proposals/pull/4300
