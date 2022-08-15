# MSC3866: `M_USER_AWAITING_APPROVAL` error code

Over the past few years, there has been some demand for the ability to let
administrators of homeservers approve any new user created on their homeserver
before their account can be used. This allows for better control upon
registration and a potential option for mitigating abuse as an alternative to
disabling registration on a homeserver or forcing new users to fill in
additional details such as an email address.

## Proposal

This document proposes the addition of a new `M_USER_AWAITING_APPROVAL` error
code to the Matrix specification. This error code can be returned in two
scenarios: registration and login.

This proposal does not describe a way for the homeserver to alert an
administrator about new accounts that are waiting to be reviewed, or a way for
administrators to approve or deny an account. This is left as an implementation
detail, as different homeserver implementations have different ways for
administrators to interact with them (e.g. Synapse's admin API vs Conduit's
admin room).

### Registration

When a user successfully registers on a homeserver that is configured so that
new accounts must be approved by an administrator, the final `POST
/_matrix/client/v3/register` request is responded to with a `403 Forbidden`
response that includes the `M_USER_AWAITING_APPROVAL` error code. For example:

```json
{
    "errcode": "M_USER_AWAITING_APPROVAL",
    "error": "This account needs to be approved by an administrator before it can be used."
}
```

### Login

When a user whose account is still pending approval by a server administrator
attempts to log in, `POST /_matrix/client/v3/login` requests are responded to
with a `403 Forbidden` response that includes the `M_USER_AWAITING_APPROVAL`
error code. For example:

```json
{
    "errcode": "M_USER_AWAITING_APPROVAL",
    "error": "This account is pending approval by a server administrator. Please try again later."
}
```

This error can be returned in any login request, as long as the homeserver is
confident that the user trying to log in is pending approval - as opposed to
registration requests where only the last one can return such an error, in order
to ensure the registration completes.

Once an account is approved, homeserver must allow the user to log in (unless
the account becomes unavailable for unrelated reasons, e.g. by getting
deactivated).

## Potential issues

This MSC does not include a way to communicate to clients early on whether the
homeserver requires new accounts to be approved by an administrator, which can
make the registration experience frustrating (because the user might not be
expecting to need to wait before using your account).

It is also unclear how to inform a user about their account being approved. This
can probably be done on a best-effort basis using contact information (e.g.
email address) provided by the user during the registration process, if any.

## Alternatives

The homeserver could include a boolean indicating whether new accounts require
approval in the response to an initial `/register` request, but it feels out of
place and possibly non-trivial to implement in a way that doesn't get in the way
of User-Interactive Authentication.

## Security considerations

It shouldn't be necessary to implement the `M_USER_AWAITING_APPROVAL` error code
on other endpoints than `/register` and `/login`. This is because other
endpoints are either unauthenticated (in which case we don't care about whether
the user is approved) or authenticated via an access token (in which case the
fact that the user has an access token either means they've managed to log in
(meaning they've been approved) or a server administrator generated one for
them).

## Unstable prefix

During development, `ORG.MATRIX.MSC3866_USER_AWAITING_APPROVAL` must be used
instead of `M_USER_AWAITING_APPROVAL`.
