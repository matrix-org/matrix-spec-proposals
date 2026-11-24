# MSC4541: Widget State

For a long time now, Matrix users extended the usefulness of their clients by embedding small web
applications that sit alongside the main timeline. This is useful because these web apps can render their own
custom content, fully independent of the parent web app.

This feature has been in use in clients such as Element Web, and widgets have been a part of the Matrix
ecosystem for a while such as [Neoboard](https://github.com/nordeck/matrix-neoboard) and
[Element Call](https://github.com/vector-im/element-call).

This proposal only defines the state event that defines what widgets may appear in a room. It does NOT define
any interactions between the client and widget, which is covered in
[MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412). As such, you should find
this MSC ample enough to implement a basic widget but it will not cover all use cases.

## Proposal

A new room state event is defined as `m.widget` with the following schema:

```jsonc
{
  "type": "m.widget",
  "state_key": "unique-id",
  "content": {
    "name": "Friendly name",
    "url": "https://widget.example.org/widget",
    "avatar_url": "mxc://anAvatar"
  }
}
```

`state_key` defines a unique identifier for the widget, which can be anything.
`name` defines the text that appears whenever a widget is described by a client, such as a heading.
`url` defines the root document of the widget to be displayed, see [URL Templating](#url-templating) for a
list of available template parameters.
`avatar_url` defines the a MXC URI for the avatar to be displayed alongside the widget.

### URL Templating

The URL may be templated to contain additional parameters, to allow widgets to display some dynamic
content. This includes:

 - `$matrix_room_id`: the ID of the room the widget is being displayed in.
 - `$matrix_user_id`: the ID of the user who is viewing the widget.
 - `$matrix_display_name`: the display name of the user who is viewing the widget.
 - `$matrix_avatar_url`: the **HTTP** avatar URL of the user who is viewing the widget.


All template parameters MUST start with a $, and string replacement apply to the whole **path** segment
of the URL.

The origin of a URL cannot be templated. If a unknown parameter is encountered, it is ignored.

For example:

```sh
https://example.com/widget?room_id=$matrix_room_id&user_id=$matrix_user_id#$matrix_display_name`
# would become
https://example.com/widget?room_id=!room:example.com&user_id=@alice:example.com#Alice
```

### Displaying a widget

A widget SHOULD be displayed either alongside a room, or as a "popout" view. Web clients will likely use a
`<iframe>` to display widgets as the defacto standard, but native clients may use a webview.

The widget SHOULD use the templated URL provided above, and render until the user navigates away from the
room.

## Potential issues

The main problem with this proposal is that it requires clients to present a web view, even if they do not
have the capability to do so. This might be because they would rather not bundle a webview dependency, run in
a terminal interface, and so on. Additionally, assistive technologies may struggle with handling interfaces
presented in a web view.

Developers should be mindful of impact of relying on widgets exclusively, and where possible allow for users
to participate without the use of widgets. As an example,
[Hookshot](https://github.com/matrix-org/hookshot) provides a widget for configuration convenience, but also
provides a bot command interface so that all users can use the integration.

## Alternatives

This proposal is focused around providing a web-based interface for integrations, but there are other methods
that may be more "native" friendly, such as providing a matrix-native command interface. However, in practice
the ecosystem seems to have accepted that webviews are acceptable.

## Security considerations

The core of this proposal is that room administrators can now embed arbitrary widgets in Matrix rooms, and as
such client developers should take every precaution to protect users from malicious widgets. Aspects include:

 - The `url` field MUST be strictly validated to ensure widgets do not try to load or execute malicious
   content. For example, `javascript:alert("XSS attack!")` should not be allowed to execute.
 - Clients should take all reasonable care to fully isolate the widget frame from the parent client. In
   browser contexts this would mean ensuring sufficient use of `sandbox` as well as tight cross-site scripting
   policies so that the widget could not, for example, sniff out the user's credentials.

## Unstable prefix

### im.vector.modular.widgets

The unstable event type for this MSC is `im.vector.modular.widgets`. This event has been used in production
instances for a long time under Element Web and other clients. While it's implementation does differ in some
respects to this proposal, it is currently the defacto standard and can be used to "prove the implementation".

## Dependencies

[MSC4412](https://github.com/matrix-org/matrix-spec-proposals/pull/4412) is a dependant of this MSC and
defines the post-message widget API.
