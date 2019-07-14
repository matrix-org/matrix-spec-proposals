# MSC2174: move the `redacts` property to `content`

[`m.room.redaction`](https://matrix.org/docs/spec/client_server/r0.5.0#m-room-redaction)
events currently have an *event-level* property `redacts` which gives the event
ID of the event being redacted.

The presence of this field at the event level, rather than under the `content`
key,  is anomalous. This MSC proposes that, in a future room version, the
`redacts` property be moved under the `content` key.
