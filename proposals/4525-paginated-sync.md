# MSC4525: Paginated Sync

This is a possible path towards further simplifying simplified sliding sync (SSS), based on ideas
from Erik and others as captured in the Alternatives section of
[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186). This was deliberately 
descoped from consideration in MSC4186 given we'd already proven tuned implementations of SSS and 
we wanted to prioritise shipping the demonstrated benefits in the spec, rather than further 
delaying the new sync API by moving the goalposts yet again.

However, MSC4186 has now passed FCP, and should land in Matrix 2.0 (at last). So, we might as well
start thinking about another round of improvements.

## Problem

[MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186) (Simplified Sliding
Sync) successfully fixed initial sync: the client asks for a window of rooms ordered by activity,
and sync time became independent of account size. However, having run it in production in the
Element X clients for a while, the sliding-window model itself has turned out to be the source of
most of the remaining problems:

* Incremental responses are unbounded: Once the client has grown its range to cover the whole
  account (e.g. `[0, 2600]`), an incremental sync must return *every* room with updates since the
  `pos` token, in one response. If the client has been offline overnight, that response can be
  enormous and slow to compute, which is exactly the failure mode of `/v3/sync` that sliding sync
  set out to fix. In practice servers defend themselves by expiring the connection
  (`M_UNKNOWN_POS`) instead...

* ...and connection expiry is very disruptive: When a connection expires (after ~30 minutes 
  offline, or when too many updates have stacked up), the client starts from scratch: it re-sends 
  the full request, re-downloads account data, push rules, read receipts, marks all E2EE as dirty
  (obligating /key/query on all known devices), and re-grows its ranges 
  over the entire room list, re-fetching a page of rooms it almost entirely already has.
  Moreover, the UX of "timeline resets" on clients can be bad if they throw away their timeline
  view/cache; this removes the concept of timeline resets entirely, radically speeding up launches.

* `timeline_limit: 1` blows holes in the timeline: To keep list responses small when initially
  growing the all_rooms list, clients run their lists with a timeline limit of 1. This means that
  whenever more than one event has arrived in a room since the last response, the room comes down
  gappy (`limited: true`), the client throws away its cached timeline connectivity, and has to
  back-paginate to stitch the gap - even though the server had the intervening events sitting right
  there. For E2EE rooms this also degrades the ability to eagerly decrypt what arrived.

* It's too easy for the client to drive the API wrong: Ranges, multiple lists, list filters, room
  subscriptions, and `timeline_limit`/`required_state` changes between requests (whose deltas the
  server computes against the per-room request config it remembered from previous requests, c.f.
  `expanded_timeline`) form a large surface area where client and server state can disagree.
  Several of the nastiest sliding sync bugs have been "the client's model of the window differs
  from the server's". Subscriptions exist purely because a room outside the ranges gets no
  updates; lists exist purely to grow coverage of the account. Both are workarounds for the
  window model.

This MSC proposes **Paginated Sync**: a dialect of MSC4186 which keeps its connection model, room
result schema, and extensions, but replaces lists, ranges, subscriptions and expanding timelines
with a single mechanism - the server pages the client through whatever has changed, most recently
active rooms first, with a bounded response size. It is the "Pagination" alternative sketched in
MSC4186, fleshed out.

## Proposal

The client `POST`s to `/sync` in a loop, exactly as in MSC4186: `conn_id`, `pos`, `timeout` and
`set_presence` behave identically, as do extensions. There are no lists, no ranges, no
subscriptions, and no `expanded_timeline`.

Instead the client sends three integers describing the maximum response it is prepared to receive,
plus a room config that applies to all rooms:

### Request body

