# MSC2714: Add forward information to forwarded messages

Currently a forwarded message is not easily recognized as a forwarded message. While for messages of `msgtype` `m.text`, `m.emote` and `m.notice` clients could do something in the `formatted_body` of `content`, for all other message types the forward highlighting would be very poor. To get around this and provide a guideline to clients which information should go with a forward, we suggest adding the "forward info" explicitly. See also https://github.com/vector-im/riot-web/issues/4747.

## Proposal

### Providing m.forward

Leaning onto edits (adding `m.new_content` inside `content`), we want to suggest to add `m.forwarded` to `content` to forwarded messages. The required information would cover at least the original `senden`, `room_id` and `origin_server_ts`:

```
{
    "content": {
        "body": "Big Ben, London, UK",
        "geo_uri": "geo:51.5008,0.1247",
        "m.forward": {
            "room_id": "!jEsTZKDJdhfrheTzSU:example.org",
            "sender": "@someone:example.org",
            "origin_server_ts": 1432735824141
        },
        "msgtype": "m.location"
    },
    "event_id": "$143273582443PhrSn:example.org",
    "origin_server_ts": 1432735824653,
    "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
    "sender": "@example:example.org",
    "type": "m.room.message",
    "unsigned": {
        "age": 1234
    }
}
```

Additional infos could be the original `event_id`, `displayname` and `avatar_url` (optionally?).

## Potential issues

Should we care of/can we avoid "fake forwards"? Does it make sense/is it possible at all to only add the original `event_id` when sending a forward and assign the server the responsibility of adding the forward information?

## Alternatives

### Extending info

```
{
    "content": {
        "body": "Big Ben, London, UK",
        "geo_uri": "geo:51.5008,0.1247",
        "info": {
            "forward_info": {
                "event_id": "$123275682943PhrSn:example.org",
                "room_id": "!jEsTZKDJdhfrheTzSU:example.org",
                "sender": "@someone:example.org",
                "origin_server_ts": 1432735824141
            }
        },
        "msgtype": "m.location"
    },
    "event_id": "$143273582443PhrSn:example.org",
    "origin_server_ts": 1432735824653,
    "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
    "sender": "@example:example.org",
    "type": "m.room.message",
    "unsigned": {
        "age": 1234
    }
}
```

### Discarded using m.relates_to

We've also discussed and discarded usind `m_relates_to` for highlighting the message as forward, like the following:

```
"m.relates_to": {
    "rel_type": "m.forwarded",
    "event_id": "!1234:server.abc",
}
```

We discarded this idea for two reasons:

1. The idea of `m.relates_to` seems to be that related messages belong to the same room.
2. Its unclear who should fetch the event from a different room she/he/it is potentially not in and how this could be done at all.


See also our discussion here https://gitlab.com/famedly/app/-/issues/320.
