# MSCXXXX: Explicit read receipts for sent events

Today, the spec dictates that clients should not send read receipts for their own events, and
homeservers should clear notifications in a room for a user after the user sends an event to the
room. 

Relevant spec sections (from Tulir's matrix-spec issue
https://github.com/matrix-org/matrix-spec/issues/1410):

The client behavior section of https://spec.matrix.org/v1.5/client-server-api/#receipts says

> Clients SHOULD NOT send read receipts for events sent by their own user.

https://spec.matrix.org/v1.5/client-server-api/#receiving-notifications says (emphasis mine)

> When the user updates their read receipt (either by using the API or by sending an event),
> notifications prior to and including that event MUST be marked as read.

This leads to overly complicated implementations on both the client and the server. Each codebase
needs to comapre the sender of events as well as the read receipts in order to handle marking the
room as read, clearning notification counts, and displaying read markers for other users. This code
is complex and leads to bugs, such as https://github.com/matrix-org/synapse/issues/14837

## Proposal

The homeserver should generate a public (`m.read`) read receipt for the user whenever the user
sends an event to the room. The receipt should point at the newly created event. This receipt should
be generated prior to calculating notification counts or push rules. This means the concept of
"where the user has read up to" is simplified to just a read receipt, where previously it was the
greater value of the user's read receipt and their last sent event.

Clients should receive this receipt at the same time as receiving the event itself back from the
homeserver (in the same /sync payload). The read receipt can't be sent prior to the event, as the
receipt would then be pointing to an event that the client doesn't know about yet, and if the event
is sent prior to the receipt there's a risk of the client attempting to generate a duplicate read
receipt for the same event.

The client logic for marking a room as read can be simplified to moving the m.read to the latest
event in the room and notifying the server if that's different than the current receipt position.
Clients wouldn't need to feature detect whether the homeserver implements this proposal, as the
client sending a read receipt for their own message shouldn't harm homeservers that predate it. In
practice, some clients already generate read receipts in this way.

## Potential issues

There is a risk that when implementing this change room notification counts could change. For example,
if a user sent an event to a room prior to implementing this MSC, and then the homeserver starts using
this MSC, the homeserver will still need to treat the last event sent by the user as the read receipt,
meaning we won't actually be able to drop the complicated code. However, in practice, some homeservers
such as synapse don't need to reevaluate notification counts and instead only calculate them at event
send time, in which case there's no risk, as no notification count would be generated for a user sent
event prior to or after this proposal is implemented.

To ease transitioning, hypothetically homeserver implementations could also backfill read receipts for
users based on their last sent event, but this would generate a fair amount of /sync traffic to
clients when it happens and should be avoided.

## Alternatives

We could stay with the existing behaviour, and instead just improve the specification to make it more
clear what clients should do.

We could also just change the spec to say the clients are now allowed to send read receipts sent by their
own user, as opposed to explicitly discouraging it as we do for today. This would allow for simpler
client implementations, but the homeserver would still have the complexity of dealing with clients that
don't do this.

The homeserver could alternatively generate a private read receipt (`m.read.private`) as opposed to a
public read receipt, but using a public receipt also simplifies the client implementations for other
users in the same room to display read receipts for other users. You're already sending a message to
the room, so no privacy concern exists.

This proposal suggests just changing how read receipts are generated as part of a new Matrix spec version
for all rooms. Alternatively, we could gate this behind a new room version, but that shouldn't be necessary.

## Security considerations

None, it's the same data being represented in a different way (the users sending to the room so they must
have read it.)

## Unstable prefix

None, but this functionality should be implemented behind a configuration flag so that homeservers can opt
into the functionality before this MSC is merged.

## Dependencies

This MSC would also impact Unread Counts as defined in
https://github.com/matrix-org/matrix-spec-proposals/pull/2654, which is not yet merged.
