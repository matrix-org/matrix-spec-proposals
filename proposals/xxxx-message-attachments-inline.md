# MSCXXXX: Inline message attachments 

This is an alternative to
[MSC2881: Message Attachments](https://github.com/matrix-org/matrix-doc/pull/2881) 
that stores all attachments directly inside current event, to not post a separate 
event for each attachment and refer to it. I think this way have less complexity 
and better for performance.

## Proposal

As lite alternative to
[MSC2881: Message Attachments](https://github.com/matrix-org/matrix-doc/pull/2881) 
we can send only one event with direct links
to all attached media, instead of sending separate event for each attachment,
because it will give less "spam" for room. Eg when user is sending message with
20 attachments - it will send only one event to room, instead of 21 like in
option one implementation. But the main problem with this option is *fallback*.

This can be done together with [MSC1767: Extensible events in
Matrix](https://github.com/matrix-org/matrix-doc/pull/1767) with adding new type
`m.attachments`, which will contain the group of attached elements.

Each element of `m.attachments` array has a structure like a message with media
item (`m.image`, `m.video`, etc), here is example of the message with this
field:

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
        }
      }
    ]
  }
}
```

#### Fallback

For fallback display of attachments in old Matrix clients, we can attach them
directly to `formatted_body` of message, here is HTML representation:
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
    "formatted_body": "<p>Here is my photos and videos from yesterday event</p>\n<div class=\"mx-attachments\"><p>Attachments:</p>\n<ul>\n<li><a href=\"https://example.com/_matrix/media/r0/download/example.com//KUAQOesGECkQTgdtedkftISg\">Image 1.jpg</a></li>\n<li><a href=\"https://example.com/_matrix/media/r0/download/example.com/0f4f88120bfc9183d122ca8f9f11faacfc93cd18\">Video 2.mp4</a></li>\n</ul></div>"
  }
```
And modern clients, that have support of the attachments feature, will cut the
`div.mx-attachment` tag and replace it to rich gallery block with thumbnails of
attachments.

If [MSC2398: proposal to allow mxc:// in the "a" tag within
messages](https://github.com/matrix-org/matrix-doc/pull/2398) will be merged
before this, we can replace `http` urls to direct `mxc://` urls, for support
servers, that don't allow downloads without authentication and have other
restrictions.

**If we will come up with better fallback display, maybe bring this option as
main suggestion?**


## Client support

### Compose recommendations:

In the message composer, on "upload file" or "paste file from clipboard" event,
the Matrix client must not instantly upload the file to the server, but the
client must show its thumbnail in the special area, with the ability to remove
it and to add more media. *Alternatively, it can start uploading instantly to
improve the speed of the following message sending process, but there is no way
to delete media in Matrix API yet ([MSC2278: Deleting attachments for expired
and redacted
messages](https://github.com/matrix-org/matrix-doc/blob/matthew/msc2278/proposals/2278-deleting-content.md),
so server will store each file, even if it is not attached to the message.*

On "message send" action, Matrix client must upload each attached media to
server, get `mxc` of it, post an event to room, and attach its `event_id` to
current message contents in `m.relates_to` array (option one); or collect all
`mxc` urls in `m.attachments` array on option two.

If the user uploads only one media and leaves the message text empty, media can
be sent as regular `m.image` or similar message, like in current implementation.

Editing interface can be represented exactly like the composer interface, where
user have the textarea for input message text, and area with all current
attachments as tiny thumbnails, in which he can rearrange attachments, remove
one of current attachments (that will remove its line from array of
`m.relates_to` and do the `redact` action on corresponding event with media in
option one, or remove item from `m.attachments` in option two; and delete media
file using
[MSC2278](https://github.com/matrix-org/matrix-doc/blob/matthew/msc2278/proposals/2278-deleting-content.md)),
add new attachment (that will upload it as new event with refer to it in edited
message `m.relates_to` array in option one / added to `m.attachments` in option
two).


### Display recommendations:

On the client side, attachments can be displayed as grid of clickable
thumbnails, like the current `m.image` events, but with a smaller size, having
fixed height, like a regular image gallery. On click, Matrix client must display
media in full size, and, if possible, as a gallery with "next-previous" buttons.
Also clients can implement collapse/expand action on gallery grid.

If the message contains only one attachment, it can be displayed as full-width
thumbnail in timeline, like current `m.image` and `m.video` messages.

Example of composer interface implementation with multiple attachments we can
lookup in [Slack](https://slack.com/), [VK Messenger](https://vk.com/messenger),
[Skype](https://skype.com).

For prevent showing of attachments as regular media in timeline before main
aggregating event will be added to room, clients should visually hide media
events, that have `"is_attachment": true` value, to display them later in
gallery, but can already start downloading of attachments thumbnails, for
speed-up display of them in gallery.

Together with [MSC2675: Serverside aggregations of message
relationships](https://github.com/matrix-org/matrix-doc/pull/2675) all
attachments will can be even aggregated on server side.

## Server support

This MSC does not need any changes on server side.


## Potential issues

1. On bad connection to server Matrix client can send attachments as events with
   `"is_attachment": true` but not send final `m.message` event, this will lead
   to posting invisible media to room. This can be solved on client side via
   caching unsent group of events, and repeat sending when connection will be
   recovered.

2. In option one - individual media event, to which `m.message` refers, can be
   deleted (redacted) after. As result, `m.message` will contain relation to
   redacted event. In this situation Matrix clients can exclude this item from
   display.

3. In option one - there are no restrictions, that message with attachments can
   refer only to other events, that have `"is_attachment": true`, because this
   is not too easy to control, and in theory user can post message, that can
   refer to other media, owned by other users, and `redact` event will try to
   delete them. But the API should restrict regular user to redact events of
   other users (if he isn't moderator), so those `redact` actions should already
   be successfully ignored by server.

4. If client attach too much media to one message, he can got rate limiting
   problem on server side. This can be solved via splitting and delaying send of
   attachments, to match server rate limits.

## Future considerations

In future, we may extend the `m.attachments` field with new types to allow
attaching external URL as cards with URL preview, oEmbed entities, and other
events (for example, to forward the list of several events to other room with
the user comment).

## Unstable prefix

Clients should use `org.matrix.mscXXXX.m.attachments` and `org-matrix-mscXXXX-mx-attachments` strings
instead of proposed, while this MSC has not been included in a spec release.
