# MSC2881: Message Attachments

*This MSC is especially for media image attachments to message, but I try to make it extendable for multiple attachment types (files, videos, and in future - external URLs, links to other Matrix events, etc). So, in most of examples, I am using "image", but it means, that, instead of image, there may be another attachment type.*

In the current implementation each media (file, image, video) can be sent only via a separate event to the room. But in most cases even one media is not sent alone, it must be commented via some text by the sender. So the user often wants to attach some images (one or several) directly to their text message when composing it, not after or before it.

And now the user can send images only before the message (or after it) as a separate message, but they can't attach images during the composing process to send them when the text is finished, together with the text message in one event.

On the display side, when the user sends multiple images, the problem is that each image is displayed alone, as separate event with full width in timeline, not linked to the message, and not grouped to the gallery.

Messages with multiple attachments now already implemented in many messengers, for example - in Skype, Slack, VK Messenger. And Matrix, because lack of support, now have problems with bridging those messages to Matrix rooms.

This is a "best fallback" version of multiple attachments implementation, more optimal implementation is moved to separate [MSC3382: Inline message Attachments](https://github.com/matrix-org/matrix-doc/pull/3382).

## Proposal

For solve described problem, I propose to add `m.attachment` relation type to current events, that will point to other media events in room, which must be shown as attachment to current event, and `is_attachment: true` marker field to all media, that was send to be an attachment for some message.

With having this feature, Matrix client should allow users to attach one or multiple media (images, video, files) to message on client side, without instant sending of them to room, and send them together with text message.

When user press "Send" button, Matrix client do the upload of all media, that user attached to message, as separate events to room (how it is done now), before sending message with typed text. And after sending of all attachments is finished, client send message with aggregating event, using `m.relates_to` field (from the [MSC2674: Event relationships](https://github.com/matrix-org/matrix-doc/pull/2674)), that points to all previously sent events with media, to group them into one gallery. Currently the `m.relates_to` is object that is bad for extensability, but here is [MSC3051: A scalable relation format](https://github.com/matrix-org/matrix-doc/pull/3051) that fixes this.

For exclude showing those events in modern clients before grouping event added, I propose extend separate media events via adding "marker" field `is_attachment: true`, if clients got this value - they must exclude showing this media in timeline, and shows them only in gallery with grouping event.

Example of media event, that send before aggregating event:
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

For delete (redact action) message with attachments, we must also apply `redact` action to each message attachment event too.

 ## Alternatives

1. An alternative can be embedding images (and other media types) directrly into message body via html tags to "body" field (`<a href>` or `<img src>`), but this will make composing, extracting and stylizing of the attachments harder.

2. Next alternative is reuse [MSC1767: Extensible events in Matrix](https://github.com/matrix-org/matrix-doc/pull/1767) for attaching and grouping media attachments, but in current state it requires only one unique type of content per message, so we can't attach, for example, two `m.image` items into one message. So, instead of separate current issue, we can extend [MSC1767](https://github.com/matrix-org/matrix-doc/pull/1767) via converting `content` to array, to allow adding several items of same type to one message, [here](https://github.com/matrix-org/matrix-doc/pull/1767/files#r532373829) is my comment with this suggestion.

3. There are also [MSC2530: Body field as media caption](https://github.com/matrix-org/matrix-doc/pull/2530) but it describes only text description for one media, not several media items, and very similar [MSC2529: Proposal to use existing events as captions for images](https://github.com/matrix-org/matrix-doc/pull/2529) that implement same thing, but via separate event. But if we send several medias grouped as gallery, usually one text description is enough for most cases, also this MSC can be the replacement of #2530 / #2529, when user send text + only one media item. And the main problem with those MSC, that in most cases, it is the image that is the comment to the text message, and not vice versa, as implied in the phrase "image caption" from those MSC, [here is my comment about this in that MSC](https://github.com/matrix-org/matrix-doc/pull/2529#issuecomment-736638196).

We still can implement both things together (my *MSC2881* as one main text with as attachments + separate short *caption texts* for each attachment via [MSC2530](https://github.com/matrix-org/matrix-doc/pull/2530)), but this will give very complex UI for manage attachments in Matrix clients, so, I think, Matrix don't need so complex feature and only one text for all attachments will be enouth, for manage full-featured "Photos Albums" with descriptions and comments we already have more suitable tools.

4. Other alternative can be posting `m.message` event at first, and link all attachments to it later via `m.relates_to` field, something like this:
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
  "m.relates_to": [
    {
      "rel_type": "m.attachment_to",
      "event_id": "$id_of_main_message"
    }
  ],
  "url": "mxc://example.com/KUAQOesGECkQTgdtedkftISg"
},
```      
But this way will give harder way to render of main message event, because Matrix clients must do the search of all attached events manually in timeline, and server will be unable to aggregate them to main message.

#### Fallback:

I see no serious problems with fallback display of attachments. For Matrix clients, that don't yet support this feature, the attachments will be represented as separate media events, like the user upload each attachment separately, before sending main message.

## Unstable prefix
Clients should use `org.matrix.msc2881.m.attachment` string instead of proposed, while this MSC has not been included in a spec release.
