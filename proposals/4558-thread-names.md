# MSC4558: Thread names

[Threads](https://spec.matrix.org/v1.16/client-server-api/#threading) give a room a way to split a
conversation off the main timeline, but a thread has no identity beyond its root event. Clients
label a thread with a preview of the root's body, which works for "reply to this message" threads
but poorly for longer-lived ones: a thread that started with "hey, quick question" and turned into
the release planning discussion is still listed as "hey, quick question".

Other chat platforms let a thread carry a short title, set by whoever started it or by a moderator,
shown in the thread list and the thread's header. This proposal adds that to Matrix with a single
new event type and relation type. In encrypted rooms the name is encrypted but the relation is not,
so the server can enforce who may name a thread and bundle the latest naming event with the root.

## Proposal

### The naming event

A thread is named by sending a room (non-state) event of type `m.thread.name` that relates to the
thread's root with a new relation type, also `m.thread.name`:

```json5
{
  "type": "m.thread.name",
  "content": {
    "name": "Release planning",
    "m.relates_to": {
      "rel_type": "m.thread.name",
      "event_id": "$thread_root"
    }
  }
}
```

| Field                   | Type   | Description                                                                     |
| ----------------------- | ------ | ------------------------------------------------------------------------------- |
| `name`                  | string | **Required.** The thread's name. Empty (after normalisation) clears the name.   |
| `m.relates_to.rel_type` | string | **Required.** `m.thread.name`.                                                  |
| `m.relates_to.event_id` | string | **Required.** The event ID of the thread root.                                  |

The event relates to the **root**, not into the thread: it does not use `rel_type: m.thread`, so
it is not a reply, does not bump the thread's reply count or latest event, and does not affect
thread read receipts or unread counts. Clients SHOULD NOT render naming events in the main
timeline (like any unknown event type, they are already hidden by most clients). That includes one
they can't decrypt, which they can recognise by its relation and SHOULD NOT show as an undecryptable
message.

The event has no `body` fallback on purpose. A rename is metadata, not a message, and clients that
do not understand it should show nothing rather than a line of text.

A name SHOULD be normalised before sending and again when read by trimming leading and trailing
whitespace. Whitespace within the name is kept as sent. Clients SHOULD limit names to 100
characters and MAY truncate longer names when displaying them. A name that is empty after
normalisation, or a `name` that is missing or not a string, means the thread has no name.

### Who may name a thread

A naming event is **valid** if its sender is either:

1. the sender of the thread root (it is their thread), or
2. a user whose power level is at least the `thread_name` level (a moderator).

`thread_name` is a new top-level key in `m.room.power_levels`, alongside `redact` and `kick`. It
defaults to 50 if absent, the conventional moderator level; a room is not required to give anyone
that level.

Naming events from any other sender MUST be ignored. Validity doesn't depend on anything encrypted,
only on the sender, the unencrypted `m.relates_to`, the root's sender and the power levels, so it
can be checked without decrypting the event. Power levels are evaluated against the room state at
the naming event. Clients SHOULD trust a bundled `latest_event` (see below) without re-checking;
clients resolving the name themselves usually only have the current room state, and use that.

The `events` map of `m.room.power_levels` can't be used for this: it matches on event type, which
is hidden in encrypted rooms, and it cannot express rule 1.

#### Event authorization rules

In a room version that adopts this rule, an event with `m.relates_to.rel_type` of `m.thread.name`
is rejected unless:

- (a) `m.relates_to.event_id` names an event in the room that has been added to the naming
  event's `auth_events`, and
- (b) the sender is that event's sender, or has a power level of at least the `thread_name` level.

The thread root has to be in `auth_events` because its sender can't be found from room state. This
also means amending the rule that rejects `auth_events` entries the auth events selection algorithm
didn't pick, and putting a non-state event in the auth chain, so it needs review from server
authors. The room version's redaction algorithm also has to keep
`thread_name` in `m.room.power_levels`, as it does for `redact`.

In room versions without this rule, servers SHOULD apply the same check to their own users' events
on `/send` and return `403 M_FORBIDDEN`. Clients MUST still ignore invalid naming events either
way, since federation can deliver them (a bundled `latest_event` has already been checked).

### Resolving the current name

The current name of a thread is taken from the most recent valid naming event related to the root,
in event-graph order (not `origin_server_ts`). If that event clears the name, the thread is
unnamed; older naming events do not show through.

#### Bundled aggregation

Servers SHOULD bundle the current naming event with the root, like `m.replace`, wherever the root
is returned with other bundled aggregations:

```json5
"unsigned": {
  "m.relations": {
    "m.thread.name": {
      "latest_event": { /* the full naming event */ }
    }
  }
}
```

In encrypted rooms this is an `m.room.encrypted` event. The server applies the validity rules
above, but can't tell whether an encrypted event clears the name, so the client decides that.

#### Fetching without server support

If the root has no bundled name, a client fetches the root's relations of this type, newest first:

```
GET /_matrix/client/v1/rooms/{roomId}/relations/{rootId}/m.thread.name?dir=b&limit=20
```

and takes the first valid event (`/relations` returns topological order). The request doesn't filter
by event type, because in encrypted rooms the server only knows these events as
`m.room.encrypted`. After that, clients
keep the name current from sync: a new valid naming event for the root replaces the cached name.
Sync delivers events in the order the server received them, which can differ from graph order, so
clients SHOULD prefer an updated bundle when the server sends one.

### Redaction

The redaction algorithm strips a naming event's content, including `m.relates_to` and `name` (or
the ciphertext holding it), so a redacted naming event no longer targets any root and is ignored.
When the naming event behind the current name is redacted, the server updates the bundle (or the
client re-resolves the name), and the next-newest valid naming event (if any) takes over. A
moderator removing an abusive name therefore restores the previous one.

