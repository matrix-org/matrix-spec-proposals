# MSC4133: Extending User Profile API with Key:Value Pairs

*This proposal aims to enhance the usability and richness of user profiles within the Matrix
ecosystem by introducing additional, customisable fields. This feature will facilitate the sharing
of more diverse user-defined public information across the federated network. The primary goal is
to enable users to publish a wide variety of possible information, such as preferred communication
languages, pronouns, public-facing organisation roles, or other relevant public details, thereby
enriching the user interaction experience without impacting existing functionalities.*

## Proposal

The Matrix protocol's current user profile structure supports very limited fields (`avatar_url` and
`displayname`). This proposal suggests expanding this structure to include custom fields,
allowing for a more versatile user profile. Specifically, it redefines the existing `avatar_url`
and `displayname` endpoints to be more flexible, while attempting to maximise compatibility with
existing clients and servers to help speed adoption.

Likewise, this proposal is designed to complement rather than replace
[MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769) (Extensible profiles as
rooms). While [MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769) offers a more
complex solution for extensible profiles, this proposal focuses on enabling the storage of small,
arbitrary key:value pairs at the global level.

This proposal does not seek to enforce the exact content or usage of these fields but rather to add
a framework for users to have extra data that can be further clarified and extended in the future as
community usage of these fields grows.

Homeservers could disable the ability for users to update these fields, or require a specific list
of fields, but the intention of this proposal is that users will be presented with a form to enter
their own free-text fields and values. After using these very flexible fields, the community may
opt to request a further extension to promote one or more fields to be specified per-room via
member events.

### Client-Server API Changes

1. **GET `/_matrix/client/v3/profile/{userId}/{key_name}`**: This endpoint will replace the existing
   profile endpoints. It will return the value of the specified `key_name`:

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

2. **PUT `/_matrix/client/v3/profile/{userId}/{key_name}`**: This endpoint will set the value of the
   specified `key_name`:

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

