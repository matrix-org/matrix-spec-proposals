---
type: module
---

### Push Notifications

```
                                   +--------------------+  +-------------------+
                  Matrix HTTP      |                    |  |                   |
             Notification Protocol |   App Developer    |  |   Device Vendor   |
                                   |                    |  |                   |
           +-------------------+   | +----------------+ |  | +---------------+ |
           |                   |   | |                | |  | |               | |
           | Matrix homeserver +----->  Push Gateway  +------> Push Provider | |
           |                   |   | |                | |  | |               | |
           +-^-----------------+   | +----------------+ |  | +----+----------+ |
             |                     |                    |  |      |            |
    Matrix   |                     |                    |  |      |            |
 Client/Server API  +              |                    |  |      |            |
             |      |              +--------------------+  +-------------------+
             |   +--+-+                                           |
             |   |    <-------------------------------------------+
             +---+    |
                 |    |          Provider Push Protocol
                 +----+
          Mobile Device or Client
```

This module adds support for push notifications. Homeservers send
notifications of events to user-configured HTTP endpoints. Users may
also configure a number of rules that determine which events generate
notifications. These are all stored and managed by the user's
homeserver. This allows user-specific push settings to be reused between
client applications.

The above diagram shows the flow of push notifications being sent to a
handset where push notifications are submitted via the handset vendor,
such as Apple's APNS or Google's GCM. This happens as follows:

1.  The client app signs in to a homeserver.
2.  The client app registers with its vendor's Push Provider and obtains
    a routing token of some kind.
3.  The mobile app uses the Client/Server API to add a 'pusher',
    providing the URL of a specific Push Gateway which is configured for
    that application. It also provides the routing token it has acquired
    from the Push Provider.
4.  The homeserver starts sending HTTP requests to the Push Gateway
    using the supplied URL. The Push Gateway relays this notification to
    the Push Provider, passing the routing token along with any
    necessary private credentials the provider requires to send push
    notifications.
5.  The Push Provider sends the notification to the device.

Definitions for terms used in this section are below:

Push Provider
A push provider is a service managed by the device vendor which can send
notifications directly to the device. Google Cloud Messaging (GCM) and
Apple Push Notification Service (APNS) are two examples of push
providers.

Push Gateway
A push gateway is a server that receives HTTP event notifications from
homeservers and passes them on to a different protocol such as APNS for
iOS devices or GCM for Android devices. Clients inform the homeserver
which Push Gateway to send notifications to when it sets up a Pusher.

Pusher
A pusher is a worker on the homeserver that manages the sending of HTTP
notifications for a user. A user can have multiple pushers: one per
device.

Push Rule
A push rule is a single rule that states under what *conditions* an
event should be passed onto a push gateway and *how* the notification
should be presented. These rules are stored on the user's homeserver.
They are manually configured by the user, who can create and view them
via the Client/Server API.

Push Ruleset
A push ruleset *scopes a set of rules according to some criteria*. For
example, some rules may only be applied for messages from a particular
sender, a particular room, or by default. The push ruleset contains the
entire set of scopes and rules.

#### Client behaviour

Clients MUST configure a Pusher before they will receive push
notifications. There is a single API endpoint for this, as described
below.

{{% http-api spec="client-server" api="pusher" %}}

##### Listing Notifications

A client can retrieve a list of events that it has been notified about.
This may be useful so that users can see a summary of what important
messages they have received.

{{% http-api spec="client-server" api="notifications" %}}

##### Receiving notifications

Servers MUST include the number of unread notifications in a client's
`/sync` stream, and MUST update it as it changes. Notifications are
determined by the push rules which apply to an event.

When the user updates their read receipt (either by using the API or by
sending an event), notifications prior to and including that event MUST
be marked as read.

##### Push Rules

A push rule is a single rule that states under what *conditions* an
event should be passed onto a push gateway and *how* the notification
should be presented. There are different "kinds" of push rules and each
rule has an associated priority. Every push rule MUST have a `kind` and
`rule_id`. The `rule_id` is a unique string within the kind of rule and
its' scope: `rule_ids` do not need to be unique between rules of the
same kind on different devices. Rules may have extra keys depending on
the value of `kind`.

The different `kind`s of rule, in the order that they are checked, are:

