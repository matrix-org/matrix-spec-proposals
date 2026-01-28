# MSC4186: Simplified Sliding Sync

The current `/sync` endpoint scales badly as the number of rooms on an account increases. It scales badly because all
rooms are returned to the client and incremental syncs are unbounded and slow down based on how long the user has been
offline. On large accounts with thousands of rooms, the initial sync operation can take tens of minutes to perform. This
significantly delays the initial login to Matrix clients, and also makes incremental sync very heavy when resuming after
any significant pause in usage.

> [!Note]
> This is a “simplified” version of the sliding sync API proposed in
> [MSC3575](https://github.com/matrix-org/matrix-spec-proposals/pull/3575), based on paring back that API based on real
> world use cases and usages.

## High level overview

From a high level, sliding sync works by the client specifying a set of rules to match rooms (via "lists" and
"subscriptions"). The server will use these rules to match relevant rooms to the user, and return any rooms that have
had changes since the previous time the room was returned to the client. If no rooms have changes, the server will block
waiting for a change (aka long-polling, like `/v3/sync`).

By judicious use of lists and subscriptions the client can control exactly what data is returned when, and help ensure
that it doesn't request "too much" data at once (thus avoiding slow responses).

## Goals

During initial design, the following goals were taken into account:

- Sync time should be independent of the number of rooms you are in.
- Time from opening of the app (when already logged in) to confident usability should be as low as possible.
- Time from login on existing accounts to usability should be as low as possible.
- Bandwidth should be minimized.
- The API should support lazy-loading of things like membership and read receipts (and avoid sending unnecessary data to
  the client).
- The API should support informing the client when room state changes from under it, due to state resolution.
- Clients should be able to work correctly without ever syncing in the full set of rooms they’re in.
- Incremental sync responses should only include rooms that the user cares about.
- Servers should not need to store all past since tokens. If a since token has been discarded we should gracefully
  degrade to initial sync.


# Proposal

We add a new `POST` `/sync` API to replace the existing `GET` `/sync` API. Clients use the new API in a similar manner
to the old one; the client repeatedly calls `/sync` which will return with any new data.

See the API section below for the request and response schemas.

## Connections

Each request may include a `pos` token, and each response includes a `pos` token that can be used for subsequent
requests.

A "connection" (aka "sync loop") is a long-running set of sync requests where each new request uses the `pos` from the
previous request. Clients can have multiple connections with the server, so long as each connection has a different
`conn_id` set in the request.

Clients must only have a single active request in-flight at any time per connection. If a client needs to send another
request before receiving a response to an in-flight request (e.g. for retries or to change parameters) the client *must*
cancel the in-flight request (at the HTTP level) and *not* process any response it receives for it. Clients MAY change
the request body if they cancel a request and send a new one with the same `pos`.

In particular, a client must use the returned `pos` value from the last *processed* response as the `pos` parameter in
the next request. A `pos` from an older response MUST NOT be used again. Doing so may either result in missed data or
result in a fatal error response from the server.

The server cannot assume that a client has received a response until it receives a new request with the `pos` token set
to the `pos` it returned in the response. The server MUST ensure that any per-connection state it tracks correctly
handles receiving multiple requests with the latest `pos` token (e.g. the client retries the request or decides to cancel
and resend a request with different parameters). Once a server has seen a request with a given `pos`, the server may
clean up any per-connection state from before that `pos`.

A server may decide to "expire" connections, either to free resources or because the server thinks it would be faster
for the client to start from scratch (e.g. because there are many updates to send down). This is done by responding with
a 400 HTTP status and an error code of `M_UNKNOWN_POS`.


## Lists and subscriptions

Clients specify a set of rules that the server uses to determine which rooms the client is interested in receiving. A
room is returned in the response if all of the following conditions hold:
1. The user has permission to view the room (or some subset of information about it).
1. The room matches at least one of the rules in the request.
1. The room has either never been sent to the client on that connection before, or there have been updates to the room
   since the last time it was sent to the client.

This MSC specifies two types of rule: a "list" and a "subscription".

Each rule also specifies a "room config", used to configure what data to return for a room that matches the rule. The
"room config" has two fields: the `timeline_limit` and `required_state`. The `timeline_limit` specifies the maximum
number of events to return in the timeline section of a room, and the `required_state` specifies what state to return.

### Lists

Lists are the primary way of specifying the rooms the client is interested in. They operate against a sequence of rooms
for the user that the server maintains. This server list is, for each user, the set of rooms that the user either
joined, been invited, knocked on, left, or been kicked or banned from, sorted by recent activity (see below for exact
ordering semantics).

Rooms that the user has been in but left are only included if the room was previously sent to the client in that
connection. Rooms the user has been kicked or banned from will always be included. We do not include rooms the user has
left themselves to save bandwidth and general efficiency (as the user knows they've left), but we still include kicked
and banned rooms as a) this should be uncommon, and b) the user may not have seen that they've been kicked/banned from
the room otherwise.

