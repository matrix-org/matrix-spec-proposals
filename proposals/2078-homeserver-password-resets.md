# MSC2078 - Sending Third-Party Request Tokens via the Homeserver

This MSC proposes removing the current requirement of the identity server to
send third-party request tokens, and allows homeservers to implement the
functionality instead. These request tokens are used to verify the identity of
the request author as an owner of the third-party ID (3PID). This can be used
for binding a 3PID to an account, or for resetting passwords via email or SMS.
The latter is what this proposal mainly focuses on, but be aware that it allows
for any task that requires requesting a token for a 3PID to be taken on by the
homeserver instead of the identity server.

The intention is to put less trust in the identity server, which is currently
one of the most centralised components of Matrix. As it stands, an attacker in
control of a identity server can reset a user's password if the identity server
is considered trusted by that homeserver, and the user has registered at least
one 3PID. This is due to the identity server handling the job of confirming the
user's control of that identity.

The MSC seeks to clarify that homeservers can take on the responsibility of
sending password reset tokens themselves, and a new response field that will
aid homeservers in doing so.

# Background

Currently when a client requests a 3PID token, it makes a call to one of the
`/requestToken` endpoints on the homeserver. For instance, during password
resets, a token is requested from either
[/_matrix/client/r0/account/password/email/requestToken](https://matrix.org/docs/spec/client_server/r0.4.0.html#post-matrix-client-r0-account-password-email-requesttoken)
or
[/_matrix/client/r0/account/password/msisdn/requestToken](https://matrix.org/docs/spec/client_server/r0.4.0.html#post-matrix-client-r0-account-password-msisdn-requesttoken),
depending on the medium of the 3PID. These requests are supplied all the
necessary details as well as an `id_server` field containing the domain address
of a identity server trusted by the homeserver.

In order to facilitate these requests, the homeserver will simply proxy them to
the identity server. The IS will send out a token via email or sms, the user
will click a link or enter the token into their client, and either the client
or the user's browser will make a request **directly to the identity server**
with the token for verification. The IS then informs the homeserver that
verification was successful. At this point you can likely see that there is
potential for abuse here, so instead Homeservers should be given the option to
stop proxying the request to the identity server, and instead just send and
validate the token themselves.

## Proposal

The homeserver should be allowed to either proxy `/requestToken` requests or
handle them itself. Specifically, this means that the homeserver can both send
password reset tokens (via email or SMS), as well as accept requests on an
arbitrary endpoint (with the same parameters as
[/_matrix/identity/api/v1/validate/email/submitToken](https://matrix.org/docs/spec/identity_service/r0.1.0.html#post-matrix-identity-api-v1-validate-email-submittoken))
to verify that token.

One additional complication that in the case of SMS, just a code is sent to a
person's phone. This is then given to the client, but the client may not know
where to send the code now, as it doesn't know whether the homeserver or
identity server generated it.

In order to combat this problem, the field `submit_url` MUST be added in the
response from all of the variants of `/requestToken` in the Client-Server API,
if and only if the verification message contains a code the user is expected to
enter into the client (for instance in the case of a short code through SMS).
This URL is simply where the client should submit this token. The endpoint
should accept the same parameters as
[/_matrix/identity/api/v1/validate/{3pid_type}/submitToken](https://matrix.org/docs/spec/identity_service/r0.1.0.html#post-matrix-identity-api-v1-validate-email-submittoken)
in the Identity Service API. The only recommendation to homeserver developers
for this endpoint's path is to not be exactly the same as that of the identity
server, in order to prevent clashes between setups running both an identity
server and homeserver on the same domain.  If `submit_url` is omitted, the
client MUST continue the same behaviour from before, which is to send the token
to the identity server directly. This is intended for backwards compatibility
with older servers.

If the client receives a response to `/requestToken` with `submit_url`, it MUST
accept a token from user input, then make a POST request to the content of
`submit_url` with the `sid`, `client_secret` and user-entered token.
`submit_url` can lead to anywhere the homeserver deems necessary for
verification. To be clear the content of `id_server` does not matter here, the
client should just submit a POST request to the value of `submit_url`. Additionally 
data MUST be submitted as a JSON body.

An example exchange from the client's perspective is shown below:

```
POST https://homeserver.tld/_matrix/client/r0/account/password/email/requestToken

{
  "client_secret": "monkeys_are_AWESOME",
  "email": "alice@homeserver.tld",
  "send_attempt": 1,
  "id_server": "id.example.com"
}
```

If the server responds with a `submit_url` field, it means the client should
collect a token from the user and then submit it to the provided URL.

```
{
  "sid": "123abc",
  "submit_url": "https://homeserver.tld/_homeserver/password_reset/msisdn/submitToken"
}
```

Since a `submit_url` was provided, the client will now collect a token from the
user, say "123456", and then submit that as a POST request to the
`"submit_url"`.

```
POST https://homeserver.tld/_homeserver/password_reset/msisdn/submitToken

{
  "sid": "123abc",
  "client_secret": "monkeys_are_AWESOME",
  "token": "123456"
}
```

The client will then receive an appropriate response:

```
{
  "success": true
}
```

If the client did not receive a `submit_url` field, they should instead assume
that verification will be completed out of band (e.g. the user clicks a link in
their email and makes the submitToken request with their web browser).

## Dismissed Alternatives

Consideration was taken not to make `id_server` an optional field. Let's
assume for a moment that it was optional. Now, a client could send a request to
`/requestToken` omitting the `id_server` field. The homeserver however has
opted to continue proxying `/requestToken` to the identity server, even though
it knows this is potentially insecure. The homeserver now has no idea which
identity server to proxy the request to, and must return a failure to the
client. The client could then make another request with an `id_server`, but
we've now made two requests that ended up in the same outcome, instead of one,
in hopes of saving a very small amount of bandwidth by omitting the field
originally.

At some point we should look into removing the `id_server` field altogether and
removing any email/SMS message sending from the identity server. This would
drastically reduce the amount of trust needed in the identity server and its
required ability. This is, however, a good first step.

## Tradeoffs

If homeservers choose to not proxy the request, they will need to implement the
ability to send emails and/or SMS messages. This is left as a detail for the
homeserver implementation.

