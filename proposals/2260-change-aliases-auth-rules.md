# MSC2260: Update the auth rules for `m.room.aliases` events

## Background

Currently, `m.room.aliases` is subject to specific [authorization
rules](https://matrix.org/docs/spec/rooms/v1#authorization-rules). When these
rules were introduced, the intention was that `m.room.aliases` would be
maintained as an up-to-date list of the aliases for the room. However, this has
not been successful, and in practice the `m.room.aliases` event tends to drift
out of sync with the aliases. FIXME: why is this, apart from
https://github.com/matrix-org/synapse/issues/1477, which could be fixed?

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

As a corollary, only users with the power level necessary to send the
`m.room.aliases` state event will be allowed to add entries to the room
directory. Server admins will continue to be able to remove entries from the
directory even if they do not have the right to send the `aliases` event (in
which case the `m.room.aliases` event will become outdated).

## Tradeoffs

Perhaps we could instead allow room admins the ability to redact malicious
`aliases` events? Or to issue new ones?

## Potential issues

1. This will bake in https://github.com/matrix-org/synapse/issues/1477 in a way
   that cannot be fixed in the case that the server admin doesn't have ops in
   the room.

2. This would allow room operators to add 'fake' aliases: for example, I could
   create a room and declare one of its aliases to be
   `#matrix:matrix.org`. It's not obvious that this will cause any problems in
   practice, but it might lead to some confusion.