A "list" is then a set of filters (e.g. only match invites, or DM rooms, etc) plus a "range" that indexes into the
*filtered* list of rooms. For example, a common list config would be no filters (i.e. all rooms) plus the range
`[0,19]`, which would cause the server to return the top 20 rooms (by activity).

Specifically, a room matches a given list if after filtering the server-maintained list of rooms by the list's filters,
the room's index in the filtered list is within the list's range.

#### Activity ordering

Rooms are ordered by last activity, based on when the last event in the room was received by the server. The exact
ordering is determined by the server implementation. (Typically, this would be essentially based on when the server
received the last event in the room, however the precise definition depends on the server architecture, especially for
servers that are "distributed").

> [!Important]
> Rooms are ***not*** ordered by "`bump_stamp`", a field returned in the room response.


### Subscriptions

A subscription is a rule that matches against a specified room ID, i.e. they allow the client to specify that a given
room should always be returned (if there are updates). This is useful if e.g. the user has opened the room and the
client always wants to get the latest data for that room.

The server MUST ensure that user has permission to see any information the server returns. Currently, the user must
either be in the room, or be invited/knocked to the room. Otherwise, the room will not be returned in the response.

> [!Note]
> A future MSC may relax this requirement to allow peeking into world-readable rooms.


## Room results

A room is returned in the response if it matches at least one rule, and either there is new data to return, or the room
has not previously been sent to the client.

See the API section below for exactly what is returned. A subset may be returned if the user does not have permission to
view the room, e.g. if they are invited but not yet joined to the room.

The server MUST NOT send any room information down that the user does not have permission to see. Specifically, the
server should only return rooms the user: is or has previously been joined to, is invited to (or rejected an invite to),
or has knocked on (or had a knock rejected).

In future MSCs, an exception *may* be added for rooms that are world readable and the user has subscribed to.

The number of events in the timeline and what state is returned depends on the "room config" specified in the rules that
the room matches from the request.  If a given room matches multiple rules and therefore multiple room configs, then the
room configs are combined (to be a superset) based on the rules below. The clients can also change room configs between
requests: see ["Combining room configs"](#combining-room-configs) below for the semantics.

The data returned in the response is only the data that has changed, e.g. if the room name hasn't changed then the
`name` field will only be sent down the first sync with the room in it and not subsequently. Clients can detect if the
data returned is the full response or a delta based on the `initial` flag.


### Combining room configs

If a room matches multiple rules, and therefore multiple room configs, then the room configs must be combined into one
before being applied.

The fields are combined by taking the "superset", i.e.:
- `timeline_limit` — take the maximum timeline limit across all room configs.
- `required_state` — take the union of the required state fields, i.e. if a state event would be returned by any room
  config it is returned by the combined room config.


### Changing room configs

When a room matches one or more rules (i.e. is eligible to be returned in the sync response) that has previously been
returned to the client, the server checks whether the combined room config is different than when the room was last
eligible to be returned. If any of the fields have been changed in a way that would cause an expansion
in the events to be returned, then the server handles the change specially, as follows.

#### Changes to `timeline_limit`

Normally the timeline events returned are only the events that have been received since the last time the room was sent
to the client (i.e. only new events). However, if the `timeline_limit` has increased (to say `N`) and the server has not
previously sent down all of the latest `N` events on the connection, the server SHOULD send down the latest `N` events
even if *some* of the events have previously been sent. If the server does not know if it has sent down all events it
SHOULD send down the latest `N` events.

For example, say the latest events in the room are `A`, `B`, `C` and `D` (from earliest to latest), and the client has
previously seen `B`, `C` and `D` with a `timeline_limit` of 1. If the client increases the `timeline_limit` to 4 then
the server SHOULD return `A`, `B`, `C` and `D`. If the client instead increased `timeline_limit` to 3, then the server
would not need to return any events as it knows the client already saw `B`, `C` and `D`.

If the server does return events that predate the last time the room was sent to the client, it MUST set the
`expanded_timeline` to `true`.

> [!IMPORTANT]
> The server should return rooms that have expanded timelines immediately, rather than waiting for the next update to
the room.

This behaviour is useful to reduce bandwidth in various cases. For example, a client may specify a list with range
`[0,99]` and a `timeline_limit` of 10, plus a list with range `[100, <MAX>]` and `timeline_limit` of `1`. This would
cause the server to return the most recent 10 events for rooms with recent activity, but only 1 event for older rooms
(that the user is unlikely to visit). If an older room that we previously only returned with one timeline event receives
a new event, we'll end up sending it down with not just the new event but the previous 10 events as well (despite having
sent the second to last event previously). If the room then drops below the threshold (and so has `timeline_limit` of
1), and then receives another update (and so the `timeline_limit` increases back to 10), the server MAY choose to
remember that it has already sent the previous 10 events and only return the latest event.

