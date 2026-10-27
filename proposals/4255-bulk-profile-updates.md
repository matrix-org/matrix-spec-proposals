# MSC4255: Bulk Profile Updates Per-User

This proposal builds upon [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133)
(Extending User Profile API with Custom Key:Value Pairs) to introduce two additional endpoints to
the Matrix Client-Server API that enable efficient bulk updates of user profiles. These endpoints
are particularly valuable for bridge applications (AppServices) that need to manage profiles for
many bridged users simultaneously.

## Problem Statement

When users interact with Matrix through bridges, they expect their profile information to stay
consistent with the bridged platform. However, the current Matrix specification only provides
single-field update endpoints, making it difficult for bridges to efficiently maintain this
consistency at scale.

Currently, bridges must make individual API calls for each field they want to update in a user's
profile. For instance, when a Discord user changes their avatar, username, and status
simultaneously, the bridge must make three separate API calls to reflect these changes in Matrix.
This becomes a significant bottleneck when managing thousands of bridged users, leading to delayed
updates and increased server load.

Some commercial bridge providers, such as Beeper, have already implemented proprietary solutions
for this problem. This proposal aims to standardise this functionality, allowing both commercial
and self-hosted bridge deployments to benefit from similar, efficient client functionality.

## Current Specification

The Matrix specification currently defines a read-only endpoint for retrieving all profile fields:
[`GET /_matrix/client/v3/profile/{userId}`](https://spec.matrix.org/v1.13/client-server-api/#get_matrixclientv3profileuserid).

However, there is no equivalent endpoint for updating multiple profile fields simultaneously.
Instead, clients must use individual PUT requests for each field they want to update.

## Proposal

This MSC introduces two new endpoints that allow updating multiple profile fields in a single
request:

### PUT Endpoint - Replace Profile

- **Endpoint**: `PUT /_matrix/client/v3/profile/{userId}`
- **Description**: Replace the entire profile with the provided fields, removing any fields not
  included in the request.
- **Rate Limiting**: Servers SHOULD apply appropriate rate limits based on their policies
- **Authentication**: Requires valid access token with permission to modify the requested userId's
  profile
- **Request Body**:

```json
{
    "avatar_url": "mxc://matrix.org/MyNewAvatar",
    "displayname": "John Doe",
    "m.example_field": "new_value1",
    "org.example.job_title": "Software Engineer"
}
```

### PATCH Endpoint - Merge Profile Updates

- **Endpoint**: `PATCH /_matrix/client/v3/profile/{userId}`
- **Description**: Merge the provided fields into the existing profile, only modifying specified
  fields.
- **Rate Limiting**: Servers SHOULD apply appropriate rate limits based on their policies
- **Authentication**: Requires valid access token with permission to modify the requested userId's
  profile
- **Request Body**:

```json
{
    "avatar_url": "mxc://matrix.org/MyNewAvatar",
    "m.example_field": "new_value1",
    "org.example.to_delete": null
}
```

### Behaviour

- The `PUT` endpoint replaces the entire profile, removing any fields not included in the request
- The `PATCH` endpoint only updates the fields provided, leaving other fields unchanged
- Both endpoints MUST respect the same size limits as individual field updates (64 KiB total
  profile size)
- Both endpoints MUST follow the same field naming requirements as individual updates
- Authentication and permissions follow the same rules as individual field updates
- Servers MUST process these requests atomically to prevent partial updates
- Servers MUST validate all fields in the request before applying any changes
- For `PATCH` requests:
  - Each top-level field in the request body directly overrides the corresponding field in the
    existing profile without any recursive merging
  - Setting a field's value to `null` removes that field from the profile
  - Fields not mentioned in the request body remain unchanged
  - The request must still result in a valid profile (respecting size limits and field naming rules)

## Use Cases

### Bridge Profile Synchronisation

When bridging platforms that support rich profiles (such as Discord, Slack, or IRC services),
bridges need to synchronise multiple profile fields simultaneously. For example:

1. Avatar URL changes
2. Display name updates
3. Custom status fields
4. Platform-specific metadata (roles, badges, etc.)

Currently, each field requires a separate API call, which is inefficient when managing thousands of
bridged users. These new endpoints allow bridges to update all relevant fields in a single request,
reducing server load and improving synchronisation speed.

## Security Considerations

1. **Authentication and Authorization**
   - All requests MUST be authenticated
   - Servers MUST verify the access token has permission to modify the requested userId's profile
   - Rate limiting SHOULD be applied as per the homeserver's normal profile endpoint limits

2. **Data Validation**
   - Servers MUST validate all fields before applying any changes
   - The total profile size MUST NOT exceed 64 KiB
   - Field names MUST follow the [Common Namespaced Identifier Grammar](https://spec.matrix.org/v1.13/appendices/#common-namespaced-identifier-grammar)

3. **Atomic Updates**
   - Servers MUST ensure updates are atomic to prevent inconsistent profile states
   - If any field update fails validation, the entire request MUST be rejected

## Error Codes

This MSC uses the same error codes as defined in [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133):

- `M_FORBIDDEN` if the user lacks permission
- `M_LIMIT_EXCEEDED` if server-defined limits are exceeded
- `M_BAD_JSON` if the request body is malformed
- `M_NOT_JSON` if the request body isn't JSON
- `M_INVALID_PARAM` if field names are invalid
- `M_TOO_LARGE` if the resulting profile would exceed size limits

## Feature Flags

Servers MUST advertise support for this feature through the following flags in the `/versions`
response:

- Stable: `uk.tcpip.msc4255.stable`
- Unstable: `uk.tcpip.msc4255`

Until this proposal is stable, implementations SHOULD use these endpoints:

- `PUT /_matrix/client/unstable/uk.tcpip.msc4255/profile/{userId}`
- `PATCH /_matrix/client/unstable/uk.tcpip.msc4255/profile/{userId}`

## Relationship to Other MSCs

This proposal doesn't technically depend on [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133)
but is considered more necessary as [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133)
introduced the concept of extra fields in the global profile, while this MSC then adds efficient
bulk update capabilities specifically to support AppService use cases.

## Alternatives

1. Continue using individual field updates, accepting the performance impact on bridges
2. Create a new batch endpoint instead of following REST conventions with PUT/PATCH
3. Restrict these endpoints to only AppServices, limiting potential use cases
4. Wait for proprietary solutions to become more widespread, risking fragmentation
