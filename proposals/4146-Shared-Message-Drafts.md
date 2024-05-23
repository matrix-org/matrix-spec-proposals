# MSC4146: Shared Message Drafts

In Matrix, most clients support saving drafts, yet there is no way to share this data. This proposal outlines how such data could be shared.

## Proposal

There is often the need to draft out a message before sending it out, like wanting someone else to proofread it first, writing a message about an ongoing event, or a plethora of other scenarios where a message should just remain unsent until the time comes. However the experience is frustrating because you are limited only to one device, or even just one client on the same device. 

If you're ever in a situation where you want to send the message, edit it, or maybe even delete the draft, you cannot do so without first going back to the device you initially wrote it on. This means you cannot carry over a draft from your Phone to your Computer to have a more comfortable typing experience, or to see the text on a bigger screen, and is generally just an inconvenience.

My first idea would be to repurpose rooms, similar to how it's proposed for Profiles-As-Rooms or how Spaces are implemented. A new room type, `m.drafts` or `m.draft` would be added, allowing the client to differentiate this room from DMs, Spaces or Groups. A creation event could look something like this:

```json
{
  "content": {
    "creator": "@example:example.com",
    "room_version": "9",
    "type": "m.drafts"
  },
  ...
}
```

In said room, the client would then send normal `m.text` events, optionally with a formatted body, and would edit the message every ´n´ seconds or once the user stops typing. <span style="color: grey">(This is more of a UI/UX implementation detail though)</span>

Another thing that would be introduced would be a field that defines what room this is supposed to be for / In which room this draft was written

This could be done something like this, with a field to indicate what room it relates to:

```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "**test!!!**",
    "format": "org.matrix.custom.html",
    "formatted_body": "<strong>test!!!</strong>",
    "m.draft_in": "!ROOMID:example.com"
  }
}
```

## Potential issues


There are some issues with both approaches, notably I thought of:

- If the room is encrypted to allow privacy for these drafts, then the drafts would be unavailable to a client that has just authenticated but has not been verified yet, and as such cannot get the keys for the messages in the room and decrypt any of the drafts.
- Clients that do not support this MSC might display the drafts room normally, allowing the user to send arbitrary messages into the room, which might become messy. 
- If a client removes the `m.draft_in` as part of an edit the draft would no longer be associated with a room, causing confusion on the users' end as to where their draft went.


## Alternatives

An alternative way to implement this would be to instead add this data to account data, adding a field similar to what Element does with `io.element.recent_emoji`

The field could be named something like `m.room_drafts` or `m.drafts` (just like the room type from idea #1) and could contain something like this:

```json
{
  "type": "m.room_drafts",
  "content": {
    "!ROOMID:example.com": {
      "body": "**test!**",
      "format": "org.matrix.custom.html",
      "formatted_body": "<strong>test!!!</strong>"
    }
  }
}
```

This would cut the requirement for re-purposing a room (from what I understand).

However, it would also mean that you cannot encrypt the drafts, and as such these drafts would be leaked metadata that the server can read. This should be avoided as drafts can belong to an encrypted room, which you do not want leaked.

## Security considerations

By implementing this by repurposing an **encrypted** room you can avoid the drafts - and as such messages that might go into an encrypted room - being leaked to the homeserver. Encryption for a feature like this is a goal that should not be neglected.

## Unstable prefix

Proposed unstable prefixes for `m.drafts` and `m.draft_in` would be:

| prefix                        | description                       |
|-------------------------------|-----------------------------------|
| `org.matrix.msc4146.drafts`   | For the room type                 |
| `org.matrix.msc4146.draft_in` | For the room ID information on the events |

## Dependencies

Not Applicable