#### Changes to `required_state`

Required state expansion works in a similar way. If a room has an expanded `required_state` then the server checks if
the room has any state that matches the new, but not the old, `required_state`. If so then that state is included in the
response. The server MAY chose not to send that state if the client has previously seen that state.

> [!Note]
> Synapse currently does not return rooms with expanded state immediately; instead it waits for the next update.


## Extensions

For requesting data other than room events (such as account data or typing notifications), clients can use "extensions".
These are split out into separate sections to a) make it easier for clients to specify just what they need, and b) to
make it easier to extend in the future.

Examples of extensions, which will be specified in future MSCs, are:
- To Device Messaging
- End-to-End Encryption
- Typing Notifications
- Receipts
- Presence
- Account Data


# API

The endpoint is a `POST` request with a JSON body to `/_matrix/client/v4/sync`.

## Request Body

### Top-level

| Name | Type | Required | Comment |
| - | - | - | - |
| `conn_id` | `string` | No | An optional string to identify this connection to the server. Only one sliding sync connection is allowed per given `conn_id` (empty or not). |
| `pos` | string | No | Omitted if this is the first request of a connection (initial sync). Otherwise, the `pos` token from the previous call to `/sync` |
| `timeout` | int | No | How long to wait for new events in milliseconds. If omitted the response is always returned immediately, even if there are no changes. Ignored when no `pos` is set. |
| `set_presence` | string | No | Same as in `/v3/sync`, controls whether the client is automatically marked as online by polling this API. <br/><br/> If this parameter is omitted then the client is automatically marked as online when it uses this API. Otherwise if the parameter is set to “offline” then the client is not marked as being online when it uses this API. When set to “unavailable”, the client is marked as being idle. <br/><br/> An unknown value will result in a 400 error response with code `M_INVALID_PARAM`. |
| `lists` | `{string: SyncListConfig}` | No | Sliding window API. A map of list key to list information (`SyncListConfig`). The list keys are used by the client to refer to the lists.  <br/><br/> Max lists: 100. <br/> The list keys must follow the grammar of "opaque identifiers". |
| `room_subscriptions` | `{string: RoomSubscription}` | No | A map of room ID to room subscription information. Used to subscribe to a specific room. Sometimes clients know exactly which room they want to get information about e.g by following a permalink or by refreshing a webapp currently viewing a specific room. The sliding window API alone is insufficient for this use case because there's no way to say "please track this room explicitly". |
| `extensions` | `{string: ExtensionConfig}` | No | A map of extension key to extension config. Different extensions have different configuration formats. |


### `SyncListConfig`

| Name | Type | Required | Comment |
| - | - | - | - |
| `timeline_limit` | `int` | Yes | The maximum number of timeline events to return per response. The server may cap this number. |
| `required_state` | `RequiredStateRequest` | Yes | Required state for each room returned. |
| `range` | `[int, int]` | No | Sliding window range. If this field is missing, no sliding window is used and all rooms are returned in this list. Integers are *inclusive*, and are 0-indexed. (This is a 2-tuple.) |
| `filters` | `SlidingRoomFilter` | No | Filters to apply to the list. |

