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
implementation detail. Self-serve locking APIs are additionally not provided.

## Proposal

When an account is locked, clients receive a `401 Unauthorized` error response
to most APIs with an `M_USER_LOCKED` error code and `soft_logout` set to `true`.
Excluded APIs are described below. We enable `soft_logout` to encourage clients
to make use of the [soft logout](https://spec.matrix.org/v1.9/client-server-api/#soft-logout)
semantics: keep encryption state, but otherwise render the account unusable. 401
is used to support legacy clients by giving the user semantically meaningful
experience: they may need to try logging in again, and when they do they may get
a more useful error message about their account status.

Clients MAY prevent actually logging the user out until the error code or response
changes. This is to allow the client to emit a few more requests after receiving
the error, as may be the case with a very active `/sync` loop. Once the error code
changes (but remains a 401 otherwise, regardless of soft logout), the client
should proceed with the logout. Similarly, if the response changes from an error
to a successful response, the client can assume the account has been unlocked and
return to normal operation without needing to get a new access token.

Upon receiving the `M_USER_LOCKED` error, clients SHOULD retain session information
including encryption state and inform the user that their account has been locked.
Details about *why* the user's account is locked are not formally described by
this proposal, though future MSCs which cover informing users about actions taken
against their account should have such details. Clients may wish to make use of
[server contact discovery](https://spec.matrix.org/unstable/client-server-api/#getwell-knownmatrixsupport)
in the meantime.

> *TODO*: MSC1929 was adopted into Matrix 1.10 - the link needs updating upon release.

Locked accounts are still permitted to access the following API endpoints:

* [`POST /logout`](https://spec.matrix.org/v1.9/client-server-api/#post_matrixclientv3logout)
* [`POST /logout/all`](https://spec.matrix.org/v1.9/client-server-api/#post_matrixclientv3logoutall)

Servers SHOULD NOT invalidate an account's access tokens in case the account becomes
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

Another option is to use 403 responses instead of 401 and `soft_logout`. We choose this
so that existing apps provide some feedback to the user without explicit support for
this MSC.

## Unstable prefix

Until this proposal is considered stable, implementations must use
`ORG_MATRIX_MSC3939_USER_LOCKED` instead of `M_USER_LOCKED`.
