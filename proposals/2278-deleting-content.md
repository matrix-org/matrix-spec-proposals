# Proposal for deleting content for expired and redacted messages

## Overview

[MSC1763](https://https://github.com/matrix-org/matrix-doc/pull/1763) proposes
the `m.room.retention` state event for defining how aggressively servers
should purge old messages for a given room.

It originally also specified how media for purged events should be purged from
disk, however this was split out into a new MSC [by
request](https://github.com/matrix-org/matrix-doc/pull/1763#discussion_r320289119)
during review.

## Proposal

We handle encrypted & unencrypted rooms differently.  Both require an API to
delete content from the local media repo (bug
[#790](https://github.com/matrix-org/matrix-doc/issues/790)), for which we
propose:

```
DELETE /_matrix/media/r0/download/{serverName}/{mediaId}
```
with a JSON dict as a request body.

The API would returns:
 * `200 OK {}` on success
 * `403` with error `M_FORBIDDEN` if invalid access_token or not authorised to delete.
 * `404` with error `M_NOT_FOUND` if the content described in the URL does not exist on the local server.

The user must be authenticated via access_token or Authorization header as the
original uploader, or however the server sees fit in order to delete the content.

Servers may wish to quarantine the deleted content for some timeframe before
actually purging it from storage, in order to mitigate abuse.

	XXX: We might want to provide an undelete API too to let users rescue
	their content that they accidentally deleted, as you would get on a
	typical desktop OS file manager.  Perhaps `DELETE` with `{ undo: true }`?

	XXX: We might also want to let admins quarantine rather than delete attachments
	without a timelimit by passing `{ quarantine: true }` or similar.

Server admins may choose to mark some content as undeletable in their
implementation (e.g. for sticker packs and other content which should never be
deleted or quarantined.)

### Encrypted rooms

There is no way for server to know what events refer to which MXC URL, so we
leave it up to the client to DELETE any MXC URLs referred to by an event after
it expires or redacts its local copy of an event.

We rely on the fact that MXC URLs should not be reused between encrypted
events, as we expect each event to have different message keys to avoid
correlation.  As a result, it should be safe to assume each attachment has
only one referring event, and so when a client deems that the event should
be deleted, it is safe to also delete the attachment without breaking any
other events.

It seems reasonable to consider the special case of forwarding encrypted
attachments between rooms as an a 'copy by reference' - if the original
event gets deleted, the others should too.  If this isn't desired, then
the attachment should be reencrypted.

### Unencrypted rooms

It's common for MXC URLs to be shared between unencrypted events - e.g. reusing
sticker media, or when forwarding messages between rooms, etc.  In this instance,
the homeserver (not media server) should count the references to a given MXC URL
by events which refer to it.

If all events which refer to it have been purged or redacted, the HS should delete
the attachment - either by internally deleting the media, or if using an
external media repository, by calling the DELETE api upon it.

If a new event is received over federation which refers to a deleted
attachment, then the server should operate as if it has never heard of that
attachment; pulling it in over federation from whatever the source server is.
This will break if a remote server sends an event referring to a local
MXC URL which may have been deleted, so don't do that - clients on servers
should send MXC URLs which refer to their local server, not remote ones.

This means that if the local server chooses to expire the source event sooner
than a remote server does, the remote server might end up not being able to
sync the media from the local server and so display a broken attachment.
This feels fairly reasonable; if you don't want people to end up with 404s
on attachments, you shouldn't go deleting things.

In the scenario of (say) a redacted membership event, it's possible that the
refcount of an unwanted avatar might be greater than zero (due to the avatar
being referenced in multiple rooms), but the room admin may want to still
purge the content from their server. This can be achieved by DELETEing the
content independently from redacting the membership events.

## Tradeoffs

Assuming that encrypted events don't reuse attachments is controversial but
hopefully acceptable.  It does mean that stickers in encrypted rooms will end
up getting re-encrypted/decrypted every time, but is hopefully be acceptable
given the resulting improvement in privacy.

## Security considerations

Media repo implementations might want to use `srm` or a similar secure
deletion tool to scrub deleted data off disk.

If the same attachment is sent multiple times across encrypted events (even if
encrypted separately per event), it's worth noting that the size of the
encrypted attachment and associated traffic patterns will be an easy way to
identify attachment reuse (e.g. who's forwarding a sensitive file to each
other).
