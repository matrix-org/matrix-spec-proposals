# Add an Error Code for Signaling a Deactivated User

Currently, when a user attempts to log in, they will receive an `M_FORBIDDEN`
errcode if their password is incorrect. However, if the user's account is
deactivated, they will also receive an `M_FORBIDDEN`, leaving clients in a
state where they are unable to inform the user that the reason they cannot
log in is that their account has been deactivated. This leads to confusion
and password resetting with ultimately results in unnecessary support
requests.

## Proposal

This proposal asks to create a new errcode, `M_USER_DEACTIVATED`, that MAY be
returned whenever an action is attempted that requires an activited user, but
the authenticating user is deactivated. The HTTP code to return alongside is
`403`.

## Tradeoffs

The alternative is to continue returning an `M_FORBIDDEN`, but send back a
different errmsg. This is undesirable as clients are supposed to treat the
message as an opaque string, and should not be performing any
pattern-matching on it.

## Potential issues

None

## Security considerations

While the existence of a user was already public knowledge (one can check if
the User ID is available through
[/_matrix/client/r0/register/available](https://matrix.org/docs/spec/client_server/r0.5.0#get-matrix-client-r0-register-available),
this proposal would allow any user to be able to detect if a registered
account has been deactivated.

## Conclusion

Adding `M_USER_DEACTIVATED` would better inform clients about the state of a
user's account, and lead to less confusion when they cannot log in.
