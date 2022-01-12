---
type: module
weight: 340
---

### Spaces

{{% added-in v="1.2" %}}

Often used to group rooms of similar subject matter (such as a public "Official
matrix.org rooms" space or personal "Work stuff" space), spaces are a way to
organise rooms while being represented as rooms themselves.

A space is defined by the [`m.space` room type](#types), making it known as a
"space-room". The space's name, topic, avatar, aliases, etc are all defined through
the existing relevant state events within the space-room.

Sending normal [`m.room.message`](#mroommessage) events within the space-room is
discouraged - clients are not generally expected to have a way to render the timeline
of the room. As such, space-rooms should be created with [`m.room.power_levels`](#mroompower_levels)
which prohibit normal events by setting `events_default` to a suitably high number.
In the default power level structure, this would be `100`. Clients might wish to
go a step further and explicitly ignore notification counts on space-rooms.

Membership of a space is defined and controlled by the existing mechanisms which
govern a room: [`m.room.member`](#mroommember), [`m.room.history_visibility`](#mroomhistory_visibility),
and [`m.room.join_rules`](#mroomjoin_rules). Public spaces are encouraged to have
a similar setup to public rooms: `world_readable` history visibility, published
canonical alias, and suitably public `join_rule`. Invites, including third-party
invites, still work just as they do in normal rooms as well.

All other aspects of regular rooms are additionally carried over, such as the
ability to set arbitrary state events, hold room account data, etc. Spaces are
just rooms with extra functionality on top.

#### Managing rooms/spaces included in a space

Spaces form a hierarchy of rooms which clients can use to structure their room
list into a tree-like view. The parent/child relationship can be defined in two
ways: with [`m.space.child`](#mspacechild) state events in the space-room, or with
[`m.space.parent`](#mspaceparent) state events in the child room.

In most cases, both the child and parent relationship should be defined to aid
discovery of the space and its rooms. When only a `m.space.child` is used, the space
is effectively a curated list of rooms which the rooms themselves might not be aware
of. When only a `m.space.parent` is used, the rooms are "secretly" added to spaces
with the effect of not being advertised directly by the space.

{{% boxes/warning %}}
Considering spaces are rooms themselves, it is possible to nest spaces within spaces,
and it is possible to create a loop. Though the creation of loops is explicitly disallowed,
implementations might still encounter them and must be careful not to loop infinitely when
this happens.

Clients and servers should additionally be aware of excessively long trees which may
cause performance issues.
{{% /boxes/warning %}}

##### `m.space.child` relationship

When using this approach, the state events get sent into the space-room which is the
parent to the room. The `state_key` for the event is the child room's ID.

For example, to achieve the following:

```
#space:example.org
    #general:example.org (!abcdefg:example.org)
    !private:example.org
```

the state of `#space:example.org` would consist of:

*Unimportant fields trimmed for brevity.*

```json
{
    "type": "m.space.child",
    "state_key": "!abcdefg:example.org",
    "content": {
        "via": ["example.org"]
    }
}
```
```json
{
    "type": "m.space.child",
    "state_key": "!private:example.org",
    "content": {
        "via": ["example.org"]
    }
}
```

No state events in the child rooms themselves would be required (though they
can also be present). This allows for users
to define personal/private spaces to organise their own rooms without needing explicit
permission from the room moderators/admins.

Child rooms can be removed from a space by omitting the `via` key of `content` on the
relevant state event, such as through redaction or otherwise clearing the `content`.

{{% event event="m.space.child" %}}

###### Ordering

When the client is displaying the children of a space, the children should be ordered
using the algorithm below. In some cases, like a traditional left side room list, the
client may override the ordering to provide better user experience. A theoretical
space summary view would however show the children ordered.

Taking the set of space children, first order the children with a valid `order` key
lexicographically by Unicode code-points such that `\x20` (space) is sorted before
`\x7E` (`~`). Then, take the remaining children and order them by the `origin_server_ts`
of their `m.space.child` event in ascending numeric order, placing them after the
children with a valid `order` key in the resulting set.

In cases where the `order` values are the same, the children are ordered by their
timestamps.  If the timestamps are the same, the children are ordered lexicographically
by their room IDs (state keys) in ascending order.

Noting the careful use of ASCII spaces here, the following demonstrates a set of space
children being ordered appropriately:

*Unimportant fields trimmed for brevity.*

```json
[
    {
        "type": "m.space.child",
        "state_key": "!b:example.org",
        "origin_server_ts": 1640341000000,
        "content": {
            "order": " ",
            "via": ["example.org"]
        }
    },
    {
        "type": "m.space.child",
        "state_key": "!a:example.org",
        "origin_server_ts": 1640141000000,
        "content": {
            "order": "aaaa",
            "via": ["example.org"]
        }
    },
    {
        "type": "m.space.child",
        "state_key": "!c:example.org",
        "origin_server_ts": 1640841000000,
        "content": {
            "order": "first",
            "via": ["example.org"]
        }
    },
    {
        "type": "m.space.child",
        "state_key": "!e:example.org",
        "origin_server_ts": 1640641000000,
        "content": {
            "via": ["example.org"]
        }
    },
    {
        "type": "m.space.child",
        "state_key": "!d:example.org",
        "origin_server_ts": 1640741000000,
        "content": {
            "via": ["example.org"]
        }
    }
]
```

1. `!b:example.org` is first because `\x20` is before `aaaa` lexically.
2. `!a:example.org` is next because `aaaa` is before `first` lexically.
3. `!c:example.org` is next because `first` is the last `order` value.
4. `!e:example.org` is next because the event timestamp is smallest.
5. `!d:example.org` is last because the event timestamp is largest.

##### `m.space.parent` relationships

Rooms can additionally claim to be part of a space by populating their own state
with a parent event. Similar to child events within spaces, the parent event's
`state_key` is the room ID of the parent space, and they have a similar `via` list
within their `content` to denote both whether or not the link is valid and which
servers might be possible to join through.

To avoid situations where a room falsely claims it is part of a given space,
`m.space.parent` events should be ignored unless one of the following is true:

* A corresponding `m.space.child` event can be found in the supposed parent space.
* The sender of the `m.space.parent` event has sufficient power level in the
  supposed parent space to send `m.space.child` state events (there doesn't need
  to be a matching child event).

{{% boxes/note %}}
Clients might need to peek into a parent space to inspect the room state if they
aren't already joined. If the client is unable to peek the state, the link should
be assumed to be invalid.
{{% /boxes/note %}}

{{% boxes/note %}}
A consequence of the second condition is that a room admin being demoted in the
parent space, leaving the parent space, or otherwise being removed from the parent
space can mean that a previously valid `m.space.parent` event becomes invalid.
{{% /boxes/note %}}

`m.space.parent` events can additionally include a `canonical` boolean key in their
`content` to denote that the parent space is the main/primary space for the room.
This can be used to, for example, have the client find other rooms by peeking into
that space and suggesting them to the user. Only one canonical parent should exist,
though this is not enforced. To tiebreak, use the lowest room ID sorted lexicographically
by Unicode code-points.

{{% event event="m.space.parent" %}}

#### Discovering rooms within spaces

Often the client will want to assist the user in exploring what rooms/spaces are part
of a space. This can be done with crawling [`m.space.child`](#mspacechild) state events
in the client and peeking into the rooms to get information like the room name, though
this is impractical for most cases.

Instead, a hierarchy API is provided to walk the space tree and discover the rooms with
their aesthetic details.

The [`GET /hierarchy`](#get_matrixclientv1roomsroomidhierarchy) API works in a depth-first
manner: when it encounters another space as a child it recurses into that space before
returning non-space children.

{{% boxes/warning %}}
Though prohibited, it is still possible for loops to occur. Servers should gracefully
break loops.

Additionally, a given child room might appear multiple times in the response as a
grandchild (for example).
{{% /boxes/warning %}}

{{% http-api spec="client-server" api="space_hierarchy" %}}

##### Server behaviour

In the case where the server does not have access to the state of a child room, it can
request the information over federation with the
[`GET /hierarchy`](/server-server-api/#get_matrixfederationv1hierarchyroomid) API. The
response to this endpoint should be cached for a period of time. The response might
additionally contain information about rooms the requesting user is already a member
of, or that the server is aware of - the local data should be used instead of the remote
server's data.

Note that the response to the client endpoint is contextual based on the user. Servers are
encouraged to cache the data for a period of time, though permission checks may need to
be performed to ensure the response is accurate for that user.
