# Allowing Reasons in all Membership Events

Currently users can specify a reason for kicking or banning users in a room
that both the target and other users in a room can see. This is useful to
explain *why* an action without having to send separate messages.

The proposal extends this to all events, including invites, invite rejections
and leaves for similar reasons.

## Proposal

Allow `reason` field to be specified for all of the following APIs:

```
POST /_matrix/client/r0/rooms/{roomId}/invite
POST /_matrix/client/r0/rooms/{roomId}/leave
POST /_matrix/client/r0/rooms/{roomId}/kick
POST /_matrix/client/r0/rooms/{roomId}/ban
POST /_matrix/client/r0/rooms/{roomId}/unban
POST /_matrix/client/r0/rooms/{roomId}/join
POST /_matrix/client/r0/join/{roomIdOrAlias}
PUT  /_matrix/client/r0/rooms/{roomId}/state/m.room.member/{userID}
```

If specified the `reason` field will be added to the generated membership
event's content.

*Note: `/state/m.room.member` API currently allows this as clients can specify
arbitrary content already*

Clients may choose to display the reason for membership events in a room,
though may not do so if e.g. they have collapsed a set of membership changes.

Clients should not display an invite reason by default to the invitee as this
allows a classic abuse and harassment vector. However, clients may wish to show
invite reasons from known¹ senders, or have a button that allows viewing any
invite reason.

## Use Cases

Some basic use cases and examples are given below.

### Kick/ban

Kicking and banning already allow specifying a reason to allow giving a reason
for the moderation action (e.g. "Banned for spamming").

### Leaving a Room

A user may wish to leave a room e.g. because the room is no longer relevant
to them, allowing them to specify a reason means they can easily step out of
the room quietly without having to send a message to explain their actions.

### Invite

This can be useful to give some context for an invite, e.g. "Alice invites Bob
to get some feedback on the membership reasons MSC".

### Rejecting an Invite

If Alice has invited Bob (and many others) to a room to discuss going to a
concert then Bob may wish to simply reject the invite if he can't make it.
Adding a "will be out of town" reason to the rejection helps Alice to know why
her invite was rejected.

### Joining room

Adding a reason for joining could be used e.g. by automated bots to say why
they're joining. For example a bridge bot may join a room when asked to bridge
the room to an external network, in which case they may have a reason such as
"BridgeBot joined to bridge the room to RemoteNetwork at the request of Alice".

## Potential Issues

The main issue here is ensuring that the invite reason cannot be used as an
abuse vector, however if clients follow the recommendations above this concern
should be mitigated.

---

¹ This is left up to implementations to decide, if they wish to do so.
