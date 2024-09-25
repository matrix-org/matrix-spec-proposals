# MSC4133: Extending User Profile API with Custom Key:Value Pairs

*This proposal aims to enhance user profiles within the Matrix ecosystem by introducing
customisable key:value pairs to global profiles. Allowing users to add arbitrary public information
to their profiles (such as preferred languages, organisational roles, or other relevant public
details) should enrich user interactions without impacting existing functionality.*

## Proposal

Currently, the Matrix protocol supports limited user profile fields: `avatar_url` and
`displayname`. This proposal extends the API to include custom fields, enabling users to add
free-text key:value pairs to their global profiles. This extension provides a flexible framework
for users to share additional public information.

This proposal is designed to be simple and compatible with existing clients and servers,
facilitating quick adoption. It complements, rather than replaces,
[MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769) (Extensible Profiles as
Rooms), by focusing on global profile data without the complexity of per-room profile management.

After using these custom freetext fields, the community can then propose further extensions to
standardise special fields with specific purposes, such as a user's timezone or languages, and
these proposals may choose to allow selected fields to be specified per-room via member events.

### Client-Server API Changes

- **Get a Profile Field**
  - **Endpoint**: `GET /_matrix/client/v3/profile/{userId}/{key_name}`
  - **Description**: Retrieve the value of a specified `key_name` from a user's profile.
  - **Response**:

```json
{
  "key_name": "field_value"
}
```

*Example*: Requesting `GET /_matrix/client/v3/profile/@alice:matrix.org/displayname` returns:

```json
{
  "displayname": "Alice"
}
```

- **Set a Profile Field**
  - **Endpoint**: `PUT /_matrix/client/v3/profile/{userId}/{key_name}`
  - **Description**: Set or update the value of a specified `key_name` in the user's profile.
  - **Request Body**:

```json
{
  "key_name": "new_value"
}
```

*Example*: Setting `PUT /_matrix/client/v3/profile/@alice:matrix.org/displayname` with:

```json
{
  "displayname": "Alice Wonderland"
}
```

*Note**: Setting a `null` value does not delete the key; the key remains with a `null` value.

- **Delete a Profile Field**
  - **Endpoint**: `DELETE /_matrix/client/v3/profile/{userId}/{key_name}`
  - **Description**: Remove a specified `key_name` (and its value) from the user's profile,
    if permitted by the homeserver.

- **Get All Profile Fields**
  - **Endpoint**: `GET /_matrix/client/v3/profile/{userId}`
  - **Description**: Retrieve all profile fields for a user.
  - **Response**:

```json
{
  "avatar_url": "mxc://matrix.org/MyC00lAvatar",
  "displayname": "John Doe",
  "u.Custom Field": "value1"
}
```

- **Partially Update Profile Fields**
  - **Endpoint**: `PATCH /_matrix/client/v3/profile/{userId}`
  - **Description**: Merge the provided JSON object into the user's profile,
     updating any specified keys without altering others.
  - **Request Body**:

```json
{
  "avatar_url": "mxc://matrix.org/MyNewAvatar",
  "displayname": "John Doe",
  "u.Custom Field": "new_value1"
}
```

- **Replace Profile Fields**
  - **Endpoint**: `PUT /_matrix/client/v3/profile/{userId}`
  - **Description**: Replace the entire user's profile with the provided JSON object,
     adding or updating keys and removing any absent ones.
  - **Request Body**:

```json
{
  "avatar_url": "mxc://matrix.org/MyNewAvatar",
  "displayname": "John Doe",
  "u.Custom Field": "new_value1"
}
```

**Note**: Clients are encouraged to manipulate fields individually to avoid race conditions.
However, this method allows for bulk updates when needed (e.g., bots managing multiple accounts).

### Server-Server API Changes

The federation endpoint `GET /_matrix/federation/v1/query/profile` will mirror the client-server
API changes to ensure profile information is consistent between local and federated users.

There is no method to verify the history of global profile fields over federation, so this endpoint
must only accept requests for local users on the current homeserver, and homeservers must only
request a profile from the homeserver specified in that user's MXID.

As per the current stable endpoint, it accepts an optional `field` query string parameter to
request a single field. At time of writing, the Matrix specification says:

