# MSC3757: Restricting who can overwrite a state event.

## Problem

Currently, there are two main restrictions on who can overwrite a state event, enforced by rules
7 and 8 of the [authorization rules](https://spec.matrix.org/latest/rooms/v11/#authorization-rules):

 * Only users with a power level greater than or equal to the "required power level" for a state
   event type may send state events of that type.
 * State events with a `state_key` that equals a user ID may be overwritten only by the user whose
   ID matches the state key.

With these restrictions, only a single piece of state for any state event type may have its write
access limited to a particular user (the state event whose `state_key` is set to the ID of the user
who has write access to it).

This is problematic if a user needs to publish multiple state
events of the same type in a room, but would like to set access control so
that only they can subsequently update the event. An example of this is if a
user wishes to publish multiple live location share beacons as per
[MSC3489](https://github.com/matrix-org/matrix-spec-proposals/pull/3489) and
[MSC3672](https://github.com/matrix-org/matrix-spec-proposals/pull/3672),
for instance one per device.
They will typically not want other users in the room to be able to overwrite the state event,
so there ought to be a mechanism to prevent other users from doing so.

## Proposal

In a future room version,
**if a state event's `state_key` *starts with* a user ID followed by an underscore, only the user
with that ID or users with a higher power level then them may overwrite that state event.**
This is an extension of the current behaviour where state events may be overwritten only by users
whose ID *exactly equals* the `state_key`.

As the spec currently enforces [a size limit of 255 bytes for both user IDs and state keys](
https://spec.matrix.org/unstable/client-server-api/#size-limits),
the size limit on state keys is increased to **511 bytes** to allow prefixing any currently-valid
state key with a maximum-length user ID (and a separator character).
The size of a state key suffix after a leading user ID and the separator character is limited to
**255 bytes** so that any such suffix may follow any user ID without the complete state key
ever surpassing the total state key size limit.
Similarly, the size of a state key without a leading user ID is limited to **255 bytes** so that any
state key without a leading user ID may be given one without ever surpassing the total size limit.

Users with a higher power level than a state event's original sender may overwrite the event
despite their user ID not matching the one in event's `state_key`. This fixes an abuse
vector where a user can immutably graffiti the state within a room
by sending state events whose `state_key` is their user ID.

Practically speaking, this means modifying the
[authorization rules](https://spec.matrix.org/v1.2/rooms/v9/#authorization-rules) such that rule 8:

> 8. If the event has a `state_key` that starts with an `@` and does not match the `sender`, reject.

becomes:

> 8. If the event has a `state_key`:
>    1. If the `state_key` starts with an `@`:
>       1. If the prefix of the `state_key` before the first `_` that follows the first `:` (or end
>          of string) is not a valid user ID, reject.
>       1. If the size of the `state_key` without its leading user ID is greater than 256 bytes, reject.
>       1. If the leading user ID does not match the `sender`, and the `sender`'s power level is not
>          greater than that of the user denoted by that ID, reject.
>    1. Otherwise, if size the `state_key` is greater than 255 bytes, reject.

Note that the size limit of 256 bytes after a leading user ID includes the separating `_`.

No additional restrictions are made about the content of the `state_key`, so any characters that
follow the `sender` + `_` part are only required to be valid for use in a `state_key`.

For example, to post a live location sharing beacon from
[MSC3672](https://github.com/matrix-org/matrix-spec-proposals/pull/3672)
for one of a user's devices:

```json=
{
    "type": "m.beacon_info",
    "state_key": "@stefan:matrix.org_{deviceid1}", // Ensures only the sender or higher PL users can update
    "content": {
        "m.beacon_info": {
            "description": "Stefan's live location",
            "timeout": 600000,
            "live": true
        },
        "m.ts": 1436829458432,
        "m.asset": {
            "type": "m.self"
        }
    }
}
```

## Potential issues

### Incompatibility with domain names containing underscores

Although both [the spec](https://spec.matrix.org/unstable/appendices/#server-name)
and [RFC 1035 §2.3.1](https://www.rfc-editor.org/rfc/rfc1035#section-2.3.1)
forbid the presence of underscores in domain names,
there noneless exist resolvable domain names that contain underscores.
The proposed auth rule for parsing a leading user ID from an underscore-separated state key would
fail on such domain names.

Possible solutions include:
- using a different character to terminate a leading user ID in state keys. That character must be
  one known to be absent from domain names in practice, and must also not be any character that
  the spec allows to appear in a server name.
- refining the proposed auth rule for parsing a leading user ID such that it does not fail on domain
  names that contain an underscore. One way to achieve this is to leverage the absence of
  underscores from top-level domains.

## Alternatives

### Variable event types

[MSC3489](https://github.com/matrix-org/matrix-spec-proposals/pull/3489)
and [MSC3672](https://github.com/matrix-org/matrix-spec-proposals/pull/3672)
originally proposed that the event type could be made variable,
with an ID appended to each separately posted event so that each one could
separately be locked to the same user ID in the `state_key`.  However, this is
problematic because you can't proactively refer to these event types in the
`events` field of the `m.room.power_levels` event to allow users to post
them - and they also are awkward for some client implementations to
manipulate.

### Event ownership flag

An earlier draft of this MSC proposed putting a flag on the contents of the
event (outside of the E2EE payload) called `m.peer_unwritable: true` to
signify ownership of the containing event by its `sender`, which would indicate
if other users were prohibited from overwriting the event or not.  However, this
unravelled when it became clear that there wasn't a good value for the `state_key`,
which needs to be unique and not subject to races from other malicious users.
By scoping who can set the `state_key` to be the user ID of the sender, this problem
goes away.

One way to satisfy the need for unique and non-racing state keys with an event ownership flag
is to key state events by not only their event type and `state_key`, but also their `sender`
when the event ownership flag is set.
This would also provide state ownership semantics that could not by overwritten by any other user,
as an event's owner would be determined implicitly from whoever sent the event,
instead of from an explicit field set in the event.
Notably, this applies to high PL users as well, leaving them with no way to replace state events
owned by lower PL users. Administration of such events would then be limited to redacting them.

With this change to state keying, endpoints for setting/retrieving state events would need to
allow specifying the owner of the event to set/retrieve.
It would also require server implementations to change how they key state events.

### Multi-component state keys

[MSC3760](https://github.com/matrix-org/matrix-spec-proposals/pull/3760)
proposes to include a dedicated `state_subkey` as the third component of what
makes a state event unique.
As an extension to this idea, a comment in [the discussion of this MSC](
https://github.com/matrix-org/matrix-spec-proposals/pull/3757#issuecomment-2099010555)
proposes allowing `state_key` to be an array of strings.
With either proposal of multi-component state keys, state events could be scoped to an owning user
by setting one of the components of the state key (either the `state_subkey` or an element of an
array `state_key`) to a user ID, instead of by prefixing the `state_key` string with a user ID.
Doing so would avoid having to parse user IDs out of `state_key` strings,
and would avoid needing to increase the size limit of the `state_key` field to give it enough room
to contain a leading user ID.
However, allowing state keys to be multi-component would change state key comparison from being a
string comparison to an array-of-strings comparison, which could be costly for existing server
implementations to migrate to.

### Owning user ID field

A comment in [the discussion of this MSC](
https://github.com/matrix-org/matrix-spec-proposals/pull/3757#discussion_r1103877363)
proposes an optional top-level field for both state and non-state events that designates ownership
of the containing event to a particular user.
This would provide ownership semantics for not only state events, but also message events, which may
be used to restrict event replacements / redactions to only the designated owner of an event.
However, it remains to be decided how using this top-level field for state events should affect
state resolution; namely, whether it is possible to set multiple events with the same `state_key`
but different owners.

## Security considerations

This change requires a new room version, so will not affect old events.

As this changes auth rules, the possibility of new attacks on state resolution must be considered.
For instance, if a user had higher power level at some point in the past, will they be able to
somehow abuse this to overwrite the state event, despite not being its owner?

When using a leading user ID in a `state_key` to restrict who can write the event, the character to
terminate the leading user ID was deliberately chosen to be an underscore, as it is not
allowed in [any form of server name](https://spec.matrix.org/v1.11/appendices/#server-name)
(either a DNS name or IPv4/6 address, with or without a numeric port specifier) and thus cannot be
confused as part of the server name of a leading user ID (with one caveat mentioned as a
[potential issue](#incompatibility-with-domain-names-containing-underscores)).
A pure prefix match will **not** be sufficient,
as `@matthew:matrix.org` will match a `state_key` of form `@matthew:matrix.org.evil.com:id1`.

This changes auth rules in a backwards incompatible way, which will break any
use cases which assume that higher power level users cannot overwrite state events whose
`state_key` is a different user ID.  This is considered a feature rather than a bug,
fixing an abuse vector where users could send arbitrary state events
which could never be overwritten.

## Unstable prefix

While this MSC is not considered stable, implementations should apply the behaviours of this MSC on
top of room version 10 or higher as `org.matrix.msc3757`.

## Dependencies

None
