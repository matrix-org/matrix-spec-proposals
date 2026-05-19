# MSC4475: Media galleries by inline MXC links

Users need an easy way to send multiple images together with their text message
to represent them as a gallery in a single message. The same is true for files
and other attachment types.

Currently, most Matrix clients allow sending only a single file (image)
together with a text message, which is not sufficient in many cases. Some
clients provide a composer UI that appears to attach multiple images, but those
images are actually sent as separate messages.

This proposal describes a convenient and flexible way to attach multiple
images and other files into a single message using inline MXC links.

## Proposal

There are three different popular approaches to handle multiple media in a
single message:

1. Multiple media file above with a single caption text below: WhatsApp,
   Telegram.
2. Message text above with multiple media attachments below: Slack.
3. Message text with inline media: Microsoft Teams, Skype.

Pros and cons of these approaches are described in the section "Alternatives".

This proposal describes approach 3, which covers approaches 1 and 2.

The Matrix protocol already allows inline links to Matrix media files using MXC
URIs; here is an example:
```html
Check out my photos from FOSDEM 2025:
<img src="mxc://example.org/JWEIFJweifjWIeifj" />
<img src="mxc://example.org/JWEIFJweifjWIeifk" />
<img src="mxc://example.org/JWEIFJweifjWIeifl" />

And especially look at this awesome group photo:
<img src="mxc://example.org/JWEIFJweifjWIeifm" />

What a nice day at FOSDEM 2025!
```

This is sufficient to implement message galleries, so we don't need any
server-side changes to use this approach.

### Client-side rendering

Matrix clients should consider messages with images that reference Matrix media
via MXC URIs as messages containing an inline gallery.

To display the images in the timeline, clients should use thumbnail-sized
images and present them as a grid: two per row on narrow screens (for example,
mobile), with more columns on wider timelines.

### Client-side composing

In the message composer, clients should allow inserting images inline within the
message text. GUI clients can render these inline as thumbnails; text-based
clients can use a textual representation of the MXC link.

### Server-side link tracking

It is useful to explicitly track the media links referenced in a message,
especially for encrypted messages where the server cannot inspect message
content to discover links.

This could be implemented via an additional array of links in the message
object, but we'll keep that out of scope and describe it in a separate MSC.

## Potential issues

None identified.

## Alternatives

When a user wants to attach an image to the message, there are usually two
intentions:

**Intention 1**: Show the image as the main message content, and, optionally,
add some comment to the image.

**Intention 2**: Show the text as the main message content, and attach an image
to it as context.

These are two different purposes for sending images, and this proposal covers
both of them.

In the result, we have three popular approaches to handle multiple media in a
single message:

1. Text below the images.

Used in messengers: Slack.

If we display the message text below the images, the main content of the message
will be the images, and the "body" will be just a commenting text, in addition
to the images.

2. Text above the images.

Used in messengers: WhatsApp, Telegram.

If we display the message text above the images, it will be the main body of
the message, and the attached images will provide additional context.

In this mode, users sometimes want to add individual captions or comments to
specific images in a gallery, which is not possible today.

3. Text with inline images

Used in messengers such as Microsoft Teams and Skype.

This approach covers the previous approaches and allows placing text anywhere:
before images, after images, or between images.

It also permits grouping images into sub-galleries inside a single message.

Therefore, this approach appears to be the most flexible and user-friendly.

---

There were already several MSCs related to the image galleries and multiple
media attachments:

- https://github.com/matrix-org/matrix-spec-proposals/pull/2881
- https://github.com/matrix-org/matrix-spec-proposals/pull/3382
- https://github.com/matrix-org/matrix-spec-proposals/pull/4274


## Security considerations

None identified.
