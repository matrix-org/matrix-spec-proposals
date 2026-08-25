# MSC4529: Client-side profile overrides

People are often known by names they don't choose for themselves. A user may want to see "Mum"
rather than "Sarah", to tell apart two colleagues who both call themselves "Alex", or to keep a
familiar name for a contact who has renamed themselves to something unrecognisable. Pictures matter
for the same reason. A user is often picked out of a timeline by their avatar before their name is
read, but many people set no avatar at all, leaving rows of identical placeholders, and others use
an image shared with a dozen people or one that changes every week. Giving somebody a picture, as an
address book does with a contact photo, is as useful as giving them a name, and it survives their
next change.

Address books and other chat apps let their user relabel a contact privately. Matrix has no
equivalent. A user can change their own profile, but not how somebody else appears to them. Clients
offering this feature today must store the labels locally, so they are lost on reinstall and never
reach the user's other devices.

This proposal introduces an account data event in which a user records the profile fields they wish
to see in place of the real ones, facilitating the usage of private labels between the user's clients.

## Proposal

A new global account data event `m.profile_overrides` is introduced. In `content`, it maps user IDs
to objects of profile field names and the values to display for them:

```json5
{
  "type": "m.profile_overrides",
  "content": {
    "@sarah:example.org": {
      "displayname": "Mum"
    },
    "@alex:example.com": {
      "displayname": "Alex (accounting)",
      "avatar_url": "mxc://example.org/SEsfnsuifSDFSSEF",
      // Fields set to null are displayed as though absent
      "m.tz": null
    }
  }
}
```

