## MSC4291: Room IDs as hashes of the create event

Currently rooms are identified by a room ID [made from a random string](https://spec.matrix.org/v1.14/appendices/#room-ids)
selected by the creating server, namespaced to the origin server. This allows a malicious server to
create a room whose ID collides with an existing ID, causing security issues if the rooms are confused
together.

This supplants [MSC4051](https://github.com/matrix-org/matrix-spec-proposals/pull/4051) with more information.

### Proposal

We redescribe the room ID to be the event ID of the room's `m.room.create`
event with the room ID sigil `!` instead of the event ID sigil `$`. For example, if a create event ID is
`$31hneApxJ_1o-63DmFrpeqnkFfWppnzWso1JvH3ogLM`, the room ID is
`!31hneApxJ_1o-63DmFrpeqnkFfWppnzWso1JvH3ogLM`.
*This effectively restricts the room ID grammar to be `!` + 43x unpadded urlsafe base64 characters.*

This binds a given room to a specific single `m.room.create` event, eliminating the risk of confusion.
This can be seen as an extension of [MSC1659](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/1659-event-id-as-hashes.md),
which replaced confusable `event_id`s with a hash of the event.

The `room_id` field is removed entirely from the `m.room.create` event, but is reintroduced on
non-federation APIs, exactly like how the `event_id` is missing over federation but reintroduced on the
other APIs. As the `room_id` is the create event ID, and all `auth_events` cite an `m.room.create`
event, the `auth_events` no longer specify the create event ID. This will slightly reduce
all event payload sizes.

The following changes on a new room version are made:
 - Concerning the create event:
   Step 1 of the [Checks performed on receipt of a PDU](https://spec.matrix.org/v1.14/server-server-api/#checks-performed-on-receipt-of-a-pdu)
   is modified to remove the `room_id` as a universal example of:
   > Is a valid event, otherwise it is dropped. For an event to be valid, it must ~~contain a room_id, and it must~~ comply with the event format of that room version.
 - Concerning the [event format](https://spec.matrix.org/v1.14/rooms/v11/#event-format-1):
   * The "Description" field for `auth_events` is adjusted to state:
     > Required: Event IDs for the authorization events that would allow this event to be in the room.
     >
     > Must contain less than or equal to 10 events. Note that if the relevant auth event selection rules are used,
     > this restriction should never be encountered.
     > **NEW: MUST NOT contain the create event ID (room ID).**
   * The "Description" field for `room_id` is adjusted to state:
     > Required: Room identifier. Omitted on `m.room.create` events.
 - Concerning [auth rules](https://spec.matrix.org/v1.14/rooms/v11/#authorization-rules):
   * Change auth rule 1.2 (“If the domain of the `room_id` does not match the domain of the sender, reject.”)
   to be (“If the create event has a `room_id`, reject”) given we no longer have a `room_id` on create events.
   * Remove auth rule 2.4 (“If there is no `m.room.create` event among the entries, reject.”) given the create event is now implied by the `room_id`.
   * Add auth rule 2.5: "If there are entries whose `room_id` does not match the `room_id` of the event itself, reject."
     This overlaps with [MSC4307](https://github.com/matrix-org/matrix-spec-proposals/pull/4307).
   * Add auth rule 2 (inserted before the current rule 2): "If the event's `room_id` is not an event ID
     for an accepted (not rejected) `m.room.create` event, with the sigil `$` replaced with sigil `!`, reject."

This creates a chicken/egg problem when upgrading rooms because:
 - The `m.room.tombstone` event needs a `content.replacement_room`.
 - The `content.replacement_room` ID is now the create event of the new room.
 - The create event of the new room needs the tombstone event ID in `content.predecessor.event_id`.
 - The `m.room.tombstone` event needs ...

<img width="793" alt="Creator chicken egg problem" src="/images/4291-creator-chicken-egg.png" />


To break this cycle, this MSC removes the `content.predecessor.event_id` field from the `m.room.create` event. There appear to be no security
reasons why this field exists. This field is sometimes used in clients to jump back to the correct part in the old room's timeline when the tombstone
occurred, which can be relevant when there are lots of leave events after the tombstone. Clients that wish to preserve this behaviour may instead
search the old room state for the `m.room.tombstone` event and then jump to that.

### Potential Issues

It is not immediately obvious which server created the room in the first place. See the "Alternatives" section
for a discussion on the pros/cons of this.

The loss of `content.predecessor.event_id` may negatively impact the way clients stitch together timelines in upgraded rooms.

### Alternatives

#### Keeping the domain suffix

We could keep the colon+server suffix as it contains useful information about the creator's server,
and has historically been used as routing information / auth checks in several places:
 - event auth for `m.federate` [in Synapse](https://github.com/element-hq/synapse/blob/9d43bec/synapse/event_auth.py#L312), though the specification [states]((https://spec.matrix.org/v1.15/rooms/v11/#authorization-rules)) this should be applied to the `sender` instead - Step 3.
 - It’s used as a last resort `?via=` candidate [in Synapse](https://github.com/element-hq/synapse/blob/v1.133.0/synapse/handlers/room_member.py#L1177).

It is also desirable to know the creator's server name without having to join and get the full create event
for Trust & Safety purposes. The create event in invites can be spoofed, as can the room ID, but spoofing the
room ID makes the invite unusable whereas spoofing the create event does not. We could rely on the `sender`
instead, but for this to be effective it would be important for servers to use the `sender` domain for routing
purposes, such that if the `sender` was invalid it would cause the invite to be unusable. On the contrary, users
unfamiliar with Matrix may see a room ID like `!OGEhHVWSdvArJzumhm:matrix.org` and think that `matrix.org` hosts/moderates/
is somehow responsible for the room in some way. By dropping the domain, we clearly express that the creator domain
may not be responsible for the contents of the room.

However, by adding the colon+server suffix we would allow malicious servers to create room IDs with _earlier room versions_
which have the same ID as the new proposed format. For example, a malicious server who knows of an existing
vNext room `!31hneApxJ_1o-63DmFrpeqnkFfWppnzWso1JvH3ogLM:example.com` could create a v11 room with the exact
same ID, causing confusion. We therefore need to create a new namespace for vNext room IDs which cannot conflict
with earlier room versions. This is why the colon+server suffix has been removed. We could alternatively encode the
room version along with the domain to form a new namespace e.g `!localpart:domain@version` where `@` has never been
allowed in the set of `domain` characters, but there isn't a strong enough reason to encode such information in
every event.

#### Removing `room_id` entirely from all events

We could remove `room_id` field from all events, and propagate it via `auth_events` instead. This
would make it harder for servers to immediately know which room an event is in as there would be
multiple potentially unknown event IDs as candidates. It’s less awkward to simply keep it in the
`room_id` field and instead remove the create event from `auth_events`.

We could rename `room_id` to `create_event_id` and require servers to universally populate `room_id` for every event
(and drop `create_event_id`) for all events delivered to clients. This better encodes the fact that the
room ID _is_ the create event ID, but it's not clear this provides any advantages beyond that, whilst incurring
fixed costs to rename fields to clients, as well as update existing codebases to look in a different key,
and update the specification to conditionally say "room ID" or "create event ID" depending on the room version.
It's likely not worth the effort, despite it being a clearer key name.

#### Using an ephemeral public key as identifier instead of the create event ID

We could generate an ephemeral keypair, sign the create event with the private key and use the public
key as the room ID. [MSC1228](https://github.com/matrix-org/matrix-spec-proposals/pull/1228) proposed this.
The problem with this approach is that we cannot guarantee that servers will actually treat the keypair
as ephemeral: they could reuse the same keypair to create a spoofed room.

### Security Considerations

This fixes a class of issues caused by confusable room IDs. Servers can currently perform a form of
eclipse attack when other servers join via them by presenting a completely different room to some
servers. This isolates the target server, controlling information that the target server sees. By
linking together the room ID (which is user-supplied e.g via `matrix:` URIs) we can guarantee that
all servers agree on the same create event, and thus the subsequent hash DAG that forms.

Servers may accidentally create the same room if a client creates >1 room in a single millisecond.
This happens because the entropy in the create event is quite small, primarily relying on the
`origin_server_ts`. Server authors concerned about this MAY add in sufficient entropy as a custom
key in the `content` of the create event. As of v11, the redaction algorithm preserves the entire
`content` so such extra keys become part of the event ID and thus the room ID. Servers may also
prefer to apply strong rate limits to prevent this scenario.

The removal of enforced server domain namespaces means event IDs truly are _global_. This means we
rely on the security of the hash function to avoid collisions (which we've always relied on _within_ a
room). This has always been implied due to the federation endpoint `/event/{eventID}`, but this change
makes the data model rely on global uniqueness. See [MSC2848](https://github.com/matrix-org/matrix-spec-proposals/pull/2848)
for more discussion.

### Dependencies

This MSC has no dependencies.
