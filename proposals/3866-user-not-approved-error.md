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

An error with the code `M_USER_AWAITING_APPROVAL` must include an
`approval_notice_medium` field, which indicates to the user how the homeserver
will let them know of their account's approval. This proposal specifies the
following values:

* `m.email`: the user is made aware of their account's approval by email to an
  address they provided during registration.
* `m.none`: the user is not made aware of their account approval in an automated
  way that's managed by the homeserver. This can mean that a server
  administrator will reach out to them out of bounds (using any relevant
  medium), or that they should wait some time and try logging in again to see if
  their account has been approved.

### Registration

When a user successfully registers on a homeserver that is configured so that
new accounts must be approved by an administrator, the final `POST
/_matrix/client/v3/register` request is responded to with a `403 Forbidden`
response that includes the `M_USER_AWAITING_APPROVAL` error code. For example:

```json
{
    "errcode": "M_USER_AWAITING_APPROVAL",
    "error": "This account needs to be approved by an administrator before it can be used.",
    "approval_notice_medium": "m.email"
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
    "error": "This account is pending approval by a server administrator. Please try again later.",
    "approval_notice_medium": "m.email"
}
```

This error can be returned in any login request, as long as the homeserver is
confident that the user trying to log in is pending approval - as opposed to
registration requests where only the last one can return such an error, in order
to ensure the registration completes.

This error can also be returned by login requests performed in the context of a
user's first authentication through an SSO provider. Since this does not involve
the user's client performing a `/register` request, this means the homeserver
must track approval of users when they are registered as part of the SSO flow.

Once an account is approved, homeserver must allow the user to log in (unless
the account becomes unavailable for unrelated reasons, e.g. by getting
deactivated).

## Potential issues

### Informing the user about this feature before they register

This MSC does not include a way to communicate to clients early on whether the
homeserver requires new accounts to be approved by an administrator, which can
make the registration experience frustrating (because the user might not be
expecting to need to wait before using their account). The author of this
proposal tried and failed to figure out a good way to expose this information:

* the capabilities endpoint is authenticated and therefore does not work in this
  context
* the `/versions` endpoint does not feel like the correct place to expose
  information about locally-enabled features
* adding a boolean to initial `/register` requests feels out of place, and could
  potentially be non-trivial to implement in a way that doesn't get in the way
  of User-Interactive Authentication

### Informing the user about their account's approval

By design, Matrix does not force users to provide way to contact them outside of
Matrix (e.g. via email) when registering. This means the homeserver might not
have a way to let the user know once their account has been approved by their
administrator. In this case, homeservers should use the `m.none` value for the
`approval_notice_medium` field in error responses. The expectation is then that
a server administrator reaches out to the user out of bounds, or that the user
waits some time before manually trying to log in again.

## Security considerations

It shouldn't be necessary to implement the `M_USER_AWAITING_APPROVAL` error code
on other endpoints than `/register` and `/login`. This is because other
endpoints are either unauthenticated (in which case we don't care about whether
the user is approved) or authenticated via an access token (in which case the
fact that the user has an access token either means they've managed to log in
(meaning they've been approved) or a server administrator generated one for
them).

## Unstable prefix

During development, the following unstable identifiers must be used:

| Stable identifier          | Unstable identifier                         |
|----------------------------|---------------------------------------------|
| `M_USER_AWAITING_APPROVAL` | `ORG.MATRIX.MSC3866_USER_AWAITING_APPROVAL` |
| `m.email`                  | `org.matrix.msc3866.email`                  |
| `m.none`                   | `org.matrix.msc3866.none`                   |
