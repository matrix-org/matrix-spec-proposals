# MSC4482: Ability to Bookmark Messages

We often find ourselves wanting to bookmark messages to look them up at a later point, be it phone numbers, addresses or something else.
Due to that we started thinking about how to implemented it.
We decided to implement Bookmarks via a new room type in which, when you bookmark a message a extensible message is sent into that room which points to the bookmarked message and the room it has been sent in.

By adding bookmarks users gain the ability to find important messages again within a room, or bookmark a area in a room that they would like to reread. 
This feature can be extended for example to allow clients to add reminders after a specified time and lots more!


## Proposal

This proposal requires 2 additions to the spec : one new room type and one new event that would be sent in this new kind of room.
This proposal leverages extensible timeline events and the fact that unknown room types are treated as regular rooms to provide a nice retrocompatibility experience with clients that do not implements this feature. 

### New room type

This MSC introduces a new room type called `m.bookmarks`.
This kind of room SHOULD only hold some `m.bookmark` events defined below. 

### Event structure

This MSC introduces a new kind of event which is a timeline event that uses extensible events blocks.
It introduces a new `m.pointer` block that references a particular event sitting in a given room.
The pointer is provided as is: it may not be "valid" (i.e. the user does not have access / permission to view the referenced event). However, in case the bookmarked / referenced event has a `m.replace` relation, the sending client should use the original event_id of the relation chain. This assumes that a `m.bookmark` event references an event and all its "versions", not a particular version of this event. 

```json5
{
  "type": "m.bookmark",
  "content": {
    "m.text": [
      {
        "body": "You bookmarked an image from Alice in Matrix Dev"
      },
      {
        "body": "You bookmarked an <a href='matrix:roomid/$ROOM_ID/e/$EVENT_ID?via=$SERVER_NAME'>image</a> from <a href='matrix:u/alice:example.org'>Alice</a> in Matrix Dev",
        "mimetype": "text/html"
      }
    ],
    "m.pointer": {
      "room_id": "$ROOM_ID",
      "event_id": "$EVENT_ID",
      "via": ["$SERVER_NAME"]
    }
}
```

The fallback text block of this event should contain at least the [Matrix URI](https://spec.matrix.org/v1.18/appendices/#matrix-uri-scheme) pointing to the bookmarked event. The rest of the body of this text block is left as an implementation detail of each client. 

## Client implementation recommendations 

### General

If the client support the `m.bookmarks` room type, it shouldn't be displayed as a normal room in the regular room list. Instead the client could display bookmarks in dedicated sections of the client. 
The client should ensure that only one `m.bookmarks` room is existing at once. 
To enforce this, the client MUST use the `m.bookmarks_room` global account data event that contains a single `active_bookmarks_room_id` parameter with the Room ID of the bookmarks room. 

### Room creation

The room should be created upon first bookmark creation, and only if the global account data `m.bookmarks_room` event isn't set. When creating the room, the client must set the
`m.bookmarks_room` account data event with the newly defined room ID.

### Unbookmarking a message

A message that is not bookmarked is a message that doesn't have a `m.bookmark` event referencing it in the `m.bookmarks` room. Thus, redacting a `m.bookmark` event is equivalent to not having its referenced event bookmarked.

### Bookmark unicity

The client should ensure that only one bookmark at the time exists for a given event and its versions. This assures that each message has a clean binary state: either bookmarked or not. This may be achieved by redacting the bookmark event. A message may be bookmarked again after being unbookmarked, by creating a new `m.bookmark` event referencing it.

### Original message redaction / edition

A bookmarked message may be redacted or edited by its sender. It is up to the client to respect the redaction of the referenced message, or resolve its latest version.

### Bookmark event editions

As all timeline events, the `m.bookmark` event may be replaced / edited through a `m.replace` relation. The client must use the latest version of the bookmark event, notably the referenced event of the `m.pointer` block.

## Potential issues

- Room upgrades: could lead to bookmarks going missing if not handled properly.
- Multiple people: having multiple people in a room will lead to unintended consequences. 
- Bookmark synchronization: timeline events do not have the same deliverability guaranties than state events. Each client has the responsibility of pulling the potential bookmark changes from the server.  

## Alternatives

### Event duplication

One could achieve bookmarking by transfering itself some events in a different "bookmarks" room.
This means duplicating the original event which : 
- does not respect the redaction of the original event
- isn't efficient
- does not provide a convenient UI integration

### Manual "pointers"

Creating Matrix event "pointers" can already be achieved by using `matrix.to` links of `matrix://` URIs sent as plain text messages in some room.
While solving the redaction and efficiency problems, this isn't still convenient since this is hardly integrable in a client UI.

### Personal pins

One way to approach bookmarking Matrix events could be through "personal pins", by storing bookmarks per-room, in a Whatsapp "starred messages" fashion.
We chose to store these bookmarks outside of the room for multiple reasons:
- These bookmarks should be private. This leaves only the room account data structure to store personal data associated to this room. We chose not to do this to avoid bloating the account data that does not have a pagination mechanism as timeline events have.
- We seek retrocompatibility with clients may not implement this MSC. Sending extensible events in a room should provide a nice (ordered) view of all saved bookmarks, whereas account data is downloaded but never displayed. 
- Having all your bookmarks in the same place is handier to provide a global view of all these bookmarks.

### Comparison to existing MSCs

[MSC4438](msc.re/4438) also tries to implement bookmarks in Matrix, but in that MSC it was decided to use account data instead. We see several
possible issues with this way of implementing bookmarks:
- Account data is fetched in one go, so over time, bookmarks pile up in the account data. The bookmarks are loaded even
if not needed.
- Using account data doesnt give Clients, that haven't implemented it, a fallback option, which still allows the user to
have the option to access their bookmarks.

We also decided that we want to leverage existing features in Matrix to our advantage, to make it as light and
extensible as possible.

The above mentioned problems also come up in other MSCs that tried to implement this or similar features, for example
[MSC2772](msc.re/2772).


## Security considerations

We don't see any security issues, since the new room and event types introduced only reference existing Matrix events.

## Unstable prefix

**This Part will be updated, when implementation starts**

*If a proposal is implemented before it is included in the spec, then implementers must ensure that the
implementation is compatible with the final version that lands in the spec. This generally means that
experimental implementations should use `/unstable` endpoints, and use vendor prefixes where necessary.
For more information, see [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324). This section
should be used to document things such as what endpoints and names are being used while the feature is
in development, the name of the unstable feature flag to use to detect support for the feature, or what
migration steps are needed to switch to newer versions of the proposal.*

## Dependencies

This MSC builds on MSC4474 (which at the time of writing have not yet been accepted
into the spec).
