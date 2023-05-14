# MSC4015: Voluntary Bot indicators

Knowing if a user is a bot is currently hard in Matrix. It currently relies heavily on the Displayname,
mxid or operating server.

Other networks commonly have indicators that a user is a Bot. In most cases, this is done by having
a dedicated API that is used by Bots. Matrix doesn't have any dedicated API. However, it can have
an indicator instead.

A flag would allow to more easily identify bots both in the timeline but crucially also allow them
to be quickly visible within the room member list.
Additionally, the flag allows bridges to mark bots from networks like discord, IRC or ActivityPub
to be marked as bots and therefore retaining the UX they have on the origin network.


## Proposal

Adding a marker to the member event content if a user is a bot. This can be set by the User itself
and is voluntary.

This flag cannot be enforced technically since there is no difference in a bot or a normal user on
the technical side. So we need to rely on the user. Furthermore, this flag is not supposed to be used
to detect spambots. It doesn't come with guarantees.

### Example

Such an example member event should look like this:

```json5
{
  "content": {
    "avatar_url": "mxc://example.org/SEsfnsuifSDFSSEF",
    "displayname": "Alice Connector",
    "membership": "join",
    "reason": "Looking for support",
    // The new flag.
    "bot": true
  },
  "event_id": "$143273582443PhrSn:example.org",
  "origin_server_ts": 1432735824653,
  "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
  "sender": "@example:example.org",
  "state_key": "@alice:example.org",
  "type": "m.room.member",
  "unsigned": {
    "age": 1234
  }
}
```

### Details of the flag

The flag consists of a boolean flag in the `content` of the event. It can therefore take either
the values `true` or `false` but also can be omitted. In this case, the user should be considered
`not a bot`.

## Potential issues

People might wrongly assume that this flag is always present and use it either for moderation tools
or get blinded by it and assume that it's always set when you are a bot.
These are currently limitations that are beyond the scope of this MSC.

We already have `m.notice` events these days. However, contrary to this MSC they are more invasive in
behaviour of the bots. Not only do they mark messages as bot messages commonly, but they also change
the notification settings. While this might make sense for most bots, there are bots where it is
reasonable to send the messages as normal messages instead. This applies for example to files,
reminder bots or similar bots that either have no way to make their event m.notice due to the event type
or are requiring notifications to behave normally due to the function of the bot.


## Alternatives

An alternative to using a single flag for `bots` it could make sense to have member types similar to
how room types work. Here a user could be `m.bot`, `m.puppet` or similar.


## Security considerations

The spec text should make sure that people understand that this is voluntary and bots might not set it.
This is to prevent confusion by implementors.

## Unstable prefix

As an unstable prefix, users should use `dev.nordgedanken.msc4015` instead of `bot`

## Dependencies

This MSC has no known dependencies