Override Rules `override`
The highest priority rules are user-configured overrides.

Content-specific Rules `content`
These configure behaviour for (unencrypted) messages that match certain
patterns. Content rules take one parameter: `pattern`, that gives the
glob pattern to match against. This is treated in the same way as
`pattern` for `event_match`.

Room-specific Rules `room`
These rules change the behaviour of all messages for a given room. The
`rule_id` of a room rule is always the ID of the room that it affects.

Sender-specific rules `sender`
These rules configure notification behaviour for messages from a
specific Matrix user ID. The `rule_id` of Sender rules is always the
Matrix user ID of the user whose messages they'd apply to.

Underride rules `underride`
These are identical to `override` rules, but have a lower priority than
`content`, `room` and `sender` rules.

Rules with the same `kind` can specify an ordering priority. This
determines which rule is selected in the event of multiple matches. For
example, a rule matching "tea" and a separate rule matching "time" would
both match the sentence "It's time for tea". The ordering of the rules
would then resolve the tiebreak to determine which rule is executed.
Only `actions` for highest priority rule will be sent to the Push
Gateway.

Each rule can be enabled or disabled. Disabled rules never match. If no
rules match an event, the homeserver MUST NOT notify the Push Gateway
for that event. Homeservers MUST NOT notify the Push Gateway for events
that the user has sent themselves.

###### Actions

All rules have an associated list of `actions`. An action affects if and
how a notification is delivered for a matching event. The following
actions are defined:

`notify`
This causes each matching event to generate a notification.

`dont_notify`
This prevents each matching event from generating a notification

`coalesce`
This enables notifications for matching events but activates homeserver
specific behaviour to intelligently coalesce multiple events into a
single notification. Not all homeservers may support this. Those that do
not support it should treat it as the `notify` action.

`set_tweak`
Sets an entry in the `tweaks` dictionary key that is sent in the
notification request to the Push Gateway. This takes the form of a
dictionary with a `set_tweak` key whose value is the name of the tweak
to set. It may also have a `value` key which is the value to which it
should be set.

The following tweaks are defined:

* `sound`: A string representing the sound to be played when this notification
arrives. A value of `default` means to play a default sound. A device
may choose to alert the user by some other means if appropriate, eg.
vibration.

* `highlight`: A boolean representing whether or not this message should be highlighted
in the UI. This will normally take the form of presenting the message in
a different colour and/or style. The UI might also be adjusted to draw
particular attention to the room in which the event occurred. If a
`highlight` tweak is given with no value, its value is defined to be
`true`. If no highlight tweak is given at all then the value of
`highlight` is defined to be false.

Tweaks are passed transparently through the homeserver so client
applications and Push Gateways may agree on additional tweaks. For
example, a tweak may be added to specify how to flash the notification
light on a mobile device.

Actions that have no parameters are represented as a string. Otherwise,
they are represented as a dictionary with a key equal to their name and
other keys as their parameters, e.g.
`{ "set_tweak": "sound", "value": "default" }`

###### Conditions

`override` and `underride` rules MAY have a list of 'conditions'. All
conditions must hold true for an event in order for the rule to match. A
rule with no conditions always matches.

Unrecognised conditions MUST NOT match any events, effectively making
the push rule disabled.

`room`, `sender` and `content` rules do not have conditions in the same
way, but instead have predefined conditions. In the cases of `room` and
`sender` rules, the `rule_id` of the rule determines its behaviour.

The following conditions are defined:

**`event_match`**

This is a glob pattern match on a field of the event. Parameters:

-   `key`: The dot-separated path of the property of the event to match, e.g.
    `content.body`.

-   `pattern`: The glob-style pattern to match against.

The match is performed case-insensitively, and must match the entire value of
the event field given by `key` (though see below regarding `content.body`). The
exact meaning of "case insensitive" is defined by the implementation of the
homeserver.

Within `pattern`:

  * The character `*` matches zero or more characters.
  * `?` matches exactly one character.

If the property specified by `key` is completely absent from the event, or does
not have a string value, then the condition will not match, even if `pattern`
is `*`.

{{% boxes/note %}}
For example, if `key` is `content.topic`, and `pattern` is `lunc?*`, then
the following event will match:

