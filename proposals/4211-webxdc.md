# MSC4211: WebXDC on Matrix


In Matrix, users may want to send each other interactive content (for example a game
in a groupchat, or maybe a collaborative board). Previously, integrations were used 
to provide such content, but they are not in-band (thus needs another server, which 
tends to be unmaintained as of now). As such, this proposal aims to resolve this by
adding [WebXDC](https://webxdc.org/) into the Matrix client ecosystem, with no 
server-side changes or additions needed to existing Matrix interfaces.

## Proposal

A common method, with a well-defined API and that isn't locked to the Matrix ecosystem
(which may be useful for, e.g bridges, which would greatly benefit from such a common 
system, and even client developers, who can simply rely on pre-existing tooling) and 
that wouldn't require server administrators to either host another software solution 
or users to resort to a centralised hub(as integrations) would be highly appreciable.

(Please note that the following simply describes how WebXDC calls transmate to 
Matrix events. More information is available at WebXDC's 
[own specification](https://webxdc.org/docs/spec/index.html))

To start a WebXDC event, a client may start by sending a `m.webxdc.start` event, 
formatted as such:
```jsonc
{
    "content": {
        "name": "Storm on Mt. Ooe", // optional, must be a string
        "url": "mxc://hell.club/WebXDCFileForClients",  // MUST be a .xdc file
        "icon": "mxc://hell.club/AnIconForTheWebXDC",   // optional,
                                                        // content.icon_mime must exist 
                                                        // iff present
        "icon_mime": "image/png"                        // present IFF content.icon is present
    },
    "room_id": "!former:hell.club",
    "event_id": "$WebXDCStart1",
    "sender": "@yuugi:hell.club",
    "type": "m.webxdc.start"
    ...
}
```
where the `content.url` field must be a MXC URI pointing to the WebXDC media.
Once a user starts, a client can show the event(alongside `content.name`, and 
`content.icon`/`content.icon_mime`) as an invitation to enter the WebXDC context. 

If the client is in the context, it MUST set `window.webxdc.selfAddr` and 
`window.webxdc.selfName` to the user's MXID and name in the room(or the global 
name stored in the profile API if unavailable, otherwise fallback to the MXID), 
respectively.

Whenever a client calls the JavaScript `window.webxdc.sendUpdate(update, desc)` 
function, it MUST send a `m.room.message` with a relation to the original event 
with `rel_type=m.webxdc`, the `content.body` field being the description if existent,
and the *required* `m.webxdc.data` containing a JSON-encoded object as a representation 
of `update`, which must be stored as a string if it contains floating-point numbers,
like so:
```js
// Client tries to send an update
window.webxdc.sendUpdate(
    { 
        payload: {graze: 430, score: 5300},
        info: window.webxdc.selfName + ' got over the Spellcard!',
        summary: "Score: 5300"
    }, 
    "New Score on Mt. Ooe"
);
```

```jsonc
{
    "content": {
        "m.relates_to": { "event_id": "$WebXDCStart1", "rel_type": "m.webxdc" },
        "body": "Marisa got over the Spellcard!",
        "m.webxdc.data": {
            "payload": {
                "graze": 430,
                "score": 5300
            },
            "info": "Marisa got over the Spellcard!",
            "summary": "Score: 5300"
        }
    },
    "sender": "@marisa:magic.forest",
    "room_id": "!former:hell.club",
    "event_id": "$WebXDCEvent",
    "type": "m.room.message",
    ...
}
```

Clients receiving such an event(including themselves) must process it with 
the listener set with `window.webxdc.setUpdateListener`, with the update's 
`payload` being the `content->m.webxdc.data` object, it's `info`, `document` 
and `summary` being the `content->m.webxdc.data->info`, `content->m.webxdc.data->document`,
and `content->m.webxdc.data->summary` fields respectively, the 
`serial`/`max_serial` field being the current and last event's `origin_server_ts` 
fields respecticely. They must also check for such events (ideally via the 
relations API).

The `window.webxdc.sendToChat(message)` function shall send a regular event to the 
current room with the `content->body` field being set to the `message.text` value, 
and being sent as the correct type of media if the `media.file` value exists.


## Potential issues

Non WebXDC-capable clients currently do not get a fallback for WebXDC start events, 
which means that such messages will either not display, or will be hidden. Note that 
this isn't a big issue, since clients that simply do not handle WebXDC generally have 
no real reason to have the file in the first place.

Handling of floating-point values within events within the spec(which effectively do 
not allow such things) may be an issue for WebXDC applications which require it.

Servers may be out of sync with the `origin_server_ts`, thus causing conditions where 
two WebXDC updates `A` and `B`, such that `A` comes before `B`, may be processed in the 
order `B` *then* `A`.

As it is experimental, this proposal does not provide a mapping between 
`window.webxdc.joinRealtimeChannel` and a real, Matrix-side construct. The author also 
doesn't see a good way to make it function alongside the existing event system properly, 
and recommends waiting until it is stable within the WebXDC API before making an MSC 
which supports it. As such, clients MUST set the function to the JavaScript `undefined` 
until a MSC which explicitly declares support for it is merged into the specification.


## Alternatives

Widgets([MSC1236](https://github.com/matrix-org/matrix-spec-proposals/issues/3803) and 
[MSC4214](https://github.com/matrix-org/matrix-spec-proposals/pull/4214)), while powerful, 
also suffer from a similar agnosticity problem with other platforms, and effectively requires an actively 
online, external server.  WebXDC also has stricter security concerns(e.g: clients cannot have sensitive 
information leaked, unlike widgets), thus making it safer, though a system that would also widgets to act 
as basic WebXDC containers (allowing clients that already have support for the more complicated widgets, 
while allowing others to focus on the WebXDC subset) would be an interesting compromise.

## Security considerations

WebXDC still suffers from some issues, due to its nature, which is effectively a packaged web application. 
As such, client developers will need to be careful to properly conceal secrets (like a user's access token), 
and must follow [the WebXDC constraints](https://webxdc.org/docs/spec/messenger.html#webview-constraints-for-running-apps).
A malicious user could also use WebXDC as a vector for existing vulnerabilities in, e.g, a browser/JavaScript 
engine, thus being able to break out of sandboxes. Clients must first consult the user on whenever they want to 
start a WebXDC session, and must warn of potential risks, especially with untrusted entities. A user could also 
craft WebXDC events(not created through the application itself, or with a modified version of the application). 
WebXDC app developers must take into consideration the source of a payload(and possibly take measures against, 
but the author finds that discussing said measures falls outside the MSC's own scope).


## Unstable prefix

Until this MSC is merged, clients shall replace the following namespaces accordingly:
- `m.webxdc`->`at.kappach.at.webxdc`
- `m.webxdc.start`->`at.kappach.at.webxdc.start`
- `m.webxdc.data`->`at.kappach.at.webxdc.data`

As this proposal acts at the event layer, there is no need to ask the server for if it has 
support for this proposal.

## Dependencies

This MSC is independent of any other unmerged MSCs.
