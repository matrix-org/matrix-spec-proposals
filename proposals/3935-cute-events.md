# MSC3935: Cute Events against social distancing

*Many people suffer from social isolation, distancing and from their friends
being far away. This MSC aims to give Matrix the capability to overcome
social distance by sending Cute Events: Googly Eyes, Hugs and Cuddles.*

This MSC targets this problem by introducing a new `msgtype` for
`m.room.message` named `m.cute_event`. Cute events should provide fallback
conent as Unicoe Emotes. Suppoted clients can render these events in a special,
emotional way.

## Proposal

This MSC extends `m.room.message` by an additional `msgtype` named `m.cute_event`.

Cute events provide the following social actions: Googly Eyes (`googly_eyes`),
Hugs (`hug`) and Cuddles (`cuddle`).

The specified type is contained in the event's content under the key `type`.

The `body` MUST contain a fallback for unsupported clients as Unicode Emote.
The emote used for representation of the particular Cute Event is chosen by
the client.

Example:

```json5
{
    "type": "m.room.message",
    "content": {
        "msgtype": "m.cute_event",
        "type": "googly_eyes",
        "body": "👀"
    }
}
```

The client SHOULD render the events in a way that:

- the event is displayed in the timeline
    - either, the sent `body` is used
    - or there's a per-type implementation using e.g. advanced animatons
- the event could also trigger bigger UI changed, such as randomly appearing
  animations depicting the desired animation on random places of the screen

## Potential issues

This MSC instroduces potential issues in regard of accessibility. They are
discussed below in the [Security](#Security considerations) section.

## Alternatives

A conscidered alternative to Cute Events are MSC2545 -  Image Packs
(Emoticons & Stickers). They lack the personalized component and a feature to appear randomly, a more customized msgtype as the Cute Events is appreciated in order to create a more personal expearience.


## Security considerations

This change is not relevant in regard of data security. However, there have
already been conscerns about accessibility in regard of suddenly appearing
contents. This SHOULD be addressed by the clients by addin an option to
deactivate automatic appearance of cute events.

## Unstable prefix

The initial implementation is found in the
[Matrix Dart SDK](https://gitlab.com/famedly/company/frontend/famedlysdk/-/merge_requests/1168),
prefixed as: `im.fluffychat.cute_event`. An
[open MR for FluffyChat](https://gitlab.com/famedly/fluffychat/-/merge_requests/1031) exists.

## Dependencies

This MSC dos not have any particular dependency.

