# MSC4086: Reference counting media

For various reasons, we must delete media items from the media repository once the events are redacted. For unencrypted events, the homeserver already has everything it needs to perform this deletion, and this spec outlines the conditions under which this deletion will happen. For encrypted events, we add a new way of tracking these.

## Proposal

The homeserver's media repository will maintain a many-many association between events and media ids. For events that are redacted, the association will be removed. For m.replaces events, the event that was replaced will have its association removed. If a media item is not associated with any event on the server, the server must delete that media item.

For newly uploaded media items, the sender must associate it with an event within a fixed amount of time (configurable by the server owner, suggested to be 1 hour), otherwise the server will delete it. In order to associate the event with media, the sender may include it in the standard url field of events such as m.image and m.sticker, or include a well formed mxc url in the message body. Additionally, room state events and account data events will also be associated. Any events received over federation will have their association recorded accordingly, if the media is in the homeserver's media repository.

For encrypted events, the sender must include an additional unencrypted field in the event, associated_media, which is an array of media ids.

All endpoints will follow either the existing apis, or #3916

## Potential issues

* The homeserver knows the association of encrypted media and encrypted events. This is an equivalent issue in #3911
* If all users on a homeserver left a room, the homeserver will no longer get redaction events, and those medias will remain even if the event is redacted.  This is an equivalent issue in #3911

## Alternatives

* #3911

* As an alternative for privacy concerns, it may be advantageous to restrict this MSC to unencrypted events only

## Security considerations

See potential issues.

## Unstable prefix

arc_reference_counting

## Dependencies

#3916 is a soft dependency

