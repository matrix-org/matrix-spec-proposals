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

This proposal does not seek to enforce the content or usage of these fields but rather to add a
framework for users to have extra data that can be further clarified and extended in the future as
community usage of these fields grows.

Homeservers could disable the ability for users to update these fields, or require a specific list
of fields, but the intention of this proposal is that users will be presented with a form to enter
their own free-text fields and values. After using these very flexible fields, the community may
opt to request a further extension to promote one or more fields to the "root" level of the profile
and have them replicated per-room via member events.

### Client-Server API Changes

1. **GET `/_matrix/client/v3/profile/{userId}/{key_name}`**: This endpoint will replace the
   existing profile endpoints. It will return the value of the specified `key_name`:

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

2. **PUT `/_matrix/client/v3/profile/{userId}/{key_name}`**: This endpoint will set the value of
   the specified `key_name`:

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

3. **GET `/_matrix/client/v3/profile/{userId}/`**: This endpoint will retrieve all profile fields:

    ```json
    {
      "avatar_url": "mxc://matrix.org/MyC00lAvatar",
      "displayname": "John Doe",
      "custom_field1": "value1",
      "custom_field2": ["value2", "value3"]
    }
    ```

4. **POST `/_matrix/client/v3/profile/{userId}`**: This endpoint will accept a complete JSON object
   to replace the entire profile:

    ```json
    {
      "avatar_url": "mxc://matrix.org/MyNewAvatar",
      "displayname": "John Doe",
      "custom_field1": "new_value1",
      "custom_field2": ["new_value2", "new_value3"]
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

### Server-Server API Changes

1. **GET `/_matrix/federation/v1/query/profile/{userId}/{key_name}`** will mirror the client-server
   API changes to ensure profile information is consistently available across the federated network.

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

## Alternatives

An alternative could be to allow for more specific endpoint modifications or to introduce a
completely new API specifically for extended information. However, these approaches could lead to
more significant changes to the existing API and higher complexity for client developers.

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
allows extra custom fields to be published in a user's profile, however as this field has a special
purpose, an unstable prefix should be used on the object until this proposal has entered the API as
stable:

```json
{
    "avatar_url": "mxc://matrix.org/MyC00lAvatar",
    "displayname": "John Doe",
    "uk.tcpip.msc4133.custom_field1": "field_value",
    "uk.tcpip.msc4133.custom_field2": ["one value", "another value"]
}
```

The new endpoints would be on the
`/_matrix/client/unstable/uk.tcpip.msc4133/profile/{userId}/{key_name}` unstable version, before
promoting to `/_matrix/client/v3/profile/{userId}/{key_name}` when this is stable.