```json
{
  "content": {
    "topic": "Lunch plans",
  },
  "event_id": "$143273582443PhrSn:example.org",
  "room_id": "!636q39766251:example.com",
  "sender": "@example:example.org",
  "state_key": "",
  "type": "m.room.topic"
}
```

Other `topic` values which will match are:

 * `"LUNCH"` (case-insensitive; `*` may match zero characters)

The following `membership` values will NOT match:
 * `" lunch"` (note leading space)
 * `"lunc"` (`?` must match a character)
 * `null` (not a string)
{{% /boxes/note %}}

As a special case, if `key` is `content.body`, then `pattern` must instead
match any substring of the value of the property which starts and ends at a
word boundary. A word boundary is defined as the start or end of the value, or
any character not in the sets `[A-Z]`, `[a-z]`, `[0-9]` or `_`.

{{% boxes/note %}}
For example, if `key` is `content.body` and `pattern` is `ex*ple`, the
following event will match:

```json
{
  "content": {
    "body": "An example event.",
  },
  "event_id": "$143273976499sgjks:example.org",
  "room_id": "!636q39766251:example.com",
  "sender": "@example:example.org",
  "type": "m.room.message"
}
```

Other `body` values which will match are:

 * `"exple"` (the pattern can match at the start and end of the body.)
 * `"An exciting triple-whammy"` (the pattern can span multiple words, and `-`
   acts as a word separator.)
{{% /boxes/note %}}


{{% boxes/warning %}}
Note that there is no implicit condition for `state_key`. In other words, push
rules which should match only state events must include an explicit condition
for `state_key`.

