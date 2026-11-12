# MSC4581: Media annotations and universal alt text

## Introduction

This proposal provides a mechanism for additional metadata about instances of media to be provided in
events in a schema-independent manner, and a use of that mechanism to provide media alt text.

Currently, the majority of event and message types that reference media do not provide any mechanism
for clients to include alt text for that media, something that remains important for accessibility
even in the context of instant messaging where it might be possible to ask the room for a description
of media. 

This proposal additionally targets forwards-compatibility with the current iteration of Extensible
Events. In that context, this proposal would substitute the `m.alt_text` content block defined in
[MSC3552] alongside `m.image`.

### Definition of alt text

This proposal refers to the HTML 5 specification, and assumes alt text to be used in a manner
consistent with [HTML 5 section 4.8.1.1](https://dev.w3.org/html5/spec-LC/embedded-content-1.html#alt).

HTML only specifies alt text for images, however this proposal permits for alt text to be provided
for media irrespective of its type.

An alt text for a video could contain a description of the events in the video, similarly to the
description of an image.

An alt text for an audio recording could be a description of a sound, again similar to that of
images, or a transcript of speech.

Alt text is not usually useful on media that is itself text or a binary format, but there is no
particular reason to disallow this.

### Universality of media annotations

Whether alt text or other media annotations are desired for any particular instance of media 
depends purely on the receiving client's interface, the receiving user's preferences and 
accessibility needs, and the properties of any accessibility tooling that is in use.

As such, neither the protocol nor the sender can safely decide where they are improper. This 
proposal's mechanism is thus independent of the schema of any particular event. It is not expected 
that all receivers consume all alt text (or any other media annotation), and it is not expected that
all media annotations make sense in all contexts where they are technically valid. It is up to the
sender to provide them where-ever possible, and to the receiver to take the ones that are wanted.

## Proposal

### Structures

A Media Map is an object where each key is a Matrix Content URI. Each URI maps to a Media Annotations
object pertaining to that media.

A Media Annotations object is keyed by namespaced identifiers representing a specific media annotation
type, and has values defined by that media annotation type. This proposal later defines the media 
annotation `m.alt` for alt text.

Future extensions could for example include mechanisms for:
- Tagging media with warnings (NSFW, flashing lights hazard, etc) in a structured manner, such that
  clients can automatically opt to hide it
- Structured links to related content (such as extended source information or a link to a transcript)
- Referencing the image pack an image was constructed from. [MSC4459] achieves this using a structure
  almost identical to the Media Map, but which is not extensible.

If this is proposal is accepted, a planned future MSC is expected to specify some mechanism for trusted
users in a room to supply some types of media annotations for an event where the sender did not include
them in the event.

### `m.media_annotations` event property

A new optional property `m.media_annotations` is defined on the content of all current and future event
types that can contain a reference to media, including state events such as `m.room.member` (which may
contain `avatar_url`). Since this property only has effect when media is actually used, maintaining a list
of such event types is not useful.

`m.media_annotations` on an event contains an Media Map scoped to media explicitly referenced anywhere 
within that event's content.

Under Extensible Events, this is best classified a mixin.

Example on a message of type `m.image`

```jsonc
{
	"type": "m.room.message",
	"msgtype": "m.image",
	"url": "mxc://example.org/A",
	"body": "the matrix logo looks like this",
	"m.media_annotations": {
		"mxc://example.org/A": {
			// m.alt's schema is described later
			"m.alt": {
    			"m.text": [{"body": "the lowercase letter M enclosed in mathematical square brackets"}]
    		},
            "org.example.foo.bar": "baz"
		}
	}
	// irrelevant data omitted
}
```

When a client is processing media with a definite *source* and wishes to obtain an annotation, the
`m.media_annotations` key of the *source* is checked for the media's URI. If a Media Annotations object 
exists in the relevant Media Map, the annotation's value is taken from there (if present). If no 
`m.media_annotations` is present, then the annotation is considered absent.

The *source* object is either:
- the sole event content from which the media URI being processed was copied. This might be an
  `m.new_content` object or a `prev_content` object
- as defined under [Reactions](#reactions), whenever multiple events' identical media references are
  coalesced, the content of the *first* event 
- as defined in the next section, an extended profile property's object value, from which the media URI
  was copied
- as defined in the next section, the user profile object itself, from which the media URI was copied

Potential examples for the first case:
- rendering an `m.room.message` of type `m.image`: sourced from the event's `content`
- rendering a room avatar: the room's `m.room.avatar` state event
- rendering a member's avatar in a room: the relevant `m.room.member` state event
- rendering images directly from an image pack (eg in a sticker picker): the relevant `m.room.image_pack`
  state event
- rendering the previous avatar of a user in a "user changed avatar from A to B" message: sourced from
  `prev_content`

#### `m.media_annotations` extended profile property

A new key `m.media_annotations` is defined for [User Profiles](https://spec.matrix.org/latest/client-server-api/#profiles), 
which contains a Media Map applicable whenever the processed media URI was taken directly from that user
profile, instead of any room event.

A planned future MSC is expected to specify server behaviour for transfer of relevant media annotations
into `m.room.member` events on user join and on profile updates.

In exception, if the profile property containing the media is an object, and a `m.media_annotations` key
exists at its top level, then that Media Map MUST be used instead of the dedicated `m.media_annotations`
profile property. Unless specified otherwise, `m.media_annotations` is valid on any profile property that
is an object.

Example profile:

```jsonc
{
  "displayname": "Matrix User",
  "avatar_url": "mxc://matrix.org/ABC",
  
  // unstable from MSC4427, as an example of a non-object containing media
  "chat.commet.profile_banner": "mxc://matrix.org/DEF",

  "m.media_annotations": {
    "mxc://matrix.org/ABC": {
      "m.alt": {
    	"m.text": [{"body": "Matrix logo"}]
      },
      "org.example.foo": "bar"
    },
    "mxc://matrix.org/DEF": {
      "org.example.bar": "foo"
    }
  }
}
```

#### `m.alt` media annotation

The `m.alt` media annotation wraps an `m.text` content block as defined by [MSC1767] (merged), which
contains alt text for the media it pertains to.

If an `m.alt` media annotation is absent, malformed, or contains no suitable text representation, the
client MAY fall back to attempting to source or generate alt text via some other mechanism, but a client
SHOULD NOT do this if the alt text is merely empty. Per [HTML 5 section 4.8.1.1.6], an empty alt text is
an explicit statement that a description is not required (eg. the surrounding text already describes the
image), and accessibility software may treat this in a special manner.

`m.alt` annotations with a value of `{}`, `{"m.text":[]}`, and `{"m.text":[{"body":""}]}` MUST all lead
to identical behaviour.

Clients SHOULD NOT accept `text/html` or other rich text formats in alt text. As in [MSC3552], `m.text`
is used purely for forwards-compatibility.

The `alt` attribute on `<img>` elements in HTML-formatted text takes precedence over `m.alt`. Clients
SHOULD still use `m.alt` if the attribute is not present.

The `m.alt` media annotation takes precedence over any other possible source of alt text unless specified
otherwise.

Currently there is no advantage in specifying an alt text for an inline image in normal messages, however
that is not necessarily true inside of a multi-representation `m.text`. It is possible that a client would
pick a different representation for the alt text than it did for the text the image is in. If non-HTML
rich text formats are ever supported, they might not be able to accomodate inline alt text at all.

Implementations should note:
- Alt texts are not used solely by screen readers. Interface for easily inspecting the alt text of media
  should be accessible for everyone.
- As specified by HTML, alt text SHOULD NOT be rendered as a tooltip, to avoid it becoming chronically
  misused as such rather than as an accessibility mechanism.

### Changes to the `m.sticker` event

Unlike the `body` property of `m.room.message`'s attachment types (ex [`m.room.image`](https://spec.matrix.org/v1.19/client-server-api/#mimage)),
the `body` property of [`m.sticker`](https://spec.matrix.org/v1.19/client-server-api/#msticker) is not
defined to be a caption. It is instead ambiguously defined to be "the alt text of the original image, or
a message to accompany and further describe the sticker"

In practice, the `body` is almost always copied from an image pack, where the corresponding `body` is
explicitly specified to contain alt text. As a result, the the `body` of stickers is almost never used
for captions, and majority of clients never display it as such.

This proposal deprecates the required `body` property of `m.sticker`, as it is made redundant. As it is
currently a required property, it MUST not be omitted until removed completely.

Example sticker event content:
```jsonc
{
    "body": "Matrix logo on a hexagon", // backwards-compatibility
	"info": {
        "h": 256,
        "mimetype": "image/png",
        "size": 21957,
        "w": 222
    },
	"m.media_annotations": {
    	"mxc://matrix.org/mRJacbBEPAJczvOltdhABxSv": {
    		"m.alt": {
    			"m.text": [{"body": "Matrix logo on a hexagon"}]
    		}
    	}
    },
	"url": "mxc://matrix.org/mRJacbBEPAJczvOltdhABxSv",
}
```

### Changes to image packs

The optional property `body` in [Image Pack Images](https://spec.matrix.org/latest/client-server-api/#mroomimage_pack_imagepackimage),
defined to contain alt text for the image, is deprecated.

When an Image Pack Image is used as a template, all applicable media annotations (including unrecognized
keys) are copied verbatim from the Media Map of the `m.room.image_pack` into the Media Map applicable to
the target context. 

When constructing an `<img>` and the `m.alt` media annotation contains only one text representation, the
alt text MAY be moved into the `alt` attribute. A client might also decide to not do this, for example to
avoid combining mismatching representations. Alt text should not be duplicated into both the Media
Annotations and the HTML element, however.

When constructing a sticker event under the same conditions, clients MAY duplicate the alt text into the
deprecated `body` of the sticker for backwards-compatibility. If `body` of the sticker is not set in this
manner, it MUST be set to the empty string, as it is still a required property.

If the image pack event contains no `m.media_annotations`, clients SHOULD synthesize one containing alt
text specified by the deprecated `body`, if that is present.

Example image pack contents:

```jsonc
{
  "images": {
    "keyboard_cat": {
      "url": "mxc://matrix.org/qwerty",
      "info": {
        "h": 12345,
        "w": 12345,
        "mimetype": "image/webp",
        "size": 150498245
      },      
    },
  },
  "pack": {
    "avatar_url": "mxc://matrix.org/asdf",
    "display_name": "random stickers",
    "usage": [
        "sticker"
    ]
  },
  "m.media_annotations": {
    "mxc://matrix.org/qwerty": {
      "m.alt": {
        "m.text": [{"body":"innocent-eyed cat sitting on a keyboard"}]
      },
      "org.example.foo": "bar",
    },
    "mxc://matrix.org/asdf": {
      "m.alt": {
        "m.text": [{"body":"<the alt text of the pack avatar>"}]
      }
    }
  }
}
```

### Reactions

Although there is no formally accepted mechanism for media in reactions, [MSC4027] has wide support.

Most clients coalesce identical reactions into a single interface element. In this circumstance, there are
multiple equally valid *source* events. To ensure that reactions are treated in a consistent manner, the
following mechanism for selecting the *source* is REQUIRED.

Whenever identical media references from multiple events are coalesced, the chronologically *first* event
is considered as a source for media annotations. The *first* event is the one which the client, to its
best knowledge, determines to be earliest in the room timeline (the specification does not require timeline
ordering to be consistent between different API endpoints). If the *first* event is determined, but does
not contain a Media Map, or its Media Map does not contain the sought media annotation type, then the media
annotation is considered absent. Other events MUST NOT be considered (this is due to T&S concerns described
in a later section).

If a client duplicates an existing reaction, the Media Map of the *first* event SHOULD be copied into the
new reaction to further increase consistency. The client MUST NOT create any that are not identical to ones
present in the *first* event. This helps ensure that annotations remain consistent even a client picks a
later event as *first* (due to the federation failure, the sender of the *first* event being ignored, or the
*first* event becoming redacted)

It should be noted that the *first* event may be edited to alter media annotations, whereas before editing
reactions was meaningless.

### Thumbnails

Some events allow explicitly specifying a media URI for a thumbnail of other media in the event. For the
purposes of media annotations, the thumbnail is treated as identical to the media it is thumbnailing. Media
annotations specifically targeting a thumbnail image MUST NOT be specified, and SHOULD be ignored. 

This does not apply to thumbnails that are not actually associated with any other media (such as in the case
of the `m.location` msgtype, in which the only present media is the thumbnail)

## Security Considerations

None. Any media annotations pertaining to encrypted media will be encrypted, as encrypted media is already
meaningless outside of an encrypted event.

## T&S considerations

### Nature of alt text

This proposal adds new ways for arbitrary text to be shared by clients, and furthermore, since alt text is
not expected to be inspected by most recipients of a message, but relied upon by those that do, abusive alt
text can be especially problematic.

This problem is a direct consequence of the purpose of alt text, however, so it cannot be mitigated, and is
already currently present in the protocol by virtue of `<img>` and `m.sticker`'s `body`

Clients SHOULD provide an easy mechanism to inspect the alt texts of media (although this should be done
regardless of T&S concerns, as alt texts are not used solely by screen readers)

Policy servers are expected to inspect `m.alt` and apply any necessary checks. Policy servers have no need
to determine whether a Media Annotations is actually applicable to any media in the event to do this.

### Coalescing

The instruction for only the *first* reaction to be considered when events are coalesced (as opposed to other
options, like iterating through them until the desired annotation is found), is a consequence of a T&S concern.

Clients picking inconsistent annotations for a reaction would make reactions significantly harder to moderate,
as users might end up seeing contextually different content. Any other strategy of picking a *source* also
introduces the ability for a user to abuse that algorithm to alter the contextual meaning of an event sent by
a different user post-factum, which is extremely undesirable.

It is impossible to be perfectly consistent, but this mechanism most reliably determines which user is
ultimately responsible for the coalesced content.

## Potential issues

### Policy servers

Alt text being inspected and rejected by policy servers can lead to significant confusion, since alt text is
not actually rendered under normal circumstances, and if copied from elsewhere will not have been written in
conjunction with the event.

This is alleviated by [MSC4387], which specifies a mechanism for policy servers to provide user-facing error
messages.

### Media reuse

The same media can appear multiple times in an event, and this proposal's mechanism intentionally does not
separate such cases, as media annotations are intended to be used for information about media that is independent
of its role in an event. Alt text, strictly speaking, *is* context-sensitive. However, in practice, the scope
of a single event is limited, and media re-use not originating from an image pack is extremely rare in the first
place.

## Alternatives

Overall, the arguments against known alternatives are based on this proposal's mechanism providing greater
consistency and forwards-compatibility

### Extensibility of `m.media_annotations`

It would be possible to map media URIs directly to the alt text object, instead of creating an intermediary
`m.alt`. However, in addition to other potential uses for media annotations listed earlier, [MSC4459] having
arrived at using an identical (but non-extensible) data structure is evidence that an extensible structure
is warranted.

### `m.alt_text` (Extensible Events)

Under Extensible Events, the `m.alt_text` content block is specified alongside `m.image` and could be
re-used. This proposal's mechanism remains compatible with the current iteration of Extensible Events without
modification, however. 

Every type that can contain media has to declare that it supports alt text explicitly, as the intended
application of an `m.alt_text` is not necessarily clear from context alone. This also means that alt text
may end up being inexplicably unsupported in some contexts, and renders it useless for forming fallbacks.
Extensible Events also explicitly requires unexpected content blocks in a known schema to be ignored. 

`m.alt_text` can only apply to one piece of media, and is also not compatible with inline media, as an
extensible object cannot be represented inline.

A generic `m.alt_text` has the same properties as this proposal when it comes to interaction with
thumbnails and reactions.

### Text formats in `m.alt`

Using `m.text` inside of alt text is a decision present in [MSC3552], and is done there for the purposes
of internationalization via [MSC3554], and other potential future extensions.

This proposal follows the same reasoning. 

Internationalization of alt text has obvious utility, however `m.text` also has the consequence of allowing
formatted text. Some aspects of formatted text, such as lists or emphasis, might be used even if not rendered
visually. However, formatted text also means potentially allowing custom formats, and even within HTML allows
the possibility of alt texts which contain math, colours, or even recursive self-references to themselves.
This would require a large amount of specific sanitization rules to make use of, for limited gain, so this
proposal recommends against allowing it at all.

### `body` of `m.sticker`

Instead of deprecating the property, it is possible to align it with `body` of `m.message`, by redefining
it to solely a caption. 

However, this would cause clients implementing this MSC to render the alt texts of stickers sent by clients
that do not (as well as historic stickers), which would lead to extreme visual disruption. If captions are
found to be desired, a separate MSC could re-introduce them under a different key.

### Thumbnails

Media annotations on thumbnails do have fringe use-cases, such as `m.alt` on video thumbnails. However, it 
s expected that if this were allowed, the resultant behaviour would be far too inconsistent to be
practically usable.

## Dependencies

This proposal has no dependencies.

## Unstable prefix

as long as this proposal is not in an accepted state, the following unstable identifiers should be used:
- `net.31a05b.media_annotations` instead of `m.media_annotations`
- `net.31a05b.media_alt` instead of `m.alt`

[MSC3552]: https://github.com/matrix-org/matrix-spec-proposals/pull/3552
[MSC3554]: https://github.com/matrix-org/matrix-spec-proposals/pull/3554
[MSC1767]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767
[MSC4459]: https://github.com/matrix-org/matrix-spec-proposals/pull/4459
[MSC4387]: https://github.com/matrix-org/matrix-spec-proposals/pull/4387
[MSC4027]: https://github.com/matrix-org/matrix-spec-proposals/pull/4027

[HTML 5 section 4.8.1.1.6]: https://dev.w3.org/html5/spec-LC/embedded-content-1.html#a-graphical-representation-of-some-of-the-surrounding-text
