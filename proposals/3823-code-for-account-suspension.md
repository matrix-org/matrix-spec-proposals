# MSC3823: Account Suspension

Unlike [account locking](https://spec.matrix.org/v1.12/client-server-api/#account-locking), suspension
allows the user to have a (largely) readonly view of their account. Homeserver administrators and
moderators may use this functionality to temporarily deactivate an account, or place conditions on
the account's experience. Critically, like locking, account suspension is reversible, unlike the
deactivation mechanism currently available in Matrix - a destructive, irreversible, action.

This proposal introduces a concept of suspension to complement locking for server admins to use. Locking
is typically more used in narrow scenarios, where the server admin wants to prevent the account from
engaging any further. An example of this may be too many failed password attempts. Suspension is more
general purpose to create a barrier to further action - a "something weird is going on -> suspend"
kind of button.

The error code introduced by this proposal is accompanied by guidelines on how servers can implement
suspension. APIs to invoke or clear suspension are not introduced, and left as an implementation detail.
These will typically be done through an administrator-only API.

## Proposal

When an account is suspended, any [Client-Server API](https://spec.matrix.org/v1.10/client-server-api/)
endpoint MAY return a 403 HTTP status code with `errcode` of `M_USER_SUSPENDED`. This indicates to
the user that the associated action is unavailable.

Clients should note that for more general endpoints, like `/send/:eventType`, suspension MAY only be
applied to a subset of request parameters. For example, a user may be allowed to *redact* events but
not send messages.

The specific list of permitted actions during suspension is left as a deliberate implementation
detail, however a server SHOULD permit the user to:

* Log in/create additional sessions (which should also behave as suspended).
* See and receive messages, particularly via `/sync` and `/messages`.
* [Verify their other devices](https://spec.matrix.org/v1.10/client-server-api/#device-verification)
  and write associated [cross-signing data](https://spec.matrix.org/v1.10/client-server-api/#cross-signing).
* [Populate their key backup](https://spec.matrix.org/v1.10/client-server-api/#server-side-key-backups).
* Leave rooms & reject invites.
* Redacting their own events.
* Log out/delete any device of theirs, including the current session.
* Deactivate their account, potentially with a deliberate time delay to discourage making a new
  account right away.
* Change or add [admin contacts](https://spec.matrix.org/v1.10/client-server-api/#adding-account-administrative-contact-information),
  but not remove. Servers are recommended to only permit this if they keep a changelog on contact information
  to prevent misuse.

The recommendation for users to continue receiving/reading messages is largely so the administrator
can maintain contact with the user, where applicable. Future MSCs may improve upon the admin<>user
communication, and account locking may also be used to prevent access to messages.

The suggested set of explicitly forbidden actions is:

* Joining or knocking on rooms, including accepting invites.
* Sending messages.
* Sending invites.
* Changing profile data (display name and avatar).
* Redacting other users' events (when a moderator/admin of a room, for example).

## Potential issues

This proposal does not communicate *why* a user's account is restricted. The human-readable `error`
field may contain some information, though anything comprehensive may not be surfaced to the user.
A future MSC is expected to build a system for both informing the user of the action taken against
their account and allow the user to appeal that action.

## Alternatives

No significant alternatives are plausible. `M_USER_DEACTIVATED` could be expanded with a `permanent`
flag, though ideally each error code should provide meaning on its own.

The related concept of locking, as discussed in places like [MSC3939](https://github.com/matrix-org/matrix-spec-proposals/pull/3939)
and [matrix-org/glossary](https://github.com/matrix-org/glossary), is semantically different from
suspension. Suspension has the key difference that the user is *not* logged out of their client,
typically used by safety teams, while locking *does* log the user out and would primarily be used by
security teams. A future MSC may combine or split the two related error codes into a descriptive set
of capabilities the user can perform.

## Unstable prefixes

Until this proposal is considered stable, implementations must use
`ORG.MATRIX.MSC3823.USER_SUSPENDED` instead of `M_USER_SUSPENDED`.