| Name | Type | Required | Comment |
| - | - | - | - |
| `conn_id` | `string` | No | As MSC4186. |
| `pos` | `string` | No | As MSC4186. |
| `timeout` | `int` | No | As MSC4186. Ignored (treated as 0) whenever the server has rooms already pending for the client - see below. |
| `set_presence` | `string` | No | As MSC4186. |
| `page_size` | `int` | Yes | The maximum number of rooms to return in this response. Clients might use a small value (e.g. 20) on the first request of a connection so the app renders quickly, then a larger one (e.g. 100) to drain the rest. |
| `limit` | `int` | Yes | The maximum number of *new* timeline events to return per room, per response. If a room has more new events than this, the server returns the most recent `limit` of them with `limited: true` and a `prev_batch`, and the client uses `/messages` to fill the gap if it cares. |
| `history` | `int` | No | The number of most-recent timeline events to return for a room which has not previously been sent on this connection (e.g. 1). This exists to make cold starts fast: one event per room is enough to order the room list and show a preview, and the client back-fills anything more via `/messages`. Defaults to `limit`. |
| `required_state` | `RequiredStateRequest` | No | As MSC4186, but specified once, top-level, and applied to every room returned. MUST be identical on every request of a connection: the server always uses the value from the *current* request and never has to remember, diff, or re-send state because the config changed. A client that wants different state starts a new connection - which is cheap, see "No connection expiry, no errors" below. |
| `extensions` | `{string: ExtensionConfig}` | No | As MSC4186, minus the per-extension `lists`/`rooms` scoping fields - with no lists or subscriptions there is nothing for them to scope. An enabled extension applies to the rooms in the response (plus its global parts, e.g. global account data, as before). |

The three integers are *not* sticky: they apply to the request they are sent in, and the client
can vary them freely between requests. `required_state` is the opposite - fixed for the life of
the connection - and either way each request is self-describing: the only cross-request state the
server keeps is which rooms it has sent, and up to where.

### Response body

| Name | Type | Required | Comment |
| - | - | - | - |
| `pos` | `string` | Yes | As MSC4186. |
| `rooms` | `{string: RoomResult}` | No | As MSC4186, minus the `lists`, `expanded_timeline` and `num_live` fields. (`num_live` is derivable here: a previously-sent room only ever receives events newer than the client's position, so its whole timeline is live; a never-sent room (`initial: true`) is all-historical.) |
| `pending` | `int` | No | The number of further rooms with undelivered updates which did not fit into `page_size`. Absent means 0. May be approximate. While this is non-zero the client should immediately sync again to drain the backlog; the server ignores `timeout` in this state and responds immediately. |
| `total_rooms` | `int` | No | The total number of rooms in the user's account (the MSC4186 server-side list: joined, invited, knocked, plus kicked/banned). Lets the client show sync progress on a cold start. |
| `extensions` | `{string: ExtensionResult}` | No | As MSC4186. |

### Semantics

The server maintains, per connection, the position up to which each room has been sent - exactly
the bookkeeping MSC4186 servers already do to compute "has this room been sent before, and what's
new since". For each sync request:

1. Compute the set of rooms with updates the connection hasn't yet received (or, on the first
   request, all rooms in the server-side list). This is the same set MSC4186 computes; there is
   just no range/filter/subscription applied to it.

2. Order it most recently active first. Unlike MSC4186, this ordering is *advisory*: nothing
   indexes into it (there are no ranges), so its only effect is which rooms the client hears
   about first, and clients order their room lists locally (from `bump_stamp` / their own latest
   events). MSC4186's exact-ordering semantics are therefore unnecessary; the server SHOULD lead
   with recent activity and that is the whole requirement.

3. Take the first `page_size` rooms. Anything left over is reported in `pending` and delivered on
   subsequent requests.

4. For each room: if it has been sent on this connection before, return up to `limit` events newer
   than what the client has, setting `limited: true` and a `prev_batch` if events were dropped.
   If it has never been sent, return the most recent `history` events with `initial: true`, a
   `prev_batch`, and `limited: true` if the room has more history. `required_state`, `bump_stamp`,
   `name`, `heroes`, counts etc. are all as MSC4186.

