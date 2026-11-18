# MSC4279: Server notice rooms

[Server Notices](https://spec.matrix.org/v1.13/client-server-api/#server-notices) are already a concept
within Matrix, though they are often perceived as [phishing attempts](https://github.com/element-hq/element-meta/issues/1759),
limiting their usefulness. At the time of their introduction, event-based server notices were primarily
intended to make users aware of Terms of Service changes on homeservers, especially as GDPR legislation
was starting to take effect. Over the years since, a few sharp edges have been found:

1. As already mentioned, the server sends a regular room invite to the user, which looks a lot like
   a phishing attempt. Users have no indication that they can trust that the invite is valid.
2. Despite being an invite, Synapse's implementation doesn't allow the user to reject it. Users get
   confusing/annoying error messages which build some trust in the invite, but erode trust in the
   server/admin/protocol's ability to function.
3. The rooms are easily lost, and can't be "closed". This leads to data being abandoned forever on
   the server.
4. The events use a custom msgtype for enhanced UI, though clients rarely implement such behaviour
   and instead rely on the fallback.

This proposal addresses these core concerns by replacing the event-based system with a room-based
mechanism. Rooms are created using presets (though could be created manually still, if desired) and
have a specific room type that clients can use to render them properly. They are still technically
sent as invites to the user, however this detail is expected to be hidden from the user in clients.
There are also some events and behaviours specified to allow the room to be cleaned up, and signal
to the client/user what actions they can take.

By improving the mechanism, the T&S team at the Matrix.org Foundation hopes to be able to use the
functionality to communicate with users who report content about the status of their reports, and
with users who have moderation action taken against them. These rooms can also support two-way
communication, allowing users to appeal the team's decision with useful context.


## Future MSC work

As a feature, server notice rooms can expand in scope until they consume all available matter in the
universe. To help limit this proposal's scope, allowing it to more easily move through the process,
the following non-exhaustive list of things are deliberately left for future proposals to tackle:

* Integrating server notice rooms into report/ticket flows. One possible option here is to extend the
  appservice room registration to include specific [room types](https://spec.matrix.org/v1.13/client-server-api/#types),
  which would allow an appservice to bridge between ticketing and Matrix. A related MSC may be to
  extend the various reporting APIs to (optionally) return a room ID to ease the user experience of
  sending a report and immediately getting a feedback "we got your report!" message.
* Interactions with sending notices to users over federation. This proposal recommends that servers
  either take measures to prevent clients from showing such rooms over federation as official, or
  outright refuse to participate. A future MSC could introduce a way to add trust decorations to the
  room, somehow.


## Proposal

The existing [`m.server_notice message type`](https://spec.matrix.org/v1.13/client-server-api/#server-notices)
is deprecated for removal by a future MSC. It is replaced by this MSC's mechanism.

A new `m.server_notice` [room type](https://spec.matrix.org/v1.13/client-server-api/#types) is
established, denoting a room as "Notice Room". Servers SHOULD limit creation of server notice rooms
to an implementation-specific definition of "administrators". When the server encounters the room
type over federation, the server SHOULD either strip the room type before serving the room to the
client, or refuse to participate. Stripping the room type prevents clients from getting confused
about how 'official' the notice is, though leads to subpar user experience.

There are two major kinds of Notice Rooms that a server may wish to use:

1. Notices the invited user(s) can reply to.
2. Readonly notices.

Both of these kinds are determined by the power levels in the room. If the user has permission to
send events of an appropriate type, the user may reply.

To make creation easier, two new [room creation presets](https://spec.matrix.org/v1.13/client-server-api/#creation)
are introduced to match the two notice kinds: `notice_readonly` and `notice`. They have the following
events set by default:

For `notice_readonly`:

* [`m.room.create`](https://spec.matrix.org/v1.13/client-server-api/#mroomcreate) has `content`:
  ```jsonc
  {
    "m.federate": false,
    "type": "m.server_notice"
  }
  ```

* [`m.room.history_visibility`](https://spec.matrix.org/v1.13/client-server-api/#mroomhistory_visibility)
  has `content`:
  ```jsonc
  {
    "history_visibility": "shared"
  }
  ```

* [`m.room.join_rules`](https://spec.matrix.org/v1.13/client-server-api/#mroomjoin_rules) has `content`:
  ```jsonc
  {
    "join_rule": "invite"
  }
  ```

* [`m.room.guest_access`](https://spec.matrix.org/v1.13/client-server-api/#mroomguest_access) has
  `content`:
  ```jsonc
  {
    "guest_access": "can_join"
  }
  ```

* [`m.room.power_levels`](https://spec.matrix.org/v1.13/client-server-api/#mroompower_levels) has
  `content`:
  ```jsonc
  {
    "events_default": 100,
    "ban": 100,
    "kick": 100,
    "invite": 100,
    "notifications": {
      "room": 100
    },
    "redact": 100,
    "state_default": 100,
    "users_default": 0,
    "users": {
      "$CREATOR_USER_ID": 100
    }
  }
  ```

For `notice`, the same events are sent with the `m.room.power_levels` having `events_default: 0`
instead of `events_default: 100`.

For both presets, the following other things *should* happen too:

* The `is_direct` flag on [`/createRoom`](https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3createroom)
  defaults to `true`.
* All invitees are given power level 0 (either explicit or implicit).
* The `name` flag on [`/createRoom`](https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3createroom)
  defaults to `Server Notice`.
* Implied by the power levels above, the room creator is giving power level 100.

Note that `m.federate` defaults to `false` for now. This may change in a future MSC, and is used to
further reinforce that notices shouldn't be sent over federation for now.


### Implementation expectations

To ensure consistent experience for users, the following constraints apply to Notice Rooms.

1. All server notices MUST be sent as *invites*, though clients SHOULD intercept the room invite to
   render it with native UI.
2. Users MUST NOT reject the invite. This is enforced by the server.
3. Users MUST NOT [leave](https://spec.matrix.org/v1.13/client-server-api/#leaving-rooms) or forget
   the room until the creator allows it (how this works is described later in this section). This is
   enforced by the server.
4. Clients SHOULD render the user's current Notice Rooms in a dedicated section of their UI rather
   than part of a room list.
5. Notice rooms SHOULD be created with suitable encryption enabled.
6. Servers SHOULD NOT allow notice rooms to be created without the use of the presets defined by this
   proposal. This is to force developers to *really* think about whether they need to override the
   default properties and change the behaviour of the room. They can still set things like `name`,
   `power_level_content_override`, etc.
7. When a user leaves a notice room, the notice is considered "archived". Archived notices may be
   [forgotten](https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3roomsroomidforget)
   to "delete" them.
8. If the client the user is leaving the notice room through doesn't support archived notices, the
   client SHOULD automatically [forget](https://spec.matrix.org/v1.13/client-server-api/#post_matrixclientv3roomsroomidforget)
   the room too.
9. Clients SHOULD NOT offer the ability to report users, rooms, or events in notice rooms.
10. Servers SHOULD use standard event types when communicating with users. For example, `m.room.message`
    with `msgtype: m.text` rather than custom or obscure types.
11. Clients SHOULD NOT show a member list, presence, typing notifications in notice rooms. Clients
    SHOULD NOT send typing notifications, either.
12. With respect to read receipts, clients SHOULD NOT show read receipts for any other user than the
    one that is logged in. Clients SHOULD send read receipts, if the user's settings permit it.
13. Clients SHOULD disable slash commands and sending threaded messages in notice rooms.
14. Clients SHOULD show the room name and topic prominently, if set.

Example gold-standard client implementation is attached to this MSC as {TODO: Insert Element Web PR here}.

Mentioned above, servers cannot allow a user to leave the room until the creator (or realistically,
anyone with suitable power level) allows it. To do this, the creator sends an `m.room.leave_rules`
state event with an empty string for a state key. This is a new event type. The `content` would be
very similar to the join rules event:

The `leave_rule` may be either `allow` or `deny`, and has a different default depending on the room
type. For `m.server_notice` rooms, the default is `deny`. For all other rooms, the default is `allow`.
The leave rule is *not *enforced by auth rules and therefore does not require a new room version. A
future MSC may change this.

Once the leave rule is set to `allow`, the user may be permitted to leave the room.

Servers should note that users can leave rooms through the [dedicated endpoints](https://spec.matrix.org/v1.13/client-server-api/#leaving-rooms)
and [`m.room.member`](https://spec.matrix.org/v1.13/client-server-api/#mroommember) events directly
in the protocol. Both will need to be blocked.


## Safety considerations

Server admins are theoretically able to utilize this API to spam content to their users. Affected
users aren't able to escape it either, unless the server admin lets them (which they probably wouldn't).
This kind of abusive behaviour is already possible with creative reverse proxy rules, and it's likely
that users on the server will not be enjoying their experience for other reasons. Users are encouraged
to embrace freedom of choice for where their account resides.

Safety teams which use this functionality to communicate with users should ensure that appropriate
measures are in place to avoid excessive exposure to abusive or harmful material. This may include
aggressive per-room rate limits and server-side policies to reject content like images from being
sent in the room.

Safety teams should also consider closing/resolving any related tickets once the other user(s) in
the notice room leave.


## Security considerations

This proposal can theoretically allow users to create rooms which appear trusted to other rooms, if
the server does not properly filter out rooms it didn't create before sending them to users. This is
most possible while an older server and newer client are in use: the server doesn't know it's supposed
to be filtering the room, and the client is simply responding to input it was given.

An approach for fixing this would be for the client to check the supported specification versions by
the server, determining whether the filtering code *should* be present. If the server doesn't support
the relevant specification version (or newer), the client should disable server notice room support.

A future MSC may also create ways to verify the creator/sender, allowing the server to drop its filter.
[MSC4145](https://github.com/matrix-org/matrix-spec-proposals/pull/4145) is a step towards this,
though without federated trust.


## Potential issues

In deprecating the event-based server notices, the usage limit notifications are also deprecated. It
is expected that the server simply sends a regular text message over a new server notice room instead,
possibly immediately allowing the receiver to leave the room. The client would ultimately render this
with a dedicated UI instead of a banner or regular room message.

Users which are [suspended](https://spec.matrix.org/v1.13/client-server-api/#account-suspension) can't
normally send messages. Servers are encouraged to allow messages to be sent in notice rooms if the
power levels support it, as this may be the user's only way to appeal an action taken against their
account. The same applies to accepting/joining the notice room, and leaving it.

Technically, notice rooms could contain more than two users. Server implementations SHOULD limit invite
lists to one other user during creation, but SHOULD NOT impede a creator's ability to invite more users
after creation (if power levels allow).


## Alternatives

No significant alternatives identified.


## Unstable prefix

While unstable:

* The room type becomes `org.matrix.msc4279.server_notice`
* The presets become `org.matrix.msc4279.notice_readonly` and `org.matrix.msc4279.notice`
* The leave rules event type becomes `org.matrix.msc4279.leave_rules`
* The `org.matrix.msc4279` feature flag is published on [`/_matrix/client/versions`](https://spec.matrix.org/v1.13/client-server-api/#get_matrixclientversions)

While stable, but not released/merged:

* The stable `m.server_notice` room type can be used.
* The stable preset names can be used.
* The stable leave rules event type can be used.
* The `org.matrix.msc4279.stable` feature flag is published on [`/_matrix/client/versions`](https://spec.matrix.org/v1.13/client-server-api/#get_matrixclientversions)

When merged:

* Stable identifiers must be used.
* The appropriate spec release is published on [`/_matrix/client/versions`](https://spec.matrix.org/v1.13/client-server-api/#get_matrixclientversions)