# MSC4401: Publishing client capabilities via profiles

Matrix allows clients to exchange both built-in and custom events with other clients in rooms. There
is, however, no way for a client to determine what types of events other clients are able to
understand. For human users, this can usually be addressed to a sufficient extent by including
fallback representations in the event, for instance via [MSC1767]. Fallbacks don't work well when
communicating with bots, however. These usually expect to receive data in a defined format and are
often unable to fall back to alternative representations such as free text.

As an example, imagine a bot operated by a health insurance that is designated to process settlement
statements from caregivers. To process such statements automatically, the bot needs them to be sent
in a predefined format, for instance, by using a custom Matrix event. The caregiver obviously needs
to know about this format beforehand so that they can transmit their statements correctly. While the
bot could simply communicate the expected format via its documentation or through help messages, it
would be much more useful if the bot could declare its format(s) in a machine-readable way. This
would allow clients to implement auxiliary features such as automatically converting a data source
to the correct format. Additionally, this would also facilitate data exchange in scenarios where
both communication partners are bots.

This proposal addresses this problem by defining a way in which clients can advertise their support
for events via profiles.

## Proposal

A new set of profile keys `m.client_capability.{DEVICE_ID}` is introduced. The value of these keys
is an object with the following properties:

- `events` (array, required): A list of objects containing details about the events this device
  supports.
  - `type` (string, required): The type of the event.
  - `content` (array): An optional list of objects describing additional requirements for properties
    inside the `content` of the event.
    - `key` (string, required): The dot-separated path of the property (analogous to `key` in
      `event_match` [push rule conditions]).
    - `value` (string, required): The exact value of the property.

As an example, here is a profile that advertises support for processing medication statements using
the FHIR event from [MSC4302] on a device `ABCDEFG`.

``` json5
{
  "m.client_capability.ABCDEFG": {
    "events": [
      {
        "type": "de.gematik.msc4302.fhir",
        "content": [{
          "key": "m\.fhir.structure_definition.url",
          "value": "http://hl7.org/fhir/StructureDefinition/MedicationStatement"
        }, {
          "key": "m\.fhir.structure_definition.version",
          "value": "4.0.1"
        }]
      }
    ]
  }
}
```

To avoid stale capabilities filling up the profile, servers SHOULD remove a device's
`m.client_capability.{DEVICE_ID}` key when the device is logged out.

## Potential issues

Profiles are currently limited to 64 KiB in size which may be reached through excessive usage of
this feature.

## Alternatives

[MSC4301] defines online capability queries using in-room messages. These use a similar data format
but introduce the problem that both parties need to be online at the same time.

Client capabilities could be stored separately from profiles on the server. This would require new
APIs for reading and writing the data, access rules, etc. though.

## Security considerations

Exposing client capabilities via profiles leaks metadata. Servers that are worried about users
misusing this feature can limit profile queries to users that have rooms in common or reside in
public rooms. Users that don't wish to expose their clients' capabilities, can simply *not* put them
into their profiles.

## Unstable prefix

While this MSC is not considered stable, `m.client_capability.*` should be referred to as
`de.gematik.msc4401.client_capability.*`.

## Dependencies

None.

  [MSC1767]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767
  [push rule conditions]: https://spec.matrix.org/v1.16/client-server-api/#conditions-1
  [MSC4302]: https://github.com/matrix-org/matrix-spec-proposals/pull/4302
  [MSC4301]: https://github.com/matrix-org/matrix-spec-proposals/pull/4301
