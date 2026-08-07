# MSC4000: Forwards fill (`/backfill` forwards)

Currently, `/messages` only backfills events when you paginate backwards with `?dir=b`.
The limiting factor here is `/backfill` which only looks backwards to find preceding
events.

The spec just says this:

> Since users in that room are able to request the history by the `/messages` client API
> endpoint, it’s possible that they might step backwards far enough into history before
> the homeserver itself was a member of that room.
> 
> To cover this case, the federation API provides a server-to-server analog of the
> `/messages` client API, allowing one homeserver to fetch history from another. This is
> the `/backfill` API.
> 
> *-- https://spec.matrix.org/v1.5/server-server-api/#backfilling-and-retrieving-missing-events*

This proposal is after adding a way to `/backfill` forwards, also known as *forwards fill*.

This also opens the door to adding backfill support to `/context` which returns events
around a given event in both directions. Please note, that this MSC doesn't dictate when
a server should `/backfill` or not. We can address this in a future MSC with spec or
guidelines which is tracked by https://github.com/matrix-org/matrix-spec/issues/1281

Navigating the DAG forwards is harder because by the nature of `prev_events`, which
connect the DAG together, gives us no indication of what comes next. We could give a
list of events that we have as forward extremeties and ask other homeservers for any
successor events (events that reference the given events in their `prev_events`).

## Proposal

Add a new server API endpoint `GET /_matrix/federation/v1/forwards_fill/{roomId}` which
is basically a mirror image of `/backfill`.

Retrieves a sliding-window history of subsequent PDUs that occurred in the given room.
Starting from the PDU ID(s) given in the `from_event_id` query parameter, the PDUs that
succeed them are retrieved, up to the total number given by the `limit`.

|   |   |
--- | ---
Rate-limited | No
Requires authentication | Yes

#### Request

##### Request parameters

Name| Type | Description
--- | --- | ---
`roomId` | `string` | **Required:** The room ID to backfill.

##### Query parameters

Name| Type | Description
--- | --- | ---
`limit` | `integer` | **Required:** The maximum number of PDUs to retrieve, including the given events.
`from_event_id` | `[string]` | **Required:** The event IDs to find successors from. TODO: Should we spec a hard limit to the number of events you can specify?


#### Responses

Status | Description
--- | ---
`200` | A transaction containing the PDUs that succeeded the given event(s), up to the given limit.

##### 200 response transaction

Name| Type | Description
--- | --- | ---
`origin` | `string` | **Required:** The server_name of the homeserver sending this transaction.
`origin_server_ts` | `integer` | **Required:** POSIX timestamp in milliseconds on originating homeserver when this transaction started.
`pdus` | `[PDU]` | **Required:** List of persistent updates to rooms. Note that events have a different format depending on the room version - check the room version specification for precise event formats.


## Potential issues

Forwards fill has the same normal problems that `/backfill` has where the server will
probably only exhaust a single chain of events up to the `limit` from the many given
events to navigate from. This makes it harder to fill in all the gaps in one pass. But
servers can keep hitting the endpoint with the new extremities until they've filled in
everything. Is there a smarter heuristic guideline that servers should follow? Or
something we should spec for how much depth/breadth a server should return given a list
of many events to navigate from?

For example with Synapse, when it does a `/messages?dir=b` and there are backward
extremities, it just does a single `/backfill` with the closest 5 extremities and just
moves on with the `/messages` response regardless of how much timeline is missing.
Perhaps this is better solved by allowing the server to indicate where the gaps are so
the client can choose if it's important to them to fill them in, see
*[MSC3871](https://github.com/matrix-org/matrix-spec-proposals/pull/3871): Gappy
timelines*.


## Alternatives

We could add a direction query parameter to `/backfill` but the semantics for are
slightly different as backfill normally includes the events you requested with `v` as
well preceding events versus with going forward, we just want to find the successors.


## Security considerations

We're only exposing messages according to the existing message history setting in the
room (`m.room.history_visibility`). No extra data is exposed, just a new way to navigate
and fetch it all.


## Auxiliary references

Other links:

 - https://github.com/matrix-org/matrix-spec-proposals/pull/3030#discussion_r802851952
 - https://github.com/matrix-org/matrix-spec/issues/601#issuecomment-1082198910
 - https://github.com/matrix-org/matrix-public-archive/issues/72


## Unstable prefix

While this feature is in development, the endpoint can be used with the unstable prefix
at `GET /_matrix/federation/org.matrix.msc4000/forwards_fill/{roomId}` instead of it's
stable `/v1` location as described above.

### While the MSC is unstable

During this period, servers should optimistically try the unstable endpoint and look for
the `404` `M_UNRECOGNIZED` error code to determine support (see [MSC3743: *Standardized
error response for unknown
endpoints*](https://github.com/matrix-org/matrix-spec-proposals/pull/3743)).

### Once the MSC is merged but not in a spec version

Once this MSC is merged, but is not yet part of the spec, servers should optimistically
use the stable endpoint and fallback to the unstable endpoint to have maximum
compatibility if desired.

### Once the MSC is in a spec version

Once this MSC becomes a part of a spec version, servers should optimistically use the
stable endpoint. If a given server doesn't support the endpoint, another server in the
room can be tried until all are exhausted.

Servers can keep falling back to the unstable endpoint and are encouraged (not
obligated) to serve the unstable fallback endpoint for a reasonable amount of time to
help smooth over the transition for other servers. "Reasonable" is intentionally left as
an implementation detail, however the MSC process currently recommends *at most* 2
months from the date of spec release.



