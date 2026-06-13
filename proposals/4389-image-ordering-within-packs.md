# MSC4389: Image ordering within packs
[MSC2545] defines image packs for use as stickers and custom emojis. [MSC4377]
extended it to define how packs are ordered. However, neither MSC defines how
images are ordered within a pack.

[MSC2545]: https://github.com/matrix-org/matrix-spec-proposals/pull/2545
[MSC4377]: https://github.com/matrix-org/matrix-spec-proposals/pull/4377

## Proposal
A new `order` field with an integer value is added to the entries inside the
`images` object. Clients SHOULD sort the images in a pack using the order field
when displaying the entire pack to users (e.g. in a sticker or emoji picker).
A missing `order` field is treated as zero (0) when sorting.

When editing a pack, clients SHOULD ensure all images in the pack have an order
set. Overwriting the order value of all images is a reasonable solution, because
the entire pack is updated atomically.

## Potential issues
If a `PATCH` endpoint is added for room state or account data, it could break
the assumption that packs are always mutated atomically. However, even then
clients can just choose to keep using the `PUT` endpoint.

## Alternatives
The `order` field could use strings like [space children do](https://spec.matrix.org/v1.16/client-server-api/#ordering-of-children-within-a-space).
The benefit of strings is that it allows inserting items in between existing
items without updating orders of every item. However, unlike space children,
images within packs are never mutated individually. It's trivial for clients to
update every order value whenever they move an image.

## Security considerations
None.

## Unstable prefix
`fi.mau.msc4389.order` can be used instead of `order` until this MSC is accepted.

## Dependencies
This MSC is an extension to [MSC2545: Image Packs](https://github.com/matrix-org/matrix-spec-proposals/pull/2545)
and therefore depends on it.
