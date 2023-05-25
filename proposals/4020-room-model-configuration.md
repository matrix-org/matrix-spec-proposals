# MSC4020: Room model configuration

The room model in Matrix is defined by a [room version](https://spec.matrix.org/v1.7/rooms/), where
standardized algorithms define how servers accept events, enforce permissions, and generally keep
messages flowing between legitimate members.

An upcoming proposal (**TODO@TR: Link**) aims to introduce a concept of running the majority of room
version algorithms client-side rather than server-side, provided the room is encrypted. Due to needing
an encrypted room, not all rooms will want to run the room client-side, but equally it would be messy
if client-side room versions and server-side room versions existed, doubling our specification size.

This proposal defines a feature-flagging system in the `m.room.create` state event to control aspects
of the room model. While none of the flags themselves are defined in this MSC, the aim is to have the
event auth rules (and similar) *optionally* run client-side instead of server-side while also laying
groundwork for future MSCs which might benefit from this sort of change.

A secondary use-case for this flagging system may be [MSC2812](https://github.com/matrix-org/matrix-spec-proposals/pull/2812),
where the proposal already states that not all rooms will need such a permissions structure. The MSC
currently asks that a `.1` suffix be used on the room version to indicate support for roles, however
this has scalability concerns when paired with something else like client-side event auth. For example,
we might say that a `.2` suffix indicates support for client-side event auth, making a server support
a hypothetical `10.1.2` room version. Then we add a feature identified by a `.3` suffix and so on until
the version string becomes a mile long, not to mention that it's unclear if `10.2.1` and `10.1.2` are
the same or different.

## Proposal

The `m.room.create` event content gains an additional field, `model`, being an object mapping a string
key to boolean value. For example:

```jsonc
{
  // irrelevant fields not shown
  "type": "m.room.create",
  "state_key": "",
  "content": {
    "room_version": "11",
    "model": {
      "client_side": true
    }
  }
}
```

The new field is automatically protected from redaction under [MSC2716](https://github.com/matrix-org/matrix-spec-proposals/pull/2176),
specified from [room version 11](https://github.com/matrix-org/matrix-spec-proposals/pull/3820). For
clarity though, all fields under `model`, including `model` itself, are protected from redaction.

**TODO@TR: This MSC can't exist before v11 (opt2).**

It is not possible to use flags on room versions which do not specifically support them. A client-side
event auth flag, for example, will need to specify how that works in practice and cannot be backported
because room versions are frozen algorithmically once written down.

This is also the reason why the flags are not namespaced: the `room_version` is already namespaced and
`model` is an extension of that version string. Unstable (and stable) room versions will need to specify
which flags, if any, they support. Unknown flags for the room version are simply ignored.

For simplicity, every flag *must* have a default value, and that default value is used when the flag
isn't specified or isn't a boolean. When `model` is not present or not an object, the default also applies
to all flags in that room version.

It is expected that the specification will continue to build stable room versions on top of other stable
room versions somewhat linearly, despite room versions themselves having no particular order. This should
mean that flags introduced in one room version carry through as considerations for the next (ie: once
client-side event auth is adopted, it's adopted for all future room versions too).

The behaviour of each flag is baked into the room version algorithms themselves.

This MSC does not define any particular flags for room versions to use, but does acknowledge that the
following MSCs do (as of writing):
* **TODO@TR: Should really write that client-side event auth MSC.**

This MSC does require a room version change itself to support the condition described earlier: unknown
flags are treated as unknown room versions entirely. Each MSC introducing a flag will additionally need
a new room version too, intentionally.

If none of the above makes sense, think of the flags as optional packages for a room version: "I want
v11 but with client-side auth and role-based permissions. I'll call it `v11+client_side+roles`".

Servers already communicate their list of supported room versions as part of the invite/join dance to
prevent servers which don't support the room version from participating. Nothing needs to change in that
approach because the room versions define which flags are possible: for a server to support v11 (for
example), it needs to already know that there's certain flags that can be set. Additionally, unknown
or otherwise invalid flags are ignored by the server, instead taking on default values, meaning that
if `model` is syntactically incorrect post-join then the server doesn't explode as a result.

## Potential issues

It's possible that ideas for flags will be incompatible, however this is no different than features
being incompatible and trying to land in a stable, assigned, room version. In creating the stable
room version, that MSC author will need to identify the conflict and resolve it. This may mean that
some flags cease to move on to future room versions as their functionality no longer serves a purpose.

This system is also difficult to explain without an actual example. **TODO@TR: Write that client-side
event auth MSC.**

This system requires a new MSC for each flag, however each flag is expected to need a new room version
anyways so it can change how rooms work.

## Alternatives

As mentioned in the introduction, we could specify such flags through the `room_version` field itself,
however this hits a couple challenges:
* The specification [didn't reserve](https://spec.matrix.org/v1.7/rooms/#room-version-grammar) characters
  outside of 0-9 and `.` for use by the specification. Theoretically this can be changed, however 32
  codepoints of length isn't a lot to work with either, making string formats like `11+client_side`
  impractical.
* Trying to stay within the existing grammar and assigning numbers to features leads to massive confusion
  and coordination problems. Each feature would end up with a numeric ID and encoded into the version
  string. For example, `11.1.2` being v11 with features 1 and 2. This is not a useful design.

Instead of trying to pack `room_version` with information, we break it out to a dedicated object that
can, in future, be made more extensible if needed. Maybe a flag has its own configuration information:
the schema can easily be altered to support `client_side: {num: 42}`, for example. For now though, we
just need booleans so we'll stick to that as a schema. A change to the schema would require a new room
version, but so would introducing a new flag.

We could also put the flags at the top level of `content` instead of under `models`, but this feels
messy.

## Security considerations

None applicable: servers already (should be) refusing to participate in rooms which have an unknown room
version. These flags are simply an extension of that room version and are strongly specified against the
room version string, making it possible for servers to know before they even join if they can participate.

## Unstable prefix

This MSC does not have any implementation requirements itself, though the MSCs which depend on it might.

Please see the dependent MSCs for unstable implementation details.

## Dependencies

This MSC requires [MSC2716](https://github.com/matrix-org/matrix-spec-proposals/pull/2176) to make things
a lot easier.
