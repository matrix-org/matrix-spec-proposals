# MSC4133: Extending User Profile API with Key:Value Pairs

*This proposal aims to enhance the usability and richness of user profiles within the Matrix
ecosystem by introducing additional, customisable fields. This feature will facilitate the sharing
of more diverse user-defined public information across the federated network. The primary goal is
to enable users to publish a wide variety of possible information, such as preferred communication
languages, pronouns, public-facing organisation roles, or other relevant public details, thereby
enriching the user interaction experience without impacting existing functionalities.*

## Proposal

The Matrix protocol's current user profile structure supports very limited fields (`displayname`
and `avatar_url`). This proposal suggests expanding this structure to include custom fields,
allowing for a more versatile user profile.

This proposal is designed to complement rather than replace
[MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769) (Extensible profiles as
rooms). While [MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769) offers a more
complex solution for extensible profiles, this proposal focuses on enabling the storage of small,
arbitrary key:value pairs at the global level.

This proposal does not seek to enforce the content or usage of these fields but rather to add a
framework for users to have extra data that can be further clarified and extended in the future as
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
   (and associated value) from the profile, if permitted by the homeserver.

4. **GET `/_matrix/client/v3/profile/{userId}/`**: This endpoint will retrieve all profile fields:

    ```json
    {
      "avatar_url": "mxc://matrix.org/MyC00lAvatar",
      "displayname": "John Doe",
      "custom_field1": "value1",
      "custom_field2": ["value2", "value3"]
    }
    ```

5. **POST `/_matrix/client/v3/profile/{userId}`**: This endpoint will accept a complete JSON object
   to replace the entire profile:

    ```json
    {
      "avatar_url": "mxc://matrix.org/MyNewAvatar",
      "displayname": "John Doe",
      "custom_field1": "new_value1",
      "custom_field2": ["new_value2", "new_value3"]
    }
    ```

### Server-Server API Changes

1. **GET `/_matrix/federation/v1/query/profile/{userId}/{key_name}`** will mirror the client-server
   API changes to ensure profile information is consistently available across the federated network.

### Capabilities

A new capability `m.set_profile_fields` will be introduced to control the ability to set custom
profile fields. The client should assume setting fields is allowed when this capability is missing.

Example capability object:

```json
{
  "capabilities": {
    "m.set_profile_fields": {
      "enabled": false
    }
  }
}
```

### Distinction Between Existing and Custom Fields

The existing fields, `avatar_url` and `displayname`, will continue to trigger state events in each
room. These fields are replicated per-room via member events. Custom fields, however, will **not**
trigger state events in rooms. They will exist solely at the global level and are intended for
storing metadata about the user that does not need to be replicated in each room.

- **avatar_url** and **displayname**: Changes to these fields will generate state events in all
  rooms the user is a member of.
- **Custom fields**: These are stored in the user's global profile and do not generate state events
  in rooms.

### Key/Namespace Requirements for Custom Fields

The namespace for field names is defined as follows:

- The namespace `m.*` is reserved for fields defined in the Matrix specification. Clients should
  ignore any fields in this namespace that they don't understand, as this field may have special
  entry/display requirements that are defined in the Matrix specification.
- The namespace `u.*` is reserved for user-defined fields. The portion of the string after the `u.`
  is defined the display name of this field.

For example, if a future MSC were to add a field for user pronouns (not included in this MSC) it
might become `m.pronouns` after entering the spec, but during the unstable process it might be
`org.matrix.msc9876.pronouns`. If the field did not exist in the Matrix spec at all, a user might
add a "My Pronouns" field in their client which would be added to their profile as `u.My Pronouns`.

### Size Limit

The name of a field must not exceed 255 bytes.

To ensure efficient handling and storage of profile data, the entire user profile JSON object
cannot exceed 64KiB. This follows the same size limit as events. Homeservers are allowed to limit
the fields (or content) that their local users can set. However, the only limit they should impose
on remote users is that the entire profile JSON block should not be larger than 64KiB.

The content of a field can be any valid JSON type, as long as the total size of the user profile
does not exceed 64KiB.

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
implemented, and tested over time in the future.

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

## Unstable prefix

The [current Matrix specification](https://spec.matrix.org/v1.10/#profiles) technically already
allows extra custom fields to be published in a user's profile, however as this proposal introduces
additional requirements and allows custom user-defined fields, an unstable prefix should be used on
these fields until this proposal has entered the API as stable:

```json
{
    "avatar_url": "mxc://matrix.org/MyC00lAvatar",
    "displayname": "John Doe",
    "uk.tcpip.msc4133.u.custom_field1": "field_value",
    "uk.tcpip.msc4133.u.custom_field2": ["one value", "another value"]
}
```

**Note:** This example includes the `u.*` namespace to identify custom user-defined fields.

The new endpoints would be on the
`/_matrix/client/unstable/uk.tcpip.msc4133/profile/{userId}/{key_name}` unstable version, before
promoting to `/_matrix/client/v3/profile/{userId}/{key_name}` when this is stable.

Likewise, the client capability `m.set_profile_fields` should use this custom prefix until stable:

```json
{
  "capabilities": {
    "uk.tcpip.msc4133.set_profile_fields": {
      "enabled": false
    }
  }
}
```
