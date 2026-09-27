# MSC4411: Widget State Event Proposal

There is a demand from users and service devlopers to extend a matrix **room**
by embedding small web applications that enrich the collaboration for the room members.

This feature has been in use in clients such as Element Web, and widgets have been a part of the Matrix
ecosystem for a while such as [Neoboard](https://github.com/nordeck/matrix-neoboard) and
[Element Call](https://github.com/vector-im/element-call).
They are not yet properly specced which hinders actual adoption. On top there are some design decisions in the
current _unpsecced_ approach, that should be changed.

The goal of this MSC is to start from the most fundamental parts.
With as little features as possible to have a starting point of matrix widgets in the specification.

MSC [MSC1236](https://github.com/matrix-org/matrix-spec-proposals/issues/3803) gets split into two.
- One responsible for the widget state event. This MSC ([MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411))
- And one for the postmessage api so the webapps can communicate (read/write) into the matrix room data. [MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412)

After this MSC clients know whcih widget are added to a room and how to add a new one.
With this MSC on its own widgets are just web bookmarks embedded into a matrix room. This is intentional as it allows splitting conversations and accelerate the spec process.
For the full picture how a widget interacts with a matrix room, [MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412) needs to also get considered.

## Proposal

A new room state event is defined as `m.widget` with the following schema:

### State Event
```json5
{
  "type": "m.widget",
  "state_key": "widget_id",
  "content": {
    "name": "some-widget-name",
    "url": "https://custom.widget.app/widget",
    "avatar_url": "mxc://anAvatar",
  }
}
```

 - `content`:
   - `name`: The widget name SHOULD be treated similar to a room name. It should be meaningful to all room members. It is expected to be the same string on all clients independent of localization.
   - `url`: The actual widget url where the widget is loaded from. Only `https://` urls are allowed (clients can allow non `https://` urls as part of their developer tools). This also takes the role as the widget-type. Widgets with the same url are of the same "application type". Template variables as
    proposed in MSC1236 get removed. So the url should be short. (See dedicated alternatives section on template parameters)
   - `avatar_url` (optional): A MXC URI for the icon used to render the widget in the client list. See [MSC2765](https://github.com/matrix-org/matrix-spec-proposals/pull/2765), which already defines this field and the sizing guidance.
 - `state_key`: opaque, client-generated uuid v4

### Accessing and rendering widgets

A client MUST show a list of available widgets in a UI element associated with a room.
This list MUST provide the widget name. It SHOULD show the widget avatar.
Additionally the client MUST provide a way the acces the secondary information `sender` and the `url` of the widget. (See `Security considerations` section for more details)
It is recommended to add the seconday information in a tooltip or context window or foldable component to not clutter the ui.
(commen places could be side panels or room settings modals)
The user SHOULD be able to open a widget (webview) as a "popout" view or next to the timeline.
Web clients will likely use an `<iframe>` to display widgets, but native clients may use a seperate webview.
If not possible to support opening webviews on the clients platform it is enough to list the widgets and communicate to the user that they need to use another
client/platform that supports opening webviews to interact with the widget.

### Remove `$matrix_widget_id`
[MSC2774](https://github.com/matrix-org/matrix-spec-proposals/pull/2774) introduced `$matrix_widget_id` and got merged. This proposal removes the template variable concept (See: `Potential Issues`/`Backwards compatibility`/`Url template parameters`)
and therefore also the `$matrix_widget_id` template paramter.

## Alternatives

### Client native command, rendering api
This proposal is focused around providing a web-based interface for integrations, but there are other methods
that may be more "native" friendly, such as providing a matrix-native command and markup (rendering /layout) interface. However, in practice
the ecosystem seems to preferr the vast feature set and flexibility of webviews.
For the usecases widgets currently are used webviews and their advanced rendering and media capabilities
are needed.
### Naming: Widget -> Matrix Room Apps
There is an ongoing dabate on how a webapp with access to matrix room data should be called:
 - MatrixApp
 - MatrixRoomApp
 - Widget
 - MatrixRoomExtension

 The following arguments have been brough up:
  - Widgets are to general. (from UI elements to full apps)
  - The name should communicate their usecase (just for a room)
  - There is a conflict of intereste to other concepts: Clients might have their own extensions api to extend a specific client (outside the matrix spec)
    So extensions might collide.
  - Widgets is already a known term in the matrix ecosystem.

This MSC can be used as a place to discuss the name. There is a large interst to not get it blocked by this discussion however.
As the only place the MSC implementation is referenceing `widget` is the state event type (`im.vector.modular.widgets` while unstable)
Another MSC for the new name could be opened while its in unstable phase.
### Intentionally skipped topics
This MSC intentionally skips the following aspects of widgets.
Those are topics that are good and important features, but not required for the initial specification.
 - Widget registries
  - A widget developer might want to have an RSS like feed of widget updates so that room admins get prompeted if a new version is available
  - Registries of widgets also solve:
    - Widget discoverability
    - Widget audition (a registry can be maintained by someone who audits widgets. Users adding an audited registry to thier client can have more trust in their good intentions and security)
 - Bundled widgets
  - Widgets can be bundled into compressed media repository objects. This has the great advantage of being independent of a third party widget host
    to be available. Additionally this fits the federated matrix concept better.
    It comes with chellanges as sowtware is usually distributed centrally. So the matrix ecosystem needs to discuss, How to distribute? and How to update?...
 - Non room scoped widgets
  - It is an open debate if widgets should also be able to be able to interact with multiple rooms.
    There are good usecases for this. But there is also a fundamental concept question:
    Is it acceptable, that a room admin (not the user of this account) can add a widget that could alter other rooms in my account?
    A compromise might be that widgets can be added to spaces and get access to rooms added to a space.
    This proposal intentionally does not want to solve/discuss those topics.
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

This can be pushed to a follow up MSC. Which asks clients to prompt users if a widget is setup without any `webview_allowlist` and `webview_sandbox`.
Those widgets then get all permissions for backwards compatibility but users will get prompted to update their widget.

## Security considerations

The core of this proposal is that room administrators can now embed arbitrary widgets in Matrix rooms, and as
such client developers should take every precaution to protect users from malicious widgets. Aspects include:

 - The `url` field MUST be strictly validated to ensure widgets do not try to load or execute malicious
   content. For example, `javascript:alert("XSS attack!")` should not be allowed to execute.
 - Clients should take all reasonable care to fully isolate the widget frame from the parent client. In
   browser contexts this would mean ensuring sufficient use of `sandbox` as well as tight cross-site scripting
   policies so that the widget could not, for example, sniff out the user's credentials.

 See also: _Add iframe capabilities to this (state event) MSC_

### Unencrypted state events
The metadata which widgets are in a room and with which name gets is unencrypted.
This should not hold the private room data that users actually interact with in the widget via the widget api.
But it does leak metadata.

### Misleading widget name
Users with a high enough power level can lie about the widget name.
This allows users to mock others into clicking the wrong widget.
On first sight this might be an issue. As room members already have access to the encrypted messages,
this does not allow any attacks beyond what they are already able to (for ecxample: share encrypted history with the public)

It can be used to mock other users however. If there are users with unconstructive motives in a room that change the widget name
to confuse others, there is a more fundamental problem with the rooms community this MSC does not solve.

The MSC still demands to show the sender of the widget event and the url (see proposal section).
## Potential issues
### Backwards compatibility
#### Comparison to the current in use widget state event
This is the old state event. Here we justify what is not needed and gets removed from the `content`
```json5
{
  "avatar_url": "mxc://anAvatar", // Keep
  "name": "Notepad", // Keep
  "url": "https://widget.repositry.org/notepad?padName=$padName&userName=$matrix_user_id" // Keep
  "creatorUserId": "@aUser:matrix.org", // Remove
  "data": { // Remove
    "padName": "Example",
    "title": "NotepadTitle"
  },
  "id": "anId", // Remove
  "eventId": "$anId", // Remove
  "roomId": "!anId:matrix.org", // Remove
  "type": "m.notepad", // Remove
}
```
 - `creatorUserId`: Can be lied about it on each update. The truth can only get aquired via back pagination. It is redundent.
 - `data`: This is used for the url template concept (which we will not continue to propose in this PR) All this can be achieved by just
    using a modified url. e.g. https://widget.repositry.org/notepad?padName=Example
    Additional data can be passed over the widget api.
 - `id` we use the `state_key` instead.
 - `eventId` The state key should hold the identifier. The `eventId` is part of the event json (outside content).
   The initial eventId can be aquired by stepping back via: `replaces_state`
 - `roomId` Widgets are only for the room they are added to. This data is implicitly known by the client.
 - `type` Is only used for allowing clients to categorize widgets. A dedicated category concept is desired here.
   But should not be part of the core MSC.

#### Url template parameters
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


#### Widget api messages
Also the widget api will change in [MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412).
Those widgets are not compatible with clients implementing [MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411)] and
[MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412)] anymore.
A similar solution to the url template appraoch can be used.

A wrapper widget that gets the old style widget url as a parameter and then proxy and translate the widget messages.

## Unstable prefix

### im.vector.modular.widgets

The unstable event type for this MSC is `im.vector.modular.widgets`. This event has been used in production
instances for a long time under Element Web and other clients. While it's implementation does differ in some
respects to this proposal, it is currently the defacto standard and can be used to "prove the implementation".

## Dependencies

[MSC2765](https://github.com/matrix-org/matrix-spec-proposals/pull/2765): Widget avatars (merged)

([MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412) defines the post-message widget API and is a dependant of this MSC.)


## Closes
https://github.com/matrix-org/matrix-spec-proposals/pull/2764
https://github.com/matrix-org/matrix-doc/pull/2774
https://github.com/matrix-org/matrix-spec-proposals/issues/3803
