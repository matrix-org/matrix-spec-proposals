# MSC4259: Profile Sync API for Federation

Currently, homeservers must individually request profiles via
[`/_matrix/federation/v1/query/profile`](https://spec.matrix.org/v1.13/server-server-api/#get_matrixfederationv1queryprofile)
when they need to display user information. This leads to significant inefficiencies in the Matrix
federation: servers must make separate requests for each profile they need, cannot efficiently
detect when profiles change, and risk serving stale data to their users. The problem becomes more
acute as servers cache profile data to reduce federation traffic, requiring careful balance between
cache duration and data freshness.

This proposal introduces a new federation endpoint that allows homeservers to efficiently sync
profile data from multiple users in a single request. It builds upon
[MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133) which introduced extended
profile fields, and adds a token-based sync mechanism that lets servers track profile changes
without repeatedly requesting unchanged data.

## Proposal

The current approach to federation profile lookups has several issues:

- Inefficient use of network resources when requesting multiple profiles
- Increased latency when displaying user information
- Difficulty in maintaining accurate (non-stale) cached copies of remote profiles
- No standardised way to efficiently detect when profiles have been updated

This MSC adds a new `/_matrix/federation/v1/profiles` endpoint that accepts batched profile
requests and returns only changed data on subsequent requests using sync tokens.

### Behaviour

1. The requesting server provides an array of MXIDs it wishes to sync profiles for

2. If `last_batch` is provided, only profiles that have changed since that sync token are returned

3. The responding server:
   - MAY filter which profiles it returns based on its policies
   - MAY return partial results and indicate this via `next_batch`
   - MUST include `next_batch` in successful responses
   - MUST NOT return profiles unless they were requested
   - SHOULD indicate users that are not present on the server
   - SHOULD suggest an appropriate `next_time` for subsequent requests

4. Missing profiles in the response indicate no changes since `last_batch`

5. Error responses for specific profiles suggest excluding them from future requests

### Federation API Changes

#### New Endpoint

- **Method**: `POST`
- **Endpoint**: `/_matrix/federation/v1/profiles`
- **Auth**: Standard federation authentication
- **Rate Limiting**: Implementation-defined, with server guidance via `next_time` response field

#### Request Format

```json
{
    "last_batch": "opaque_server_token", // Optional sync token from previous response
    "accounts": [                        // Required array of MXIDs
        "@alice:example.com",
        "@bob:example.com"
    ]
}
```

#### Response Format

```json
{
    "content": {
        "@alice:example.com": {
            "displayname": "Alice",
            "avatar_url": "mxc://example.com/alice",
            "org.example.language": "en-GB"
        },
        "@bob:example.com": {
           "errcode": "M_NOT_FOUND",
           "error": "User not found"
        }
    },
    "next_batch": "opaque_server_token_2",
    "next_time": "2024-03-14T12:30:00Z"
}
```

#### Error Codes

Inside profile payloads, standard Matrix error codes are used for errors:

- `M_FORBIDDEN`: "User profile is not accessible to the requesting server"
- `M_NOT_FOUND`: "User does not exist"

For entire-endpoint errors, the following standard Matrix error codes are used:

- **403 response**:
  - `M_FORBIDDEN`: "Profile lookup over federation is disabled on this homeserver"

- **404 response**:
  - `M_UNKNOWN_TOKEN`: "Profile sync token unknown or expired"

- **429 response**:
  - `M_LIMIT_EXCEEDED`: "Too many requests" (should use `retry_after_ms` to indicate time to retry)

### Implementation Notes

- When no `last_batch` parameter is provided, return current profile data for all requested
  accounts. This is typically used for initial sync or to start over when all tokens have expired.

- Servers MUST maintain a history of sync tokens to allow clients to resume syncs after connection
  issues. Servers SHOULD store at least the last 3-5 tokens to provide resilience against temporary
  network failures.

- Servers MAY expire old tokens based on their own policies (e.g. time-based expiry or storage
  limits). When a client provides an expired token, servers MUST return `M_UNKNOWN_TOKEN` to prompt
  the client to restart their sync chain.

- The implementation of tokens is left to the server - they could be timestamps, change IDs, or any
  other mechanism that allows tracking profile changes. The only requirement is that using a token
  in a subsequent request returns all profile changes since that token was issued.

- All timestamps (e.g. in `next_time`) MUST be UTC and include the 'Z' suffix.

- The `next_time` field is advisory; servers are recommended to also enforce their own rate limits.

- Servers MAY redact certain profiles, e.g. refusing to return profiles for users not sharing rooms
  with the requesting server.

- Requesting servers COULD optimise their sync frequency based on user activity, for example:
  1. Reducing frequency or temporarily suspending syncs when users are offline
  2. Resuming more frequent syncs when users become active again

## Security Considerations

1. This endpoint follows standard federation authentication rules

2. Servers maintain control over which profiles they expose

3. Rate limiting helps prevent abuse

## Alternatives

1. Timestamp-based syncing
   - Less reliable for tracking exact changes
   - Harder to handle clock skew between servers
   - No built-in mechanism for detecting missed updates
   - More complex to implement correctly across timezones

2. EDU-based profile updates
   - Higher bandwidth usage due to individual EDU requests (especially for each changed field,
     if a user updates multiple fields which a pull-based endpoint would help consolidate)
   - Requires servers to send EDUs the recipient may not be interested in
   - No way to quickly recognise when a recipient is permanently offline to stop sending EDUs
   - Difficult for servers to know how long to cache if sender may have stopped sending EDUs
   - Profile updates do not necessarily need to be instantaneous like typing notifications

3. Webhook-style push notifications for profile changes
   - No precedent for this in the current Matrix specification
   - Similar issues to EDUs regarding bandwidth and wasted outbound traffic

## Unstable Prefix

Until this proposal is stable:

- Endpoint: `/_matrix/federation/unstable/uk.tcpip.msc4259/profiles`
- Client feature flag: `uk.tcpip.msc4259`

### Feature Flag Advertisement

Servers implementing this endpoint MUST advertise support via the `/_matrix/federation/v1/version` endpoint:

```json
{
    "server": {
        "name": "Synapse",
        "version": "1.99.0"
    },
    "unstable_features": {
        "uk.tcpip.msc4259": true
    }
}
```

Once this MSC is merged, servers SHOULD advertise `uk.tcpip.msc4259.stable` until the next spec
version where these endpoints are officially written into the spec.