The field names are those of the [profile](https://spec.matrix.org/v1.18/client-server-api/#profiles):
`displayname`, `avatar_url`, `m.tz`, and any other extended profile field. A value MUST have the
type that field would have in a real profile, except that `null` means the user has no value for
that field. Clients MUST ignore entries whose key is not a valid
[user ID](https://spec.matrix.org/v1.18/appendices/#user-identifiers) and fields whose value is of
the wrong type, which leaves room to extend the event later. To remove an override, remove its key.
Clients SHOULD drop a user's entry rather than leave an empty object behind.

The [`m.profile_fields`](https://spec.matrix.org/v1.18/client-server-api/#mprofile_fields-capability)
capability restricts which fields a user may change in their own profile. It does not constrain
overrides. An override is never sent to the server as profile data, so a client MAY override any
field, including one the server manages on the overridden user's behalf.

Where a client displays a profile field for which an override exists, it SHOULD display the override
in place of the value it would otherwise use, whether that came from the user's profile or from an
`m.room.member` event. This applies in every room and everywhere a profile is shown, including
[room names and avatars](https://spec.matrix.org/v1.18/client-server-api/#calculating-the-display-name-for-a-room)
derived from members.

A user may set a different display name and avatar in each room, and an override replaces all of
them. This is intended. Overriding a user's profile is a choice to see them the same way wherever
they appear, and that uniformity is the point of the feature.

Overrides MUST NOT affect anything the client sends. The text of a
[mention](https://spec.matrix.org/v1.18/client-server-api/#user-and-room-mentions) or reply
fallback, and all other outgoing content, MUST use the real profile, so that a private label is
never revealed to the room.

Clients [disambiguate](https://spec.matrix.org/v1.18/client-server-api/#calculating-the-display-name-for-a-user)
colliding display names by appending the user ID. A client MAY treat an overridden name as
unambiguous, since the user chose it themselves, provided the real user ID remains discoverable
elsewhere, such as on the user's profile view.

This is a client-to-client mechanism carried over the existing
[account data](https://spec.matrix.org/v1.18/client-server-api/#client-config) endpoints; servers
need no knowledge of this proposal.

The server never needs to read the event, so it can be encrypted. [MSC4483] defines encrypted
account data, in which the content of designated events is encrypted with a key held in secret
storage. If it is accepted, this proposal declares `m.profile_overrides` encryptable, and a client
MAY store the event in the encrypted form:

```json
{
  "type": "m.profile_overrides",
  "content": {
    "encrypted": {
      "iv": "...",
      "ciphertext": "...",
      "mac": "..."
    }
  }
}
```

The plaintext is the `content` described above, and encryption changes nothing else in this
proposal. A client implementing it without [MSC4483] finds no key in the encrypted form that is a
valid user ID, so under the rules above it ignores the event and displays real profiles, as though
it implemented neither proposal.

## Potential issues

The event is rewritten in full for every change, so simultaneous edits from two clients can lose one
of them. This is the same race [`m.direct`](https://spec.matrix.org/v1.18/client-server-api/#mdirect)
has, and is tolerable for the same reasons: such writes are rare and user-initiated. A user with
many overrides also ends up with a large event. Each entry is bounded by the limits the
specification already places on a profile, 255 bytes per key and 64 KiB for the profile as a whole,
so the event grows with the number of users overridden rather than without limit. In practice the
feature is used for a handful of users at a few dozen bytes each.

An override is a snapshot and does not track later changes to the real profile. That is largely the
point, but it does mean a user will not notice when the underlying name changes.

Clients that do not implement this proposal display real profiles, which is a safe degradation,
though a user running two clients may then see different names in each.

If the event is encrypted under [MSC4483], a client implementing this proposal but not that one
cannot read the overrides. Worse, if the user edits an override on such a client, it rewrites the
event in plaintext and every encrypted override is lost. Encryption also ties the event to secret
storage, so a user who resets their identity loses their overrides.

## Alternatives

Clients could continue to store overrides locally, as they do today. This needs no specification,
but the labels are lost on reinstall and do not reach the user's other devices, which is the problem
being solved.

One event type per overridden user, such as `m.profile_override.@alice:example.org`, would avoid the
read-modify-write race and allow a single override to be updated in isolation. It also embeds a user
ID in an event type, which is unlike anything else in the specification, and gives up the ability to
enumerate overrides. The race does not seem serious enough to justify that.

[MSC3015] and [MSC4431] apply the same idea to room state, storing personal overrides as room
account data whose content mirrors the state event being overridden. [MSC3015] is generic, keying
the account data on `override.` followed by the state event type, so any state event could in
principle be overridden; it proposes to gate this behind an allowlist of `m.room.name`,
`m.room.avatar`, `m.room.topic` and perhaps `m.room.pinned_events`. [MSC4431] covers room names
alone, as `m.room.name.private`. They personalise *rooms*, where this proposal personalises *users*,
and neither supersedes the other. A client may implement any of them alone or all of them together,
and a user may reasonably want a private name for a room and a private name for a user at the same
time. [MSC3015] even lists `m.room.member` among the state types its allowlist could
admit, but defers it pending the extensible profiles of [MSC1769], so the two fit together directly.

This proposal does not extend either to `m.room.member`, because a profile is not room state. A room
has a natural per-user container in its room account data; a user has none. Per-room storage would
therefore repeat each override in every room shared with that user, need a further write on joining
another, and leave the same user labelled inconsistently wherever a copy was missed. `displayname`
and `avatar_url` belong to the user rather than to any room, and extended profile fields such as
`m.tz` have no room state to mirror at all. A single global map keyed by user ID
follows the shape of the thing being overridden, and leaves room-level personalisation to the
proposals above.

[MSC4441] stores private free-text notes about users in a global account data map of the same
shape, and lists name and avatar overrides as a possible later extension. The two do different
jobs. An override replaces something a user may declare about themselves: a name, an avatar, a
timezone. A note is something others say about a user that the user would not declare, so it
corresponds to no profile field, and inventing one for it would let a user pre-write a note
about themselves. Each event therefore mirrors the thing it describes: profile fields here,
annotations there. A client may implement either or both.

Finally, servers could rewrite profiles before serving them, which would extend the feature to
clients that do not implement it. That would require every server to participate. It would also hide
the real profile from clients that need it, such as when composing a mention, and put a
presentational concern in the server.

## Security considerations

The user's homeserver can read their account data, so unless the event is encrypted under
[MSC4483], the labels they choose are visible to a server administrator, and a label like
"therapist" or "work" gives away plenty. Clients SHOULD NOT present the feature as private from the
homeserver in that case. Encryption narrows the exposure but does not remove it: an overridden
`avatar_url` points at unencrypted media, and the server can see it being fetched. The overridden
user learns nothing either way: nothing is sent to them and no room state changes.

## Unstable prefix

While this MSC is not considered stable, `m.profile_overrides` should be referred to as
`org.matrix.msc4529.profile_overrides`. Clients SHOULD prefer the stable event type where both are
present, and may use it as soon as this proposal is accepted, since no feature negotiation is
involved. [MSC4483] uses the event type as the encryption info, so ciphertext created under the
unstable type must be re-encrypted when migrating to the stable one.

## Dependencies

None. The use of [MSC4483] is optional and nothing here waits on its acceptance.

  [MSC1769]: https://github.com/matrix-org/matrix-spec-proposals/pull/1769
  [MSC3015]: https://github.com/matrix-org/matrix-spec-proposals/pull/3015
  [MSC4431]: https://github.com/matrix-org/matrix-spec-proposals/pull/4431
  [MSC4441]: https://github.com/matrix-org/matrix-spec-proposals/pull/4441
  [MSC4483]: https://github.com/matrix-org/matrix-spec-proposals/pull/4483
