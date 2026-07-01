# MSC4019: Encrypted event relationships

The current event relationships specification sacrifices metadata privacy for the sake of
server-side aggregations. There are a lot of times when the former is more important.
In this proposal, we are giving individual users the choice upon which side is more important for
them.

## Proposal

We introduce a state event, `m.room.relationship_encryption`, where the state key is always the
empty string, and the content an empty object. The existence of this event signals that clients
should send and read received events with `m.relates_to` in the encrypted payload instead of
the cleartext part. Like `m.room.encryption`, once turned on, it cannot be turned off.

### Client behaviour

If the state event `m.room.relationship_encryption` exists or existed in the room, clients SHOULD send the
`m.relates_to` that appears in any encrypted event in the encrypted payload. In received encrypted events,
clients SHOULD ignore the `m.relates_to` that appears in the cleartext part of the event if an `m.relates_to`
appears in the encrypted payload. If there is no `m.relates_to` in the encrypted payload, clients SHOULD
use the `m.relates_to` in the cleartext part of the event instead.
Clients SHOULD NOT trust the results obtained from the
[relationships API](https://spec.matrix.org/v1.6/client-server-api/#relationships-api)
in the client-server API, and SHOULD NOT obtain event relationships from those API.
If clients called the relationships API, they SHOULD understand that the responses may be incomplete.
They SHOULD also check for each encrypted received event in the response whether it contains an encrypted
`m.relates_to`, and if it does, it SHOULD use the encrypted copy to verify whether the event does belong
to that relationship.

### Server behaviour

Servers MAY track the existence of the state event `m.room.relationship_encryption` and, if it exists
or existed in the room, respond to the relationships API as if no event relationships exists in the room.

## Potential issues

According to the existing specs, clients might ignore the `m.relates_to` in the encrypted payload of
an event, causing rendering issues for them. Thus, clients that supports `m.room.relationship_encryption`
MAY send the `m.relates_to` in both the cleartext part and the encrypted payload for rooms that has this state event.
Clients that do so SHOULD inform their users of this, and SHOULD allow the users to choose whether they
want to send the `m.relates_to` in the cleartext part.

As "Client behaviour" indicates, using encrypted relationships for events means that the user does not
want the relationships to be exposed to the server, so the relationships API, including aggregations,
will not work. Clients SHOULD have their own way to build the event relationships from individual events.

Users should be aware that, even though the event relationships are encrypted, there might be some other clues from which a homeserver can potentially find out the relationships between events. For example, when a client sees a reply to an event, it may try to fetch the event being replied to from the homeserver, and thus it can know the event being fetched is related to some other event in some way.

## Alternatives

We could also just let the clients to decide (maybe by user's preferences) whether to send `m.relates_to`
in the encrypted payload, ignoring the state event. At the first look, this alternative approach leads to
arguably better privacy. However, it lacks interoperability, because users would need to explain to
others how to tweak the settings for those having a conversation with them. And if the other users in the
room do not know how to turn this option on, it actually has worse privacy than my proposal.

## Security considerations

See "potential issues."

## Unstable prefix

Use `moe.kazv.mxc.msc.4019.room.relationship_encryption` for `m.room.relationship_encryption`.

## Dependencies

None.
