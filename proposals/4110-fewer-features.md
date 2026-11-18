# MSC4110: Fewer features

The Fewer Features proposal aims to make Matrix bridges work better with other platforms. Currently, it is hard for clients and Matrix users to know if what they send in a bridged room will be supported or not. The goal of Fewer Features is to let bridges communicate which Matrix features are supported on the external platform. Then, clients and bots can change how they act based on what the external platform supports.

In a nutshell, bridges can set a state event that says which Matrix features are discouraged or disallowed in this room. Clients and bots can use this information to disable features, change UI elements, or change the way events are sent. This will give the best possible experience to people on the other side of the bridge. It will also reassure Matrix users that their actions are working properly, because incompatible actions simply cannot be sent.


## Proposal


### When a bridge should set Fewer Features

Fewer Features is a request from the bridge for the client to not use a certain feature. This means Fewer Features is ideal when:

* the external platform does not support the feature
* or the bridge does not handle the feature in a satisfactory way

However, Fewer Features may not be ideal when:

* the external platform supports the feature and the bridge is able to bridge it
* the external platform doesn't support the feature, but the bridge does special converting to make it work

### State event

A bridge that wants to set fewer features can send a state event like so:

```json
{
    "content": {
        "send": {
            "FEATURE_DECLARATION_KEY": DESIRABILITY_LEVEL,
        },
        "send_default": DESIRABILITY_LEVEL,
        "receive": {
            "FEATURE_DECLARATION_KEY": DESIRABILITY_LEVEL,
        },
        "receive_from_users": [
            "@_theplatform_*:example.net"
        ],
        "send_reaction": {
            "reaction_list": [
                EMOJI,
                ANOTHER_EMOJI
            ],
            "reactions_per_user_per_event": NUMBER,
            "reactions_per_event": NUMBER
        }
    },
    "type": "m.room.event_features",
    "state_key": "@my_cool_bridge:example.net"
}
```

