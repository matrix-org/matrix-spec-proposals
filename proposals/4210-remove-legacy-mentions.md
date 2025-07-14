# MSC4210: Remove legacy mentions
Matrix v1.7 introduced [intentional mentions], where events list users they
mention explicitly, instead of the recipients inferring mentions from the raw
message text. For backwards-compatibility reasons, messages without the new
`m.mentions` field still use the old plaintext matching for mentions.

[intentional mentions]: https://spec.matrix.org/v1.15/client-server-api/#user-and-room-mentions

Plaintext matching means it's very difficult for automated tools to tell which
users are mentioned in a message. This means that it's easy to spam mentions by
simply not using intentional mentions.

If intentional mentions are mandatory, automated tools could easily ban users
who send more than X mentions in a single message. There could even be a new
push rule condition to allow checking the number of mentioned users and skip
notifying entirely.

## Proposal
Support for legacy mentions is dropped. Specifically, the following deprecated
standard push rules are removed entirely:

* [`.m.rule.contains_display_name`](https://spec.matrix.org/v1.15/client-server-api/#_m_rule_contains_display_name)
* [`.m.rule.contains_user_name`](https://spec.matrix.org/v1.15/client-server-api/#_m_rule_contains_user_name)
* [`.m.rule.roomnotif`](https://spec.matrix.org/v1.15/client-server-api/#_m_rule_roomnotif)

Additionally, the `contains_display_name` [push rule condition] is deprecated.

[push rule condition]: https://spec.matrix.org/v1.15/client-server-api/#conditions-1

Including an empty `m.mentions` key is still required for clients that are
aware of intentional mentions, as omitting it would cause current clients to
assume messages are not using intentional mentions.

## Potential issues
Users using old clients (which don't send intentional mentions) will no longer
be able to mention users on up-to-date clients/servers.

Users using old clients (which don't support the new push rule conditions) will
also no longer be notified for mentions in case the client depends on the push
rules served by the server.

## Alternatives
The removal could be done in a new room version, such as when switching to
extensible events, as suggested by [MSC3952]. However, such a migration will
likely take much longer than clients implementing intentional mentions.
Additionally, the room upgrade UX is still an open issue, which means many
rooms simply don't upgrade. Therefore, making a slightly breaking change to
existing room versions seems like the better option.

[MSC3952]: https://github.com/matrix-org/matrix-spec-proposals/pull/3952

## Security considerations
This proposal doesn't add any features, so there are no new security
considerations.

## Unstable prefix
Not applicable, this proposal only removes features.

## Dependencies
None.
