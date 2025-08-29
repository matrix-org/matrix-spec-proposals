# MSC0000: Template for new MSCs

This MSC is to add a new `m.room.language` state event. This would allow users to set a desired
language preference for each room which would aid in client feature development.

Features such as message search require a tokenizer which depend on the language being toknized.
Enabling per-room language setting would allow a multi-lingual user to have search working in 
different languages across rooms.

Accessibility features such as screen readers would also benifit from knowing what language they
are reading.

## Proposal

Add a new `m.room.language` state event. This would hold a single field `"language": <language>`, 
similar to the `m.room.name`, using the 
[IETF BCP 47](https://developer.mozilla.org/en-US/docs/Glossary/BCP_47_language_tag).

## Potential issues

Potential issues with this approach are that they do not allow for ranked choice. For example,
one may know French and Spanish but not English. If said person sets a room to French and the 
client only supports Spanish and English, then the client could default to English when for the
user, Spanish would've been the better choice.

## Alternatives

Rather than adding a new state event, this could be a client setting. However, the drawbacks of
this are that each member of a room would have to ensure they have the right language setting. 

## Security considerations

There are no security concerns. 
