# MSC4507: Return additional room state from `/_matrix/federation/v1/hierarchy/{roomId}`

The [`GET
/_matrix/federation/v1/hierarchy/{roomId}`](https://spec.matrix.org/v1.19/server-server-api/#get_matrixfederationv1hierarchyroomid)
federation endpoint allows homeservers to ask another homeserver for certain
information about a room or a space. This is most useful when a homeserver does
not (currently) have any users in the room, and thus does not have the latest
room state synchronised.

The information that is returned is maintained as part of the Matrix spec, and
includes fields such as `join_rule`, `room_type`, `topic`. However, there may be
times when it's useful for a homeserver to request arbitrary state events from a
room without joining it.

This proposal adds a new query parameter and response field to [`GET
/_matrix/federation/v1/hierarchy/{roomId}`](https://spec.matrix.org/v1.19/server-server-api/#get_matrixfederationv1hierarchyroomid)
which allows homeservers to ask for certain pieces of state from a room, or any
space child rooms, that they may not be in.

It also defines a new state event, which determines which state event types and
state keys a homeserver that isn't in the room is allowed to see.

## Use case

The primary use case that motivated this proposal is the concept of "security
policies" from Element's implementation of [Mission Partner
Environments](https://element.io/en/mission-partner-environments). Broadly, one
defines a "security policy" for a room which, among other things, states the
security clearance needed to access the room. This security policy is
implemented as a state event, and clearance information is stored in local
OIDC identity providers or LDAP instances as user attributes.

When a user tries to join a room, their own homeserver must approve/deny the join
based on the user's security clearance and the security policy in the room. But
the homeserver may not have access to the room's security policy if this is the
first user to join the room. Therefore, homeservers need a way to request this
information from resident servers before carrying out the room join.

This unlocks other use cases as well, of course. No longer does a bespoke field
for every type of state event need to be defined in the response body of this
request. In addition, homeservers can choose to "opt out" of information they
don't need by not specifying the state event. The current shape of the endpoint
has no method of doing that.

## Proposal

### Query parameter

Add a `additional_state` query parameter to [`GET
/_matrix/federation/v1/hierarchy/{roomId}`](https://spec.matrix.org/v1.19/server-server-api/#get_matrixfederationv1hierarchyroomid).
The value is a JSON object in form:

```json
{"type": "m.room.avatar", "state_key": ""}
```

and may be repeated multiple times in order to ask for multiple state events.
`state_key` may be omitted to ask for all state events of the given type.

A JSON object is preferable to a tuple of `(type, state_key)`, as it is both
self-describing and easily extendable.

If `additional_state` is provided, as the value cannot be parsed as JSON, the
homeserver MUST respond with status code 400 and error `M_NOT_JSON`. If the
parsed JSON is otherwise invalid (i.e. missing a `type` field) the homeserver
MAY return status code 400 and error `M_INVALID_PARAM`.

### `m.public_state` state event

A new state event `m.public_state` with a `state_key` of an empty string is
defined as the state events that a room is willing to share publicly. The
content of `m.public_state` looks like the following:

```json5
{
  "public_state": {
    "m.room.topic": {
      // optional, restricts the set of state_keys that are considered public.
      "state_keys": [""]
    },
    // no "state_keys" field means "all state keys are public"
    "com.example.some_state": {}
  }
}
```

If a state event type is not present, it is assumed to not be public.

A state event is preferred to individual homeserver configuration, as that can
lead to different responses from different homeservers. As well as lack of easy
per-room configuration, or control by room admins (rather than homeserver
operators).

### Response

The remote homeserver SHOULD return state events from the room that match the
requested state events and are authorised to be shared by the `m.public_state`
state event, as known to the resident homeserver.

These are returned in a new `additional_state` field in the response:

```json5
{
  "children": [
    {
      // ... other fields
      "room_id": "!second_room:example.org",
      "additional_state": [
        {
          "content": {
            "topic": "This is a child room"
          },
          "type": "m.room.topic",
          "sender": "@alice:example.com",
          "state_key": ""
        }
        // `com.example.some_state` was not present in this room.
      ]
    }
  ],
  "inaccessible_children": [
    "!secret:example.org"
  ],
  "room": {
    // ... other fields
    "room_id": "!space:example.org",
    "additional_state": [
      {
        "content": {
          "topic": "A space for friends"
        },
        "type": "m.room.topic",
        "sender": "@alice:example.com",
        "state_key": ""
      },
      {
        "content": {
          "foo": "bar"
        },
        "type": "com.example.some_state",
        "sender": "@bob:example.com",
        "state_key": "my_state_key"
      }
    ]
  }
}
```

State events will not be returned if the event does not exist, or if the state
event is not considered public. There is no difference in response between a
state event not existing vs. the homeserver deciding not to return the state
event is returned to the requester. This property prevents requesters from
'probing' rooms to learn whether a certain state event is present.

### Permissions

The default power level required to send `m.public_state` events is 100.

## Potential issues

### `m.public_state` is eventually consistent

If a state event is marked as public via `m.public_state`, then marked private
again by another `m.public_state`, it is possible for the event to still be
exposed if a homeserver in the room has not yet received the second
`m.public_state` state event. Likewise, a state event may not be made public yet
if the first state event has not yet reached a given resident homeserver.

This edge case is considered acceptable for the above use case.

## Alternatives

### /v2 endpoint

Define a `/v2/` of the Federation hierarchy endpoint which removes all other
response fields, and only relies on `additional_state` semantics. This allows
homeservers to only ask for the fields they need, eliminating extra bandwidth
used for other fields. This is probably best paired with an updated
Client-Server `/hierarchy` request, so clients can specify which fields they're
interested in.

It'd also be best to make the request a POST, so that we don't have to abuse
query parameters for the `(event type, state_key)` definitions.

## Security considerations

This endpoint allows homeservers that aren't in a room to request arbitrary
state events from the room. This opens up a huge attack surface. Room admins and
moderators should ensure they specify exactly the room state they intend to
expose via the `m.public_state` state event, and nothing more.

## Unstable prefix

While this MSC is not accepted, implementations should make use of the following
unstable identifiers:

* `m.public_state` state event -> `org.matrix.msc4507.public_state`
* `additional_state` query parameter -> `org.matrix.msc4507.additional_state`

## Dependencies

This MSC does not depend on any other MSCs.
