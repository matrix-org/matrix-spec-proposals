# MSC3842: Power levels on message (extensible) events

Currently in Matrix anyone can send an event of any type in most rooms, though some rooms (like
announcement-only) rooms limit what some people can send. It's additionally been desirable to
be able to ban images or other rich media in a room which might be bridged to a less capable
platform, though this use-case is less common.

This proposal aims to try and figure out power levels for events from the perspective of
[MSC1767 Extensible Events](https://github.com/matrix-org/matrix-spec-proposals/pull/1767)
where the client might end up rendering the event as a fallback rather than as the primary,
easily-blocked, type. Similar considerations can be made for when the event type is hidden
from the server, like with encrypted events.

## Proposal

TBD. I think we can rely on client-side enforcement when the event contains a mixed type? Power
levels would no longer be used to enforce conversation norms and instead be used to encourage
use cases like announcement rooms.

## Potential issues

TBD

## Alternatives

TBD

## Security considerations

TBD

## Unstable prefix

Not yet applicable.

## Dependencies

Soft dependencies:

* [MSC1767: Extensible events](https://github.com/matrix-org/matrix-spec-proposals/pull/1767)
