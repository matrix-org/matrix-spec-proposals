# MSC2557: Clarifications on spoilers

Spoiler messages are described in [MSC2010](https://github.com/matrix-org/matrix-doc/pull/2010)
though the MSC is unclear if the fallback is required to be sent by clients.

## Proposal

The fallback for spoiler messages is optional, though recommended to be sent by clients. Clients
should make reasonable efforts to represent the spoiler in the `body` field of a message.

The recommended fallback format is unchanged.

Additionally, this proposal opens up spoilers to any HTML-supporting message types. Currently
this includes `m.text` (already included by MSC2010), `m.notice`, and `m.emote`.

## Potential issues

Clients could inadvertently spoil parts of a message by not representing the spoiler correctly
in the `body` of the message. The author believes this would quickly show up as a bug report
on the client due to the nature of spoilers.
