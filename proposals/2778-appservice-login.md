# MSC2778: Providing authentication method for appservice users

Appservices within Matrix are increasingly attempting to support End-to-End Encryption. As such, they
need a way to generate devices for their users so that they can participate in E2E rooms. In order to
do so, this proposal suggests implementing an appservice extension to the 
[`POST /login` endpoint](https://matrix.org/docs/spec/client_server/r0.6.0#post-matrix-client-r0-login).

Appservice users do not usually need to login as they do not need their own access token, and do not
traditionally need a "device". However E2E encryption demands that all users in a room have a device
which means bridge users need to be able to generate a device on demand.

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
    "user": "alice"
  }
}
```

The response body should be unchanged from the existing `/login` specification.

If:

- The access token is not provided
- The access token does not correspond to a appservice
- The access token does not correspond to a appservice that manages this user
- Or the user has not previously been registered

Then the servers should reject with HTTP 403, with an `errcode` of `"M_FORBIDDEN"`. 

Homeservers should ignore the `access_token` parameter if a type other than
`m.login.application_service` has been provided.

The expected flow for appservices would be to `/register` their users, and
then `/login` to generate the appropriate device.

## Potential issues

This proposal means that there will be more calls to make when setting up a appservice user, when
using encryption. While this could be done during the registration step, this would prohibit creating
new devices should the appservice intentionally or inadvertently lost the client-side device data.

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

## Security considerations

The /login endpoint will generate an access token which can be used to control the appservice user, which
is superflous as the appservice `as_token` should be used to authenticate all requests on behalf of ghosts.
This can safely be ignored or used, but is an extra token hanging around.

## Unstable prefix

Implementations should use `uk.half-shot.msc2778.login.application_service` for `type` given in the
`POST /login` until this lands in a released version of the specification.