# MSC4047: Send Keys

A common feature request is a room structure where most/all members are not aware of each other. Matrix
currently requires all senders to be aware of each other for routing purposes, making it difficult to hide
a user's subscription to the room.

The core principle of this problem is tracked as [issue #367](https://github.com/matrix-org/matrix-spec/issues/367),
though the exact semantics described by that issue are different from this proposal. Instead of limiting
membership visibility by power level, this MSC aims to introduce an ability for "external senders", with
an assumption that [MSC2753-style](https://github.com/matrix-org/matrix-spec-proposals/pull/2753) peeking
or other similar mechanism can be used to subscribe to the room without becoming a member.

External senders are accomplished with a "send key" in this proposal. A public key is published to the room
for event auth concerns, and a private key is sent to the desired senders. Anyone with that private key can
then send events into the room.

Dependencies:
* [MSC4046](https://github.com/matrix-org/matrix-spec-proposals/pull/4046)

## Proposal

*This MSC is done entirely in context of a future room version, due to event auth and redaction algorithm
changes.*

A simple public/private key pair is used as an additional authentication mechanism for events in a room.
The public portion of that key pair is persisted to the room as `m.room.send_key`, and the private
portion is shared out of band from the room. `m.room.send_key` MUST have an empty string as a `state_key`,
but can contain multiple keys under `content`. The use of a single event type is to avoid complications
with both event authorization and state resolution[^1].

**TODO**: Decide on default key pair type. Ed25519 keys would probably be fine?

An `m.room.send_key` looks as such:

```jsonc
{
  // irrelevant fields not shown
  "type": "m.room.send_key",
  "state_key": "",
  "content": {
    "ed25519:efgh": "<unpadded base64 encoded public key>"
  }
}
```

`m.room.send_key` retains all `content` upon redaction, as otherwise event authorization would fail when
the key is used. Invalidating keys is covered later in this proposal.

A state event naturally inhibits who is able to actually (re)generate a send key. It is suggested that
servers update their default power level templates for new rooms to include the `m.room.send_key` state
event as only available to "room admins", or at least the same as `m.room.join_rules`.

Events using a send key are signed by that send key:

```jsonc
{
  // irrelevant fields not shown
  "type": "m.room.message",
  "sender": "@alice:example.org", // presumed to not be in the room at the time
  "content": {
    "msgtype": "m.text",
    "body": "Hi"
  },
  "signatures": {
    "example.org": {
      "ed25519:abcd": "<sender signature, as required by auth rules>"
    },
    "$sendKeyEventId": {
      "ed25519:efgh": "<signature with send key>"
    }
  }
}
```

This implies 3 things:

1. The sender has access to the private key.
2. The sender knows the event ID of the `m.room.send_key` event.
3. The sender is capable of signing a fully-formed PDU to prevent forgery attempts (see "Security
   Considerations" section)

The first and second items are covered by the "Distribution of send keys" section in this proposal,
and the last item is covered by the new `/make` and `/send_pdu` APIs introduced later.

With respect to [event authorization](https://spec.matrix.org/v1.8/rooms/v10/#authorization-rules),
events use a send key when their `signatures` include a key starting with `$`. That key MUST appear
as in the event's `auth_events` and MUST be a state event of type `m.room.send_key`, with empty state
key. If the event is not referenced or does not point to the send key state event the event is rejected.
If the referenced send key state event does not contain the key ID being used, or the signature fails
verification, the event is rejected.

Note that as part of [receiving a PDU](https://spec.matrix.org/v1.8/server-server-api/#checks-performed-on-receipt-of-a-pdu)
the server already checks 3 conditions:

1. The event passes based upon its `auth_events`.
2. The event passes based upon the state prior to its own change (ie: a send key state event is not
   sent using a new key only it contains).
3. The event passes based upon the current state of the room, which may be different from #1 and #2,
   otherwise it is [soft-failed](https://spec.matrix.org/v1.8/server-server-api/#soft-failure).

The first two conditions are covered above where we say an event using a send key *must* reference a
valid send key, and have a valid accompanying signature. The third condition we cover with an additional
note to say that if the referenced key ID (regardless of event ID) fails the signature verification
using the current `m.room.send_key` state event then the event is soft-failed. This could be because
the key has been removed from the state event or the key itself changed.

Note that there are no rules to prevent a key from being regenerated. Preventing in-place changes to
keys is trivial with authorization rules, however there's not sufficient reason to actually prevent
the behaviour. Whether changing a key in-place or removing the old key before adding a new key, the
new `m.room.send_key` state event becomes current and causes use of the previous key to be soft-failed.

**OPEN QUESTION**: How interested are we in guaranteed history? If a bunch of events are sent using a
send key and that key is later regenerated/removed, a new server joining the room would ultimately
soft-fail all of those events. An "easy" fix to this would be to never allow send keys to change or
be removed, but then there's a gaping security hole in the room when the private key gets leaked.

The event authorization changes are covered more verbosely later in this proposal, in addition to a
description of how power levels work with respect to sent events.

### Distribution of send keys

After a user has generated a key and populated a relevant `m.room.send_key`, they need to actually
send the private key to an external sender (or several). This is done over encrypted
[to-device messages](https://spec.matrix.org/v1.8/client-server-api/#send-to-device-messaging),
shielding the private key material from anyone along the send path. The following `m.send_key` object
is encrypted using Olm before being sent, exactly like [`m.room_key`](https://spec.matrix.org/v1.8/client-server-api/#mroom_key).

```jsonc
{
  "type": "m.send_key",
  "content": {
    "room_id": "!room:example.org", // room ID where the `m.room.send_key` event is
    "event_id": "$eventIdOfSendKeyInRoom", // `m.room.send_key` event ID
    "keys": { // the subset of keys the receiver is getting
      "ed25519:efgh": "<unpadded base64 private key>"
    },
    "servers": [ // resident servers which can be useful for sending an event later
      "example.org"
    ]
  }
}
```

It is up to the sender to determine which of the receiver's devices will ultimately get the keys, and which
ones. Typically, it's expected that Olm sessions will be established with all of a target user's devices and
keys will be sent to all of them. Note that a receiver can trivially gossip the keys to its other devices if
it so chooses.

The receiver is then responsible for persisting the send key(s) and associated information. Secure storage
is recommended.

### Using send keys

Private keys are generally going to be kept within a client's secure storage, which is a bit of a problem
if the server needs to use that private key to send an event on its behalf. This MSC relies on the endpoints
described by [MSC4046](https://github.com/matrix-org/matrix-spec-proposals/pull/4046) to send PDUs into rooms.

Between the `GET /make_pdu` and `PUT /send_pdu` calls, the client would use the private key to sign the PDU
it constructed, making it legal to send into the room.

### Event authorization changes

*This section comprehensively covers the changes discussed in the MSC, duplicating details as needed.*

The following definitions are referenced by this section:

* [Authorization rules](https://spec.matrix.org/v1.8/rooms/v10/#authorization-rules)
* [Auth events selection algorithm](https://spec.matrix.org/v1.8/server-server-api#auth-events-selection)
* ["Checks performed upon receipt of a PDU"](https://spec.matrix.org/v1.8/server-server-api/#checks-performed-on-receipt-of-a-pdu)

Note that throughout the changes described below there may be more implementation efficient methods. Specifically
in Change 3 a server can likely optimize the new rules down a bit, but for specification purposes we need to
describe the complete machine operation.

**Change 1**: Prevent `signatures` from containing not-`m.room.send_key` event IDs, and ensure Rule 2.2 passes
when `m.room.send_key` is referenced. This change also confirms that the send key signatures are valid. A
desirable characteristic of this change is that both multiple send keys and send key events can be used to
authorize an event - a failure in any one of those signatures causes the whole event to become rejected.

The auth events selection algorithm is appended with:

> * The current `m.room.send_key` event, if used.

The following new rules after Rule 2.4 are appended under Rule 2 of the authorization rules:

> 2. [...]
>    5. If entries matching each of the keys under `signatures` prefixed with `$` are not present, reject.
>    6. If any of the entries from 2.5 do not reference `m.room.send_key` with empty string state key, reject.

The text "Events must be signed by the server denoted by the `sender` property." is appended with:

> If events have "send key" signatures (Rules 2.5 and 2.6), all of those signatures must be valid per the
> `m.room.send_key` events they reference.

**Change 2**: Ensure events referencing old/regenerated send keys are soft-failed.

Check 6 of "checks performed upon receipt of a PDU" is clarified as such:

> With respect to Check 6, events using "send key" signatures must have a valid signature when using the current
> `m.room.send_key` state event in the room, otherwise it is "soft failed".
>
> For example, if the current `m.room.send_key` event ID is `$current`, and the following signature is present:
>
  ```json
  {
    "$event": {
      "ed25519:abcd": "<signature>"
    }
  }
  ```
>
> then the signature for `ed25519:abcd` must be valid when compared against `m.room.send_key`.

The signature validation is expected to be defined as part of the `m.room.send_key` event. Namely, for a given
key ID:

1. If `content` does not contain that key ID, signature fails.
2. If the public key from `content` doesn't verify the signature, signature fails.

Note that ["checking for a signature"](https://spec.matrix.org/v1.8/appendices/#checking-for-a-signature) may
require an update on Step 3 to account for `m.room.send_key` as a place to "look up" verification keys.

**Change 3**: Allow the `sender` to be considered "in the room" for purposes of event auth, provided they aren't
banned or explicitly in the `leave` state.

Immediately prior to Rule 5 of the authorization rules, the following new rules are inserted:

> 5. If the `sender`'s current membership state is `ban`, reject.
> 6. If the `sender` has a current `m.room.member` state event with `membership` of `leave`, reject.
> 7. If the event uses "send keys" (see Rules 2.5 and 2.6), consider the `sender` as joined for rules which follow.
> 8. [unchanged] If the `sender`'s current membership state is not `join`, reject.

(Rule 5 becomes Rule 8 with these additions)

Note that [Server ACLs](https://spec.matrix.org/v1.8/server-server-api/#server-access-control-lists-acls) still
apply to events using send keys. Server ACLs are not currently part of event authorization, but do apply at a
transport level.

**Change 4**: Prevent send keys from changing/adding/removing send keys as a safety measure.

Immediately after Rule 3 of the authorization rules, the following rule is inserted:

> 4. If `type` is `m.room.send_key`:
>    1. If the event uses "send keys" (see Rules 2.5 and 2.6), reject.

## Potential issues

The potential issues with this MSC are primarily security considerations.

## Alternatives

Pseudo IDs of some variety, or senders-as-keys, might be an easier/different way to solve this MSC's
problem scope.

## Security considerations

A major consideration is what the private key actually allows an attacker to do if they get their hands
on it. Matrix also uses eventual consistency which allows for events using an "old" send key to potentially
be surfaced. The soft failure and rejection characteristics are primarily designed for these two problems.

This MSC requires that the send key signature cover the entire event, just as the origin server's
signature does. If the signature were to instead cover a subset of the event, the event contents could
be easily duplicated with distinct event IDs. This creates an easy spam vector: if the signature covered,
for example, `sender`, `room_id`, and `content` then a malicious sender/server could simply copy/paste
the send key signature and change other details like `prev_events` to flood the room with distinct events
at nearly no cost to them. Instead, by covering the whole event the worst an attacker can do is send
the exact same event ID over and over, which quickly becomes pointless.

Note that the spam vector here is subtly (and dangerously) different to a normal spam vector in Matrix.
It's currently possible for a malicious server to quickly generate billions of events with distinct IDs,
but critically it's possible to kick that server/sender out of the room in a multitude of ways, blocking
further spam from reaching the room. With send keys though, the server does not need to be a member of
the room to spam it. Those servers are reliant on another member server to send their events though, and
therefore can be easily rate limited. A member server colluding with an external server to bypass rate
limiting might not be easily detected by human moderators/admins, and potentially impossible via monitoring
at the federation level. There is not currently a proposed solution to this particular problem.

One option might be to have the "delivering server" of an event using send keys to additionally sign the
event itself, but if an event is coming over `/backfill` or similar then the signature from the original
server which delivered it to the room would be lost, making automated monitoring difficult.

This MSC does not consider participation and "dealing with the DAG" as sufficient barriers to spam. Nor
does it consider invites (both explicit and implicit through room alias knowledge) as a reasonable measure
against having malicious servers in a room. A server can always *become* malicious after proving its
innocence.

To prevent sender-specific spam, this MSC ensures it does not prevent a user from being banned or server
being ACL'd if it attempts to evade the user bans, for example.

Keys stored in `m.room.send_keys` should also be rotated frequently enough to reduce exposure risk. Every
few days should be sufficient for most use cases. Note that rotating the key does not prevent an old key
from being used, as discussed earlier in this section, but does cause the sent event to be soft-failed.

## Unstable prefix

While this proposal is not incorporated into a stable room version, implementations should use `org.matrix.msc4047`
as an unstable room version, using [room version 11](https://spec.matrix.org/v1.8/rooms/v11/) as a base.
The event type `m.room.send_key` should additionally be prefixed as `org.matrix.msc4047.send_key` in that
room version for clarity during development.

### Test vectors

**TODO**: "This event produces this event ID" sort of idea.

## Footnotes

[^1]: When auth events can reference or affect each other there is a potential unbreakable loop. This MSC
makes efforts to ensure that `m.room.send_key` cannot be used to change itself, but this doesn't always work
for auth events spread over multiple events. Role-Based Access Control (RBAC) for example is best represented
as multiple state events which can (theoretically) modify each other. If Alice is trying to use their role to
modify Bob's role, but Bob is trying to use their role to prevent Alice from modify that same role, who wins?
There's some things we can do in the event design to prevent this, such as define a "power level" alongside
the role, but sometimes it's just easier to copy `m.room.power_levels` and cram everything into a single event.
This MSC takes the route of cramming everything into a single event, and blocks attempts to use send keys to
add/change/remove send keys for safety.
