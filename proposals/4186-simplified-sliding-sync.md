# MSC4186: Simplified Sliding Sync

The current `/sync` endpoint scales badly as the number of rooms on an account increases. It scales badly because all
rooms are returned to the client, incremental syncs are unbounded and slow down based on how long the user has been
offline, and clients cannot opt-out of a large amount of extraneous data such as receipts. On large accounts with
thousands of rooms, the initial sync operation can take tens of minutes to perform. This significantly delays the
initial login to Matrix clients, and also makes incremental sync very heavy when resuming after any significant pause in
usage.

Note: this is a “simplified” version of the sliding sync API proposed in
[MSC3575](https://github.com/matrix-org/matrix-spec-proposals/pull/3575), based on paring back that API based
on real world use cases and usages.


# Goals

This improved `/sync` mechanism has a number of goals:

- Sync time should be independent of the number of rooms you are in.
- Time from opening of the app (when already logged in) to confident usability should be as low as possible.
- Time from login on existing accounts to usability should be as low as possible.
- Bandwidth should be minimized.
- Support lazy-loading of things like read receipts (and avoid sending unnecessary data to the client)
- Support informing the client when room state changes from under it, due to state resolution.
- Clients should be able to work correctly without ever syncing in the full set of rooms they’re in.
- Don’t incremental sync rooms you don’t care about.
- Servers should not need to store all past since tokens. If a since token has been discarded we should gracefully
  degrade to initial sync.

These goals shaped the design of this proposal.


# Proposal

The core differences between sync v2 and simplified sliding sync are:

- The server initially only sends the most recent N rooms to the client (where N is specified by the client), which then
  can paginate in older rooms in subsequent requests
- The client can configure which information the server will return for different sets of rooms (e.g. a smaller timeline
  limit for older rooms).
- The client can filter what rooms it is interested in
- The client can maintain multiple sync loops (with some caveats)
  - This is useful for e.g. iOS clients which have a separate process to deal with notifications, as well as allowing
    the app to split handling of things like encryption entirely from room data.

The basic operation is similar between sync v2 and simplified sliding sync: both use long-polling with tokens to fetch
updates from the server. I.e., the basic operation of both APIs is to do an “initial” request and then repeatedly call
the API supplying the token returned in the previous response in the subsequent “incremental” request.


## Lists and room subscriptions

The core component of a sliding sync request is “lists”, which specify what information to return about which rooms.
Each list specifies some filters on rooms (e.g. ignore spaces), the range of filtered rooms to select (e.g. the most
recent 20 filtered rooms), and the config for the data to return for those rooms (e.g. the required state, timeline
limit, etc). The order of rooms is always done based on when the server received the most recent event for the room.

The client can also specify config for specific rooms if it has their room ID, these are known as room subscriptions.

Multiple lists and subscriptions can be specified in a request. If a room matches multiple lists/subscriptions then the
config is “combined” to be the superset of all configs (e.g. take the maximum timeline limit). See below for the exact
algorithm.

The server tracks what data has been sent to the client in which rooms. If a room matches a list or subscription that
hasn’t been sent down before, then the server will respond with the full metadata about the room indicated by `initial:
true`. If a room stops matching a list (i.e. it falls out of range) then no further updates will be sent until it starts
matching a list again, at which point the missing updates (limited by the `timeline_limit`) will be sent down. However,
as clients are now expected to paginate all rooms in the room list in the background (in order to correctly order and
search them), the act of a room falling out of range is a temporary edge-case.


## Pagination

Pagination is achieved by the client increasing the ranges of one (or more) lists.

For example an initial request might have a list called `all_rooms` specifying a range of `0..20` in the initial
request, and the server will respond with the top 20 rooms (by most recently updated). On the second request the client
may change the range to `0..100`, at which point the server will respond with the top 100 rooms that either a) weren’t
sent down in the first request, or b) have updates since the first request.

Clients can increase and decrease the ranges as they see fit. A common approach would be to start with a small window
and grow that until the range covers all the rooms. After some threshold of the app being offline it may reduce the
range back down and incrementally grow it again. This allows for ensuring that a limited amount of data is requested at
once, to improve response times.


## Connections

Clients can have multiple “connections” (i.e. sync loops) with the server, so long as each connection has a different
`conn_id` set in the request.

Clients must only have a single request in-flight at any time per connection (clients can have multiple connections by
specifying a unique `conn_id`). If a client needs to send another request before receiving a response to an in-flight
request (e.g. for retries or to change parameters) the client *must* cancel the in-flight request (at the HTTP level)
and *not* process any response it receives for it.

In particular, a client must use the returned `pos` value in a response as the `since` param in exactly one request that
the client will process the response for. Clients must be careful to ensure that when processing a response any new
requests use the new `pos`, and any in-flight requests using an old `pos` are canceled.

The server cannot assume that a client has received a response until it receives a new request with the `since` token
set to the `pos` it returned in the response. The server must ensure that any per-connection state it tracks correctly
handles receiving multiple requests with the same `since` token (e.g. the client retries the request or decides to
cancel and resend a request with different parameters).

