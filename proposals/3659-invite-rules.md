# MSC3659 - Invite Rules

This MSC proposes the creation of an optional account data state which allows users to control how invites directed at them
are processed by their homeserver.

*Homeservers may choose to ignore an Invitee's invite rules *if* the Inviter is a homeserver admin.*

## Proposal

### Glossery
- Inviter: The matrix user which has created the invite request.
- Invitee: The matrix user which is receiving the invite request.
- Invite request: An invite that the homeserver is to process. For Synapse, this would be handled by [`on_invite_request`](https://github.com/matrix-org/synapse/blob/develop/synapse/handlers/federation.py#L752).

### `m.invite_rules`

An invite rules state contains one required key.
- `"rules"`: An Array of `RuleItem`s. The Array should contain no more than 127 entries.

*Homeservers may wish to implement a smaller maximum, if so that maximum should be no smaller than 8*

*Homeservers may also wish to exceed the defined maximum, doing so is allowed, but at their own peril.*

#### `RuleItemAction`
A String-Enum that defines an action that the ruleset evaluator is to perform.

* `"allow"`: Allow the invite request, breaks from ruleset evaluation.
* `"deny"`: Reject the invite request.
* `"continue"`: Do not take any action and continue ruleset evaluation.

*Ruleset evaluation is performed before an invite request is acknowledged by the homeserver, invite rejection here refers to rejecting the invite request in the form of returning a HTTP error to the Inviter's homeserver. Not to reject an invite request which has already been acknowledged (visible to the Invitee) by the homeserver.*

#### `RuleItem`
A RuleItem defines a Rule that can test against an invite request.

- `"type"`: Required String-Enum, must be one of the defined types below.
- `"pass":` A required `RuleItemAction` that will be performed if the rule evaluates as True
- `"fail":` A required `RuleItemAction` that will be performed if the rule evaluates as False

##### `m.user`
Validates as True if the Inviter MXID is equal to the defined `"user_id"`.
- `"user_id"`: Required String, a valid user id.

##### `m.shared_room`
Validates as True if the Inviter and Invitee are in the defined `"room_id"`.
- `"room_id"`: Required String, a valid room id.

##### `m.target_room_id`
Validates as True if the target room id is equal to the defined `room_id`.
- `"room_id"`: Required String, a valid room id.

##### `m.target_room_type`
Validation depends on the value of `room_type`.
- `"room_type"`: Required String-Enum.
  - `"room_type": "is-direct-room"`: Rule evaluates as True if the Invitee's membership state in the target room has `"is_direct"` set to True.
  - `"room_type": "is-space"`: Rule evaluates as True if the target room's `m.room.create` `type` is `"m.space"`
  - `"room_type": "is-room"`: Rule evaluates as True if the target room is not a direct room or a space.

#### `InviteRule`
A String-Enum.
* `"any"`: Always evaluates as True.
* `"has-shared-room"`: Evaluates as True if the Inviter shares at least one room with the Invitee.
* `"has-direct-room"`: Evaluates as True if the Inviter has an active room defined in the Invitee's `m.direct` account data state. *Active is defined as "if both the Invitee and Inviter are present".*
* `"none"`: Always evaluates as False.

#### Evaluation

* The Invitee's homeserver receives an invite request from the Inviter:
  * If the `"m.invite_rules"` account data state exists, then:
    * If `"rules"` is defined, then for each `RuleItem`:
      * Evaluate the `RuleItem` and save either the `"pass"` or `"fail"` `RuleItemAction` depending on the result.
      * If the `RuleItemAction` is:
        * `"allow"`, then: Break from the invite rules loop.
        * `"deny"`, then: Respond with `M_FORBIDDEN`.
        * `"continue"`, then: Continue for each.

*If the rules loop is iterated through without any action taken, it is treated as `"allow"`.*

Implementations may wish to utilise result caching where applicable to improve performance. Such as for rules that may require comparing the joined rooms of each user.

*Such cache would be storing the resulting `Boolean` returned during `RuleItem` evaluation, **not** the `RuleItemAction` which is picked from the defined `"pass"` or `"fail"` keys.*

#### Invite Rejection
If an invite is to be rejected, the homeserver *should* respond with M_FORBIDDEN, and the error message: "This user is not permitted to send invites to this server/user"

#### Example
The following example will allow any invites from `@bob:example.com` or members of `!a:example.com`, deny any invites from `@alice:example.com`, and allow direct invites from any user who shares at least one room with the Invitee.

```js
{
    "type": "m.invite_rules",
    "content": {
        "rules": [
            {
                "type": "m.user",
                "user_id": "@bob:example.com",
                "pass": "allow",
                "fail": "continue"
            },
            {
                "type": "m.user",
                "user_id": "@alice:example.com",
                "pass": "deny",
                "fail": "continue"
            },
            {
                "type": "m.shared_room",
                "room_id": "!a:example.com",
                "pass": "allow",
                "fail": "continue"
            },
            {
                "type": "m.invite_rule",
                "rule": "has-shared-room",
                "pass": "continue",
                "fail": "deny"
            },
            {
                "type": "m.target_room_type",
                "room_type": "is-direct-room",
                "pass": "allow",
                "fail": "deny"
            }
        ]
    }
}
```

## Alternatives
Currently, there is no way outside of homeserver-wide restrictions (mjolnir, anti-spam plugins), for users to control who can send them invites. While users can ignore single users to prevent them from sending them invites, this does little since a malicious user simply create another matrix account.

## Potential Issues
There is a potential denial of service for the `has-shared-room` and `has-direct-room` invite rules, as they require searching through all rooms a user is in, which could be a lot. This heavily depends on the homeserver's internals of course.

The `"rules"` Array's defined maximum may not be suitable for resource-strained, or particularly large homeservers. Homeservers should make the maximum rules configurable for the homeserver admin.

As homeservers may set a custom rule limit, clients currently have no reliable way of knowing that limit. Some way of signalling the limit to the client should be looked into

## Unstable prefix
While this MSC is in development, implementations of this MSC should use the state type `org.matrix.msc3659.invite_rules`
