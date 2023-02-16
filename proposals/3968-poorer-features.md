# MSC3968: Poorer features

Matrix owes its name to its aim to interoperate with many protocols, by being supporting a superset
of their individual features. While this is great to bridge events from other protocols to Matrix,
this causes friction in the other direction, as events need to be either converted to a fallback
(that may not be natural to the target platform) or silently dropped altogether.

Additionally, room administrators may also prefer to forbid some features in order to ease moderation,
cater to specific needs of their community, or provide a different experience of Matrix.

This MSC aims to provide a way for bridges and room administrators to signal which features senders
should avoid using. This allows clients to hide elements from their UI, provide an error or warning
early to the user, or themselves fallback using any extra context they may have.


## Proposal

This MSC introduces a new `m.room.event_features` state event type, which associates a desirability
level to:

- attachment mimetypes for `m.file`, `m.audio`, `m.video`, ... events;
- `msgtype` values
- (for clients implementing [MSC1767][MSC1767]) to mimetypes used in extensible events;
- keys in `"content"` objects;
- HTML elements

Mimetypes, msgtype values, keys, and HTML element names are jointly referred to as "entities" below.


### Desirability level

This level is an integer, whose values are defined as:

- under -100: this entity is forbidden, and must not be sent in any case.
  Clients receiving events containing them should hide them from their users
  (or display these events without as if they didn't contain the entity)
- from -100 to -1: this entity is discouraged, and should not be sent unless there is
  no alternative.
  Clients receiving these events may hide them from their users
  (or display these events without as if they didn't contain the entity)
- 0 to 100: this entity is acceptable
- over 100: currently undefined, and should be interpreted as 100


Unlike `m.room.power_levels`, `m.room.event_features` acts on event content, so it is enforced
primarily by receiving clients.

Servers may apply restrictions before sending unencrypted events, and return `M_FORBIDDEN`
in case the event contains an entity with a level under 0.
Receiving servers may hide such events from their clients.


### Format of `m.room.event_features`

`m.room.event_features` events may have these keys:

- `attachment_mimetypes` (object with integer values): This is a mapping from file mimetypes
  to desirability level
- `attachment_mimetypes_default` (integer): the default desirability level for file mimetypes
  Can be overridden by the `content_mimetypes` key. Defaults to 0 if unspecified.
- `content_mimetypes` (object with integer values): This is a mapping from content mimetype
  (as per MSC1767) to desirability level
- `content_mimetypes_default` (integer): the default desirability level for content mimetypes
  (as per MSC1767). `*` may be used as a wildcard.
  Can be overridden by the `content_mimetypes` key. Defaults to 0 if unspecified.
- `keys` (object with integer values): This is a mapping from key name to desirability level
- `keys_default` (integer): the default desirability level for keys.
  Can be overridden by the `keys` key. Defaults to 0 if unspecified.
- `html_elements` (object with integer values): This is a mapping from HTML element name to desirability level
- `html_elements_default` (integer): the default desirability level for HTML elements.
  Can be overridden by the `html_elements` key. Defaults to 0 if unspecified.
- `msgtypes` (object with integer values): This is a mapping from `msgtype` of `m.room.message`
  events to desirability level
- `msgtypes_default` (integer): the default desirability level for values of `msgtype`
  in `m.room.message` events.
  Can be overridden by the `msgtypes` key. Defaults to 0 if unspecified.

Values not matching these types and undefined keys should be ignored.

`m.room.event_features` events with a non-empty state key should be ignored.


### Examples


#### matrix-appservice-irc

To forbid features known not to gracefully degrade on matrix-appservice-irc
as of 2023-02 (ie. outside RFC1459 and sending files), that is:

```json5
{
    "content": {
        "keys": {
            "m.in_reply_to": -50,  // replies
            "m.new_content": -100,  // edits
            "m.relates_to": -1,  // Other relations are unlikely to be bridged gracefully
            // encrypted files:
            "file": -100,
            "thumbnail_file": -100
        },
        // discourage HTML elements with no counterpart on IRC:
        "html_elements_default": -1,
        "html_elements": {
            "a": 0,
            "b": 0,
            "code": 0,
            "dive": 0,
            "font": 0,
            "p": 0,
            "pre": 0,
            "i": 0,
            "u": 0,
            "span": 0,
            "strong": 0,
            "em": 0,
            "strike": 0
        },
        // forbid text messages which are neither text nor HTML (eg. `m.location`),
        // and encourage text messages over media (which IRC users may prefer not to display inline):
        "mimetypes_default": -100,
        "mimetypes": {
            "text/plain": 0,
            "text/html": 0
        },
        "msgtypes_default": -100,
        "msgtypes": {
            "m.audio": 0,
            "m.emote": 100,
            "m.file": 0,
            "m.image": 0,
            "m.notice": 100,
            "m.text": 100,
            "m.video": 0,
            "m.server_notice": 0
        }
    },
    "sender": "@appservice:example.com",
    "state_key": "",
    "type": "m.room.event_features"
}
```

#### Easing moderation

Rooms whose moderators cannot listen to content on the fly can forbid them:

```json5
{
    "content": {
        "mimetypes": {
            "audio/*": -100,
            "video/*": -100
        },
        "msgtypes": {
            "m.audio": -100,
            "m.video": -100
        }
    },
    "sender": "@room-admin:example.com",
    "state_key": "",
    "type": "m.room.event_features"
}
```


## Potential issues

Clients not implementing this MSC will allow their users to send events hidden from other users.
This is already a problem when sending event types not supported by other clients, but in order
to minimize further impact, the following precautions should be taken until this MSC is widely
implemented:

- room administrators are discouraged from configuring levels under -100
- developers are discouraged from hiding events matching desirability levels from -100 and -1

New/updated `m.room.event_features` state events may race with new events.
Receiving clients/servers should allow a short grace period if possible before hiding
or dropping events.

When backfilling history backward, clients should consider they may receive a
`m.room.event_features` event that predates events they already received.


## Alternatives

- giving a name to every feature (or use MSC number) and attribute a desirability level to each
  of these names. While this makes `m.room.event_features` more readable from developer tools,
  it adds an extra burdens on clients and servers to keep track of these names and map them to
  entities anyway
- using `"forbidden"`, `"discouraged"`, and `"acceptable"` as levels instead of integers.
  This prevents finer grained display rules (eg. receiving clients may choose to hide events matching
  levels under -50, because they are "very discouraged" by the administrator) and future
  extendability (eg. values over 100 meaning an entity is required).
  Integer values also gives sending clients the option to prioritize some UI elements over others,
  in order to send "acceptable" entities with higher desirability levels if they have to choose
  one over the other (eg. default to picture vs video vs audio recording based on the room).
- Making clients bundle a list of known limits for each bridge and rely on [MSC2346][MSC2346]
  to allow them to discover bridges in a room.
  This puts a significant maintenance burden on clients, requires users to constantly update
  them to match new bridges (or new bridge configurations), may lead to different Matrix clients
  showing different sets of events, does not allow room administrators to set arbitrary limits.
- also including event types (eg. to forbid `m.sticker`), but this is better dealt with using
  `m.room.power_levels`


## Security considerations

Clients should not expect or rely on servers blocking or hiding "forbidden" or "discouraged"
entities, even when events are not end-to-end encrypted.

Different clients may see different things (but it is already an issue with `body`/`formatted_body`
or with [MSC1767][MSC1767]), allowing abusers to send messages targeted to certain (classes of) users
via public rooms.
It is therefore recommended for receiving clients and servers not to hide these events from
users with some sort of moderation powers (eg. power-level over 50, or high enough to issue
kicks or redactions).


## Unstable prefix

During development, `org.matrix.msc3968.room.event_features` is to be used
instead of `m.room.event_features`.


## Dependencies

This MSC builds on [MSC1767][MSC1767], though clients not implementing MSC1767 can simply ignore
parts related to mimetypes, as they have nothing to enforce anyway.


[MSC1767]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767
[MSC2346]: https://github.com/matrix-org/matrix-spec-proposals/pull/2346
