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

An invite rules state contains one required key, and two optional keys.
- `"invite_rule"`: A required String-Enum which has four values
  - `"invite_rule": "all"`: Identical behaviour to the `m.invite_rules` state not existing, no special processing is performed
    for the Invitee.
  - `"invite_rule": "has-shared-room"`: Only allow invites where the Inviter shares at least one room with the Invitee.
  - `"invite_rule": "has-direct-room"`: Only allow invites where the Inviter shares at least one direct room with the Invitee.
  - `"invite_rule": "none"`: Prevent any invites from being sent to the Invitee.
- `"allow"`: An Array of RuleItems where if any are true, an invite request will not be blocked.
- `"deny"`: An Array of RuleItems where if any are true, an invite request will be blocked.

#### `RuleItem`
A RuleItem defines a Rule that can test against an invite request. This primarily exists for structural consistency with the room state `m.join_rules`.
It also serves to allow `m.invite_rules` to be easily extended in the future, such as to introduce an `m.ruleset` type that would accept Mjolnir ruleset rooms.

- `"type"`: Required String-Enum, must be one of the defined types below.

##### `m.user`
Validates as true if the Inviter MXID is equal to the defined `"user_id"`
- `"user_id"`: Required String, a valid MXID.

##### `m.shared_room`
Validates as true if the Inviter and Invitee are in the defined `"room_id"`.
- `"room_id"`: Required String, a valid room id.

##### `m.target_room`
Validates as true if the room which the Invitee is being invited to has the same room id as the defined `"room_id"`.
- `"room_id"`: Required String, a valid room id.

#### Evaluation

In order to prevent homeservers from interpriting `m.invite_rule` states differently, an evaluation order is defined here:

- An Inviter attempts to create an invite request to the Invitee.
  - If `"m.invite_rules"` exists as an account state:
    - If `"allow"` exists, evaluate the defined Rulesets. If one evaluates as True, break from the `"m.invite_rules"` check.
    - If `"deny"` exists, evaluate the defined Rulesets. If one evaluates as True, reject the invite request.
    - If `"type"` within content of `"m.invite_rules"` is:
       1. `"all"`: Break from the `m.invite_rules` check and continue.
       2. `"has-shared-room"`: Get all Rooms Invitee is in, and check if the Inviter has a `"join"` membership state.
          If the Inviter does not have at least one shared room, Reject the invite request.
       3. `"has-direct-room"`: Check if the Invitee's account data state `"m.direct"` exists.
          - If true, test if the content of `"m.direct"` contains a key which is the Inviter's MXID.
            - If `True`, test if the Invitee has a `"join"` membership state in any rooms defined in the key's value. If no matches are found, reject the invite request.
            - If `False`, reject the invite request.
          - If false, reject the invite request.
       4. `"none"`: Reject the invite request.

#### Invite Rejection
If an invite is to be rejected, the homeserver *should* respond with M_FORBIDDEN error code, and the error message: "This user is not permitted to send invites to this server/user"

#### Example:
```js
{
    "type": "m.invite_rules",
    "content": {
        "invite_rule": "has-direct-room",
        "allow": [
            {
                "type": "m.user",
                "user_id": "@bob:example.com"
            },
            {
                "type": "m.shared_room",
                "room_id": "!a:example.com"
            }
        ],
        "deny": [
            {
                "type": "m.user",
                "user_id": "@alice:example.com"
            },
            {
                "type": "m.target_room",
                "room_id": "!b:example.com"
            }
        ]
    }
}
```

## Alternatives
Currently, there is no way outside of homeserver-wide restrictions (mjolnir, anti-spam plugins), for users to control who can send them invites. While users can ignore single users to prevent them from sending them invites, this does nothing since a malicious user simply create another matrix account.

## Potential Issues
There is a potential denial of service for the `has-shared-room` and `has-direct-room` invite rules, as they require searching through all rooms a user is in, which could be a lot. This heavily depends on the homeserver's internals of course.

Additionally, as no limit for the `"allow"` and `"deny"` rulesets is specified, an Invitee could make hundreads of rules to attempt to
slow the homeserver down. For homeservers where this may be a concern, a sensible limit should be configurable by the homeserver admin.

## Unstable prefix
While this MSC is in development, implementations of this MSC should use the state type `org.matrix.msc3659.invite_rules`