For an example of this, see the default rule
[`.m.rule.tombstone`](#mruletombstone) below.
{{% /boxes/warning %}}

**`contains_display_name`**

This matches unencrypted messages where `content.body` contains the
owner's display name in that room. This is a separate rule because
display names may change and as such it would be hard to maintain a rule
that matched the user's display name. This condition has no parameters.

**`room_member_count`**

This matches the current number of members in the room. Parameters:

-   `is`: A decimal integer optionally prefixed by one of, `==`, `<`,
    `>`, `>=` or `<=`. A prefix of `<` matches rooms where the member
    count is strictly less than the given number and so forth. If no
    prefix is present, this parameter defaults to `==`.

**`sender_notification_permission`**

This takes into account the current power levels in the room, ensuring
the sender of the event has high enough power to trigger the
notification.

Parameters:

-   `key`: A string that determines the power level the sender must have
    to trigger notifications of a given type, such as `room`. Refer to
    the [m.room.power\_levels](#mroompower_levels) event schema for information about what
    the defaults are and how to interpret the event. The `key` is used
    to look up the power level required to send a notification type from
    the `notifications` object in the power level event content.

##### Predefined Rules

Homeservers can specify "server-default rules" which operate at a lower
priority than "user-defined rules". The `rule_id` for all server-default
rules MUST start with a dot (".") to identify them as "server-default".
The following server-default rules are specified:

###### Default Override Rules

**`.m.rule.master`**

Matches all events. This can be enabled to turn off all push
notifications other than those generated by override rules set by the
user. By default this rule is disabled.

Definition:

```json
{
    "rule_id": ".m.rule.master",
    "default": true,
    "enabled": false,
    "conditions": [],
    "actions": [
        "dont_notify"
    ]
}
```

**`.m.rule.suppress_notices`**

Matches messages with a `msgtype` of `notice`.

Definition:

```json
{
    "rule_id": ".m.rule.suppress_notices",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_match",
            "key": "content.msgtype",
            "pattern": "m.notice",
        }
    ],
    "actions": [
        "dont_notify",
    ]
}
```

**`.m.rule.invite_for_me`**

Matches any invites to a new room for this user.

Definition:

```json
{
    "rule_id": ".m.rule.invite_for_me",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "key": "type",
            "kind": "event_match",
            "pattern": "m.room.member"
        },
        {
            "key": "content.membership",
            "kind": "event_match",
            "pattern": "invite"
        },
        {
            "key": "state_key",
            "kind": "event_match",
            "pattern": "[the user's Matrix ID]"
        }
    ],
    "actions": [
       "notify",
        {
            "set_tweak": "sound",
            "value": "default"
        }
    ]
}
```

**`.m.rule.member_event`**

Matches any `m.room.member_event`.

Definition:

```json
{
    "rule_id": ".m.rule.member_event",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "key": "type",
            "kind": "event_match",
            "pattern": "m.room.member"
        }
    ],
    "actions": [
        "dont_notify"
    ]
}
```

**`.m.rule.contains_display_name`**

Matches any message whose content is unencrypted and contains the user's
current display name in the room in which it was sent.

Definition:

```json
{
    "rule_id": ".m.rule.contains_display_name",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "contains_display_name"
        }
    ],
    "actions": [
        "notify",
        {
            "set_tweak": "sound",
            "value": "default"
        },
        {
            "set_tweak": "highlight"
        }
    ]
}
```

**<a name="mruletombstone"></a>`.m.rule.tombstone`**

Matches any state event whose type is `m.room.tombstone`. This is
intended to notify users of a room when it is upgraded, similar to what
an `@room` notification would accomplish.

Definition:

```json
{
    "rule_id": ".m.rule.tombstone",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_match",
            "key": "type",
            "pattern": "m.room.tombstone"
        },
        {
            "kind": "event_match",
            "key": "state_key",
            "pattern": ""
        }
    ],
    "actions": [
        "notify",
        {
            "set_tweak": "highlight"
        }
    ]
}
```

**`.m.rule.roomnotif`**

Matches any message whose content is unencrypted and contains the text
`@room`, signifying the whole room should be notified of the event.

Definition:

```json
{
    "rule_id": ".m.rule.roomnotif",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_match",
            "key": "content.body",
            "pattern": "@room"
        },
        {
            "kind": "sender_notification_permission",
            "key": "room"
        }
    ],
    "actions": [
        "notify",
        {
            "set_tweak": "highlight"
        }
    ]
}
```

###### Default Content Rules

**`.m.rule.contains_user_name`**

Matches any message whose content is unencrypted and contains the local
part of the user's Matrix ID, separated by word boundaries.

Definition (as a `content` rule):

```json
{
    "rule_id": ".m.rule.contains_user_name",
    "default": true,
    "enabled": true,
    "pattern": "[the local part of the user's Matrix ID]",
    "actions": [
        "notify",
        {
            "set_tweak": "sound",
            "value": "default"
        },
        {
            "set_tweak": "highlight"
        }
    ]
}
```

###### Default Underride Rules

**`.m.rule.call`**

Matches any incoming VOIP call.

Definition:

```json
{
    "rule_id": ".m.rule.call",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "key": "type",
            "kind": "event_match",
            "pattern": "m.call.invite"
        }
    ],
    "actions": [
        "notify",
        {
            "set_tweak": "sound",
            "value": "ring"
        }
    ]
}
```

**`.m.rule.encrypted_room_one_to_one`**

Matches any encrypted event sent in a room with exactly two members.
Unlike other push rules, this rule cannot be matched against the content
of the event by nature of it being encrypted. This causes the rule to be
an "all or nothing" match where it either matches *all* events that are
encrypted (in 1:1 rooms) or none.

Definition:

```json
{
    "rule_id": ".m.rule.encrypted_room_one_to_one",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "room_member_count",
            "is": "2"
        },
        {
            "kind": "event_match",
            "key": "type",
            "pattern": "m.room.encrypted"
        }
    ],
    "actions": [
        "notify",
        {
            "set_tweak": "sound",
            "value": "default"
        }
    ]
}
```

**`.m.rule.room_one_to_one`**

Matches any message sent in a room with exactly two members.

Definition:

```json
{
    "rule_id": ".m.rule.room_one_to_one",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "room_member_count",
            "is": "2"
        },
        {
            "kind": "event_match",
            "key": "type",
            "pattern": "m.room.message"
        }
    ],
    "actions": [
        "notify",
        {
            "set_tweak": "sound",
            "value": "default"
        }
    ]
}
```

**`.m.rule.message`**

Matches all chat messages.

Definition:

```json
{
     "rule_id": ".m.rule.message",
     "default": true,
     "enabled": true,
     "conditions": [
         {
             "kind": "event_match",
             "key": "type",
             "pattern": "m.room.message"
         }
     ],
     "actions": [
         "notify"
     ]
}
```

**`.m.rule.encrypted`**

Matches all encrypted events. Unlike other push rules, this rule cannot
be matched against the content of the event by nature of it being
encrypted. This causes the rule to be an "all or nothing" match where it
either matches *all* events that are encrypted (in group rooms) or none.

Definition:

```json
{
     "rule_id": ".m.rule.encrypted",
     "default": true,
     "enabled": true,
     "conditions": [
         {
             "kind": "event_match",
             "key": "type",
             "pattern": "m.room.encrypted"
         }
     ],
     "actions": [
         "notify"
     ]
}
```

##### Push Rules: API

Clients can retrieve, add, modify and remove push rules globally or
per-device using the APIs below.

{{% http-api spec="client-server" api="pushrules" %}}

##### Push Rules: Events

When a user changes their push rules a `m.push_rules` event is sent to
all clients in the `account_data` section of their next `/sync` request.
The content of the event is the current push rules for the user.

{{% event event="m.push_rules" %}}

###### Examples

To create a rule that suppresses notifications for the room with ID
`!dj234r78wl45Gh4D:matrix.org`:

    curl -X PUT -H "Content-Type: application/json" "https://example.com/_matrix/client/v3/pushrules/global/room/%21dj234r78wl45Gh4D%3Amatrix.org?access_token=123456" -d \
    '{
       "actions" : ["dont_notify"]
     }'

To suppress notifications for the user `@spambot:matrix.org`:

    curl -X PUT -H "Content-Type: application/json" "https://example.com/_matrix/client/v3/pushrules/global/sender/%40spambot%3Amatrix.org?access_token=123456" -d \
    '{
       "actions" : ["dont_notify"]
     }'

