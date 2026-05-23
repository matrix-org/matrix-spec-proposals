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

Rooms can have data that go beyond the chat timeline. Widgets focus on allowing custom applications to render and interact with the
room data in a custom way.

This MSC specifically focuses on this aspect of widgets since it is the only well-established use-case we have in the matrix ecosystem.

The scope is to define a widget for a single room only. We want to define a simple base and leave the support for wider scope
(example: multiple rooms, spaces) for separate MSCs.

### State Event
```json5
{
  // irrelevant fields omitted for brevity
  "type": "m.widget",
  "state_key": "some-uuid",
  "content": {
    "name": "some-widget-name", // required
    "url": "https://custom.widget.app/widget", // required
    "avatar_url": "mxc://anAvatar", // optional
  }
}
```
 - `name`: The widget name SHOULD be treated similar to a room name. It should be meaningful to all room members. It is expected to be the same string on all clients independent of localization.
 - `url`: The actual widget url where the widget is loaded from. This also takes the role as the widget type parameter. Most per room and per user fields are available through the widget api [MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412) so the urls should be very short.
 - `avatar_url` The icon used to render the widget in the client list.

Url template parameters are excluded. Additional per user and per room data are exposed via widget api. 
This has an advantage that it also solves the reactive data, example: theme, language. If the theme is passed over widget api
it can be updated reactively. For additional room level metadata can be hardcoded from URL. This emplies that a widget
that relies on per user data has to use widget api. This MSC values simplicty for the basic building blocks more then
focusing on the use case of injecting user specific data into url parameters.

## Comparions to current unspecced implementation

This is the old state event. Here we justify what is not needed and gets removed
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

## Closes
https://github.com/matrix-org/matrix-spec-proposals/pull/2764
https://github.com/matrix-org/matrix-doc/pull/2774
https://github.com/matrix-org/matrix-spec-proposals/issues/3803