> If no `field` was specified, the response should include the fields of the user's profile that
> can be made public, such as the display name and avatar.

Given this wording, homeservers currently already have the flexibility to decide whether some
fields are published over federation, and this proposal continues to allow this behaviour.

### Capabilities

A new capability `m.profile_fields` controls the ability to *set* custom profile fields and is
advertised on the `GET /_matrix/client/v3/capabilities` endpoint. Clients should check for this
capability before attempting to create or modify a profile field.

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

- **Behaviour**
  - **When capability missing**: Clients should assume extended profiles are supported, and that
    they can be created/written to. If a server intends to deny some (or all) changes, it SHOULD
    use the capability to advertise this to improve client experience.
  - **When `enabled` is `false`**: Clients should expect to display profiles but NOT create or
     update fields. Any attempt to do so should result in a `403 Forbidden` error. This does not
     affect `avatar_url` and `displayname` fields, which are allowed for compatibility purposes.
  - **When `enabled` is `true`**: Clients should allow users to create or update custom fields,
    except those listed in the `disallowed` array. Individual requests will receive a
    `400 Bad Request` or `403 Forbidden` response from the homeserver if server-side policies
    prevent them.

### Error Handling

Consistent error codes and messages ensure clear communication of issues:

#### **400 Bad Request**: Request exceeds limits or is malformed

- **`M_BAD_JSON`**: Malformed request.

```json
{
  "errcode": "M_BAD_JSON",
  "error": "The provided JSON is malformed."
}
```

- **`M_TOO_LARGE`**: Exceeds size limits.

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

#### **403 Forbidden**: User lacks permission

