# MSC4585: Encourage setting the width attribute when sending custom emotes

Today, the ["Sending custom emotes" client spec](https://spec.matrix.org/v1.19/client-server-api/#sending-custom-emotes)
encourages the `width` attribute to be omitted when sending inline images with the `data-mx-emoticon` tag:

> The height attribute MUST be present for backwards compatibility with clients that do not support custom emotes.
> Clients SHOULD set this to “32”.
> Clients implementing image pack support SHOULD override this value when rendering based on the user’s font size
> or other environmental factors. The width attribute SHOULD be omitted to preserve the image’s aspect ratio.

Accordingly, clients cannot determine the expected aspect ratio of such an emote until the download finishes.
If the client initially guesses the image's aspect ratio incorrectly, it needs to resize the inline content,
and thus the message containing it, to preserve the intended image height.
Depending on the rendering implementation, this approach can also cause glitches or
[performance issues](https://github.com/SchildiChat/schildichat-android-next/issues/151).


## Proposal

Instead of *discouraging* clients from setting the inline image `width` for custom emotes, the spec should *encourage*
them to include this field. To preserve the spec's original intent of maintaining the image's aspect ratio, clients that
set this width should also be required to scale it appropriately, such that applying the specified height of `32`
together with the calculated width yields a properly scaled image without any stretching.

Clients can calculate the width as follows:

$$
width = 32 \times \frac{originalWidth}{originalHeight}
$$

Clients should furthermore round the result to an integer and ensure the value is greater than zero to satisfy the
expectations of rendering clients.
Clients rendering the inline image should keep using the same logic for sizing custom emotes as they do today, but can
now calculate an appropriate aspect ratio ahead of time without waiting for the image to finish downloading and decoding.


## Potential issues

None expected. All fields involved retain their current meaning in the spec.


## Alternatives

Both `width` and `height` could be set to the actual dimensions of the images. This can cause a poor experience on
clients that do not yet respect the `data-mx-emoticon` attribute, and is generally worse in terms of backwards
compatibility.

Instead of setting `width`, a new field `aspectRatio`, or two new fields `originalWidth` and `originalHeight`, could be
introduced. These new fields aren't technically required to achieve this MSC's goal and can thus increase complexity
unnecessarily.


## Security considerations

None. All fields involved retain their current meaning in the spec.


## Unstable prefix

None required. All fields involved retain their current meaning in the spec.


## Dependencies

None.
