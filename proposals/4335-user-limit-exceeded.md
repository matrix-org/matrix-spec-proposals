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

This proposal adds a new error code `M_USER_LIMIT_EXCEEDED` to the Matrix specification. This error
code should be returned when a user has exceeded limits that are specifically associated with their
account, such as:

* **Storage quotas**: When a user has exceeded their allocated storage space for media uploads,
  message history, or other persistent data.
* **Resource limits**: When a user has reached their maximum number of allowed rooms, devices,
  or other account-scoped resources.
* **Feature limits**: When a user has exceeded usage limits for specific features (e.g., number
  of public rooms they can create, number of invites they can send).
* **Account tier restrictions**: When a user's account type (free, premium, etc.) prevents them
  from performing certain operations.

The error should be returned with HTTP status code **403 Forbidden** to indicate that the operation
is not permitted due to the user's current limits.

### Error Response Format

When returning this error, servers should use the standard Matrix error response format:

```json
{
  "errcode": "M_USER_LIMIT_EXCEEDED",
  "error": "User has exceeded their storage quota of 10GB"
}
```

The human-readable `error` field should provide specific information about what limit was exceeded
and, where possible, include details about the current usage and limit values to help users
understand their situation.

### Applicable Endpoints

This error code can be returned by any Matrix Client-Server API endpoint where user-specific limits
might be enforced. Examples might include:

* `POST /_matrix/media/v3/upload` - When storage quota is exceeded
* `POST /_matrix/client/v3/rooms/{roomId}/invite` - When invite limits (like maximum participant count) are exceeded

The HTTP response code should be chosen based on the specification for the individual endpoint. For
example, the most appropriate code for `POST /_matrix/media/v3/upload` would be `403`.

### Distinction from Other Error Codes

This error code is distinct from:

* `M_LIMIT_EXCEEDED`: Used for general rate limiting that applies to all users or based on IP/client
* `M_FORBIDDEN`: Used for authorization failures or policy violations not related to usage limits
* `M_RESOURCE_LIMIT_EXCEEDED`: Used for server-wide resource constraints affecting all users
* `M_TOO_LARGE`: Used when a request is too large (file size, message length, etc.) regardless of user limits

## Potential issues

This error code does not specify the exact nature of the limit that was exceeded, which could
potentially lead to ambiguity. However, this is consistent with other Matrix error codes that
rely on the human-readable `error` field to provide specific details. Implementers should ensure
they provide clear, actionable error messages.

The error code does not provide machine-readable information about current usage or limits,
which could be useful for clients to display progress bars or usage statistics. However, adding
such fields would require a more complex specification change and could be addressed in a future
MSC if deemed necessary.

## Alternatives

Several alternatives were considered for this proposal:

**Use M_RESOURCE_LIMIT_EXCEEDED**: The existing `M_RESOURCE_LIMIT_EXCEEDED` error code could be
expanded to cover user-specific limits. However, this code is currently used for server-wide
resource constraints, and overloading it could create confusion about whether the limit applies
to the user specifically or the server generally.

**Add structured error information**: Instead of a simple error code, a more complex error format
could include machine-readable fields for limit types, current usage, and maximum limits. While
this would provide more information, it would require a more significant change to the error
response format and could be added in a future MSC if needed.

**Multiple specific error codes**: Separate error codes could be introduced for different types
of limits (e.g., `M_STORAGE_LIMIT_EXCEEDED`, `M_ROOM_LIMIT_EXCEEDED`). However, this approach
would require many new error codes and doesn't provide significant benefits over a single code
with descriptive error messages.

## Security considerations

None as only adding a new error code.

## Unstable prefix

While this proposal is being developed and refined, implementations should use the unstable prefix
`ORG.MATRIX.MSC4335.M_USER_LIMIT_EXCEEDED` instead of `M_USER_LIMIT_EXCEEDED`.

For example:

```json
{
  "errcode": "ORG.MATRIX.MSC4335.M_USER_LIMIT_EXCEEDED",
  "error": "User has exceeded their fair usage limit of 2GB"
}
```

Once the MSC is accepted and the error code is included in the Matrix specification, implementations
should transition to using the stable `M_USER_LIMIT_EXCEEDED` error code.

## Dependencies

None.
