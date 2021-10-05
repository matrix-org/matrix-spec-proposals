# MSC3429: Individual room preview API

Presently in Matrix it's possible to get (public) information about a user using the
[`GET /profile/@user:example.org`](https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-r0-profile-userid)
endpoint, but a similar approach doesn't really exist for rooms.

If the room happens to be public in the room directory, the client could scrape the directory until
it finds the room, though this can mean parsing thousands of rooms or giving up after some hundred
or so pages.

It should be possible for clients to render room references (matrix.to links, `matrix:` links, etc)
as rich content, similar to how Discord invite links work:

![discord-invite-links](./images/3429-discord-invite-example.png)

## Proposal

Using [MSC3173](https://github.com/matrix-org/matrix-doc/pull/3173)'s definition of stripped state
visibility, we introduce a new `GET /_matrix/client/v1/rooms/{id_or_alias}/preview` endpoint which
returns an object similar to the [`GET /publicRooms`](https://matrix.org/docs/spec/client_server/r0.6.1#get-matrix-client-r0-publicrooms)
endpoint with the stripped state:

```json5
{
  // Fields copied from /publicRooms
  "room_id": "!id:example.org",
  "num_joined_members": 42,

  // The stripped state for the room
  "stripped_state_events": [
    {"type": "m.room.name", "state_key": "", "content": {"name": "My Public Room"}},
    // ... etc
  ]
}
```

The stripped state definition does not currently recommend exposing the `m.room.guest_access` or
`m.room.history_visibility` state events, which are covered by fields on `/publicRooms`, so this
proposal changes that to include them. The other details about the room, such as the room create
event (to detect room type), encryption state, topic, avatar, name, etc are already covered.

The endpoint should not be rate limited and does not require authentication, to mirror the semantics
of `/publicRooms`.

If authentication is not provided, the caller is limited to rooms which are fully public (public
join rules, history available to everyone, etc). If authentication is provided, the server must use
that to determine if the user has access to see the room state (eg: joined already, is a restricted
room they haven't joined yet, etc). These definitions are the same as in [MSC3173](https://github.com/matrix-org/matrix-doc/pull/3173).

If an alias was provided and cannot be resolved to a room, a `404 M_NOT_FOUND` error is returned.

If the room ID is not known to the server, the request goes over federation as
`/_matrix/federation/v1/room/{id}/preview`. To assist with routing to a potential server, the
client-server `/preview` endpoint can take `via` query parameters, just like matrix.to or `matrix:`
URLs can. If the requesting server doesn't have a user which could request the room state, or the
room is not known to the remote server, then a `404 M_NOT_FOUND` error is returned and passed
through to the client. In practice, the requesting server should always be able to tell whether or
not it'll have enough permission to expose the state, but might not have persisted the stripped state
from an invite sent to a local user, thus needing to re-request it. The requesting server is still
required to validate that the user making the call has appropriate permission to access the stripped
state for the room.

There are no particular caching recommendations, however given the information about a room rarely
changes, the suggestion from the author is to use the same caching semantics as the room directory.
If a room becomes non-public, it should be evicted from the cache.

## Alternatives

There are a few possible alternatives to this which are mainly focused around the approach. All are
considered a bit sub-optimal for the reasons explained within.

### Add a filter option to `/publicRooms`

This feels like it overloads the room directory's purpose, and doesn't necessarily solve the issue of
a room being publicly accessible by link but (un)intentionally not being listed in the public room
directory for a given server. Further, this largely relies on the client knowing which server's directory
to query, which is unlikely to be known prior to the request.

### Use the media repo's `/preview_url` endpoint

While certainly possible, the media repo for some server setups would need to gain knowledge of rooms,
and still need to make federated requests to get information it is missing. It ultimately ends up needing
the information provided by the proposed endpoint, which it is certainly welcome to do as an added feature.

### Rely on a matrix.to-provided API

If matrix.to were to offer an API into this, it'd also need to access the same information provided by
this proposal. In fact, the public view for matrix.to already loops through the room directory to try
and resolve a room preview where an API like this could instead be used.

## Security considerations

This new endpoint exposes public information about a room that not everyone is comfortable with sharing.
The endpoint is most similar to `GET /profile` in how it works, and the same server-side semantics can
be applied (such as analogous options to Synapse's `require_auth_for_profile_requests` or
`limit_profile_requests_to_users_who_share_rooms` config options). Similarly, the server might want to
refuse responses over federation (`allow_public_rooms_over_federation` in Synapse).

Server implementations are encouraged to add or reuse config options to control the behaviour of these
new endpoints, specifically for purposes of protecting rooms. Some such options may be to reuse the
existing room directory config options and introduce a new one to limit `/preview` requests to rooms
in that room directory. All of this privacy-preserving behaviour is considered legal under this proposal.

The endpoint is not rate limited to match its counterparts being not rate limited in the specification.
Servers are still encouraged to apply an amount of rate limiting, though the harshness of the typical
recommendation within the spec does not apply to these endpoints.

## Unstable prefix

While this MSC is not considered stable, the endpoints become:

* `/_matrix/client/unstable/org.matrix.msc3429/rooms/{id_or_alias}/preview`
* `/_matrix/federation/unstable/org.matrix.msc3429/room/{id}/preview`

