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

## Client-Server API Changes

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
  - **Description**: Set or update the value of a specified `key_name` in the user's profile,
    if permitted by the homeserver.
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
  - **Description**: Merge the provided JSON object into the user's profile, updating
    any specified keys without altering others, if permitted by the homeserver.
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
    adding or updating keys and removing any absent ones, if permitted by the homeserver.
  - **Request Body**:

```json
{
  "avatar_url": "mxc://matrix.org/MyNewAvatar",
  "displayname": "John Doe",
  "u.Custom Field": "new_value1"
}
```

**Note**: Clients are encouraged to manipulate fields individually to avoid race conditions.
However, this method allows for bulk updates when needed (e.g. bots managing multiple accounts).

## Server-Server API Changes

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

## Capabilities

A new capability `m.profile_fields` controls the ability to *set* custom profile fields and is
advertised on the `GET /_matrix/client/v3/capabilities` endpoint. Clients should check for this
capability before attempting to create or modify a profile field.

- **Capability Structure**:

```json
{
  "capabilities": {
    "m.profile_fields": {
      "enabled": true,
      "allowed": ["u.Custom Field 1", "org.example.job_title"],
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
    except those listed in the `disallowed` array, if it exists. Servers may optionally specify the
    `allowed` array to allowlist fields that users may set - if the `allowed` key is provided with
    empty content (e.g. `"allowed": []`) this also disallows the setting of any fields. If both
    `allowed` and `disallowed` keys are provided, the `disallowed` one should be ignored. Clients
    will receive `400 Bad Request` or `403 Forbidden` responses from the homeserver if server-side
    policies prevent them.

## Error Handling

Consistent error codes and messages ensure clear communication of issues:

### **400 Bad Request**: Request exceeds limits or is malformed

- **`M_BAD_JSON`**: Malformed request.

```json
{
  "errcode": "M_BAD_JSON",
  "error": "The provided JSON is malformed."
}
```

- **`M_PROFILE_TOO_LARGE`**: Exceeds total profile size limits.

```json
{
  "errcode": "M_PROFILE_TOO_LARGE",
  "error": "The profile data exceeds the maximum allowed size of 64KiB."
}
```

- **`M_KEY_TOO_LARGE`**: Exceeds individual key length limits.

```json
{
  "errcode": "M_KEY_TOO_LARGE",
  "error": "The key name exceeds the maximum allowed length of 128 bytes."
}
```

- **`M_TOO_MANY_KEYS`**: Exceeds key limits.

```json
{
  "errcode": "M_TOO_MANY_KEYS",
  "error": "The user has exceeded the maximum number of allowed keys in their profile."
}
```

### **403 Forbidden**: User lacks permission

**Note:** See [MSC4170](https://github.com/matrix-org/matrix-spec-proposals/pull/4170) for more
discussion on how server policy may result in 403 errors for profile requests.

### **404 Not Found**: Target cannot be found

- **`M_NOT_FOUND`**: Profile key does not exist.

```json
{
  "errcode": "M_NOT_FOUND",
  "error": "The requested profile key does not exist."
}
```

## Propagation of Profile Fields to Membership Events

The existing fields, `avatar_url` and `displayname`, will continue to trigger state events in each
room. These fields are replicated per-room via member events.

All other fields (unless a future proposal specifies otherwise) will **not** trigger state events
in rooms and will exist solely at the global level for storing metadata about the user.

## Key/Namespace Requirements

(Whenever "bytes" are referred to as a limit, this is calculated as UTF-8 bytes, so a two-byte code
point consumes two bytes of this limit. This size would be measured before any JSON encoding.)

Each profile *must* be *at most* 64KiB (65,536 bytes) in size, as measured in Canonical JSON, and
includes `avatar_url` and `displayname`.

Homeservers are not expected to enforce namespaces, as future expansions may be unknown to the
server, but clients are expected to use the correct namespace for field creation/updates.

Key must follow the [Common Namespaced Identifier Grammar](https://spec.matrix.org/unstable/appendices/#common-namespaced-identifier-grammar),
but with an additional `u.*` namespace for user-defined fields:

- **Namespace `m.*`**: Reserved for fields defined in the Matrix specification. This field may have
  special entry/display requirements, so clients that do not recognise a field in this namespace
  *may* attempt to display it, but should *not* attempt to update the content.

- **Namespace `u.*`**: Reserved for user-defined custom fields. The portion of the key name after
  the `u.` defines the display name of this field (e.g. `u.Bio`). The values in this namespace must
  always be UTF-8 strings with a content not exceeding 512 bytes.

- **Namespace `tld.name.*`**: Client-specific or unstable fields use Java package naming convention.

Following this change, for example, a user could enter a "My Timezone" field manually in their
client, and the client would be required to encode this as `u.my_timezone` key in their profile.
Clients would be expected to treat this as a string inside the profile with no special meaning.
However, following [MSC4175](https://github.com/matrix-org/matrix-spec-proposals/pull/4175),
clients would use the unstable key `us.cloke.msc4175.tz` (or stable key `m.tz`) following the
validation and formatting required by that MSC.

## Implementation Details

- Custom fields MUST not trigger state events in rooms; their data must not be replicated to
  `m.room.member` events unless a future proposal creates exceptions for specific fields.

- Servers SHOULD cache remote profiles for *at least* 5 minutes after retrieval; however, until
  a future proposal establishes a method for servers to notify each other of updates, it is
  *recommended* profiles be cached no longer than 15 minutes to avoid displaying stale data.
  Servers MUST not cache for longer than 24 hours to avoid unwanted data persistence.

- Clients COULD provide a UI for users to view/enter their own free-text custom fields in the `u.*`
  namespace of their own profile.

- If clients present custom fields in profiles to users, clients SHOULD provide settings to choose
  the scope of profiles they present the freetext (i.e. `u.*` namespaced) fields from, (e.g. none,
  only users on the local server, users in the current room, any users sharing a room with this
  user, all users globally) with defaults sensitive to their implementation's UI and intended
  audience. This proposal *recommends* clients only display profiles of users in the current room
  whose membership status is `join`, `invite`, or `knock`, and whose `m.room.member` event has
  *not* been redacted. If a client offers an option for custom fields to always be available in the
  UI, an option should be provided to hide/minimise them automatically.

- Servers MAY add/remove/modify fields in their own user's global profile data, whether for
  moderation purposes or for other policy reasons, e.g. to automatically populate a job title based
  on the user's organisation.

- Servers MAY suppress all extended profile fields to their users (e.g. during a go-live phase);
  however, this feature could cause confusion if some users can see fields that other users
  cannot, so should be used sparingly.

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

This proposal does not directly address reporting of user profiles over federation, but
[MSC4202](https://github.com/matrix-org/matrix-spec-proposals/pull/4202) offers a facility for
users to report offensive content to the homeserver that account belongs to. This proposal is not
dependent on [MSC4202](https://github.com/matrix-org/matrix-spec-proposals/pull/4202) but encourages
the use of moderation options to allow users to report offensive content.

## Alternatives

An alternative approach could involve introducing a completely new API for extended profile
information. However, this may lead to increased complexity for client and server implementations.

At the time of writing, Extensible Profiles as Rooms
([MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769) and variant
[MSC4201](https://github.com/matrix-org/matrix-spec-proposals/pull/4201)) is under development for
richer and more granular content and privacy controls, which this proposal does not intend to
replace - this proposal focuses on basic global profile data without the complexity of per-room
profile management.

## Security Considerations

Since profile fields are public, the server is not directly responsible for the privacy of the data;
however, clients should make users aware that any information published in their profile will be
visible to others on the federated network.

Likewise, if a server automatically publishes data in user profile fields (e.g. setting a job title
based on an organisation's internal user database) then they must have consent to do so, and users
should be made aware that data is published on their behalf.

Homeservers and clients *must* comply relevant privacy regulations, particularly regarding data
deletion and retention. Profile data *should* be cleared when a user is deactivated, and while
homeservers *should* cache remote profiles, they *should* avoid caching beyond 24 hours to minimise
the risk of unintended data persistence.

To minimise the impact of abuse, clients should offer suitable defaults for the users they will
display the profile fields from. A user may *choose* to display fields from all users globally,
but *by default* profiles should only be shown when the users share the current room and the other
user is in the `join`, `invite`, or `knock` membership states.

The proposal [MSC4202](https://github.com/matrix-org/matrix-spec-proposals/pull/4202) adds reporting
of user profiles over federation, which offers a facility for users to report offensive content to
the homeserver that account is registered on.

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
