---
toc_hide: true
---

Upon receipt of a redaction event, the server must strip off any keys
not in the following list:

-   `event_id`
-   `type`
-   `room_id`
-   `sender`
-   `state_key`
-   `content`
-   `hashes`
-   `signatures`
-   `depth`
-   `prev_events`
-   `prev_state`
-   `auth_events`
-   `origin`
-   `origin_server_ts`
-   `membership`

The content object must also be stripped of all keys, unless it is one
of one of the following event types:

-   `m.room.member` allows key `membership`.
-   `m.room.create` allows key `creator`.
-   `m.room.join_rules` allows key `join_rule`.
-   `m.room.power_levels` allows keys `ban`, `events`, `events_default`,
    `kick`, `redact`, `state_default`, `users`, `users_default`.
-   `m.room.aliases` allows key `aliases`.
-   `m.room.history_visibility` allows key `history_visibility`.
