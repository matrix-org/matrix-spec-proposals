# MSC4210: Remove legacy mentions
Matrix v1.7 introduced intentional mentions, where events list users they
mention explicitly, instead of the recipients inferring mentions from the raw
message text. For backwards-compatibility reasons, messages without the new
`m.mentions` field still use the old plaintext matching for mentions.

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

* `.m.rule.contains_display_name`
* `.m.rule.contains_user_name`
* `.m.rule.roomnotif`

Additionally, the `contains_display_name` push rule condition is deprecated.

## Potential issues
Users using old clients will no longer be able to mention users on up-to-date
clients/servers.

## Alternatives

## Security considerations
This proposal doesn't add any features, so there are no new security
considerations.

## Unstable prefix
Not applicable, this proposal only removes features.

## Dependencies
None.
