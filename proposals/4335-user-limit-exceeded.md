# MSC4335: M_USER_LIMIT_EXCEEDED error code

Currently, Matrix homeservers lack a standardized error code to indicate when user-related limits
have been exceeded. This creates inconsistent client experiences when homeservers need to reject
operations due to per-user quotas, rate limits, or resource constraints.

Different implementations may return generic error codes like `M_FORBIDDEN` or `M_TOO_LARGE`, making
it difficult for clients to provide appropriate user feedback or implement proper retry logic.

A concrete use case for this is the
[fair usage limits introduced on the matrix.org homeserver](https://matrix.org/homeserver/pricing/#usage-limits).

This proposal introduces a new error code `M_USER_LIMIT_EXCEEDED` that homeservers can use to
signal when a user has exceeded their allocated limits, distinct from general rate limiting or
server-wide constraints. This improves the user experience by allowing clients to provide more
specific error messages and handle user-specific limitations appropriately.

## Proposal

This proposal adds a new [common error code]
`M_USER_LIMIT_EXCEEDED` to the Matrix specification. This error code should be returned when a user has exceeded
limits that are specifically associated with their account, such as:

* **Storage quotas**: When a user has exceeded their allocated storage space for media uploads,
  message history, or other persistent data.
* **Resource limits**: When a user has reached their maximum number of allowed rooms, devices,
  or other account-scoped resources.
* **Feature limits**: When a user has exceeded usage limits for specific features (e.g., number
  of public rooms they can create, number of invites they can send).
* **Account tier restrictions**: When a user's account type (free, premium, etc.) prevents them
  from performing certain operations.

The error response must also contain additional fields:

* `info_uri` string (required) - an opaque URI that the client can link the user to in order to get more context on the
  error.
* `soft_limit` boolean (optional, default `false`) - `true` means that the specific limit encountered can be increased.
  Otherwise it is a hard limit that cannot be increased.
* `increase_uri` (required if `soft_limit` is `true`) - an opaque URI where the user can undertake actions to increase
  the encountered limit.

The `info_uri` and `increase_uri` are "opaque" in the sense that the homeserver implementation may choose to encode
information, such as the type of limit encountered, within the URI but it may do so using an encoding of its choosing.

The HTTP response code should be chosen based on the specification for the individual endpoint. For
example, the most appropriate code for [`POST /_matrix/media/v3/upload`] would be `403 Forbidden`.

An example response body for the error might look as follows:

```json
{
  "errcode": "M_USER_LIMIT_EXCEEDED",
  "error": "User has exceeded their storage quota of 10GB",
  "info_uri": "https://example.com/homeserver/about?limit_type=quota",
  "soft_limit": true,
  "increase_uri": "https://example.com/homeserver/upgrade"
}
```

For a hard limit:

```json
{
  "errcode": "M_USER_LIMIT_EXCEEDED",
  "error": "User has exceeded their storage quota of 10GB",
  "info_uri": "https://example.com/homeserver/about?limit_type=quota"
}
```

### Applicable Endpoints

As it is a [common error code], `M_USER_LIMIT_EXCEEDED` may be returned by any Matrix Client-Server API endpoint.

For the purpose of illustration, practical examples could include:

* [`POST /_matrix/media/v3/upload`] - When the server is enforcing a storage quota.
* [`POST /_matrix/client/v3/rooms/{roomId}/invite`] - When invite limits (like maximum participant count) are exceeded.
* [`POST /_matrix/client/v3/createRoom`] - When the number or type of rooms is constrained.

### Distinction from Other Error Codes

This error code is distinct from:

* `M_LIMIT_EXCEEDED`: Used for general rate limiting that applies to all users or based on IP/client
* `M_FORBIDDEN`: Used for authorization failures or policy violations not related to usage limits
* `M_RESOURCE_LIMIT_EXCEEDED`: Used for server-wide resource constraints affecting all users
* `M_TOO_LARGE`: Used when a request is too large (file size, message length, etc.) regardless of user limits

## Potential issues

This error code does not specify the exact nature of the limit that was exceeded, which could
potentially lead to ambiguity. However, this is consistent with other Matrix error codes that
rely on the human-readable `error` field to provide specific details. Instead the `info_uri`
provides a way for the homeserver to apply arbitrary limits without the client having to understand
every type in advance.

The homeserver can choose to provide localised and personalised content on the `info_uri` and `increase_uri` if it
wishes.

The error code does not provide machine-readable information about current usage or limits,
which could be useful for clients to display progress bars or usage statistics. However, adding
such fields would require a more complex specification change and could be addressed in a future
MSC if deemed necessary.

## Alternatives

Several alternatives were considered for this proposal:

### Use M_RESOURCE_LIMIT_EXCEEDED

The existing [`M_RESOURCE_LIMIT_EXCEEDED`] looks very similar at first glance.

However, this code is explicitly referring to a limit being applied to the *server* and not to the *user* themselves:

> The request cannot be completed because the homeserver has reached a resource limit imposed on it.
> For example, a homeserver held in a shared hosting environment may reach a resource limit if it starts using too much
> memory or disk space.

As such this error code is currently rendered by
[existing](https://github.com/element-hq/element-web/blob/c96da5dbf8e20ced4a512a03a75c91f8680e8d40/src/i18n/strings/en_EN.json#L1112)
[clients](https://github.com/element-hq/element-ios/blob/2dc7b76c44545b3d027cdf0196c6af6eba8932f4/Riot/Assets/en.lproj/Vector.strings#L615)
as something similar to:

> This homeserver has exceeded one of its resource limits

As such, I think this message would be confusing to users the interim whilst clients updated their implementations and
that a new error code would be the best way forward.

### Add structured error information

Instead of a simple error code, a more complex error format
could include machine-readable fields for limit types, current usage, and maximum limits. While
this would provide more information, it would require a more significant change to the error
response format and could be added in a future MSC if needed.

### Multiple specific error codes

Separate error codes could be introduced for different types
of limits (e.g., `M_STORAGE_LIMIT_EXCEEDED`, `M_ROOM_LIMIT_EXCEEDED`). However, this approach
would require many new error codes and doesn't provide significant benefits over a single code
with descriptive error messages.

### Define specific endpoints

Instead of making this a [common error code] instead it could be an
["other" error code](https://spec.matrix.org/v1.16/client-server-api/#other-error-codes) and have the specific endpoints
listed.

A downside of this is that if a homeserver wished to introduce a new type of limit or quota that was not foreseen, then
another MSC would be required to introduce it.

Instead, by making it a [common error code] the homeserver operator has flexibility over what types of limit they
choose without requiring further coordination with clients.

## Security considerations

None as only adding a new error code.

## Unstable prefix

While this proposal is being developed and refined, implementations should use the following:

* `ORG.MATRIX.MSC4335_USER_LIMIT_EXCEEDED` instead of `M_USER_LIMIT_EXCEEDED`
* `org.matrix.msc4335.info_uri` instead of `info_uri`
* `org.matrix.msc4335.soft_limit` instead of `soft_limit`
* `org.matrix.msc4335.increase_uri` instead of `increase_uri`

For example:

```json
{
  "errcode": "ORG.MATRIX.MSC4335_USER_LIMIT_EXCEEDED",
  "error": "User has exceeded their fair usage limit of 2GB",
  "org.matrix.msc4335.info_uri": "https://example.com/homeserver/about?limit_type=quota",
  "org.matrix.msc4335.soft_limit": true,
  "org.matrix.msc4335.increase_uri": "https://example.com/homeserver/upgrade"
}
```

## Dependencies

None.

[`POST /_matrix/media/v3/upload`]: https://spec.matrix.org/v1.16/client-server-api/#post_matrixmediav3upload
[`POST /_matrix/client/v3/rooms/{roomId}/invite`]: https://spec.matrix.org/v1.16/client-server-api/#thirdparty_post_matrixclientv3roomsroomidinvite
[`M_RESOURCE_LIMIT_EXCEEDED`]: https://spec.matrix.org/v1.16/client-server-api/#other-error-codes
[common error code]: https://spec.matrix.org/v1.16/client-server-api/#common-error-codes
[`POST /_matrix/client/v3/createRoom`]: https://spec.matrix.org/v1.16/client-server-api/#post_matrixclientv3createroom