### `RoomSubscription`

| Name | Type | Required | Comment |
| - | - | - | - |
| `timeline_limit` | `int` | Yes | Same as in `SyncListConfig` |
| `required_state` | `RequiredStateRequest` | Yes | Same as in `SyncListConfig` |

### `RequiredStateRequest`

Describes the set of state that the server should return for the room.

| Name | Type | Required | Comment |
| - | - | - | - |
| `include` | `[RequiredStateElement]` | No | The set of state to return (unless filtered out by `exclude`), if any. |
| `exclude` | `[RequiredStateElement]` | No | The set of state to filter out before returning, if any. |
| `lazy_members` | `bool` | No | Whether to enable lazy loaded membership behaviour. Defaults to `false`. |


#### `RequiredStateElement`

| Name | Type | Required | Comment |
| - | - | - | - |
| `type` | `string` | No | The event type to match. If omitted then matches all types. |
| `state_key` | `string` | No | The event state key to match. If omitted then matches all state keys. <br/><br/> Note: it is possible to match a specific state key, for all event types, by specifying `state_key` but leaving `type` unset. |



#### Lazy loaded memberships

Room members can be lazily-loaded by using the `lazy_members` flag. Typically, when you view a room, you want to
retrieve all state events except for `m.room.member` events which you want to lazily load. To get this behaviour, clients
can send the following:

```jsonc
    {
        "required_state": {
            "include": [{}],  // An empty object matches everything
            "lazy_members": true
        }
    }
```

This is (almost) the same as [lazy loaded
memberships](https://spec.matrix.org/v1.16/client-server-api/#lazy-loading-room-members) in `/v3/sync`. When specified,
the server will return the membership events for:
1. All the `senders` of events in `timeline_events`, excluding membership events that were previously returned. This
   ensures that the client can render all the timeline events without having to fetch more events from the server.
1. The target (i.e. `state_key`) of all membership events in `timeline_events`, excluding membership events previously
   returned.
1. All membership updates since the last sync when `limited` is false (i.e. non-gappy syncs). This allows the client to
   cache the membership list without requiring the server to send all membership updates for large gaps. Caching is
   useful as it reduces the frequency that clients have to fetch the full membership list from the server, which needs
   to happen e.g. to send an encrypted message to the room. Note that clients can't rely on seeing membership changes in
   the `timeline` section to keep the current state up-to-date, due to state resolution.


Memberships returned to the client due to `lazy_members` are *not* filtered by `exclude`.


#### Combining `required_state`

When combining room configs with different `required_state` fields the result must be the superset of them all. There
are two approaches server-side for handling this: a) keep the `required_state` separate and return any state that
matches any of them, or b) merge the fields together, however care must be taken to correctly account for wildcards.

#### Examples

Simple example that returns the create event and power levels:

```jsonc
    {
        "required_state": {
            "include": [
                {"type": "m.room.create", "state_key": ""},
                {"type": "m.room.power_levels", "state_key": ""},
            ],
        }
    }
```

An example that returns all the state except the create event:

```jsonc
    {
        "required_state": {
            "include": [{}],  // An empty object matches everything
            "exclude": [{"type": "m.room.create", "state_key": ""}]
        }
    }
```



### `SlidingRoomFilter`

