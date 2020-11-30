# MSC2881: Message Attachments

*This MSC is especially for media image attachments to message, but I try to make it extendable for multiple attachment types (files, videos, and in future - external URLs, links to other Matrix events, etc). So, in most of examples, I am using "image", but it means, that, instead of image, there may be another attachment type.*

In the current implementation each media (file, image, video) can be sent only via a separate event to the room. But in most cases media is not sent alone, it must be commented via some text by the sender. So the user often wants to attach some images (one or several) directly to his text message when he is composing it.

And now the user can send images only before the message (or after it) as a separate message, but he can't attach images during the composing process to send them when the text is finished, together with the text message in one event.

On the display side, when the user sends multiple images, the problem is that each image is displayed alone, as separate event with full width in timeline, not linked to the message, and not grouped to the gallery.

## Proposal

Matrix client allow users to attach media (images, video, files) to message without instant sending of them to room, and send together with text message.

When user press "Send" button, Matrix client do the upload of all media, that user attached to message, as separate events to room (how it is done now), before sending message with typed text. And after sending of all attachments is finished, client send message with aggregating event, using `m.relates_to` field (from the [MSC2674: Event relationships](https://github.com/matrix-org/matrix-doc/pull/2674)), that points to all previously sent events with media, to group them into one gallery.

For exclude showing those events in modern clients before grouping event added, I propose extend separate media events via adding "marker" field `is_attachment: true`, if clients got this value - they must exclude showing this media in timeline, and shows them only in gallery with grouping event.

Example of media event, that send before grouping event:
```json
{
  "msgtype": "m.image",
  "body": "Image 1.jpg",
  "info": {
    "mimetype": "image/jpg",
    "size": 1153501,
    "w": 963,
    "h": 734,
  },
  "is_attachment": true,
  "url": "mxc://example.com/KUAQOesGECkQTgdtedkftISg"
},
```
And aggregating event, to send after all message attachments:
```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "Here is my photos and videos from yesterday event",
    "m.relates_to": [
      {
            "rel_type": "m.attachment",
            "event_id": "$id_of_previosly_send_media_event_1"
      },
      {
            "rel_type": "m.attachment",
            "event_id": "$id_of_previosly_send_media_event_2"
      }
    ]
  }
}
```
For edits of "message with attachments" we can reuse same "m.relates_to" array via simply adding `"rel_type": "m.replace"` item to it, here is example:
```json
    "m.relates_to": [
      {
            "rel_type": "m.attachment",
            "event_id": "$id_of_previosly_send_media_event_1"
      },
      {
            "rel_type": "m.replace",
            "event_id": "$id_of_original event"
      },
      {
            "rel_type": "m.attachment",
            "event_id": "$id_of_previosly_send_media_event_2"
      }
    ]
```
### Fallback:

I see no serious problems with fallback display of attachments. For Matrix clients, that don't yet support this feature, the attachments will be represented as separate media events, like the user upload each attachment before sending main message.

## Client support

### Compose recommendations:

In the message composer, on "paste file" event, the Matrix client must not instantly upload the file to the server, but the client must show its thumbnail in the special area, with the ability to remove it and to add more media. *Alternatively, it can start uploading instantly to improve the speed of the following message sending process, but there is no way to delete media in Matrix API, so server will store each file, even if it is not attached to the message.*

On "message send" action, Matrix client must upload each attached media to server, get `mxc` of it, post an event to room, and attach its `event_id` to current message contents in `m.relates_to` array.

If the user uploads only one media and leaves the message text empty, media can be sent as regular `m.image` or similar message, like in current implementation.

Editing interface can be represented exactly like the composer interface, where user have the textarea for input message text, and area with all current attachments as tiny thumbnails, in which he can remove one of current attachments (that will remove its line from array of `m.relates_to`), add new attachment (that will upload it as new event, and refer to it in edited message `m.relates_to` array).

### Display recommendations:

On the client site, attachments can be displayed as grid of clickable thumbnails, like the current `m.image` events, but with a smaller size, having fixed height, like a regular image gallery. On click, Matrix client must display media in full size, and, if possible, as a gallery with "next-previous" buttons.

If the message contains only one attachment, it can be displayed as full-width thumbnail in timeline, like current `m.image` and `m.video` messages.

## Server support

This MSC does not need any changes on server side.

## Potential issues

1. On bad connection to server Matrix client can send attachments as events with `"is_attachment": true` but not send final `m.message` event, this will lead to posting invisible media to room. This can be solved on client side via caching unsent group of events, and repeat sending when connection will be recovered.

2. Individual media event, to which `m.message` refers, can be deleted after. As result, `m.message` will contain relation to redacted event. In this situation Matrix clients can exclude this item from display.

## Alternatives

1. Main alternative implementation (my fist proposal in this MSC) is sending only one event with direct links to all attached media, instead of sending separate event for each attachment. This can be done together with [MSC1767: Extensible events in Matrix](https://github.com/matrix-org/matrix-doc/pull/1767) with adding new type `m.attachments`, which will contain the group of attached elements.

Each element of `m.attachments` array has a structure like a message with media item (`m.image`, `m.video`, etc), here is example of the message with this field:

```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "Here is my photos and videos from yesterday event",
    "m.attachments": [
      {
        "msgtype": "m.image",
        "url": "mxc://example.com/KUAQOesGECkQTgdtedkftISg",
        "body": "Image 1.jpg",
        "info": {
          "mimetype": "image/jpg",
          "size": 1153501,
          "w": 963,
          "h": 734,
          "thumbnail_url": "mxc://example.com/0f4f88220b7c9a83d122ca8f9f11faacfc93cd18",
          "thumbnail_info": {
            "mimetype": "image/jpg",
            "size": 575468,
            "w": 787,
            "h": 600
          }
        }
      },
      {
        "msgtype": "m.video",
        "url": "mxc://example.com/KUAQOe1GECk2TgdtedkftISg",
        "body": "Video 2.mp4",
        "info": {
          "mimetype": "video/mp4",
          "size": 6615304,
          "w": 1280,
          "h": 720,
          "thumbnail_url": "mxc://example.com/0f4f88120bfc9183d122ca8f9f11faacfc93cd18",
          "thumbnail_info": {
            "mimetype": "image/jpeg",
            "size": 2459,
            "w": 800,
            "h": 450
          },
        }
      }
    ]
  }
}
```
For fallback display of attachments in old Matrix clients, we can attach them directly to `formatted_body` of message, here is HTML representation:
```html
<p>Here is my photos and videos from yesterday event</p>
<div class="mx-attachments">
  <p>Attachments:</p>
  <ul>
    <li><a href="https://example.com/_matrix/media/r0/download/example.com/KUAQOesGECkQTgdtedkftISg">Image 1.jpg</a></li>
    <li><a href="https://example.com/_matrix/media/r0/download/example.com/0f4f88120bfc9183d122ca8f9f11faacfc93cd18">Video 2.mp4</a></li>
  </ul>
</div>
```
and JSON of `content` field:
```json
"content": {
    "msgtype": "m.text",
    "body": "Here is my photos and videos from yesterday event\nAttachments:\nhttps://example.com/_matrix/media/r0/download/example.com//KUAQOesGECkQTgdtedkftISg\nhttps://example.com/_matrix/media/r0/download/example.com/0f4f88120bfc9183d122ca8f9f11faacfc93cd18",
    "format": "org.matrix.custom.html",
    "formatted_body": "<p>Here is my photos and videos from yesterday event</p>\n<div class=\"mx-attachments\"><p>Attachments:</p>\n<ul>\n<li><a href="https://example.com/_matrix/media/r0/download/example.com//KUAQOesGECkQTgdtedkftISg">Image 1.jpg</a></li>\n<li><a href="https://example.com/_matrix/media/r0/download/example.com/0f4f88120bfc9183d122ca8f9f11faacfc93cd18">Video 2.mp4</a></li>\n</ul></div>"
  }
```
If [MSC2398: proposal to allow mxc:// in the "a" tag within messages](https://github.com/matrix-org/matrix-doc/pull/2398) will be merged before this, we can replace `http` urls to direct `mxc://` urls, for support servers, that don't allow downloads without authentication and have other restrictions.

This way will give less "spam" for room, because when user sends message with 20 attachments, it will send only one event to room, instead of 21 like in main implementation. But it have worse fallback, than main implementation.

2. Second alternative can be embedding images (and other media types) into message body via html tags to "body" field, but this will make extracting and stylizing of the attachments harder.

3. Next alternative is reuse [MSC1767: Extensible events in Matrix](https://github.com/matrix-org/matrix-doc/pull/1767) for attaching and grouping media attachments, but in current state it requires only one unique type of content per message, so we can't attach, for example, two `m.image` items into one message. So, instead of separate current issue, we can extend [MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767) via converting `content` to array, to allow adding several items of same type to one message, [here](https://github.com/matrix-org/matrix-doc/pull/1767/files#r532373829) is my comment with this suggestion.

4. There are also [MSC2530: Body field as media caption](https://github.com/matrix-org/matrix-doc/pull/2530) but it describes only text description for one media, not several media items, and very similar [MSC2529: Proposal to use existing events as captions for images](https://github.com/matrix-org/matrix-doc/pull/2529) that implement same thing, but via separate event. But if we send several medias grouped as gallery, usually one text description is enough.

## Future considerations

In future, we may extend the `m.attachments` field with new types to allow attaching external URL as cards with URL preview, oEmbed entities, and other events (for example, to forward the list of several events to other room with the user comment).

 ## Unstable prefix
Clients should use `org.matrix.msc2881.m.attachments`, `org.matrix.msc2881.m.attachment` and `org-matrix-msc2881-mx-attachments` strings instead of proposed, while this MSC has not been included in a spec release.
