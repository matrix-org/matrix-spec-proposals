# MSC4133: Extending User Profile API with Key:Value Pairs

*This proposal aims to enhance the usability and richness of user profiles within the Matrix
ecosystem by introducing additional, customisable fields. This feature will facilitate the sharing
of more diverse user-defined public information across the federated network. The primary goal is
to enable users to publish a wide variety of possible information, such as preferred communication
languages, pronouns, public-facing organisation roles, or other relevant public details, thereby
enriching the user interaction experience without impacting existing functionalities.*

## Proposal

The Matrix protocol's current user profile structure supports very limited fields (`avatar_url` and
`displayname`). This proposal suggests expanding this structure to include custom fields, allowing
for a more versatile user profile. Specifically, it redefines the existing `avatar_url` and
`displayname` endpoints to be more flexible, while attempting to maximise compatibility with
existing clients and servers to help speed adoption.

Likewise, this proposal is designed to complement rather than replace
[MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769) (Extensible Profiles as
Rooms). While [MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769) offers a
more complex solution for extensible profiles, this proposal focuses on enabling the storage of
small, arbitrary key:value pairs at the global level.

This proposal does not seek to enforce the exact content or usage of these fields but rather to add
a framework for users to have extra data that can be further clarified and extended in the future
as community usage of these fields grows.

Homeservers could disable the ability for users to update these fields or require a specific list
of fields, but the intention of this proposal is that users will be presented with a form to enter
their own free-text fields and values. After using these very flexible fields, the community may
opt to request a further extension to promote one or more fields to be specified per-room via
member events.

### Client-Server API Changes

1. **GET `/_matrix/client/v3/profile/{userId}/{key_name}`**: This endpoint extends the existing
   profile API to allow clients to retrieve the value of a specified `key_name` in a user's profile:

```json
{
    "key_name": "field_value"
}
```

For example, requesting `/_matrix/client/v3/profile/@alice:matrix.org/displayname` would return:

```json
{
    "displayname": "Alice"
}
```

2. **PUT `/_matrix/client/v3/profile/{userId}/{key_name}`**: This endpoint allows clients to set
   the value of a specified `key_name`:

```json
{
    "key_name": "new_value"
}
```

For example, setting `/_matrix/client/v3/profile/@alice:matrix.org/displayname` with:

```json
{
    "displayname": "Alice Wonderland"
}
```

**Note**: As the `DELETE` endpoint exists below, a `PUT` to key using a `null` value should leave
the key in place without deleting the key.