| Name | Type | Required | Comment |
| - | - | - | - |
| `is_dm` | `bool` | No | Flag which only returns rooms present (or not) in the `m.direct` entry in account data.<br/><br/> If unset, both DM rooms and non-DM rooms are returned. If False, only non-DM rooms are returned. If True, only DM rooms are returned. |
| `spaces` | `[string]` | No | Filter the room based on the space they belong to according to `m.space.child` state events. <br/><br/> If multiple spaces are present, a room can be part of any one of the listed spaces (OR'd). The server will inspect the `m.space.child` state events for the JOINED space room IDs given. Servers MUST NOT navigate subspaces. It is up to the client to give a complete list of spaces to navigate. Only rooms directly mentioned as `m.space.child` events in these spaces will be returned. Unknown spaces or spaces the user is not joined to will be ignored. |
| `is_encrypted` | `bool` | No | Flag which only returns rooms which have an `m.room.encryption` state event. <br/><br/> If unset, both encrypted and unencrypted rooms are returned. If `false`, only unencrypted rooms are returned. If `True`, only encrypted rooms are returned. |
| `is_invited` | `bool` | No | Flag which only returns rooms the user is currently invited to. <br/><br/> If unset, both invited and joined rooms are returned. If `false`, no invited rooms are returned. If `true`, only invited rooms are returned. |
| `room_types` | `[string \| null]` | No | If specified, only rooms where the `m.room.create` event has a `type` matching one of the strings in this array will be returned. <br/><br/> If this field is unset, all rooms are returned regardless of type. This can be used to get the initial set of spaces for an account. For rooms which do not have a room type, use `null` to include them. |
| `not_room_types` | `[string \| null]` | No | Same as `room_types` but inverted.<br/><br/> This can be used to filter out spaces from the room list. If a type is in both `room_types` and `not_room_types`, then `not_room_types` wins and they are not included in the result. |
| `tags` | `[string]` | No | Filter the room based on its room tags.<br/><br/> If multiple tags are  present, a room can have any one of the listed tags (OR'd). |
| `not_tags` | `[string]` | No | Filter the room based on its [room tags](https://spec.matrix.org/v1.16/client-server-api/#room-tagging).<br/><br/> Takes priority over `tags`. For example, a room with tags A and B with filters `tags: [A]` `not_tags: [B]` would NOT be included because `not_tags` takes priority over `tags`. This filter is useful if your rooms list does NOT include the list of favourite rooms again. |


### Example request

```jsonc
{
    "conn_id": "main",

    // Sliding Window API
    "lists": {
        "foo-list": {
            "range": [0, 99],
            "required_state": {
                "include": [
                    {"type": "m.room.create", "state_key": ""},
                ],
                "lazy_members": true,
            },
            "timeline_limit": 10,
            "filters": {
                "is_dm": true
            },
        }
    },
    // Room Subscriptions API
    "room_subscriptions": {
        "!sub1:bar": {
            "required_state": { "include": [{}] },
            "timeline_limit": 10,
        }
    }
}
```


## Response Body


### Top-level

| Name | Type | Required | Comment |
| - | - | - | - |
| `pos` | `string` | Yes | The next position token in the sliding window to request. |
| `lists` | `{string: SyncListResult}` | No | A map of list key to list results. |
| `rooms` | `{string: RoomResult}` | No | A map of room ID to room results. |
| `extensions` | `{string: ExtensionResult}` | No | A map of extension key to extension results. Different extensions have different result formats. |


### `SyncListResult`

| Name | Type | Required | Comment |
| - | - | - | - |
| `count` | `int` | Yes | The total number of entries in the list. |


### `RoomResult`

Not all fields will be returned depending on the user's membership in the room.

All fields in this section may be omitted. When `initial` is set to `false` then an omitted field means that the field
remains unchanged from its previous value. When `initial` is set to `true` then an omitted field means that the field is
not set, e.g. if `initial` is `true` and `name` is not set then the room has no name. Care must be taken by clients to
ensure that if they previously saw that the room had a `name`, then it MUST be cleared if it receives a room response
with `initial: true` and no `name` field.

#### Common fields

These fields are common to all `RoomResult` values. Further fields may be included depending on the user's `membership`, and
are defined below.

| Name | Type | Required | Comment |
| - | - | - | - |
| `bump_stamp` | `int` | No | An integer that can be used to sort rooms based on the last "proper" activity in the room. Greater means more recent. <br/><br/> "Proper" activity is defined as an event being received is one of the following types: `m.room.create`, `m.room.message`, `m.room.encrypted`, `m.sticker`, `m.call.invite`, `m.poll.start`, `m.beacon_info`. <br/><br/> For rooms that the user is not currently joined to, this instead represents when the relevant membership happened, e.g. when the user left the room. <br/><br/> The exact value of `bump_stamp` is opaque to the client, a server may use e.g. an auto-incrementing integer, a timestamp, etc. <br/><br/> The `bump_stamp` may decrease in subsequent responses, if e.g. an event was redacted/removed (or purged in cases of retention policies). <br/><br/> If omitted, the `bump_stamp` has not changed. |
| `membership` | `string` | No | The current membership of the user, or omitted if the does not a have a membership event in the room (for peeking). |
| `lists` | `[string]` | No | The name of the lists that match this room. The field is omitted if it doesn't match any list and is included only due to a subscription. |

#### Currently or previously joined rooms

When a user is or has been in the room, the following field are also returned:

| Name | Type | Required | Comment |
| - | - | - | - |
| `name` | `string` | No | Room name or calculated room name. |
| `avatar` | `string` | No | Room avatar |
| `heroes` | `[StrippedHero]` | No | A truncated list of users in the room that can be used to calculate the room name. Will first include joined users, then invited users, and then finally left users: the same users as the `m.heroes` section in the [`/v3/sync` specification](https://spec.matrix.org/v1.16/client-server-api/#get_matrixclientv3sync_response-200_roomsummary) |
| `is_dm` | `bool` | No | Flag to specify whether the room is a direct-message room (according to account data). If absent the room is not a DM room. |
| `initial` | `bool` | No | Flag which is set when this is the first time the server is sending this data on this connection, or if the client should replace all room data with what is returned. Clients can use this flag to replace or update their local state. The absence of this flag means `false`. |
| `expanded_timeline` | `bool` | No | Flag which is set if we're returning more historic events due to the timeline limit having increased. See "Changing room configs" section. |
| `required_state` | `[Event\|StateStub]` | No | Changes in the current state of the room. <br/><br/> To handle state being deleted, the list may include a `StateStub` type (c.f. schema below) that only has `type` and `state_key` fields. The presence or absence of `content` field can be used to differentiate between the two cases. |
| `timeline_events` | `[Event]` | No | The latest events in the room. May not include all events if e.g. there were more events than the configured `timeline_limit`, c.f. the `limited` field. <br/><br/> If `limited` is true then we include bundle aggregations for the event, as per `/v3/sync`. <br/><br/> The last event in the list is the most recent. |
| `prev_batch` | `string` | No | A token that can be passed as a start parameter to the `/rooms/<room_id>/messages` API to retrieve earlier messages. |
| `limited` | `bool` | No | True if there are more events since the previous sync than were included in the `timeline_events` field, or that the client should paginate to fetch more events.<br/><br/> Note that server may return fewer than the requested number of events and still set `limited` to true, e.g. because there is a gap in the history the server has for the room. <br/><br/>Absence means `false` |
| `num_live` | `int` | No | The number of timeline events which have "just occurred" and are not historical, i.e. that have happened since the previous sync request. The last `N` events are 'live' and should be treated as such.<br/><br/> This is mostly useful to e.g. determine whether a given `@mention` event should make a noise or not. Clients cannot rely solely on the absence of `initial: true` to determine live events because if a room not in the sliding window bumps into the window because of an `@mention` it will have `initial: true` yet contain a single live event (with potentially other old events in the timeline). |
| `joined_count` | `int` | No | The number of users with membership of join, including the client's own user ID. (same as `/v3/sync` `m.joined_member_count`) |
| `invited_count` | `int` | No |  The number of users with membership of invite. (same as `/v3/sync` `m.invited_member_count`) |
| `notification_count` | `int` | No | The total number of unread notifications for this room. (same as `/v3/sync`). <br/><br/> Does not included threaded notifications, which are returned in an extension. |
| `highlight_count` | `int` | No | The number of unread notifications for this room with the highlight flag set. (same as `/v3/sync`) <br/><br/> Does not included threaded notifications, which are returned in an extension. |


> [!Note]
> Synapse always returns 0 for `notification_count` and `highlight_count`


#### Invite/knock/rejections

For rooms the user has not been joined to the client also gets the stripped state events. This is commonly the case for
invites or knocks, but can also be for when the user has rejected an invite.

| Name | Type | Required | Comment |
| - | - | - | - |
| `stripped_state` | `[StrippedState]` | Yes  | Stripped state events (for rooms where the user is invited). Same as `rooms.invite.$room_id.invite_state` for invites in `/v3/sync`. |

The reason the full fields from the previous section can't be included is because we don't have any of that information
for remote invites and the user isn't participating in the room yet so we shouldn't leak anything to them. We can only
rely on the information in the invite/knock/etc event.

> [!Note]
> Synapse currently may inadvertently return extra fields from the previous section.

> [!Note]
> Knock support hasn't been implemented in Synapse.


### `StrippedHero` type

The `StrippedHero` has the following fields:


| Name | Type | Required | Comment |
| - | - | - | - |
| `user_id` | string | Yes | The user ID of the hero. |
| `displayname` | string | No | The display name of the user from the membership event, if set |
| `avatar_url` | string | No | The avatar url from the membership event, if set |


### `StateStub` type

The `StateStub` is used in `required_state` to indicate that a piece of state has been deleted.

| Name | Type | Required | Comment |
| - | - | - | - |
| `type` | string | Yes | The `type` of the state entry that was deleted |
| `state_key` | string | Yes | The `state_key` of the state entry that was deleted |


### Example response

```jsonc
{
  "pos": "s58_224_0_13_10_1_1_16_0_1",
  "lists": {
      "foo-list": {
          "count": 1337,
      }
  },
  "rooms": {
      "!sub1:bar": {
          "name": "Alice and Bob",
          "avatar": "mxc://...",
          "initial": true,
          "required_state": [
              {
                "sender":"@alice:example.com",
                "type":"m.room.create",
                "state_key":"",
                "content": {}
              },
              ...
          ],
          "timeline": [
              {"sender":"@alice:example.com","type":"m.room.message", "content":{"body":"B"}},
              ...
          ],
          "prev_batch": "t111_222_333",
          "joined_count": 41,
          "invited_count": 1,
          "notification_count": 1,
          "highlight_count": 0,
          "num_live": 2,
          "membership": "join"
      },
      ...
  },
  "extensions": {}
}
```

# Common patterns

Below are some potentially common patterns that clients may wish to use.

## Paginating room list

Pagination of the room list is achieved by the client increasing the range of one (or more) lists.

For example an initial request might have a list called `all_rooms` specifying a range of `[0,19]` in the initial
request, and the server will respond with the top 20 rooms (by most recently updated). On the second request the client
may change the range to `[0,99]`, at which point the server will use the top 100 rooms and respond with the ones that
either a) weren’t sent down in the first request, or b) have updates since the first request.

Clients can increase and decrease the range as they see fit. A common approach would be to start with a small window
and grow that until the range covers all the rooms. After some threshold of the app being offline it may reduce the
range back down and incrementally grow it again. This allows for ensuring that a limited amount of data is requested at
once, to improve response times.

## Example usage

This section gives an example of how a client can use this API (roughly based on how Element X currently uses the API).

When the app starts up it configures a single list with a range of `[0, 19]` (to get the top 20 rooms) and a
`timeline_limit` of 1. This returns quickly with the top 20 rooms (or just the changes in the top 20 rooms if a token
was specified).

The client then increases the range (in the next request) to `[0, 99]`, which will return the next 80 rooms. Note: the
range here matches 100 rooms, however we only send the 80 rooms that we didn't send down in the previous request.

The client can use room subscriptions, with a `timeline_limit` of 20, to preload history for the top rooms. This means
that if the user clicks on one of the top rooms the app can immediately display a screens worth of history. (An
alternative would be to have a second list with a static range of `[0, 19]` and a `timeline_limit` of 20. The downside
is that the clients may use a different order for the room list and so always fetching extra events for the top 20 rooms
may return more data than required.)

The client can keep increasing the list range in increments to pull in the full list of rooms. The client uses the
returned `count` for the list to know when to stop expanding the list.

The client *may* decided to reduce the range back to `[0, 19]` (and then subsequently incrementally expand the range),
this can be done.

When the client is expecting a fast response (e.g. while expanding the lists), it should set the `timeout` parameter to
0 to ensure the server doesn't block waiting for new data. This can easily happen if the app starts and sends the first
request with a `pos` parameter, if the client shows a spinner but doesn't set a timeout then the request may take a long
time to return (if there were no updates to return).

# Alternatives

## Pagination

In practice, having the client specify the range to use for the lists is often sub-optimal. The client generally wants
to have the sync request return as quickly as possible, but it doesn't know how much data the server has to return and
so whether to increase or decrease the range.

An alternative is for the client to specify a `page_size`, where the server sends down at most `page_size` number of
rooms. If there are more rooms to send to the client (beyond `page_size`), then the client can request to "paginate" in
these missed updates in subsequent updates.

Since this may require substantial client side changes compared with the current implementation, this should be explored
separately.

## Timeline event trickling

If the `timeline_limit` is increased then the server will send down historic data (c.f. "Changing room configs") with
`expanded_timeline` set, which allows the clients to easily preload more history in recent rooms.

This mechanism is fiddly to implement, and ends up resending down events that we have previously sent to the client.

A simpler alternative is to use `/messages` to fetch the history. This has two main problems: 1) clients generally want
to preload history for multiple rooms at once, and 2) `/messages` can be slow if it tries to backfill over federation.

