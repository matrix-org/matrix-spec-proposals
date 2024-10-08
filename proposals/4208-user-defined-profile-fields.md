# MSC4208: Adding User-Defined Custom Fields to User Global Profiles

*This proposal depends on [MSC4133: Extending User Profile API](https://github.com/matrix-org/matrix-spec-proposals/pull/4133).
It introduces user-defined custom fields in the `u.*` namespace for user profiles.*

## Proposal

This proposal aims to enable users to add arbitrary custom key:value pairs to their global user
profiles within the Matrix ecosystem. By leveraging the extended profile API introduced in
[MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133), users can enrich their
profiles with additional public information such as preferred languages, organisational roles, or
other relevant details.

### Key/Namespace Requirements

As per [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133), the profile API is
extended to allow additional fields beyond `avatar_url` and `displayname`. This MSC defines the use
of the `u.*` namespace for user-defined custom fields:

- **Namespace `u.*`**: Reserved for user-defined custom fields. The portion of the key name after
  the `u.` defines the display name of this field (e.g., `u.bio`). The values in this namespace
  must always be UTF-8 strings with content not exceeding 512 bytes.

### Client-Server API Changes

#### Setting a Custom Profile Field

To set or update a custom profile field, clients can use the `PUT` endpoint defined in
[MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133):

- **Endpoint**: `PUT /_matrix/client/v3/profile/{userId}/{key_name}`
- **Description**: Set or update the value of a specified `key_name` in the user's profile,
  if permitted by the homeserver.
- **Request Body**:

```json
{
  "u.key_name": "new_value"
}
```

*Example*: Setting the custom field `u.bio` for user `@alice:matrix.org`:

```http
PUT /_matrix/client/v3/profile/@alice:matrix.org/u.bio
```

With body:

```json
{
  "u.bio": "I love Matrix!"
}
```

#### Retrieving Custom Profile Fields

To retrieve custom fields from a user's profile, clients use the `GET` endpoint:

- **Endpoint**: `GET /_matrix/client/v3/profile/{userId}/{key_name}`
- **Description**: Retrieve the value of a specified `key_name` from a user's profile.
- **Response**:

```json
{
  "key_name": "field_value"
}
```

*Example*: Retrieving the custom field `u.bio` for user `@alice:matrix.org`:

```http
GET /_matrix/client/v3/profile/@alice:matrix.org/u.bio
```

Response:

```json
{
  "u.bio": "I love Matrix!"
}
```

#### Deleting a Custom Profile Field

To delete a custom profile field:

- **Endpoint**: `DELETE /_matrix/client/v3/profile/{userId}/{key_name}`
- **Description**: Remove a specified `key_name` and its value from the user's profile,
  if permitted by the homeserver.

#### Retrieving All Profile Fields

Clients can retrieve all profile fields for a user, including custom fields:

- **Endpoint**: `GET /_matrix/client/v3/profile/{userId}`
- **Description**: Retrieve all profile fields for a user.
- **Response**:

```json
{
  "avatar_url": "mxc://matrix.org/MyC00lAvatar",
  "displayname": "Alice",
  "u.bio": "I love Matrix!",
  "u.location": "London"
}
```

### Capabilities

A new capability `m.custom_profile_fields` is introduced to control the ability to set custom
profile fields. It is advertised on the `GET /_matrix/client/v3/capabilities` endpoint. Clients
should check for this capability before attempting to create or modify custom fields.

- **Capability Structure**:

```json
{
  "capabilities": {
    "m.custom_profile_fields": {
      "enabled": true
    }
  }
}
```

- **Behaviour**:
  - **When capability is missing**: Clients should assume that custom profile fields are not
    supported and refrain from providing options to set them.

  - **When `enabled` is `false`**: Clients should not allow users to create or update custom
    fields. Any attempt to do so should result in a `403 Forbidden` error.

  - **When `enabled` is `true`**: Clients should allow users to create or update custom fields in
    the `u.*` namespace, except those listed in the `disallowed` array.

### Error Handling

Consistent error codes and messages ensure clear communication of issues. Homeservers should use
the following error codes:

- **`M_KEY_NOT_ALLOWED`**: The specified key is not allowed to be set.

```json
{
  "errcode": "M_KEY_NOT_ALLOWED",
  "error": "The profile key 'u.bio' is not allowed to be set."
}
```

- **`M_TOO_LARGE`**: The value provided exceeds the maximum allowed length.

```json
{
  "errcode": "M_TOO_LARGE",
  "error": "The value exceeds the maximum allowed length of 512 bytes."
}
```

### Client Considerations

- Clients SHOULD provide a UI for users to view and edit their own custom fields in the `u.*`
  namespace.

- When displaying other users' profiles, clients SHOULD retrieve and display custom fields in the
  `u.*` namespace.

- Clients SHOULD be cautious about the amount of data displayed and provide options to limit or
  filter the display of custom fields.

### Server Considerations

- Homeservers MAY impose limits on the number of custom fields, whether for storage reasons or to
  ensure the total profile size remains under 64KiB as defined in [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133).

- Homeservers MAY validate that keys in the `u.*` namespace conform to the required format and
  enforce size limits on values.

- Homeservers MAY restrict certain keys or values based on server policies.

## Potential Issues

- **Privacy Concerns**: Users need to be aware that custom profile fields are public and visible to
  anyone who can access their profile.

- **Abuse Potential**: As with any user-generated content, there is potential for misuse. Servers
  and clients need to be prepared to handle offensive or inappropriate content.

- **Interoperability**: Until widespread adoption occurs, not all clients may support displaying
  custom fields, leading to inconsistent user experiences.

## Security Considerations

- **Content Moderation**: Homeservers SHOULD provide mechanisms to report and handle abusive
  content in custom profile fields. [MSC4202](https://github.com/matrix-org/matrix-spec-proposals/pull/4202)
  provides an example of one such mechanism.

- **Data Protection**: Homeservers SHOULD ensure compliance with data protection regulations,
  especially regarding user consent and data retention.

## Unstable Prefixes

### Unstable Namespace

Until this proposal is stabilised, custom fields should use an unstable prefix in their keys:

- **Namespace `uk.tcpip.msc4208.u.*`**: For example, `uk.tcpip.msc4208.u.bio`.

### Unstable Capability

The capability should be advertised with an unstable prefix:

```json
{
  "capabilities": {
    "uk.tcpip.msc4208.custom_profile_fields": {
      "enabled": true,
      "allowed": ["uk.tcpip.msc4208.u.*"]
    }
  }
}
```

## Dependencies

This proposal depends on [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133),
which introduces the extended profile API to allow additional fields in user profiles.
