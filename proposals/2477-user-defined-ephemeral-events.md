# MSC2476: User-defined ephemeral events in rooms

Matrix currently handles the transfer of data in the form of Persistent- as well as Ephemeral Data
Units, both of which follow the same general design in the way they're encoded and transferred over
both the Client-Server and Server-Server API.

Currently only users are only able to provide their own event types and data in the case of
persistent data, in the form of state events as well as messages / timeline events.  
The sending of ephemeral data by clients - on the other hand - is currently limited to only typing
notifications, event receipts, read markers, and presence updates. Which greatly limits the
potential usefulness of ephemeral events as a general mechanism for transferring short-lived data.

Therefore, this proposal suggest extending both the Client-Server and Server-Server APIs to allow
users to transfer arbitrary ephemeral data types and content into rooms in which they have the right
to do so.


## Proposal

The proposed change is to add support for users to provide their own data types and content, in a
similar manner to the already existing support for users to send their own types of persistent data.

Note though that this proposal does not include any support for sending user-defined ephemeral
events which are not explicitly bound to rooms, like the global `m.presence` event.

Examples of how this feature could be used are; as regular status updates to a user-requested
long-lived task, which a bot might has started for a received event. Or pehaps as a GPS live-location
feature, where participating client would regularly post their current location relative to a
persistent geo-URI event. Perhaps for organizing meetups, or for viewing active tracking of the 
locations of vehicles in an autonomous fleet - along with peristent messages posted at a lesser
rate for a timeline generation.

The example that will be used througout this proposal is an ephemeral data object that's tracking
the current status of a user-requested 3D print, with some basic printer- and print-status
information being sent every few seconds to a control room, including a reference to the event that
the status is referring to - which the client could use to render a progress bar or other graphic
with.

### Addition of an ephemeral event sending endpoint to the Client-Server API

The suggested addition to the CS API is the endpoint
`PUT /_matrix/client/r0/rooms/{roomId}/ephemeral/{eventType}/{txnId}`, which would act in an almost
identical manner to the event sending endpoint that is already present.  
An example of how an update might be posted using the new endpoint;

```
PUT /_matrix/client/r0/rooms/%21636q39766251%3Aexample.com/ephemeral/com.example.3dprint/19914 HTTP/1.1
Content-Type: application/json

{
  "print_event_id": "$E2RPcyuMUiXyDkQ02ASEbFxcJ4wFNrt5JVgov0wrqWo",
  "printer_id": 10,
  "status": {
    "hotend_c": 181.4,
    "bed_c": 62.5,
    "position": [54, 275, 87.2]
  },
  "time": {
    "elapsed": 4324,
    "estimated": 7439
  }
}
```

Example of a response;

Status code 200:

```json
{}
```

### Extension of power levels to handle user-defined ephemeral events

As it would be possible for the user-defined events to be used to flood a room with invisible
traffic by malicious users - increasing the bandwidth usage for all connected servers, this proposal
also suggests extending the power levels to handle ephemeral types as well.

The suggested keys to add to the `m.room.power_levels` events are as follows;

- `ephemeral`, of type `{string: integer}`
- `ephemeral_default`, of type `integer`

These new keys are suggested to function in an identical manner to the already existing `events` and
`events_default` keys, with the suggested default - and fallback - value for `ephemeral_default`
being 50, while the suggested default - and fallback - values for `ephemeral` would be;

```json
{
  "m.fully_read": 0,
  "m.receipt": 0,
  "m.typing": 0
}
```

**NB**;  
To reduce the complexity of the change, this proposal suggests to - for the time being - only limit
the user-defined types by these power levels changes. The default values for `m.*` specified here in
`ephemeral_defaults` would then only be expected to be informational in purpose.

### Extension of the ephemeral data received in /sync responses

Because the user-defined ephemeral events can't be aggregated and massaged by Synapse in a simple
manner, this then suggests instead adding a few more (**optional** but suggested for `m.*`,
**required** otherwise) fields to the ephemeral events as they are encoded in a sync response. The
suggested additions are;  

- `sender`, of type `string`
- `origin_server_ts`, of type `integer`

To reduce the risk of breaking existing clients, as well as reducing the scope of change required by
this proposal, the suggestion is to leave the original `m.*` events unaltered for now - therefore
the use of fields that can be both optional *as well as* required depending on the ephemeral type.

