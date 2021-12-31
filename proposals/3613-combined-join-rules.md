# MSC3613: Combinatorial join rules

[Join rules](https://spec.matrix.org/v1.1/client-server-api/#mroomjoin_rules) define what conditions
a user must meet in order to, well, join a room. With the current setup it is impossible to have more
than one rule active at a time, which makes it difficult to allow anyone from room X to join, but also
join is their knock was accepted. The room would instead have to choose which condition it favoured.

This proposal aims to introduce the smallest possible baseline for a slightly improved join rules
system, allowing for combinations of join rules to take effect. Alternative MSCs, like
[MSC3386](https://github.com/matrix-org/matrix-doc/pull/3386) instead seek to redesign the join rules
structure entirely. This proposal is intended to fill the gap while the more complex MSCs work out
their specifics.

## Proposal

In a new room version, we simply add an optional array to the
[`m.room.join_rules`](https://spec.matrix.org/v1.1/client-server-api/#mroomjoin_rules) event. The
existing behaviour of the `join_rule` key is kept, though has slightly modified behaviour per below.

The new array, `join_rules`, is simply an array which contains objects representing the `m.room.join_rules`
event content (minus the array itself - this does not recurse). The array acts as a "first match wins"
setup, or effectively a bunch of `OR` conditions.

A sample would be:

*Unrelated keys removed to reduce noise.*

```json5
{
  "type": "m.room.join_rules",
  "state_key": "",
  "content": {
    "join_rule": "knock",
    "join_rules": [
      {
        "join_rule": "restricted",
        "allow": [
          {
            "type": "m.room_membership",
            "room_id": "!VzMVEOJOrVWFENLtnO:localhost"
          }
        ]
      },
      {
        "join_rule": "knock"
      }
    ]
  }
}
```

The sample effectively means a user can join the room if:
* They receive an explicit invite.
* They have their `knock` approved (which is an invite).
* They are a member of `!VzMVEOJOrVWFENLtnO:localhost`.

A setup similar to this is expected to be the most common setup.

Note how the `join_rule` persists in the protocol, even with this MSC's introduction. This is to
ensure backwards compatibility with clients and various places in the protocol which aren't aware
of the new rules. While servers will be required to parse the event as described below, areas such
as the room creation presets, older clients, room directory, etc are not easily made fully aware
of a new array.

The `join_rule` must always be specified, even alongside `join_rules`. The `join_rule` should represent
the most semantically relevant join rule for the room - it does not need to be listed in the array,
but should best represent the room's access control. The sample chose `knock`, but a different scenario
may very well choose `restricted` or even `private`.

If the `join_rule` is `restricted`, the `allow` array must also be present at the same level. This
is for backwards compatibility.

Whenever the server (or client) is checking against the join rules it would now check the `join_rules`
array if present. If not present, and only when not present, the `join_rule` string is checked instead.
For a `restricted` join rule, the `allow` list must always be next to the `join_rule` string (eg: don't
have `join_rule: knock, allow: [...]` - the list would be ignored).

For clarity, the server could implement a check similar to:

```python
def is_join_rule(room_version: RoomVersion, event: EventBase, expected_rule: JoinRules) -> bool:
    """Returns whether the join rule event matches the expected join rule.

    Args:
        room_version: The RoomVersion the event is in
        event: The join rules event
        expected_rule: The anticipated rule

    Returns:
        bool: True if the join rule is as expected.
    """
    if not event:
        return expected_rule == JoinRules.INVITE

    if room_version.msc3613_simplified_join_rules:
        arr = event.content.get("join_rules", [])
        if arr and isinstance(arr, list):
            return expected_rule in list(r.get("join_rule", None) for r in arr)

    return event.content.get("join_rule", None) == expected_rule
```

As implied, if the `join_rules` array is not an array then the server falls back to `join_rule`.

Finally, the `join_rules` key is to be protected from redaction. This has a drawback of not being
able to easily remove abuse within the objects, however is simpler on the redaction algorithm itself.

## Potential issues

This representation isn't perfect and can be a bit confusing. As acknowledged in the introduction,
this proposal is meant to introduce the mixed functionality of join rules without re-architecting
the system. Other MSCs are welcome/encouraged to explore what a new join rules system might be.

This proposal allows room admins to make bad decisions, though this proposal also does not have an
interest in preventing bad decisions from happening. For example, a room might decide to mix two
incompatible rules: `public` and `invite`. If this happens, the room is effectively public as the
`invite` rule wouldn't be serving a practical purpose (remember: the first passing join rule wins).
Room admins are recommended by the proposal author to not make bad decisions.

Through effort, room admins can additionally break out their join rules nonsensically. Again however,
this proposal doesn't have an interest in patching bad decisions. An example would be:

```json5
[
  {
    "join_rule": "restricted",
    "allow": [
      {"type": "m.room_membership", "room_id": "!a:example.org"}
    ]
  },
  {
    "join_rule": "restricted",
    "allow": [
      {"type": "m.room_membership", "room_id": "!b:example.org"}
    ]
  },
  {
    "join_rule": "restricted",
    "allow": [
      {"type": "m.room_membership", "room_id": "!c:example.org"}
    ]
  }
]
```

This could be condensed into a singular `restricted` rule, but the room admin is legal in splitting
the rule out.

Finally, this proposal favours backwards compatibility to its own detriment. This is intentional to
give clients (and other areas of the protocol/ecosystem) time to consider what their project might
look like if the join rules system were to change completely. This acts more like an easing function
than a complete refactoring by design.

## Alternatives

[MSC3386](https://github.com/matrix-org/matrix-doc/pull/3386) and similar ideas favour a complete
rebuild of the join rules system. While a potentially great change for Matrix, it doesn't feel proper
for the short term.

## Security considerations

Room admins can specify insane or otherwise lengthy lists of join rules. Servers should be wary of
these sorts of events when considering their loop usage, however this MSC doesn't forbid using all
65kb of an event to specify join rules.

As mentioned in the potential issues, room admins can additionally make bad decisions about security.
Clients are encouraged to design and build a user interface which reduces the chances of a `public`
and `invite` rule set. Such an interface might be:

```
This room is:
[ ] Public
[x] Private

Join rules (disabled when Public):
[x] Allow members of `#space:example.org` to join
[x] Allow knocking
```

## Unstable prefix

While this MSC is not considered stable, implementations should use an `org.matrix.msc3613` room version
which uses room version 9 as a base.

## Dependencies

No relevant dependencies.

## Considered but not included

During a trial implementation of this proposal there were authorization rules added to validate that
a `m.room.join_rules` event is properly structured. While an initial reaction is to include auth rules
for the event, it ultimately doesn't appear important for the protocol. For example, the damage of a
user sending an empty join rules event (or one with unspecified rules) is naturally self-healing by the
room becoming invite only in conditions where the join rules don't match exactly.

As such, the changes to auth rules are excluded from this proposal.
