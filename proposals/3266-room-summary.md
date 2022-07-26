# MSC3266: Room Summary API

Quite a few clients and tools have a need preview a room:

- A client may want to show the room in the roomlist, when showing a space.
- matrix.to may want to show avatar and name of a room.
- Nextcloud may want to list the names and avatars of your `/joined_rooms` when
  asking where to share the media.
- A client may want to preview a room, when hovering a room alias, id or after
  clicking on it.
- A client may want to preview a room, when the user is trying to knock on it or
  to show pending knocks.
- A traveller bot may use that to show a room summary on demand without actually
  keeping the whole room state around and having to subscribe to /sync (or
  using the appservice API).
- A client can use this to knock on a room instead of joining it when the user
    tries to join my room alias or link.

There are a few ways to request a room summary, but they only support some of
the use cases. The [spaces hierarchy API](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv1roomsroomidhierarchy) only provides
limited control over what rooms to summarize and returns a lot more data than
necessary.  `{roomid}/initialSync` and `{roomid}/state/{event_type}` don't work
over federation and are much heavier than necessary or need a lot of http calls
for each room.

## Proposal

A new client-server API, which allows you to fetch a summary of a room by id or
alias, and a corresponding server-server API to fetch a summary over federation.

### Client-Server API

The API returns the summary of the specified room, if the room could be found
and the client should be able to view its contents according to the same rules as the
[`/hierarchy`](https://spec.matrix.org/v1.3/client-server-api/#server-behaviour-19)
endpoint. This is generally described as being a "potential joiner", which
includes rules such as being a member of a room that allows joining a
[`restricted`](https://spec.matrix.org/v1.3/client-server-api/#restricted-rooms),
the room being
[knockable](https://spec.matrix.org/v1.3/client-server-api/#knocking-on-rooms),
public or you already being a member. For unauthenticated requests a response
should only be returned if the room is publicly accessible.

A request could look like this:

```
GET /_matrix/client/v1/summary/{roomIdOrAlias}?
    via=matrix.org&
    via=neko.dev
```

(This is not under `/rooms`, because it can be used with an alias.

- `roomIdOrAlias` can be the roomid or an alias to a room.
- `via` are servers that should be tried to request a summary from, if it can't
  be generated locally. These can be from a matrix URI, matrix.to link or a
  `m.space.child` event for example.

A response includes the stripped state in the following format:

```json5
{
  room_id: "!ol19s:bleecker.street",
  avatar_url: "mxc://bleecker.street/CHEDDARandBRIE",
  guest_can_join: false,
  name: "CHEESE",
  num_joined_members: 37,
  topic: "Tasty tasty cheese",
  world_readable: true,
  join_rule: "public",
  room_type: "m.space",
  membership: "invite",
  encryption: "m.megolm.v100",
  room_version: "9001",
}
```

These are the same fields as those returned by `/publicRooms`, with a few
additions: `room_type`, `membership`, `room_version` and `encryption`.

`room_type`, `room_version` and `encryption` are already accessible as part of
the stripped state according to
https://spec.matrix.org/v1.3/client-server-api/#stripped-state , with the
exception of `membership`. These are the same fields as in the response to
[`/hierarchy`](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv1roomsroomidhierarchy)
apart from the addition of the `room_type`, `membership`, `room_version` and
`encryption` fields. The membership can already be accessed by a client anyway,
this API just provides it as a convenience.


#### Rationale and description of response fields

| fieldname          | description                                                                                                                                           | rationale                                                                                                                             |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| room_id            | Required. Id of the room                                                                                                                               | Useful when the API is called with an alias.                                        |
| avatar_url         | Optional. Avatar of the room                                                                                                                          | Copied from `publicRooms`.                                                                                                            |
| guest_can_join     | Required. If guests can join the room.                                                                                                                | Copied from `publicRooms`.                                                                                                            |
| name               | Optional. Name of the room                                                                                                                            | Copied from `publicRooms`.                                                                                                            |
| num_joined_members | Required. Member count of the room                                                                                                                    | Copied from `publicRooms`.                                                                                                            |
| topic              | Optional. Topic of the room                                                                                                                           | Copied from `publicRooms`.                                                                                                            |
| world_readable     | Required. If the room history can be read without joining.                                                                                            | Copied from `publicRooms`.                                                                                                            |
| join_rule          | Optional. Join rules of the room                                                                                                                      | Copied from `publicRooms`.                                                                                                            |
| room_type          | Optional. Type of the room, if any, i.e. `m.space`                                                                                                    | Used to distinguish rooms from spaces.                                                                                                |
| room_version       | Optional (for historical reasons). Version of the room.                                                                                               | Can be used by clients to show incompatibilities with a room early.                                                                   |
| membership         | Optional (1). The current membership of this user in the room. Usually `leave` if the room is fetched over federation.                                              | Useful to distinguish invites and knocks from joined rooms.                                                                           |
| encryption         | Optional. If the room is encrypted this specified the algorithm used for this room. This is already accessible as stripped state. | Some users may only want to join encrypted rooms or clients may want to filter out encrypted rooms, if they don't support encryption or not this algorithm. |

It should be possible to call this API without authentication, but servers may
rate limit how often they fetch information over federation more heavily, if the
user is unauthenticated.

(1) The field `membership` will not be present when called unauthenticated, but
is required when called authenticated. It should be `leave` if the server
doesn't know the users membership state (for example if the server is not known
to the local server).

#### Modifications to `/_matrix/client/v1/rooms/{roomId}/hierarchy`

For symmetry the `room_version` and `encryption` fields are also added to the
`/hierarchy` API.

### Server-Server API

For the
[`/hierarchy`](https://spec.matrix.org/v1.3/server-server-api/#get_matrixfederationv1hierarchyroomid)
federation API is reused. This provides (with a few changes) all the information
needed in this MSC, but it also provides a few additional fields and one level
of children of this room.

Additionally the `encryption` and `room_version` fields are added to the
responses for each room.

In theory one could also add the `max_depth` parameter with allowed values of 0
and 1, so that child rooms are excluded, but this performance optimization does
not seem necessary at this time and could be added at any later point while
degrading gracefully.

(Originally there was a separate federation API for this, but it was decided
by the author that lowering the duplication on the federation side is the way to go.)

## Potential issues

### Performance

Clients may start calling this API very often instead of using the
[`/hierarchy`](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv1roomsroomidhierarchy)
for spaces or caching the state received via `/sync`.
Looking up all the state events required for this API may cause performance
issues in that case.

To mitigate that, servers are recommended to cache the response for this API and
apply rate limiting if necessary.

## Alternatives

- The 
    [`/hierarchy`](https://spec.matrix.org/v1.3/client-server-api/#get_matrixclientv1roomsroomidhierarchy)
    API could be used, but it returns more data than necessary
    by default (but it can be limited to just 1 room) such as all the
    `m.space.child` events in a space, but also is missing the room version,
    membership and the encryption field. (We do reuse the federation API now.)
- For joined rooms, the `/sync` API can be used to get a summary for all joined
    rooms. Apart from not working for unjoined rooms, like knocks, invites and
    space children, `/sync` is very heavy for the server and the client needs to
    cobble together information from the `state`, `timeline` and
    [`summary`](https://github.com/matrix-org/matrix-doc/issues/688) sections to
    calculate the room name, topic and other fields provided in this MSC.
    Furthermore, the membership counts in the summary field are only included, if
    the client is using lazy loading.
    This MSC provides similar information as calling `/sync`, but it uses the
    stripped state, which is needed to allow this to work for unjoined rooms and
    it excludes `m.heroes` as well as membership events, since those are not
    included in the stripped state of a room. (A client can call
    `/joined_members` to receive those if needed. It may still make sense to
    include heroes so that clients could construct a human-friendly room display
    name in case both the name and the canonical alias are absent; but solving
    the security implications with that may better be left to a separate MSC.
- The `/state` API could be used, but the response is much bigger than needed,
    can't be cached as easily and may need more requests. This also doesn't work
    over federation (yet). The variant of this API, which returns the full state
    of a room, also does not return stripped events, which prevents it from
    being used by non-members. The event for specific events DOES return
    stripped events, but could not provide a member count for a room.
- Peeking could solve this too, but with additional overhead and
    [MSC2753](https://github.com/matrix-org/matrix-doc/pull/2753) is much more
    complex. You need to add a peek and remember to remove it. For many usecases
    you just want to do one request to get info about a room, no history and no
    updates. This MSC solves that by reusing the existing hierarchy APIs,
    returns a lightweight response and provides a convenient API instead.
- This API could take a list of rooms with included `via`s for each room instead
    of a single room (as a POST request). This may have performance benefits for
    the federation API and a client could then easily request a summary of all
    joined rooms. It could still request the summary of a single room by just
    including only a single room in the POST or a convenience GET could be
    provided by the server (that looks like this proposal).
- [MSC3429](https://github.com/matrix-org/matrix-doc/pull/3429) is an
    alternative implementation, but it chooses a different layout. While this
    layout might make sense in the future, it is inconsistent with the APIs
    already in use, harder to use for clients (iterate array over directly
    including the interesting fields) and can't reuse the federation API. In my
    opinion an MSC in the future, that bases all summary APIs on a list of
    stripped events seems like the more reasonable approach to me and would make
    the APIs more extensible.

## Security considerations

This API may leak data, if implemented incorrectly or malicious servers could
return wrong results for a summary.

Those are the same concerns as on [MSC2946](https://github.com/matrix-org/matrix-doc/pull/2946)
or [MSC3173](https://github.com/matrix-org/matrix-doc/pull/3173).

This API could also be used for denial of service type attacks. Appropriate
ratelimiting and caching should be able to mitigate that.

## Unstable prefix

This uses the `im.nheko.summary` unstable prefix. As such the paths are prefixed
with `unstable/im.nheko.summary`.

- the client API will be
    `/_matrix/client/unstable/im.nheko.summary/summary/{roomIdOrAlias}`.

Some implementations still use
    `/_matrix/client/unstable/im.nheko.summary/rooms/{roomIdOrAlias}/summary`,
    but this was a mistake in this MSC. Endpoints using aliases shouldn't be under /rooms.

Additionally the fields `encryption` and `room_version` in the summaries are
prefixed with `im.nheko.summary` as well since it is new. The latter might still
be called `im.nheko.summary.version` in some implementations.
