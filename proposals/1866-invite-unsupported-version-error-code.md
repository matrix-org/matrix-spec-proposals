# MSC 1866 - Unsupported Room Version Error Code for Invites

It is currently unspecified what error code should be relayed to clients when
they attempt to invite a user on a remote server that does not support the room
version.

The proposal is to reuse the `M_UNSUPPORTED_ROOM_VERSION` error code that is
currently returned by the create room API.

Strictly, the error returned by the create room API would mean the local server
didn't support the room version, while for the invite API it would mean the
remote server didn't. However, there is sufficient overlap that it makes sense
to reuse the same error code and rely on the context to differentiate the two
cases.
