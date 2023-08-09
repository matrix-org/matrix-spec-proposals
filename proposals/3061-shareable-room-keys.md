# MSC3061: Sharing room keys for past messages

In Matrix, rooms can be configured via the `m.room.history_visibility` state
event such that historical messages can be visible to all Matrix users
(`world_readable`), all room members (`shared`), room members from the time
that they are invited to a room (`invited`), or room members from the time that
they join a room (`joined`).  However, currently in encrypted rooms, rooms with
the history visibility set to `world_readable` or `shared` are effectively
set to `invited` since other members generally do not send new members the keys
to decrypt messages sent before they were invited or joined a room.

We define a "shared-history" flag that identifies keys for messages that were
sent when the room's visibility setting was set to `world_readable` or
`shared`.  This allows clients to know which keys are "safe" to share with new
members so that they can decrypt historical messages.  We also give examples of
ways in which this flag can be used.


## Proposal

A room key (such as a megolm session) is flagged as having been used for shared
history when it was used to encrypt a message while the room's history
visibility setting was set to `world_readable` or `shared`.

If the client does not have an `m.room.history_visibility` state event for the
room, or its value is not understood, the client should treat it as if its
value is `joined` for the purposes of determining whether the key is used for
shared history.  This is in contrast with the normal processing of
`m.room.history_visibility` which defaults to `world_readable` when there is no
`m.room.history_visibility` state event or its value is not understood.  This
is done so that, in the event of a bug that causes the client to fail to obtain
the state event, the client will fail in a secure manner.

Internally, a client may use any mechanism it wants to keep track of this flag.
When a room key is marked as having been used for shared history:

- `m.room_key` and `m.forwarded_room_key` messages used to share this key have
  a `shared_history` property set to `true` e.g.

  ```json
  {
    "type": "m.room_key",
    "content": {
      "algorithm": "m.megolm.v1.aes-sha2",
      "room_id": "!room_id",
      "session_id": "session_id",
      "session_key": "session_key",
      "shared_history": true
    }
  }
  ```

- the [`SessionData` type](https://spec.matrix.org/unstable/client-server-api/#definition-sessiondata)
  in key backups (that is, the plaintext object that gets encrypted into the
  `session_data` field) of this key has a `shared_history` property set to
  `true` in the decrypted JSON structure e.g.

  ```json
  {
    "algorithm": "m.megolm.v1.aes-sha2",
    "forwarding_curve25519_key_chain": [
      "hPQNcabIABgGnx3/ACv/jmMmiQHoeFfuLB17tzWp6Hw"
    ],
    "sender_claimed_keys": {
      "ed25519": "aj40p+aw64yPIdsxoog8jhPu9i7l7NcFRecuOQblE3Y"
    },
    "sender_key": "RF3s+E7RkTQTGF2d8Deol0FkQvgII2aJDf3/Jp5mxVU",
    "session_key": "AgAAAADxKHa9uFxcXzwYoNueL5Xqi69IkD4sni8Llf...",
    "shared_history": true
  }
  ```

  and,
- the [`SessionData` type](https://spec.matrix.org/unstable/client-server-api/#key-export-format)
  used in key exports has a `shared_history` property that is set to `true` for
  this key e.g.

  ```json
  {
    "algorithm": "m.megolm.v1.aes-sha2",
    "forwarding_curve25519_key_chain": [
      "hPQNcabIABgGnx3/ACv/jmMmiQHoeFfuLB17tzWp6Hw"
    ],
    "sender_claimed_keys": {
      "ed25519": "aj40p+aw64yPIdsxoog8jhPu9i7l7NcFRecuOQblE3Y"
    },
    "sender_key": "RF3s+E7RkTQTGF2d8Deol0FkQvgII2aJDf3/Jp5mxVU",
    "session_key": "AgAAAADxKHa9uFxcXzwYoNueL5Xqi69IkD4sni8Llf...",
    "shared_history": true
  }
  ```

When a client obtains a key that has the `shared_history` property set to
`true`, then it flags the key internally as having been used for shared
history.  Otherwise, the key should not be flagged as such.

When the room's history visibility setting changes to `world_readable` or
`shared` from `invited` or `joined`, or changes to `invited` or `joined` from
`world_readable` or `shared`, senders that support this flag must rotate their
megolm sessions.

Clients may use this flag to modify their behaviour with respect to sharing
keys.  For example, when the user invites someone to the room, they may
preemptively share keys that have this flag with the invited user.  Other
behaviours may be possible, but must be careful not to guard against malicious
homeservers.  See the "Security Considerations" section.

## Potential issues

Room keys from clients that do not support this proposal will not be eligible
for the modified client behaviour.

The suggested behaviour in this MSC is to only share additional keys when
inviting another user.  This does not allow users who join the room but were
not invited (for example, if membership is restricted to another space, or if
the room is publicly joinable) to receive the keys.  Also, if the inviter does
not have all the keys available for whatever reason, the invitee has no way of
receiving the keys.  This may be solved in the future when we have a mechanism
for verifying room membership.

## Alternatives

Rather than having the sender flagging keys, a client can paginate through the
room's history to determine the room's history visibility settings when the
room key was used.  This would not require any changes, but has performance
problems.  In addition, the server could lie about the room history while the
user is paginating through the history.  By having the sender flag keys, this
ensures that the key is treated in a manner consistent with the sender's view
of the room.

Rather than using a boolean flag, we could include the history visibility
setting as-is.  For example, a `history_visibility` field could be added, which
is set to the history visibility setting (e.g. `world_readable`).  This
produces an equivalent effect, but it pushes the processing of the history
visibility setting to the receiver rather than the sender.  For consistency, it
is better for as much of the decision-making done by the sender, rather than
the receiver.

## Security considerations

Clients should still ensure that keys are only shared with authorized users and
devices, as a malicious homeserver could inject fake room membership events.
One way to ensure that keys are only shared with authorized users is to only
share keys with users when the client invites them, as the client is then
certain that the user is allowed to be in the room.  Another way is to have a
mechanism of verifying membership, such as the method proposed in
[MSC3917](https://github.com/matrix-org/matrix-spec-proposals/pull/3917).

## Unstable prefix

Until this feature lands in the spec, the property name to be used is
`org.matrix.msc3061.shared_history` rather than `shared_history`.