```json
{
  "next_batch": "...",
  // ...
  "rooms": {
    "join": {
      "!636q39766251:example.com": {
        // ...
        "timeline": {
          "events": [
            {
              "content": {
                "gcode": "mxc://example.com/GEnfasiifADESSAF",
                "printer": 10,
              },
              "type": "com.example.3dprint_request",
              "event_id": "$4CvDieFIFAzSYaykmBObZ2iUhSa5XNEUnC-GQfLl2yc",
              "room_id": "!636q39766251:example.com",
              "sender": "@alice:matrix.org",
              "origin_server_ts": 1432735824653,
              "unsigned": {
                "age": 5558
              }
            },
            {
              "content": {
                "body": "Print of fan_shroud_v5.gcode started on printer 10, ETA is 2h. Stream is available at https://example.com/printers/10.m3u8",
                "print": {
                  "gcode": "mxc://example.com/GEnfasiifADESSAF",
                  "printer": 10,
                  "video": "https://example.com/printers/10.m3u",
                  "eta": 7253
                },
                "m.relates_to": {
                  "m.in_reply_to": {
                    "event_id": "$4CvDieFIFAzSYaykmBObZ2iUhSa5XNEUnC-GQfLl2yc"
                  }
                },
                "msgtype": "m.text"
              },
              "origin_server_ts": 1432735825887,
              "sender": "@printbot:example.com",
              "type": "m.room.message",
              "unsigned": {
                "age": 4324
              },
              "event_id": "$E2RPcyuMUiXyDkQ02ASEbFxcJ4wFNrt5JVgov0wrqWo",
              "room_id": ""
            }
          ]
        },
        "ephemeral": {
          "events": [
            {
              "content": {
                "user_ids": [
                  "@alice:matrix.org",
                  "@bob:example.com"
                ]
              },
              "type": "m.typing",
              "room_id": "!636q39766251:example.com"
            },
            {
              "content": {
                "print_event_id": "$E2RPcyuMUiXyDkQ02ASEbFxcJ4wFNrt5JVgov0wrqWo",
                "printer_id": 10,
                "status": {
                  "hotend_c": 181.4,
                  "bed_c": 62.5,
                  "position": [54, 275, 87.2]
                },
                "time": {
                  "elapsed": 4324,
                  "estimated": 7440
                }
              },
              "type": "com.example.3dprint",
              "room_id": "!636q39766251:example.com",
              "sender": "@printbot:example.com",
              "origin_server_ts": 1432735830211
            }
          ]
        }
      }
    }
  }
}
```

### Extension of the Server-Server spec

As the server-server protocol is currently only designed for transferring the well-defined EDUs that
exist as part of the Matrix communication protocol, this proposal suggests adding additional fields
to the EDU schema in order to let them transmit the user-specified data untouched - while still
adding source information that is important for the receiving clients.

The suggested (**optional** but suggested for `m.*`, **required** otherwise) fields to add to the
EDU schema are;

- `room_id`, of type `string`
- `sender`, of type `string`
- `origin`, of type `string`
- `origin_server_ts`, of type `integer`

A user-defined ephemeral event could then look like this when federated;

```json
{
  "content": {
    "print_event_id": "$E2RPcyuMUiXyDkQ02ASEbFxcJ4wFNrt5JVgov0wrqWo",
    "printer_id": "10",
    "status": {
      "hotend_c": 181.4,
      "bed_c": 62.5,
      "position": [54, 275, 87.2]
    },
    "time": {
      "elapsed": 4324,
      "estimated": 7440
    }
  },
  "room_id": "!636q39766251:example.com",
  "sender": "@printbot:example.com",
  "origin": "example.com",
  "origin_server_ts": 1432735830211,
  "edu_type": "com.example.3dprint"
}
```


## Potential issues

Because this change completely redefines how ephemeral events are used, it is likely to be expected
that some servers and clients could struggle to handle the new types of data that this proposal
would create. But as the protocol is defined with an extensible transport - JSON, it should not be
difficult - if even necessary - for clients or servers to be modified to support the changes.

Additionally, as ephemeral data is never encoded into room state there's not as many tools for
admins to handle abuse that occur through the use of the feature.  
The proposals suggested changes to power levels - and limitation of what event types can be sent -
should mitigate the potential of abuse from the feature though, as long as admins don't allow any
user-defined ephemeral types to be sent by regular users.

This change could impact the - currently in review - [MSC2409], necessitating some kind of filter for
what event types would be transferred to appservices.


## Alternatives

The ephemeral state that this change would allow to transfer could as easily be sent using
self-destructing messages with the help of [MSC1763] or [MSC2228], which would result in a similar
experience to the end user.  
Unfortunately using persistent events in such a manner would add a lot of unnecessary data to the
room DAG, while also increasing both the computational work and the database pressure through the
repeated and rapid insertions and redactions that it would result in.

### Client-Server protocol changes

The additions to ephemeral objects could be expanded to also apply to the normal `m.*` types as well,
which would reduce the complexity of the spec as there would be no distinction between the built-in
Matrix types as well as the user-defined types.  
This could cause some clients to break though, if they expect the well-defined objects to keep to
their specced forms.

### Server-Server protocol changes

Instead of adding potentially optional keys to the EDU schema, the entire object could instead be
embedded into the content key, using an EDU type key that denotes it as an user-defined type.  
This would mean a smaller change to the server-server communication, while still allowing a server
module to filter or track events based on their types or origins.

```json
{
  "content": {
    "room_id": "!636q39766251:example.com",
    "sender": "@printbot:example.com",
    "origin": "example.com",
    "origin_server_ts": 1432735830211,
    "type": "com.example.3dprint",
    "content": {
      "print_event_id": "$E2RPcyuMUiXyDkQ02ASEbFxcJ4wFNrt5JVgov0wrqWo",
      "printer_id": "10",
      "status": {
        "hotend_c": 181.4,
        "bed_c": 62.5,
        "position": [54, 275, 87.2]
      },
      "time": {
        "elapsed": 4324,
        "estimated": 7440
      }
    }
  },
  "edu_type": "m.user_defined"
}
```

Possibly, the additional requirements for user-defined types could instead also be expanded to cover
the regular Matrix types as well, which would remove the need for optional fields - but could in
return impact the federation between servers, if they're built to only handle the exact requirements
of the spec.

[MSC1763]: https://github.com/matrix-org/matrix-doc/blob/matthew/msc1763/proposals/1763-configurable-retention-periods.md
[MSC2228]: https://github.com/matrix-org/matrix-doc/tree/matthew/msc2228/proposals/2228-self-destructing-events.md
[MSC2409]: https://github.com/Sorunome/matrix-doc/blob/soru%2Bhs/appservice-edus/proposals/2409-appservice-edus.md
