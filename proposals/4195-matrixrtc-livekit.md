# MSC4195: MatrixRTC using LiveKit backend

This proposal defines a new [MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143) compliant
RTC backend Focus type utilising [LiveKit](https://github.com/livekit/livekit) SFUs.

## Proposal

The `type` of the Focus is `livekit`.

We introduce a two sub-types of LiveKit Focus:

- LiveKit SFU Focus - a LiveKit SFU backend infrastructure.
- LiveKit oldest membership Focus selection algorithm - an algorithm to select a communal LiveKit SFU based on the age of the session participants.

### LiveKit SFU Focus

A backend LiveKit SFU Focus is represented in these places:

- the `m.rtc_foci` entry of the `.well-known/matrix/client`
- the `foci_preferred` of the `m.rtc.member` state event
- the `focus_active` of the `m.rtc.member` state event. TODO: is this correct?

It is represented as a JSON object with the following fields:

- `type` required string - `livekit`
- `livekit_service_url` required string - The URL of the LiveKit MatrixRTC backend to use for the session.

An example within a `.well-known/matrix/client`:

```json5
{
  // rest of the .well-known/matrix/client content
  "m.rtc_foci": [
    {
      "type": "livekit",
      "livekit_service_url": "https://livekit-jwt.call.element.dev"
    }
  ]
}
```

An example within the `foci_preferred` of the `m.rtc.member` state event:

```json5
{
  // rest of the m.rtc.member event
  "foci_preferred": [
    {
      "type": "livekit",
      "livekit_service_url": "https://livekit-jwt.call.element.dev",
    }
  ]
}
```

### LiveKit oldest membership Focus selection algorithm

We define a new Focus that uses the age of the session participant `m.rtc.member` to determine the Focus to use.

This can be used in the `focus_active` of the `m.rtc.member` state event.

The Focus is represented as follows:

- `type` required string - `livekit`
- `focus_selection` required string - `oldest_membership`

### SFU authentication with LiveKit

LiveKit SFUs requires a JWT `access_token` to be provided when [connecting to the WebSocket](https://docs.livekit.io/reference/internals/client-protocol/#WebSocket-Parameters).
We standardise the method by which the LiveKit JWT token is obtained by a MatrixRTC application.

Prerequisites:

- the `livekit_service_url` for the MatrixRTC backend has been discovered from one of the methods above
- the Matrix client has obtained an OpenID Token from the [Client-Server API](https://spec.matrix.org/v1.11/client-server-api/#openid).

The JWT token is obtained by making a `POST` request to the `/sfu/get` endpoint of the LiveKit service.

The `Content-Type` of the request is `application/json` and the body JSON body contains the following fields:

- `room_id` required string: the room ID of the Matrix room where the `m.rtc.member` event state key is present.
- `session` required object: the contents of the `session` from the `m.rtc.member` event.
- `openid_token` required object: The verbatim OpenID token response obtained from the
  [Client-Server API](https://spec.matrix.org/v1.11/client-server-api/#post_matrixclientv3useruseridopenidrequest_token).
- `member` required object: The contents of the `member` from the `m.rtc.member` event.

If the request is successful an HTTP `200` response is returned with `Content-Type` `application/json` and the body contains:

- `jwt` string: The JWT token to use for authentication with the SFU.
- `url` string: The URL of the LiveKit SFU to use for the session.

The LiveKit JWT should have permissions as defined below.

An example request where `livekit_service_url` is `https://livekit-jwt.call.element.dev/xyz`:

```http
POST /xyz/sfu/get HTTP/1.1
Host: livekit-jwt.call.element.dev
Content-Type: application/json

{
  "room_id": "!tDLCaLXijNtYcJZEey:element.io",
  "session": {
    "application": "m.call",
    "call_id": ""
  },
  "openid_token": {
    "access_token":  "FPkexLLvKbAHKclQhpvgfWxx",
    "expires_in": 3600,
    "matrix_server_name": "call.ems.host",
    "token_type": "Bearer"
  },
  "member": {
    "id": "xyzABCDEF10123",
    "device_id": "DEVICEID",
    "user_id": "@user:matrix.domain"
  }
}
```

An example response:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "jwt": "thejwt",
  "url": "wss://livekit-jwt.call.element.dev/rtc"
}
```

### Pseudonymous LiveKit participant identity

We use a pseudonymous LiveKit participant identity for privacy so that the Matrix user ID is not exposed to the LiveKit SFU backend.

The pseudonymous LiveKit participant identity is calculated as the SHA-256 hash of the concatenation of:

- the Matrix user ID
- `|`
- `member`.`device_id`
- `|`
- `member`.`id`.

e.g. `SHA256(@user:matrix.domain|DEVICEID|xyzABCDEF10123)`

### LiveKit JWT permission grants

As well as being a valid [LiveKit JWT](https://docs.livekit.io/home/get-started/authentication/) the following constraints
are applied:

- `sub`: This is the pseudonymous LiveKit participant identity as described above.
- `video`.`room`: The name of the room should be the unique for the given `room_id` and `session` inputs. It is opaque to the MatrixRTC application.

The permissions should be sufficient to allow the MatrixRTC application to join the room.

For example:

```json
{
  "exp": 1726764439,
  "iss": "API2bYPYMoVqjcE",
  "nbf": 1726760839,
  "sub": "SHA256(@user:matrix.domain|DEVICEID|xyzABCDEF10123)",
  "video": {
    "canPublish": true,
    "canSubscribe": true,
    "room": "!gIpOlaUSrXBmgtveWK:call.ems.host_m.call_",
    "roomCreate": true,
    "roomJoin": true
  }
}
```

### End-to-end encryption

End-to-end encryption is mapped into the LiveKit frame level encryption mechanism described [here](https://github.com/livekit/livekit/issues/1035).

Where a shared password is used by the application it is used as the `string` input to the LiveKit key derivation function (which uses PBKDF2) and all participants use the same derived key for encryption and decryption.

Where a per-participant key is used it is imported as the byte array input to the LiveKit key derivation function (which uses HKDF). The `index` field of the `m.rtc.encryption_keys` event is used as the key index for the key provider.

On receipt of the `m.rtc.encryption_keys` event the application can associate the received key with the LiveKit participant identity by calculating the
pseudonymous LiveKit participant identity as described above.

## Potential issues

## Alternatives

## Security considerations

To prevent abuse of SFU resources, during the backend service should validate the OpenID token as part of requests to `/sfu/get`.

The Server-Server API endpoint [/_matrix/federation/v1/openid/userinfo](https://spec.matrix.org/v1.11/server-server-api/#get_matrixfederationv1openiduserinfo)
can be used for this purpose.

An access control policy should be applied based on the result of the OpenID token validation. For example,
access might be restricted to users of a particular homeserver or to users with a specific role.

The homeserver restriction could be applied by checking the `matrix_server_name` field of the OpenID token before validating the token.

The `room_id` could be validated too, and checking that the Matrix user from the OpenID token is a member of the room.

## Unstable prefix

Assuming that this is accepted at the same time as [MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143)
no unstable prefix is required as these fields  will only be accessed via some other unstable prefix.

## Dependencies

This MSC builds on [MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143)
(which at the time of writing has not yet been accepted into the spec).