3. **DELETE `/_matrix/client/v3/profile/{userId}/{key_name}`**: This endpoint will remove the key
   (and associated value) from the profile, if permitted by the homeserver. Could be considered a
   partial alternative to [MSC3754](https://github.com/matrix-org/matrix-spec-proposals/pull/3754)
   which specifies `DELETE` endpoints for specifically `/avatar_url` and `/displayname`.

4. **GET `/_matrix/client/v3/profile/{userId}`**: This endpoint will retrieve all profile fields:

```json
{
    "avatar_url": "mxc://matrix.org/MyC00lAvatar",
    "displayname": "John Doe",
    "u.Custom Field": "value1",
    "m.allowed_list": ["value2", "value3"]
}
```

5. **PATCH `/_matrix/client/v3/profile/{userId}`**: This endpoint will accept a complete JSON object
   to *merge* into the current profile, updating any changed keys without removing/changing any
   absent ones:

```json
{
    "avatar_url": "mxc://matrix.org/MyNewAvatar",
    "displayname": "John Doe",
    "u.Custom Field": "new_value1",
    "m.allowed_list": ["new_value2", "new_value3"]
}
```

6. **PUT `/_matrix/client/v3/profile/{userId}`**: This endpoint will accept a complete JSON object
   to replace the entire profile, not only adding/updating any changed keys, but removing any
   absent ones in the process:

```json
{
    "avatar_url": "mxc://matrix.org/MyNewAvatar",
    "displayname": "John Doe",
    "u.Custom Field": "new_value1",
    "m.allowed_list": ["new_value2", "new_value3"]
}
```

**Note**: User-interactive clients are encouraged to manipulate fields individually to avoid race
conditions, however this `PUT` method allows single-client accounts (such as bots) to overwrite the
entire profile in a single request, which allows bridge bots managing many accounts to bulk update
profiles for their users with minimal requests.

### Server-Server API Changes

**GET `/_matrix/federation/v1/query/profile`** will mirror the client-server API changes
to ensure profile information is consistently available across the federated network.

As there is no method to verify the history of these fields over federation, this endpoint must
only accept requests for local users on the current homeserver, and homeservers must only request
a profile from the homeserver specified in that user's MXID.

As per the current stable endpoint, it accepts an optional `field` query string parameter to
request a single field. At time of writing, the Matrix specification says:

> If no `field` was specified, the response should include the fields of the user's profile that
> can be made public, such as the display name and avatar.

Given this wording, homeservers currently already have the flexibility to decide whether some
fields are published over federation, and this proposal continues to allow this behaviour.

### Capabilities

A new capability `m.profile_fields` will be introduced to control the ability to set custom
profile fields.

For backwards compatibility purposes, clients should assume these extended endpoints are not
supported when this capability is missing.

When the capability exists but is set to `false`, clients should expect to read/display extended
fields, but should expect the server to deny creating/updating any custom fields. When this is set
to `true` it should be possible to create/update custom fields, but individual updates may receive
a 400/403 from the homeserver following the error codes listed below.

Example capability object:

```json
{
  "capabilities": {
    "m.profile_fields": {
      "enabled": false
    }
  }
}
```

### Error Handling

To ensure clear communication of issues, the following error codes and messages will be used:

**400 Bad Request**: When the request is malformed, exceeds specified limits, or the profile JSON
object is larger than 64KiB:

- **Error Code for Malformed Request**: `M_BAD_JSON`

```json
{
    "errcode": "M_BAD_JSON",
    "error": "The provided JSON is malformed."
}
```

- **Error Code for Exceeding Size Limit**: `M_TOO_LARGE`

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
    "error": "Profile field u.Bio exceeds maximum allowed size of 1024 bytes."
}
```

- **Error Code for Invalid Data**: `M_INVALID_PARAM`

```json
{
    "errcode": "M_INVALID_PARAM",
    "error": "The key name exceeds the maximum allowed length of 255 bytes."
}
```

- **Error Code for Exceeding Resource Limits**: `M_RESOURCE_LIMIT_EXCEEDED`

```json
{
    "errcode": "M_RESOURCE_LIMIT_EXCEEDED",
    "error": "The user has exceeded the maximum number of allowed keys in their profile."
}
```

**403 Forbidden**: When the user does not have permission to take this action on a specific key,
such as when the server policy (e.g.
[MSC4170](https://github.com/matrix-org/matrix-spec-proposals/pull/4170)) restricts such actions:

- **Error Code**: `M_FORBIDDEN`

```json
{
    "errcode": "M_FORBIDDEN",
    "error": "You do not have permission to modify this field."
}
```

**404 Not Found**: When attempting to `GET` or `DELETE` a profile key that does not exist:

- **Error Code**: `M_NOT_FOUND`

```json
{
    "errcode": "M_NOT_FOUND",
    "error": "The requested profile key does not exist."
}
```

### Propagation of Profile Fields to Membership Events

The existing fields, `avatar_url` and `displayname`, will continue to trigger state events in each
room. These fields are replicated per-room via member events. Other fields, however, will **not**
trigger state events in rooms. They will exist solely at the global level and are intended for
storing metadata about the user that does not need to be replicated in each room.

- **avatar_url** and **displayname**: Changes to these fields will generate state events in all
  rooms the user is a member of.
- **Custom fields**: These are stored in the user's global profile and do not generate state events
  in rooms.

### Key/Namespace Requirements for Custom Fields

Homeservers are not expected to enforce these namespaces, as future expansions may be unknown to
the server, but clients are expected to use the correct namespace for field creation/updates.

The namespace for field names is defined as follows:

- The namespace `m.*` is reserved for fields defined in the Matrix specification. This field may
  have special entry/display requirements that are defined in the Matrix specification. If a client
  does not recognise a field in this namespace, it may attempt to display it, but should not
  attempt to update the content in case it has special requirements.
- The namespace `u.*` is reserved for user-defined fields. The portion of the string after the `u.`
  is defined the display name of this field. These user-defined fields will always be string format.
- Client-specific or unstable fields MUST use the Java package naming convention: `tld.name.*`.

Following support for this specification change, a user could enter a "My Timezone" field manually
in their client and the client would be expected to add a `u.My Timezone` key in their profile.
However, this would be expected to be a string value, even if the user types "null" or an integer
into the box.

In contrast, [MSC4175](https://github.com/matrix-org/matrix-spec-proposals/pull/4175) would use the
unstable key `us.cloke.msc4175.tz` and following approval would then support clients using the
`m.tz` key with the values/validation that MSC requires.

### Size Limit

The key *must* be a string of *at least* one byte, and *must* not exceed 255 bytes.

To ensure efficient handling and storage of profile data, this proposal requires the entire user
profile JSON object not exceed 64KiB.

A future MSC may increase this limit or add exceptions, but this current limit has been chosen to
allow both servers and clients to have predictable upper limits, especially for caching.

Homeservers may limit the fields (or content) that their local users can set, setting a size limit
per field and/or for the entire profile, and may limit the maximum number of keys a user may set.

For example, if a homeserver implementation finds it more efficient to measure limits per value, it
could limit users to 50 keys with a 1024 byte limit per value, which would allow a user to set the
50 of the maximum key and value lengths without needing to calculate against the 64KiB total limit.

**Note:** The existing `avatar_url` and `displayname` keys are contained within the profile, so if
an implementation enforces a per-value limit on fields, it must also enforce them upon these fields.

### Implementation Details

- This feature will be implemented as optional but recommended, enabling a smooth transition and
  minimal disruption to existing deployments.
- The profile data will be public by default, and compliance with GDPR and other privacy
  regulations will be enforced, particularly in terms of data deletion and retention policies.
- Custom fields will not trigger state events in rooms, maintaining account-wide metadata without
  creating state events or other moderation issues.

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

## Security Considerations

Since the profile data is public, there are minimal security risks associated with the transmission
of sensitive information; however, it is critical to ensure that all data handled through these
endpoints complies with GDPR and other privacy regulations, particularly in the event of user data
deletion.

It is crucial to ensure that clients inform users this data will be public, does not include
sensitive personal information, and complies with legal frameworks such as GDPR. Homeservers will
be encouraged to implement data caching strategies that do not exceed 24 hours to minimise the risk
of unintended data persistence.

## Unstable Prefixes

### Unstable Profile Fields

The current Matrix specification technically already allows extra custom fields to be published in
a user's profile, however as this proposal introduces additional requirements and allows custom
user-defined fields, an unstable prefix should be used on these fields until this proposal has
entered the API as stable:

```json
{
    "avatar_url": "mxc://matrix.org/MyC00lAvatar",
    "displayname": "John Doe",
    "uk.tcpip.msc4133.u.Custom Field": "field_value",
    "uk.tcpip.msc4133.m.allowed_list": ["one value", "another value"]
}
```

### Unstable Endpoints

`/_matrix/client/unstable/uk.tcpip.msc4133/profile/{userId}` would be necessary for the `PATCH` and `PUT`
methods allowed when unstable capability (detailed below) is advertised by the server.

The existing `GET` method would act as normal and remain on `/_matrix/client/v3/profile/{userId}`
without *need* for an unstable endpoint.

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
      "enabled": false
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