### Encryption

**Naming events are encrypted in encrypted rooms.** Their `m.relates_to` stays unencrypted, as for
any relation, so the server can still validate and bundle them. Only `name` and the event type are
hidden. An `m.relates_to` inside the encrypted payload is ignored, as it is for edits, so an event
can't become a naming event in a way the server can't see.

An encrypted naming event reaches the server as `m.room.encrypted`, which matches the default
`.m.rule.encrypted` (or `.m.rule.encrypted_room_one_to_one`) push rule and notifies every member.
Clients can suppress the notification once they decrypt the event, but some push paths cannot
(for example a web push service worker that must display something for every push it receives),
so every rename would become a phantom "new message" on members' devices. Poll votes and live
location have the same problem, so it shouldn't be solved by sending names in cleartext.

Instead, servers SHOULD add a default override push rule, placed after `.m.rule.suppress_edits`,
that matches the unencrypted relation, so it needs no decryption:

```json5
{
  "rule_id": ".m.rule.thread_name",
  "default": true,
  "enabled": true,
  "conditions": [
    {
      "kind": "event_property_is",
      "key": "content.m\\.relates_to.rel_type",
      "value": "m.thread.name"
    }
  ],
  "actions": []
}
```

Until a user's server has this rule, their client MAY add an equivalent rule to their own push rules
(with a rule ID that doesn't start with `.`). This only helps that user.

### Display

Clients that support this proposal SHOULD show the thread's name, where it has one, in place of or
alongside the root preview wherever the thread is identified: the thread list, the header of the
thread view, and the thread summary under the root in the main timeline. Clients SHOULD offer
naming to the users permitted by the rules above, and SHOULD hide the option from others.

## Potential issues

- **Clients that don't support it** show no name: the root preview stays the only label. This is
  the intended degradation, but it means a name chosen to disambiguate a thread is invisible to
  part of the room. In encrypted rooms they may also show a naming event they can't decrypt as an
  undecryptable message.
- **Servers without the push rule** notify members of every rename in encrypted rooms, for members
  whose client hasn't added its own rule and can't suppress the notification after decrypting.
- **Ordering follows the event graph.** Concurrent renames from different servers may disagree on
  which is most recent. This is the same trade-off as edits.
- **Spam can push valid events out of the first page.** If more than `limit` invalid naming events
  are sent after the last valid one, the first `/relations` page contains no valid event and the
  thread looks unnamed. Clients MAY paginate further. Federation can still deliver invalid events,
  but a server that bundles the name skips them.
- **Root senders who leave** keep their right to rename the thread under rule 1 if they rejoin.
  This mirrors how a user can always edit their own messages.
- **Servers that don't bundle** leave clients to fetch `/relations` once per thread they display.
- **A gappy sync can skip a rename**, leaving a cached name out of date until the client resolves it
  again.
- **Enforcement isn't federation-wide** without the new room version; the `/send` check only covers
  local senders.
- **The auth rule needs a new room version** and the thread root in `auth_events`.
- **The relation is visible to the homeserver** even in encrypted rooms, though the name isn't.

## Alternatives

- **A state event keyed by root** (`m.thread.name` with `state_key` = root event ID). This gives
  current-value semantics, server-side resolution and inclusion in sync for free, and power levels
  could gate it. However, room state is unbounded in a busy room with many threads, every name
  ends up in every joining member's state, and state keys cannot express "the root's sender may
  set this" without an auth rule change or the `@user:...` state key ownership conventions of
  MSC3757, which do not fit a key that is an event ID.
- **`rel_type: m.reference`** instead of a new relation type, with clients filtering by event type.
  This works with existing server relation handling and is a reasonable choice; a dedicated
  relation type was chosen so that `/relations` can be filtered precisely and so that servers can
  validate and bundle it without seeing event types, which are hidden in encrypted rooms.
- **`rel_type: m.thread`** (sending the name into the thread). This would count as a reply, bump
  unread counts and appear in the thread's timeline, which is the opposite of what a rename should
  do.
- **Bundling the current name** in the `m.thread` bundled aggregation of the root
  (`unsigned.m.relations["m.thread"]`), next to `latest_event` and `count`. That aggregation
  describes replies, so the name gets its own `m.thread.name` entry instead.
- **Sending the name unencrypted**, as an earlier version of this proposal did. This avoids phantom
  notifications without a push rule, but exposes names to the homeserver, and the push problem is
  better solved in general.
- **Enforcing only on `/send` and in clients**, without an event authorization change. This needs no
  new room version, but isn't enforced over federation.
- **Using the root's content** (an edit adding a title). Only the root's sender can edit it, so
  moderators could not rename, and the name would be lost on clients that fold edits differently.

## Security considerations

- Names are user-generated text shown in UI chrome. Clients MUST treat them as plain text and
  SHOULD cap their displayed length so a long name cannot cover other UI.
- Without the auth rule, server validation only covers local senders, so clients validate too.
- A moderator (at the `thread_name` level, 50 by default) can rename any thread, including one
  started by a higher-powered user. With the default power levels, this matches their ability to
  redact that user's messages.

## Unstable prefix

Until this proposal is accepted, implementations use `moe.crafty.matrix.thread_name` for the event
type, the relation type, the bundle key and the power level key. This is the identifier already
used by the existing implementation in the Zam client. The push rule uses the ID
`.moe.crafty.matrix.rule.thread_name` and matches the unstable relation type.

## Dependencies

- The `event_property_is` push rule condition (already in the spec).
- A new room version for the auth rule. The `/send` check and client validation work without it.
- Bundling is optional for servers.
