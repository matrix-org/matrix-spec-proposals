# MSC4459: Image pack references
[MSC2545](https://github.com/matrix-org/matrix-spec-proposals/pull/2545)
introduced image packs, which can be used as stickers and custom emojis.
However, it did not specify an easy way to share packs other than manually
linking to the room that contains the pack. Other networks like Telegram,
WhatsApp and Signal allow sharing packs by simply sending a sticker or custom
emoji, which allows the recipient to click the image to view the pack.

## Proposal
This proposal introduces an image pack sharing mechanism similar to other
networks by adding metadata about the origin of the image to sticker events.

A `m.image_source_packs` field is added to `m.sticker` events. The field
contains a map from `mxc://` URI to an image pack reference. The reference
object contains:

* `room_id` with the ID of the room where the image pack is located.
* `via` (optional) with an array of server names that can be used to join the room.
* `state_key` with the state key of the image pack state event.
* `shortcode` with the short code of the particular image that was used
  (the shortcode is the key in the `images` map inside the state event).

The field can be used in any event that contains images from an image pack. It
is a map to allow use in contexts where one event contains multiple images.
The primary use cases are:

* `m.sticker` events
* `m.reaction` events using [MSC4027](https://github.com/matrix-org/matrix-spec-proposals/pull/4027) or similar proposals
* `m.room.message` events containing custom emojis in `formatted_body`

To avoid leaking information about private packs, clients SHOULD only reference
packs that are in a public or knockable room.

### Examples

<details>
<summary>Sticker</summary>

```json
{
  "type": "m.sticker",
  "content": {
    "body": "Blobcat threatens you with cactus",
    "url": "mxc://tastytea.de/glmVmTfoMPqAYETjWCGreuag"
    "info": {
      "mimetype": "image/png",
      "size": 17198,
      "w": 64,
      "h": 64
    },
    "m.mentions": {},
    "m.image_source_packs": {
      "mxc://tastytea.de/glmVmTfoMPqAYETjWCGreuag": {
        "room_id": "!mxZlZeHjtbkmpqofEQ:tastytea.de",
        "via": ["fairydust.space", "matrix.org", "maunium.net"],
        "state_key": "Unhappy Blobcats",
        "shortcode": "blobcat_cactus"
      }
    }
  }
}
```

</details>

<details>
<summary>Reaction using MSC4027</summary>

```json
{
  "type": "m.reaction",
  "content": {
    "m.relates_to": {
      "rel_type": "m.annotation",
      "event_id": "$0KG--Cf1Xi3qpVgudjBrLRdr6nYCP4rqZXo867esl5I",
      "key": "mxc://tastytea.de/glmVmTfoMPqAYETjWCGreuag"
    },
    "com.beeper.reaction.shortcode": ":blobcat_cactus:",
    "m.image_source_packs": {
      "mxc://tastytea.de/glmVmTfoMPqAYETjWCGreuag": {
        "room_id": "!mxZlZeHjtbkmpqofEQ:tastytea.de",
        "via": ["fairydust.space", "matrix.org", "maunium.net"],
        "state_key": "Unhappy Blobcats",
        "shortcode": "blobcat_cactus"
      }
    }
  }
}
```

</details>

<details>
<summary>Text message with custom emojis</summary>

```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text"
    "body": "meow :blobcat_cactus: :blobcat_thinking:",
    "format": "org.matrix.custom.html",
    "formatted_body": "meow <img src=\"mxc://tastytea.de/glmVmTfoMPqAYETjWCGreuag\" alt=\":blobcat_cactus:\" title=\"Blobcat threatens you with cactus\" data-mx-emoticon=\"\" height=\"32\"> <img src=\"mxc://tastytea.de/uBWzDiNIwAEKvZuisqCdMNIH\" alt=\":blobcat_thinking:\" title=\"Thinking Blobcat\" data-mx-emoticon=\"\" height=\"32\">",
    "m.mentions": {},
    "m.image_source_packs": {
      "mxc://tastytea.de/glmVmTfoMPqAYETjWCGreuag": {
        "room_id": "!mxZlZeHjtbkmpqofEQ:tastytea.de",
        "via": ["fairydust.space", "matrix.org", "maunium.net"],
        "state_key": "Unhappy Blobcats",
        "shortcode": "blobcat_cactus"
      },
      "mxc://tastytea.de/uBWzDiNIwAEKvZuisqCdMNIH": {
        "room_id": "!mxZlZeHjtbkmpqofEQ:tastytea.de",
        "via": ["fairydust.space", "matrix.org", "maunium.net"],
        "state_key": "Misc Blobcats",
        "shortcode": "blobcat_thinking"
      }
    }
  }
}
```

</details>


## Potential issues
If an image is present in multiple packs, the client will have to pick one to
use as the source. This is likely not an issue, as sticker and emoji pickers are
usually grouped by pack. Clients can also always omit the source if they can't
pick one.

## Alternatives
The source could be expressed as some kind of a `matrix:` URI instead of an
object, e.g. `matrix:roomid/mxZlZeHjtbkmpqofEQ:tastytea.de?via=fairydust.space&via=matrix.org&via=maunium.net&action=show_image_pack&image_pack_key=Unhappy%20Blobcats&image_shortcode=blobcat_cactus`.
This would allow sharing links outside of Matrix, but it's much less readable
than a JSON object. A future MSC can still define a URI format for external
linking if needed.

Packs could have a new flag to indicate whether they want to be referenced
instead of only relying on room join rules.

## Security considerations
Some information about image packs and rooms may be leaked if clients aren't
careful with what they include references to.

## Unstable prefix
`com.beeper.msc4459.image_source_packs` can be used instead of `m.image_source_packs`

## Dependencies
This MSC builds on MSC2545, which is in final comment period as of writing and
will presumably be accepted.

This MSC can also be used together with MSC4027, but there is no hard dependency.
