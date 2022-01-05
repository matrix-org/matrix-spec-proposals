---
type: module
---

### Sticker Messages

This module allows users to send sticker messages in to rooms or direct
messaging sessions.

Sticker messages are specialised image messages that are displayed
without controls (e.g. no "download" link, or light-box view on click,
as would be displayed for for [m.image](#mimage) events).

Sticker messages are intended to provide simple "reaction" events in the
message timeline. The matrix client should provide some mechanism to
display the sticker "body" e.g. as a tooltip on hover, or in a modal
when the sticker image is clicked.

#### Events

Sticker events are received as a single `m.sticker` event in the
`timeline` section of a room, in a `/sync`.

{{% event event="m.sticker" %}}

#### Client behaviour

Clients supporting this message type should display the image content
from the event URL directly in the timeline.

A thumbnail image should be provided in the `info` object. This is
largely intended as a fallback for clients that do not fully support the
`m.sticker` event type. In most cases it is fine to set the thumbnail
URL to the same URL as the main event content.

It is recommended that sticker image content should be 512x512 pixels in
size or smaller. The dimensions of the image file should be twice the
intended display size specified in the `info` object in order to assist
rendering sharp images on higher DPI screens.
