# MSC3971: Sharing image packs

MSC2545 proposes a way to implement image sets in Matrix, but there is no convenient way to find or
share image sets.  In the current state of Matrix, users want access to more image sets, but cannot
find them. We propose a way to address this issue which will make it easier for users to access the
image sets they desire.

In other messaging applications, images sent from an image pack, such as emojis and stickers, are
clickable, and clicking the image leads the user to that pack.  Additionally, some competitiors
provide a permalink url to each image pack, allowing these urls to be shared as well as cataloged
on third party sites.

In this MSC, we propose a way to provide the following:

1. Sharable url link to the image pack.
2. Clickable emojis and stickers.

With the following requirements:

1. Links is sharable inside and outside Matrix clients.  When shared outside a Matrix client, such
  as on a social media site, clicking the link will open Matrix and show the image pack, if the
  user's client supports it.
2. Reasonable fallback in case the user is using a client that does not yet implement this MSC.
3. Handle it appropriately when a room has multiple image packs.


## Proposal

In order to share an image pack, a matrix.to deeplink to the latest state event for that pack should
be used.  When clicked in a supported Matrix client, the client should use this event id to display
the latest version of the pack, as well as optionally changes to the pack that happened since.  This
url is the "pack url".  The room id must be used, not the room alias, as the alias may change.

Depending on the adoption of the protocol, a matrix:// url may also be used.

To indicate that a link is linking to an image pack, the query param ```action=view_image_pack``` should
be added to the url.  Clients should still treat links to an image pack as a pack url, even if the query
param is not present.  If the query param is present, but the linked event is not an image pack event,
client must either display an error or simply treat the link as an event link that's not an image pack.

It is recommended that in the UI for viewing, updating, or manging packs, that the client provide a
function for the user to copy the pack url to the clipboard for easy sharing.  This function should
not be shown for packs that are part of private rooms.

If a client not supporting this MSC clicks this link, then the deeplink will simply point to the state
event, if that client chooses to display it.

### Stickers and emojis

When the image pack is part of a public room which supports guest access, then the client must include
the pack url in the event when sending an image from that pack.  If the room is private, then the
client must not include the pack url.  In the case of other levels of privacy, such as whether the
room allows membership requests (knocking) or has joining through a space, the client may optionally
share the pack url at the discretion of the user.

Of course, when sending an emoji or sticker that is not part of a pack, the client does not have to
include a pack url either.


The pack url is included in the following way:

1. For stickers, the pack url is included as an additional string field in the event content ```pack_url```
2. For emojis, the emoji should be sent as in MSC 2545 with an additional data field ```data-mx-pack-url```
  to indicate that this is a pack.  ```<img data-mx-emoticon data-mx-pack-url="https://matrix.to/#/!hvgkwxdxoAwOmJvvUH:matrix.org/$_KxiZYeOMJDthWxj3m_lRiW_twVmOMJo_afvRRmnkCM" height="18" src="mxc://matrix.org/cqiMCZgfXMWgDQqqFYnhjFPk" title=":abc:" alt=":abc:">```

## Potential issues

The main issue with this proposal is that these links are indistinguishable from regular matrix deeplinks.  This
way, it is difficult for the client to give a good user experience without knowing the room contents, and if the
room cannot be previewed, then the user will only be left with a "this room can't be previewed" wall.

It's possible that the pack may have been changed, and the pack no longer contains the image that linked to it.
This is not an ideal end user experience.

## Alternatives

An alternative to this proposal is to implement a bespoke url scheme for sharing image sets.  If we did this
then we can have a more seamless "add pack" experience even if the room is not previewable.  For example, the user
might see the message "this pack can't be previewed: Add Pack" and still get the option to add the pack in one click.

## Security considerations

There are no major security implications of this change.  Clients may only share room links of public rooms
with guest access.

## Unstable prefix

For stickers, the pack url field should be ```arc_pack_url```.
For emojis, the data field should be ```data-arc-pack-url```

## Dependencies

This MSC builds on MSC2545 (which at the time of writing has not yet been accepted
into the spec).
