# MSC4259: Profile Update EDUs for Federation

Currently, homeservers must individually request profiles via
[`/_matrix/federation/v1/query/profile`](https://spec.matrix.org/v1.13/server-server-api/#get_matrixfederationv1queryprofile)
when they need to display user information.

This can lead to significant inefficiencies in Matrix federation, as servers must make separate
requests for each profile they need, cannot efficiently detect when profiles change, and thus risk
serving stale data to their users. The problem becomes more acute as servers cache profile data to
reduce federation traffic, requiring a careful balance between cache duration and data freshness.

This issue has always existed to some degree, but has gained urgency to accommodate profile changes
introduced in [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133).

This proposal specifically focuses on efficient delivery of profile updates between servers. While
client delivery of profile updates is also important, that solution is to be addressed separately,
such as through a sliding sync extension like
[MSC4262](https://github.com/matrix-org/matrix-spec-proposals/pull/4262).

## Proposal

The current approach to federation profile lookups has several issues:

- Inefficient use of network resources when requesting multiple profiles
- Increased latency when displaying user information
- Difficulty in maintaining accurate (non-stale) cached copies of remote profiles
- No standardised way to efficiently detect when profiles have been updated

This MSC adds a new `m.profile` EDU type that servers generate when users update their profiles,
allowing real-time notifications of profile changes between servers.

### Behaviour

1. When a user updates their profile via client-server APIs, their homeserver:
   - Processes and stores the profile update as per normal
   - MAY generate EDUs to notify other servers
   - If sending EDUs, SHOULD only send them to servers that share a room with the user,
     filtering/ratelimiting/de-duplicating the broadcasts as needed to meet their own policies

2. Remote servers receiving the EDU:
   - MAY use these EDUs to update cached profile data, and thus hold onto cached profiles for longer
   - COULD ignore the EDU if they are not interested in updates for this user

3. EDU handling:
   - Servers MAY cache profile data from EDUs to reduce future federation traffic
   - Profile information is considered public, so servers MAY broadcast to any known server
   - Servers MUST NOT forward EDUs to other servers

### EDU Format

```json5
{
    "type": "m.profile",
    "content": {
        "user_id": "@alice:example.com",
        "fields": {
            "displayname": "Alice",
            "avatar_url": null,  // Signals removal of avatar_url
            "org.example.language": "en-GB"
        }
    }
}
```

The EDU contains only fields that have changed. Fields set to `null` should be considered removed.
Omitted fields should be considered unchanged. Recipients can fetch the full profile using the
existing federation API if they need to verify the complete state.

### Implementation Notes

- All profile field values follow the same validation rules as the existing profile endpoints

- Servers should implement appropriate rate limiting for EDU generation/sending, and MAY delay
  notifications to de-duplicate/combine multiple field updates into a single EDU

- While this EDU system reduces the need for manual profile requests, implementations should note:
  - Remote servers may not support or send these EDUs
  - EDUs can occasionally fail to be delivered
  - Both servers and clients COULD implement periodic re-fetching of profiles (e.g. weekly or
    monthly) if they require stronger consistency guarantees
  - The frequency of such re-fetching should be balanced against available resources, network
    conditions, and desired data freshness

- Profile updates are typically much less frequent than other EDU types like presence updates,
  so broadcasting these small delta updates to servers sharing rooms with the user is considered
  efficient and scalable. Receiving servers can quickly filter unwanted updates with minimal
  processing overhead.

## Security Considerations

1. EDUs follow standard federation authentication rules

2. Profile information is considered public data in Matrix

3. Rate limiting helps prevent abuse

## Alternatives

1. Pull-based sync API
   - Could be more efficient for small servers that want to sync on their own schedule
   - Allows servers to batch multiple profile requests
   - However, doesn't scale well to servers with thousands of users
   - Complex to maintain filter lists of which users each server wants updates for
   - Higher latency for profile updates compared to EDU-based approach

2. Webhook-style push notifications for profile changes
   - No precedent for this in the current Matrix specification
   - Similar scaling issues to pull-based approach regarding filter lists
   - Would require new federation endpoints and authentication mechanisms

## Unstable Prefix

Until this proposal is stable, use:

- EDU type: `uk.tcpip.msc4259.profile`
