# MSC3912: Relation-based redaction

There are cases where, when redacting an event, it would make sense to also
redact all events that relate to it in a certain way. A few examples of this
are:

* Edits: when redacting a message that has been edited, also redacting its edits
  would ensure that none of the information in the original message leaks
  through them.
* Live location sharing (from
  [MSC3489](https://github.com/matrix-org/matrix-spec-proposals/pull/3489)): the
  user streaming its live location might want to delete their location history
  once they have stopped sharing it.
* Moderation: a room's moderator might want to delete an entire thread from a
  room, a poll with all its answers, etc.

Currently, the only way to do this is for the client to keep track of each
individual event and redact them itself. This is cumbersome because it might
require clients to work around their own limits on how much history is stored
for a given room, and might cause them to hit rate limits when attempting to
send redactions, which would translate into general slowness for the user (since
their other actions would also be prevented by rate limiters as a result).

## Proposal

We add a new optional `with_relations` property to the body of the [`PUT
/_matrix/client/v3/rooms/{roomId}/redact/{eventId}/{txnId}`](https://spec.matrix.org/latest/client-server-api/#put_matrixclientv3roomsroomidredacteventidtxnid)
requests. This property is a list of relation types. If an event relates to the
event specified in the `{eventId}` parameter with a relation type specified in
this `with_relations` property, the server also redacts it on behalf of the user
performing the redaction. The response body of this endpoint does not change.

For example, let's consider the following message:

```json
{
    "type": "m.room.message",
    "content": {
        "body": "Hello",
        "msgtype": "m.text",
        "m.relates_to": {
            "rel_type": "m.replace",
            "event_id": "$some_event_id"
        }
    },
    "event_id": "$a"
}
```

And its edit:

```json
{
    "type": "m.room.message",
    "content": {
        "body": "* Hello world!",
        "msgtype": "m.text",
        "m.new_content": {
            "body": "Hello world!",
            "msgtype": "m.text"
        },
        "m.relates_to": {
            "rel_type": "m.replace",
            "event_id": "$a"
        }
    },
    "event_id": "$b"
}
```

Then the request:

```
PUT /_matrix/client/v3/rooms/!someroom:example.com/redact/$a/foo

{
    "with_relations": ["m.replace"]
}
```

Causes events `$a` and `$b` to both get redacted.

A server may wish to leverage
[MSC2244](https://github.com/matrix-org/matrix-doc/pull/2244) (mass redactions)
to redact all events targeted by the redaction request if supports it, however this is not a
requirement.

If the `with_relations` property is absent from the request body, only the event referred to by the `{eventId}` parameter (`$a` in the example above) is redacted. Same goes if `with_relations` is an empty list.

If an event that matches the redaction criteria (i.e. relates to the event
that's being redacted with one of the relation types specified in the request)
cannot be redacted by the user sending the redaction request (because of
insufficient permissions), it is ignored. Clients may attempt to detect cases
where a user would not be able to redact some events matching the redaction
criteria (e.g. matching `m.reference` relations when redacting a `m.poll.start`
event, matching `m.thread` relations, etc., with an insufficient power level to
delete other users' events) and display a warning to the user in this case.

If an event that matches the redaction criteria comes down federation after
redaction requests has completed, the server must attempt to redact it on behalf
of the redaction request's sender.

Servers may wish to copy the `with_relations` property into the
`m.room.redaction` event's `unsigned` object in order to facilitate watching for
new events to redact once the redaction request has completed. Servers must
ignore `with_relations` properties in the `unsigned` object of redaction events that were not sent by a local user.

Since the response format to the `PUT
/_matrix/client/v3/rooms/{roomId}/redact/{eventId}/{txnId}` does not change as a
result of this proposal, servers may respond to the request once the event referenced to by the `{eventId}` parameter is redacted, and redact events that relate to it in the background.


### Unstable feature in `/version`

Homeservers which support this MSC should indicate it by adding
`org.matrix.msc3912` and `org.matrix.msc3912.stable` in the response to `GET
/_matrix/client/versions` requests.


## Alternatives

The server could respond to the client with some information about whether some
events could not be redacted due to insufficient permissions. However, this
could lead to confusing user experience, wherein the server responds by telling
the client all events could be redacted, but another event comes down federation
shortly afterwards that cannot be redacted.

An alternative proposal would be specifying a static list of relation types to
consider when redacting a message. However, this would not work well with more
generic ones such as `m.reference`, and would restrict clients in the UX they
offer to users (e.g. a client might want to show a checkbox to a user offering
them to redact a whole thread when redacting the thread's root, if this user is
a room moderator). This could still be helpful for some relation types (e.g.
`m.replaces`) but clients are likely better positioned to make this decision
given they have more control over feature UX.

## Unstable prefixes

Until this proposal is stabilised, `org.matrix.msc3912.with_relations` should be
used instead of `with_relations`.