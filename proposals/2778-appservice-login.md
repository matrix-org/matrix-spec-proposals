# MSC2778: Providing authentication method for appservice users

Appservices within Matrix are increasingly attempting to support End-to-End Encryption. As such, they
need a way to generate devices for their users so that they can participate in E2E rooms. In order to
do so, this proposal suggests implementing an appservice extension to the 
[`POST /login` endpoint](https://matrix.org/docs/spec/client_server/r0.6.0#post-matrix-client-r0-login).

Appservice users do not usually need to login as they do not need their own access token, and do not
traditionally need a "device". However, E2E encryption demands that at least one user in a room has a Matrix device
which means bridge users need to be able to generate a device on demand. In the past, bridge developers
have used the bridge bot's device for all bridge users in the room, but this causes problems should the bridge
wish to only join ghosts to a room (e.g. for DMs).

Another advantage this provides is that an appservice can now be used to generate access tokens for
any user in its namespace without having to set a password for that user, which may be useful in the
case of software where maintaining password(s) in the configuration is undesirable.

## Proposal

A new `type` is to be added to `POST /login`.

`m.login.application_service`

The `/login` endpoint may now take an `access_token` in the same way that other
authenticated endpoints do. No additional parameters should be specified in the request body.

Example request

```json
{
  "type": "m.login.application_service",
  "identifier": {
    "type": "m.id.user",
    "user": "_bridge_alice"
  }
}
```

Note: Implementations MUST use the `identifier.type`=`m.id.user` method of specifying the
localpart. The deprecated top-level `user` field **cannot** use this login flow type. This
is deliberate so as to coax developers into using the new identifier format when implementing
new flows.

The response body should be unchanged from the existing `/login` specification.

If:

- The access token is not provided
- The access token does not correspond to a appservice
- Or the user has not previously been registered

Then the servers should reject with HTTP 403, with an `errcode` of `"M_FORBIDDEN"`. 

If the access token does not correspond to a appservice that manages this user, then the `errcode` should be `"M_EXCLUSIVE"`.

Homeservers should ignore the `access_token` parameter if a type other than
`m.login.application_service` has been provided.

The expected flow for appservices would be to `/register` their users, and
then `/login` to generate the appropriate device.

## Potential issues

This proposal means that there will be more calls to make when setting up a appservice user, when
using encryption. While this could be done during the registration step, this would prohibit creating
new devices should the appservice intentionally or inadvertently have lost the client-side device data.

## Alternatives

One minor tweak to the current proposal could be to include the token as part of the auth data, rather than
being part of the header/params to the request. An argument could be made for either, but since the specification
expects the appservice to pass the token this way in all requests, including `/register`, it seems wise to keep
it that way.

Some community members have used implementation details such as a "shared secret" authentication method to
log into the accounts without having to use the /login process at all. Synapse provides such a function,
but also means the appservice can now authenticate as any user on the homeserver. This seems undesirable from a
security standpoint.

A third option could be to create a new endpoint that simply creates a new device for an appservice user on demand.
Given the rest of the matrix eco-system does this with /login, and /login is already extensible with `type`, it would
create more work for all parties involved for little benefit.

Finally, `POST /register` does already return a `device_id`, `access_token` for appservice users by default. However critically
this means that bridges will need to be designed to store the access_token and device_id from the point of creating the user,
so older bridges would be unable to get an access token for existing users as `POST /register` would fail.
It would difficult to log out these tokens if they got exposed additionally, as the AS would not be able to fetch a new access token.
Furthermore, the ability to generate access tokens for real users who registered elsewhere would not be possible with this mechanism. 

## Security considerations

Appservices could use this new functionality to generate devices for any userId that are within it's namespace e.g. setting the
user namespace regex to `@.*:example.com` would allow appservice to control anyone on the homeserver. While this sounds scary, in practise
this is not a problem because:

- Appservice namespaces are mainained by the homeserver admin. If the namespace were to change, then it's reasonable
  to assume that the server admin is aware. There is no defense mechanism to stop a malicious server admin from creating new
  devices for a given user's account as they could also do so by simply modifying the database.

- While an appservice *could* try to masquerade as a user maliciously without the server admin expecting it, it would still 
  be bound by the restrictions of the namespace. Server admins are expected to be aware of the implications of adding new
  appservices to their server so the burden of responsibility lies with the server admin.

- Appservices already can /sync as any user using the `as_token` and send any messages as any user in the namespace, the only
  difference is that without a dedicated access token they are unable to receive device messages. While in theory this
  does make them unable to see encrypted messages, this is not designed to be a security mechanism.

- An appservice trying to log in as a user will always create a new device, which means the user would be informed of the
  new device on their existing sessions. It should be very obvious if a malicous appservice is creating new devices on your account.

In conclusion this MSC only automates the creation of new devices for users inside an AS namespace, which is something
a server admin could already do. Appservices should always be treated with care and so with these facts in mind the MSC should 
be considered secure.

## Unstable prefix

Implementations should use `uk.half-shot.msc2778.login.application_service` for `type` given in the
`POST /login` until this lands in a released version of the specification.

## Implementations

The proposal has been implemented by a homeserver, a bridge SDK and two bridges:

- [synapse](https://github.com/matrix-org/synapse/pull/8320)
- [mautrix-python](https://github.com/tulir/mautrix-python/commit/12d7c48ca7c15fd3ff61608369af1cf69e289aeb)
- [mautrix-whatsapp](https://github.com/tulir/mautrix-whatsapp/commit/ead8a869c84d07fadc7cfcf3d522452c99faaa36)
- [matrix-appservice-bridge](https://github.com/matrix-org/matrix-appservice-bridge/pull/231/files#diff-5e93f1b51d50a44fcf0ca46ea1793c1cR851-R864)
