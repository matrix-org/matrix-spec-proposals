# MSC3414: Encrypted state events

Currently in Matrix, all room state is unencrypted and accessible to everyone in the room, and
occasionally people outside the room (public room directory, invite state, peekable rooms, etc).
Most events in room state could be encrypted to preserve metadata, which is what this MSC aims
to achieve. Some parts cannot be encrypted though in order to maintain a working protocol.

## Proposal

Under this proposal, all room state events can be encrypted with the exception of events critical to
maintain the protocol. Those critical events are:

* `m.room.create`
* `m.room.member`
* `m.room.join_rules`
* `m.room.power_levels`
* `m.room.third_party_invite`
* `m.room.history_visibility`
* `m.room.guest_access`
* `m.room.encryption` - Though not critical to the server-side protocol, it is critical to clients.

Clients should ignore encrypted events of the above types.

Events which could be encrypted but aren't recommended to be encrypted under this proposal are:

* `m.space.child` and `m.space.parent` - These are used by the server in some endpoints, though could
  be interpretted by clients if absolutely needed.

All other state event types are able to be encrypted, if the room itself is encrypted.

An encrypted state event looks very similar to a regular encrypted room message: the `type` becomes
`m.room.encrypted` and the `content` is the same shape as a regular `m.room.encrypted` event. The
`state_key` for encrypted state events is an arbitrary string used to differentiate different kinds
of state while protecting the underlying event type.

**Note**: It is deliberate that state keys can ultimately cause conflicts when the room state as a
whole is decrypted. This is because a consistent hash of, say, `room_id + event_type` would mean that
an attacker can simply run the hash algorithm themselves to determine which state event to target
if they wanted to try "breaking" the encryption. Without consistent hashing, the attacker is forced
to break all/most of the room state or find another vector of attack for the information they're
after. Lack of consistent hashing does cause some problems though.

Clients are expected to decrypt all room state so they can reuse the appropriate `state_key` when
updating state events. However, conflicts are still possible within the decrypted set of state (such
as two events claiming to be `m.room.name` with empty state key): these are resolved by using the
most recent event by `origin_server_ts` then by `event_id` in lexicographic order.

An obvious challenge to all of this is that clients won't have decryption keys for the events if
they joined after the events were sent. To combat this, when a client joins a room it should send
keyshare requests to anyone with larger-than-default power level in the room, where those empowered
clients should then respond with the appropriate decryption keys regardless of device/user trust. Note
that this effectively means a client should use a dedicated megolm session when working with room state.
This also implies that all room state is still available to all members of the room - per-event ACLs
are deliberately not covered by this MSC, though could be trivially implemented on top of a system
like this.

Keyshare requests are sent to all larger-than-default members of the room to ensure that the event sender
isn't required to stay online 24/7 for new members to decrypt the events. The theory here is that at least
one of the room moderators/admins will be online when the user joins (considering most joins to encrypted
rooms will follow an invite), so getting the decryption keys should be easier. Clients might wish to
send out a wider keyshare request if the larger-than-default members don't respond in X seconds.

For invites, servers are expected to include all `m.room.encrypted` state events in the invite/knock
state. When sending invites, clients *should* send decryption keys for the aesthetic events (room name,
topic, etc) so the invite can be contextual, though this is not required. This same approach is not
possible on 3PID invites, however that is considered an acceptable loss under this MSC.

### Worked example

To encrypt an `m.room.name` state event, the client would first determine if there's already an encrypted
room name event. If so, it would use the same `state_key`, but otherwise generate a string to become
the `state_key`. Then, the event is encrypted as normal with the following payload:

```json5
{
  "type": "m.room.name",
  "state_key": "", // actual state key for the event, not the generated one!
  "content": {
    "name": "Secret Chat"
  },
  "room_id": "!room:example.org"
}
```

Finally, the state event is sent to the room to end up as:

```json5
{
  "type": "m.room.encrypted",
  "state_key": "<generated_or_reused_string>",
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "sender_key": "<sender_curve25519_key>",
    "device_id": "<sender_device_id>",
    "session_id": "<outbound_group_session_id>",
    "ciphertext": "<encrypted_payload_base_64>"
  }
}
```

