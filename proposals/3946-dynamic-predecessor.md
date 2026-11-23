# MSC3946: Dynamic room predecessor

Currently, the only way to specify the predecessor of a room is during room creation in
the `m.room.create` state event which can't be changed after the room is created
(the `m.room.create` event is immutable and can't be changed retroactively).

This is in contrast to specifying the successor of a room via the `m.room.tombstone`
state event in the `replacement_room` content field which can be sent at any time to
update the state.

Traditionally, the predecessor use case has only been necessary for room upgrades where
one room is replaced by another and since the old room exists at the time of the new
room being created, it can easily be specified in the `m.room.create` event of the new
room.

But in history import cases like
[MSC2716](https://github.com/matrix-org/matrix-spec-proposals/pull/2716), specifying the
predecessor after the fact becomes important because the new historical room wasn't
available to reference when the current room was originally created. It's important to
note that history import is more than just
[MSC2716](https://github.com/matrix-org/matrix-spec-proposals/pull/2716) since people
can use [MSC3316 timestamp
massaging](https://github.com/matrix-org/matrix-spec-proposals/pull/3316) `?ts=123`
query parameter to send messages back in time and in general servers can craft events to
appear as being sent at any timestamp which are accepted over federation.

Replacing the predecessor of a room is also nice if you make a mistake in the import
process and only notice after the fact. You can easily create a new historical room with
the mistake corrected and splice it into the predecessor/successor chain as necessary.

For the Gitter import case specifically (personal use case), we're using the single
`/send?ts=123` endpoint with timestamp massaging. We're creating a separate historical
room, importing the message history one by one, tombstoning to point to the "live" room
and want to use this MSC to have the "live" room's predecessor point back to the
historical room.


## Proposal

Add a `m.room.predecessor` state event type where you can specify the room predecessor.
This allows the predecessor state to be updated as necessary.

Event type: State event
State key: A zero-length string.

**`m.room.predecessor` event `content` field definitions:**

key | type | value | description | required
--- | --- | --- | --- | ---
`predecessor_room_id` | string | Room ID | A reference to the room that came before and was replaced by this room | yes
`via_servers` | [string] | List of server names | The servers to attempt to join the room through. These servers should be participating in the room to be useful. This option is necessary since room ID's are not routable on their own.

The presence of `m.room.predecessor` state in the room should take priority over the
`predecessor` specified in the `m.room.create` event.

An additional note is that since via servers are not specified alongside the
`predecessor` in a `m.room.create` event, the `m.room.create` usage should probably be
phased out in favor of this new event. Even if the via servers were specified in the
`m.room.create` event, they'd quickly go out of date, as the `m.room.create` event is
immutable. Whenever via servers change, the dynamic room predecessor event can be
updated with new via information


## Potential issues

*None surmised so far*


## Alternatives

One possible alternative is to allow sending the `m.room.create` multiple times but this
would require extensive [authorization
rule](https://spec.matrix.org/v1.5/rooms/v10/#authorization-rules) changes and
considerations.

It would also be good to consider whether `predecessor` should be part of the
`m.room.create` at all. Maybe we should consider removing it in favor of this new event
type.


## Security considerations

`m.room.predecessor` is a state event that falls under the same power-level state
restrictions/permissions as other state events so there shouldn't be any additional
considerations here.

Room upgrades are a known hairy area of Matrix and how clients deal with them (or lack
of) but this doesn't change any of the existing semantics of predecessors. This is just
a way to change the predecessor of where people should point to instead.


## Unstable prefix

While this feature is in development, the `m.room.predecessor` state event can be used
as `org.matrix.msc3946.room_predecessor`.

Clients can choose to honor the unstable event type at their discretion.


