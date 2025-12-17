# MSC4347: Emoji verification images

I propose supplying exact images to be used within emoji verification, to avoid
confusion for users where clients use different emoji fonts.

## Motivation

During device or user verification, if the [emoji method of SAS
verification](https://spec.matrix.org/v1.15/client-server-api/#sas-method-emoji)
is used, users are asked to compare two lists of emoji characters across two
devices.

Clients present these emoji to the user with a message like "Confirm that the
emojis below match those shown on your other session".

The spec provides words to describe each character in various languages, and
also a Unicode code point for each character. Different devices and applications
render these characters differently, based on the fonts they have available.

This causes confusion: especially for a user who has never seen this before, it
is not clear what exactly is being asked. (For all they know the list of symbols
is always the same and the important point is whether the font/rendering styles
are identical!)

I suggest that a standard set of images and a standard layout to display them
will help users make a quick and confident judgement of whether they are the
same or different.

## Proposal

I propose providing a fixed set of images to use for emoji verification, and
recommending a fixed layout for display on screen.

### Including URLs in the Emoji table

Currently the spec provides Unicode code points of emoji for each
number 0-63 along with translated names. It also provides this information as
JSON at a well-known URL
(`https://github.com/matrix-org/matrix-spec/blob/main/data-definitions/sas-emoji.json`).

The table within the spec and the JSON file would be adjusted to add links to
URLs like:

`https://github.com/matrix-org/matrix-spec/blob/main/data-definitions/sas-emoji/00.svg`

...

`https://github.com/matrix-org/matrix-spec/blob/main/data-definitions/sas-emoji/63.svg`

And the spec would supply images at these URLs.

I propose including both SVG and PNG format images, so `sas-emoji.json` would
contain entries like this:

```
{
  "number": 4,
  "emoji": "🦄",
  "svg": "https://github.com/matrix-org/matrix-spec/blob/main/data-definitions/sas-emoji/04.svg",
  "png": "https://github.com/matrix-org/matrix-spec/blob/main/data-definitions/sas-emoji/04.png"
  "description": "Unicorn",
  "unicode": "U+1F984",
  "translated_descriptions": {
    "ar": "حصان وحيد القرن",
    "bg": "Еднорог",
    "ca": "Unicorn",
    ...
  }
},
```

### Changes to the spec wording

I propose updating the wording of the spec to say graphical clients SHOULD
include copies of these images in their distributions and display them instead
of the corresponding Unicode code points rendered using a font. They can choose
freely whether to use SVG or PNG images, but prefer SVG if both are possible.

I also propose that graphical clients SHOULD display these images in two rows,
centred vertically, with 4 images on the first row and 3 images on the second,
with the local translation of the corresponding word below each image.

Unless absolutely necessary, the images will not change, so clients are not
expected to update them in future, and will probably not bother to automate
downloads of the images as part of their build process.

There is no uptime guarantee for the supplied URLs, so clients SHOULD NOT depend
on them being available when a user needs to use them.

### Non-graphical clients

Non-graphical clients or other clients that are unable to use the supplied
images may continue to use Unicode code points as before.

### Sourcing the images

I propose taking a snapshot of the relevant images from
[twemoji](https://github.com/twitter/twemoji) at the time of incorporating this proposal
into the spec, and freezing the set of images at that time.

These images are attractive and clear.

These images are provided under the CC BY 4.0 license so may be used with
proper attribution, which should be added to the spec text and client
applications.

### Future changes

If at all possible, these images will not change. In future, if they need to
change in an incompatible way, I expect that the verification process will be
extended to include information allowing clients to negotiate which image set to
use, but this is out of scope for this proposal.

### Tooling

A program to download the necessary images from twemoji is provided at
[codeberg.org/andybalaam/download-matrix-twemoji](https://codeberg.org/andybalaam/download-matrix-twemoji).

The zipped result of running this tool is at
[github.com/user-attachments/files/23101244/sas-emoji.zip](https://github.com/user-attachments/files/23101244/sas-emoji.zip).

If this proposal is merged and the images are available from the spec repo, a
similar tool could be provided to download them directly.

## Potential issues

* If existing clients use Unicode characters to aid accessibility (e.g. for
  blind users), the use of an image might reduce accessibility. However, the
  already-provided word forms of the emoji are intended to give clients an easy
  way of exposing an accessible interface for the verification process, and
  nothing about this proposal changes that. Clients may also use the standard
  accessibility mechanisms for their platform (e.g. the `alt` or `aria-label`
  properties in HTML) to supply the Unicode characters.

* The visual style of the twemoji emojis may not fit well with some client
  applications. I consider this aesthetic disruption worth it if it makes the
  verification process easier to use.

* Some client developers may be concerned at the legal ramifications of
  incorporating CC-licensed artwork into their applications, but my
  understanding of twemoji's license (CC BY 4.0) is that this is allowed for
  applications distributed under any license, so long as they comply with the
  attribution requirement. The
  [README](https://github.com/twitter/twemoji#attribution-requirements) file for
  twemoji lists multiple very easy ways of giving attribution that should be
  possible for any client application. Of course, I am not a lawyer so the
  foundation would need to satisfy itself as to the situation. Client developers
  who really felt unable to adopt the images could continue to display emoji
  using Unicode code points.

## Alternatives

* We could miss out the image URLs in `sas-emoji.json` and expect client
  developers to figure out the correct URLs based on the pattern, but providing
  explicit URLs avoids potential problems with misinterpretations, and provides
  some future-proofing against URL changes in the future.

* We could choose either SVG or PNG images and not supply both. This would
  further improve consistency, but might make life difficult for client
  developers who are not able to render certain image types.

* We could use a different emoji set for the images, for example:

    * [Emojitwo](https://emojitwo.github.io)
    * [noto-emoji](https://github.com/googlefonts/noto-emoji)

    but twemoji is already in widespread use in Matrix clients, so seems the
    least disruptive alternative.

* We could provide the images as a zip file like
  [github.com/user-attachments/files/23101244/sas-emoji.zip](https://github.com/user-attachments/files/23101244/sas-emoji.zip)
  either in addition to the individual images, or as an alternative. This would
  probably be more convenient for client implementors, but would be less aligned
  with the way sas-emoji.json is structured.

## Security considerations

This proposal is intended to improve security by making it easier for users to
perform verification.

If implemented correctly within clients, I can't see any security risks.

## Unstable prefix

None required.

## Dependencies

None.

## Implementations

There is a draft Element Web implementation in
[element-web#31571](https://github.com/element-hq/element-web/pull/31571), which
uses a temporary custom version of the spec npm package at
[andybalaam-matrix-spec](https://www.npmjs.com/package/andybalaam-matrix-spec),
built from a draft spec PR at
[matrix-spec#2273](https://github.com/matrix-org/matrix-spec/pull/2273).