We could implement a bulk `/messages` endpoint, where the client would specify multiple rooms and `prev_batch` tokens.
We can also add a flag to disable attempting to backfill over pagination (to match the behaviour of the sync timeline).

Another alternative is to do one initial sync with a low `timeline_limit` and then another with the higher
`timeline_limit`. This is conceptually simple, though has the main downside of potentially duplicating a lot of data
(such as state). The approach also doesn't support the use case for having two lists so that rooms that bubble to the
top of the room list automatically get expanded timelines.

# Security considerations

Care must be taken, as with `/v3/sync`, to ensure that only the data that the user is authorized to see is returned in
the response.

Servers SHOULD limit the amount of data that they store per-user to guard against resource consumption, e.g. limiting
the number of connections a device can have active. This protects against malicious clients creating large numbers of
connections that get persisted to the database.

Servers MAY decide to expire the sync connection if the generated response on an incremental request is likely very
large or expensive to compute.


# Unstable prefix

The unstable URL for simplified sliding sync is `/_matrix/client/unstable/org.matrix.simplified_msc3575/sync`. The flag
in `/_matrix/client/versions` is `org.matrix.simplified_msc3575`.


# Appendix

## Open questions

1. <del>In the response should we specify which lists a room is part of?</del>
1. <del>Should `knock_state` and  `invite_state` use the same name in the room response, e.g. `stripped_state`?</del>
1. <del>In the room response how do we inform clients that a piece of state was deleted (rather than added/updated)?</del>
1. <del>We need to decide what to do with `unstable_expanded_timeline`. We can either rename it to `expanded_timeline`, or
   remove the functionality and replace it with a bulk `/messages` endpoint (for multiple rooms). See "Timeline event
   trickling" section.</del>
