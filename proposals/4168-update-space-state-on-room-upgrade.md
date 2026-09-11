# MSC4168: Update `m.space.*` state on room upgrade

When a [room upgrade](https://spec.matrix.org/v1.11/client-server-api/#room-upgrades) is performed,
many state events are copied over to the new room, to minimize the amount of work the user has to do
after the upgrade. However, the spec doesn't currently recommend that `m.space.child` or `m.space.parent`
be copied over, as well as these events being updated in other rooms.

This leads to spaces only showing the old versions of rooms, meaning that users joining the space
would be met with a screen telling them that the conversation has moved somewhere else. On top of
that, clients which organize rooms by the space they're in wouldn't organize upgraded space
members, as they would not be part of the space. While the space members can be updated manually,
this can be very tedious and prone to error (i.e. missing specific rooms from the manual process),
especially for spaces with many rooms and sub-spaces.

## Proposal

In the following sentences, "relevant space state events" refer to `m.space.parent` events for all
room types, in addition to `m.space.child` events for rooms with a type of
[`m.space`](https://spec.matrix.org/v1.16/client-server-api/#types).

When a room upgrade is performed, servers SHOULD copy relevant space state events from the old room
to the new room. The `sender` field in the new event SHOULD be set to the user who performed the
upgrade.

In addition, servers SHOULD send new relevant space state events pointing to the upgraded room in
rooms that reference the old room via `m.space.parent` or `m.space.child` events. In practice, this
means:
- In rooms that reference the old room via `m.space.child` events (roughly speaking:
  spaces which are parents of the upgraded room), the upgrading server
  SHOULD send a new `m.space.child` event with `state_key` set to the new room's ID,
  copying the `order` and `suggested` fields from the `content` of the
  `m.space.child` with `state_key` of the previous room ID.
- In rooms that reference the old room via `m.space.parent` events (roughly speaking: child rooms
  of an upgraded space), the upgrading server SHOULD send a new `m.space.parent` event with
  `state_key` set to the new room's ID. If the previous `m.space.parent` event has `canonical` set
  to `true` in `content`, homeservers SHOULD update the old state event to set `canonical` to
  `false`, while setting it to `true` in the newly-sent `m.space.parent` event.

Like the events sent in the new room, these events sent in existing rooms SHOULD be set to the user
who performed the upgrade.

Note that this will only be possible in rooms where the upgrading
user (or any other user on the same homeserver, if the implementation decides to use any user it
can) has the power to do so.

Additionally, for both event types, homeserver implementations MAY remove the `via` field of
relevant space events referencing the previous room, to signal to clients that they shouldn't join
the previous room. Otherwise, said events SHOULD remain unchanged. 

The `via` field of each new relevant space state event pointing to the upgraded room SHOULD only
contain the server name of the server doing the upgrade, regardless of its previous content. This is
because the servers listed in the previous `via` field may not have joined the upgraded room yet,
and thus servers may not be able to join through them.

### Examples
Given the following initial rooms:
```mermaid
flowchart TB
    !project_space -->|child| !feedback_space
    !project_space -->|child, order: '1'| !support
    !project_space -->|child, suggested| !development

    !feedback_space -->|parent| !project_space
    !support -->|parent| !project_space

    !feedback_space -->|child| !beta_users
    !feedback_space -->|child| !suggestions

    !beta_users -->|parent, canonical| !feedback_space
    !suggestions -->|parent| !feedback_space
```

Here is the changed & new state after (assuming a user on `example.org` is upgrading the following rooms):
### Upgrading `!project_space` to `!upgraded_project_space`

#### `!upgraded_project_space`:
```diff
+{
+    "type": "m.space.child",
+    "state_key": "!feedback_space",
+    "content": {
+        "via": ["example.org", "another.domain", "yet-another.domain"]
+    }
+}
+{
+    "type": "m.space.child",
+    "state_key": "!support",
+    "order": "1",
+    "content": {
+        "via": ["example.org", "another.domain", "yet-another.domain"]
+    }
+}
+{
+    "type": "m.space.child",
+    "state_key": "!development",
+    "suggested": true,
+    "content": {
+        "via": ["example.org", "another.domain", "yet-another.domain"]
+    }
+}
```

#### `!feedback_space` & `!support`:
```diff
+{
+    "type": "m.space.parent",
+    "state_key": "!upgraded_project_space",
+    "content": {
+        "via": ["example.org"]
+    }
+}
```

Additionally, if the server implementation decides to remove the previous space's `via`:

```diff
 {
     "type": "m.space.parent",
     "state_key": "!project_space",
-    "content": {
-        "via": ["example.org", "another.domain", "yet-another.domain"]
-    }
+    "content": {}
 }
```

### Upgrading `!support` to `!upgraded_support`

#### `!upgraded_support`:
```diff
+{
+    "type": "m.space.parent",
+    "state_key": "!project_space",
+    "content": {
+        "via": ["example.org", "another.domain", "yet-another.domain"]
+    }
+}
```

#### `!project_space`:
```diff
+{
+    "type": "m.space.child",
+    "state_key": "!upgraded_support",
+    "order": "1",
+    "content": {
+        "via": ["example.org"]
+    }
+}
```

Additionally, if the server implementation decides to remove the previous room's `via`:

```diff
 {
     "type": "m.space.child",
     "state_key": "!support",
     "order": "1",
-    "content": {
-        "via": ["example.org", "another.domain", "yet-another.domain"]
-    }
+    "content": {}
 }
```

### Upgrading `!feedback_space` to `!upgraded_feedback_space`

#### `!project_space`:
```diff
+{
+    "type": "m.space.child",
+    "state_key": "!upgraded_feedback_space",
+    "content": {
+        "via": ["example.org"]
+    }
+}
```

Additionally, if the server implementation decides to remove the previous space's `via`:

```diff
 {
     "type": "m.space.child",
     "state_key": "!feedback_space",
-    "content": {
-        "via": ["example.org", "another.domain", "yet-another.domain"]
-    }
+    "content": {}
 }
```

#### `!upgraded_feedback_space`:
```diff
+{
+    "type": "m.space.child",
+    "state_key": "!beta_users",
+    "content": {
+        "via": ["example.org", "another.domain", "yet-another.domain"]
+    }
+}
+{
+    "type": "m.space.child",
+    "state_key": "!suggestions",
+    "content": {
+        "via": ["example.org", "another.domain", "yet-another.domain"]
+    }
+}
+{
+    "type": "m.space.parent",
+    "state_key": "!project_space",
+    "content": {
+        "via": ["example.org", "another.domain", "yet-another.domain"]
+    }
+}
```

#### `!beta_users`:
```diff
+{
+    "type": "m.space.parent",
+    "state_key": "!upgraded_feedback_space",
+    "canonical": true,
+    "content": {
+        "via": ["example.org"]
+    }
+}
 {
     "type": "m.space.parent",
     "state_key": "!feedback_space",
-    "canonical": true,
     "content": {
         "via": ["example.org", "another.domain", "yet-another.domain"]
     }
 }
```

Additionally, if the server implementation decides to remove the previous space's `via`:

```diff
 {
     "type": "m.space.parent",
     "state_key": "!feedback_space",
-    "content": {
-        "via": ["example.org", "another.domain", "yet-another.domain"]
-    }
+    "content": {}
 }
```

#### `!suggestions`:
```diff
+{
+    "type": "m.space.parent",
+    "state_key": "!upgraded_feedback_space",
+    "content": {
+        "via": ["example.org"]
+    }
+}
```

Additionally, if the server implementation decides to remove the previous space's `via`:

```diff
 {
     "type": "m.space.parent",
     "state_key": "!feedback_space",
-    "content": {
-        "via": ["example.org", "another.domain", "yet-another.domain"]
-    }
+    "content": {}
 }
```

## Potential issues

This proposal does not attempt to update `m.space.*` state in rooms where the user upgrading the room
is not able to update them, as this not only likely requires something like
[MSC4049](https://github.com/matrix-org/matrix-spec-proposals/pull/4049), but also adds other additional
complications (e.g. which server should update the state?).

Users may also not want to update events in other rooms. Hopefully this proposal can be used to determine
if there is a use-case for not updating events in other rooms. If there is one, then a query parameter can
be added to toggle this feature.

## Alternatives

As above, utilizing [MSC4049](https://github.com/matrix-org/matrix-spec-proposals/pull/4049) to update
`m.space.*` events in other rooms could be an alternative, but due to additional complications in addition
to requiring this MSC to be merged, it is deemed as not the best solution (for now).

## Security considerations

None considered.

## Unstable prefix

None required, as currently no new endpoints or fields are being proposed.

## Dependencies

None.
