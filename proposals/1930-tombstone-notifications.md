# Proposal to add a default push rule for m.room.tombstone events

Currently users are unaware of when a room becomes upgraded, leaving them potentially in the old room
without knowing until they visit the room again. By having a notification for when the room is upgraded,
users are able to ensure they are able to stay relevant in rooms by joining the upgraded room.


## Proposal

A new default override rule is to be added which is similar to `@room` notifications:

```json
{
    "rule_id": ".m.rule.tombstone",
    "default": true,
    "enabled": true,
    "conditions": [
        {
            "kind": "event_match",
            "key": "type",
            "pattern": "m.room.tombstone"
        }
    ],
    "actions": [
        "notify",
        {
            "set_tweak": "highlight",
            "value": true
        }
    ]
}
```


## Tradeoffs

Clients could calculate this on their own and show some sort of "room upgraded" notification instead,
however by doing it this way it means that all clients would need to be aware of room upgrades. Having
a default push rule means that clients get this notification for free. Clients which want a more diverse
UX can still do so by ignoring this push rule locally.
