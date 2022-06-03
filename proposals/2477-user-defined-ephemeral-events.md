# MSC2476: User-defined ephemeral events in rooms

Matrix currently handles the transfer of data in the form of Persistent- as well as Ephemeral Data
Units, both of which follow the same general design in the way they're encoded and transferred over
both the Client-Server and Server-Server API.

Currently, users are only able to provide their own event types and data in the case of
persistent data, in the form of state events as well as messages / timeline events.  
The sending of ephemeral data by clients - on the other hand - is currently limited to only typing
notifications, event receipts, and presence updates. Which greatly limits the potential usefulness
of ephemeral events as a general mechanism for transferring short-lived data.

Therefore, this proposal suggest extending both the Client-Server and Server-Server APIs to allow
users to transfer arbitrary ephemeral data types and content into rooms in which they have the right
to do so.


## Proposal

The proposed change is to add support for users to provide their own data types and content, in a
similar manner to the already existing support for users to send their own types of persistent data.

Note though that this proposal does not include any support for sending user-defined ephemeral
events which are not explicitly bound to rooms, like the global `m.presence` event.

Examples of how this feature could be used are; as regular status updates to a user-requested
long-lived task, which a bot might have started for a received event. Or perhaps as a GPS live-location
feature, where participating clients would regularly post their current location relative to a
persistent geo-URI event. Perhaps for organizing meetups, or for viewing active tracking of the 
locations of vehicles in an autonomous fleet - maybe along with peristent messages posted at a lesser
rate for timeline generation.

The example that will be used througout this proposal is an ephemeral data object that's tracking
the current status of a user-requested 3D print, with some basic printer- and print-status
information being sent every few seconds to a control room, including a reference to the event that
the status is referring to - which the client could use to render a progress bar or some other graphic
with.

### Addition of an ephemeral event sending endpoint to the Client-Server API

The addition to the CS API is the endpoint
`PUT /_matrix/client/v1/rooms/{roomId}/ephemeral/{eventType}/{txnId}`, which would act in an almost
identical manner to the [`PUT /_matrix/client/v3/rooms/{roomId}/send/{eventType}/{txnId}`][PUT Room Event]
endpoint that is already present.  
An example of how an update might be posted using the new endpoint is provided as;

```
PUT /_matrix/client/v1/rooms/%21636q39766251%3Aexample.com/ephemeral/com.example.3dprint/19914 HTTP/1.1
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

As EDUs do not have event IDs, this is an empty JSON object

```json
{}
```

Status code 400:

The user tried to send a `m.*` EDU, instead of using the type-specific endpoint

```json
{
  "errcode": "M_UNKNOWN",
  "error": "Cannot send built-in ephemeral types with this endpoint"
}
```

Status code 403:

Power levels forbid the user from sending the attempted EDU 

```json
{
  "errcode": "M_FORBIDDEN",
  "error": "You do not have permission to send the EDU"
}
```

User is not in the room

```json
{
  "errcode": "M_FORBIDDEN",
  "error": "You are not a member of the room"
}
```

Status code 429:

The request was rate-limited

```json
{
  "errcode": "M_LIMIT_EXCEEDED",
  "error": "Too many requests",
  "retry_after_ms": 2000
}
```

### Extension of power levels to handle user-defined ephemeral events

As it would be possible for the user-defined events to be used to flood a room with invisible
traffic by malicious users - increasing the bandwidth usage for all connected servers, this proposal
also suggests extending the power levels to handle ephemeral types as well.

In any room version implementing this MSC, the auth rules concerning ephemeral events in the
`m.room.power_levels` state event are;

- `ephemeral` (`{string: integer}`) - A mapping of EDU types to the power-level required to send them
- `ephemeral_default` (`integer`) - The default power-level required to send any EDU not listed in
the above mapping

These new keys are expected to function in an identical manner to the already existing `events` and
`events_default` keys in the `m.room.power_levels` state event.  
The fallback value for `ephemeral_default` - if missing - should be 50, while the fallback value for
the `ephemeral` dictionary should be `{}` - or an empty mapping. Which would imply that _any_ ephemeral
event type should require a power level of at least `ephemeral_default` (or 50) to send.

With this change it is therefore recommended for servers to include at least the following `ephemeral`
configuration for all newly created rooms - of any room version implementing this MSC, to allow for
clients continued sending of the default ephemeral events in Matrix;

```json
{
  "m.receipt": 0,
  "m.typing": 0
}
```

An example of what a full `m.room.power_levels` object could look like with this MSC;

```json
{
  "type": "m.room.power_levels",
  "sender": "@alice:example.com",
  "content": {
    "users": {
      "@alice:example.com": 100
    },
    "users_default": 0,
    "events": {
      "m.room.name": 50,
      "m.room.power_levels": 100,
      "m.room.history_visibility": 100,
      "m.room.canonical_alias": 50,
      "m.room.avatar": 50,
      "m.room.tombstone": 100,
      "m.room.server_acl": 100,
      "m.room.encryption": 100
    },
    "events_default": 0,
    "ephemeral": {
      "m.receipt": 0,
      "m.typing": 0
    },
    "ephemeral_default": 50,
    "state_default": 50,
    "ban": 50,
    "kick": 50,
    "redact": 50,
    "invite": 0
  },
  "state_key": "",
  "origin_server_ts": 1627993163991,
  "unsigned": {
    "age": 10418356643
  },
  "event_id": "$za6Ba5Rosa6pahn8the7phairei3eiM3aithoh4aev0moh4siephec6laeraiyaF",
  "room_id": "!lioc7Ree1eekea4u:example.com"
}

