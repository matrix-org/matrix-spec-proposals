# MSC4221: Room Banners

This proposal adds room banners to Matrix, similar to the way Discord has guild banners.

## Proposal

Matrix has ways to add room avatars, but those are limited to a 1:1 aspect ratio. This proposal adds banners to rooms, which are a 16:9 aspect ratio.
A banner state event should have the type `m.room.banner` and the content should contain the `url` in `mxc://` format.
Example event:
```json
{
  "type": "m.room.banner",
  "sender": "@everypizza:chat.blahaj.zone",
  "content": {
    "info": {
      "mimetype": "image/jpeg"
    },
    "url": "mxc://…/…"
  },
…
}
```
## Potential issues

A malicious user could upload a banner with explicit or illegal content. A future MSC may provide a way to mark room pictures or banners as sensitive using [MSC4193](http://github.com/matrix-org/matrix-spec-proposals/pull/4193).

## Alternatives

Pinned messages and room topics are in similar areas of the UI in some clients.

## Security considerations

None I can think of.

## Unstable prefix

While this MSC is unstable, clients wanting to implement this should use `page.codeberg.everypizza.room.banner` instead of `m.room.banner`.

## Dependencies

N/A
