# MSC2260: Update the auth rules for `m.room.aliases` events

## Background

Currently, `m.room.aliases` is subject to specific [authorization
rules](https://matrix.org/docs/spec/rooms/v1#authorization-rules). When these
rules were introduced, the intention was that `m.room.aliases` would be
maintained as an up-to-date list of the aliases for the room. However, this has
not been successful, and in practice the `m.room.aliases` event tends to drift
out of sync with the aliases (https://github.com/matrix-org/matrix-doc/issues/2262).

Meanwhile, `m.room.aliases` is open to abuse by remote servers who can add spam
or offensive aliases (https://github.com/matrix-org/matrix-doc/issues/625).

## Proposal

`m.room.aliases` exists to advertise the aliases available for a given
room. This is an ability which should be restricted to privileged users in the
room.

Therefore, the special-case for `m.room.aliases` is to be removed from the
[authorization
rules](https://matrix.org/docs/spec/rooms/v1#authorization-rules). `m.room.aliases`
would instead be authorised following the normal rules for state events.

TBD: are you still allowed to add rooms to the directory when you don't have
the necessary power level? If so, presumably this happens without updating the
`m.room.aliases` event. So:

 * Is there any mechanism for syncing the alias list if you are later given
   ops?

 * What if another user on your server has ops? What if Eve lacks ops and
   secretly adds `#offensive_alias:example.com`, and then Bob (who has ops)
   adds `#nice_alias:example.com`? How do we make sure that the offensive alias
   isn't published by Bob?

Server admins will continue to be able to remove entries from the directory
even if they do not have the right to send the `aliases` event (in which case
the `m.room.aliases` event will become outdated).

It would also be logical to allow the contents of `m.room.aliases` events to be
redacted, as per [MSC2261](https://github.com/matrix-org/matrix-doc/issues/2261).

## Tradeoffs

Perhaps allowing room admins the ability to redact malicious `aliases` events
is sufficient? Given that a malicious user could immediately publish a new
`aliases` event (even if they have been banned from the room), it seems like
that would be ineffective.

Or we could just allow room admins to issue new `m.room.aliases` events
(possibly restricting them to removing aliases, though it's TBD if state res
would work reliably in this case). However, that seems to suffer the same
problem as above.

## Potential issues

1. This will bake in https://github.com/matrix-org/synapse/issues/1477 in a way
   that cannot be fixed in the case that the server admin doesn't have ops in
   the room.

2. This would allow room operators to add 'fake' aliases: for example, I could
   create a room and declare one of its aliases to be
   `#matrix:matrix.org`. It's not obvious that this will cause any problems in
   practice, but it might lead to some confusion.
