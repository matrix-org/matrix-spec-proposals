# MSC4466: Altering profile change propagation

Currently, when a user changes their `displayname` or `avatar_url`, [the server
SHOULD](https://spec.matrix.org/v1.18/client-server-api/#events-on-change-of-profile-information) send
a `m.room.member` event to every room that user is in which updates the `displayname` or `avatar_url`
field in their previous membership event. This behavior may not be desirable to users who have changed
their per-room `displayname`/`avatar_url` in a large number of rooms, as the new membership events will
overwrite any per-room changes.

This proposal describes a simple method for clients to control how the server sends profile update membership
events. Clients may ask the server to suppress the events entirely and manage updating the user's membership events
manually. Alternatively, they may ask the server to only send the events to rooms where the user has not overridden
their `displayname` and `avatar_url`. This functionality is provided both as a convenience for client developers and to
improve the reliability and lessen the possible the bandwidth impact of this common use case, which would otherwise
require clients to manually send potentially hundreds of state events at once.

This proposal also clarifies what keys the server should preserve when sending these membership events.

## Proposal

A new query parameter `propagate_to` is introduced on [`PUT /_matrix/client/v3/profile/{userId}/{keyName}`](https://spec.matrix.org/v1.18/client-server-api/#put_matrixclientv3profileuseridkeyname)
and [`DELETE /_matrix/client/v3/profile/{userId}/{keyName}`](https://spec.matrix.org/v1.18/client-server-api/#delete_matrixclientv3profileuseridkeyname).
Its behavior is only defined if `{keyName}` is `displayname` or `avatar_url`; the server MUST ignore it, if it is
present, for any other value of `{keyName}`.    Three values are defined for `propagate_to`, which change the server's
behavior when sending an updated `m.room.member` event:

- `all`: The server MUST send a `m.room.member` event for `{userId}` to every room that `{userId}` has a `join`
membership in, with `{keyName}` set to the newly provided value, or removed entirely, in accordance with the
[key copying rules](#key-copying-rules).
- `unchanged`: For each room that `{userId}` has a `join` membership
in, the server MUST check the value of `{keyName}` in the `m.room.member` event's content. If `PUT` was used and
the content's current value of `{keyName}` is exactly equivalent to the value of `{keyName}` in the user's global
profile data, or `DELETE` was used and the user's global profile data is already missing an entry for `{keyName}`,
the server MUST send a `m.room.member` event to that room with `{keyName}` changed to the newly provided value or
removed entirely, in accordance with the [key copying rules](#key-copying-rules). For all other rooms, the server
MUST NOT send a `m.room.member` event to that room. This allows clients to easily offer a way to change a user's
profile information while keeping per-room changes intact.
- `none`: The server MUST NOT send `m.room.member`
events to any rooms.

The server MUST additionally update the user's global profile data with the new value of
`{keyName}`, regardless of the value of `propagate_to`. This is the data that is returned by [`GET /_matrix/client/v3/profile/{userId}`](https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientv3profileuserid)
and related endpoints.

If the `propagate_to` query parameter is not provided, the server MUST behave as if it were set to `all`, in
keeping with current behavior.

Example for the behavior of `unchanged`:

| `displayname` in global profile      | `displayname` in room membership | `displayname` in PUT request | New `displayname` in room membership                                                                                                 |
| ------------------------------------ | -------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Alice Margatroid                     | Alice "Nickname" Margatroid      | Alice                        | Unchanged from Alice "Nickname" Margatroid, because `displayname` in room membership is different from displayname in global profile |
| Alice Margatroid                     | Alice Margatroid                 | Alice                        | Changed to Alice, because `displayname` in room membership is identical to `displayname` in global profile                           |

Additionally, a new `propagate_to` query parameter is introduced on on `PUT /_matrix/client/v3/profile/{userId}`
([MSC4437](https://github.com/matrix-org/matrix-spec-proposals/pull/4437)). This query parameter has the same
acceptable values and same behavior as the `propagate_to` query parameter on the `PUT
/_matrix/client/v3/profile/{userId}/{keyName}` endpoint, with the following caveats:

- If the query parameter
is set to `unchanged`, the server MUST consider both `displayname` and `avatar_url` when checking `{userId}`'s
current membership. If only one field would need to be changed or deleted according to the `unchanged` logic,
the server MUST send a membership event to that room which changes or deletes _only_ that field. If both fields
need to be changed or deleted, the server MUST send events which update _both_ fields.
- If the query parameter
is set to `all`, or the query parameter is set to `unchanged` and both `displayname` and `avatar_url` were updated,
the server SHOULD only send a single `m.room.member` event that changes or deletes both fields.

The [key copying rules](#key-copying-rules) MUST also be followed when sending membership events in response to
a request to this endpoint.

If the `propagate_to` query parameter is not provided, the server MUST behave as if it were set to `all`, in
keeping with the current behavior of MSC4437.

### Key copying rules

When sending a new `m.room.member` event with the intent of updating `displayname` or
`avatar_url`, the server:
- MUST set `displayname` or `avatar_url`, whichever is applicable, to the newly provided
value. 
- MUST NOT copy
`join_authorised_via_users_server` from the previous membership event. The presence of this field requires the event
to be signed by the authorizing server as well, which is of course not possible without that server's participation.
- MUST NOT copy `reason` from the previous membership event. The profile change API does not currently specify
a method to give a reason for a profile change, and describing such a method is out of the scope of this MSC.
- MUST copy ALL OTHER fields from the previous membership event's content unchanged, including whichever of
`displayname` or `avatar_url` was not changed.

Future MSCs which add new fields to the content of `m.room.member` events may specify additional rules.

## Potential issues

No method is provided by this MSC for clients to specify a list of rooms to send a `m.room.member` event in. A client
may implement this easily by updating the user's global profile without sending any events (setting `propagate_to`
to `none`), and then sending `m.room.member` events itself in whatever rooms it chooses.

This MSC does not specify a solution to the problem of the server being flooded with thousands of `state_ids` and
`get_missing_events` requests when updating a user's membership in a large number of rooms at once. The server
MAY choose to send the new membership events at a slow pace to manage the load.

## Alternatives

[MSC4069](https://github.com/matrix-org/matrix-spec-proposals/pull/4069) is a similar proposal which
only implements a Boolean flag to suppress propagation (equivalent to setting this proposal's `propagate_to` to
`none`), and tasks clients with deciding how to update a user's profile if they wish to do anything more complex. The
use case of "update my profile but not in rooms where I changed it" seems common enough to the author of this
proposal that having a server-side implementation of it, which will likely be more efficient since the server
already has access to relevant state, would be useful. An implementation of MSC4069 could likely be converted to
an implementation of this proposal with little effort.

## Security considerations

This MSC's impact on security is at most a subset of what was already possible using the existing profile
system. Users can still send large numbers of state events to their joined rooms by changing their display name
or avatar repeatedly, but this was already possible with the existing endpoints, and this MSC in fact
allows well-behaved users and clients to lessen the number of state events the server sends on their behalf.

## Unstable prefix

While this proposal is unstable, implementations should use
`computer.gingershaped.msc4466.propagate_to` instead of `propagate_to` as a query parameter for the `PUT
/_matrix/client/v3/profile/{userId}/{keyName}` endpoint and `DELETE /_matrix/client/v3/profile/{userId}/{keyName}`
endpoint. Servers may use the `computer.gingershaped.msc4466` unstable feature flag on `/versions` to advertise support for
this proposal.

Servers which implement MSC4437 as well as this proposal should strongly consider supporting this proposal's
extensions to MSC4437. While this proposal is unstable, servers which support the extensions should use
`computer.gingershaped.msc4466.propagate_to` instead of `propagate_to` as a query parameter for the `PUT
/_matrix/client/v3/profile/{userId}` endpoint and `PUT /_matrix/client/unstable/com.beeper.msc4437/profile/{userId}`
unstable endpoint. Servers may use the `computer.gingershaped.msc4466.msc4437_extensions` unstable feature flag to indicate
that they support the extensions.

## Dependencies
This proposal depends on MSC4133, which is already in the specification, and MSC4437, which is proposed for FCP.

This proposal supersedes MSC4069. 
