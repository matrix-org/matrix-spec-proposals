# Separate Endpoints for Binding Threepids

*Note: This MSC obseletes
[MSC2229](https://github.com/matrix-org/matrix-doc/pull/2229), which dealt
with changing the rules of the `bind` flag on [POST
/account/3pid](https://matrix.org/docs/spec/client_server/r0.5.0#post-matrix-client-r0-account-3pid).
That endpoint is being deprecated as part of this MSC, thus MSC2229 is no
longer relevant.*

On the Client Server API there is currently a single endpoint for binding a
threepid (an email or a phone number): [POST
/account/3pid](https://matrix.org/docs/spec/client_server/r0.5.0#post-matrix-client-r0-account-3pid).
Depending on whether the `bind` flag is `true` or `false`, the threepid will
be bound to either a user's account on the homeserver, or both the homeserver
and an identity server. Note that we use the term `add` when talking about
adding a threepid to a homeserver, and `bind` when binding a threepid to an
identity server. This terminology will be used throughout the rest of this
proposal.

Typically, when using the `/account/3pid` endpoint, the identity server
handles the verification -- either by sending an email to an email address,
or a SMS message to a phone number. Once completed, the homeserver will check
with the identity server that verification had indeed happened, and if so,
the threepid would be either added to the homeserver, or added to the
homeserver and bound to the identity server simultaneously.

Now, consider the fact that the identity server used in this process is
provided by the user, using the endpoint's `id_server` parameter. If the user were
to supply a malicious identity server that would immediately answer "yes" to
any threepid validation, then the user could add any threepid to their
account on the homeserver (which is likely not something homeserver admins want).

To be clear, this is not a long-standing security issue. It is not a problem
in any released version of Synapse, as Synapse keeps a list of "trusted
identity servers" that acts a whitelist for what identity servers a user can
specify.

The concept of this whitelist is being removed in this MSC however, as part
of lessening the reliance of homeservers on identity servers. This cannot be
done while the homeserver is still trusting an identity server for validation
of threepids. If the endpoints are split, the homeserver will handle the
validation of threepids being added to user accounts, and identity servers
will validate threepids being bound to themselves.

## Proposal

To solve this problem, two new endpoints will be added to the Client Server
API: `POST /account/3pid/bind` and `POST /account/3pid/add`. Both will
require authentication and be rate-limited. The request parameters of `POST
/account/3pid/bind` are the same as [POST
/account/3pid](https://matrix.org/docs/spec/client_server/unstable#post-matrix-client-r0-account-3pid),
minus the `bind` flag, and the contents of `three_pid_creds` have been
brought to the top level of the request body. The request parameters of `POST
/account/3pid/add` will simply consist of a JSON body containing
`client_secret` and `sid`.

The homeserver should prevent a threepid being added to a user's account if
it already part of another user's account. However, the homeserver should not
check for existing threepids when binding to an identity server. Identity
servers do not enforce this requirement and neither should the proxying
homeserver.

An example of binding a threepid to an identity server with this new endpoint
is as follows:

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
    "id_server": "example.org",
    "id_access_token": "abc123_OpaqueString",
    "sid": "abc123987",
    "client_secret": "don'tT3ll"
}
```

The homeserver will then make a bind request to the specified identity server
on behalf of the user. The homeserver will record if the bind was successful
and notify the user.

The threepid has now been bound on the user's requested identity server
without causing that threepid to be used for password resets or any other
homeserver-related functions.

For completeness, here is an example of adding a threepid to the homeserver
only, using the `/account/3pid/add` endpoint:

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

The client then sends a request to the endpoint on the homeserver to add 
the threepid to a user's account.

```
POST https://home.server/_matrix/client/r0/account/3pid/add

{
    "sid": "abc123987",
    "client_secret": "don'tT3ll"
}
```

The threepid has now been added to the user's account.

To achieve the above flows, some changes need to be made to existing
endpoints. The `id_server` and `id_access_token` parameters are to be removed
from the Client-Server API's [POST
/account/3pid/email/requestToken](https://matrix.org/docs/spec/client_server/unstable#post-matrix-client-r0-account-3pid-email-requesttoken)
and [POST
/account/3pid/msisdn/requestToken](https://matrix.org/docs/spec/client_server/unstable#post-matrix-client-r0-account-3pid-msisdn-requesttoken)
endpoints, as these endpoints are now only intended for the homeserver to
send validation requests from.

Additionally, the [POST
/account/3pid](https://matrix.org/docs/spec/client_server/unstable#post-matrix-client-r0-account-3pid)
endpoint is deprecated as the two new endpoints replace its functionality.
The `bind` parameter is to be removed, with the endpoint functioning as if
`bind` was `false`. Allowing an endpoint to add a threepid to both the
identity server and homeserver at the same time requires one to trust the
other, which is the exact behaviour we're trying to eliminate. Doing this
also helps backward compatibility, as explained below.

The text "It is imperative that the homeserver keep a list of trusted
Identity Servers and only proxies to those that it trusts." is to be removed
from all parts of the spec, as the homeserver should no longer need to trust
any identity servers.

## Tradeoffs

One may question why clients don't just contact an identity server directly
to bind a threepid, bypassing the implications of binding through a
homeserver. While this will work, binds should still occur through a
homeserver such that the homeserver can keep track of which binds were made,
which is important when a user wishes to deactivate their account (and remove
all of their bindings made on different identity servers).

A verification could occur on an identity server, which could then tell the
homeserver that a validation happened, but then there are security
considerations about how to authenticate an identity server in that instance
(and prevent people pretending to be identity servers and telling homeservers
about hundreds of fake threepid additions to a user's account).

## Backwards compatibility

Old matrix clients will continue to use the `/account/3pid` endpoint. This
MSC removes the `bind` parameter and forces `/account/3pid` calls to act as
if `bind` was set to `false`. Old clients will still be able to add 3pids to
the homeserver, but not bind to the identity server. New homeservers must
ignore any `id_server` information passed to this endpoint.

New matrix clients running with old homeservers should try their desired
endpoint (either `/account/3pid/add` or `/account/3pid/bind`) and on
receiving a HTTP `404` error code, should either attempt to use
`/account/3pid` with the `bind` parameter or give up, at their discretion.

## Security considerations

Reducing the homeserver's trust in identity servers should be a boost to
security and improve decentralisation in the Matrix ecosystem to boot.

Some endpoints of the Client Server API allow a user to provide an
`id_server` parameter. Caution should be taken for homeserver developers to
stop using these user-provided identity servers for any sensitive tasks, such
as password reset or account registration, if it removes the concept of a
trusted identity server list.
