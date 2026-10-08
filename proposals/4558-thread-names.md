# MSC4558: Thread names

[Threads](https://spec.matrix.org/v1.16/client-server-api/#threading) give a room a way to split a
conversation off the main timeline, but a thread has no identity beyond its root event. Clients
label a thread with a preview of the root's body, which works for "reply to this message" threads
but poorly for longer-lived ones: a thread that started with "hey, quick question" and turned into
the release planning discussion is still listed as "hey, quick question".

Other chat platforms let a thread carry a short title, set by whoever started it or by a moderator,
shown in the thread list and the thread's header. This proposal adds that to Matrix with a single
new event type and relation type, and no server changes.

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
timeline (like any unknown event type, they are already hidden by most clients).

The event has no `body` fallback on purpose. A rename is metadata, not a message, and clients that
do not understand it should show nothing rather than a line of text.

A name SHOULD be normalised before sending and again when read by trimming leading and trailing
whitespace. Whitespace within the name is kept as sent. Clients SHOULD limit names to 100
characters and MAY truncate longer names when displaying them. A name that is empty after
normalisation, or a `name` that is missing or not a string, means the thread has no name.

### Who may name a thread

Because a naming event is an ordinary room event, the server will accept one from any member who
can send events. Clients therefore decide which naming events count. A naming event is **valid**
if its sender is either:

1. the sender of the thread root (it is their thread), or
2. a user whose power level is at least the room's `redact` level (a moderator: someone who can
   already remove other users' messages, and so could remove an abusive name anyway).

Naming events from any other sender MUST be ignored. Power levels are evaluated against the
current room state.

Rooms MAY additionally restrict who can send `m.thread.name` at all through the `events` map of
`m.room.power_levels`, which the server enforces for non-state events too. That cannot express
rule 1, which is why the rule above lives in the client.

### Resolving the current name

The current name of a thread is taken from the valid naming event with the greatest
`origin_server_ts` among those related to the root. Ties keep the order the server returned them
in. If that event clears the name, the thread is unnamed; older naming events do not show through.

To load a thread's name, a client fetches the root's relations of this type, newest first:

```
GET /_matrix/client/v1/rooms/{roomId}/relations/{rootId}/m.thread.name/m.thread.name?dir=b&limit=20
```

and applies the rule above to the returned chunk. After that, clients keep the name current from
sync: a new valid naming event for the root replaces the cached name if it is newer.

### Redaction

The redaction algorithm strips `name` and `m.relates_to` from a naming event, so a redacted naming
event no longer targets any root and is ignored. When the naming event behind the current name is
redacted, the client re-resolves the name, and the next-newest valid naming event (if any) takes
over. A moderator removing an abusive name therefore restores the previous one.

### Encryption

**Naming events are sent unencrypted, including in encrypted rooms.**

An encrypted naming event reaches the server as `m.room.encrypted`, which matches the default
`.m.rule.encrypted` (or `.m.rule.encrypted_room_one_to_one`) push rule and notifies every member.
Clients can suppress the notification once they decrypt the event, but some push paths cannot
(for example a web push service worker that must display something for every push it receives),
so every rename would become a phantom "new message" on members' devices. A cleartext
`m.thread.name` event matches no default push rule and notifies no one.

The consequence is that thread names are visible to the homeserver, in the same way room names
(`m.room.name`) and topics (`m.room.topic`) are. Clients SHOULD tell users this when they name a
thread in an encrypted room.

### Display

Clients that support this proposal SHOULD show the thread's name, where it has one, in place of or
alongside the root preview wherever the thread is identified: the thread list, the header of the
thread view, and the thread summary under the root in the main timeline. Clients SHOULD offer
naming to the users permitted by the rules above, and SHOULD hide the option from others.

## Potential issues

- **Clients that don't support it** show nothing: the root preview stays the only label. This is
  the intended degradation, but it means a name chosen to disambiguate a thread is invisible to
  part of the room.
- **`origin_server_ts` is chosen by the sender's server** and can be wrong or manipulated. A
  permitted namer with a skewed clock could pin an old name over a newer one. Ordering by
  topological order would be more robust, but `/relations` does not expose it and the current
  behaviour matches how clients already order edits.
- **Spam can push valid events out of the first page.** If more than `limit` invalid naming events
  are sent after the last valid one, the first `/relations` page contains no valid event and the
  thread looks unnamed. Clients MAY paginate further; room admins can also restrict the event type
  in power levels.
- **Root senders who leave** keep their right to rename the thread under rule 1 if they rejoin.
  This mirrors how a user can always edit their own messages.
- **No server-side aggregation.** Every client fetches `/relations` once per thread it displays.
  For a long thread list that is one request per thread. See Alternatives.
- **Unencrypted in encrypted rooms** is a deliberate privacy trade-off (see Encryption), and may be
  surprising to users who assume everything in an encrypted room is encrypted.

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
  later aggregate it (below) without inspecting event types.
- **`rel_type: m.thread`** (sending the name into the thread). This would count as a reply, bump
  unread counts and appear in the thread's timeline, which is the opposite of what a rename should
  do.
- **Bundling the current name** in the `m.thread` bundled aggregation of the root
  (`unsigned.m.relations["m.thread"]`), next to `latest_event` and `count`. This removes the extra
  request per thread, but needs server changes and requires the server to apply the permission
  rule. It is compatible with this proposal and could follow it.
- **Encrypting the name and adding a default push rule** to suppress notifications for it. The
  server cannot see the type of an encrypted event, so no server-side push rule can match it; this
  only works if every push path can decrypt before notifying.
- **Using the root's content** (an edit adding a title). Only the root's sender can edit it, so
  moderators could not rename, and the name would be lost on clients that fold edits differently.

## Security considerations

- Names are user-generated text shown in UI chrome. Clients MUST treat them as plain text and
  SHOULD cap their displayed length so a long name cannot cover other UI.
- Because permission is enforced by clients, a misbehaving client may display names from senders
  that should be ignored. This affects only that client's users.
- Names in encrypted rooms are visible to the homeserver (see Encryption).
- A moderator can rename any thread, including one started by a higher-powered user. This matches
  their existing ability to redact that user's messages.

## Unstable prefix

Until this proposal is accepted, implementations use `moe.crafty.matrix.thread_name` for both the
event type and the relation type. This is the identifier already used by the existing
implementation in the Zam client.

## Dependencies

None. This proposal uses only existing endpoints (`/send`, `/relations`) and existing power level
semantics.
