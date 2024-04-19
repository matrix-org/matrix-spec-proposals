# MSC4133: Extending User Profile API with Key:Value Pairs

*This proposal aims to enhance the usability and richness of user profiles within the Matrix ecosystem by
introducing additional, customizable key:value pairs. This feature will facilitate the sharing of more
diverse user-defined public information across the federated network. The primary goal is to enable users to
publish a wide variety of possible information, such as preferred communication languages, pronouns,
public-facing organisation roles, or other relevant public details, thereby enriching the user interaction
experience without impacting existing functionalities.*

## Proposal

The Matrix protocol's current user profile structure supports very limited fields (`displayname` and
`avatar_url`). This proposal suggests expanding this structure to include an `extended` object capable of
storing arbitrary key:value pairs, thus allowing for a more versatile user profile.

### Client-Server API Changes

1. **GET `/_matrix/client/v3/profile/{userId}`**: This endpoint will be extended to include an `extended`
   field in the JSON response:

    ```json
    {
      "avatar_url": "mxc://matrix.org/MyC00lAvatar",
      "displayname": "John Doe",
      "extended": {
        "field_name": "field_value",
        "field_2": ["one value", "another value"]
      }
    }
    ```

2. **GET `/_matrix/client/v3/profile/{userId}/extended`** will retrieve only the `extended` object. To ensure
   backward compatibility, it should *always* return an object when this user can update an extended profile,
   and return a 403 or 404 error when the server either will not allow or does not support them.

3. **PUT `/_matrix/client/v3/profile/{userId}/extended`** will accept a JSON object to replace the entire
   `extended` object, simplifying data management by allowing bulk updates instead of individual key
   modifications:

    ```json
    {
      "extended": {
        "new_field": "new_value",
        "new_field_2": ["value_one", "value_two"]
      }
    }
    ```

### Server-Server API Changes

1. **GET `/_matrix/federation/v1/query/profile`** will mirror the client-server API changes to ensure
   extended profile information is consistently available across the federated network.

### Implementation Details

- This feature will be implemented as optional but recommended, enabling a smooth transition and minimal
  disruption to existing deployments.
- The extended profile data will be public by default, and compliance with GDPR and other privacy regulations
  will be enforced, particularly in terms of data deletion and retention policies.

## Potential Issues

Initial challenges are primarily ensuring uniform support for the `extended` field across different servers
and clients during the rollout phase: users may come to expect that other users will check their supported
languages before communicating with them, but the sender's server does not support extended profiles.

As such, this MSC is designed to be as simple as possible to get initial functionality and data structures
implemented widely in both clients and servers, so further extensions can be debated, implemented, and tested
over time in the future.

## Alternatives

An alternative could be to allow for more specific endpoint modifications or to introduce a completely new
API specifically for extended information. However, these approaches could lead to more significant changes
to the existing API and higher complexity for client developers.

## Security Considerations

Since the `extended` data is public, there are minimal security risks associated with the transmission of
sensitive information; however, it is critical to ensure that all data handled through these endpoints
complies with GDPR and other privacy regulations, particularly in the event of user data deletion.

It is crucial to ensure that clients inform users this data will be public, does not include sensitive
personal information, and complies with legal frameworks such as GDPR. Homeservers will be encouraged to
implement data caching strategies that do not exceed 24 hours to minimise the risk of unintended data
persistence.

## Unstable prefix

Until this proposal is accepted and finalized within the Matrix specification, implementers are encouraged to
use the `/unstable` prefix (see [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324)) for endpoints
and a feature flag to manage client support.
