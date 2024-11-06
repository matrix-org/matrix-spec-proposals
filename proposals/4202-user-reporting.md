# MSC4202: Reporting User Profiles over Federation

*This proposal extends [MSC3843](https://github.com/matrix-org/matrix-spec-proposals/pull/3843) to
allow reporting user profiles over federation. Clients can offer a user interface feature, such as
a button on a user's profile, enabling users to report another user's profile to the administrators
of their own homeserver, which can then forward the report over federation if necessary.*

## Proposal

Building upon the reporting mechanism proposed in
[MSC3843](https://github.com/matrix-org/matrix-spec-proposals/pull/3843), this MSC proposes that
clients offer an option in user profiles to report the most recent `m.room.member` event of the
user in a shared room. This leverages the existing client-server and federation APIs for reporting
events, allowing servers to handle profile reports without any changes to the APIs.

### Client Behaviour

Clients SHOULD offer a user interface element in user profiles (e.g., a "Report User" button) that
allows users to report problematic profiles. When reporting a profile, clients SHOULD:

- Identify a room (`room_id`) that both the reporting user and the reported user share. This could
  be any mutual room, including a direct message room. If no mutual room exists, clients MAY
  display an error to the user indicating that the profile cannot be reported through this mechanism.

- Obtain the most recent `m.room.member` event (`event_id`) for the reported user in that room. This
  event contains the profile information (display name, avatar URL) set by the user in that room.

- Use the existing client-server endpoint `POST /_matrix/client/v3/rooms/{roomId}/report/{eventId}`
  to report the `m.room.member` event. The request body SHOULD include:

  - A `reason` provided by the user, explaining why the profile is being reported.
  
  - A `score` indicating the severity, as per the existing specification, though servers MAY ignore
    this parameter.

  - If reporting content in the user's profile, it is recommended for the client include an MXC URI
    for a screenshot of the profile (including MXID and offending content) to aid investigation.

#### Example Request

Reporting a user's profile:

```
POST /_matrix/client/v3/rooms/!roomid:example.org/report/$eventid
Content-Type: application/json

{
  "reason": "Inappropriate profile content: mxc://example.org/abcd1234",
  "score": 0
}
```

### Homeserver Behaviour

Upon receiving the report, the homeserver SHOULD process it according to its moderation policies.
If the event being reported originated from a remote homeserver, and if the homeserver supports
federation reporting as per MSC3843, it MAY forward the report to the remote homeserver using the
federation endpoint:

```
POST /_matrix/federation/v1/rooms/{roomId}/report/{eventId}
Content-Type: application/json

{
  "reason": "Inappropriate profile content"
}
```

The homeserver SHOULD ensure that the `event_id` corresponds to an event in the room and SHOULD
verify that the event was issued by the reported user's homeserver.

### Federation Considerations

When a homeserver receives a report over federation for an `m.room.member` event, it SHOULD handle
it similarly to how it handles other event reports:

- If the reported event was created by the receiving homeserver, it SHOULD process the report and
  take appropriate action as per its moderation policies.

- If the reported event was not created by the receiving homeserver, it MAY choose to ignore the
  report and respond with an `M_UNACTIONABLE` error code and an HTTP `400` status.

#### Example Error Response

```json
{
  "errcode": "M_UNACTIONABLE",
  "error": "Cannot act on the reported event."
}
```

### Considerations

- **Selecting the Appropriate Event**: Clients need to ensure they report the correct
  `m.room.member` event. In rooms where the reported user has updated their profile multiple times,
  the most recent membership event SHOULD be used.

- Clients may offer to report previous member events, if the user has changed their profile to hide
  the original content that caused offence.

- **Shared Rooms**: Reporting a user in a room requires that both users share a room. If no mutual
  room exists, the client cannot report the profile via this mechanism.

- **Event Context**: By reporting the `m.room.member` event, servers have the necessary context to
  investigate the profile as it appeared in that room. The event includes the display name and
  avatar URL used by the user in that room.

## Security Considerations

- **Anonymity**: The original reporter's identity is not included in the report sent over
  federation. However, since the report is sent from the reporter's homeserver, it may still be
  possible to infer their identity, especially if the homeserver has a small user base.

- **Abuse**: This mechanism could be abused to send spam reports. Homeservers SHOULD implement rate
  limiting and MAY require additional verification steps before acting on reports.

- **Privacy**: Reporting an `m.room.member` event includes the profile information set by the user
  in that room. Servers SHOULD handle this data appropriately and respect user privacy.

## Potential Issues

- **Lack of Mutual Rooms**: If the reporting user and the reported user do not share any rooms, the
  client cannot report the profile using this method.

- **Profile Changes**: If the user changes their profile after the report is made, the reported
  `m.room.member` event may no longer reflect the current profile. Servers may need to consider
  this when handling reports.

- **Reporting Outside Rooms**: There is currently no method to report a user/profile without a room,
  so clients that allow viewing a user profile elsewhere (e.g. links to users outside a room, or
  while searching the user directory) may require a non-room-based endpoint for these scenarios.

## Alternatives

- **Reporting by User ID**: Previous versions of this MSC proposed allowing reports to specify a
  user ID directly. However, reusing the existing event reporting mechanism simplifies
  implementation and leverages existing APIs.

- **New Federation Endpoint**: Define a new federation endpoint specifically for reporting user
  profiles. This adds complexity and is unnecessary if the existing mechanisms can be used, however
  some clients may offer the ability to view user profiles outside of a room context and therefore
  require a reporting method not tied to a specific room event. This could be facilitated with a
  variant of [MSC4151](https://github.com/matrix-org/matrix-spec-proposals/pull/4151) that adds an
  endpoint like `/_matrix/client/v3/profile/{userId}/report` to report a user profile specifically
  to the homeserver without optionally notifying room admins.

## Dependencies

- [MSC3843](https://github.com/matrix-org/matrix-spec-proposals/pull/3843): Reporting content over
  federation