Because a room the client has already received only ever comes down with events *newer* than what
the client has, and gaps are explicit per-room (`limited` + `prev_batch`), the response to any
request is bounded by roughly `page_size * limit` events regardless of how long the client has
been away. Catch-up after a week offline is the same shape as catch-up after ten seconds: a few
pages of the most recently active rooms, oldest news elided behind per-room gaps.

#### Draining and long-polling

If `pending` was non-zero, the client just syncs again; the server responds immediately (ignoring
`timeout`) until the backlog is drained. Once `pending` is 0, the connection behaves like any
sync loop: the server parks the request until something changes, then returns the changed rooms.
A client that wants to render fast on cold start uses a small `page_size` for the first request
and a bigger one for the drain; nothing else changes.

#### Fairness

Most-recent-first ordering has a starvation hazard: if more than `page_size` rooms have constant
traffic, a quiet room's single new message could sit behind the noisy rooms indefinitely, since
the noisy rooms re-earn their place at the top of the ordering on every request. Servers MUST
prevent this. The recommended approach: reserve a slice of each page (say a quarter) for the
rooms whose undelivered updates are *oldest*, filling the rest most-recent-first. This guarantees
every pending room is delivered within a bounded number of pages while keeping the top of the
page hot, and - unlike schemes that widen the page - never returns more than `page_size` rooms,
so the client's first fast page stays fast. (Servers MAY use other schemes, e.g. spreading a
`page_size * limit` event budget across more rooms with fewer events each; the requirement is
only that no room's updates are deferred indefinitely.)

#### No connection expiry

MSC4186 servers expire connections partly for resource reasons but mostly as a pressure valve:
"there is too much to send down, it's cheaper to start again". Paginated sync removes the
pressure: incremental responses are bounded, so there is no response-size reason to ever expire a
connection. Servers SHOULD keep connections alive indefinitely, subject only to genuine resource
limits. If a server does discard per-connection state, degradation is graceful: rooms it has
forgotten about simply come down as never-sent (`initial: true` with `history` events) - there is
no equivalent of re-growing ranges, and extensions re-send their data as they do on any initial
sync.

Because of this, `M_UNKNOWN_POS` is removed from the API entirely. A `pos` the server does not
recognise - expired, forged, issued to a different device, whatever - is simply treated as
absent (after authentication, and taking nothing on trust from the token): the connection starts
afresh and rooms are re-sent as never-sent. The client has **no error path to implement**: no
expiry detection, no session-restart logic, no "must not process responses after expiring"
rules. Every response is handled the same way.

#### History is `/messages`'s job

There is deliberately no way to ask sync for more history: no `timeline_limit` increases, no
`expanded_timeline`, no timeline trickling. A room arrives with at most `history` (first time) or
`limit` (subsequently) events and a `prev_batch`; anything further back - filling a gap, preloading
a screenful of scrollback for the top rooms, finding the most recent *visible* event for a room
preview when the latest events turn out to be state or redactions - is fetched via
`/rooms/{roomId}/messages`, concurrently with the sync loop, at whatever priority the client
chooses. This replaces the fiddliest part of MSC4186 (config-change detection and
`expanded_timeline` re-sends) with an API that already exists.

For this to be pleasant, `/messages` wants a mode which does not block on backfilling over
federation (matching sync-timeline behaviour); that is proposed separately. A bulk multi-room
`/messages` may also be worthwhile for preloading, as noted in MSC4186's alternatives; neither is
a hard dependency of this MSC.

#### Worked example

A client with 2,600 rooms cold-starts: `{page_size: 20, limit: 10, history: 1}`. The first
response contains the 20 most recently active rooms, one event each, `total_rooms: 2600`,
`pending: 2580` - enough to paint a useful room list immediately. The client re-requests with
`page_size: 100` and drains the rest in 26 fast pages, while concurrently `/messages`-ing the
visible rooms to deepen their previews. No ranges were grown; the server never sent an event the
client already had.

