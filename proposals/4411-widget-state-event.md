# MSC4411: Widget State Event Proposal

There is demand from users and service developers to extend a Matrix **room**
by embedding small web applications that enrich collaboration for the room members.

This feature has been in use in clients such as Element Web, and widgets have been a part of the Matrix
ecosystem for a while, for example [Neoboard](https://github.com/nordeck/matrix-neoboard) and
[Element Call](https://github.com/vector-im/element-call).
They are not yet properly specced, which hinders adoption. On top of that, there are some design decisions in the
current _unspecced_ approach that should be changed.

The goal of this MSC is to start from the most fundamental parts.
It includes as few features as possible to provide a starting point for Matrix widgets in the specification.

[MSC1236](https://github.com/matrix-org/matrix-spec-proposals/pull/1236) gets split into two:
- One responsible for the widget state event. This MSC
  ([MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411))
- One for the postmessage API, so that web apps can read and write Matrix room data.
  [MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412)

With this MSC, clients know which widgets have been added to a room and how to add a new one.
On its own, this MSC makes widgets just web bookmarks embedded into a Matrix room. This is intentional, as it
allows splitting the discussion and accelerates the spec process.
For the full picture of how a widget interacts with a Matrix room,
[MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412) also needs to be considered.

This MSC closes/supersedes the following earlier proposals:
- [MSC2764](https://github.com/matrix-org/matrix-spec-proposals/pull/2764)
- [MSC2774](https://github.com/matrix-org/matrix-spec-proposals/pull/2774)
  (already merged, see _Remove `$matrix_widget_id`_)
- [MSC1236 / issue 3803](https://github.com/matrix-org/matrix-spec-proposals/issues/3803)

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
   - `name` (required): The widget name SHOULD be treated similarly to a room name. It should be meaningful to all room
     members. It is expected to be the same string on all clients independent of localization.
   - `url` (required): The URL the widget is loaded from. Only `https://` urls are allowed
     (clients can allow non `https://` urls as part of their developer tools). Clients MUST validate the url
     before loading it (see `Security considerations`). This also takes the role of the widget type.
     Widgets with the same url are of the same "application type". Template variables as proposed in MSC1236 are
     removed, so the url should be short. (See `Potential issues`/`Backwards compatibility`/
     `Url template parameters`)
   - `avatar_url` (optional): A MXC URI for the icon used to render the widget in the client list. See
     [MSC2765](https://github.com/matrix-org/matrix-spec-proposals/pull/2765), which already defines this field
     and the sizing guidance.
 - `state_key`: opaque, client-generated unique identifier

A state event of type `m.widget` whose content does not match the schema above (for example a missing or
non-string `name` or `url`) is considered a removed widget and MUST NOT be listed or rendered by clients.
Clients SHOULD set the content to `{}` for removing widgets.

When a client observes removal of a widget or a change to its `url`, it MUST stop the old instance,
end its Widget API access, and cancel its pending API approvals before loading a replacement.
A replacement MUST NOT inherit the old instance's active permissions merely because its `state_key` did not change.

#### Power Levels

The default power level system will be used to control who can modify widgets.
(i.e. `events/m.widget` controls who can modify widgets.)
If `m.widget` is not listed in `events`, `state_default` applies as for any other state event.
Since widgets can load arbitrary web content in the room members' clients, room creators SHOULD NOT lower
this below the level required for other room configuration state events.

Permission to add or edit widget state does not imply or grant approval for the widget to use the Matrix API
or access device features.

### Accessing and rendering widgets

A client MUST show a list of available widgets in a UI element associated with a room.
This list MUST provide the widget name. It SHOULD show the widget avatar.
Additionally, the client MUST provide a way to access the secondary information: the `sender` and the `url` of
the widget (see the `Security considerations` section for more details).
It is recommended to show the secondary information in a tooltip, context menu or foldable component so as not
to clutter the UI.
(Common places are side panels or room settings modals.)
The user SHOULD be able to open a widget (webview) as a "popout" view or next to the timeline.
Web clients will likely use an `<iframe>` to display widgets, but native clients may use a separate webview.
If opening webviews is not possible on the client's platform, it is sufficient to list the widgets and
communicate to the user that they need to use another client/platform that supports opening webviews to interact
with the widget.

### Default webview capabilities

Until a dedicated capability negotiation is specified (see `Alternatives`/
`Add iframe capabilities to this (state event) MSC`), clients SHOULD load every widget with the following default
set of capabilities. This matches what is deployed in practice today (Element Web) and is sufficient for the
existing widget ecosystem (e.g. Element Call, Neoboard).

Web clients SHOULD use:
```html
<iframe
  sandbox="allow-forms allow-popups allow-popups-to-escape-sandbox allow-same-origin allow-scripts
           allow-presentation allow-downloads"
  allow="microphone; camera; encrypted-media; autoplay; display-capture; clipboard-write; clipboard-read"
></iframe>
```

Native clients SHOULD grant the equivalent capabilities through their platform's webview permission mechanism:
running scripts, persistent storage, forms, opening popups/external links, downloads, presentation, microphone,
camera, encrypted media, media autoplay, screen capture and clipboard read/write.

Clients MUST NOT allow a widget to navigate the client itself (e.g. `allow-top-navigation`).
Granting a capability in the webview does not bypass the platform's own user prompt (e.g. for camera or
microphone access); clients MAY additionally prompt the user before granting sensitive capabilities.

These webview settings do not grant Matrix Widget API permissions.

### Remove `$matrix_widget_id`
[MSC2774](https://github.com/matrix-org/matrix-spec-proposals/pull/2774) introduced `$matrix_widget_id` and was
merged. This proposal removes the template variable concept
(see `Potential issues`/`Backwards compatibility`/`Url template parameters`)
and therefore also the `$matrix_widget_id` template parameter.

## Intentionally skipped topics
This MSC intentionally skips the following aspects of widgets.
These are good and important features, but they are not required for the initial specification.
 - Widget registries
   - A widget developer might want to have an RSS-like feed of widget updates so that room admins get prompted
     when a new version is available
   - Registries of widgets also solve:
     - Widget discoverability
     - Widget auditing (a registry can be maintained by someone who audits widgets. Users adding an audited
       registry to their client can have more trust in the widgets' good intentions and security.)
 - Bundled widgets
   - Widgets can be bundled into compressed media repository objects. This has the great advantage of not
     depending on a third-party widget host for availability. Additionally, this fits the federated Matrix
     concept better.
     It comes with challenges, as software is usually distributed centrally. So the Matrix ecosystem needs to
     discuss how to distribute and how to update widgets.
 - Non-room-scoped widgets
   - It is an open debate whether widgets should also be able to interact with multiple rooms.
     There are good use cases for this. But there is also a fundamental concept question:
     Is it acceptable that a room admin (not the user of this account) can add a widget that could alter other
     rooms in my account?
     A compromise might be that widgets can be added to spaces and get access to rooms added to a space.
     This proposal intentionally does not attempt to solve or discuss these topics.

## Alternatives

### Client-native command and rendering API
This proposal is focused on providing a web-based interface for integrations, but there are other methods
that may be more "native" friendly, such as providing a Matrix-native command and markup (rendering/layout)
interface. However, in practice the ecosystem seems to prefer the vast feature set and flexibility of webviews.
For the use cases widgets are currently used for, webviews and their advanced rendering and media capabilities
are needed.

### Naming: Widget -> Matrix Room Apps
There is an ongoing debate about what a web app with access to Matrix room data should be called:
 - MatrixApp
 - MatrixRoomApp
 - Widget
 - MatrixRoomExtension

The following arguments have been brought up:
 - "Widget" is too general (it covers everything from UI elements to full apps).
 - The name should communicate the use case (just for a room).
 - There is a conflict with other concepts: clients might have their own extension API to extend a
   specific client (outside the Matrix spec),
   so "extensions" might collide.
 - "Widget" is already a known term in the Matrix ecosystem.

This MSC can be used as a place to discuss the name. However, there is a strong interest in not getting it blocked by
this discussion.
As the only place where the MSC implementation references `widget` is the state event type
(`im.vector.modular.widgets` while unstable),
another MSC for the new name could be opened while this one is in the unstable phase.

### Add iframe capabilities to this (state event) MSC
(This section is also relevant for the security considerations.)

Webviews can be restricted in two independent ways. On the web these are the
[`sandbox`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe#sandbox) attribute and the
[`allow`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Permissions-Policy#directives)
attribute (Permissions Policy). Native platforms have equivalent mechanisms (e.g. Android
`WebChromeClient.onPermissionRequest`, iOS `WKUIDelegate` media capture callbacks).

Sandbox capabilities relevant for widgets:
 - `allow-scripts`, `allow-same-origin`: required by practically every widget (the widget is loaded cross-origin
   to the client, which is what makes this combination acceptable)
 - `allow-forms`
 - `allow-popups`, `allow-popups-to-escape-sandbox`: opening links, OAuth/SSO login windows
 - `allow-downloads`: exporting files
 - `allow-presentation`, `allow-pointer-lock`, `allow-orientation-lock`, `allow-modals`: niche
 - `allow-top-navigation*`: should never be granted, since the widget could navigate the client away

Permissions Policy features relevant for widgets:
 - `camera`, `microphone`, `display-capture`, `speaker-selection`: calls and screen sharing
 - `autoplay`, `fullscreen`, `picture-in-picture`, `encrypted-media`: media
 - `clipboard-read`, `clipboard-write`: editors, whiteboards
 - `screen-wake-lock`, `web-share`, `geolocation`
 - Hardware and other sensitive features (`usb`, `serial`, `hid`, `bluetooth`, `midi`, `payment`,
   `publickey-credentials-get`, sensors, ...) are niche and should require an explicit user prompt.

Some permissions cannot be delegated to an embedded webview at all. Browsers do not allow cross-origin iframes to
request `notifications`; this would need to be proxied by the client through the postmessage API
([MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412)).

The default set of capabilities clients use today is defined in `Proposal`/`Default webview capabilities`.

The base state event could be extended with a field listing the capabilities the widget needs. To stay platform
independent this should use abstract capability names (camera, microphone, screen capture, clipboard, fullscreen,
downloads, popups, ...) rather than raw HTML tokens, which clients map to their platform's mechanism.
A client can then prompt the user based on the requested capabilities.

Alternatively, this can be done via the postmessage API. This has the advantage that the user who sets up the
widget does not need to know which capabilities are required: the widget implementation has full control over
what it requests.

Either way, this is left to a follow-up MSC. Such an MSC could ask clients to prompt users if a widget is set up
without any capability declaration. Those widgets then get the default set of capabilities (see
`Default webview capabilities`) for backwards compatibility, but users get prompted to update their widget.

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
The metadata about which widgets are in a room, and under which name, is unencrypted.
This does not include the private room data that users actually interact with in the widget via the widget API,
but it does leak metadata.

### Misleading widget name
Users with a high enough power level can lie about the widget name.
This allows users to trick others into clicking the wrong widget.
A misleading name can also cause users to approve unintended access.

Therefore, this MSC requires clients to show the sender of the widget event and the url (see the proposal
section).

## Potential issues
### Backwards compatibility
#### Comparison to the currently used widget state event
This is the old state event. Here we justify what is not needed and therefore removed from the `content`:
```json5
{
  "avatar_url": "mxc://anAvatar", // Keep
  "name": "Notepad", // Keep
  "url": "https://widget.repository.org/notepad?padName=$padName&userName=$matrix_user_id", // Keep
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
 - `creatorUserId`: Can be lied about on each update. The truth can only be acquired via back pagination.
   It is redundant.
 - `data`: This is used for the url template concept (which this MSC no longer proposes). All of
   this can be achieved by using a modified url, e.g. `https://widget.repository.org/notepad?padName=Example`.
   Additional data can be passed over the widget API.
 - `id`: We use the `state_key` instead.
 - `eventId`: The state key holds the identifier. The `eventId` is part of the event JSON (outside of
   `content`).
   Clients can access the initial `eventId` by walking `prev_content` via the state history endpoints.
 - `roomId`: Widgets are only for the room they are added to. This data is implicitly known by the client.
 - `type`: Is only used to allow clients to categorize widgets. A dedicated category concept is desired here,
   but should not be part of the core MSC. Additionally, without the need for query parameters,
   widget urls should look more like: `https://widget.repository.org/notepad` instead of
   `https://widget.repository.org/notepad?padName=$padName&userName=$matrix_user_id`.
   So the url becomes the type identity of the widget.

#### Url template parameters
In previous unspecced widget implementations, template parameters are used to pass data to the widget.
e.g. `$matrix_user_id` in a url gets replaced with `@userA:matrix.org` depending on the context.
This allows for very simple room-dependent widget setups:
`https://myDocumentApp.org/$matrix_room_id` allows using a third-party document app with a room-specific
context.
This looks useful at first sight, but in practice it has drawbacks:
 - **Hard to implement**. (Regex operations on urls are always cumbersome, and it is hard to catch all edge cases.)
 - **Incentivises non-ideal solutions**. It is convenient to just reuse the room id or the user id for some url
   parts but often it is not the actual identifier that should be used.
   In the cases where url parameters are most helpful (widgets that don't speak the widget API),
   they are used like a hack.
 - **Duplicated API**. Even with the current implementation (supporting url parameters), we still end up using the
   postmessage API ([MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412)).
   The postmessage API allows reactive updates. Themes and languages will therefore be updated through a
   message. Template parameters will result in two solutions for one problem. The display name, theme or
   language might be a template parameter but also queryable through the widget API so that the widget can get
   updates on display name changes.
 - **Easy workaround that does not need a specification**. In case the community really needs to add a widget
   from a web app that does not support the widget API, a simple wrapper could be built: a webview that uses the
   postmessage API to then populate the template url and load the actual app in an iframe.

#### Widget API message wrapper
The widget API will also change in [MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412).
Existing widgets will no longer be compatible with clients implementing
[MSC4411](https://github.com/matrix-org/matrix-spec-proposals/pull/4411) and
[MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412).
A similar solution to the url template approach can be used.

A wrapper widget can get the old-style widget url as a parameter and then proxy and translate the widget
messages.

### Migration

The current widget implementation with `im.vector.modular.widgets` will eventually be deprecated.
Clients should provide a tool to replace the `im.vector.modular.widgets` state event with a `m.widget` one.
As the widget API won't match, this replacement should also wrap the widget in an API wrapper as proposed in
the section `Widget API message wrapper`.

This allows clients to stop supporting old-style widgets. Custom tooling for migration or
clients that do the migration automatically will make sure old widgets are still usable without
clients maintaining two implementations.

## Unstable prefix

### `im.vector.modular.widgets` and `org.matrix.msc4411.widget`

The unstable event type for this MSC is `org.matrix.msc4411.widget`.
`im.vector.modular.widgets` has been used in production instances for a long time under Element Web and other
clients. While its implementation differs in some respects from this proposal, it is currently the de facto
standard and can be used to "prove the implementation".

## Dependencies

[MSC2765](https://github.com/matrix-org/matrix-spec-proposals/pull/2765): Widget avatars (merged)

([MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412) defines the post-message widget API
and depends on this MSC.)