A server may decide to “expire” connections, either to free resources or because the server thinks it would be faster
for the client to start from scratch (e.g. because there are many updates to send down). This is done by responding with
a 400 HTTP status and an error code of `M_UNKNOWN_POS`.


## List configuration

**TODO**, these are the same as in [MSC3575](https://github.com/matrix-org/matrix-spec-proposals/pull/3575):

- Required state format
- The filters
- Lazy loading of members
- Combining room config


## Room config changes

When a room comes in and out of different lists or subscriptions, the effective `timeline_limit` and `required_state`
parameters may change. This section outlines how the server should handle these cases.

If the `timeline_limit` *increases* then the server *may* choose to send down more historic data. This is to support the
ability to get more history for certain rooms, e.g. when subscribing to the currently visible rooms in the list to
precache their history. This is done by setting `unstable_expanded_timeline` to true and sending down the last N events
(this may include events that have already been sent down). The server may choose not to do this if it believes it has
already sent down the appropriate number of events.

If new entries are added to  `required_state` then the server must send down matching current state events.


## Extensions

We anticipate that as more features land in Matrix, different kinds of data will also want to be synced to clients. Sync
v2 did not have any first-class support to opt-in to new data. Sliding Sync does have support for this via "extensions".
Extensions also allow this proposal to be broken up into more manageable sections. Extensions are requested by the
client in a dedicated extensions block.

In an effort to reduce the size of this proposal, extensions will be done in separate MSCs. There will be extensions
for:

- To Device Messaging \- MSC3885
- End-to-End Encryption \- MSC3884
- Typing Notifications \- MSC3961
- Receipts \- MSC3960
- Presence \- presence in sync v2: spec
- Account Data \- account\_data in sync v2: MSC3959
- Threads

**TODO** explain how these interact with the room lists, this is the same as in
[MSC3575](https://github.com/matrix-org/matrix-spec-proposals/pull/3575)

## Request format

```javascript
{
  "conn_id":  "<conn_id>",  // Client chosen ID of the connection, c.f. "Connections"

  // The set of room lists
  "lists": {
    // An arbitrary string which the client is using to refer to this list for this connection.
    "<list-name>": {

      // Sliding window ranges, c.f. Lists and room subscriptions
      "ranges": [[0, 10]],

      // Filters to apply to the list.
      "filters": {
        // Flag which only returns rooms present (or not) in the DM section of account data.
        // If unset, both DM rooms and non-DM rooms are returned. If false, only non-DM rooms
        // are returned. If true, only DM rooms are returned.
        "is_dm": true|false|null,

        // Flag which only returns rooms which have an `m.room.encryption` state event. If unset,
        // both encrypted and unencrypted rooms are returned. If false, only unencrypted rooms
        // are returned. If true, only encrypted rooms are returned.
        "is_encrypted": true|false|null,

        // Flag which only returns rooms the user is currently invited to. If unset, both invited
        // and joined rooms are returned. If false, no invited rooms are returned. If true, only
        // invited rooms are returned.
        "is_invite": true|false|null,

        // If specified, only rooms where the `m.room.create` event has a `type` matching one
        // of the strings in this array will be returned. If this field is unset, all rooms are
        // returned regardless of type. This can be used to get the initial set of spaces for an account.
        // For rooms which do not have a room type, use 'null' to include them.
        "room_types": [ ... ],

        // Same as "room_types" but inverted. This can be used to filter out spaces from the room list.
        // If a type is in both room_types and not_room_types, then not_room_types wins and they are
        // not included in the result.
        "not_room_types": [ ... ],
      },

      // The maximum number of timeline events to return per response.
      "timeline_limit": 10,

      // Required state for each room returned. An array of event type and state key tuples.
      // Elements in this array are ORd together to produce the final set of state events
      // to return. One unique exception is when you request all state events via ["*", "*"]. When used,
      // all state events are returned by default, and additional entries FILTER OUT the returned set
      // of state events. These additional entries cannot use '*' themselves.
      // For example, ["*", "*"], ["m.room.member", "@alice:example.com"] will _exclude_ every m.room.member
      // event _except_ for @alice:example.com, and include every other state event.
      // In addition, ["*", "*"], ["m.space.child", "*"] is an error, the m.space.child filter is not
      // required as it would have been returned anyway.
      "required_state": [ ... ],
    }
  },

  // The set of room subscriptions
  "room_subscriptions": {
    // The key is the room to subscribe to.
    "!foo:example.com": {
      // These have the same meaning as in `lists` section
      "timeline_limit": 10,
      "required_state": [ ... ],
    }
  },

  // c.f. "Extensions"
  "extensions": {
  }
}
```


## Response format

```javascript
{
  // The position to use as the `since` token in the next sliding sync request.
  // c.f. Connections.
  "pos": "<opaque string>",

  // Information about the lists supplied in the request.
  "lists": {
    // Matches the list name supplied by the client in the request
    "<list-name>" {
      // The total number of rooms that match the list's filter. Note that rooms can be in
      // multiple lists, so may be double counted.
      "count": 1234,
    }
  },

  // Aggregated rooms from lists and room subscriptions. There will be one entry per room, even if
  // the room appears in multiple lists and/or room subscriptions.
  "rooms": {
    "!foo:example.com": {
      // The room name (as specified by any `m.room.name` event), if one exists. Only sent initially
      // and when it changes.
      "name": str|null,
      // The room avatar, if one exists. Only sent initially and when it changes.
      "avatar_url": str|null,
      // The "heroes" for the room, if there is no room name. Only sent initially and when it changes.
      "heroes": [
        {"user_id":"@alice:example.com","displayname":"Alice","avatar_url":"mxc://..."},
      ],

      // Flag which is set when this is the first time the server is sending this data on this connection.
      // When set the client must replace any stored metadata for the room with the new data. In
      // particular, the state must be replaced with the state in `required_state`.
      "initial": true|null,

      // Same as in sync v2. Indicates whether there are more events to fetch than those in the timeline.
      "limited:" true|null,
      // Indicates if we have "expanded" the timeline due to the timeline_limit changing, c.f. Room config
      // changes above.
      "unstable_expanded_timeline": true|null,
      // The list of events, sorted least to most recent.
      "timeline": [ ... ],
      // The current state of the room as a list of events. This is the full state if `initial`
      // state is set, otherwise it is a delta from the previous sync.
      "required_state": [ ... ],
      // The number of timeline events which have just occurred and are not historical.
      // The last N events are 'live' and should be treated as such.
      "num_live": 1,
      // Same as sync v2, passed to `/messages` to fetch more past events.
      "prev_batch": "...",

      // For invites this is the stripped state of the room at the time of invite
      "invite_state": [ .. ],

      // For knocks this is the stripped state of the room at time of knock
      "knock_state": [ .. ],

      // Whether the room is a DM room.
      "is_dm": true|null,

      // An opaque integer that can be used to sort the rooms by "Bump Stamp"
      "bump_stamp": 1,

      // These are the same as sync v2.
      "joined_count": 1,
      "invited_count": 1,
      "notification_count": 1,
      "highlight_count": 1,
    }
  },

  "extensions": {
  },
}
```

# Example usage

This section gives an example of how a client can use this API (roughly based on how Element X currently uses the API).

When the app starts up it configures a single list with a range of `[0, 19]` (to get the top 20 rooms) and a
`timeline_limit` of 1. This returns quickly with the top 20 rooms (or just the changes in the top 20 rooms if a token
was specified).

The client then increases the range (in the next request) to `[0, 99]`, which will return the next 80 rooms. The server
may sort the rooms differently than they are returned by the server (e.g. they may ignore reactions for sorting
purposes). Note: the range here matches 100 rooms, however we only send the 80 rooms that we didn't send down in the
previous request.

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
request with a `since` parameter, if the client shows a spinner but doesn't set a timeout then the request may take a
long time to return (if there were no updates to return).


# Alternatives / changes

There are a number of potential changes that we could make.

## Pagination

In practice, having the client specify the ranges to use for the lists is often sub-optimal. The client generally wants
to have the sync request return as quickly as possible, but it doesn't know how much data the server has to return and
so whether to increase or decrease the range.

An alternative is for the client to specify a `page_size`, where the server sends down at most `page_size` number of
rooms. If there are more rooms to send to the client (beyond `page_size`), then the client can request to "paginate" in
these missed updates in subsequent updates.

Since this would require client side changes, this should be explored in a separate MSC.

## Timeline event trickling

If the `timeline_limit` is increased then the server will send down historic data (c.f. "Room config changes"), which
allows the clients to easily preload more history in recent rooms.

This mechanism is fiddly to implement, and ends up resending down events that we have previously sent to the client.

A simpler alternative is to use `/messages` to fetch the history. This has two main problems: 1) clients generally want
to preload history for multiple rooms at once, and 2) `/messages` can be slow if it tries to backfill over federation.

We could implement a bulk `/messages` endpoint, where the client would specify multiple rooms and `prev_batch` tokens.
We can also add a flag to disable attempting to backfill over pagination (to match the behaviour of the sync timeline).

## `required_state` response format

The format of returned state in `required_state` is a list of events. This does now allow the server to indicate if a
"state reset" has happened which removed an entry from the state entirely (rather than it being replaced with another
event).

This is particularly problematic if the user gets "state reset" out of the room, where the server has no mechanism to
indicate to the client that the user has effectively left the room (the server has no leave event to return).

We may want to allow special entries in the `required_state` list of the form
`{"type": .., "state_key": .., content: null}` to indicate that the state entry has been removed.


# Security considerations

Care must be taken, as with sync v2, to ensure that only the data that the user is authorized to see is returned in the
response.


# Unstable prefix

The unstable URL for simplified sliding sync is `/org.matrix.simplified_msc3575/sync`. The flag in `/versions` is
`org.matrix.simplified_msc3575`.
