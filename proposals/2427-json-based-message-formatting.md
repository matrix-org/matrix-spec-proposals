# JSON based message formatting
## Problem
Matrix formatting is currently based on a subset of HTML. While HTML is easy to
render in a browser, other platforms have to either make a completely custom
renderer, or use an existing renderer where the supported subset may not match
the subset used in Matrix. Additionally, custom attributes like `data-mx-color`
mean that even clients that can use existing renderers will need to preprocess
the HTML or modify the renderer.

## Proposal
The proposed solution is a JSON-based message formatting system. While JSON is
not the most efficient byte count wise, it would be trivial to switch to a
binary object representation when using this system.

While a custom formatting system means new renderers will need to be made in
all environments, it is easier to make a custom renderer for text formatted
using a well-defined JSON system, than it is to parse HTML and try to handle
all the quirks.

A formatted message consists of one or more chunks. Each chunk is a JSON
object, containing one primary field and zero or more secondary fields. The
chunks are located in an array under the `m.formatted` key of the `content`
object. All fields are namespaced.

##### Primary field
The primary field is the main content of the chunk. Each chunk must have
exactly one primary field.

* `m.text` (string) - A normal text chunk.
* `m.image` (string) - An inline image. The value must be a `mxc://` URI to an
  image.

##### Secondary fields (attributes)
Secondary fields are attributes that change the way the chunk is rendered. The
number of secondary fields is not restricted, but some fields have other
conditions. Unknown secondary field types should be ignored.

`simple` attributes are booleans that must either be `true` or not be set at
all.

* `m.bold` (simple) - **Bold**
* `m.italic` (simple) - *Italic*
* `m.strikethrough` (simple) - ~~Strikethrough~~
* `m.underline` (simple) - <u>Underline</u>
* `m.quote` (simple) - A “quote”. May also be rendered as a
  > blockquote.
* `m.superscript` (simple) - <sup>Super</sup>script
* `m.subscript` (simple) - <sub>Sub</sub>script
* `m.spoiler` (string) - Spoiler. The value is the reason for the spoiler and
  should be shown before the hidden content.
* `m.code` (string) - Monospace text. The value is the language.
* `m.link` (string) - Hyperlink. The value is the URL. As in the current HTML
  subset, clients should only allow the schemes `http`, `https`, `ftp`,
  `mailto`, `gopher`, `magnet` or platform specific known schemes.
* `m.link.preview` (boolean) - Whether or not to include an URL preview. Only
  valid if `m.link` is set. Defaults to `true` or the URL previewing preference
  of the user.
* `m.user` (string) - Matrix user ID to reference.
* `m.mention` (boolean) - Whether or not to ping the referenced user. Only
  valid if `m.user` is set. Defaults to `true`.
* `m.room` (string) - Matrix room alias or ID to reference.
* `m.width` (int) - Width for image. Only valid if primary type is `image`.
* `m.height` (int) - Height for image. Only valid if primary type is `image`.
* `m.mime_type` (string) - The mime type for the image. Can also be used to
  specify the mime type of the text, although clients may not use that
  information for anything.
* `m.alt_text` (string) - The alt text and hover title for the image. Only
  valid if primary type is `image`.
* `m.fg_color` (string) - Foreground color as a hex color. Only valid if
  primary type is `text`.
* `m.bg_color` (string) - Background color as a hex color. Allowed for both
  `text` and `image` primary types, as transparent images may want to specify a
  different background color.

##### Versioning
Events that use the `m.formatted` key MUST also contain the `m.formatted.version`
key, which specifies the version of the formatting schema. The value of the
version field should be two numeric identifiers, the major and minor version
number, separated by a dot. The initial version is `0.1`.

Minor version changes may only add or deprecate secondary fields. Major version
changes may also change primary fields. When a client encounters a major version
that it does not recognize, it should fall back to rendering the plaintext body.

For example, a future minor version could include support for replies to a part
of a message, i.e. rich quotes.

### Disadvantages compared to current Matrix HTML
* No truly nested formatting. While a chunk can have multiple styles like
  `m.bold` and `m.italic` simultaneously, it can't have child elements like
  HTML can. In practice, this means:
  * No tables. This is not really relevant for instant messaging: they're hard
    to render, only riot web supports them anyway, and even that doesn't
    support sending them after the switch to CommonMark.
  * No lists. Lists can be done with plain text. It's also better if users
    don't get surprised by `6.` turning into `1.` because it's an ordered list,
    although that's more of a markdown input problem.
* More bytes. However, switching Matrix to a more efficient binary format would
  make it have less bytes. Especially a partially structured binary format
  could be significantly more efficient.

### Examples
```json
{
  "m.formatted.version": "0.1",
  "m.formatted": [
    {"m.mention": true, "m.user": "@user:example.org", "m.text": "Pretty user"},
    {"m.text": ": Good day, user!\nDid you see this image?\n"},
    {"m.width": 128, "m.height": 64, "m.alt_text": "Fancy image", "m.image": "mxc://example.org/ABCDEF"}
  ]
}
``` 
```html
<a href="https://matrix.to/#/@user:example.org">Pretty user</a>: Good day, user!<br/>
Did you see this image?<br/>
<img src="mxc://example.org/ABCDEF" width="128" height="64" alt="Fancy image" title="Fancy image" />
```

---

```json
{
  "m.formatted.version": "0.1",
  "m.formatted": [
    {"m.text": "I like cheese "},
    {"m.italic" true, "m.text": "Thiiiiiis" },
    {"m.text": " much"}
  ]
}
```
```html
I like cheese <em>Thiiiiiis</em> much
```

---

```json
{
  "m.formatted.version": "0.1",
  "m.formatted": [
    {"m.fg_color": "#ff0000", "m.text":"R"},
    {"m.fg_color": "#ffdb00", "m.text":"A"},
    {"m.fg_color": "#49ff00", "m.text":"I"},
    {"m.fg_color": "#00ff92", "m.text":"N"},
    {"m.fg_color": "#0092ff", "m.text":"B"},
    {"m.fg_color": "#4900ff", "m.text":"O"},
    {"m.fg_color": "#ff00db", "m.text":"W"}
  ]
}
```
```html
<font color="#ff0000">R</font>
<font color="#ffdb00">A</font>
<font color="#49ff00">I</font>
<font color="#00ff92">N</font>
<font color="#0092ff">B</font>
<font color="#4900ff">O</font>
<font color="#ff00db">W</font>
```

## Alternatives
### Indexed formatting entities
Instead of having the text within the formatting entities, the formatting
entities could use indexes to refer to a separate plain text string. However,
this would require specifying the exact encoding used for indexing, and was
therefore rejected.
