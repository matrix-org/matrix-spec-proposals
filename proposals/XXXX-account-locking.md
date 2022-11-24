# MSCXXXX: Account locking

There are legitimate cases where server administrators might want the ability to
temporarily lock users out of their account. For example, server administrators
might require users to go through a regular, out-of-bounds verification check in
order to keep using their account, and temporarily lock a user out of their
account if they do not complete this check in time.

At the time of writing this proposal, the only option for a server administrator
to prevent a user from accessing their account is to deactivate it. However,
this is a pretty destructive operation. Ideally, a locked account could be
unlocked without any visible impact on the account itself (joined rooms,
associated 3PIDs, etc).

Note that
[MSC3823](https://github.com/matrix-org/matrix-spec-proposals/pull/3823)
addresses a similar concept coming from a moderation perspective. However,
locking and suspending an account are semantically different.

## Proposal

A new `M_USER_LOCKED` is introduced, which is communicated to clients in `403 Forbidden` HTTP responses.

When an account is locked:

* homeservers must respond to any authenticated request from the user with
  `M_USER_LOCKED`, _except_ for requests to `/logout` and `/logout/all`.
* homeservers must not automatically invalidate existing access tokens for the
  user.
* clients should keep data that has already been locally persisted, unless the
  user manually logs out.

When an account is unlocked, clients and the homeserver can start interacting
again as if nothing happened, similarly to when a client recovers after loss of
connection.

## Alternatives

This proposal could be merged with
[MSC3823](https://github.com/matrix-org/matrix-spec-proposals/pull/3823), which
describes a similar concept coming from a content moderation perspective.
However, locking and suspending an account are semantically different enough
that the author of this proposal thinks that it makes sense for those two cases
to be described differently in the API.

Another option for merging this proposal with MSC3823 would be adding a
`suspended` boolean property and an optional `href` string property (which would
be required if `suspended` is `true`) to errors bearing the `M_USER_LOCKED`
error code. Opinions are welcome on whether this is a better solution than using
two distincts error codes.

## Unstable prefix

Until this proposal is accepted, implementations must use
`ORG_MATRIX_MSCXXXX_USER_LOCKED` instead of `M_USER_LOCKED`.