1. **DELETE `/_matrix/client/v3/profile/{userId}/{key_name}`**: This endpoint removes a key (and
   associated value) from the profile, if permitted by the homeserver. This could be considered a
   partial alternative to [MSC3754](https://github.com/matrix-org/matrix-spec-proposals/pull/3754),
   which specifies `DELETE` endpoints specifically for `/avatar_url` and `/displayname`.

2. **GET `/_matrix/client/v3/profile/{userId}`**: This endpoint retrieves all profile fields:

```json
{
    "avatar_url": "mxc://matrix.org/MyC00lAvatar",
    "displayname": "John Doe",
    "u.Custom Field": "value1"
}
```

5. **PATCH `/_matrix/client/v3/profile/{userId}`**: This endpoint accepts a complete JSON object to
   *merge* into the current profile, updating any changed keys without altering any absent ones:

```json
{
    "avatar_url": "mxc://matrix.org/MyNewAvatar",
    "displayname": "John Doe",
    "u.Custom Field": "new_value1"
}
```

6. **PUT `/_matrix/client/v3/profile/{userId}`**: This endpoint accepts a complete JSON object to
   replace the entire profile, adding or updating any changed keys and removing any keys that are
   absent in the provided object:

```json
{
    "avatar_url": "mxc://matrix.org/MyNewAvatar",
    "displayname": "John Doe",
    "u.Custom Field": "new_value1"
}
```

**Note**: User-interactive clients are encouraged to manipulate fields individually to avoid race
conditions, however this `PUT` method allows single-client accounts (such as bots) to overwrite the
entire profile in a single request, which allows bridge bots managing many accounts to bulk update
profiles for their users with minimal requests.

### Server-Server API Changes

**GET `/_matrix/federation/v1/query/profile`** will mirror the client-server API changes to ensure
profile information is consistently available across the federated network.

As there is no method to verify the history of these fields over federation, this endpoint must
only accept requests for local users on the current homeserver, and homeservers must only request a
profile from the homeserver specified in that user's MXID.

As per the current stable endpoint, it accepts an optional `field` query string parameter to
request a single field. At time of writing, the Matrix specification says:

> If no `field` was specified, the response should include the fields of the user's profile that
> can be made public, such as the display name and avatar.

Given this wording, homeservers currently already have the flexibility to decide whether some
fields are published over federation, and this proposal continues to allow this behaviour.

### Capabilities

A new capability `m.profile_fields` is introduced to control the ability to set custom profile
fields.

- **Advertising the Capability**: Servers SHOULD advertise this capability in the `capabilities`
  object returned by the `GET /_matrix/client/v3/capabilities` endpoint.

- **Checking the Capability**: Clients SHOULD check for the presence and value of the
  `m.profile_fields` capability before attempting to create or update custom profile fields.

- **Capability Structure**:

```json
{
    "capabilities": {
        "m.profile_fields": {
            "enabled": true,
            "disallowed": ["org.example.job_title"]
        }
    }
}
```

- **When capability missing**: Clients SHOULD assume extended profile fields are supported, and
  that they can be created/written to. If a server intends to deny some (or all) changes, it SHOULD
  use the capability to advertise this to improve client experience.

- **When `enabled` is `false`**: Clients SHOULD expect to read and display extended fields but
  SHOULD NOT allow users to create or update custom fields. Any attempt to do so may result in a
  `403 Forbidden` error.

- **When `enabled` is `true`**: Clients MAY allow users to create or update custom fields, except
  those listed in the `disallowed` array. Individual requests will receive a `400 Bad Request` or
  `403 Forbidden` response from the homeserver if server-side policies prevent them.

### Error Handling

To ensure clear communication of issues, the following error codes and messages will be used:

#### 400 Bad Request: When request is malformed, exceeds limits, or the profile larger than 64KiB

- **Error code for malformed request**: `M_BAD_JSON`

```json
{
    "errcode": "M_BAD_JSON",
    "error": "The provided JSON is malformed."
}
```

- **Error code for profile/field exceeding size limit**: `M_TOO_LARGE`

```json
{
    "errcode": "M_TOO_LARGE",
    "error": "The profile data exceeds the maximum allowed size of 64KiB."
}
```

or

```json
{
    "errcode": "M_TOO_LARGE",
    "error": "Profile field u.Bio exceeds maximum allowed size of 512 bytes."
}
```

or

```json
{
    "errcode": "M_TOO_LARGE",
    "error": "The key name exceeds the maximum allowed length of 128 bytes."
}
```

or

```json
{
    "errcode": "M_TOO_LARGE",
    "error": "The user has exceeded the maximum number of allowed keys in their profile."
}
```

#### 403 Forbidden: User lacks permission to take this action (e.g. restricted by server policy)

**Note:** See [MSC4170](https://github.com/matrix-org/matrix-spec-proposals/pull/4170) for more
discussion on how server policy may result in 403 errors for profile requests.

- **404 Not Found**: When attempting to `GET` or `DELETE` a profile key that does not exist:
  - **Error Code**: `M_NOT_FOUND`

```json
{
    "errcode": "M_NOT_FOUND",
    "error": "The requested profile key does not exist."
}
```

### Propagation of Profile Fields to Membership Events

The existing fields, `avatar_url` and `displayname`, will continue to trigger state events in each
room. These fields are replicated per-room via member events. Custom fields, however, will **not**
trigger state events in rooms and will exist solely at the global level for storing metadata about
the user.

- **avatar_url** and **displayname**: Changes to these fields will generate state events in all
  rooms the user is a member of.
- **Custom fields**: These are stored in the user's global profile and do not generate state events
  in rooms.

### Key/Namespace Requirements for Custom Fields

Homeservers are not expected to enforce these namespaces, as future expansions may be unknown to
the server, but clients are expected to use the correct namespace for field creation/updates.

- The namespace `m.*` is reserved for fields defined in the Matrix specification. This field may
  have special entry/display requirements that are defined in the Matrix specification. If a client
  does not recognise a field in this namespace, it may attempt to display it, but should not
  attempt to update the content in case it has special requirements.

- The namespace `u.*` is reserved for user-defined fields. The portion of the string after the `u.`
  is defined as the display name of this field. These user-defined fields will always be string
  format, and as measured in UTF-8 byte counts:
  - The *name* of each key must not exceed 128 bytes.
  - The *content* of each value must not exceed 512 bytes.

- Client-specific or unstable fields MUST use the Java package naming convention: `tld.name.*`.

Following support for this specification change, a user could enter a "My Timezone" field manually
in their client and the client would be expected to add a `u.My Timezone` key in their profile.
However, this would be expected to be a string value, even if the user types "null" or an integer
into the box.

In contrast, [MSC4175](https://github.com/matrix-org/matrix-spec-proposals/pull/4175) would use the
unstable key `us.cloke.msc4175.tz` and following approval would then support clients using the
`m.tz` key with the values/validation that MSC requires.

### Size Limits

Whenever "bytes" are referred to as a limit, this is calculated as UTF-8 bytes, so a two-byte code
point consumes two bytes of this limit. This size would be measured before any JSON encoding.

Until another MSC specifies otherwise:

- Each profile *must* be *at most* 64KiB (65536 bytes) in size, as measured in Canonical JSON.
- Each key *must* be a string of *at least* one byte and it's name *must* not exceed 128 bytes.
- Each key's *value* in the `u.*` namespace *must* not exceed 512 bytes in length.
- The limit on overall profile size includes `avatar_url` and `displayname`.

### Implementation Details

- The profile data will be public by default, and compliance with GDPR and other privacy
  regulations will be enforced, particularly in terms of data deletion and retention policies.

- Custom fields will not trigger state events in rooms, maintaining account-wide metadata without
  creating state events or other moderation issues.

- Clients are encouraged to provide settings for users to choose the scope of users they present
  the freetext (i.e. `u.*` namespaced) fields from (e.g. none, only users on the local server,
  users in the current room, any users sharing a room with this user, all users globally) with
  defaults sensitive to their implementation's UI and intended audience.

- Clients should provide a UI for users to enter their own free-text custom fields in the `u.*`
  namespace of their own profile.

## Potential Issues

Initial challenges are primarily ensuring uniform support for custom fields across different
servers and clients during the rollout phase: users may come to expect that other users will check
their supported languages before communicating with them, but the sender's server does not support
custom profiles.

As such, this MSC is designed to be as simple as possible to get initial functionality and data
structures implemented widely in both clients and servers, so further extensions can be debated,
implemented, and tested over time.

As this data is stored only at the global level, it won't allow users to modify fields per-room,
or track historical changes in profile fields. However, this is for performance and moderation
reasons, as many users will struggle to maintain many fields of personal data between different
rooms, and publishing state events for every field change could become an additional burden on
servers and moderators.

In a similar vein, this proposal offers no method to "broadcast" to other users or homeservers that
changes have occurred. This is intentional to keep the scope of this change narrow and maximise
compatibility with existing servers. A future proposal may wish to use an EDU (such as Presence) to
notify users and homeservers that these custom fields have been updated.

## Alternatives

An alternative could be to allow for more specific endpoint modifications or to introduce a
completely new API specifically for extended information. However, these approaches could lead
to more significant changes to the existing API and higher complexity for client developers.

### Security Considerations

Since the profile data is public, there are minimal security risks associated with the transmission
of sensitive information; however, users should be made aware that any information they add will be
visible to others on the federated network.

Clients *should* inform users that any custom profile fields they add will be publicly accessible,
and *should* discourage users from adding sensitive personal information to their profiles.

Homeservers and clients *must* comply with GDPR and other relevant privacy regulations, particularly
regarding data deletion and retention. Profile data *should* be cleared when a user is deactivated.
While homeservers *should* cache remote profiles, they *should* implement strategies that do not
exceed 24 hours to minimize the risk of unintended data persistence.

To minimise the impact of abuse, clients should offer suitable defaults for the users they will
display the profile fields from. A user may *choose* to display fields from all users globally,
but *by default* profiles should only be shown when the users share a room (or the current one).

## Unstable Prefixes

### Unstable Profile Fields

The current Matrix specification technically already allows extra custom fields to be published in
a user's profile. However, as this proposal introduces additional requirements and allows custom
user-defined fields, an unstable prefix should be used on these fields until this proposal has
entered the API as stable:

```json
{
    "avatar_url": "mxc://matrix.org/MyC00lAvatar",
    "displayname": "John Doe",
    "uk.tcpip.msc4133.u.Custom Field": "field_value"
}
```

### Unstable Endpoints

`/_matrix/client/unstable/uk.tcpip.msc4133/profile/{userId}` would be necessary for the `PATCH` and
`PUT` methods allowed when the unstable capability (detailed below) is advertised by the server.

The existing `GET` method would act as normal and remain on `/_matrix/client/v3/profile/{userId}`
without need for an unstable endpoint.

Likewise, when the unstable capability is advertised by the server, the server should accept the
new key endpoints `/_matrix/client/unstable/uk.tcpip.msc4133/profile/{userId}/{key_name}` which
would then promote to `/_matrix/client/v3/profile/{userId}/{key_name}` when the stable capability
is advertised following this specification change.

### Unstable Client Capability

The client capability `m.profile_fields` should use this prefix until stable:

```json
{
    "capabilities": {
        "uk.tcpip.msc4133.profile_fields": {
            "enabled": true,
            "disallowed": ["org.example.job_title"]
        }
    }
}
```

### Unstable Client Features

The client feature `uk.tcpip.msc4133` should be advertised on the `/_matrix/client/versions`
endpoint when the `PUT` and `PATCH` methods are accepted on the
`/_matrix/client/unstable/uk.tcpip.msc4133/profile/{userId}` endpoint.

Once this MSC is merged, the client feature `uk.tcpip.msc4133.stable` should be advertised when the
`PUT` and `PATCH` methods are accepted on the `/_matrix/client/v3/profile/{userId}` endpoint until
the next spec version where this endpoint is officially written into the spec, e.g.

```json
{
  "unstable_features": {
    "uk.tcpip.msc4133": true,
    "uk.tcpip.msc4133.stable": true
  },
  "versions": [
    "v1.11"
  ]
}
```
