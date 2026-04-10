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
  "requester": "@foo:origin.org",
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
      "m.tz": "America/New_York",
      "user_id": "@foo:bar.com",
    }
  ]
}
```

All profile fields (cf [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133)) should be returned here.

Search should be performed on all the profile fields too.

Field `requester` should be verified by the requested server: since the request is signed, we know that it has been sent by a specific server, so we MUST check that the
server name of the requester matches the requester server.

`requester` field is useful to be able to filter the results on the requested server directly, depending of the visibility user preference (cf next section).

When an user calls the client user search API, the server should send a federated user search request to all known servers or a subset of it. It would then receive the results and return them to the user.
Servers must not forward this request to other servers and only return results known locally. This is to avoid infinite loop between servers knowing each other.

However we have a problem here: we can't have expectation on when and even if servers will answer to the search request.

We are hence proposing some changes to the client API to accommodate the need to have a way to stream new results to the client.

### Client endpoint changes

#### New account data to control user visibility in the directory

We propose to add a new account data of type `m.user_directory` with a single `visibility` field to give the user the ability to control their visibility in the user directory.

Different values are possible :
- `hidden` : not visible to anyone
- `local` : visible only to local homeserver users
- `restricted`: visible to any user sharing a room with
- `remote`: visible to users on local and remote homeservers

If no value is provided (or it is null), the user hasn't set a preference and the server should follow the current expected behavior (visible if sharing a room in common or in public room).

Example of the content of a `m.user_directory` account data:
```json
{
    "visibility": "local"
}
```

#### POST /_matrix/client/v3/user_directory/search

#### Request
```json
{
  "limit": 10,
  "search_term": "foo",
  "search_token": "a1d29g4f73",
  "search_scope": "remote"
}
```

We propose to introduce a reactive mechanism to allow the server to stream new results to the client.

For that we introduce a `search_token` to the request coming from the response of a previous search(`search_token`).
A request containing a `search_token` will stall until new results are available to the server.
If some more results are expected to be returned, it may include another `search_token`, and hence.

`search_token` is optional within the request so proposed changes are retro-compatible.

We also propose a new `search_scope` parameter to limit the scope of a search.
Possible values are:
- `local` : only search users local to the homeserver, this must not trigger a federated search
- `restricted`: search users known to this homeserver, this must not trigger a federated search
- `remote`: on top of users known to this homeserver, it should include results coming from other homeservers via the newly introduced federated search endpoint.

This parameter is optional and default to remote.

#### Response
```json
{
  "search_token": "a1d29g4f73",
  "limited": true,
  "results": [
    {
      "avatar_url": "mxc://bar.com/foo",
      "display_name": "Foo",
      "m.tz": "America/New_York",
      "user_id": "@foo:bar.com"
    }
  ]
}
```
`search_token` :  is a unique identifier that means that more results can be retrieved by querying with this `search_token`. `limited` should be `true` when `search_token` is returned.

## Potential issues

We may have requests lost or getting timeout from intermediary network equipment, especially since we are using some kind of long polling.
We think the fact that we use a `search_token` that changes on each request allow the server to track correctly if new search results were already received by the client or not.

## Alternatives

Previous version of this MSC was using a profile field to store the visibility setting of the user, and hence this setting was visible to everyone.
By adding `requester` in the federation request, the target server is fully in control of enforcing user setting and we avoid leaking the setting.
One drawback is that we can't cache the result per target server and results should be cached per user. It feels like an acceptable performance tradeoff.

Rather than using a `search_token`, we could use a `search_id` that will be the same for all subsequent calls.
This solution is less informative about the progression of the search from the server perspective, cf `Potential issues` section.

## Security considerations

### Sensitive Data Exposure

A malicious server could list all user matrix ids that are defined in `remote` or `restricted`.

#### Data Exposure Mitigation recommendations

The federation search endpoint should be rate limited.

We recommend to not answer for `search_term` with less than 3 characters like "a" or "at", except when an exact match is available.

#### Trust & Safety recommendations

We recommend to log requests (or at least their count) from each server in order to be able to identify and ban the malicious servers who are trying to scrap all visible (including `restricted` ones) users profiles of the federation.

Before, a server needed to join a room to list the users in a room (`restricted`). This scenario is logged in the room state.
Now with this change, it is possible to list all the restricted users from other servers with no trace left at the protocol level.


## Unstable prefix

`fr.tchap.user_directory.visibility` should be used as an unstable identifier for the profile field.

`/_matrix/federation/unstable/fr.tchap/user_directory/search` should be used as an unstable federation endpoint.


## Dependencies

This MSC references [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133) but does not depend on it.