### Restricted rooms

Restricted rooms ([MSC3083](https://github.com/matrix-org/matrix-doc/pull/3083)) implement a join rule where
people can join a room if they are members of one or more other given rooms. While
[MSC3061](https://github.com/matrix-org/matrix-doc/pull/3061) can be leveraged for explicit invites to new
members of the room, the MSC also does not solve the problem that restricted rooms impose.

To fix the reliance on key sharing, it is proposed that keys be automatically sent whenever restricted-ness
changes and when membership changes in a room used by a restricted room.

As a worked example, Room A and Room B exist, where Room B is restricted to members of Room A. Alice is admin
of both rooms and Bob got invited to Room A by Alice. Alice shares keys for all relevant parts of Room A (the
state and timeline under MSC3061) and Room B's state with Bob. If Alice were to add Room C as a room for members
to join Room B with, then Alice would send decryption keys for all of Room B's state with all members of Room
C too.

In order to limit the exposure of state to unjoined parties, it is acceptable for a client to only share keys
for aesthetic events (name, avatar, topic, etc) until the user joins the room where they then receive the full
state through key sharing or other mechanisms. This is primarily intended to reduce exposure of a room's
metadata until the user joins an appropriate room. As an alternative, clients could share just the aesthetic
events on invite and the remainder when the user accepts the invite, pre-empting their join attempt to the
restricted room.

### Other details

Clients should ensure that keyshare requests are from current members of the room, from their view. Clients
should also attempt to request keys from their own devices in addition to empowered users in the event that
a different device accepted the invite or the keys were sent to the "wrong" device. Key backup might also be
useful here.

Keyshare requests from blocked devices/users are still expected to be ignored or declined.

Note that clients will have to track where a session was used to ensure the sessions are appropriately sent
to users. For some clients this might be a simple lookup to see if the session ID is used in a state event,
though for others it might make more sense to explicitly track it.

For media events like room avatars, encryption is the same as regular room messages. The media is uploaded
encrypted to the homeserver then detailed in a payload that is also encrypted to the final room state event.

## Potential issues

Decryption failures of any variety are always an ongoing risk with encryption, however it is believed that
the vast majority of decryption failures are related to implementation or out-of-scope bugs. This MSC has
taken steps to ensure that each user will receive decryption keys eventually, though the speed of receipt
for these keys might be delayed.

Keysharing is not great as a method of transport for these keys, however this is believed to be better over
members of the room sending keys when they see the join. Instead of spamming decryption keys at the joined
user, or worse: missing the join and not sending anything, the joiner is responsible for trying to locate
the keys themselves.

Conflicts are extremely easy to manufacture, however the feature making it easy to form conflicts is needed
in order to protect the event's metadata. The conflict resolution algorithm can additionally be easily
abused (ie: sending a timestamp for the year 4025 to force the room name to never change), however at that
point the room is making it harder on itself to change over time.

Protocol-critical events are still unencrypted, however this is required given it is impractical to give
servers specialized devices of their own at this time. A peer-to-peer world might solve this problem in
a different way, considering the servers are devices which can receive decryption keys.

This MSC prioritizes protection of the average room's metadata, which unfortuantely lends protection to
abusive or illegal rooms as well. Though this MSC does make it harder for trust & safety teams to identify
encrypted abusive rooms, there are other methods and approaches which teams can use to remove harmful
content from their servers. Those methods are not detailed here to keep the MSC on topic.

Clients won't be able to use helper APIs for complete protection of metadata, such as the `name` key on
[`/createRoom`](https://matrix.org/docs/spec/client_server/r0.6.1#post-matrix-client-r0-createroom). This
might lead to additional server load when the client hits
[`PUT /state`](https://matrix.org/docs/spec/client_server/r0.6.1#put-matrix-client-r0-rooms-roomid-state-eventtype-statekey)
though more intelligent processing of rate limits should make it easier for clients and servers to honour
the requests. For example, increased burst limits for the few minutes after a room is created.

This effectively breaks the room directory and [space summary API](https://github.com/matrix-org/matrix-doc/pull/2946)
as they use named fields for details such as the room name. Considering both APIs use the same shape,
as defined by [`/publicRooms`](https://matrix.org/docs/spec/client_server/r0.6.0#post-matrix-client-r0-publicrooms),
the proposal here is to include a new `encrypted_state` key which is an array of Stripped State events
for all `m.room.encrypted` state events. For example:

```json5
{
  "chunk": [
    {
      "aliases": ["#home:example.org"],
      "canonical_alias": "#home:example.org",
      "guest_can_join": true,
      "num_joined_members": 42,
      "room_id": "!room:example.org",
      "world_readable": true,
      "encrypted_state": [
        {"type": "m.room.encrypted", "state_key": "<string>", "content": {/*encrypted*/}},
        {"type": "m.room.encrypted", "state_key": "<string>", "content": {/*encrypted*/}},
        {"type": "m.room.encrypted", "state_key": "<string>", "content": {/*encrypted*/}}
      ]
    }
  ]
}
```

Other approaches such as deprecating `name`, `topic`, etc in favour of a `state` array are best considered
for other MSCs.

## Alternatives

We could send a regular room message with the state event content, then in the room state simply use the
regular event type and state key with a content of `{"encrypted": "$event_id"}`, however this leaks
state metadata still and requires the client to have visibility on a random message event. Further, it
is not easily enforced that the `$event_id` even exist. Variations on this idea such as using the event
ID in the state key and using `m.room.encrypted` for the `type` are subject to similar issues.

## Security considerations

Decryption keys would be sent to invited parties under this proposal. This is a risk if there are badly
behaving clients which populated room state (such as re-using a megolm session across regular messages
and room state), and specifies that someone not in a room can decrypt events without being a member of
the room. The primary expected risk here is that a malicious user might be using a well-behaved client
to leak aesthetic details of the room to other parties through invites: room operators should be careful
who they allow to send invites. This is a similar risk to [MSC3061](https://github.com/matrix-org/matrix-doc/pull/3061).

Users could be excluded from seeing what the room is about because no one will provide keys to decrypt
the events. This is considered an unlikely social risk.

Sole admins could lose the decryption keys for their own state events, prompting keyshare requests to
other non-empowered users which effectively gives them authority over the room state (they could decline
to provide keys). Room admins will still be able to send further state events which leverage the conflict
resolution algorithm outlined by this MSC, though the original state events are subject to the remainder
of the room agreeing to send keys appropriately.

For DMs and similiarly sized rooms, it's somewhat likely that all parties lose decryption keys, thus
making the room state effectively lost to time. This is a pre-existing issue in Matrix and best solved
by a user remembering the event contents to re-send them.

As mentioned in the early parts of this proposal, clients could encrypt and send events which are listed
as "critical" to the protocol. Clients must take care to *not* honour encrypted versions of these events
as they will likely be mismatched from how the server is treating the room.

Users leaving the room, either voluntarily or by force, can still decrypt the room state. This is unavoidable
given keys were given to them in the first place, and is the same risk as the room events themselves.
This MSC makes no specific recommendation for when to re-encrypt/rotate sessions outside of the guidelines
already present in the specification. For example, do not use a session after a user has left the room as
that user could theoretically acquire and decrypt a state event they weren't supposed to. Clients are
welcome to re-encrypt the entire room state with a new session after a member leaves the room, however
rate limits and practicality will come into question.

While encrypted state events are, well, encrypted, it is not proposed that implementations use this to
store credentials or secrets in room state: sensitive information can still be revealed with keyshare
requests, manual key exports/imports, etc. This MSC also has a number of places where keys are shared
with invited members rather than joined members, leading to a potential of exposure.

## Unstable prefix

While this MSC is not considered stable, clients should send both encrypted and unencrypted copies of
state events to the room. The conflict resolution algorithm applies to the decrypted set of events, which
ultimately means clients will pick up the most recent encrypted or unencrypted state event for that event
type.

No requirement to use namespaced prefixes is present due to `m.room.encrypted` already being a valid and
supported event type.
