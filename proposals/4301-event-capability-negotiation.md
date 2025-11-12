# MSC4301: Event capability negotiation between clients

Matrix allows clients to exchange both built-in and custom events with other clients in rooms. There
is, however, no way for a client to tell what types of events the other clients in a room are able
to understand. This is problematic as a compatibility mismatch means that the recipient user might
only be able to see a fallback representation of an event or, in the worst case, nothing at all. At
the same time, the sender is left wholly unaware of the recipient's experience.

A glaring example of this occurs when Matrix is used to exchange [FHIR] resources, e.g. via
[MSC4302]. These resources can be subject to complex customizations via so called *profiles* which
affect rendering and processing logic. For a client that aims to send FHIR resources into a room, it
is, therefore, crucial to know whether or not the recipients in the room can actually work with the
specific FHIR profiles it is going to use. The usual Matrix approach of designing new events to
include backwards-compatible fallbacks is not feasible in this case. The only apparent fallback is
transmitting FHIR resources as generic JSON or XML files. Such files are not (easily) human-readable
and will appear mostly impractical to recipients, however.

[MSC4300] partially addresses this problem by enabling clients to communicate the result of
processing a specific event back to the sender. This lets senders determine after the fact whether
the events they have sent were understood by other clients or not.

This proposal goes a step further and introduces a scheme for clients to query whether other clients
understand an event *ahead* of actually sending it. This allows clients to efficiently negotiate
compatible event types resulting in the best possible experience for all participants.

## Proposal

A new room event type `m.request.event_capability` is introduced to request supported event types
from other clients. These capability requests may be time-sensitive and, in the best case, result in
a capability response from each participating device. For this reason, the processing status request
/ response mechanism from [MSC4300] is reused. `m.request.event_capability` has the following
properties in `content`:

- `m.request.status` (object, required): Generic information about the request as per [MSC4300].
- `m.request.event_capability` (object, required): Information about the event capability request.
  - `events` (array, required): A list of objects containing details about the events being queried.
    - `type` (string, required): The type of the event.
    - `content` (array): An optional list of objects describing additional requirements for
      properties inside the `content` of the event.
      - `key` (string, required): The dot-separated path of the property (analogous to `key` in
        `event_match` [push rule conditions]).
      - `value` (string, required): The exact value of the property.

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
    // I'd like to send any of these events into this room.
    // Which of these do you understand?
    "m.request.event_capability": {
      "events": [
        // How about m.fhir containing advanced rendering SDC questionnaires v4?
        {
          "type": "m.fhir",
          "content": [{
            "key": "m\.fhir\.structure_definition.url",
            "value": "http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-render"
          }, {
            "key": "m\.fhir\.structure_definition.version",
            "value": "4.0.0"
          }]
        },
        // Or if you don't know v4, maybe you support v3?
        {
          "type": "m.fhir",
          "content": [{
            "key": "m\.fhir\.structure_definition.url",
            "value": "http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-render"
          }, {
            "key": "m\.fhir\.structure_definition.version",
            "value": "3.0.0"
          }]
        },
        // Or failing that, do you at least understand base SDC questionnaires v4?
        {
          "type": "m.fhir",
          "content": [{
            "key": "m\.fhir\.structure_definition.url",
            "value": "http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire"
          }, {
            "key": "m\.fhir\.structure_definition.version",
            "value": "4.0.0"
          }]
        }
      ]
    }
  }
}
```

The requirements expressed through `type` and the elements of `content` are to be combined using
logical AND.

Recipient clients MAY respond to `m.request.event_capability` within its lifetime with the
`m.response.status` event from [MSC4300] and the following additional properties in `content`:

- `m.response.event_capability` (object, required): Information about the event capability response
  - `events` (array, required): The subset of events from `m.request.event_capability` that the
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
        "m.text": [{ "body": "Unknown structure definition http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire-render" }]
      }]
    },
    "m.relates_to": {
      "event_id": "$1",
      "rel_type": "m.reference",
    },
    // These are the events I understand.
    "m.response.event_capability": {
      "events": [
        // I can only do m.fhir with base SDC questionnaires, sorry!
        {
          "type": "m.fhir",
          "content": [{
            "key": "m\.fhir\.structure_definition.url",
            "value": "http://hl7.org/fhir/uv/sdc/StructureDefinition/sdc-questionnaire"
          }, {
            "key": "m\.fhir\.structure_definition.version",
            "value": "4.0.0"
          }]
        }
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

Rather than allowing specific requirements on `content` fields, queries could be limited to only
event types. This would noticeably simplify the scheme. However, particularly in the case of FHIR,
it seems impractical to define event types for every possible resource or profile in their various
versions.

## Security considerations

The concerns and remedies around leaking metadata from [MSC4300] apply to this proposal as well.

## Unstable prefix

While this MSC is not considered stable, `m.request.event_capability` (the event type) and
`m.response.event_capability` should be referred to as `de.gematik.msc4301.request.event_capability`
and `de.gematik.msc4301.response.event_capability`, respectively. Properties inherited from
[MSC4300] have their own prefixing requirements.

## Dependencies

This proposal builds on [MSC4300] which at the time of writing has not yet been accepted into the
spec. This proposal does not depend on [MSC4302] but is intended to work in concert with it.

  [FHIR]: https://www.hl7.org/fhir/
  [MSC4302]: https://github.com/matrix-org/matrix-spec-proposals/pull/4302
  [MSC4300]: https://github.com/matrix-org/matrix-spec-proposals/pull/4300
  [push rule conditions]: https://spec.matrix.org/v1.16/client-server-api/#conditions-1
