# MSC3356: Add additional fields to the openid user info

The Matrix OpenID user info API (represented by the endpoints `/_matrix/client/r0/user/.../openid/request_token` 
and `/_matrix/federation/v1/openid/userinfo`) may be used by widgets (i.e. third party applications) to authenticate 
users against their current Matrix session.

Currently the Matrix user id (Field `sub`) is the only field included in the user info. Especially for room-based 
access control, like it is implemented for Jitsi conferences (see 
https://github.com/matrix-org/prosody-mod-auth-matrix-user-verification), additional information 
(room memberships and powerlevels) must be fetched via Synapse-specific endpoints, which requires a specific 
administrative access token per Synapse-homeserver.

## Proposal

To enable third party applications for simple room-based access control, the OpenID user info returned by 
`/_matrix/federation/v1/openid/userinfo` shall be extended by the following fields:

1. `display_name` The user's current display name. This value may be used to enforce consistent user names between Matrix 
and the third party application.

2. `avatar_url` The user's avatar url _(optional)_.

3. `room_powerlevels` A map between the id of the local rooms the user is joined to and the respective currently 
held power level.

```json
{
   "sub": "@johndoe:example.com",
   "display_name": "John Doe",
   "avatar_url": "https://eu.ui-avatars.com/api/?name=John+Doe",
   "room_powerlevels": {
      "!zqoHDglfYXhEaDJxKy:example.com": 100,
      "!omkHaNDeHnPdcmHCcE:example.com": 50
   }
}
```

## Security Considerations

As the additional fields may contain sensitive information, they shall not be exposed by default. Instead, the 
[OpenID token request endpoint](https://matrix.org/docs/spec/client_server/latest#id603) 
`/_matrix/client/r0/user/.../openid/request_token` shall be extended to accept a user-/client-defined set of 
requested user info fields for the specific token. The set may be specified as an array `userinfo_fields` in 
an optional JSON request body:

```
POST /_matrix/client/r0/user/%40johndoe%3Aexample.com/openid/request_token HTTP/1.1
Content-Type: application/json

{ "userinfo_fields": [ "display_name", "room_powerlevels" ] }
```

## Unstable prefix

_While this proposal is not considered stable, implementations should use `org.matrix.msc3356.` as a prefix for all 
introduced fields:_

| Field name | Unstable field name |
|-|-|
| `display_name` | `org.matrix.msc3356.display_name` |
| `avatar_url` | `org.matrix.msc3356.avatar_url` |
| `room_powerlevels` | `org.matrix.msc3356.room_powerlevels` |
| `userinfo_fields` | `org.matrix.msc3356.userinfo_fields` |
