# MSC2174: move the `redacts` property to `content`

[`m.room.redaction`](https://matrix.org/docs/spec/client_server/r0.5.0#m-room-redaction)
events currently have an *event-level* property `redacts` which gives the event
ID of the event being redacted.

The presence of this field at the event level, rather than under the `content`
key,  is anomalous. This MSC proposes that, in a future room version, the
`redacts` property be moved under the `content` key.

For backwards-compatibility with *older* clients, servers should add a `redacts`
property to the top level of `m.room.redaction` events in *newer* room versions
when serving such events over the Client-Server API.

For improved compatibility with *newer* clients, servers should add a `redacts`
property to the `content` of `m.room.redaction` events in *older* room versions
when serving such events over the Client-Server API.
