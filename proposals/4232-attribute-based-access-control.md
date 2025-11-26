# MSC4232: Attribute-Based Access Control (ABAC)

Within Matrix rooms it is important to be able to grant specific actions to users with more trust or
capability to embody a role, such as giving a concept of "moderators" the kick and ban permissions. In
Matrix today, this is accomplished using "power levels", or simple integers assigned to a set of possible
flags to denote the "required level" and a similar set of integers assigned to users, with a specified
default, to denote their "user level". For all flags with a required level less then or equal to the
user level, that action may be performed by that user.

This system works in a wide variety of scenarios, but has a few notable rough edges:

1. Bridges to networks and protocols with complex permissions systems, such as Discord, can't easily
   be represented in Matrix. Many of these networks use a Role-Based Access Control (RBAC) model, where
   roles are given permissions, and users are given roles. Some of these networks, like the [proposed
   MIMI Policy](https://datatracker.ietf.org/doc/html/draft-ietf-mimi-room-policy-00), use more simplified
   *attributes* to assign to users instead though, maximizing the number of possible connected platforms.

2. Running state resolution over a single permissions event (`m.room.power_levels`) is both a blessing
   and a curse. While it helps make conflicts easier to resolve by limiting the choices, the experienced
   behaviour can be unexpected to users when event A is chosen over event B, for example. This can
   lead to users "losing" their admin permissions, or more subtle changes to the room's permissions
   model. RBAC and ABAC don't necessarily make state resolution easier to manage, but do limit the
   unexpected outcomes from users.

3. When combining permissions into a single event, multiple users attempting to update the event can
   overwrite each other's changes. This is relatively rare, but when it happens it is confusing to
   users. If the users are on the same server then that server can do some behind the scenes work to
   mask the issue, though this is less effective over federation.

To help address the above, and retain maximum interoperability with other networks, this proposal
introduces a concept of [Attribute-Based Access Control (ABAC)](https://en.wikipedia.org/wiki/Attribute-based_access_control).
ABAC as it's implemented in this proposal is effectively a set of boolean flags assigned to a user
to describe what that user can do, with defaults being implied for sake of consistency. In the current
model of [MSC4056](https://github.com/matrix-org/matrix-spec-proposals/pull/4056), RBAC is implemented
as assigning the boolean flags to a role rather than a user directly, allowing for some repeatability
and user-specific context to be applied, like a name and colour for the role. This proposal doesn't
prohibit the use of roles or permission templates, but does not specify them.

## Proposal

**Disclaimer**: What follows is largely a brain dump. There may be incomplete ideas, or ideas which
don't work. There's also little thought into what effect this will have on specific Authorization Rules
and State Resolution, though reviewers may be able to determine rough impact.

In a future room version, `m.room.power_levels` loses all meaning and effect. In its place, a new
`m.room.permissions` state event is established with the following schema and behaviour.

Event Type: `m.room.permissions`
State Key: Empty String or User ID
Content: As implied by:

```jsonc
{
  "m.namespaced_boolean": true,
  "m.namespaced_object": {
    "m.namespaced_boolean": true
  }
}
```

When the state key is a user ID, the content (also known as the attributes) are assigned to that
user, bearing the meaning of those attributes. When an empty string, the event represents the defaults
for users lacking an explicit `m.room.permissions` event.

Because state may not be deleted in Matrix currently, an empty `content` object for `m.room.permissions`
denotes "use defaults".

### Attributes

Attributes are namespaced using the [Common Namespaced Identifier Grammar](https://spec.matrix.org/v1.12/appendices/#common-namespaced-identifier-grammar),
allowing for custom attributes to be assigned to users. Where a client (or server, technically) does
not recognize an attribute, it MUST ignore it entirely.

Attributes MAY define their default behaviour when not specified either in the room-level defaults
(empty string state key for `m.room.permissions`) or in a user-assigned event. For example, an attribute
may say "when not explicitly `false`, this attribute is `true`".

Attribute values can either be a boolean or an object with further sub-attributes which can only be
a boolean value. A future MSC may introduce support for more complex types. When an object, the object
MUST be exhaustive, meaning defaults are only applied at the very top level and do not recurse to
sub-attributes.

To mirror power levels, the following attributes are created with the described behaviour/defaults:

* `m.kick` - default `false` - when `true`, the user may kick other users which do not have this
  attribute.
* `m.ban` - default `false` - same as `m.kick`, but for bans.
* `m.redact` - default `false` - same as `m.kick`, but for redacting other users' messages.
  * Like power levels, a different attribute limits self-redaction.
* `m.invite` - default `false` when `join_rules: public`, default `true` in all other rooms - when
  `true`, the user may invite other users to the room.
* `m.assign` - default `{}` - maps attributes the user is able to assign to other users. Attributes
  not specified in the object are presumed `false`.
  * Example:
    ```jsonc
    {
      "m.assign": {
        "m.assign": false, // explicit, but technically not required to be here
        "m.ban": true,
        "m.invite": true
      }
    }
    ```
* `m.state` - default `{}` - maps the state event types the user is able to send in the room. Event
  types not specified in the object are presumed `false`.
  * Example:
    ```jsonc
    {
      "m.state": {
        "m.room.name": true,
        "m.room.history_visibility": false, // explicit, but not technically required to be here
        "m.room.topic": true
      }
    }
    ```
* `m.events` - default `{"m.*": true}` - maps the non-state ("message") event types the user is able
  to send in the room. `m.*` is reserved to denote "all unspecified event types" and the behaviour
  associated with it. When `m.*` is not specified, it is presumed `true` to avoid a footgun.
  * Example:
    ```jsonc
    {
      "m.events": {
        "m.*": false, // when false, the user can only send event types explicitly marked `true`
        "m.room.message": true,
        "m.reaction": true
      }
    }
    ```

### Carving out space for roles

A future MSC may layer roles on top of ABAC, giving rooms an option to bulk-apply permissions to users
and add some renderable details like name and colour. A possible design for this would be to expand
the scope of `m.room.permissions`'s state key to include arbitrary, non-user ID, strings to denote a
"role ID". That role can then be assigned with a custom attribute like so:

```jsonc
{
  "m.roles": {
    "admin": false,
    "mod": true,
    "supporter": true,
    "cool_person": true
  }
}
```

Careful consideration for loops would be required in that future MSC.

## Potential issues

TBD

## Alternatives

TBD

## Security considerations

TBD

## Safety considerations

TBD

## Unstable prefix

While this MSC is not included in a stable room version, it MUST only be implemented in an unstable
room version using the following format: `org.matrix.msc4232.<parent version>`. For example, if an
implementation implements this proposal using room version `11` as a base, the unstable room version
would be `org.matrix.msc4232.11`.

For valid consideration under the MSC process, an implementation must base itself off the latest
stable room version available at time of FCP.

## Dependencies

TBD
