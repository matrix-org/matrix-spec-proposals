# MSC4193: Spoilers on Media
This proposal aims to enhance the protocol with more ways to make other users feel comfortable while using the protocol.
## Background
Matrix includes a way to add a spoiler to text, which hides the text from visibility without explicit user interaction to show the hidden text. However, there is no official way to do this with images.
## Proposal
Some other chat protocols, like Discord or Telegram, offer a way to hide potentially sensitive or triggering images in a way that requires the user to explicitly interact with it to show the image.

In the event that a message has both a spoiler on the body and the image, clients should reveal the spoilers separate from each other.

In events with an image, video, or audio file, there will be an optional `m.spoiler` field containing a `reason` string. If present, the client should show a blurred version of the image and require user interaction to show the full image.
## Example
```
    "body": "example.png",
    "info": {
      "size": 12607,
      "mimetype": "image/png",
      "w": 1235,
      "h": 473,
      "xyz.amorgan.blurhash": "L3TSErUbl9y?u*VEkWnit,tlayWB"
    },
    "msgtype": "m.image",
    "m.mentions": {},
    "m.spoiler": {
      "reason": "example"
    }
    "url": "mxc://example.com/example-media"
```
## Potential issues
Clients that do not support this feature will show all media without a spoiler. This is not practically fixable.
## Alternatives
One alternative is the [Spoilerinator](https://codeberg.org/cf/spoilerinator) tool. However, it depends on HTML, which not all clients implement, and it needs you to copy the media URL, then running the external tool. Additionally, [MSC3725](https://github.com/matrix-org/matrix-spec-proposals/pull/3725) provides a similar way to do this.
## Security considerations
None, hopefully.
## Unstable prefix
Until this is stable, clients should use `page.codeberg.everypizza.msc4193.spoiler` and `page.codeberg.everypizza.msc4193.spoiler.reason`.
