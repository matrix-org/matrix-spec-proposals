# MSC4258: Federated User Directory

Currently user search can only be done locally, which would at best get a list of all users known to the server.

This proposal aims at introducing a federation endpoint allowing servers to broadcast the search to the current federating servers and get results among all their known users.

Improvement of the client API is also proposed to accommodate the fact that results will arrive asynchronously and to allow users to manage their visibility on search results. 


## Proposal

### Federation endpoint

We first propose a new federation endpoint similar to the [current client API](https://spec.matrix.org/v1.12/client-server-api#post_matrixclientv3user_directorysearch).
It would be authenticated and rate limited.

#### `POST /_matrix/federation/v3/user_directory/search`

#### Request
```json
{
  "limit": 10,
  "search_term": "foo"
}
```

#### Response
```json
{
  "limited": false,
  "results": [
    {
      "avatar_url": "mxc://bar.com/foo",
      "display_name": "Foo",
      "m.user_directory.visibility": "local",
      "user_id": "@foo:bar.com"
    }
  ]
}
```

All profile fields (cf [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133)) should be returned here.

When an user calls the client user search API, the server should send a federated user search request to all known servers. It would then receive the results and return them to the user.
Servers must not forward this request to other servers and only return results known locally. This is to avoid infinite loop between servers knowing each other.

However we have a problem here: we can't have expectation on when and even if servers will answer to the search request.

We are hence proposing some changes to the client API to accommodate the need to have a way to stream new results to the client.

Note that `m.user_directory.visibility` is defined further down this proposal.

### Client endpoint changes

We propose to introduce a reactive mechanism to allow the server to stream new results to the client.

#### POST /_matrix/client/v3/user_directory/search 

#### Request
```json
{
  "limit": 10,
  "search_term": "foo",
  "search_token": "a1d29g4f73"
}
```

For that we introduce a `search_token` to the request coming from the response of a previous search(`search_token`). A request containing a `search_token` will stall until new results are available to the server. If some more results are expected to be returned, it may include another `search_token`, and hence.

`search_token` is optional within the request so proposed changes are retro-compatible.

#### Response
```json
{
  "search_token": "a1d29g4f73",
  "limited": true,
  "results": [
    {
      "avatar_url": "mxc://bar.com/foo",
      "display_name": "Foo",
      "m.user_directory.visibility": "local",
      "user_id": "@foo:bar.com"
    }
  ]
}
```
`search_token` :  is a unique identifier that means that more results can be retrieved by querying with this `search_token`. `limited` should be `true` when `search_token` is returned.

#### New profile field to control user visibility in the directory

We propose to add a new field in the profile (MSC4133) `m.user_directory.visibility` to give the user the ability to control their visibility in the user directory.

Different values are possible :
- `hidden` : not visible to anyone
- `local` : visible only to local homeserver users
- `restricted`: visible to any user sharing a room with
- `remote` (or federated or public ?): visible to users on local and remote homeservers

If no value is provided (or it is null), the user hasn't set a preference and the server should follow the current expected behavior (visible if sharing a room in common or in public room).

```json
{
    "avatar_url": "…", 
    "displayname": "…",
    "m.user_directory.visibility": "local"
}
```

## Potential issues

We may have requests lost or getting timeout from intermediary network equipment, especially since we are using some kind of long polling.
We think the fact that we use a `search_token` that changes on each request allow the server to track correctly if new search results were already received by the client or not.

## Alternatives

We first thought about using an account data, however it has a big caveat: remote servers can't access it, hence remote servers will not be able to honor the visibility when trying to return remote users that are already visible locally to them.

Rather than using a `search_token`, we could use a `search_id` that will be the same for all subsequent calls.
This solution is less informative about the progression of the search from the server perspective, cf `Potential issues` section.

## Security considerations

### Sensitive Data Exposure

A malicious server could list all user matrix ids that are defined in `remote` or `restricted`.

#### Data Exposure Mitigation recommendations

The federation search endpoint should be rate limited.

We recommend to not answer for `search_term` with less than 3 characters like "a" or "at".

#### Trust & Safety recommendations

We recommend to log requests (or at least their count) from each server in order to be able to identify and ban the malicious servers who are trying to scrap all visible (including `restricted` ones) users profiles of the federation.

Before, a server needed to join a room to list the users in a room (`restricted`). This scenario is logged in the room state.
Now with this change, it is possible to list all the restricted users from other servers with no trace left at the protocol level.


## Unstable prefix

`fr.tchap.user_directory.visibility` should be used as an unstable identifier for the profile field.

`/_matrix/federation/unstable/fr.tchap/user_directory/search` should be used as an unstable federation endpoint.


## Dependencies

This MSC builds on [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133)
