# MSC2260: Update the auth rules for `m.room.aliases` events

## Background

The [`m.room.aliases`](https://matrix.org/docs/spec/client_server/r0.5.0#m-room-aliases)
state event exists to list the available aliases for a given room. This serves
two purposes:

  * It allows existing members of the room to discover alternative aliases,
    which may be useful for them to pass this knowledge on to others trying to
    join.

  * Secondarily, it helps to educate users about how Matrix works by
    illustrating multiple aliases per room and giving a perception of the size
    of the network.

However, it has problems:

  * Any user in the entire ecosystem can create aliases for rooms, which are
    then unilaterally added to `m.room.aliases`, and room admins are unable to
    remove them. This is an abuse
    vector (https://github.com/matrix-org/matrix-doc/issues/625).

  * For various reasons, the `m.room.aliases` event tends to get out of sync
    with the actual aliases (https://github.com/matrix-org/matrix-doc/issues/2262).

Note that `m.room.aliases` is subject to specific [authorization
rules](https://matrix.org/docs/spec/rooms/v1#authorization-rules).

## Proposal

We remove the special-case for `m.room.aliases` from the [authorization
rules](https://matrix.org/docs/spec/rooms/v1#authorization-rules). `m.room.aliases`
would instead be authorised following the normal rules for state events.

This would mean that only room moderators could add entries to the
`m.room.aliases` event, and would therefore solve the abuse issue. However, it
would increase the likelihood of `m.room.aliases` being out of sync with the
real aliases.

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

1. This will increase the number of ways that `m.room.aliases` differs from
   reality, particularly if we allow people to add entries to directories when
   they lack ops in the room, but also when server admins remove entries from
   the directory (currently https://github.com/matrix-org/synapse/issues/1477
   could be fixed, but under this MSC it would be unfixable.)

2. Often, all moderators of a room will be on one server, so much of the point of
   `m.room.aliases` (that of advertising alternative aliases on other servers)
   would be lost.

3. This would allow room operators to add 'fake' aliases: for example, I could
   create a room and declare one of its aliases to be
   `#matrix:matrix.org`. It's not obvious that this will cause any problems in
   practice, but it might lead to some confusion.
