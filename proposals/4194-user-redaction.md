# MSC4194: User redaction

Targeted attacks are a problem in Matrix. Typically throwaway users
are used to target matrix rooms with abuse in the form of multiple
messages.  The intent of the spammer is to fill the room timeline view
in clients with abuse.

Typically, a moderator will be pinged by a bystander, and the
moderator will respond by first banning the throwaway account and then
issuing redactions via a client for each event the throwaway account
sent.

Due to the architecture of various Matrix APIs, there are multiple
issues that can occur in the moderator's flow.

1. Calling `/messages` is required for some clients to accurately get
   the full list of `event_id`s the throwaway account sent.  This is a
   compounding problem because homeservers can be slow to respond to a
   filtered `/messages` request and then the client must still process
   the response and issue a redaction for each event returned.
   This is how both Mjolnir and Draupnir source events for redaction.

2. The client must call `/rooms/redact/event` for each target event,
   requiring the client to make multiple requests, further impeding
   response time. Homeservers typically rate limit the number of
   redactions that a client can send to `/redact` evenly with `/send`,
   which further compounds response time.
   [MSC2244](https://github.com/matrix-org/matrix-spec-proposals/pull/2244)
   tried to alleviate part of the problem by allowing the redactions
   to be sent in one event. But there currently are no endpoints that
   allow you to create this event[^create-mass-redaction].

3. Soft failure of events sent by the throwaway account after a ban
   stop them from being visible to the matrix client, and there is no
   way for a moderator to redact them. This is a huge problem that
   occurs far more frequently than it should.

[^create-mass-redaction]: I think?
## Proposal

This proposal introduces a very simple client-server endpoint to
alleviate all three of the concerns surrounding the moderators
redaction flow.

### Redacting a user's events

A new endpoint is introduced into the client-server spec.

`POST /_matrix/client/v1/rooms/{roomID}/redact/user/{userID}`

This endpoint redacts the target matrix user's unredacted events in
reverse chronological order, starting from the most
chronologically-recent visible event in the room history for the
requesting user.

This endpoint is blind to the distinction between normal and
soft-failed events, and will cause redactions to be issued
for any soft-failed events that match the scope of the
request.

It is left to an implementation detail whether a `m.room.redaction`
event is created for each event, or
[MSC2244](https://github.com/matrix-org/matrix-spec-proposals/pull/2244)
is employed. We expect that for now, most implementations will
issue one `m.room.redaction` event for each event under
the scope of the request.

#### Rate limiting

This endpoint SHOULD be rate limited, but the number `m.room.redaction`
events emitted SHOULD NOT be the subject of the rate limit.
But instead the number of events that have been redacted overall.
This is to cover semantics of MSC2244.
Servers SHOULD be more liberal in the number of events that
can be redacted in comparison to rate limits for `/send` when
the endpoint is being used to redact another user's events.
Rather than their own events.

#### Query parameters

`limit`: `integer` - The maximum number of events to redact. Default: 25.

#### Response

`is_more_events`: `boolean` - Whether there are more events outside of
the scope of the request sent by the user that could be redacted, but
have not been because of the `limit` query parameter.  If
`is_more_events` is true, then the server should expect that the
client can optionally be called again, to redact more even more events.

`redacted_events`: `integer` - The number of events that have been redacted, including soft failed events.

`soft_failed_events`: `integer` - The number of soft failed events that have been redacted.

```
200 OK
Content-Type: application/json

{
  "is_more_events": false,
  "redacted_events": 5
  "soft_failed_events": 1
}
```

##### Limited response

Servers may wish to limit the maximum size of the limit that can be specified.

```
{
  "errcode": "M_LIMIT_TOO_LARGE",
  "error": "The limit parameter specified for this request is too large.",
  "max_limit": 100
}
```

## Potential issues

None so far.

## Alternatives


## Security considerations

### Use case for self redaction

Implementers should be cautious over the use of this API for self
redaction. We might omit that use case from the MSC if there are concerns.

## Unstable prefix

If nothing exists for what `M_LIMIT_TOO_LARGE` is trying to do, then
`org.matrix.msc4194.LIMIT_TOO_LARGE`

`POST /_matrix/client/unstable/org.matrix.msc4194/rooms/{roomID}/redact/user/{userID}`

## Dependencies

None
