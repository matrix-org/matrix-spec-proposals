### MSC XXXX: Bridge information state event

Many rooms across the matrix network are currently bridged into other networks, using our bridging API.
However the specification does not contain a method to determine which networks are bridged into a given
room. Many users have taken to peeking at the list of aliases for a giveaway alias like `#freenode_` or
looking for bridge bots or users with a `@_discord_` prefix.

This is an unacceptable situation. Users must know beforehand the names of IRC networks or protocols in order
to determine if a given ID is part of a bridge. The bridge cannot give away any infomation about itself
via Matrix. And blah blah blah. It alos allows bridges to be re-usable between different servers should we
want to go for the decentralised route one day.

This proposal stands to fix, or partially fix the following issues:
 - a bunch of riot projects that depend upon this
 - a bunch of spec items too

This proposal is heavily based upon my previous attempt [#1410](https://github.com/matrix-org/matrix-doc/issues/1410)
albeit with a notably reduced set of features. The aim of this proposal is to offer information about the
bridged network and nothing more.

## Proposal

This proposal uses

It should be noted that this MSC is intended to provide the baseline needed to display information about
a bridge. Future MSCs should be written to expand this event as the need arises.

### `org.matrix.bridge`

*The name of the event type should eventually be `m.bridge` but has been prefixed until the spec is ready.*

```js
{
    "state_key": "org.matrix.appservice-irc://network_id/channel_id",
    "type": "org.matrix.bridge"
    "content": {
        "creator": "@alice:matrix.org", // Optional
        "status": "active" // Optional, will default to active. One of "active", "disabled".
        "network": {
            "id": "freenode",
            "displayname": "Freenode", // Optional
            "avatar": "mxc://foo/bar" // Optinal
        },
        "channel": {
            "id": "#friends",
            "displayname": "Friends" // Optional
        },
        // Custom vendor-specific keys
        "org.matrix.appservice-irc.room_mode": "+sn",
    },
    "sender": "@appservice-irc:matrix.org"
}
```

The `state_key` must be comprised of the bridge's prefix, followed by the `network.id`, followed by the `channel.id`.

The `sender` should be the MXID of the bridge bot.

The `creator` field is the name of the *user* which provisioned the bridge. In the case of alias based bridges, where the
creator is not known -- it may be omitted.

The `status` field informs the client if the bridge is still active, or has been disabled. The meaning may be different
depending on the context of the network.

The `network` field should be information about the specific network the bridge is connected to. This may be "Freenode" for IRC,
or "Discord" if the network is global. (What does this mean?).

The event may contain information specific to the bridge in question, such as the mode for the room in IRC. These keys
should be prefixed by the bridge's name. Clients may be capable of displaying this extra information and are free to do so.

## Potential issues

This proposal knowingly discards some information present in #1410. These were removed to allow the MSC to pass quicker
through the process, as well as some of the information having limited value to clients.

The proposal intentionally sidesteps the 'bridge type' problem: Codifing what a portal, plumbed and gatewayed bridge look
like in Matrix. For the time being, the event will not contain information about the type of bridge in a room but merely
information about what is is connected to.

## Alternatives

Some thoughts have been thought on using the third party bridge routes in the AS api to get bridge info,
by calling a specalised endpoint. There are many issues with this, such as the routes not working presently
over federation, as well as requring the bridge to be online. Using a state event ensures the data is scoped
per room, and can be synchronised and updated over federation.

## Security considerations

Anybody with the correct PLs to post state events will be able to manipulate a room by sending a bridge
event into a room , even if the bridge is not present or does not exist. It goes without saying that if
you let people modify your room state, you need to trust them not to mess around.