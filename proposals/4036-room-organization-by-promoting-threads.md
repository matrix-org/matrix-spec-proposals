# MSC436: Room organization by promoting threads

Sometimes, having a discussion in a busy room can be difficult.
People are often simply replying with a message event which is technically not related (`m.relates_to`) using replies (`m.in_reply_to`) or threads (`m.thread`) with the previous messages of the conversation making separation of one conversation from others difficult.

The functionality of threads is often unused,
considerably because simply typing in a reply is just simpler/faster and the lack of support by clients although a fallback mechanism exists.

This MSC solely proposes client-side behavior.

## Proposal

Standardize a room state `m.promote_threads` (`dev.coffeeco.MSC4036.promote_threads` for non-finalized implementations of this MSC) with a Boolean value or an object, defaulting to `false`.

The value SHOULD NOT be set to an object
but clients MUST consider an object as implicating a value of `true` (possibly with additional behavior changes)
for the purpose of forwards compatibility.

If set to `false` or unset,
clients behavior MAY NOT alter their behavior.

If set to `true` or some object,
clients should alter their user experience to guide the user to reply using threads with the following proposed changes:

- On messages without a relation (`m.relates_to`),
functionality to reply in a thread may be promoted,
e.g. by displaying an enlarged button,
making it more accessible than the `m.in_reply_to` functionality.

- In the scope of the room, outside of a thread,
clients may chose to minimize the message input functionality
or hide it behind a button (e.g. "Start new conversation")
to indicate that a room prefers replies in threads.

- For messages which are others are related to in a `m.thread`-relation,
clients may choose to show a selection of the messages related to that message as a preview. 

## Potential issues

This MSC may be considered to have a too specific way how clients work and behave in mind.
Hence, this MSC only proposes behavior.

A potential issue may be that clients without support for threads or not following the proposed behavior will continue to reply as before,
which may cause conversations in threads (as promoted by this MSC) to disappear faster due to new messages and replies of conversations not using threads.
This may create difficulties with translations.

Also, it may be considered to add the possibility to select specific behavior changes specified above.
However, this might cause a too broad variation of the user interface, making it harder to understand and less predictable.

## Alternatives

Instead of `m.promote_threads` being a value of `true` or `false`,
it may be considerable that the value also may be an object.
If the value is an object, it must be treated equally with a value of `true` with the following additions:
The object may contain a strings,
for example to specify the label of the button to access the message input box outside the scope of a thread
(e.g. "Ask a new question", "Open a new issue").

[MSC3088: room-subtyping](https://github.com/matrix-org/matrix-spec-proposals/blob/travis/msc/mutable-subtypes/proposals/3088-room-subtyping.md)
proposes specification for room purposes,
e.g. data-driven spaces or DM rooms.
The proposed behavior of this MSC could be applied to a further room purpose, a `m.discussions` (or `dev.coffeeco.MSC4036.discussions`).
E.g. like:
```json
{
  "type": "m.room.purpose",
  "state_key": "m.discussions",
  "content": {
    "m.promote_threads": true
  }
}
```

## Security considerations

Not applicable

## Unstable prefix

For the proposed `m.promote_threads` state key,
the unstable `dev.coffeeco.MSC4036.promote_threads` shall be used.

## Dependencies

Potentially [MSC3088: room-subtyping](https://github.com/matrix-org/matrix-spec-proposals/blob/travis/msc/mutable-subtypes/proposals/3088-room-subtyping.md),
if seen as an extension of it as depicted in the alternatives section.
