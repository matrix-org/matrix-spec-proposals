# MSC2765: Widget avatars

Currently widgets have a name and title associated with them, though no opportunity for avatars
for a favicon-like experience. This proposal introduces such a concept.

## Proposal

In the widget's `data`, a new optional paramater named `avatar_url` is added. This parameter is
an MXC URI to an image clients can use to associate with the widget, likely alongside the `name`
and/or `title`.

Widget avatars SHOULD be legible at small sizes, such as 20x20. The MXC URI in the `avatar_url`
should be the source material to allow clients to use the `/thumbnail` API to get a size for their
use case.

Rendering avatars is optional for clients, much like how clients are not required to use the `name`
or `title` of a widget.

## Alternatives

We could define a whole structured system for different thumbnail sizes, though we have a thumbnail
API which can be used to request whatever size is needed by the client.

## Security considerations

Widget avatars could be non-images. Clients should use the thumbnail API to encourage error responses
from the server when a widget avatar is a non-image.

## Unstable prefix

Not applicable - this is backwards compatible with specification and an allowed property of `data`
without this MSC.
