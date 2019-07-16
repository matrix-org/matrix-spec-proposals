# Add an Error Code for Signaling a Deactivated User

Currently, when a user attempts to log in, they will receive an `M_FORBIDDEN`
errcode if their password is incorrect. However, if the user's account is
deactivated, they will also receive an `M_FORBIDDEN`, leaving clients in a
state where they are unable to inform the user that the reason they cannot
log in is that their account has been deactivated. This leads to confusion
and password resetting with ultimately results in unnecessary support
requests.

## Proposal

This proposal asks to create a new errcode, `M_USER_DEACTIVATED`, that can be
returned whenever an action is attempted that requires an activited user, but
the authenticating user is deactivated. The recommended HTTP code to return
alongside is `403`.

## Tradeoffs

The alternative is to continue returning an `M_FORBIDDEN`, but send back a
different errmsg. This is undesirable as it requires clients to pattern match
on a long phrase that could be minutely changed at any time, breaking
everything.

## Potential issues

None

## Security considerations

This would allow users to be able to detect if their account had been
deactivated. This is probably something we'd like to allow though.

## Conclusion

Adding `M_USER_DEACTIVATED` would better inform clients about the state of a
user's account, and lead to less confusion when they cannot log in.
