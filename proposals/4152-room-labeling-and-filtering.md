# MSC4152: Room labeling and filtering

As noted by [MSC3060](https://github.com/matrix-org/matrix-spec-proposals/pull/3060), rooms currently
support being described by a name, avatar, and topic. These options have been used extensively by
rooms to become discoverable, and in some cases be more prominent than other rooms the user may actually
be looking for.

This proposal introduces a concept of "labeling" a room to describe its content, similar to the keyword
list many rooms currently put into the topic. This labeling system works similar to aliases to allow
local server admins to append their own labels without affecting the "published" labels in the room
itself.

Clients can then use account data to persist in a cross-client and interoperable way the labels a user
is interested in seeing. This information could be used by the server to filter room directory results,
or used by other clients to manually filter their room lists as needed.

[MSC3060](https://github.com/matrix-org/matrix-spec-proposals/pull/3060) is a highly related MSC in
this space, and discussed in the alternatives section of this proposal.

## Proposal

### In-room labeling

A new *optional* room state event is introduced: `m.room.labels`. It has a zero-length string for a
state key. Its `content` looks as follows:

```json
{
  "labels": [
    "m.nsfw",
    "org.example.another_label"
  ]
}
```

The `m.room.labels` event is used to share labels on a room between servers, and is set by the room's
participants (typically moderators and admins only). Each entry under `labels` is bound by the
[Common Namespaced Identifier Grammar](https://spec.matrix.org/v1.10/appendices/#common-namespaced-identifier-grammar).

It is anticipated that Matrix will build up a list of "official" labels for clients to use and translate
into their users' language. How this list is constructed is out of scope for this MSC, though could
be done as a subcommittee of the SCT or through individual MSCs.

### Local server labeling

Similar to [aliases](https://spec.matrix.org/v1.10/client-server-api/#room-aliases), rooms can have
a published set of labels (`m.room.labels` above) and a set which is only available to the local server.
Unlike aliases though, it is anticipated that server-specified labels will only be set by the server
admins/operators rather than its users. A future MSC may explore user-contributed/curated tags.

A new endpoint requiring authentication and rate limiting is made available:

```
GET /_matrix/client/v1/rooms/:roomId/labels
<no request body>
```

The response format is always 200 OK, though the `labels` array may be empty:

```json
{
  "labels": [
    "m.nsfw",
    "org.example.yet_another_different_label"
  ]
}
```

If the requesting user passes the [history visibility](https://spec.matrix.org/v1.10/client-server-api/#room-history-visibility)
checks for the room's `m.room.labels` state event, the labels from that state event are included in
the list. If the room does not have an `m.room.labels` state event, the event does not specify
`content.labels`, `content.labels` is empty, or the user fails the history visibility check then the
room's labels are *not* appended to the response.

It is left as a deliberate implementation detail to determine when to expose the server's local labels
to the caller, if ever. For example, servers may only expose labels for rooms which are in the room
directory, are public, or where the user participates. If the server is withholding labels or has none
to provide, those labels are not included in the response.

If the room is not known to the server, `labels` may need to be retrieved from the
[public room directory over federation](https://spec.matrix.org/v1.10/server-server-api/#public-room-directory)
instead. See later sections for details on this mechanic. If the room still cannot be found, an empty
array is returned by the endpoint.

Between these three conditions, the `labels` array may be empty, but must always be provided.

Informing a room that the server has applied server-local labels to their room is left as an implementation
detail. A future MSC may provide a formal mechanism to inform users/rooms of action being taken, and
options for them to appeal that decision.

### Label information through room directory

In addition to the `/labels` endpoint above, clients are able to discover labels through the
[`/publicRooms`](https://spec.matrix.org/v1.10/client-server-api/#get_matrixclientv3publicrooms)
endpoint. A new property is added to each room entry: `labels`. Its behaviour is exactly as described
by the `/labels` endpoint above.

The `labels` property is also added to each room entry on the [federation `/publicRooms`](https://spec.matrix.org/v1.10/server-server-api/#get_matrixfederationv1publicrooms)
endpoint, still using the same behaviour as `/labels` above. This is done intentionally as the federation
`/publicRooms` endpoint is typically called on behalf of a local (remote to the called server) user
trying to search that directory specifically. Allowing the server's local labels to bias the results
gives the same experience that a local user would under that server's filtering mechanisms.

### Filtering room directory by (not) labels

For both the Client-Server API and Federation API `/publicRooms` endpoints mentioned above, callers
can specify `label` and `not_label` query parameters. To specify multiple labels, multiple query parameters
are used. For example: `/publicRooms?label=m.nsfw&label=org.example.another_label`.

Servers include or exclude rooms in the results which match the respective labels.

**Implementation note**: Servers may not support the filtering option. Clients in particular should
manually filter the results using the user's preferences for content, described below.

### Expressing (dis)interest in labels

Users typically have multiple clients and want settings to be shared across all of them. Clients can
use a new `m.label_interest` account data event to express their interest or disinterest in certain
labels. This event is managed by the normal [`GET /account_data/:type`](https://spec.matrix.org/v1.10/client-server-api/#get_matrixclientv3useruseridaccount_datatype)
and [`PUT /account_data/:type`](https://spec.matrix.org/v1.10/client-server-api/#put_matrixclientv3useruseridaccount_datatype)
APIs.

The `content` (or request/response body for the account data endpoints) for `m.label_interest` is:

```json
{
  "labels": [
    "m.nsfw"
  ],
  "not_labels": [
    "org.example.different_label"
  ]
}
```

Clients can then use this information to filter results in the room directory, locally on the user's
room list, etc. The `m.label_interest` event is intended to be treated as a series of `OR` conditions
joined by an `AND` for `labels` and `not_labels`. In SQL, this would be:

```sql
SELECT * FROM rooms AS r JOIN labels AS b ON r.room_id = b.room_id
WHERE b.label = ANY ("m.nsfw") AND b.label != ANY ("org.example.different_label");
```

<!-- TODO: Verify SQL syntax above -->

Clients are encouraged to provide both arrays to the `/publicRooms` filter verbatim.

### `m.nsfw` official label

The first official label introduced is `m.nsfw`. When set on a room, the room is indicated to contain
"Not Safe For Work" content. The definition of this is deliberately vague to allow communities and
servers to shape their own guidelines.

By default, rooms with the `m.nsfw` label should be treated as `not_labels` in filters. The default
user experience is therefore that `m.nsfw` rooms are not shown to users unless they opt in.

## Potential issues

**TODO**

## Alternatives

**TODO**

**TODO: Specifically reference MSC3060**

## Security considerations

**TODO**

## Unstable prefix

While this proposal is not considered stable, clients should use the following mapped identifiers:

* `org.matrix.msc4152.labels` in place of `m.room.labels`
* `org.matrix.msc4152.labels` and `org.matrix.msc4152.not_labels` in place of the `/publicRooms`
  `?labels` and `?not_labels` query parameters.
* `org.matrix.msc4152.labels` in place of `labels` on room results in `/publicRooms`.
* `org.matrix.msc4152.label_interest` in place of `m.label_interest`.
* `org.matrix.msc4152.nsfw` in place of the `m.nsfw` label.

All other identifiers are as described in the MSC due to being namespaced at a higher level. For
example, the `m.label_interest` account data event does *not* prefix the `labels` and `not_labels`
fields.

## Dependencies

This MSC has no direct dependencies.
