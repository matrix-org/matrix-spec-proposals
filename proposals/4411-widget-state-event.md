# MSC4411: Widget State Event Proposal

There is a demand from users and service devlopers to extend a matrix **room**
by embedding small web applications that enrich the collaboration for the room members.

For a long time this has been done in some clients without ever being specced.
This feature has been in use in clients such as Element Web, and widgets have been a part of the Matrix
ecosystem for a while such as [Neoboard](https://github.com/nordeck/matrix-neoboard) and
[Element Call](https://github.com/vector-im/element-call).
But not properly being specced hinders actual adoption. On top there are some design decisions in the
current _unpsecced_ approach, that should be changed.

The goal of this MSC is to start from the most fundamental parts.
With as little features as possible to have a starting point of matrix widgets in the specification.

MSC [MSC1236](https://github.com/matrix-org/matrix-spec-proposals/issues/3803) gets split into two.
- One responsible for the widget state event. This MSC ([MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411))
- And one for the postmessage api so the webapps can communicate (read/write) into the matrix room data. [MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412)

After this MSC clients know if a widget is added to a room and how to add them.
With just this MSC widgets are just embedded-bookmarks. This is intentional as it allows splitting conversations and accelerate the spec process. For the full picture [MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412) needs to also get considered.

## Proposal

A new room state event is defined as `m.widget` with the following schema:

### State Event
```json5
{
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
 - `url`: The actual widget url where the widget is loaded from. This also takes the role as the widget type Widgets with the same url are of the same application type. Template variables are
 get dropped. So the url should be short. (See dedicated alternatives section on template parameters)
 - `avatar_url` The icon used to render the widget in the client list.
 - `version` the currently in used version

### Accessing and rendering widgets

A client MUST show a list of available widgets in a UI element associated with a room.
(commen places could be side panels or room settings modals)
The user SHOULD be able to open a widget (webview) as a "popout" view or next to the timeline.
Web clients will likely use an
`<iframe>` to display widgets as the defacto standard, but native clients may use a webview.
If not possible to support opening webviews on the clients platform it is enough to list the widgets and referr to using another client that supports opening webviews.

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

## Alternatives
### Url template parameters
In previous unspecced widget implementations templete parameters are used to pass data to the widget.
e.g. `$matrix_user_id` in a url gets replaces with `userA@matrix.org` depending on the context.
This allows for very simple room dependent widget setups:
`https://myDocumentApp.org/$matrix_room_id` allows to use a third party document app with a room specific context.
This looks useful on first sight but in practice it has drawbacks:
 - **Hard to implement**. (regex operations on urls is always combersome and hard to catch all edgecases)
 - **Incentifies non ideal solutions**. It is convinient to just reuse the room id or the user id for some url parts but often it is not the actual identifier that should be used.
 In the cases the url parameters are the most helpful (For widgets that dont speak the widget api)
 They are used like a hack.
 - **Duplicated API** Even with the current implementation (supporting url parameters) we still end up using the postmessage api ([MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412))
 The postmessage api allows reactive updates. Themes and languages therefore will be updated through a message. Template paramerts will result in two solutions for one problem. The display name, theme or language might be a template paramter but also queryable through the widget api so the widget can get updates to display name changes.
 - **Easy workaraound that does not need a specification** In case the community really needs add a widget from a webapp that does not support the widget api a simple wrapper could be build: A webview that uses the postmessage api to then popultate the template url and load the actual app in an iframe.

### Client native command, rendering api
This proposal is focused around providing a web-based interface for integrations, but there are other methods
that may be more "native" friendly, such as providing a matrix-native command and markup (rendering /layout) interface. However, in practice
the ecosystem seems to preferr the vast feature set and flexibility of webviews.
For the usecases widgets currently are used webviews and their advanced rendering and media capabilities
are needed.
### Naming: Widget -> Matrix Room Apps
There is an ongoing dabate on how a webapp with access to matrix room data should be called

### Add iframe capabilities to this (state event) MSC
(this section is also relevant for the Security considerations)

Iframes and webviews can be restricted via `sandbox` and `allow lists` on most platfroms.
 - `allow-downloads`
 - `allow-popups`
 - ...
(see: [sandbox](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe#sandbox) for a complete list)

 - `background-sync`
 - `microphone`, `camera`
 - `notifications`
 - ...
(see: [permissions api](https://developer.mozilla.org/en-US/docs/Web/API/Permissions_API#permission-aware_apis) for a complete list)

The base state event could be extended with a `webview_allowlist` and `webview_sandbox` object.
These contain the configurations that are needed for this app.

A client can then prompt the user based on the requested permissions and sandbox values.

This can also be added as a follow up MSC.
It can also be done via the postmessage api. (Which has the advantage that the user who sets up the widget does not need to know what permissions are required. The widget implementation has full control over what it requests)

## Security considerations

The core of this proposal is that room administrators can now embed arbitrary widgets in Matrix rooms, and as
such client developers should take every precaution to protect users from malicious widgets. Aspects include:

 - The `url` field MUST be strictly validated to ensure widgets do not try to load or execute malicious
   content. For example, `javascript:alert("XSS attack!")` should not be allowed to execute.
 - Clients should take all reasonable care to fully isolate the widget frame from the parent client. In
   browser contexts this would mean ensuring sufficient use of `sandbox` as well as tight cross-site scripting
   policies so that the widget could not, for example, sniff out the user's credentials.

 See also: _Add iframe capabilities to this (state event) MSC_
## Unstable prefix

### im.vector.modular.widgets

The unstable event type for this MSC is `im.vector.modular.widgets`. This event has been used in production
instances for a long time under Element Web and other clients. While it's implementation does differ in some
respects to this proposal, it is currently the defacto standard and can be used to "prove the implementation".

## Dependencies

[MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412) is a dependant of this MSC and
defines the post-message widget API.

## Closes
https://github.com/matrix-org/matrix-spec-proposals/pull/2764
https://github.com/matrix-org/matrix-doc/pull/2774
https://github.com/matrix-org/matrix-spec-proposals/issues/3803