**Note:** See [MSC4170](https://github.com/matrix-org/matrix-spec-proposals/pull/4170) for more
discussion on how server policy may result in 403 errors for profile requests.

#### **404 Not Found**: Target cannot be found

- **`M_NOT_FOUND`**: Profile key does not exist.

```json
{
  "errcode": "M_NOT_FOUND",
  "error": "The requested profile key does not exist."
}
```

### Propagation of Profile Fields to Membership Events

The existing fields, `avatar_url` and `displayname`, will continue to trigger state events in each
room. These fields are replicated per-room via member events.

All other fields (unless a future proposal specifies otherwise) will **not** trigger state events
in rooms and will exist solely at the global level for storing metadata about the user.

### Key/Namespace Requirements for Custom Fields

Homeservers are not expected to enforce these namespaces, as future expansions may be unknown to
the server, but clients are expected to use the correct namespace for field creation/updates.

The *name* of each key must be a valid UTF-8 string of between one and 128 bytes.

- **Namespace `m.*`**: Reserved for fields defined in the Matrix specification. This field may have
  special entry/display requirements, so clients that do not recognise a field in this namespace
  *may* attempt to display it, but should *not* attempt to update the content.

- **Namespace `u.*`**: Reserved for user-defined custom fields. The portion of the key name after
  the `u.` defines the display name of this field (e.g. `u.Bio`). The values in this namespace must
  always be UTF-8 strings with a content not exceeding 512 bytes.

- **Namespace `tld.name.*`**: Client-specific or unstable fields use Java package naming convention.

Following this change, for example, a user could enter a "My Timezone" field manually in their
client and the client would be expected to add a `u.My Timezone` key in their profile. Clients
would be expected to treat this as a string inside the profile with no special meaning. However,
following [MSC4175](https://github.com/matrix-org/matrix-spec-proposals/pull/4175), clients would
use the unstable key `us.cloke.msc4175.tz` (or stable key `m.tz`) with the validation and
formatting required by that MSC.

### Size Limits

Whenever "bytes" are referred to as a limit, this is calculated as UTF-8 bytes, so a two-byte code
point consumes two bytes of this limit. This size would be measured before any JSON encoding.

Until a future MSC specifies otherwise:

- Each profile *must* be *at most* 64KiB (65,536 bytes) in size, as measured in Canonical JSON.
- Each key *must* be a string of *at least* one byte and it's name *must* not exceed 128 bytes.
- Each key's *value* in the `u.*` namespace *must* not exceed 512 bytes in length.
- The limit on overall profile size includes `avatar_url` and `displayname`.

### Implementation Details

- The profile data will be public by default, and compliance with GDPR and other privacy
  regulations will be enforced, particularly in terms of data deletion and retention policies.

- Custom fields will not trigger state events in rooms, maintaining account-wide metadata without
  creating state events or other moderation issues.

- Homeservers should cache remote profiles but implement strategies to minimise unintended data
  persistence (e.g. expire caches within 24 hours).

- Clients are encouraged to provide settings for users to choose the scope of users they present
  the freetext (i.e. `u.*` namespaced) fields from (e.g. none, only users on the local server,
  users in the current room, any users sharing a room with this user, all users globally) with
  defaults sensitive to their implementation's UI and intended audience. This proposal *recommends*
  clients only display profiles of users in the current room whose membership status is `join`,
  `invite`, or `knock`, and that if custom fields are always available in the UI, an option should
  be provided to hide/minimise them automatically. These recommendations are to moderation concerns
  associated with displaying information from banned or departed users.

- Clients should provide a UI for users to enter their own free-text custom fields in the `u.*`
  namespace of their own profile.

- This proposal focuses on introducing custom free-text fields in a controlled manner. Future
  extensions, such as fields with special behaviours or administrative controls, will be addressed
  in separate MSCs to allow for thorough community discussion and consideration of UI and
  moderation impacts.

## Potential Issues

Primarily ensuring uniform support across different servers and clients during the rollout phase:
we don't want users to come to expect other users will check their profile (e.g. languages) before
communicating with them unless most clients and servers support this feature.

As such, this MSC is designed to be as simple as possible to get initial functionality and data
structures implemented widely, so further extensions can be debated, implemented, and tested with
due care over time.

As this data is stored only at the global level, it won't allow users to modify fields per-room,
or track historical changes in profile fields. However, many users would struggle to track their
own data across many rooms, and publishing state events for every field change could quickly become
a heavy burden on servers and moderators.

This proposal recommends future MSCs add certain fields to per-room member events when there is
value in doing so - the current free-text fields added by this proposal are not considered to have
this value.

This proposal also does not offer a method to "broadcast" to other users or homeservers that
changes have occurred. This is intentional to keep the scope of this change narrow and maximise
compatibility with existing servers. A future proposal may wish to use an EDU (such as Presence) to
notify users and homeservers that these custom fields have been updated.

## Alternatives

An alternative approach could involve introducing a completely new API for extended profile
information. However, this may lead to increased complexity for client and server implementations.

## Security Considerations

Since profile fields are public, there are minimal security risks associated with the transmission
of sensitive information; however, users should be made aware that any information they add will be
visible to others on the federated network. Clients *should* inform them of this.

Homeservers and clients *must* comply relevant privacy regulations, particularly regarding data
deletion and retention. Profile data *should* be cleared when a user is deactivated, and while
homeservers *should* cache remote profiles, they *should* avoid caching beyond 24 hours to minimise
the risk of unintended data persistence.

To minimise the impact of abuse, clients should offer suitable defaults for the users they will
display the profile fields from. A user may *choose* to display fields from all users globally,
but *by default* profiles should only be shown when the users share the current room and the other
user is in the `join`, `invite`, or `knock` membership states.

## Unstable Prefixes

### Unstable Profile Fields

Until this proposal is stable, custom fields should use an unstable prefix:

```json
{
  "avatar_url": "mxc://matrix.org/MyC00lAvatar",
  "displayname": "John Doe",
  "uk.tcpip.msc4133.u.Custom Field": "field_value"
}
```

### Unstable Endpoints

Use unstable endpoints when the capability is not yet stable:

- **Get/Set/Delete Custom Fields**:
  - `/_matrix/client/unstable/uk.tcpip.msc4133/profile/{userId}/{key_name}`

- **Patch/Put Profile**:
  - `/_matrix/client/unstable/uk.tcpip.msc4133/profile/{userId}`

### Unstable Capability

Advertise the capability with an unstable prefix:

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

Client feature `uk.tcpip.msc4133` should be advertised on the `/_matrix/client/versions` endpoint
when the `PUT` and `PATCH` methods are accepted on the
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
