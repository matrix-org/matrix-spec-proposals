# MSC3939: Account locking

Account locking is a common safety and security tool where server administrators
can prevent a user from usefully using their account. For example, too many failed
login attempts, escalation in moderation action, or out of band verification
needing to be completed.

Currently, Matrix only supports deactivating an account. This is a destructive
action which often leads to the account leaving all joined rooms, among other
details. With account locking, the effect of making the user unable to access
their account is achieved without destroying that same account - the account
can always be unlocked.

This proposal covers account locking, though leaves the specifics of use as an
implementation detail. APIs for administration of locking are also not provided.

## Proposal

When an account is locked, clients receive a `401 Unauthorized` error response
to most APIs with an `M_USER_LOCKED` error code and `soft_logout` set to `true`.
Excluded APIs are described below. We enable `soft_logout` to encourage clients
to make use of the [soft logout](https://spec.matrix.org/v1.9/client-server-api/#soft-logout)
semantics: keep encryption state, but otherwise render the account unusable. 401
is used to support legacy clients by giving the user a semantically meaningful
experience: they may need to try logging in again, and when they do they may get
a more useful error message about their account status, though their session data
may be deleted by the client if it doesn't recognize the error code. Soft logout
aims to prevent total destruction of this data, however.

Upon receiving the `M_USER_LOCKED` error, clients SHOULD retain session information
including encryption state and inform the user that their account has been locked.
Details about *why* the user's account is locked are not formally described by
this proposal, though future MSCs which cover informing users about actions taken
against their account should have such details. Clients may wish to make use of
[server contact discovery](https://spec.matrix.org/v1.10/client-server-api/#getwell-knownmatrixsupport)
in the meantime.

Clients SHOULD hide the normal UI from the user when informing them that their
account is locked, preventing general use of the account.

Clients SHOULD continue to `/sync` and make other API calls to more quickly detect
when the lock has been lifted.  However, clients should rate-limit their requests. If unlocked, the APIs will either return a different
error code or a normal 200 OK/successful response. For example, `/sync` will return
to working as though nothing ever happened. If the error code changes to
`M_UNKNOWN_TOKEN`, the client should delete local session data as it normally
would when seeing the error code (and use soft logout as it normally would). This
is typically expected if the server admin logged the user out or the user logged
themselves out.

Locked accounts are still permitted to access the following API endpoints:

* [`POST /logout`](https://spec.matrix.org/v1.9/client-server-api/#post_matrixclientv3logout)
* [`POST /logout/all`](https://spec.matrix.org/v1.9/client-server-api/#post_matrixclientv3logoutall)

When a user's account is locked, servers SHOULD NOT invalidate an account's access tokens in case the account becomes
unlocked: the user should be able to retain their sessions without having to log
back in. However, if a client requests a logout (using the above endpoints), the
associated access tokens should be invalidated as normal.

## Potential issues

This proposal does not communicate *why* a user's account is restricted. The human-readable `error`
field may contain some information, though anything comprehensive may not be surfaced to the user.
A future MSC is expected to build a system for both informing the user of the action taken against
their account and allow the user to appeal that action.

## Alternatives

[MSC3823](https://github.com/matrix-org/matrix-spec-proposals/pull/3823) covers
a similar concept, though is semantically different. See [matrix-org/glossary](https://github.com/matrix-org/glossary)
for details.

Another similar concept would be "shadow banning", though this only applies to
moderation use cases.

A 403 HTTP status code was considered instead of 401 with a `soft_logout`. A 403
would indicate that the given action is denied, but otherwise keep the user logged
in. This could wrongly indicate [suspension](https://github.com/matrix-org/matrix-spec-proposals/pull/3823),
confusing the user. Instead, we provide a semantically similar experience where
the user gets soft logged out on legacy clients, preserving encryption and related
session data (assuming the client also supports soft logout). This can result in
some loss of other session data however, like device-specific settings. Users may
also be differently confused when they try to log back in and get cryptic error
messages (indicating wrong username/password), however as mentioned above in the
Potential Issues section, communicating actions taken against an account is a
concern for a future MSC.

## Unstable prefix

Until this proposal is considered stable, implementations must use
`ORG_MATRIX_MSC3939_USER_LOCKED` instead of `M_USER_LOCKED`.
