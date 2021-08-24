# MSC3356: Add additional fields to the openid user info

The Matrix OpenID user info API (represented by the endpoints `/_matrix/client/r0/user/.../openid/request_token` and `/_matrix/federation/v1/openid/userinfo`) may be used by widgets (i.e. third party applications) to authenticate users against their current Matrix session.

Currently the Matrix user id (Field `sub`) is the only field included in the user info. Especially for room-based access control, like it is implemented for Jitsi conferences (see https://github.com/matrix-org/prosody-mod-auth-matrix-user-verification), additional information (room memberships and powerlevels) must be fetched via Synapse-specific endpoints, which requires a specific administrative access token per Synapse-homeserver.

## Proposal

To enable third party applications for simple room-based access control, the openid user info returned by `/_matrix/federation/v1/openid/userinfo` shall be extended by the following fields:

1. `name` The user's current display name.

2. `room_powerlevels` A map between the id of the local rooms the user is joined to and the respective currently held power level.

```json
{
   "sub": "@johndoe:example.com",
   "name": "John Doe",
   "room_powerlevels": {
      "!zqoHDglfYXhEaDJxKy:example.com": 100,
      "!omkHaNDeHnPdcmHCcE:example.com": 50
   }
}
```
