# MSC3912: Redaction of related events

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

We add a new optional `with_rel_types` property to the body of the [`PUT
/_matrix/client/v3/rooms/{roomId}/redact/{eventId}/{txnId}`](https://spec.matrix.org/latest/client-server-api/#put_matrixclientv3roomsroomidredacteventidtxnid)
requests. This property is a list of relation types. If an event relates to the
event specified in the `{eventId}` parameter with a relation type specified in
this `with_rel_types` property, the server also redacts it on behalf of the user
performing the redaction. The response body of this endpoint does not change.

The client may not be aware of the relation types associated with an event (for
example in the case of moderation). That's why we introduce a catch-all `"*"` value,
which if found in the list means "any relation type".

For example, let's consider the following message:

```json
{
    "type": "m.room.message",
    "content": {
        "body": "Hello",
        "msgtype": "m.text"
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
    "with_rel_types": ["m.replace"]
}
```

Causes events `$a` and `$b` to both get redacted.

A server may wish to leverage
[MSC2244](https://github.com/matrix-org/matrix-doc/pull/2244) (mass redactions)
to redact all events targeted by the redaction request if supports it, however
this is not a requirement.

If the `with_rel_types` property is absent from the request body, only the event referred to by the `{eventId}` parameter (`$a` in the example above) is redacted. Same goes if `with_rel_types` is an empty list.

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

Since the response format to `PUT
/_matrix/client/v3/rooms/{roomId}/redact/{eventId}/{txnId}` requests does not change as a
result of this proposal, servers may respond to the request once the event
referenced to by the `{eventId}` parameter is redacted, and redact events that
relate to it in the background.

This is important to note that we do not consider parent events. In the previous example,
a redaction of `$b` would not cause `$a` to be redacted. The following request:

```
PUT /_matrix/client/v3/rooms/!someroom:example.com/redact/$b/foo

{
    "with_rel_types": ["m.replace"]
}
```

Causes only event `$b` to get redacted.

The redaction will be limited to the events which meet the validity requirements of the
selected relationship types, for example [these requirements](https://spec.matrix.org/v1.6/client-server-api/#validity-of-replacement-events) for edited events.
In case of the previous example, let's consider this additional event `$c`: 

```json
{
    "type": "m.room.message",
    "content": {
        "body": "* Hello world2!",
        "msgtype": "m.text",
        "m.new_content": {
            "body": "Hello world2!",
            "msgtype": "m.text"
        },
        "m.relates_to": {
            "rel_type": "m.replace",
            "event_id": "$b"
        }
    },
    "event_id": "$c"
}
```

This edit event is invalid because we must not edit an edit (We were supposed to refer to the
original event: `$a`)
Then the request:

```
PUT /_matrix/client/v3/rooms/!someroom:example.com/redact/$a/foo

{
    "with_rel_types": ["m.replace"]
}
```

Causes events `$a` and `$b` to get redacted, but no `$c`

### Unstable feature in `/versions`

While this MSC is unstable, homeservers which support this MSC should indicate it by adding
`org.matrix.msc3912` flag in the `unstable_features` array of the response to `GET
/_matrix/client/versions` requests.
Once this MSC becomes a part of a spec version, clients should rely on the presence of the spec
version, that supports the MSC, in versions on /versions, to determine support.

## Potential issues

Since all the redactions are sent on behalf of the user who sent the original
`PUT /_matrix/client/v3/rooms/{roomId}/redact/{eventId}/{txnId}` request, if
this user leaves the room the server is no longer able to send redactions on
their behalf. However, the author considers this a small edge case which is
unlikely to happen in practice, and can be worked around by another user (with
permissions to delete the new events) sending another `PUT
/_matrix/client/v3/rooms/{roomId}/redact/{eventId}/{txnId}`.


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
used instead of `with_rel_types`.