# Separate Endpoints for Binding Threepids

On the Client Server API there is currently a single endpoint for binding a
threepid (an email or a phone number): [POST
/account/3pid](https://matrix.org/docs/spec/client_server/unstable#post-matrix-client-r0-account-3pid).
Depending on whether the `bind` flag is `true` or `false`, the threepid will
be bound to either a user's account on the homeserver, or both the homeserver
and an identity server.

For context a threepid can be bound to an identity server to allow other users to find
their Matrix ID using their email address or phone number. A threepid can
also be bound to a user's account on the homeserver. This allows the 
threepid to be used for message notifications, login, password reset, and
other important functions.

Typically, when using the `/account/3pid` endpoint,
the identity server handles the verification -- either by sending an email to
an email address, or a SMS message to a phone number. Once completed, the
homeserver will check with the identity server that verification had indeed
happened, and if so, the threepid would be bound (again, either to the
homeserver, or the homeserver and identity server simultaneously).

Now, consider the fact that the identity server used in this process is
provided by the user, using the endpoint's `id_server` parameter. If the user were
to supply a malicious identity server that would immediately answer "yes" to
any threepid validation, then the user could add any threepid to their
account on the homeserver (which is likely not something homeserver admins want).

To be clear, this is not a long-standing security issue. It is not a problem
in any released version of Synapse, as Synapse keeps a list of "trusted
identity servers" that acts a whitelist for what identity servers a user can
specify.

Synapse is soon to lose this whitelist however, as part of lessening the
reliance of homeservers on identity servers. This cannot be done while the
homeserver is still trusting an identity server for validation of threepids.
If the endpoints are split, the homeserver will handle the validation of
threepids being added to user accounts, and identity servers will validate
threepids being added to their own database.

To solve this problem, we propose adding two new endpoints. One that is only
used for binding to user's account, and another that is only for binding to
an identity server of the user's choice. The existing binding endpoint will
be deprecated.

One may question why clients don't just contact an identity server directly
to bind a threepid, bypassing the implications of binding through a
homeserver. While this will work, binds should still occur through a
homeserver such that the homeserver can keep track of which binds were made,
which is important when a user wishes to deactivate their account (and remove
all of their bindings made on different identity servers).

A bind could be made on an identity server, which could then tell the
homeserver that a validation occured, but then there are security
considerations about how to authenticate an identity server in that instance
(and prevent people pretending to be identity servers and telling homeservers
about hundreds of fake binds to a user's account).

This MSC obseletes
[MSC2229](https://github.com/matrix-org/matrix-doc/pull/2229), which dealt
with changing the rules of the `bind` flag on the original endpoint. Since
that endpoint is being deprecated, the MSC is no longer relevant.

## Proposal

Two new endpoints will be added to the Client Server API: `POST
/account/3pid/bind` and `POST /account/3pid/add`. Both will require
authentication. The request parameters of `POST /account/3pid/bind` are the
same as [POST
/account/3pid](https://matrix.org/docs/spec/client_server/unstable#post-matrix-client-r0-account-3pid),
minus the `bind` flag. The request parameters of `POST /account/3pid/add`
will simply consist of a JSON body containing `client_secret` and `sid`.

An example of binding a threepid to **an identity server only** with this new
endpoint is as follows:

First the client must request the threepid be validated by its chosen identity server.

```
POST https://identity.server/_matrix/identity/v2/validate/email/requestToken

{
    "client_secret": "don'tT3ll",
    "email": "bob@example.com",
    "send_attempt": 1
}
```

Once an email has been sent, the user clicks the link in the email, which
notifies the identity server that the email has been verified.

Next, the client completes the bind by calling the new endpoint on the homeserver:

```
POST https://home.server/_matrix/client/r0/account/3pid/bind

{
    "three_pid_creds": {
        "id_server": "example.org",
        "id_access_token": "abc123_OpaqueString",
        "sid": "abc123987",
        "client_secret": "don'tT3ll"
    }
}
```

The homeserver will then make a bind request to the specified identity server
on behalf of the user. The homeserver will record if the bind was successful
and notify the user.

The threepid has now been binded on the user's requested identity server
without causing that threepid to be used for password resets or any other
homeserver-related functions.

For completeness, here is an example of binding a threepid to the
homeserver only, using the old endpoint:

The homeserver is validating the threepid in this instance, so the client
must use the `/requestToken` endpoint of the homeserver:

```
POST https://home.server/_matrix/client/r0/account/3pid/email/requestToken

{
    "client_secret": "don'tT3ll",
    "email": "bob@example.com",
    "send_attempt": 1,
}
```

Once an email has been sent, the user clicks the link in the email, which
notifies the homeserver that the threepid has been verified.

The client then sends a request to the old endpoint on the homeserver to bind
the threepid to user's account.

```
POST /_matrix/client/r0/account/3pid/bind

{
    "sid": "abc123987",
    "client_secret": "don'tT3ll"
}
```

The threepid will then be bound to the user's account.

The achieve the above flows, some changes need to be made to existing
endpoints. This MSC requests that the `id_server` and `id_access_token`
parameters be removed from the Client-Server API's [POST
/account/3pid/email/requestToken](https://matrix.org/docs/spec/client_server/unstable#post-matrix-client-r0-account-3pid-email-requesttoken)
and [POST
/account/3pid/msisdn/requestToken](https://matrix.org/docs/spec/client_server/unstable#post-matrix-client-r0-account-3pid-msisdn-requesttoken)
endpoints, as these endpoints are now only intended for the homeserver to
send validation requests from.

Additionally, the [POST
/account/3pid](https://matrix.org/docs/spec/client_server/unstable#post-matrix-client-r0-account-3pid)
endpoint is deprecated as the two new endpoints replace its functionality.
The `bind` endpoint will also be removed, with the endpoint functioning as if
`bind` was `false`. Allowing an endpoint to add a threepid to both the
identity server and homeserver at the same time requires one to trust the
other, which is the exact behaviour we're trying to eliminate. Doing this
also helps backward compatibility, as explained below.

This MSC also requests that the text "It is imperative that the homeserver
keep a list of trusted Identity Servers and only proxies to those that it
trusts." be removed from all parts of the spec, as the homeserver should no
longer need to trust any identity servers.

## Tradeoffs

It may be possible to reduce the two calls per flow into a single endpoint,
but the current asynchronous approach makes it easy for a client to send a
request, go offline, have the threepid be validated, and then come online
again to finalize the validation afterwards.

## Backwards compatibility

Old matrix clients will continue to use the `/account/3pid` endpoint. As this
MSC removes the `bind` parameter and forces `/account/3pid` calls to act as
if `bind` was set to `false`, old clients will still be able to add 3pids,
but they will only be added to the homeserver, not the identity server. New
homeservers will ignore any `id_server` information passed to this endpoint.

New matrix clients running with old homeservers should try their desired
endpoint (either `/account/3pid/add` or `/account/3pid/bind`) and on
receiving a HTTP `404` error code, should either attempt to use
`/account/3pid` with the `bind` parameter or give up, at their discretion.

## Security considerations

Reducing the homeserver's trust in identity servers should be a boost to
security and improve decentralisation in the Matrix ecosystem to boot.

Caution should be taken for homeserver developers to be sure not to continue
to use user-provided identity servers for any sensitive tasks once it removes
the concept of a trusted identity server list.

## Conclusion

This MSC helps to minimize the homeserver's trust in an identity server even
further to the point where it is only used for binding addresses for lookup -
which was the original intention of identity servers to begin with.

Additionally, by clearly separating the threepid bind endpoint into two
endpoints that each have a clear intention, the concept of attaching
threepids to a Matrix user becomes a lot easier to reason about.
