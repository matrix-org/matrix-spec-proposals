# MSC4142: Remove unintentional intentional mentions in replies

Currently, the reply spec has a section called [Mentioning the replied to user](https://spec.matrix.org/v1.10/client-server-api/#mentioning-the-replied-to-user)
which says

> In order to notify users of the reply, it may be desirable to include the
> sender of the replied to event and any users mentioned in that event. See
> [user and room mentions](https://spec.matrix.org/v1.10/client-server-api/#user-and-room-mentions)
> for additional information.

The "*any users mentioned in that event*" part is particularly problematic, as
it effectively means all mentions will be propagated forever through a reply
chain, causing lots of unintentional pings.

The propagation was originally added to preserve the old reply fallback mention
behavior where explicit mentions in the replied-to message were be copied to
the reply fallback and therefore caused pings. However, the current spec copies
far more than just explicit pings from the replied-to message. Additionally, no
other chat application that I know of propagates mentions like that.

## Proposal
The proposed fix is to stop propagating mentions entirely. The `m.mentions`
object of replies should only contain explicit mentions in the new message,
plus the sender of the replied-to message. The mentions in the replied-to
message are ignored.

Clients are still free to add other mentions to the list as they see fit. For
example, a client could offer a button to mention all users in a reply chain.
This proposal simply changes the default behavior recommended in the spec.

## Potential issues
Users who have already got used to the new behavior may be surprised when they
don't get mentioned by reply chains.

## Alternatives
### Split `m.mentions`
To preserve the old reply fallback behavior, `m.mentions` could be split into
"explicit" and "implicit", so that replies copy explicit mentions into the
implicit list. Future replies would then only copy new explicit pings and
wouldn't cause an infinite chain.

Since other chat applications don't copy pings at all, having a weird feature
like that doesn't seem worth the additional complexity.

## Security considerations
This proposal doesn't touch anything security-sensitive.

## Unstable prefix
Not applicable, this proposal only changes how the existing `m.mentions` object
is filled for replies.