The same client returns after a weekend away. 340 rooms have new traffic. The old world: one
giant response, or (more likely) `M_UNKNOWN_POS` and a full restart. Here: four pages of
`page_size: 100`, each bounded, most active rooms first, busy rooms gapped at `limit: 10` with
`prev_batch` tokens for the client to back-fill on demand. The connection - and every room's
timeline connectivity for rooms with fewer than 10 new events - survives intact.

A room gets 500 messages while the app is foregrounded: each sync response delivers at most
`limit` of them; if the client falls behind the room comes down `limited` with a `prev_batch`,
i.e. the gap is explicit and local to that room, rather than being escalated into a connection
reset that takes the other 2,599 rooms' state with it.

## Potential issues

* A client which never drains its backlog (e.g. syncs once then sleeps) accumulates pending rooms
  server-side; but the tracking cost is the same per-room bookkeeping MSC4186 already pays, and
  `pending` gives the server an obvious signal for genuinely dead connections.
* Room list *ordering* on the client is by `bump_stamp`, computed from at most `history` events on
  cold start; if a room's most recent events are all non-"proper" activity (reactions, state), the
  client may need `/messages` to find a preview-worthy event. This is already true of MSC4186 with
  `timeline_limit: 1` - and unlike MSC4186, the client can actually fix it, cheaply, per-room.
* Losing subscriptions means a client cannot ask for elevated `required_state`/timeline for one
  specific room. In practice Element X used subscriptions primarily to hear about visible rooms at
  all (because they were outside the ranges) - which this design makes automatic, as every room
  with traffic is delivered. Clients wanting deep state for an opened room fetch it with existing
  per-room APIs (`/state`, `/members`, `/messages`).

## Alternatives

We could stay with MSC4186 and work around each problem individually: cap incremental response sizes
by splitting them (this proposal, but bolted onto the range machinery); keep sessions alive by
storing more server-side; raise `timeline_limit` and accept bigger list responses. Each patch adds
surface area to what is already the most subtle part of the API, whereas most-recent-first paging
makes the problems structurally impossible and *removes* surface area.  Instead, the simplicity of
this MSC is the point: an implementation of this MSC is an MSC4186 implementation minus lists,
ranges, filters, subscriptions, per-room config-change detection (the server remembering and
diffing each room's previously-requested `timeline_limit`/`required_state` to implement
`expanded_timeline` and required-state expansion), extension scoping, `num_live`, connection expiry
and the client-side error path, plus a sort, a truncate, and a counter. The per-connection state a
server keeps reduces to a single map: room ID to the position it has been sent up to.

On the other hand, something which SSS removed which feels increasingly painful is the ability to
delta compress responses or requests - for instance, we have no way of sending an incremental
update to account_data, or avoid re-sending filter configuration.  One option could be to carefully
reintroduce that in this MSC.

## Security considerations

As MSC4186. Bounded response sizes if anything help here: a malicious or broken client can no
longer construct requests (huge ranges, many lists) whose responses are expensive for the server
to assemble; the per-request work is capped by `page_size * limit` however the account is shaped.
Servers should still cap the number of connections per device and rate-limit as usual.

MSC4186 requires rejecting a `pos` issued to another user with `M_UNKNOWN_POS`, to stop a stolen
token granting capabilities. This proposal's treat-as-absent rule satisfies the same goal more
simply: possession of a `pos` grants nothing, because the server takes nothing on trust from it -
an unrecognised token yields a fresh connection scoped to the *authenticated* user, same as
sending no token at all.

## Unstable prefix

While this MSC is unstable, the endpoint is `POST
/_matrix/client/unstable/org.matrix.msc4525/sync`, advertised via the `org.matrix.msc4525` flag in
`/_matrix/client/versions`.

## Dependencies

Builds on MSC4186 (connections, room results, activity ordering, extensions), which has passed FCP.
