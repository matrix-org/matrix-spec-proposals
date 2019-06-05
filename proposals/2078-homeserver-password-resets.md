# MSC2078 - Sending Password Reset Emails via the Homeserver

This MSC proposes removing the current requirement of the identity server to
send password reset tokens, and allows homeservers to implement the
functionality instead. The intention is to put less trust in the identity
server which is currently one of the most centralised components of Matrix. As
it stands, an attacker in control of a identity server can reset a user's
password if the identity server is considered trusted by that homeserver, and
the user has registered at least one third-party identifier (3PID). This is due
to the identity server currently handling the job of confirming the user's
control of that identity.

The MSC aims to simply clarify that homeservers can take on the responisibility
of sending password reset tokens themselves.

## Proposal

Currently when a client requests a password reset, they make a call to either
[/_matrix/client/r0/account/password/email/requestToken](https://matrix.org/docs/spec/client_server/r0.4.0.html#post-matrix-client-r0-account-password-email-requesttoken)
or
[/_matrix/client/r0/account/password/msisdn/requestToken](https://matrix.org/docs/spec/client_server/r0.4.0.html#post-matrix-client-r0-account-password-msisdn-requesttoken).
This request is supplied all the necessary details as well as an `id_server`
field containing the address of a identity server trusted by the homeserver.

The `id_server` field is currently required as the homeserver must know where
to proxy the request to. This MSC proposes not to change the requirements of
this field. Instead, it asks to clarify that the homeserver is allowed to not
proxy the request, but carry it out itself. This would mean the homeserver can
both send password reset tokens (via email or SMS), as well as accept requests
an endpoint (with the same parameters as
[/_matrix/identity/api/v1/validate/email/submitToken](https://matrix.org/docs/spec/identity_service/r0.1.0.html#post-matrix-identity-api-v1-validate-email-submittoken))
to verify that token.

An additional complication is that in the case of SMS, a full link to reset
passwords is not sent, but a short code. The client then asks the user to enter
this code, however the client may now not know where to send the code. Should
it send it to the identity server or the homeserver? Which sent out the code?

In order to combat this problem, the field `submit_url` should be added in the
response from both the email and msisdn variants of the `/requestToken`
Client-Server API, if and only if the verification message contains a code the
user is expected to enter into the client (for instance in the case of a short
code through SMS). If this field is omitted, the client should continue the
same behaviour from before, which is to send the token to the identity server
directly. This is intended for backwards compatibility with older servers.

If the client receives a response to `/requestToken` with `submit_url`, it
should accept the token from user input, then make a POST request to the
content of `submit_url` with the `sid`, `client_secret` and user-entered token.
`submit_url` can lead to anywhere the homeserver deems necessary for
verification. This data should be submitted as a JSON body.

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
  "submit_url": "https://homeserver.tld/path/to/submitToken"
}
```

Since a `submit_url` was provided, the client will now collect a token from the
user, say "123456", and then submit that as a POST request to the
`"submit_url"`.

```
POST https://homeserver.tld/path/to/submitToken

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

## Tradeoffs

If homeservers choose to not proxy the request, they will need to implement the
ability to send emails and/or SMS messages. This is left as a detail for the
homeserver implementation.

## Future Considerations

At some point we should look into removing the `id_server` field altogether and
removing any email/SMS message sending from the identity server. This would
drastically reduce the amount of trust needed in the identity server and its
required ability. This is, however, a good first step.
