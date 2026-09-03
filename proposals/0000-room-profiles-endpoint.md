# MSC0000: Room profiles endpoint

This MSC builds on the profile updates over legacy ([MSC4429](https://github.com/matrix-org/matrix-spec-proposals/pull/4429))
and sliding sync ([MSC4262](https://github.com/matrix-org/matrix-spec-proposals/pull/4262)) MSC's.

This MSC aims to provide a solution for Matrix clients to fetch user profile data from Matrix servers.
Currently, there are multiple ways a client may end up receiving profile data from the backend.

1) By fetching a full profile or individual fields using `GET /_matrix/client/v3/profile/{userId}`
  or `GET /_matrix/client/v3/profile/{userId}/{keyName}`.
2) From legacy and sliding sync responses ([MSC4429](https://github.com/matrix-org/matrix-spec-proposals/pull/4429),
  [MSC4262](https://github.com/matrix-org/matrix-spec-proposals/pull/4262)).

Additionally, display names and avatar urls may be discovered by clients using other methods. For 
this MSC, we're assuming the client would also need to know about other custom profile fields.

The first option above is clear - the client knows it needs a profile, and it fetches it. Or it might
just want a single field, and can fetch it when needed. However, this method is inefficient if the
client needs to fetch multiple profiles.

The second option, profile data down sync streams works for many cases. As per the MSC's involved,
clients will receive profile data in roughly the following ways:

* For initial sync, full profiles always for members in the rooms the sync relates to.
* For incremental sync:
  * Updates to profile fields.
  * When lazy loading, full profiles if the user has events in the sync timeline.

What is not covered by profile updates via sync streams is the following situation:

* Alice, on a lazy loading client, syncs
* Alice joins a room
* Alice does a lazy loading incremental sync

In this situation, Alice would receive the full profiles of any users who had timeline events in the
lazy loading sync response. Alice's client would not receive profile information regarding users in
the joined room that the client didn't know about before, unless those users had events in the timeline.

## Proposal

This MSC proposes two new endpoints.

Just as we already have a `GET /_matrix/client/v3/rooms/{roomId}/members` to paginate through room members,
a new endpoint `GET /_matrix/client/v3/rooms/{roomId}/profiles` would allow paginating through profiles
of a room.

Additionally, as clients may need to efficiently fetch certain profiles across multiple rooms, a new
endpoint `POST /_matrix/client/v3/profiles/query` is suggested for this purpose.

These endpoints would help clients efficiently fetch profiles for things like the room members list,
when operating in lazy loading mode, for example to show user status of room members.

### Client-Server API Changes

#### Fetch room profiles

- **Endpoint**: `GET /_matrix/client/v3/rooms/{roomId}/profiles`
- **Description**: Retrieve room member user profiles.
- **Pagination**: *Yes TODO What mechanism?*
- **Parameters**:
  - `fields` - Request only specific fields, comma separated list, for example:

    `GET /_matrix/client/v3/rooms/{roomId}/profiles?fields=m.status,m.tz`
- **Response**:

  ```json
  {
    "@alice:example.com": {
      "displayname": "Alice",
      "m.status": {
        "emoji": "💬",
        "text": "In a meeting"
      }
    },
    "@bob:domain.tld": {
      "displayname": "Bob"
    }
  }
  ```

TODO: error codes

#### Query profiles

- **Endpoint**: `POST /_matrix/client/v3/profiles/query`
- **Description**: Query a list of profiles from the server.
- **Pagination**: No
- **Request body**: Request body should contain a list of profiles, and optionally fields, to query.

  * `users` - List of user IDs to query for. The maximum amount of profiles the homeserver should
    accept to be requested in one go should be limited to 100.
  * `fields` - (Optional) Request only specific fields, comma separated list. If not
    given, all profile fields will be returned.

    Example request body:
    
  ```json
  {
    "users": [
      "@alice:example.com",
      "@bob:domain.tld"
    ],
    "fields": "m.status,m.tz"
  }
  ```
- **Response**:

  ```json
  {
    "@alice:example.com": {
      "displayname": "Alice",
      "m.status": {
        "emoji": "💬",
        "text": "In a meeting"
      }
    },
    "@bob:domain.tld": {
      "displayname": "Bob"
    }
  }
  ```

The homeserver MUST check that the user has access to view the profile and/or profile
fields. While at the time of writing this MSC profile fields are considered public
information, this may change with future MSC.

TODO: error codes

### Homeserver implementation details

Fetching profiles via the new endpoints should never trigger lookups to fetch profiles from other
homeservers. The response should be calculated from known profiles locally. It should be assumed that
remote servers push profile changes over, so they would already be available
(see [MSC4259](https://github.com/matrix-org/matrix-spec-proposals/pull/4259) as one possibility).

## Potential issues

TBD

## Alternatives

### Provide full profiles in sync based on the user joining a room

It would be possible to solve missing profiles in clients for users joining new rooms in lazy loading mode
by just delivering all the room member profiles to the client every time the syncing user joins a new room.
This solution is not very elegant and would potentially cause a massive amount of traffic to clients, when
the user joins a new large room. This solution does not give the control to the client on what users
profiles they want to fetch. It also doesn't cover for any other cases there might be in the future for
"I want to fetch all the profiles of a particular room". This kind of use case might not even involve syncing.

### Extend the room members endpoint to return profiles

Extending the `GET /_matrix/client/v3/rooms/{roomId}/members` endpoint, which clients might use
to fetch the full room membership list to return profiles would ensure clients don't need to
make an extra endpoint call. This could, for example be, a new `profiles` top level key, to
avoid polluting the returned `ClientEvent` objects in `chunk`.

This endpoint is paginated based on the sync endpoint token, and thus would not serve other use cases
outside of syncing clients.

### Extend the room joined members endpoint to return profiles

Extending `GET /_matrix/client/v3/rooms/{roomId}/joined_members` to return more profile information
than just `display_name` and `avatar_url`, would allow for clients to use this endpoint to fetch
profile information. However, this endpoint is not paginated, and thus could produce extremely large
responses for large rooms, as the data stored in profiles may outweigh the current display names
and avatar urls by many factors.

## Security considerations

None foreseen at this moment.

## Unstable prefix

While this MSC is unstable, the endpoints are:

* `GET /_matrix/client/unstable/org.matrix.mscxxxx/rooms/{roomId}/profiles`
* `POST /_matrix/client/unstable/org.matrix.mscxxxx/profiles/query`

Support for these endpoints MUST be advertised via the `org.matrix.mscxxxx` flag in `/_matrix/client/versions`.

## Dependencies

This MSC builds on [MSC4429](https://github.com/matrix-org/matrix-spec-proposals/pull/4429) and
[MSC4262](https://github.com/matrix-org/matrix-spec-proposals/pull/4262) (which at the time of writing
have not yet been accepted into the spec).
