# Widget State Event Proposal
This MSC splits [MSC1236](https://github.com/matrix-org/matrix-spec-proposals/issues/3803) into two.
 - One responsible for the widget state event.
 - And one for the postmessage api.

This MSC will only focus on the state event.

There are multiple attempts to specify widgets. (TODO add list and backgroud context)
Over the years there is a clear core part the community converged to that is activly used.
The goal of this MSC is to ONLY focus on the absolute core parts of the widget concept and get this into the spec.

There are also a lot of existing MSCs extending the widget postmessage api. This MSC is phrased so that those extensions
fit well and do not have overlap with the core widget concepts introduced in this MSC.

## Proposal

Rooms can have data that go beyond the chat timeline. Widgets focus on allowing custom appliactions to render and interact with the
room data in a custom way.

This MSC specifically focuses on this aspect of widgets since it is the only well-established usecase we have in the matrix ecosystem.

It does intentionally not talk about Account widgets ([MSC1236](https://github.com/matrix-org/matrix-spec-proposals/issues/3803) for ref)

state event
```json5
{
  "eventId": "$anId",
  "id": "!anId",
  "name": "FlappyRoyal",
  "url": "https://custon.widget.app/widget",
  "avatar_url": "mxc://anAvatar",
}
```

This is the old state event here we justify what is not needed and gets removed
```json5
{
  "avatar_url": "mxc://anAvatar", // Keep
  "creatorUserId": "@aUser:matrix.org", // Remove
  "data": { // Remove
    "padName": "Example",
    "title": "NotepadTitle"
  },
  "eventId": "$anId", // Keep
  "id": "anId", // Keep
  "name": "Notepad", // Keep
  "roomId": "!anId:matrix.org", // Remove
  "type": "m.notepad", // Remove
  "url": "https://widget.repositry.org/notepad?padName=$padName&userName=$matrix_user_id" // Keep
}
```
 - `creatorUserId`: Can be lied about it on each update. The truth can only get aquired via back pagination. It is redundent.
 - `data`: This is used for the url template concept (which we will not continue to propose in this PR) All this can be achieved by just
    using a modified url. e.g. https://widget.repositry.org/notepad?padName=Example
    Additional data can be passed over the widget api. (TODO: Backwards comapt comment)
 - `roomId` Widgets are only for the room they are added to. This data is implicitly known by the client.
 - `type` Is only used for allowing clients to categorize widgets. A dedicated category concept is desired here. Not part of the core msc.
 
## Alternatives
 - Enforce Iframe instead of WebView

 
## Closes
https://github.com/matrix-org/matrix-spec-proposals/pull/2764
https://github.com/matrix-org/matrix-doc/pull/2774
https://github.com/matrix-org/matrix-spec-proposals/issues/3803
