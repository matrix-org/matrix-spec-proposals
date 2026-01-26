# MSC4300: Requesting and reporting event processing status

Matrix allows clients to exchange both built-in and custom events with other clients in rooms. There
is, however, no way for a client to understand if the events it sent were actually understood by
other clients or not. This is problematic as a compatibility mismatch means that the recipient user
might only be able to see a fallback representation of an event or, in the worst case, nothing at
all. At the same time, the sender is left wholly unaware of the recipient's experience.

These problems are aggravated when one or both of the participating clients are an automated system
(a.k.a. bot) which cannot easily issue or respond to generic "Did you see my message?" questions.

The present proposal partially addresses this problem by defining a generic scheme for clients to
request and receive an explicit processing status for events from other clients.

## Proposal

A new content block `m.request.status` is introduced to request a processing status from other
clients when sending events. It has the following properties in `content`:

- `from_device` (required, string): The sending device's device ID. Allows recipients to optionally
  submit their responses privately via to-device messages in the future.
- `to_device`(optional, string): The receiving device's device ID. Should be set when the sender
  wants to a adress a specific receiving device only.
- `lifetime` (integer): The duration in milliseconds during which the sender will consider responses
  to this request. Prevents meaningless delayed responses when new or previously disconnected
  devices encounter requests on older events.

Clients MAY add `m.request.status` as a top-level property in `content` on any event they send.

``` json5
{
  "type": "m.pizza",
  "event_id": "$1",
  "content": {
    "m.request.status": {
      "from_device": "RJYKSTBOIE",
      "to_device": "EIOBTSKYJR", // optional the receiving device
      "lifetime": 90000, // 90s
    },
    // properties specific to m.pizza
  }
}
```

Clients that receive events containing `m.request.status` content blocks where `to_device` is either
missing or identical to their own device ID, MAY respond to them with a new room event type
`m.response.status`. The latter contains an `m.reference` relation pointing to the original event as
well as an `m.response.status` content block with the following properties:

- `from_device` (required, string): The sending device's device ID. Helps clients identify the
  remote echo of their own responses.
- `status` (required, string, one of `success`, `error`): Whether the sending device has understood
  and successfully processed the event.
- `messages` (array): An optional array of messages to help recipients understand the `status`.
  - `type`: (required, string, one of `info`, `warning`, `error`): The message category.
  - `m.text`: (required, object): The message in one or more textual representations as per
    [MSC1767].

The event `content` MAY contain further properties based on the type of the event that is being
responded to.

``` json5
{
  "type": "m.response.status",
  "content": {
    "m.response.status": {
      "from_device": "EIOBTSKYJR",
      "status": "error",
      "messages": [{
        "type": "error",
        "m.text": [{ "body": "Unknown event type m.pizza" }]
      }]
    },
    "m.relates_to": {
      "event_id": "$1",
      "rel_type": "m.reference",
    },
    // optional properties specific to m.pizza
  }
}
```

Clients can check whether a request has expired using `lifetime`, `origin_server_ts` and their local
clock. Once a request has expired, clients SHOULD refrain from sending `m.response` events
themselves and ignore any new `m.response` events received from other clients.

## Potential issues

The mechanism introduced above doesn't enable clients to determine if other clients are able to
understand an event without actually sending it. [MSC4301] builds upon the present proposal and
introduces event capability queries to achieve this.

This proposal doesn't strictly define what constitutes successful processing of an event. At a
minimum, the meaning of success will depend on the type of event sent and the receiving client. An
archival bot, for instance, may have to decrypt and export an event to consider it processed
successfully. An instant messaging client for end users, on the other hand, might have to render an
event in a way that allows the user to interact with it. The kind of rendering needed will be
specific to the type of event in this case.

It is expected that the mechanism introduced in this proposal will be used as a basis for more
specialised features that clearly define the semantics of success. Therefore, this aspect is
consciously left unspecified here.

## Alternatives

Requests for processing statuses could be sent separately from the event being processed, for
instance, via to-device messages. This, however, introduces complexity because now both messages
have to be received and decrypted before responses can be sent. It is not clear what benefits, if
any, this alternative would have over the solution proposed in the present proposal.

Instead of sending processing statuses per event, clients could statically advertise the types of
events that they are able to understand, for instance, via profiles or state events in a room. This
would allow senders to look up recipient capabilities ahead of time but would not allow recipients
to communicate back detailed information about their processing status of individual events. As a
result, the two mechanisms are not necessarily competing and could also play together.

Delivery receipts as proposed in [MSC4089] are a partial alternative to this proposal. These
receipts only convey receipt and decryption status but not whether the decrypted event was actually
understood and processed successfully. Additionally, delivery receipts don't cover the case where an
event was received but failed to be processed. Lastly, receipts in their current form also don't
support including additional encrypted information about the processing result.

## Security considerations

Communicating the processing status via room events leaks metadata by revealing client capabilities
to all room participants. This can be mitigated by transporting the status via to-device messages
instead. A future proposal may generalise the mechanism introduced here accordingly. Until then,
clients are not required to respond to status requests under this proposal and MAY simply ignore
them.

Contrary to the above, persisting processing status responses in timeline events can be necessary in
scenarios that require auditability.

## Unstable prefix

While this MSC is not considered stable, `m.request.status` and `m.response.status` should be
referred to as `de.gematik.msc4300.request.status` and `de.gematik.msc4300.response.status`,
respectively.

## Dependencies

None.

  [MSC1767]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767
  [MSC4301]: https://github.com/matrix-org/matrix-spec-proposals/pull/4301
  [MSC4089]: https://github.com/matrix-org/matrix-spec-proposals/pull/4089
