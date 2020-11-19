### MSC2836: Threading

*This MSC probably supersedes https://github.com/matrix-org/matrix-doc/issues/1198*

Matrix does not have arbitrarily nested threading for events. This is a desirable feature for implementing clones of social
media websites like Twitter and Reddit. The aim of this MSC is to define the simplest possible API shape to implement threading
in a useful way. This MSC does NOT attempt to consider use cases like editing or reactions, which have different requirements
to simple threading (replacing event content and aggregating reactions respectively).

The API can be broken down into 2 sections:
 - Making relationships: specifying a relationship between two events.
 - Querying relationships: asking the server for relationships between events.

The rest of this proposal will outline the proposed API shape along with the considerations and justifications for it.

#### Making relationships

Relationships are made when sending or updating events. The proposed API shape is identical to
[MSC1849](https://github.com/matrix-org/matrix-doc/blob/matthew/msc1849/proposals/1849-aggregations.md):
```
{
    "type": "m.room.message",
    "content": {
        "body": "i <3 shelties",
        "m.relationship": {
            "rel_type": "m.reference",
            "event_id": "$another_event_id"
        }
    }
}
```

Justifications for this were as follows:
 - Quicker iterations by having it in event content rather than at the top-level (at the `event_id` level).
 - Ability for relationships to be modified post-event creation (e.g by editing the event).
 - Doesn't require any additional server-side work (as opposed to adding the event ID as a query param e.g `?in-reply-to=$foo:bar`).

Drawbacks include:
 - Additional work required for threading to work with E2EE. See MSC1849 for proposals, but they all boil down to having the `m.relationship`
   field unencrypted in the event `content`.

Edge cases:
 - Any event `type` can have an `m.relationship` field in its `content`.
 - Redacting an event with an `m.relationship` field DOES NOT remove the relationship. Instead, it is preserved similar to how `membership`
   is preserved for `m.room.member` events, with the following rules:
     * Remove all fields except `rel_type` and `event_id`.
     * If `rel_type` is not any of the three types `m.reference`, `m.annotation` or `m.replace` then remove it.
     * If `event_id` is not a valid event ID (`$` sigil, correct max length), then remove it.
   The decision to preserve this field is made so that users can delete offensive material without breaking the structure of a thread. This is
   different to MSC1849 which proposes to delete the relationship entirely.
 - It is an error to reference an event ID that the server is unaware of. Servers MUST check that they have the event in question: it need not
   be part of the connected DAG; it can be an outlier. This prevents erroneous relationships being made by abusing the CS API.
 - It is NOT an error to reference an event ID in another room. Cross-room threading is allowed and this proposal goes into more detail on how
   servers should handle this as a possible extension.
 - It is an error to reference yourself. Cyclical loops are still possible by using multiple events and servers should guard against this by
   only visiting events once.

#### Querying relationships

Relationships are queryed via a new CS API endpoint:
```
POST /_matrix/client/r0/event_relationships
{
    "event_id": "$abc123",         // the anchor point for the search, must be in a room you are allowed to see (normal history visibility checks apply)
    "max_depth": 4,                // if negative unbounded, default: 3.
    "max_breadth": 10,             // if negative unbounded, default: 10.
    "limit": 100,                  // the maximum number of events to return, server can override this, default: 100.
    "depth_first": true|false,     // how to walk the DAG, if false, breadth first, default: false.
    "recent_first": true|false,    // how to select nodes at the same level, if false oldest_first - servers compare against origin_server_ts, default: true.
    "include_parent": true|false,  // if event_id has a parent relation, include it in the response, default: false.
    "include_children": true|false // if there are events which reply to $event_id, include them all (depth:1) in the response: default: false.
    "direction": up|down           // if up, parent events (the events $event_id is replying to) are returned. If down, children events (events which reference $event_id) are returned, default: "down".
    "batch": "opaque_string"       // A token to use if this is a subsequent HTTP hit, default: "".
}
```
which returns:
```
{
    "events": [                    // the returned events, ordered by the 'closest' (by number of hops) to the anchor point.
        { ... }, { ... }, { ... },
    ],
    "next_batch": "opaque_string", // A token which can be used to retrieve the next batch of events, if the response is limited.
                                   // Optional: can be omitted if the server doesn't implement threaded pagination.
    "limited": true|false          // True if there are more events to return because the `limit` was reached. Servers are not obligated
                                   // to return more events, see if the next_batch token is provided or not.
}
```

Justifications for the request API shape are as follows:
 - The HTTP path: cross-room threading is allowed hence the path not being underneath `/rooms`. An alternative could be
   `/events/$event_id/relationships` but there's already an `/events/$event_id` deprecated endpoint and nesting this new MSC
   underneath a deprecated endpoint conveys the wrong meaning.
 - The HTTP method: there's a lot of data to provide to the server, and GET requests shouldn't have an HTTP body, hence opting
   for POST. The same request can produce different results over time so PUT isn't acceptable as an alternative.
 - The anchor point: pinning queries on an event is desirable as often websites have permalinks to events with replies underneath.
 - The max depth: Very few UIs show depths deeper than a few levels, so allowing this to be constrained in the API is desirable.
 - The max breadth: Very few UIs show breadths wider than a few levels, so allowing this to be constrained in the API is desirable.
 - The limit: For very large threads, a max depth/breadth can quickly result in huge numbers of events, so bounding the overall
   number of events is desirable. Furthermore, querying relationships is computationally expensive on the server, hence allowing
   it to arbitrarily override the client's limit (to avoid malicious clients setting a very high limit).
 - The depth first flag: Some UIs show a 'conversation thread' first which is depth-first (e.g Twitter), whereas others show
   immediate replies first with a little bit of depth (e.g Reddit).
 - The recent first flag: Some UIs show recent events first whereas others show the most up-voted or by some other metric.
   This MSC does not specify how to sort by up-votes, but it leaves it possible in a compatible way (e.g by adding a
   `sort_by_reaction: 👍` which takes precedence which then uses `recent_first` to tie-break).
 - The include parent flag: Some UIs allow permalinks in the middle of a conversation, with a "Replying to [link to parent]"
   message. Allowing this parent to be retrieved in one API hit is desirable.
 - The include_children flag: Some UIs allow permalinks in the middle of a conversation, with immediate children responses
   visible. Allowing the children to be retrieved in one API hit is desirable.
 - The direction enum: The decision for literal `up` and `down` makes for easier reading than `is_direction_up: false` or
   equivalent. The direction is typically `down` - find all children from this event - but there is no reason why this cannot
   be inverted to walk up the DAG instead.
 - The batch token: This allows clients to retrieve additional results. It's contained inside the HTTP body rather than as
   a query param for simplicity - all the required data that the server needs is in the HTTP body. This token is optional as
   paginating is reasonably complex and should be opt-in to allow for ease of server implementation.

Justifications for the response API shape are as follows:
 - The events array: There are many possible ways to structure the thread, and the best way is known only to the client
   implementation. This API shape is unopinionated and simple.
 - The next batch token: Its presence indicates if there are more events and it is opaque to allow server implementations the
   flexibility for their own token format. There is no 'prev batch' token as it is intended for clients to request and persist
   the data on their side rather than page through results like traditional pagination.
 - The limited flag: Required in order to distinguish between "no more events" and "more events but I don't allow pagination".
   This additional state cannot be accurately represented by an empty `next_batch` token.

Server implementation:
 - Sanity check request and set defaults.
 - Can the user see (according to history visibility) `event_id`? If no, reject the request, else continue.
 - Retrieve the event. Add it to response array.
 - If `include_parent: true` and there is a valid `m.relationship` field in the event, retrieve the referenced event.
   Apply history visibility check to that event and if it passes, add it to the response array.
 - If `include_children: true`, lookup all events which have `event_id` as an `m.relationship` - this will almost certainly require
   servers to store this lookup in a dedicated table when events are created. Apply history visibility checks to all these
   events and add the ones which pass into the response array, honouring the `recent_first` flag and the `limit`.
 - Begin to walk the thread DAG in the `direction` specified, either depth or breadth first according to the `depth_first` flag,
   honouring the `limit`, `max_depth` and `max_breadth` values according to the following rules:
     * If the response array is `>= limit`, stop.
     * If already processed event, skip.
     * Check how deep the event is compared to `event_id`, does it *exceed* (greater than) `max_depth`? If yes, skip.
     * Check what number child this event is (ordered by `recent_first`) compared to its parent, does it *exceed* (greater than) `max_breadth`? If yes, skip.
     * Process the event.
   If the event has been added to the response array already, do not include it a second time. If an event fails history visibiilty
   checks, do not add it to the response array and do not follow any references it may have. This algorithm bounds an infinite DAG
   into a "window" (governed by `max_depth` and `max_breadth`) and serves up to `limit` events at a time, until the entire window
   has been served. Critically, the `limit` _has not been reached_ when the algorithm hits a `max_depth` or `max_breadth`, it is only
   reached when the response array is `>= limit`.
 - When the thread DAG has been fully visited or the limit is reached, return the response array (and a `next_batch` if the request
   was limited). If a request comes in with the `next_batch` set to a valid value, continue walking the thread DAG from where it
   was previously left, ensuring that no duplicate events are sent, and that any `max_depth` or `max_breadth` are honoured
   _based on the original request_ - the max values always relate to the original `event_id`, NOT the event ID previously stopped at.

##### Querying relationships over federation

Relationships can be queried over federation using a new endpoint which is the same as the CS API format. See the CS API section for more info. The path
used for this new federation endpoint is `/_matrix/federation/v1/event_relationships`. There is one additional response field: `auth_chain` which contains
all the necessary auth events for the events in `events`, e.g:
```
{
    "events": [                    // the returned events, ordered by the 'closest' (by number of hops) to the anchor point.
        { ... }, { ... }, { ... },
    ],
    "next_batch": "opaque_string", // A token which can be used to retrieve the next batch of events, if the response is limited.
                                   // Optional: can be omitted if the server doesn't implement threaded pagination.
    "limited": true|false,         // True if there are more events to return because the `limit` was reached. Servers are not obligated
                                   // to return more events, see if the next_batch token is provided or not.
    "auth_chain": [                // The auth events required to authenticate events in `events`, in any order without duplicates.
        { ... }, { ... }, { ... },
    ]
}
```

Justification:
 - In an ideal world, every server would have the complete room DAG and would therefore be able to explore the full scope of a thread in a room. However,
   over federation, servers have an incomplete view of the room and will be missing many events. In absence of a specific API to explore threads over
   federation, joining a room with threads will result in an incomplete view.
 - The requirements here have a lot in common with the [Event Context API](https://matrix.org/docs/spec/client_server/r0.6.0#id131). However, the context
   API has no federated equivalent. This means any requests for events the server is unaware of will incorrectly return `404 Not Found`.
 - The same API shape is proposed to allow code reuse and because the same concerns and requirements are present for both federation and client-server.

Server behaviour:
 - When receiving a request to `/event_relationships`: ensure the server is in the room then walk the thread in the same manner as the CS API form. Do not
   make outbound `/event_relationships` requests on behalf of this request to avoid routing loops where 2 servers infinitely call `/event_relationships` to
   each other.
 - For each event returned: include all `auth_events` for that event recursively to create an auth chain and add them to `auth_chain`.
 - Servers should make outbound `/event_relationships` requests *for client requests* when they encounter an event ID they do not have. The event may have
   happened much earlier in the room which another server in the room can satisfy.

#### Cross-room threading extension

This MSC expands on the basic form to allow cross-room threading by allowing 2 extra fields to be specified
in the `unsigned` section of the event: `relationship_servers` and `relationship_room_id`:
```
{
    "type": "m.room.message",
    "content": {
        "body": "i <3 shelties",
        "m.relationship": {
            "rel_type": "m.reference",
            "event_id": "$another_event_id",
        }
    },
    "unsigned": {
      "relationship_room_id":"!someroomid:anotherhost",
      "relationship_servers": [ "localhost", "anotherhost" ]
    }
}
```

Only servers can set these fields. The server should set these fields
when an event is sent according to the following rules:
 - Check the client can view the event ID in question. If they cannot, reject the request.
 - Check that the room's `m.room.create` event allows cross-room threading by the presence of `"m.cross_room_threading": true`
   in the `content` field. If absent, it is `false`.
 - Fetch the servers *currently in the room* for the event. Add them all to `relationship_servers`.
 - Fetch the room ID that the event belongs to. Add it to `relationship_room_id`.

This proposal does not require any changes to `/createRoom` as `"m.cross_room_threading": true` can be specified via the
`creation_content` field in that API.

The `POST /event_relationships` endpoint includes a new field:
 - `auto_join: true|false`: if `true`, will automatically join the user calling `/event_relationships` to rooms they are not joined to
   in order to explore the thread. Default: `false`.

Server implementation:
 - When walking the thread DAG, if there is an event that is not known, check the relationship for `relationship_room_id` and `relationship_servers`. If
   they exist, peek into the room ([MSC2444](https://github.com/matrix-org/matrix-doc/pull/2444)), or if that is not supported,
   join the room as the user querying `/event_relationships` if and only if `"auto_join": true` in the `/event_relationships` request. This
   is required in order to allow the event to be retrieved. Server implementations can treat the auto join as the same as if the
   client made a request to [/join/{roomIdOrAlias}](https://matrix.org/docs/spec/client_server/r0.6.0#post-matrix-client-r0-join-roomidoralias)
   with the `server_name` query parameters set to those in `relationship_servers`.
 - After joining the room, the server should use the federated API `/event_relationships` to explore the thread in the newly joined room as the server
   will not have those events. These events can be stored as outliers or dropped depending on storage requirements.

Security considerations:
 - Allowing cross-room threading leaks the event IDs in a given room, as well as which servers are in the room at the point
   the reply is sent. It is for this reason that there is an opt-in flag at room creation time.

Justifications:
 - Because the client needs to be able to view the event being replied to, it is impossible for the replying client to
   respond to an event which the server is unaware of. However, it is entirely possible for queries to contain events
   which the server is unaware of if the sender was on another homeserver. For this reason, we need to contain routing
   information *somewhere* so servers can retrieve the event and continue navigating the thread. As the client and server
   already have the event which contains a relationship to another event inside an unknown room, the simplest option is to
   also contain the routing information with that relationship.
 - The fields are in the `unsigned` section so clients cannot artificially set them, and because `unsigned` is where a lot
   of other server-calculated metadata resides.

##### Backreferences

Using the threading model proposed above, events contain information about their parents but parents do not contain information about their
children. This means that events can follow their path up to the root event but cannot explore siblings not on that root path. "Backreferences"
means adding additional metadata to allow the discovery of child events from a given parent event. These backreferences are necessary over
federation where each server has an incomplete view of the thread. Consider:

```
Letters = Servers
Numbers = Events

!room1 (A,B)    !room2 (B,C)
                     1 <- parent
                     |
   +-----------------+
   |                 |
   2                 3 <- children
```
- When event 2 is created, only servers A,B will know this.
- A backreference event needs to be created in !room2 in order for C to ever be aware of event 2.
- When C is aware of event 2, it can then peek/join into !room1 to receive updates to that fork.
- This means that **in order to create a relationship, the user must be in parent event's room**.

The backreference event MUST be sent by the server on behalf of the client and look like:
```
{
    "type": "m.room.backref",
    "content": {
        "event_id": "$parent_event_id",
        "m.relationship": {
            "rel_type": "m.child",
            "event_id": "$child_event_id",
        }
    },
    "sender": "@user_making_relation:localhost",
    "room_id": "!parent_event:room",
    "unsigned": {
      "relationship_room_id":"!someroomid:anotherhost",
      "relationship_servers": [ "localhost", "anotherhost" ]
    }
}
```

Justification:
 - Backreference events have to exist so servers can be aware of new child threads in different rooms. Without it,
   servers will only be able to walk from their event up to the root and not explore the entire thread. Furthermore,
   servers will not converge on a consistent view of the thread as some servers have information that others are missing.
 - We re-use the `m.relationship` shape because the event is a literal relationship.
 - The type `m.room.backref` is used so clients can filter these out if they don't know or want to render them on the UI.
 - We re-use the `unsigned.relationship_*` fields as routing information is critical in order to follow backreferences.

Edge cases:
 - It is not an error if the user does not have permission to send this event into the parent room.
 - The child event should be sent first, and only after success should the backreference event be sent. This is already
   implied because the backreference event needs to reference the event ID of the child.

Security considerations:
 - We omit the `content` of the child event and only share event metadata with the parent room for privacy. This
   can be displayed on the UI as "Alice referenced this event in another room" which can be hyperlinked to the
   room in question.

Server behaviour:
 - When sending an event: if an event contains a valid `m.relationship` - where valid means that the user is joined to both child/parent rooms -
   send the event then create the backreference event and send it into the parent room on a best-effort basis. Failures
   for any reason are non-fatal. 
 - When receiving a backreference event: persist the relationship between parent/child for use in `/event_relationships`.

The net result of this is:
 - 1: A client makes an `/event_relationships` request with `auto_join: true`. The server begins walking the thread.
 - 2: The server encounters an event ID it does not have and the `unsigned` metadata indicates it is in a different room.
 - 3: The server joins the room on behalf of the client.
 - 4: The server calls the federated form of `/event_relationships` to the server joined via.
 - 5: The server continues until it find an unknown event ID again then loops back to Step 2 until the request is satisfied.
 - 6: Subsequent children made in this thread will be actively pushed to the server as normal events with the type `m.room.backref`.
      This provides additional search paths for the next `/event_relationships` request and can be actively shown in the client's UI.
