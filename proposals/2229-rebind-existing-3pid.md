# Allowing 3PID Owners to Rebind

## Note: This MSC has been made obsolete by MSC2290.

MSC2290 provides two separate API endpoints, one for adding a 3PID to the
homeserver, and another for binding to an identity server. These new
endpoints will allow the homeserver to enforce rules on emails that already
exist on the homeserver, only when modifying homeserver email, while only
needing to forward requests when binding to an identity server. This removes
the problem MSC2229 is trying to solve, and it is thus made obsolete.

---

```
3PID
    noun

    A "third-party identifier" such as an email address or phone number, that
    can be tied to your Matrix ID in order for your contacts outside of
    Matrix to find you, typically with the help of an identity server.

Identity server
    noun

    A queryable server that holds mappings between 3PIDs and Matrix IDs.

Bind
    verb

    Create a mapping between a 3PID and a Matrix ID. Useful for people to
    find a user based on their existing third-party contact information.
```

As part of the on-going privacy work, Matrix client applications are
attempting to make the concept of an identity server clearer to the user, as
well as allowing a user to interact with multiple identity servers while
logged in. In facilitating this, Matrix clients should be able to allow
logged-in users the ability to pick an identity server, see what 3PIDs they
currently have bound to their Matrix ID, and bind/unbind addresses as they
desire.

When implementing this functionality, a technicality in the spec was found
to prevent certain abilities for a user. A user could not add a 3PID to their
homeserver before binding it to an identity server. It also prevents users
from binding the same 3PID to multiple identity servers. The line "The
homeserver must check that the given email address is **not** already
associated with an account on this homeserver." appears under the [POST
/_matrix/client/r0/account/3pid/email/requestToken](https://matrix.org/docs/spec/client_server/r0.5.0#post-matrix-client-r0-account-3pid-email-requesttoken)
endpoint description. The same goes for the [equivalent msisdn (phone)
endpoint](https://matrix.org/docs/spec/client_server/r0.5.0#post-matrix-client-r0-account-3pid-msisdn-requesttoken).

When a user adds an email to their account on their homeserver, they can
choose to bind that email to an identity server at the same time. This is
specified through a `bind` boolean. If the user first adds the 3PID with
`bind: false`, then decides they want to bind that 3PID to an identity server
to make themselves discoverable by it, by making another request with `bind:
true`, the homeserver will reject the second request, because this 3PID is
already tied to the user's account.

Similarly, when a user initially sends their 3PID with `bind: true` through a
homeserver to identity server A, the homeserver keeps a record and attaches
the address to the local account. If the user then switches to identity
server B to try and do the same, the homeserver will reject the second
request as this address has already been bound.

## Proposal

This proposal calls for allowing 3PID owners to rebind their 3PIDs using the
[`POST
/_matrix/client/r0/account/3pid/email/requestToken`](https://matrix.org/docs/spec/client_server/r0.5.0#post-matrix-client-r0-account-3pid-email-requesttoken)
and [`POST
/_matrix/client/r0/account/3pid/msisdn/requestToken`](https://matrix.org/docs/spec/client_server/r0.5.0#post-matrix-client-r0-account-3pid-msisdn-requesttoken)
endpoints by extending the definition of what homeservers should check before
rejecting a bind.

Homeservers should reject the binding of a 3PID if it has already been bound,
**unless** the requesting user is the one who originally bound that 3PID. If
so, then they should be able to bind it again and again if they so choose.

In doing so, users would be able to rebind their 3PIDs, even if the
homeserver has already been made aware of it.

## Tradeoffs

Identity servers will still let 3PIDs be rebound to another Matrix ID, while
a single homeserver won't let a 3PID transition between two users. If one
thinks about typical internet services however, you aren't allowed to simply
take an email address from another account even if you have control of it, so
this shouldn't be too unintuitive.

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
times, we allow the basic ability of publishing a 3PID after associating it
with an account, as well as allow users to interact with multiple identity
servers on the same account with the same 3PIDs. This not only allows the
user to play around and gain a better understanding of the purpose of an
identity server, but it is also one step towards further decentralisation in
the identity server space.