1. <del>The request `required_state` field is a bit confusing and uses special strings (like `"*"` and `"$LAZY"`).</del>
1. Duplication between room response `heroes` and `required_state` when specifying `lazy_members`, e.g. should we drop
   `heroes` if we are returning membership events?
1. <del>Should the room response include the user's current membership? The client can always request it via
   `required_state`, but that may be wasted if the client doesn't need any other information from the member event.</del>
1. Should we remove the `highlight_count` and `notification_count` fields, given clients increasingly must calculate
   this themselves, and Synapse currently doesn't implement it nor does Element X use it.
1. Should we support subscribing to rooms the user is not a member of, i.e. peeking for world readable rooms.
1. Should we support timeline filtering?
1. <del>Should we move `pos`, and other URL params, into the request body? This would allow web clients to cache the CORS
   requests, rather than having to pre-flight each request.</del>
1. How do we make it so that the clients don't have to send up the same body each time?

## TODOs

1. <del>If we're keeping the notification counts we should add `unread_thread_notifications`</del>
    - This should exist in the thread extension
1. We should add `knock_servers` as per MSC4233, if that lands.


## Changelog

Changes from the initial implementation of simplified sliding sync.

1. Add `set_presence` URL param.
2. Rename `invite_state` to `stripped_state`
3. When state is deleted we return a stub `{"type: "..", "state_key": ".." }` in `required_state`.
4. Rename `unstable_expanded_timeline` to `expanded_timeline`
5. Add `lists` to room response
6. Add `membership` field to room response.
7. Change the format of `required_state` in the request.
8. Move URL parameters to the request body. This is so that on web every request doesn't need to be pre-flighted for
   CORS.
9. Convert `ranges` to `range` in `SyncListConfig` in the request.
10. <del>Make the `lists` request field "sticky".</del>
11. Rename `is_invite` to `is_invited`.
