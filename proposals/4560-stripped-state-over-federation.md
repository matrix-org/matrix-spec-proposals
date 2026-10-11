# MSC4560: Stripped state requests over federation

The current [room summary
endpoint](https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv1room_summaryroomidoralias) is fairly
limited: it returns a few specific pieces of data derived from a handful of room state events, along with some
additional metadata like the number of users joined to the room. Its federation counterpart, the [hierarchy
endpoint](https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv1roomsroomidhierarchy), which pulls double
duty as the mechanism behind fetching space hierarchies, has the same issue, and in the case of federated summaries its
information about space children is completely superfluous. This proposal describes a new client-server and federation
endpoint pair that allows clients to efficiently access a limited set of stripped state events for rooms they aren’t
joined to, as a more extensible mechanism for requesting room summaries.

# Proposal

## Allowed stripped state events

The following events may be requested in a stripped form over federation:

- `m.room.create`
- `m.room.name`
- `m.room.avatar`
- `m.room.topic`
- `m.room.join_rules`
- `m.room.canonical_alias`
- `m.room.guest_access`
- `m.room.history_visibility`
- `m.room.encryption`
- `m.space.child`
- `m.space.parent`

Future MSCs may add more events to this list.

## Client-server endpoint

### `POST /_matrix/client/v1/stripped_state/{room_id_or_alias}`

| Rate limited | Requires authentication |
|--------------|-------------------------|
| Yes          | Optional                |

This endpoint allows clients to ask for a room’s stripped state.

#### Request

##### Path parameters

| Name               | Type                  | Description             |
|--------------------|-----------------------|-------------------------|
| `room_id_or_alias` | Room Id \| Room Alias | The room being queried. |

##### Query parameters

| Name  | Type            | Description                                                                                       |
|-------|-----------------|---------------------------------------------------------------------------------------------------|
| `via` | \[Server Name\] | A list of server names to request the stripped state from, if the local server cannot provide it. |

##### Request body

| Name                 | Type           | Default | Description                                                                                                                               |
|----------------------|----------------|---------|-------------------------------------------------------------------------------------------------------------------------------------------|
| `state`              | \[Event Type\] | `[]`    | The state event types to include in the response.                                                                                         |
| `num_joined_members` | boolean        | `false` | Whether to include `num_joined_members` in the response. To speed up responses, clients should not set this unless they intend to use it. |

If `via` has more than 32 servers, the server MUST return `M_TOO_LARGE`.

