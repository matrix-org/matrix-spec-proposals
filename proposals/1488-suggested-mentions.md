# Suggested Mentions Proposal

## Motivation

Bridges/bots may not be able to use the exact identifer[1] of the user they are bridging when sending messages on behalf of the user onto another network. Therefore it's entirely possible for replies to a user's message to not include their identifier and not recieve pings for those messages. An example from IRC would be:

- User's displayname is AReallyLongName
- Network sets their nick as AReallyLo because it is too long
- Replies to "AReallyLongName" end up being "AReallyLo" which does 
  not ping them.

## Proposal

The proposed change adds a new event type `m.suggested_mention` which allows a bridge to specify a set of mentions to add (and optionally mentions to remove if they were previously set.) 

This would be sent into a room between the bridge bot and the user.

### Format

#### Content

| Key         | Type     | Default | Required |
| -------     | -------- | ------- | -------- |
| body        | string   |   ""    | Yes |
| request     | string   |         | Yes |
| new_phrases | [string] |   []    | No |
| old_phrases | [string] |   []    | No |

#### body

The body should be some text to describe the suggestion for clients
who do not support the event. This can be anything, but this specification requires that this SHOULD give enough information for the user to infer what the operation is.

#### request

This SHOULD be shown in the prompt to describe why the mention is being suggested. Client should treat this value as freeform and MUST warn that the operation is potentially dangerous. 

### new_phrases

A list of phrases to be added to the users mention list. If the changes are accepted, the client should add these phrases to ``m.push_rules`` in the client's account_data. The parameters of this new mention are up to the client, as the bridge is only suggesting phrases but not *how* the mention is to show.

### old_phrases

A list of phrases to be removed from the users mention list. This is similar to ``new_phrases`` but we are removing any push rules which *exactly* match this phrase.

#### Example Add

```json
{
    "age": 242352,
    "content": {
        "body": "CoolIrcNetwork has set your nickname to HalfyDog.",
        "request":"CoolIrcNetwork has set your nickname on IRC",
        "new_phrases": [
            "HalfyDog"
        ]
    },
    "event_id": "$WLGTSEFSEF:localhost",
    "origin_server_ts": 1431961217939,
    "room_id": "!abridgeadminroom:localhost",
    "sender": "@irc_bridge:localhost",
    "type": "m.suggested_mention"
}
```

#### Example Remove

```json
{
    "age": 242352,
    "content": {
        "body": "CoolIrcNetwork has unset your nickname, 'HalfyDog'.",
        "request":"CoolIrcNetwork has unset your nickname on IRC",
        "old_phrases": [
            "HalfyDog"
        ]
    },
    "event_id": "$WLGTSEFSEF:localhost",
    "origin_server_ts": 1431961217939,
    "room_id": "!abridgeadminroom:localhost",
    "sender": "@irc_bridge:localhost",
    "type": "m.suggested_mention"
}
```

#### Example Replace

```json
{
    "age": 242352,
    "content": {
        "body": "CoolIrcNetwork has set your nickname to HalfyDog and removed HalfyDog[m].",
        "request":"CoolIrcNetwork has set your nickname on IRC",
        "new_phrases": [
            "HalfyDog"
        ],
        "old_phrases": [
            "HalfyDog[m]"
        ]
    },
    "event_id": "$WLGTSEFSEF:localhost",
    "origin_server_ts": 1431961217939,
    "room_id": "!abridgeadminroom:localhost",
    "sender": "@irc_bridge:localhost",
    "type": "m.suggested_mention"
}
```

### Example Client UX

The event should show us as a prompt with a client provided explanatory title and description of what a suggested_mention.

The prompt should make it known who the user is. The prompt should then contain the ``request`` text somewhere. 

Finally, the prompt should list the additions and deletions that will be made to the user's mentions. The client *could* offer the option to accept some of them.

Finally, there should be buttons to accept the changes, ignore the changes, or ignore all future requests from the user.

---


If the client doesn't support this event, the body should be shown in a plain room event instead.

## Alternatives

### New API

A new API that allows bridges to directly modify the account_data of a user. This would need to work over federation and would be a security nightmare, or consider breaking federation support for this and only allowing local users to have their mentions changed. This also does not give the user a chance to consent, unless we prompt them first which adds greater complexity.

### Simply message the user from the bridge

This is similiar to the proposal without any interactive element. The bridge will just message the user and expect them to fill out the mention themselves.


[1] Identifier could be the displayname, or userid or the localpart.