# MSC1958: Widget structure alterations

Widgets are already very powerful in Matrix due to [MSC1236](https://github.com/matrix-org/matrix-doc/issues/1236),
however there are some areas which can be iterated upon.


## Proposal

There are two types of widgets: Account and Room. Account widgets are referred to as "User Widgets"
in MSC1236, however they are renamed here and throughout the integrations API proposals to better
match where they live and who they affect.

#### Account widgets

To recap, account widgets only affect the user which has set them in their own account data. They
cannot be used by other users, and are often used to expand upon the user's experience of a client.
A modern example of an account widget would be the sticker picker: although many people do not realize
it, this is actually a widget powered by the integrations manager. Account widgets currently look
as follows in account data:
```json
{
  "type": "m.widgets",
  "content": {
    "first_widget_arbitrary_id": {
      "content": {
        "type": "m.stickerpicker",
        "url": "https://example.org/stickers.html",
        "data": {
            "api_url": "https://stickers.example.org"
        },
        "name": "Stickerpicker"
      },
      "sender": "@travis:t2l.io",
      "state_key": "first_widget_arbitrary_id",
      "type": "m.widget",
      "id": "first_widget_arbitrary_id"
    },
    "second_widget_arbitrary_id": {
      "content": {
        "type": "m.integration_manager",
        "url": "https://example.org/integrations.html?my_custom_key=$custom_key",
        "data": {
            "api_url": "https://integrations.example.org",
            "custom_key": "custom_value"
        },
        "name": "Integration Manager"
      },
      "sender": "@travis:t2l.io",
      "state_key": "second_widget_arbitrary_id",
      "type": "m.widget",
      "id": "second_widget_arbitrary_id"
    }
  }
}
```

The changes proposed which differ from MSC1236 are:
* `creatorUserId` and `sender` become optional and can be assumed to be the current user.
* `state_key` becomes optional and can be assumed to be the `id`.
* `type` on a widget event becomes optional and should be assumed to be `m.widget`.
* The template variables supported become `$matrix_user_id`, `$matrix_display_name`, `$matrix_avatar_url`.
  `$matrix_room_id` doesn't make sense for account widgets, and should not be provided. Custom keys must
  additionally be supported.
* In cases where the user has multiple `m.stickerpicker` widgets, similar ordering rules apply for showing
  `m.integration_manager` widgets: lexigraphically sort the widgets by `id` and show them in tabs, or pick
  one arbitrarily and use that as the canonical widget. MSC1236 does not define any behaviour. Integration
  manager ordering is defined by [MSC1957](https://github.com/matrix-org/matrix-doc/pull/1957).
* `m.stickerpicker` widgets are required to have a `data` object containing an `api_url`. This is relevant
  for [MSC0000 - Sticker picker API](https://github.com/matrix-org/matrix-doc/pull/0000). For backwards
  compatibility with widgets which don't have this property, clients should try to determine the integration
  manager API URL for the widget or continue ignoring the property's existence (showing an iframe instead).

To further clarify: Widgets should no longer be receiving a `scalar_token` via query params. If they need
to authenticate the user, they are able to use
[MSC0000 - OpenID information exchange for widgets](https://github.com/matrix-org/matrix-doc/pull/0000).

#### Room widgets

As a reminder, room widgets are widgets which are defined in room state and visible/accesible to members
of the room. This includes interacting with the widget. Typically these kinds of widgets are shared notepads,
video conferences, or dashboards however there is no restriction for what could be contained here.

This proposal does not alter MSC1236 with respect to room widgets, however it does add some clarifications
on top:
* Like account widgets, room widgets should no longer be receiving a `scalar_token` and instead should be
  using [MSC0000 - OpenID information exchange for widgets](https://github.com/matrix-org/matrix-doc/pull/0000).
* Although not mentioned in MSC1236, clients are permitted to build widgets into their app if they like. For
  example, a Jitsi widget could translate to built-in call support instead of embedding an iframe. This is
  the one of the rationales for including specific `data` on widgets.

#### Widget titles

Widgets already have a `name` component which best describes what it is ("Etherpad", "Jitsi Conference", etc).
In practice there is a `title` attribute which can be specified in `data` to have a secondary title next to
the widget's name. It is proposed that the `title` be moved to the same level as the `name`, otherwise behaving
the same as in practice: if present, it should show up next to the widget's name. If not set or an empty string,
it should not be shown.

*Note*: In the wild there is a widget title API endpoint that goes along with the `title` property, however
the author is excluding the API from this proposal for doubts of its usefulness and the security concerns with
getting it into the integrations API as proposed. The API is currently called against the integration manager
if the widget is missing a title and a title can be displayed, however with multiple integration managers and
untrusted widgets being proposed it is unclear whether the client should be making this API call anymore. The
security concern comes with the need for authorization on the API endpoint, which means the client would need
to register with a likely unknown integration manager, effectively sending the user's ID over too. Clients could
implement additional prompts however the concern becomes one of user experience where the title would be causing
permission request dialogs for ultimately unimportant information.


## Potential issues

This proposal alters the existing required fields for widgets, potentially introducing complexity into
applications which already rely on the fields. These applications are encouraged to follow the fallback
advice provided in the proposal.

The exclusion of a widget title API endpoint may not be the best option in the current landscape. Although
the author's own integration manager implementation does not make use of the API in a significant way, other
integration managers might. It is unclear to the author how other managers make use of the existing API.


## Security considerations

Token security is achieved by simply never providing it to the widgets. Some integration managers currently
rely on the token being provided to restrict access to particular assets like the widget's script itself. The
author proposes that those implementations make use of
[MSC0000 - OpenID information exchange for widgets](https://github.com/matrix-org/matrix-doc/pull/0000)
through minimal scripts which acquire a token, set appropriate cookies/headers, and load the remaining resources
afterwards.