To always notify for messages that contain the work 'cake' and set a
specific sound (with a rule\_id of `SSByZWFsbHkgbGlrZSBjYWtl`):

    curl -X PUT -H "Content-Type: application/json" "https://example.com/_matrix/client/v3/pushrules/global/content/SSByZWFsbHkgbGlrZSBjYWtl?access_token=123456" -d \
    '{
       "pattern": "cake",
       "actions" : ["notify", {"set_sound":"cakealarm.wav"}]
     }'

To add a rule suppressing notifications for messages starting with
'cake' but ending with 'lie', superseding the previous rule:

    curl -X PUT -H "Content-Type: application/json" "https://example.com/_matrix/client/v3/pushrules/global/content/U3BvbmdlIGNha2UgaXMgYmVzdA?access_token=123456&before=SSByZWFsbHkgbGlrZSBjYWtl" -d \
    '{
       "pattern": "cake*lie",
       "actions" : ["notify"]
     }'

To add a custom sound for notifications messages containing the word
'beer' in any rooms with 10 members or fewer (with greater importance
than the room, sender and content rules):

    curl -X PUT -H "Content-Type: application/json" "https://example.com/_matrix/client/v3/pushrules/global/override/U2VlIHlvdSBpbiBUaGUgRHVrZQ?access_token=123456" -d \
    '{
       "conditions": [
         {"kind": "event_match", "key": "content.body", "pattern": "beer" },
         {"kind": "room_member_count", "is": "<=10"}
       ],
       "actions" : [
         "notify",
         {"set_sound":"beeroclock.wav"}
       ]
     }'

#### Server behaviour

#### Push Gateway behaviour

##### Recommendations for APNS

The exact format for sending APNS notifications is flexible and up to
the client app and its' push gateway to agree on. As APNS requires that
the sender has a private key owned by the app developer, each app must
have its own push gateway. It is recommended that:

-   The APNS token be base64 encoded and used as the pushkey.
-   A different app\_id be used for apps on the production and sandbox
    APS environments.
-   APNS push gateways do not attempt to wait for errors from the APNS
    gateway before returning and instead to store failures and return
    'rejected' responses next time that pushkey is used.

#### Security considerations

Clients specify the Push Gateway URL to use to send event notifications
to. This URL should be over HTTPS and *never* over HTTP.

As push notifications will pass through a Push Provider, message content
shouldn't be sent in the push itself where possible. Instead, Push
Gateways should send a "sync" command to instruct the client to get new
events from the homeserver directly.
