# MSC 2346: Bridge information state event

Many rooms across the Matrix network are currently bridged into third party networks, using bridges.
However the spec does not contain a cross-federated method to determine which networks are
bridged into a given room.

There exists a way to do this in a local setting, by using the [/thirdparty/location](https://matrix.org/docs/spec/application_service/r0.1.2#get-matrix-app-v1-thirdparty-protocol-protocol) API but this creates a splitbrain view across the
federation and is an unnacceptable situation.

Many users have taken to peeking at the list of aliases for a giveaway alias like `#freenode_` or
looking for bridge bots or users with a `@_discord_` prefix. This is an unacceptable situation,
as it assumes prior knowledge of these networks and an understanding of how bridges operate.

## Proposal

This proposal attempts to address this problem by providing a single state event for each bridge in a room
to announce what network/channel combination have been bridged into a room.

It should be noted that this MSC is intended to provide the baseline needed to display information about
a bridge, and nothing more.

This proposal is heavily based upon my previous attempt [#1410](https://github.com/matrix-org/matrix-doc/issues/1410)
albeit with a notably reduced set of features. The aim of this proposal is to offer information about the
bridged network and nothing more.

### `m.bridge`

*The name of the event type should eventually be `m.bridge` but has been prefixed until the spec is ready.*

```js
{
    "state_key": "org.matrix.appservice-irc://{protocol.id}/{network.id}/{channel.id}",
    "type": "m.bridge",
    "content": {
        "creator": "@alice:matrix.org", // Optional
        "status": "active" // Optional, will default to active. One of "active", "disabled".
        "protocol": {
            "id": "irc",
            "displayname": "IRC"
        },
        "network": { // Optional
            "id": "freenode",
            "displayname": "Freenode", // Optional
            "avatar": "mxc://foo/bar", // Optional
            "external_url": "irc://chat.freenode.net" // Optional
        },
        "channel": {
            "id": "#friends",
            "displayname": "Friends", // Optional
            "external_url": "irc://chat.freenode.net/#friends" // Optional
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

The `status` field informs the client if the bridge is still active, or has been disabled.

The `protocol` field describes the protocol that is being bridged. For example, it may be "IRC", "Slack", or "Discord". This
field does not describe the low level protocol the bridge is using to access the network, but a common user recongnisable
name. 

The `network` field should be information about the specific network the bridge is connected to. 
It's important to make the distinction here that this does *NOT* describe the protocol name, but the specific network
the user is on. For protocols that do not have the concept of a network, this field may be omitted.

The `channel` field should be information about the specific channel the room is connected to. 

The `external_url` key is a optional link to a connected channel or network that works in much the same way as
`external_url` works for bridged messages in the AS spec.

In terms of hierachy, the protocol can contain many networks, which can contain many channels.

The event may contain information specific to the bridge in question, such as the mode for the room in IRC. These keys
should be prefixed by the bridge's name. Clients may be capable of displaying this extra information and are free to do so.

## /_matrix/app/v1/thirdparty/location

This proposal does NOT seek to deprecate the `location` API even though this spec effectively supercedes it in most respects.
A future MSC may choose to remove it, however.

## Potential issues

The proposal intentionally sidesteps the 'bridge type' problem: Codifing what a portal, plumbed and gatewayed bridge look
like in Matrix. For the time being, the event will not contain information about the type of bridge in a room but merely
information about what is is connected to.

## Alternatives

Some thoughts have been thought on using the third party bridge routes in the AS api to get bridge info,
by calling a specalised endpoint. There are many issues with this, such as the routes not working presently
over federation, as well as requring the bridge to be online. Using a state event ensures the data is scoped
per room, and can be synchronised and updated over federation.

## Future MSCs

(This section is for the beneift of readers to understand why this MSC doesn't contain X feature)

This proposal forms the basis for bridges to become more interactive with clients as first class citizens rather
than relying upon users having prior knowledge about which users are bridged users, or where a room is bridged to.

Future MSCs could expand the /publicRooms response format to show what network a room is bridged to before the
user attempts to join it. Another potential MSC could allow users to see which bridges they are connected to
via an accounts settings page, rather than relying on PMs to the bridge bot.

## Security considerations

Anybody with the correct PLs to post state events will be able to manipulate a room by sending a bridge
event into a room, even if the bridge is not present or does not exist. It goes without saying that if
you let people modify your room state, you need to trust them not to mess around. A future MSC may allow
users to "trust" some mxids as bridges, rather than relying on just PLs to convey trustworthiness.
