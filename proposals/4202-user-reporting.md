# MSC4202: Reporting User Profiles over Federation

*This proposal extends [MSC3843](https://github.com/matrix-org/matrix-spec-proposals/pull/3843) to
allow reporting user profiles over federation. Clients can offer a user interface feature, such as
a button at the bottom of a user's profile, enabling users to report another user's profile to the
administrators of the server from which the profile was accessed.*

## Proposal

Building upon the reporting mechanism proposed in
[MSC3843](https://github.com/matrix-org/matrix-spec-proposals/pull/3843) and the user profile
information introduced in [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133),
this MSC proposes modifying the reporting endpoint to allow the use of a Matrix User ID (MXID) in
place of an event ID. This enables users to report user profiles directly to the homeserver of the
reported user.

### Extended Federation Endpoint

The existing federation endpoint for reporting events is:

```
POST /_matrix/federation/v1/rooms/{roomId}/report/{eventId}
```

This MSC proposes extending this endpoint to allow reporting user profiles by accepting a user ID
in the `eventId` position, identified by the `@` prefix:

```
POST /_matrix/federation/v1/rooms/{roomId}/report/{userId}
```

Where `userId` is a Matrix User ID in the format `@user:domain`.

#### Example Request

Reporting a user's profile:

```
POST /_matrix/federation/v1/rooms/!roomid:example.org/report/@baduser:badserver.com
{
  "reason": "Inappropriate profile content: mxc://example.org/abcd1234"
}
```

### Request Body Parameters

The request body includes the following parameters:

- `reason` (string, **required**): A description explaining why the profile is being reported.
  This cannot be blank. It is *strongly* recommended that clients include the MXC URI of a
  screenshot of the problematic profile content, clearly showing as much of the profile as possible
  (especially the MXID) to ensure the user's identity is unmistakable. Homeservers are free to log
  profile changes as they see fit, however this snapshot may assist investigating the report.

### Behaviour

When a homeserver receives a profile report, it SHOULD handle it similarly to how it handles event
reports:

- If the reported `userId` belongs to the receiving homeserver, it SHOULD process the report and
  take appropriate action as per its moderation policies.
- If the reported `userId` does not belong to the receiving homeserver, it MAY choose to ignore
  the report and respond with an `M_UNACTIONABLE` error code and an HTTP `400` status.

### Error Responses

- `400 M_UNACTIONABLE`: The server cannot act on the reported content. This may be because the
  reported user is not hosted on the server, or the server does not support profile reporting.

#### Example Error Response

```json
{
  "errcode": "M_UNACTIONABLE",
  "error": "Cannot act on the reported user."
}
```

### Rate Limiting

Homeservers are strongly encouraged to rate limit incoming profile reports to prevent abuse.
An example limit might be 10 reports per minute from a single server.

## Client Behaviour

Clients SHOULD offer a user interface element in user profiles (e.g., a "Report User" button) that
allows users to report problematic profiles. When reporting a profile:

- Clients SHOULD use the extended federation endpoint to send the report to the reported user's
  homeserver.
- Clients SHOULD include a `reason` for the report, provided by the user.
- Clients SHOULD include an MXC URI of the offending profile to aid in the investigation.

## Security Considerations

- **Anonymity**: The original reporter's identity is not included in the report sent over
  federation. However, since the report is sent from the reporter's homeserver, it may still be
  possible to infer their identity, especially if the homeserver has a small user base.

- **Abuse**: This mechanism could be abused to send spam reports. Homeservers SHOULD implement rate
  limiting and MAY require additional verification steps before acting on reports.

- **Privacy**: Including screenshots may expose personal data. Clients SHOULD inform users that
  any attached images will be sent to the remote server and ensure users consent to this.

- **Validity**: Homeservers SHOULD verify that the `userId` is a valid Matrix User ID and handle
  reports appropriately. They SHOULD also ensure that they do not process reports for users not
  hosted on their server unless they choose to do so.

## Potential Issues

- **Spam Reports**: Servers may receive a high volume of unnecessary or malicious reports. Rate
  limiting and appropriate error responses can help mitigate this issue.
- **Cross-Domain Trust**: Servers need to decide how much trust to place in reports received from
  other homeservers. Policies may vary between servers.

## Alternatives

- **New Endpoint**: Define a new federation endpoint specifically for reporting user profiles.
  However, reusing the existing endpoint simplifies implementation and leverages existing mechanisms.
- **Policy Rooms**: As mentioned in MSC3843, servers could negotiate shared policy rooms to handle
  reports. This adds complexity and is beyond the scope of this MSC.

## Unstable Prefix

While this MSC is not yet stable, implementations SHOULD use the following endpoint:

```
POST /_matrix/federation/unstable/uk.tcpipuk.msc0000/rooms/{roomId}/report/{userId}
```

## Dependencies

- [MSC3843](https://github.com/matrix-org/matrix-spec-proposals/pull/3843): Reporting content over
  federation
