# MSC4194: Batch redaction of events by sender within a room (including soft failed events)

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

3. Soft failure of events sent by the throwaway account after the
   moderator bans the throwaway. These events are not visible to the
   moderator's matrix client, and there is no way for a moderator to
   redact these events. This is a huge problem that occurs far more
   frequently than it should[^often-soft-failure].

[^create-mass-redaction]: I think?

[^often-soft-failure]: https://github.com/matrix-org/synapse/issues/9329
## Proposal

This proposal introduces a very simple client-server endpoint to
alleviate all three of the concerns surrounding the moderators
redaction flow.

### Redacting a user's events

A new endpoint is introduced into the client-server spec.
The endpoint is introduced with the intention to allow convenient and
quick bulk redaction of spam events for room moderators.  Who may not
necessarily have administrative privileges on their homeserver, and
will also need to redact messages from remote users.

`POST /_matrix/client/v1/rooms/{roomID}/redact/user/{userID}`

This endpoint redacts the target matrix user's unredacted events by
sending redactions on behalf of the requesting user.

The target user's unredacted events are sourced in reverse
chronological order, starting from the most chronologically-recent
visible event in the room history for the requesting user.
Similarly to `/rooms/{roomID}/messages?dir=b`.

This endpoint is blind to the distinction between normal and
soft-failed events, and will cause redactions to be issued
for any soft-failed events that match the scope of the
request.

Events known to have already been redacted SHOULD be ignored and MUST
NOT contribute to the request limit.

It is left to an implementation detail whether a `m.room.redaction`
event is created for each event, or
[MSC2244](https://github.com/matrix-org/matrix-spec-proposals/pull/2244)
is employed. We expect that for now, most implementations will
issue one `m.room.redaction` event for each event under
the scope of the request. Sent by the requesting user.

#### Rate limiting

This endpoint SHOULD be rate limited, but the number `m.room.redaction`
events emitted SHOULD NOT be the subject of the rate limit.
But instead the number of events that have been redacted overall.
This is to cover semantics of MSC2244.

Servers SHOULD be more liberal in the number of events that can be
redacted in comparison to rate limits for `/send` when the endpoint is
being used to redact another user's events.  Rather than the
requester's own events. The intent of being liberal is to allow
moderators to remove spam quickly, rather than struggling behind rate
limits for `/rooms/redact/event` or `/send`.

#### Path parameters

`roomID`: `string` - The room to get events to redact from.

`userID`: `string` - The sender of the events to redact.

#### Query parameters

`limit`: `integer` - The maximum number of events to
redact. Default: 25.

Client authors should be aware that the server may return less than
the `limit` even when `is_more_events` is `true`, and so should always
check the response.

#### Request body

`reason`: `string` - The reason for redacting the user's events
(Optional).

#### Response

`is_more_events`: `boolean` - Whether there are more events outside of
the scope of the request sent by the user that could be redacted, but
have not been because of the `limit` query parameter.  If
`is_more_events` is true, then the server should expect that the
client can optionally call the endpoint again, to redact even more events.

`redacted_events`: `object` - An object with the following fields:

* `total`: `integer` - The number of events that have been redacted,
  including soft failed events.

* `soft_failed`: `integer` - The number of soft failed events that
  have been redacted.

```
200 OK
Content-Type: application/json

{
  "is_more_events": false,
  "redacted_events": {
    "total": 5,
    "soft_failed": 1
  }
}
```

#### Limited response

Servers may wish to limit the maximum size of the limit that can be
specified. This maximum limit may even be dynamic to comply with rate
limiting.

To do this, they should simply redact less events than the limit provided
by the client.

```
POST /.../?limit=1000
200 OK
Content-Type: application/json

{
  "is_more_events": true,
  "redacted_events": {
    "total": 25,
    "soft_failed": 3
  }
}
```

## Potential issues

### Forward compatibility with `/messages` style query parameters

We probably want to keep the endpoint compatible with `/messages`
style query pamarameters if the endpoint needs to be extended in the
future. It is our current assessment that we are currently forward
compatible. But someone should double check.

### Redacting "future" soft-failed events

Given that a request to the `/rooms/redact/user` endpoint is very
likely to occur after a room ban, then it makes sense that there could
still be soft failed events outside the scope of the request. The
moderator's homeserver is likely to discover soft-failed events from
the target user after the moderator's request has completed.

It could make sense to add a flag to the endpoint to tell the
moderator's homeserver to issue redactions on their behalf for the
newly discovered events. However, this could be complicated for
servers to implement.  The flag would have to reset if the target user
is unbanned, and all incoming soft failed events will have to be
checked against a list of flagged servers.

At the moment we will remain forward compatible with a future
proposal to add a flag.


## Alternatives

* An endpoint could be developed to expose soft-failed events to
  clients or appservices such as in
 [MSC4109](https://github.com/matrix-org/matrix-spec-proposals/pull/4109).

## Security considerations

### Use case for self redaction

Implementers should be cautious over the use of this API for self
redaction. We might omit that use case from the MSC if there are concerns.

## Unstable prefix

Until the MSC is accepted, implementations can use `org.matrix.msc4194` as the
unstable prefix and as a flag in the `unstable_features` section of `/versions`:
* `/_matrix/client/unstable/org.matrix.msc4194/rooms/{roomID}/redact/user/{userID}`
  instead of `/_matrix/client/v1/rooms/{roomID}/redact/user/{userID}`
Once the MSC is merged, the `org.matrix.msc4194.stable` unstable feature flag
can be used to advertise support for the stable version of the endpoint, until
the spec release with the endpoint is advertised.

## Dependencies

None
