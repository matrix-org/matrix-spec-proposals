# MSC3931: Push rule condition for room version features

Currently it is not possible to have per-room-version push rules, making it potentially difficult
to roll out push rules which rely on events being in a specific room version. An example of this
is [MSC1767](https://github.com/matrix-org/matrix-spec-proposals/pull/1767) (Extensible Events) -
a new room version is defined for "extensible" events to be sent in, and to help enforce that they
should only be respected in that specific room version it'd be ideal to toggle the push rules on
only in a suitable room version.

A challenge is that changing push rule conditions can be difficult in the spec and implementation
process, and room versions are non-linear and further can't be guaranteed to have certain functionality
in them.

This proposal introduces "feature flags" in the context of a new push rule condition to better check
what is possible in a given room version. An example implementation of this, for extensible events,
is [MSC3932](https://github.com/matrix-org/matrix-spec-proposals/pull/3932).

## Proposal

As mentioned in the introduction, a new [push rule condition](https://spec.matrix.org/v1.4/client-server-api/#conditions-1)
is introduced to cover feature flag checks in room versions: `room_version_supports`. This condition
has a single `feature` parameter to compare against the room version an event appears in.

The value of `feature` is a [namespaced](https://spec.matrix.org/v1.4/appendices/#common-namespaced-identifier-grammar)
string to represent a feature flag of a room version. These feature flags are arbitrary and intended
to only ever be defined for the purposes of push rule conditions: they serve no other purpose. Each
room version would specify which "push rule feature flags" it supports, allowing servers to easily
compare supported flags versus the push rule condition.

An example condition would be:

```json5
{
  "kind": "room_version_supports",
  "feature": "org.example.custom_room_version_feature_name"
}
```

Unknown feature flags cause the condition to fail, or return `false`, preventing that rule from
executing (as if it was disabled).

Each feature flag can additionally have its own rules for processing, such as what happens on push
rules which *do not* specify a `room_version_supports` condition. This is able to be supported because
implementations aware of the flag would be able to support such a behaviour, and those which don't
would end up resolving the push rule to `false` anyways.

This proposal does not define any feature flags itself - this is a task left to other MSCs.

## Potential issues

Push rule conditions are always an "AND" condition, making it potentially worthwhile to have this new
feature flags condition to support an array of strings instead. This would allow a push rule to say
"any of these flags", though it is unclear if a theoretical push rule would want that specific feature
instead of "all of these flags".

Instead of defining an array, this proposal recommends that duplicated push rules be created to cover
the "OR" case. For example:

```json5
{
  "conditions": [
    { "kind": "event_match", "key": "type", "org.example.event" },
    { "kind": "room_version_supports", "feature": "org.example.first_feature" }
  ]
}
```
```json5
{
  "conditions": [
    { "kind": "event_match", "key": "type", "org.example.event" }, // unchanged
    { "kind": "room_version_supports", "feature": "org.example.second_feature_flag" }
  ]
}
```

## Alternatives

None discovered, though a more sophisticated system is likely possible.

## Security considerations

No new considerations are relevant.

## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc3931.room_version_supports`
as the `kind`.
