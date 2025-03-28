# MSC4196: MatrixRTC voice and video conferencing application `m.call`

## Proposal

We define a MatrixRTC application type of `m.call`.

### `m.rtc.member` state event

A valid `m.rtc.member` state event with application `m.call` has the following fields in addition to the fields defined in [MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143):

- `session` required object:
  - `application` required string: `m.call`
  - `call_id` required string: The call ID of the session. Use `""` for a room level call.
  - `scope` required string: The scope of the call. One of: `m.room`. More scopes may be added in the future.

For example:

```json5
// event type: "m.rtc.member"
// MSC3757 formatted state key: "@user:matrix.domain_xyzABCDEF10123"
{
  // standard fields from MSC4143:
  "member": {
    "id": "xyzABCDEF10123",
    "device_id": "DEVICEID",
    "user_id": "@user:matrix.domain"
  }
  "focus_active": { ...focus_1 },
  "foci_preferred": [
    { ...focus_1 },
  ],
  "session": {
    "application": "m.call",
    // additional fields for m.call:
    "call_id": "",
    "scope": "m.room"
  }
}
```

### Ringing with the `m.rtc.notify` room event

A valid `m.rtc.notify` event with application `m.call` has the following fields in addition to the fields defined in [MSC4075](https://github.com/matrix-org/matrix-spec-proposals/pull/4075):

- `session` required object: the contents of the `session` from the `m.rtc.member` event.

```json5
// event type: "m.rtc.notify"
{
  "content": {
    // standard fields from MSC4075:
    "application": "m.call",
    "m.mentions": {"user_ids": [], "room": true },
    "notify_type": "notification",
    "session": {
      "application": "m.call",
      // for application = "m.call":
      "call_id": ""
    }
  }
}
```

## Potential issues

## Alternatives

## Security considerations

## Unstable prefix

The `m.call` application type is already within unstable prefixed entries (e.g.
`org.matrix.msc3401.call.member`) and as such doesn't need its own unstable prefix.

## Dependencies

This MSC builds on [MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143) and [MSC4075](https://github.com/matrix-org/matrix-spec-proposals/pull/4075).
