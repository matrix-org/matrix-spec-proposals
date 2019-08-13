# Allowing 3PID Owners to Rebind

3PID
    noun
    A third-party identifier such as an email address or phone number, that
    can be tied to your Matrix ID in order for your contacts outside of
    Matrix to find you, typically with the help of an [identity
    server](https://matrix.org/docs/spec/identity_service/r0.2.1.html).

As part of the on-going privacy work, Matrix client applications are
attempting to make the concept of an identity server more clear to the user,
as well as allowing a user to interact with multiple identity servers while
they're logged in.

As part of facilitating this work, Matrix clients should be able to allow
users, while logged in, the ability to pick an identity server, see what
3PIDs they currently have bound to their Matrix ID, and bind/unbind as they
desire.

When implementating this functionality, a technicality in the spec was found
to prevent the ability to bind the same 3PID to multiple identity servers.
The line "The homeserver must check that the given email address is **not**
already associated with an account on this homeserver." appears under the
[POST
/_matrix/client/r0/account/3pid/email/requestToken](https://matrix.org/docs/spec/client_server/r0.5.0#post-matrix-client-r0-account-3pid-email-requesttoken)
line. The same goes for the [equivalent msisdn
endpoint](https://matrix.org/docs/spec/client_server/r0.5.0#post-matrix-client-r0-account-3pid-msisdn-requesttoken).

If a user binds their email address, through the homeserver to identity
server A, then switches to identity server B to try and do the same, the
homeserver will reject the second request as this email address has already
been bound. This is due to the homeserver attaching the email address user's
accounts whenever a bind is performed through them.

## Proposal

This proposal calls for allowing 3PID owners to rebind their 3PIDs using the
[POST
/_matrix/client/r0/account/3pid/email/requestToken](https://matrix.org/docs/spec/client_server/r0.5.0#post-matrix-client-r0-account-3pid-email-requesttoken) and [POST
/_matrix/client/r0/account/3pid/msisdn/requestToken](https://matrix.org/docs/spec/client_server/r0.5.0#post-matrix-client-r0-account-3pid-msisdn-requesttoken)
endpoints by extending the definition of what homeservers should check before rejecting a bind.

Homeservers should reject the binding of a 3PID if it already been bound,
**unless** the requesting user is the one who originally bound that 3PID. If
so, then they should be able to bind it again if they choose.

In doing so, it would allow users to bind their 3PIDs to multiple identity
servers, even if the homeserver has already been made aware of it.

## Tradeoffs

Identity servers will still let 3PIDs be rebound to another Matrix ID, while
a single homeserver won't let a 3PID transition between two users. If one
thinks about typical internet services however, you aren't allowed to simply
take an email address from another account even if you have control of it.

## Potential issues

Newer clients will expect homeservers to allow them to switch between
identity servers and bind/rebind emails as they please. If dealing with an
older homeserver, clients will receive an `HTTP 400 M_THREEPID_IN_USE`.
Clients should be prepared to understand that this may just mean they are
dealing with an old homeserver, versus the 3PID already being bound on this
homeserver by another user.

## Security considerations

None.

## Conclusion

By lifting the restriction of not allowing a user to bind a 3PID multiple
times, we unlock the ability to interact with multiple identity servers on
the same account. This not only allows the user to play around and gain a
better understanding of the purpose of an identity server, but it is also one
step towards further decentralisation in the identity server space.
