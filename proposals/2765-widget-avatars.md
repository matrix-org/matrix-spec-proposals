# MSC2765: Widget avatars

Currently widgets have a name and title associated with them, though no opportunity for avatars
for a favicon-like experience. This proposal introduces such a concept.

## Proposal

A new optional parameter named `avatar_url` is added to the widget definition. This parameter is
an MXC URI to an image clients can use to associate with the widget, likely alongside the `name`
and/or `title`.

Widget avatars SHOULD be legible at small sizes, such as 20x20. The MXC URI in the `avatar_url`
should be the source material to allow clients to use the `/thumbnail` API to get a size for their
use case.

Rendering avatars is optional for clients, much like how clients are not required to use the `name`
or `title` of a widget.

An example widget would be:

```json
{
    "creatorUserId": "@alice:example.org",
    "data": {
        "custom_key": "This is a custom key",
        "title": "This is a witty description for the widget"
    },
    "id": "20200827_WidgetExample",
    "name": "My Cool Widget",
    "type": "m.custom",
    "url": "https://example.org/my/widget.html?roomId=$matrix_room_id",
    "waitForIframeLoad": true,
    "avatar_url": "mxc://example.org/abc123"
}
```

## Alternatives

We could define a whole structured system for different thumbnail sizes, though we have a thumbnail
API which can be used to request whatever size is needed by the client.

## Security considerations

Widget avatars could be non-images. Clients should use the thumbnail API to encourage error responses
from the server when a widget avatar is a non-image.

## Unstable prefix

While this MSC is not in a released version of the specification, clients should use an alternative
event type for widgets or use `org.matrix.msc2765.avatar_url` when using `m.widget` or `m.widgets`
as an event type.
