---
toc_hide: true
---

Events must be signed by the server denoted by the `sender` key.

`m.room.redaction` events are not explicitly part of the auth rules.
They are still subject to the minimum power level rules, but should always
fall into "10. Otherwise, allow". Instead of being authorized at the time
of receipt, they are authorized at a later stage: see the
[Redactions](#redactions) section below for more information.

The types of state events that affect authorization are:

-   `m.room.create`
-   `m.room.member`
-   `m.room.join_rules`
-   `m.room.power_levels`
-   `m.room.third_party_invite`

{{% boxes/note %}}
Power levels are inferred from defaults when not explicitly supplied.
For example, mentions of the `sender`'s power level can also refer to
the default power level for users in the room.
{{% /boxes/note %}}

The rules are as follows:

1.  If type is `m.room.create`:
    1.  If it has any previous events, reject.
    2.  If the domain of the `room_id` does not match the domain of the
        `sender`, reject.
    3.  If `content.room_version` is present and is not a recognised
        version, reject.
    4.  If `content` has no `creator` field, reject.
    5.  Otherwise, allow.
2.  Reject if event has `auth_events` that:
    1.  have duplicate entries for a given `type` and `state_key` pair
    2.  have entries whose `type` and `state_key` don't match those
        specified by the [auth events
        selection](/server-server-api#auth-events-selection)
        algorithm described in the server specification.
3.  If event does not have a `m.room.create` in its `auth_events`,
    reject.
4.  If type is `m.room.member`:
    1.  If no `state_key` key or `membership` key in `content`, reject.
    2.  If `content` has a `join_authorised_via_users_server`
        key:
        1.  If the event is not validly signed by the user ID denoted
            by the key, reject.
    3.  If `membership` is `join`:
        1.  If the only previous event is an `m.room.create` and the
            `state_key` is the creator, allow.
        2.  If the `sender` does not match `state_key`, reject.
        3.  If the `sender` is banned, reject.
        4.  If the `join_rule` is `invite` then allow if membership
            state is `invite` or `join`.
        5.  If the `join_rule` is `restricted`:
            1.  If membership state is `join` or `invite`, allow.
            2.  If the `join_authorised_via_users_server` key in `content`
                is not a user with sufficient permission to invite other
                users, reject.
            3.  Otherwise, allow.
        6.  If the `join_rule` is `public`, allow.
        7.  Otherwise, reject.
    4.  If `membership` is `invite`:
        1.  If `content` has `third_party_invite` key:
            1.  If *target user* is banned, reject.
            2.  If `content.third_party_invite` does not have a `signed`
                key, reject.
            3.  If `signed` does not have `mxid` and `token` keys,
                reject.
            4.  If `mxid` does not match `state_key`, reject.
            5.  If there is no `m.room.third_party_invite` event in the
                current room state with `state_key` matching `token`,
                reject.
            6.  If `sender` does not match `sender` of the
                `m.room.third_party_invite`, reject.
            7.  If any signature in `signed` matches any public key in
                the `m.room.third_party_invite` event, allow. The public
                keys are in `content` of `m.room.third_party_invite` as:
                1.  A single public key in the `public_key` field.
                2.  A list of public keys in the `public_keys` field.
            8.  Otherwise, reject.
        2.  If the `sender`'s current membership state is not `join`,
            reject.
        3.  If *target user*'s current membership state is `join` or
            `ban`, reject.
        4.  If the `sender`'s power level is greater than or equal to
            the *invite level*, allow.
        5.  Otherwise, reject.
    5.  If `membership` is `leave`:
        1.  If the `sender` matches `state_key`, allow if and only if
            that user's current membership state is `invite`, `join`,
            or `knock`.
        2.  If the `sender`'s current membership state is not `join`,
            reject.
        3.  If the *target user*'s current membership state is `ban`,
            and the `sender`'s power level is less than the *ban level*,
            reject.
        4.  If the `sender`'s power level is greater than or equal to
            the *kick level*, and the *target user*'s power level is
            less than the `sender`'s power level, allow.
        5.  Otherwise, reject.
    6.  If `membership` is `ban`:
        1.  If the `sender`'s current membership state is not `join`,
            reject.
        2.  If the `sender`'s power level is greater than or equal to
            the *ban level*, and the *target user*'s power level is less
            than the `sender`'s power level, allow.
        3.  Otherwise, reject.
    7. If `membership` is `knock`:
        1.  If the `join_rule` is anything other than `knock`, reject.
        2.  If `sender` does not match `state_key`, reject.
        3.  If the `sender`'s current membership is not `ban`, `invite`,
            or `join`, allow.
        4.  Otherwise, reject.
    8.  Otherwise, the membership is unknown. Reject.
5.  If the `sender`'s current membership state is not `join`, reject.
6.  If type is `m.room.third_party_invite`:
    1.  Allow if and only if `sender`'s current power level is greater
        than or equal to the *invite level*.
7.  If the event type's *required power level* is greater than the
    `sender`'s power level, reject.
8.  If the event has a `state_key` that starts with an `@` and does not
    match the `sender`, reject.
9. If type is `m.room.power_levels`:
    1.  If `users` key in `content` is not a dictionary with keys that
        are valid user IDs with values that are integers (or a string
        that is an integer), reject.
    2.  If there is no previous `m.room.power_levels` event in the room,
        allow.
    3.  For the keys `users_default`, `events_default`, `state_default`,
        `ban`, `redact`, `kick`, `invite` check if they were added,
        changed or removed. For each found alteration:
        1.  If the current value is higher than the `sender`'s current
            power level, reject.
        2.  If the new value is higher than the `sender`'s current power
            level, reject.
    4.  For each entry being added, changed or removed in both the
        `events`, `users`, and `notifications` keys:
        1.  If the current value is higher than the `sender`'s current
            power level, reject.
        2.  If the new value is higher than the `sender`'s current power
            level, reject.
    5.  For each entry being changed under the `users` key, other than
        the `sender`'s own entry:
        1.  If the current value is equal to the `sender`'s current
            power level, reject.
    6.  Otherwise, allow.
10. Otherwise, allow.

{{% boxes/note %}}
Some consequences of these rules:

-   Unless you are a member of the room, the only permitted operations
    (apart from the initial create/join) are: joining a public room;
    accepting or rejecting an invitation to a room.
-   To unban somebody, you must have power level greater than or equal
    to both the kick *and* ban levels, *and* greater than the target
    user's power level.
{{% /boxes/note %}}