```

### Extension of the room-specific ephemeral data received in /sync responses

Because the user-defined ephemeral events can't be aggregated and massaged by the homeserver in a simple
manner, this MSC instead requires adding a few more fields to the room-specific ephemeral events as
they are encoded in a sync response. The additions in question are;

- `sender` (`string`) - The fully qualified ID of the user that sent the EDU
- `origin_server_ts` (`integer`) - The timestamp in milliseconds on the originating homeserver when
this event was sent

To reduce the scope of changes required by this proposal, it is suggested to allow the original `m.*`
events to skip these keys where no value could be easily assigned to them. E.g. typing notices, read
receipts.

```json5
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
                "printer": 10
              },
              "type": "com.example.3dprint_request",
              "event_id": "$4CvDieFIFAzSYaykmBObZ2iUhSa5XNEUnC-GQfLl2yc",
              "sender": "@alice:matrix.org",
              "origin_server_ts": 1432735824653,
              "unsigned": {
                "age": 5558
              }
            },
            {
              "content": {
                "body": "Print of fan_shroud_v5.gcode started on printer 10, ETA is 2h. Stream is available at https://example.com/printers/10.m3u8",
                "com.example.3dprint": {
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
              "event_id": "$E2RPcyuMUiXyDkQ02ASEbFxcJ4wFNrt5JVgov0wrqWo"
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
              "type": "m.typing"
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

### Delivery guarantees

The current ephemeral event system in Matrix is built on a sort-of guaranteed delivery - albeit with
mutation/consolidation - of the events. This might not be desirable with custom ephemeral events, as
they could contain volumes of data that's not as easy to keep around for a guaranteed delivery.

Therefore I suggest that servers are only required to provide best-effort delivery, with the exact
method in how they propagate EDUs - and store them - left up to implementation.  
(Perhaps keeping a max-size ring buffer per room - that will thus remove old data when necessary.
Or maybe only storing per active sync token, per user, per device.)

As the messages in question are ephemeral, I think the only guarantee that should be required is that
all users that are online when the message is sent will receive it. Anything above that should be
commended, but not required.

### Extension of the Server-Server spec

As the server-server protocol is currently only designed for transferring the well-defined EDUs that
exist as part of the Matrix communication protocol, this proposal requires some additional fields to
be added to the EDU schema in order to let them transmit the user-specified data untouched - while
still adding source information that is important for the receiving clients.

The fields to add to the EDU schema are;

- `room_id` (`string`) - The fully qualified ID of the room the event was sent in
- `sender` (`string`) - The fully qualified ID of the user that sent the event
- `origin` (`string`) - The `server_name` of the homeserver that created this event
- `origin_server_ts` (`integer`) - Timestamp in milliseconds on origin homeserver when this event
was created

A user-defined ephemeral event might then look like this when federated;

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

To reduce the scope of the changes required by this proposal, the suggestion is to allow the original
`m.*` events to skip these keys where no value can be easily assigned to them. E.g. aggregated typing
notices, receipt lists.


## Potential issues

Because this change completely redefines how ephemeral events are used, it is likely to be expected
that some servers and clients could struggle to handle the new types of data that this proposal
would create. But as the protocol is defined with an extensible transport - JSON, it should not be
difficult - if even necessary - for clients or servers to be modified to support the changes.

Additionally, as ephemeral data is never encoded into room state there's not as many tools for
admins to handle abuse that occur through the use of the feature.  
The proposal's suggested changes to power levels - and limitation of what event types can be sent -
should mitigate the potential of abuse from the feature though, as long as admins don't allow any
user-defined ephemeral types to be sent by regular users.

This change could impact the - currently in review - [MSC2409], necessitating some kind of filter for
what event types would be transferred to appservices. [MSC2487] suggests a possible solution for this
potential problem.


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
their specced forms. Additionally, it might be hard for the server to assign a correct sender and
timestamp to events if they are aggregated from multiple sources - e.g. typing notices and read
receipt lists.

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


## Unstable Prefix

During implementation, the URL for submitting user-defined EDUs should be
`PUT /_matrix/client/unstable/org.matrix.msc2477/rooms/{roomId}/ephemeral/{eventType}/{txnId}`, and
should only be allowed for rooms versioned as `org.matrix.msc2477`. (Using room version 9 as the base)

Similarly, the keys `ephemeral` and `ephemeral_default` in `m.room.power_levels` should be prefixed
with `org.matrix.msc2477.` until this MSC is incorporated into a stable room version.


[PUT Room Event]: https://spec.matrix.org/v1.2/client-server-api/#put_matrixclientv3roomsroomidsendeventtypetxnid
[MSC1763]: https://github.com/matrix-org/matrix-doc/pull/1763
[MSC2228]: https://github.com/matrix-org/matrix-doc/pull/2228
[MSC2409]: https://github.com/matrix-org/matrix-doc/pull/2409
[MSC2487]: https://github.com/matrix-org/matrix-doc/pull/2487
