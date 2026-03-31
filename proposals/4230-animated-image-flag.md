# MSC4230: 'Animated' flag for images

Since animated images are thumbnailed to a still image, clients need to download the full
image in order to display an animated image (or even to tell whether or not it is animated).
However, there is currently no way of telling that an image is animated without downloading
the original image. This means that clients wishing to display the image as animated must
download the original image for any image format which is capable of being animated. This
means they download the full size image for non-animated images even when the user never
chooses to enlarge the image.

Even clients that animate images on hover must pre-fetch the full size image if they want the
animation to start without a delay while it's downloaded.

## Proposal

We add an optional boolean flag, `is_animated` to the `info` object of `m.image` and `m.sticker` events indicating if
the image is animated or not. This SHOULD match whether the original image contains animation. Note
that this will require clients probe the image file for animation. If a client is unable to determine
whether an image is animated, it should leave the flag unset.

Example:

```json5
{
    "body": "partyparrot.gif",
    "file": {
      [...]
    },
    "info": {
      "w": 640,
      "h": 480,
      "mimetype": "image/gif",
      "size": 35295,
      "is_animated": true,
    }
```

If this flag is `false`, receiving clients SHOULD assume, but not trust, that the image is not animated.
If `true`, they SHOULD assume that it is, again, without trusting.

Behaviour when the field is omitted is left up to the client. They might choose to behave as if it is present
and set to `true`, ensuring backwards compatibility whilst still saving bandwidth for images where the flag
is present and set to `false`. Perhaps they might decide to change this behaviour once more clients start
sending the flag.

## Potential issues

Clients may lie about the flag which would cause unexpected behaviour, for example, an image which
the client did not tell the user was animated might then animate when the user clicks to enlarge it,
allowing for 'jump scares' or similar. Clients may wish to prevent images from being animated if the
flag is set to false.

As above, supporting animated images becomes harder for sending clients because they must work out if
an image is animated in order to set the flag. We must accept that some clients, particularly browser-based
clients, may get this wrong.

## Alternatives

We could specify that clients behave as if the flag is set to true if it's absent. This would mean
clients that didn't want to probe images on upload could omit the flag, at the expense of receiving
clients needing to download the original to probe for animation.

We could require that servers, or clients in the case of encrypted rooms, preserve animation on
thumbnailing. This is quite a burden for clients and would make thumbnails larger.

This could also potentially be extended to `m.sticker` events.

## Security considerations

Potential for clients to lie about the flag and cause unexpected animation is covered in 'Potential
Problems'.

## Unstable prefix

Until stable, the flag will be `org.matrix.msc4230.is_animated`.

## Dependencies

None.
