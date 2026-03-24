# MSC4438: Message bookmarks via account data

There is currently no interoperable way for Matrix clients to let users bookmark specific room
events for later retrieval across devices. Individual clients can implement local bookmarks, but
those do not sync between devices or across client implementations. Existing mechanisms such as
room pins
([`m.room.pinned_events`](https://spec.matrix.org/v1.17/client-server-api/#mroompinned_events))
and room tags solve different problems: pins are shared room state visible to all members, while
tags classify rooms rather than individual events.

[MSC2771](https://github.com/matrix-org/matrix-spec-proposals/pull/2771) previously proposed a
bookmarks feature but was abandoned before reaching maturity. It stored bookmarks in room account
data as a flat array, which limited it to per-room views and raised scalability concerns for users
with many bookmarks.

This proposal defines a client-side convention for bookmarking room events using existing global
account data APIs. A bookmarked event is represented by one account data event containing the
bookmark's metadata, plus an index account data event which carries bookmark ordering information
for the user.
This proposal does not add new homeserver endpoints or federation behavior. Homeservers continue
to store and return the account data through the existing Client-Server API.

This MSC is intentionally narrow. It standardizes bookmarks for room events and messages, not
arbitrary Matrix entities. A qualifying proof-of-concept implementation exists in
[smokku/cinny][smokku/cinny] in commit `6363e441482f1d5435fc0c9b422ec5206d54195a`,
which stores bookmarks in global account data and exposes add, remove, and list
functionality in the client UI.

## Proposal

This proposal introduces a pair of account data event type conventions:

* A single global index event which lists bookmark IDs in a suggested display order.
* One global account data event per bookmark ID which stores the bookmarked event's metadata.

Clients use the existing global account data endpoints:

* [`PUT /_matrix/client/v3/user/{userId}/account_data/{type}`][PUT account data]
* [`GET /_matrix/client/v3/user/{userId}/account_data/{type}`][GET account data]

As with other account data, these events are delivered in the top-level `account_data` section of
[`/sync`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3sync).

### Event types

* `m.bookmarks.index` for the bookmark index event.
* `m.bookmark.<bookmark_id>` for individual bookmark item events.

The account data is global account data, not room account data.

### Bookmark index event

The bookmark index event maintains the bookmark ID sequence for all active bookmarks along with
versioning metadata.

**Event type:** `m.bookmarks.index`

**Content:**

| Field          | Type       | Required | Description                                                        |
|----------------|------------|----------|--------------------------------------------------------------------|
| `version`      | integer    | Yes      | Schema version. Must be `1`.                                       |
| `revision`     | integer    | Yes      | Monotonically increasing counter, incremented on each mutation.    |
| `updated_ts`   | integer    | Yes      | Unix timestamp in milliseconds of the last modification.           |
| `bookmark_ids` | [string]   | Yes      | Bookmark ID sequence; also used as an ordering hint for display.   |

Example:

```json
{
    "version": 1,
    "revision": 12,
    "updated_ts": 1741451160000,
    "bookmark_ids": [
        "bmk_1a2b3c4d",
        "bmk_5e6f7788"
    ]
}
```

The `revision` field allows clients to detect concurrent modifications from other devices. When a
client receives an updated index via `/sync` with a `revision` higher than the locally known
value, it should refresh its bookmark list from the server.

The `bookmark_ids` array provides the default ordering hint for bookmark presentation. Clients
should prepend new bookmark IDs to the beginning of the array so that the stored order reflects
most-recent-first creation. Clients may still sort, group, or partition bookmarks differently in
their own UI.

Clients must treat missing or malformed index content as an empty bookmark set.

### Bookmark item event

Each bookmarked event is represented by a separate global account data event. The event type is
formed by concatenating the prefix `m.bookmark.` with the bookmark ID.

**Event type:** `m.bookmark.<bookmark_id>`

**Content:**

| Field           | Type    | Required | Description                                                              |
|-----------------|---------|----------|--------------------------------------------------------------------------|
| `version`       | integer | Yes      | Schema version. Must be `1`.                                             |
| `bookmark_id`   | string  | Yes      | The client-generated bookmark ID (see [Bookmark ID](#bookmark-id)).      |
| `uri`           | string  | Yes      | [Matrix URI][Matrix URI scheme] pointing to the event.                   |
| `room_id`       | string  | Yes      | The room ID containing the bookmarked event.                             |
| `event_id`      | string  | Yes      | The event ID of the bookmarked message.                                  |
| `event_ts`      | integer | Yes      | The `origin_server_ts` of the bookmarked event, in milliseconds.         |
| `bookmarked_ts` | integer | Yes      | Unix timestamp in milliseconds when the bookmark was created.            |
| `sender`        | string  | No       | The sender MXID of the bookmarked event, if known at bookmark time.      |
| `room_name`     | string  | No       | A room name snapshot, if known at bookmark time.                         |
| `body_preview`  | string  | No       | A short preview of the event body (see [Body preview](#body-preview)).   |
| `msgtype`       | string  | No       | The event content's `msgtype`, if applicable.                            |
| `deleted`       | boolean | No       | When `true`, the bookmark has been tombstoned. Defaults to `false`.      |

Example:

```json
{
    "version": 1,
    "bookmark_id": "bmk_a1b2c3d4",
    "uri": "matrix:roomid/%21abc%3Aexample.com/e/%24evt123%3Aexample.com",
    "room_id": "!abc:example.com",
    "event_id": "$evt123:example.com",
    "event_ts": 1741440000000,
    "bookmarked_ts": 1741443960000,
    "sender": "@alice:example.com",
    "room_name": "General Chat",
    "body_preview": "Here is the link to the deployment guide you asked about. Let me know if...",
    "msgtype": "m.text"
}
```

Clients must ignore malformed bookmark item events. Clients must also ignore bookmark item events
where `deleted` is `true`.

The optional metadata fields (`sender`, `room_name`, `body_preview`, `msgtype`) are cached at
bookmark creation time. They allow clients to display a meaningful bookmark list without needing to
fetch each original event. These cached values may become stale over time (e.g. if a room is
renamed or a message is edited) - they are a convenience snapshot, not an authoritative copy.
Clients may refresh them at their discretion but are not required to.

The presence of `room_id`, `event_id`, and `uri` duplicates some information by design. This lets
clients use the explicit room and event identifiers directly for display, grouping, partitioning,
or lookup purposes without having to parse URI components out of `uri`.

### Matrix URI

The `uri` field must use the [`matrix:` URI scheme][Matrix URI scheme] to reference
the bookmarked event using a room ID and event ID.

The canonical form used by this MSC is:

```text
matrix:roomid/<room_id>/e/<event_id>
```

When serialized, the room ID and event ID components are percent-encoded as required by the URI
rules. For example, an event `$event:example.org` in room `!somewhere:example.org` becomes:

```text
matrix:roomid/%21somewhere%3Aexample.org/e/%24event%3Aexample.org
```

Clients may include query parameters such as `via` when needed for navigation, but this MSC does
not require them.

### Bookmark ID

The `bookmark_id` identifies a bookmark item and forms the suffix of the corresponding account
data event type. This MSC does not require any particular bookmark ID generation method.

Instead:

* `bookmark_id` must be valid for use as the suffix of the bookmark item account data event type,
  so that it can be concatenated with the event type prefix to form a valid account data type key.
* When creating a bookmark, if a client already knows an existing bookmark item for the same
  `(room_id, event_id)`, it should reuse that item's `bookmark_id` instead of generating a new
  one.
* Clients should make reasonable effort to deduplicate bookmarks for the same `(room_id, event_id)`.
* Clients should make reasonable effort to avoid clashing with bookmark IDs generated by other
  clients.
* If a client intentionally uses a `bookmark_id` format already known to be used by another client,
  it should use the same algorithm for that format rather than inventing a different one with the
  same shape.
* Clients may use their own algorithm and format for `bookmark_id`.

The qualifying implementation currently uses the following simple reference algorithm (djb2-like) to
generate bookmark IDs and deduplicate bookmarks by `(room_id, event_id)`:

```text
<room_id>|<event_id>
```

1. Start with `hash = 0`.
2. For each UTF-16 code unit `ch` in the input string, update the hash as
   `hash = ((hash << 5) - hash + ch) | 0`.
3. Convert the resulting 32-bit signed integer to an unsigned 32-bit integer.
4. Encode it as lowercase hexadecimal, padded to 8 characters with leading zeroes.
5. Prefix the hexadecimal value with `bmk_`.

Reference implementation:

```text
function computeBookmarkId(roomId, eventId):
    input = roomId + "|" + eventId
    hash = 0
    for each character ch in input:
        hash = ((hash << 5) - hash + charCode(ch)) | 0  // signed 32-bit
    hex = toUnsigned32(hash).toHex().padStart(8, '0')
    return "bmk_" + hex
```

For example, if the resulting hexadecimal value is `1a2b3c4d`, the bookmark ID is
`bmk_1a2b3c4d`.

### Body preview

`body_preview` is optional. Clients may omit it entirely, derive it from the event body, or use any
other reasonable preview strategy that helps users identify the bookmarked event.

The qualifying implementation derives `body_preview` from `content.body` and truncates it to 120
characters with an ellipsis (`U+2026`) when needed, but this behavior is not required by the MSC.

### Adding a bookmark

To add a bookmark for a room event, a client:

1. Determines whether it already knows a bookmark item for the same `(room_id, event_id)`. If so,
   it should reuse that `bookmark_id`.
2. Otherwise, generates a new `bookmark_id` using its chosen method.
3. Constructs the bookmark item content from the target event and its room.
4. Writes the bookmark item to account data with type `m.bookmark.<bookmark_id>`.
5. Reads the current bookmark index event from the server, or treats it as empty if it is missing
   or invalid.
6. If the bookmark ID is not already present in `bookmark_ids`, prepends it.
7. Increments `revision` by `1` and sets `updated_ts` to the current timestamp in milliseconds.
8. Writes the updated bookmark index event.

Writing the item before updating the index ensures that when other devices receive the updated
index via `/sync`, the referenced item is already available.

If the chosen bookmark ID already exists, clients must not add a duplicate ID to `bookmark_ids`.
Clients should also avoid creating a second bookmark for the same `(room_id, event_id)` when they
already know an existing bookmark item for that event.

### Removing a bookmark

To remove a bookmark, a client:

1. Reads the current bookmark index event from the server, or treats it as empty if it is missing
   or invalid.
2. Removes the bookmark ID from `bookmark_ids` if present.
3. Increments `revision` by `1` and sets `updated_ts` to the current timestamp in milliseconds.
4. Writes the updated bookmark index event.
5. Reads the bookmark item event for the bookmark ID.
6. If the bookmark item exists and is valid, rewrites it with `deleted` set to `true`.

Soft-deletion is used because account data events cannot be deleted from the server. Setting
`deleted: true` signals to all clients that this bookmark should be ignored. Clients should
tombstone the bookmark item event rather than abandoning the old item content, so that other
clients which encounter the item event can determine that the bookmark has been explicitly removed.

### Listing bookmarks

To list bookmarks, a client:

1. Reads the bookmark index event.
2. Iterates `bookmark_ids` in order.
3. Reads the corresponding bookmark item event for each ID.
4. Returns only bookmark items whose content is valid and not tombstoned.

If `bookmark_ids` contains duplicates, clients should ignore later duplicates and only surface the
first occurrence. If the index references missing, malformed, or tombstoned bookmark item events,
clients must skip those entries.

The ordering of `bookmark_ids` should be treated as the default display ordering hint. Clients may
sort, group, or partition bookmarks differently when presenting bookmarks to the user.

Clients may cache the bookmark list locally and refresh it when the index event changes.

### Checking if a message is bookmarked

To check whether a specific message is bookmarked:

1. Consult the locally cached bookmark items, if available.
2. Compare the target `(room_id, event_id)` against the bookmark items' `room_id` and `event_id`
   fields.

Clients should use locally cached bookmark items or locally maintained reverse lookups for this
check instead of issuing unnecessary server requests.
Clients should not rely on bookmark IDs being derived from `(room_id, event_id)` in a predictable way,
because different clients may use different algorithms.

### Cross-device synchronization

Clients should listen for changes to the `m.bookmarks.index` account data event via `/sync`. When
the index event is received with a `revision` different from the locally known value, the client
should refresh its bookmark list by re-fetching all items from the server.

The `revision` counter provides a lightweight mechanism for clients to detect when the bookmark
list has been modified by another device. Clients are not expected to implement conflict
resolution - the last write wins, as is standard for account data.

### Client behavior

Clients may expose bookmark actions in message menus, show bookmark list views, and support local
filtering or search over bookmark metadata, but those UI details are not part of the normative
protocol behavior defined by this MSC.

Clients should validate content before use. Missing or malformed fields must not cause a bookmark
to be surfaced as valid. Clients which do not understand this MSC will simply ignore these account
data event types.

### Implementation note

The qualifying proof-of-concept in [smokku/cinny][smokku/cinny] currently uses the implementation-specific
event types `pl.chrome.bookmarks.index` and `pl.chrome.bookmark.<bookmark_id>`. Those names are not
proposed as spec identifiers. They are existing proof-of-concept names which should migrate to the
unstable MSC prefix while the proposal is under review.

The qualifying implementation also currently uses a djb2-based bookmark ID scheme for simplicity.
That implementation detail is not required by this MSC and will need to be updated as the MSC
moves forward.

## Potential issues

This design stores one account data event per bookmark plus a separate index event. That makes the
model straightforward to update and reason about, but it creates account-data fan-out for users
with large bookmark collections. Fetching a full bookmark list may require reading many account
data event types. Homeserver implementations may impose limits on account data size or count. This
proposal does not define an upper limit on the number of bookmarks, but clients may choose to warn
users or implement client-side limits. One mitigation strategy might be to resurrect tombstoned
bookmark item events and reuse their IDs when creating new bookmarks.

This MSC does not mandate any specific bookmark ID generation method. That gives clients
flexibility, but it also means different clients may generate different IDs for the same
`(room_id, event_id)` unless they deliberately align on the same format and algorithm or reuse
existing bookmark IDs they have already observed.

The reference implementation uses a compact 32-bit djb2-style hash with a `bmk_` prefix. Clients
that choose similarly short hash-based identifiers should consider collision risk carefully, because
two different room-event pairs could map to the same account data event type and overwrite each
other.

The optional metadata in bookmark item events, such as `room_name` and `body_preview`, is only a
snapshot. It can become stale if the room is renamed, the event is edited, or the client later
discovers richer context. When navigating to a bookmarked message, clients should fetch the actual
event from the server.

Because account data writes are last-write-wins, concurrent modifications from multiple devices
can race. The `revision` field helps clients reason about updates, but this MSC does not define a
conflict-resolution protocol beyond normal account data semantics.

A bookmark may point to an event which later becomes inaccessible, redacted, or otherwise
unavailable to the user. In that case, the bookmark metadata can still exist even though
navigation to the underlying event fails.

Since bookmarks are stored as plain account data, the server does not validate bookmark content or
enforce consistency between the index and items. A malformed client could write invalid data.
Clients must validate bookmark data when reading it and gracefully handle missing or invalid
entries.

## Alternatives

### Room account data (MSC2771 approach)

[MSC2771](https://github.com/matrix-org/matrix-spec-proposals/pull/2771) proposed storing
bookmarks in room account data with type `m.bookmarks`, containing an array of
`{event_id, title, comment}` objects.

This approach has drawbacks:

* **No cross-room view**: Listing all bookmarks requires iterating over every joined room's
  account data.
* **Scalability**: All bookmarks for a room are stored in a single event, which grows unboundedly.
* **Fragmented UX**: Users cannot easily see all their bookmarks in one place.

Global account data with split storage addresses all of these issues.

### Single-event storage

All bookmarks could be stored in a single account data event (e.g. an array within
`m.bookmarks`). That reduces the number of account data event types, but it makes each update
rewrite the whole collection and is less convenient for incremental updates or future extension.

### Client-local bookmarks

Bookmarks could be kept entirely local to a client. That avoids any protocol work, but it fails
the main goal of interoperable, synced bookmarks across devices and clients.

### Reuse of existing Matrix concepts

Room pins are shared state visible to other room members and therefore are not suitable for
private personal bookmarks. Room tags classify rooms rather than individual events and cannot
directly represent a bookmark to a message.

### Dedicated server-side API

A server-side bookmarks API (e.g. `/_matrix/client/v1/bookmarks`) could provide better
performance, pagination, and server-side search. However, this would require changes to homeserver
implementations and the Client-Server API specification. The account data approach works with all
existing homeservers without any server-side changes, making it immediately deployable.

### Mandatory shared bookmark ID algorithm

This MSC could mandate one global bookmark ID algorithm for every client. That would improve
automatic cross-client deduplication, but it would also hard-code one algorithm and one output
format into the proposal. This MSC instead allows clients to choose their own bookmark ID schemes
while requiring reasonable effort to deduplicate bookmarks for the same `(room_id, event_id)` and
to reuse already-known IDs for that tuple.

## Security considerations

Bookmark item events may duplicate selected event metadata into account data, including sender
IDs, room names, and body previews. Bookmark data is stored as unencrypted account data. Even in
encrypted rooms, the bookmark's cached metadata (`room_name`, `sender`, `body_preview`) is
visible to the homeserver administrator. Clients should consider the privacy implications of
retaining this metadata, especially on shared devices or in exported client data. Clients may
choose to omit the optional cached fields for bookmarks created from encrypted rooms, storing only
the required fields (`room_id`, `event_id`, `uri`). This trades display convenience for improved
privacy.

Account data is transmitted over TLS but is not end-to-end encrypted. The homeserver can read all
bookmark data. This is consistent with other account data features in Matrix (e.g. `m.direct`,
`m.push_rules`). A future MSC for encrypted account data would benefit bookmarks along with all
other account data.

Clients must treat bookmark item content as untrusted input, even when it originates from the same
user account. Malformed or maliciously crafted bookmark content must be validated before use and
must not cause unsafe rendering or navigation behavior.

Bookmark ID collisions can be security-relevant if an attacker can cause two different event
references to map to the same bookmark ID and thereby overwrite or mask bookmark data. This risk
depends on the chosen bookmark ID algorithm. Implementations using short hash-based identifiers,
including the reference djb2-style scheme, should consider that trade-off carefully. Reusing
another client's bookmark ID format with a different algorithm can also create avoidable
inter-client clashes.

Bookmarks can preserve previews of event content even after the original room event becomes harder
to access. Clients may wish to minimize how much message content they copy into `body_preview`,
and should not treat the bookmark item as an authoritative event record.

## Unstable prefix

Before this MSC is accepted, implementations should use the unstable event type names:

| Stable identifier                | Unstable identifier                                  |
|----------------------------------|------------------------------------------------------|
| `m.bookmarks.index`              | `org.matrix.msc4438.bookmarks.index`                 |
| `m.bookmark.<bookmark_id>`       | `org.matrix.msc4438.bookmark.<bookmark_id>`          |

This MSC does not define any new HTTP endpoints, so it does not need `/unstable` endpoint paths.
This MSC also does not require an `unstable_features` flag in `/_matrix/client/versions`, because
the behavior relies only on existing account data APIs and private client-side conventions.

After acceptance, implementations may migrate to the stable identifiers listed above.

## Dependencies

This MSC has no dependencies on other MSCs.

It relies on the existing Matrix Client-Server account data APIs and the existing Matrix URI
scheme:

* [PUT account data][PUT account data]
* [GET account data][GET account data]
* [Matrix URI scheme][Matrix URI scheme]

[PUT account data]: https://spec.matrix.org/v1.17/client-server-api/#put_matrixclientv3useruseridaccount_datatype
[GET account data]: https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3useruseridaccount_datatype
[Matrix URI scheme]: https://spec.matrix.org/v1.17/appendices/#matrix-uri-scheme
[smokku/cinny]: https://github.com/smokku/cinny/commit/6363e441482f1d5435fc0c9b422ec5206d54195a
