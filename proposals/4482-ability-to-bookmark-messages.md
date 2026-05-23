# MSC4482: Ability to Bookmark Messages

We often find ourselves wanting to bookmark messages to look them up at a later point, be it phone numbers, addresses or something else.
Due to that we started thinking about how to implemented it.
We decided to implement Bookmarks via a new room type in which, when you bookmark a message a extensible message is sent into that room which points to the bookmarked message and the room it has been sent in.

By adding bookmarks users gain the ability to find important messages again within a room, or bookmark a area in a room that they would like to reread. 
This feature can be extended for example to allow clients to add reminders after a specified time and lots more!


## Proposal

### Event structure

```json5
{
  "type": "m.bookmark",
  "content": {
    "m.text": [
      {
        "body": "You bookmarked <message_link> in <roomid>"
      }
    ],
    "m.pointer": {
      "roomId": "<roomId>",
      "eventId": "<eventId>"
    }
  } 
}
```


### New room type : `m.bookmark`

## Client implementation recommendations 

## General

If the client support the `m.bookmark` room type, it should'nt be displayed as a normal room in the regular room list. Instead the client could display bookmarks in dedicated sections of the client. 
The client should ensure that only one `m.bookmark` room is existing at once.
If there are multiple `m.bookmark` rooms, we leave this as an implementation detail.

## Room creation

The room should be created on first bookmark creation.
The client should check if a `m.bookmark` room already exists before creating a new one.



## Potential issues

- Room upgrades: could lead to bookmarks going missing if not handled properly. 
- Multiple people: having multiple people in a room will lead to unintended consequences. 


## Alternatives

- One could use a room full of matrix.to links.
- Bookmarks could be implemented by duplicating the original message -> we didn't do this for 
    - respect redactions
    - be lean
- We didn't wanted to do "personal pins" through room related events because : 
    - we want to keep them private
    - have an easy entry point to find all your bookmarks
- Using (room) account data was also irrelevant because fetching all the data at once could be problematic

## Security considerations

We don't see any security issues, since pointers do not contain other data

## Unstable prefix

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
