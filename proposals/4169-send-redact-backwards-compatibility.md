# MSC4169: Backwards-compatible redaction sending using `/send`
[MSC2174] moved the `redacts` key from the top level to inside `content`. It
also defined forwards- and backwards-compatibility for receiving by defining
that servers will copy the key to both locations when serving events to clients.
The `/redact` endpoint is also forwards-compatible because it works in all room
versions. However, `/send` was not made backwards-compatible. This means that
clients can't switch to using `/send` unless they keep track of room versions.

## Proposal
The proposed solution is to have the server adjust the content of
`/send/m.room.redaction` calls based on the room version. To future-proof the
backwards compatibility for [MSC2244], conversion between arrays and strings is
also introduced.

Additionally, the `/redact` endpoint is deprecated, as there is no longer any
reason to use it.

[MSC2244]: https://github.com/matrix-org/matrix-spec-proposals/pull/2244

* When `/send` is called with a string value for `redacts` in pre-v11 room,
  versions the server will move the `redacts` field from the content (request
  body) to the top level of the event being formed.
* When `/send` is called with a string value for `redacts` in post-MSC2244 room
  versions, the server will replace the `redacts` field with an array containing
  the string value provided by the client.
* When `/send` is called with an array value for `redacts` in pre-MSC2244 room
  versions, the behavior depends on the number of items in the array:
  * if the array contains a single item, the server will replace the `redacts`
    field with the only item inside the array.
    * if the call is in a pre-v11 room, the field is also moved to the top
      level.
  * if the field contains multiple items, the server will return a standard
    error with `M_MASS_REDACTION_UNSUPPORTED` as the errcode and HTTP 400 as
    the status code.

## Potential issues

## Alternatives
### Client-side switching
Clients could remember room versions themselves and adjust the endpoint based
on that. This works fine for thick clients which cache data locally anyway, but
does not work for things like bots which have minimal local state.

### Just use `/redact`
`/redact` works fine for all room versions. We could discourage using `/send`
for redactions and prefer `/redact` instead. Extending `/redact` to allow an
array may also feel less weird than the server modifying content in `/send`.

## Security considerations
Clients may accidentally send invalid redaction events if they try to redact
using `/send` in an old room on a server that does not implement this MSC.

## Unstable prefix

## Dependencies
This MSC defines additional behavior for [MSC2244], which has been accepted,
but not yet implemented.

[MSC2174]: https://github.com/matrix-org/matrix-spec-proposals/pull/2174