The type shall be `m.room.event_features` and the state key shall be the user ID that sends the event (the bridge bot's user ID).

Everything in `content` is optional. An empty dictionary is considered the same as an unset dictionary. An empty array is considered different to an unset array.

### Desirability levels

* `0`: Default value, same as it being unset. The bridge understands and will send/convert/substitute the event for the destination platform.
* `-1`: This feature will be worse over the bridge. The client can choose to *Discourage, Substitute, or Disallow* the feature.
* `-2`: This feature will not work over the bridge, and the bridge will fall back to the `body` or `formatted_body` instead. The client can choose to *Substitute or Disallow* the feature.
* `-3`: This feature will not work over the bridge, and fallbacks aren't a good enough substitute. The client must *Disallow* the feature.

### Discourage, Substitute, Disallow

* *Discourage* means: Warn the user that the feature may not work well over the bridge, but allow them to use it anyway (e.g. by displaying a notice while the user is using the feature).
* *Substitute* means: The bridge isn't able to provide a suitable substitute for this event, but the sending client could. The client should leave the feature as-is AND also provide a fallback `body` or `formatted_body` that is suitably close to parity with the original intention. The bridge will use the substitution provided by the client.
* *Disallow* means: Disable the feature entirely (e.g. by removing UI elements that would activate it, or by using different preferences while in the room).

It is the client's choice whether their Substitution is "suitably close to parity" to be able to use it. This should be considered on a feature-by-feature and client-by-client basis.

### Feature declarations - sending

When preparing or sending events, clients must keep these feature declarations in mind. Clients receiving events that use these features do not have to change their behaviour.

#### `reply`

This affects the [rich replies](https://spec.matrix.org/v1.9/client-server-api/#rich-replies) section of the spec.

This means the external platform doesn't support replies. If the feature is Substituted, the bridge will send through the `formatted_body` reply fallback instead. If the feature is Disallowed, the reply fallbacks aren't good enough, and clients shouldn't send replies at all.

#### `replace`

This affects the [event replacements](https://spec.matrix.org/v1.9/client-server-api/#event-replacements) section of the spec.

This means the external platform doesn't support edits. It is unlikely that clients can generate a suitable fallback for edits, as the original event will remain unchanged in chat, and it will be difficult for external users to see the difference unless the client's `formatted_body` fallback uses a diffing algorithm between old and new (the spec does not recommend this). If the feature is Substituted, clients might choose to disable it unless they have really good `formatted_body`.

#### `redact`

This affects sending a redaction according to [section 7.9.2 of the spec](https://spec.matrix.org/v1.9/client-server-api/#redactions).

This means the external platform doesn't support redacting events.

To comply with personal data laws, clients MUST still allow the user to redact the event on Matrix-side, but must inform the user it will still be visible on the external platform.

#### `matrix.to_room`

This affects the [matrix.to navigation](https://spec.matrix.org/v1.9/appendices/#matrixto-navigation) section of the spec.

This means the external platform doesn't support links or references to rooms, so the bridge won't be able to convert the `matrix.to` links to a suitable representation.

If the feature is Substituted, clients might be able to display a room name instead of a link. If the feature is Disallowed, clients shouldn't send `matrix.to` room links.

#### `matrix.to_user`

This means the external platform doesn't support links or references to users, so the bridge won't be able to convert it.

If the feature is Substituted, clients might be able to display a user name instead of a link. If the feature is Disallowed, clients shouldn't send `matrix.to` user links.

#### `matrix.to_event`

This means the external platform doesn't support links or references to specific events, so the bridge won't be able to convert it.

It is unlikely that clients can substitute this feature. If the feature is Disallowed, clients shouldn't send `matrix.to` event links.

#### `rich_text`

This affects the [event content HTML](https://spec.matrix.org/v1.9/client-server-api/#mroommessage-msgtypes) section of the spec.

This means the external platform doesn't support any kind of rich text, and all messages will display as plain text. This will also affect the `<img>` HTML element.

If the feature is Substituted, the bridge will send through the `body`. If the feature is Disallowed, clients should disable rich text controls and should not convert typed Markdown or HTML to rich text.

#### `line_break`

This means messages on the external platform cannot contain line breaks.

#### `file`

This means the external platform doesn't support files. The bridge may be able to send through a hyperlink to the file. If the feature is Disallowed, clients should not upload files. This will also affect the `<img>` HTML element.

#### `voip`

This affects the [Voice over IP](https://spec.matrix.org/v1.9/client-server-api/#voice-over-ip) section of the spec.

This means the external platform doesn't support calls or the bridge is not capable of negotiating a call.

Specific codecs of VoIP (e.g. if a platform supports voice but not video) are managed by the VoIP module. They are not managed by this module.

#### `reaction`

This affects the [event annotations and reactions](https://spec.matrix.org/v1.9/client-server-api/#event-annotations-and-reactions) section of the spec.

This means the external platform doesn't support reactions. It is unlikely that clients can Substitute this feature. If the event is Disallowed, clients shouldn't send reactions.

#### `sticker`

This affects the [sticker messages](https://spec.matrix.org/v1.9/client-server-api/#sticker-messages) section of the spec.

This means the external platform doesn't support stickers. Clients might choose to Substitute with an image instead, if `file` is available.

#### `thread`

This affects the [threading](https://spec.matrix.org/v1.9/client-server-api/#threading) section of the spec.

This means the external platform doesn't support threads. Note that as per the spec, thread fallbacks look like rich replies. Discourage will suggest Matrix users not to create threads (if they do, they'll appear as rich replies). Substitute will always appear as rich replies. Disallow should remove UI elements that start new threads.

### Feature declarations - sending reactions

Unfortunately, other platforms often have special behaviour around reactions, which needs to be declared separately. Reaction behaviour is defined under the `send_reaction` key.

Fallbacks are not available for these keys. Once the defined limit of a key is hit, the feature should be disallowed.

#### `reaction_list`

This is a list of all reactions that can be added to a message. This will probably be a list of emojis, but can also include text. (If the key is not specified, Matrix users can react with any text.) The special value `mxc://*` means any MXC URL can be used as a reaction.

#### `reactions_per_event`

This is the number of reactions that each Matrix user can add to each event. (If the key is not specified, there is no limit.)

Once the limit is reached for a user on an event, clients must either:

* disallow further reactions
* OR automatically remove the existing reaction, then add the newly chosen reaction

### Feature declarations - receiving

The received events declaration only supports desirability levels 0 and -3.

Clients receiving events that use a Disallowed feature should hide the feature.

This only affects events received from the users in `receive_from_users`. `receive_from_users` should reference the simulated users managed by the bridge. Each string in `receive_from_users` may contain at most one asterisk `*` which acts as a wildcard.

#### `read_receipt`

This affects the [read receipts](https://spec.matrix.org/v1.9/client-server-api/#receipts) section of the spec.

This means the external platform doesn't support read receipts. As such, the read receipts from external users will always match the messages they send (since sending a message automatically updates the read marker). Clients should not display these read receipts because they are misleading.

### Extending to future features

Features added to Matrix in the future will need their own feature declaration keys. There are two ways to add new keys to Fewer Features:

1. In the MSC or spec for a new feature, the proposal can state what key to use.
2. If any feature in the spec does not have a key, a new MSC can be created to simply propose adding a key for it.

In addition, any MSCs that are not merged can use their `org.matrix.mscxxxx` number as the feature key. For example, the feature declaration key for [bot indicators][MSC4015] can be `org.matrix.msc4015`. This could be used to inform bots that this bridge will not bridge their bot markers to the external platform.


### Merging multiple events

A room may have multiple bridges and thus multiple `event_features` state events. Use this algorithm to merge multiple events:

1. Merge `send` from each event. For each feature, choose the lowest number out of all the events.
1. After merging `send`, `send_default` applies to any features that are not in any event's `send`.
1. Merge `reaction_list` by only including list items that appear in every event.
1. Merge `reactions_per_event` by choosing the smallest number out of all the events.
1. While `receive` does need to be considered on every event, `receive`does not need to be merged between events, because each `receive` only applies to the `receive_from_users` in that event.
1. If any users of `receive_from_users` are in multiple events, this is undefined behaviour.

Here is the algorithm as pseudocode:

```php
send <- {}
send_default <- 0
reaction_list <- unset
reactions_per_event <- unset
receive_from_user <- {}

for event <- get state events with type "m.room.event_features" and any state_key
    for key <- keys of event.send:
        send[key] <- the smaller number of (send[key], event.send[key])

    send_default <- the smaller of send_default and event.send_default

    reaction_list <- the common elements of (reaction_list, event.send_reaction.reaction_list)
    reactions_per_event <- the smaller number of (reactions_per_event, event.send_reaction.reactions_per_event)

    for user_id <- event.receive_from_user:
        for key <- keys of event.receive:
            receive_from_user[user_id][key] <- event.receive[key]

for key <- keys defined in this proposal:
    if send[key] is not set yet:
        send[key] <- send_default
```

Operations used:

* `the smaller number of` takes numerical arguments and returns the smallest one. Unset arguments are not considered. The result is a number unless all arguments are unset.
* `the common elements of` takes list arguments and returns only the elements which are in every list. Unset arguments are not considered. The result is a list unless all arguments are unset.
* `dict[key]` accesses the key of the dictionary. If the key hasn't been set on that dictionary yet, the result of the access is unset.


## Examples


### IRC

```json5
{
    "content": {
        "send": {
            "matrix.to_event": -3, // IRC messages have no identifiers and cannot be referenced
            "rich_text": -1, // IRC doesn't have rich text. This is only -1 because the bridge can deal with it, but prefers plain text messages.
            "line_break": -1, // IRC also doesn't have line breaks. This is only -1 because the bridge can deal with it, but prefers plain text messages.
            "reply": -2,
            "replace": -2, // Messages cannot be edited on IRC. The client can use a substitute, but only if it's a good substitute.
            "redact": -3, // Messages cannot be deleted on IRC.
            "file": -2,
            "voip": -3,
            "reaction": -3,
            "thread": -3,
            "org.matrix.msc4015": -2 // IRC doesn't have a way to indicate automated accounts/messages
        },
        "send_default": -1, // Matrix is changing and IRC is not. Matrix events invented in the future are unlikely to be supported.
        "receive": {
            "read_receipt": -3
        },
        "receive_from_users": [
            "@_coolircbridge_*:example.net"
        ]
    },
    "type": "m.room.event_features",
    "state_key": "@cool_irc_bridge:example.net"
}
```

Here are some example changes a client could make when acting on this Fewer Features event. This is not intended to be a prescriptive or exhaustive list. This is just an example of how some changes to clients could improve the experience and consistency across platforms in IRC bridged rooms.

* Display a tooltip warning on rich text controls, saying that external users won't see it as intended
* Remove rich text controls and disable markdown interpretation in the message input box
* Make reply fallback `body` fit on a single line since `reply` and `line_break` are both listed
* Remove the reply button
* Warn users in the delete confirmation modal that external users will still see the message
* Upload files to a pastebin and post the link, rather than attaching them as m.file
* Remove the react, call, and thread buttons
* Hide read receipts from users matching `@_coolircbridge_*:example.net`

### Discord

```json5
{
    "content": {
        "send": {
            "voip": -3, // Voice calls are only supported in voice channels, but this room represents a text channel
            "thread": -1 // This bridge prefers to make threads as separate rooms, to fully support all of Discord's features like different members and pinned messages per room
        },
        "send_reaction": {
            "reaction_list": [
                "mxc://*",
                // And a giant list of every emoji supported in the Discord client
            ]
        },
        "receive": {
            "read_receipt": -3
        },
        "receive_from_users": [
            "@_cooldiscordbridge_*:example.net"
        ]
    },
    "type": "m.room.event_features",
    "state_key": "@cool_discord_bridge:example.net"
}
```

Here are some example changes for this Fewer Features event. Again, this list is not prescriptive or exhaustive.

* Hide the call buttons
* Warn users in the thread start interface prompt that threads may not work as well for external users


## Potential issues


Clients without a cache might not be able to efficiently look up all state events under `m.room.event_features` without requesting the entire room state from the server, which may be slow or too resource expensive if the room has thousands of members. A workaround for such clients is to get `m.room.power_levels`, and for each user ID with PL 50 or higher, look up `m.room.event_features` with that user ID as the state key. This will probably work well because bridges will have an elevated power level in rooms they manage.

When backfilling history backward, clients should consider they may receive a `m.room.event_features` event that predates events they already received.


## Alternatives


- Making clients bundle a list of known limits for each bridge and rely on [MSC2346][MSC2346] to allow them to discover bridges in a room. This puts a significant maintenance burden on clients, requires users to constantly update them to match new bridges (or new bridge configurations), may lead to different Matrix clients showing different sets of events, does not allow room administrators to set arbitrary limits.

- Requiring the `state_key` to be empty, so a single `m.room.event_features` event is valid at any given time. This can cause event updates to race when two bridges are set up at the same time; and makes it harder (or impossible) to tear down a (restrictive) bridge without removing restrictions of other bridges or admins.

- Extending `m.room.power_levels`'s `events` feature to support allowing/denying fine-grained features rather than the current coarse-grained event types. This would require a lot of extra work to get the server involved to catch this in the C-S API. Servers would also need to handle this during federation. This wouldn't work in encrypted rooms without deliberately leaking even more metadata. This doesn't take the burden off clients, as clients would still need to understand Fewer Features to send compliant events. While server support may be possible, it would be best discussed in a separate MSC.

- Hiding more received events from other Matrix users (e.g. merging `send` and `receive`). If implemented, bad actors would be able to send events hidden from some clients but visible to other clients which do not implement this MSC. In this case, to be able to moderate rooms, Fewer Features would have to be deactivated for room moderators to let them moderate effectively. This would add more complexity, and there's no reason to hide features used by native Matrix users anyway.

- Allowing positive desirability levels as well as negative ones to encourage clients to use certain features. This idea seems misguided since if a client has implemented a feature, it will already try to use it opportunistically. For example, a client supporting [breakout rooms][MSC3985] will already offer the feature and use it. Similarly, a bot supporting [bot indicators][MSC4015] will always use this feature. If a bridge could say "me and my platform both support [bot indicators][MSC4015], go ahead and use them!", any bot supporting bot indicators will already be using them opportunistically. It doesn't make sense to encourage clients to use certain features, when clients already try to use all of their implemented features without being asked.


## Differences to [MSC3968 Poorer Features][MSC3968]


This proposal is based off MSC3968 but has some notable differences:

* Behaviour for clients is defined.
* Desirability levels are simplified. Rather than -100 to +100, there are now 3 possible values with specific meanings.
* Bridges can predict what clients will do for each desirability level.
* This proposal is less extensible and more straight to the point. Rather than limiting individual types, keys, and elements, this proposal limits entire features.
* Extensible events are not specifically mentioned here, since this proposal limits features rather than naming specific parts of event json.
* As Matrix features evolve and are re-specified, the state events will not have to change with them, since the state events only mention general features rather than implementation specific parts of event json.


## Server implementation


Servers do not have to do anything for Fewer Features because it sounds hard. I want to keep this proposal as straightforward as possible. A future MSC could propose behaviour for servers.


## Security considerations


A state event that disables all features would severely degrade the room for everybody. However, such an event can only be sent by room members with sufficient power levels to send state events, which is default PL 50. Modeators with PL 50 can already do a lot of things to mess up the room, such as deleting every event and banning every user. So it is not considered a problem that PL 50 can send this event.

`receive_from_users` with lots of items with wildcards could cause high resource usage for clients. Limiting it to one wildcard per string, combined with the existing maximum event json size, should keep this under control.


## Unstable prefix


While this MSC is in development, `org.matrix.msc4110.event_features` is to be used instead of `m.room.event_features`.


[MSC2346]: https://github.com/matrix-org/matrix-spec-proposals/pull/2346
[MSC3968]: https://github.com/matrix-org/matrix-spec-proposals/pull/3968
[MSC3985]: https://github.com/matrix-org/matrix-spec-proposals/pull/3985
[MSC4015]: https://github.com/matrix-org/matrix-spec-proposals/pull/4015