If `state` includes event types that are not [allowed stripped state events](#Allowed-stripped-state-events), the server
MUST return `M_INVALID_PARAM` *before* contacting any vias.

#### Responses

| Status                | Description                                                      |
|-----------------------|------------------------------------------------------------------|
| 200                   | The room’s stripped state was successfully fetched.              |
| 400 `M_INVALID_PARAM` | An event type in `state` is not an allowed stripped state event. |
| 400 `M_TOO_LARGE`     | More than 32 vias were supplied.                                 |
| 403 `M_FORBIDDEN`     | The requesting user may not view the room’s stripped state.      |
| 404 `M_NOT_FOUND`     | The room could not be found locally or through any provided via. |

##### 200 response

| Name                 | Type                     | Required | Description                                                                                                                                              |
|----------------------|--------------------------|----------|----------------------------------------------------------------------------------------------------------------------------------------------------------|
| `state`              | \[`StrippedStateEvent`\] | Yes      | The stripped state of `room_id_or_alias`. May be empty if no state events were requested, or if none of the requested events existed in the target room. |
| `num_joined_members` | number                   | No       | The number of members joined to the room. Will be absent if `num_joined_members` was not `true` in the request.                                          |
| `via`                | Server Name              | Yes      | The server that provided the stripped state. This MUST be the local server’s name if the local server provided the stripped state without asking a via.  |

If the server can generate the stripped state locally, it MUST include ALL of the [allowed stripped state
events](#Allowed-stripped-state-events) listed in the request that are present in the room’s state, regardless of their
`state_key`.

`num_joined_members` is derived from the room’s `m.room.member` state events. Since there may be many thousands of
`m.room.member` state events in a room, it is substantially more efficient to only send this field instead of including
the room’s complete membership list.

If the server is a resident of the provided room, it MUST generate the stripped state itself based off of its copy of
the room’s current state, and MUST set its own server name in the `via` field of the response. Otherwise, it SHOULD ask
the provided `via` servers using the federation endpoint defined below. The server MAY query vias in parallel, but in
all cases MUST NOT return an error response unless ALL of the vias return an error response. This is to handle future
outdated servers returning `M_INVALID_PARAM` for state event types that are added to the allowlist in newer versions of
Matrix. In all cases, the server MUST set the `via` field in the response to the name of the server whose successful
response it decides to use.

If a via cannot be contacted for any reason, the server SHOULD treat it as if it returned `M_NOT_FOUND`.

Clients SHOULD show the `via` in their UI when displaying data derived from stripped state, such as a room preview
before joining, in a manner which indicates that the displayed data was provided by the `via`. This is necessary to
provide accountability and guard against malicious servers returning falsified room previews, as it is impossible to
validate the `via`’s response without joining the room. If the `via` is the local server, clients MAY show an indicator
that the preview is trustworthy.

### Visibility checks

Servers SHOULD use the below rules to determine if a user (possibly anonymous) may access a room’s stripped state. These
are the same rules that currently apply to the room summary endpoint.

These checks can only be performed if the server is a resident of the room. They do not apply if the server is asking a
via for the stripped state.

All checks use the room’s current state. Checks that require an authenticated user are skipped if the request is
anonymous.

1.  If the room’s history visibility is `world_readable`, allow.
2.  If the authenticated user is joined or invited to the room, allow.
3.  If the room’s join rule is `public`, `knock`, or `knock_restricted`, allow.
4.  If the room’s join rule is `restricted`, and the server [is able to
    verify](https://spec.matrix.org/v1.19/server-server-api/#restricted-rooms:~:text=all%20conditions%2E-,The,conditions,-%2E)
    that the authenticated user fulfills all of the join conditions, allow.
5.  Otherwise, deny.

If the user does not pass the checks, an error MUST be returned. This error SHOULD be `M_FORBIDDEN`, but servers MAY
choose to return `M_NOT_FOUND` instead of `M_FORBIDDEN`. As clients MAY show different UI for the two error codes,
server developers are encouraged to consider the security and user experience tradeoffs before doing this.

## Federation endpoint

### `POST /_matrix/federation/v1/stripped_state/{room_id}`

| Rate limited | Requires authentication |
|--------------|-------------------------|
| Yes          | Optional                |

This endpoint allows servers to ask other servers for a room’s stripped state.

#### Request

##### Path parameters

| Name      | Type    | Description             |
|-----------|---------|-------------------------|
| `room_id` | Room Id | The room being queried. |

##### Request body

| Name                 | Type           | Default | Description                                              |
|----------------------|----------------|---------|----------------------------------------------------------|
| `state`              | \[Event Type\] | `[]`    | The state event types to include in the response.        |
| `num_joined_members` | boolean        | `false` | Whether to include `num_joined_members` in the response. |

If `state` includes event types that are not [allowed stripped state events](#Allowed-stripped-state-events), the server
MUST return `M_INVALID_PARAM`.

#### Responses

| Status                | Description                                                      |
|-----------------------|------------------------------------------------------------------|
| 200                   | The room’s stripped state was successfully fetched.              |
| 400 `M_INVALID_PARAM` | An event type in `state` is not an allowed stripped state event. |
| 403 `M_FORBIDDEN`     | The requesting server may not view the room’s stripped state.    |
| 404 `M_NOT_FOUND`     | The room could not be found locally.                             |

##### 200 response

| Name                 | Type                     | Description                               |
|----------------------|--------------------------|-------------------------------------------|
| `state`              | \[`StrippedStateEvent`\] | The stripped state of `room_id`.          |
| `num_joined_members` | number                   | The number of members joined to the room. |

Servers MUST include ALL [allowed stripped state events](#Allowed-stripped-state-events) of the types listed in the
request’s `state` array that are present in the room’s state, regardless of their `state_key`.

### Visibility checks for servers

When responding to requests to the federation stripped state endpoint, servers SHOULD use the below rules to determine
if the requesting server may access a room’s stripped state.

All checks use the room’s current state.

1.  If the requesting server is ACLed from the room, deny.
2.  If the server has at least one user joined to the room, allow.
3.  Otherwise, use the [visibility checks for users](#Visibility-checks), treating the server as an unauthenticated
    user.

If the server does not pass the checks, a `M_FORBIDDEN` error MUST be returned.

Servers MAY choose to return `M_NOT_FOUND` instead of `M_FORBIDDEN`, as with the visibility checks for users, and with
the same tradeoff.

## Changes to existing endpoints

`GET /_matrix/client/v1/room_summary/{roomIdOrAlias}` is deprecated by this proposal, to be removed in a future
specification version. The stripped state endpoint replaces all of its functionality except for the `membership` field
in its response. The `membership` field is mentioned to be [“exposed solely for
convenience”](https://github.com/deepbluev7/matrix-doc/blob/room-summaries/proposals/3266-room-summary.md#:~:text=Exposed%20solely%20for%20convenience)
in the room summary MSC itself, and as clients have many other ways to access this information this MSC does not include
an equivalent field for the sake of simplicity.

`GET /_matrix/client/v1/rooms/{roomId}/hierarchy` and `GET /_matrix/client/v1/rooms/{roomId}/hierarchy` are deprecated
by this proposal, to be removed in a future spec version. Clients should traverse the space hierarchy by fetching
`m.room.child` events using this proposal’s endpoints. This will require clients to adjust their logic for displaying
space hierarchies, but has several benefits:

- The hierarchy endpoints are somewhat notorious for their slow speed. For deeply nested hierarchies and requests with a
  high `max_depth`, servers have to make multiple federation requests to load all the spaces, and process large amounts
  of duplicated data, as the federation hierarchy endpoint returns full summaries for the room’s direct children as well
  as the children’s room IDs. (Continuwuity does not use this data at all.)
- Pagination of the client-server hierarchy endpoint does not have a well-defined behavior for handling changes to the
  hierarchy in the middle of pagination. (For this reason, Continuwuity does not paginate and always returns the full
  hierarchy.) Having clients manage hierarchy traversal allows pagination to be handled by the client, which always
  knows what it has and has not seen.
- Clients may not be interested in all the data included in the hierarchy’s summaries, or may wish to fetch some data in
  the background. With the stripped state endpoint this is both possible and easy to do.

*Continuwuity is cited here for illustrative purposes, not for justification, as it is the homeserver the author has the
most familiarity with.*

The [public room directory endpoints](https://spec.matrix.org/v1.19/client-server-api/#published-room-directory), which
have a similar response structure to the summary endpoint, could also be changed to use stripped state, but such a
change is out of the scope of this MSC.

# Potential issues

No mechanism is provided to request a specific combination of state event and state key. The current list of allowed
stripped state event types consists entirely of events that either exclusively use the default `""` state key
(authorization-related events) or are only useful with all state keys fetched at once (`m.space.child`).

# Alternatives

## Non-stripped state requests over federation?

Instead of stripped state, full PDUs could be transmitted over federation, and full events could be sent to clients.
This approach was rejected primarily because, for the use case these endpoints seek to target, the extra data included
in PDUs is largely unnecessary, has negligible security benefits, and potentially tempts server developers to write
insecure logic.

While sending full PDUs would allow homeservers to verify signatures and content hashes on responses from vias, this
only proves that the events themselves are valid in isolation. They can still be cherry-picked by vias, or replaced with
entirely new events signed by the via itself, so servers cannot persist them or treat them like normal incoming events.
The only defense against this is running auth checks against the events, which requires fetching those events’ full auth
chains, and in the worst case begins to resemble a federated room join, which seems like a suboptimal solution to the
problem of inspecting a room *without* joining.

## Peeking over federation

Federated room peeking, while solving similar problems to those solved by this proposal (and the existing summary and
hierarchy endpoints), is a significantly more complex mechanism, and has been [a work in
progress](https://github.com/matrix-org/matrix-spec-proposals/pull/2444) for six years and counting in no small part
because of this complexity. Additionally, in its current form, only rooms that are `world_readable` may be peeked, which
is more restrictive than the visibility checks used for summaries. This proposal’s approach is intended to be both more
extensible than the current summary endpoint and easier to implement than federated peeking.

## Allow any state event type in public rooms

The whitelist of allowed stripped state event types applies to public rooms, even though anyone can join and acess the
room’s state anyway. Requesting arbitrary state events is nonetheless forbidden by this proposal. This is primarily for
the sake of consistency – it should certainly not be possible to access arbitrary state for `knock` and
`knock_restricted` rooms – but also to avoid exposing all past and future state event types to public room spiders
without even requiring them to join the room first. Additionally, as the stripped state endpoints do not paginate,
requesting certain state event types like `m.room.member` would lead to enormous responses, and blacklisting these
events from being requested from public rooms only would complicate the proposal even further. Arbitrary state event
access in public rooms is the domain of federated peeking, not room summaries.

## Extend the existing endpoints

[MSC4507](https://github.com/matrix-org/matrix-spec-proposals/pull/4507) proposes including stripped state events in
`GET /_matrix/federation/v1/hierarchy/{roomId}` using a new query parameter and a state event to control visibility.
Besides introducing potential data duplication, as the existing room summary fields are still sent, the author of this
proposal believes that any solution that requires more work from room administrators than adjusting the visibility
settings already available to them is not practicable for use in the public federation. The use case outlined in
MSC4507, a vendor-specific “security policy” state event, could easily be achieved using this proposal in tandem with a
modified homeserver deployment that extends the list of allowed stripped state event types.

# Security considerations

This proposal has largely the same security considerations as the existing room summary and hierarchy endpoints. The
primary flaw with those endpoints, and the new ones introduced by this proposal, is their vulnerability to the “me when I
lie attack”: when the client supplies vias, there is no way to prove that a via’s response actually reflects the room’s
state without joining the room, which allows vias to show servers misleading or malicious information for rooms they are
queried about. For this reason, the client-server endpoints include a `via` field in their responses, which clients are
encouraged to display prominently wherever stripped state data is shown to the user, alongside a notice that the data is
only as trustworthy as the via it was fetched from. This issue, of course, does not apply if the client did not provide
vias or if the server was able to generate the stripped state locally.

The list of allowed state events maps cleanly to information that the summary and hierarchy endpoints already return,
with two exceptions: `m.space.parent` is completely new, and `m.space.child` is now accessible to anonymous users and
public room spiders (previously the hierarchy endpoint required authentication). This change exposes a limited amount of
additional information to anonymous entities, whereas previously a spider would at least need to provide a server
signing key to use the federation hierarchy endpoint, but does not introduce significant security concerns: spiders
still cannot access data for non-public rooms, and it is still possible to hide room IDs in a space by nesting them
under an invite-only subspace or simply using `m.space.parent` relations only. In addition, exposing hierarchy
information to spiders could be useful for public communities that want to show prospective joiners their structure.

The ability to query `knock` rooms' stripped state allows slightly more information to be gleaned about the room's users before knocking. The room's creator list is accessible through the `m.room.create` event, and other events include `sender` fields that can reveal users who may have had powerlevels at some point in the room's history. Since this information is also available simply by knocking on the room and checking the stripped state in the response, this is deemed to be an acceptable tradeoff for the benefit of allowing clients to preview `knock` rooms.

# Unstable prefix

While this proposal is unstable, the following identifiers should be used:

| Stable identifier                                      | Unstable identifier                                                                   |
|--------------------------------------------------------|---------------------------------------------------------------------------------------|
| `/_matrix/client/v1/stripped_state/{room_id_or_alias}` | `/_matrix/client/unstable/org.continuwuity.msc4560.stripped_state/{room_id_or_alias}` |
| `/_matrix/federation/v1/stripped_state/{room_id}`      | `/_matrix/federation/unstable/org.continuwuity.msc4560.stripped_state/{room_id}`      |

Servers may use the `org.continuwuity.msc4560` unstable feature flag to indicate that they support the client-server
stripped state endpoints.

# Dependencies

None.
