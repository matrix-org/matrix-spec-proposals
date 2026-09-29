# MSC4257: Move profiles to a separate event

Profile updates being part of membership, makes all kinds of operations a pain in the ass,
be it calculating auth events, or figuring out if someone changed their displayname or joined.

What if we made them a separate event instead, and simplified the redaction rules for membership events?


## Proposal

We could move profiles (display names/avatars) to a separate event. This would make calculating event auth
chains faster, as there's far less noise to consider. Additionally, it'd allow telling membership edges
appart in code a decent amount faster. This MSC's purpose is to be a middle step between current day
Matrix and Profiles as Rooms. This also doesn't break historical profiles, as needed in some contexts.
Additionally, this could be used together with MSC 4133 to optionally override fields per room, unless
specified otherwise in the field's MSC.

An example of an `m.room.member` event after this MSC could look like this:
```json5
{
    "content": {
        "is_direct": false, // Should this be moved to a different event? Or only be valid when membership==invite?
        "membership": "join"
    },
    "event_id": "$aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "origin_server_ts": 1737828697089,
    "sender": "@bob:example.com",
    "state_key": "@bob:example.com",
    "type": "m.room.member",
    "unsigned": {
        "age": 4
    }
}
```

An example of an `m.room.member.profile` event after this MSC could look like this:
```
{
    "content": {
        "displayname": "Alice",
        "avatar_url": "mxc://example.com/abcdefg",
        "m.pronouns.en": "she/her"
    },
    "event_id": "$aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaab",
    "origin_server_ts": 1737828697090,
    "sender": "@bob:example.com",
    "state_key": "@bob:example.com",
    "type": "m.room.member.profile",
    "unsigned": {
        "age": 4
    }
}
```

This change would make event auth faster, as profile updates no longer need to be considered.
Additionally: the profile event is only allowed to be sent by the user specified in the state key,
except in the case that the content being sent is an empty json set`{}`, or in the case of a redaction.

## Potential issues

This is going to require a separate room version, I think? Especially given this changes the redaction
rules for m.room.member events as additional fields are technically no longer required.

## Alternatives

None yet.

## Security considerations

I do not think this MSC has any security ramifications.

## Unstable prefix

`gay.rory.room.member.profile`, relevant if used in older room versions.

## Dependencies

None.
