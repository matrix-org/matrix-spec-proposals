# MSC2432: Updated semantics for publishing room aliases

This MSC offers an alternative to [MSC2260](https://github.com/matrix-org/matrix-doc/issues/2260).

## Background

The [`m.room.aliases`](https://matrix.org/docs/spec/client_server/r0.6.0#m-room-aliases)
state event exists to list the available aliases for a given room. This serves
two purposes:

  * It allows existing members of the room to discover alternative aliases,
    which may be useful for them to pass this knowledge on to others trying to
    join.

  * Secondarily, it helps to educate users about how Matrix works by
    illustrating multiple aliases per room and giving a perception of the size
    of the network.

However, it has problems:

  * Any user in the entire ecosystem can create aliases for rooms, which are
    then unilaterally added to `m.room.aliases`, and room admins are unable to
    remove them. This is an abuse
    vector (https://github.com/matrix-org/matrix-doc/issues/625).

  * For various reasons, the `m.room.aliases` event tends to get out of sync
    with the actual aliases (https://github.com/matrix-org/matrix-doc/issues/2262).

## Proposal

We propose that that room moderators should be able to manually curate a list
of "official" aliases for their room, instead of matrix servers automatically
publishing lists of all room aliases into the room state. No particular
guarantees are offered that this alias list is entirely accurate: it becomes
room moderators' responsibility to keep it so.

Meanwhile, the aliases that map to a given room on a given server become
the ultimate responsibility of the administrators of that server. We give them
tools to inspect the alias list and clean it up when necessary, in addition to
the current tools which allow restriction of who can create aliases in the
first place.

A detailed list of proposed modifications to the Matrix spec follows:

 * `m.room.aliases` loses any special meaning within the spec. In particular:

   * Clients should no longer format it specially in room timelines.

   * Clients and servers should no longer consider `m.room.aliases` when
     [calculating the display name for a
     room](https://matrix.org/docs/spec/client_server/r0.6.0#calculating-the-display-name-for-a-room).

     (Note: servers follow the room display-name algorithm when calculating
     room names for certain types of push notification.)

   * A future room version will remove the special [authorization
rules](https://matrix.org/docs/spec/rooms/v1#authorization-rules) and
[redaction rules](https://matrix.org/docs/spec/client_server/r0.6.0#redactions).

 * [`m.room.canonical_alias`](https://matrix.org/docs/spec/client_server/r0.6.0#m-room-canonical-alias)
   is extended to include a new `alt_aliases` property. This, if present,
   should be a list of alternative aliases for the room. An example event might
   look like:

   ```json
   {
     "content": {
       "alias": "#somewhere:localhost",
       "alt_aliases": [
         "#somewhere:overthere.com",
         "#somewhereelse:example.com"
       ]
     },
     "room_id": "!jEsUZKDJdhlrceRyVU:example.org",
     "state_key": "",
     "type": "m.room.canonical_alias"
   }
   ```

   It is valid for `alt_aliases` to be non-empty even if `alias` is absent or
   empty. This means that no alias has been picked out as the 'main' alias.

   (Note: although the spec currently claims that `alias` is mandatory, Synapse
   generates `m.room.canonical_alias` events with no `alias` property when the
   main alias is deleted. This change would legitimise that behaviour.)

   (For clarity: it is not proposed that the `alt_aliases` be considered when
   calculating the displayname for a room.)

 * [`PUT /_matrix/client/r0/rooms/{roomId}/state/{eventType}/{stateKey}`](https://matrix.org/docs/spec/client_server/r0.6.0#put-matrix-client-r0-rooms-roomid-state-eventtype-statekey)
   is extended to recommend that servers validate any *new* aliases added to
   `m.room.canonical_alias` by checking that it is a valid alias according to
   the [syntax](https://matrix.org/docs/spec/appendices#room-aliases), and by
   looking up the alias and and that it corresponds to the expected room ID.

   (Note: Synapse currently implements this check on the main alias, though
   this is unspecced.)

   The following error codes are specified:

   * HTTP 400, with `errcode: M_INVALID_PARAMETER` if an attempt is made to add
     an entry which is not a well-formed alias (examples: too long, doesn't
     start with `#`, doesn't contain a `:`).

   * HTTP 400, with `errcode: M_BAD_ALIAS` if an added alias does not point at
     the given room (either because the alias doesn't exist, because it can't
     be resolved due to an unreachable server, or because the alias points at a
     different room).

 * Currently, [`PUT /_matrix/client/r0/directory/room/{roomAlias}`](https://matrix.org/docs/spec/client_server/r0.6.0#put-matrix-client-r0-directory-room-roomalias)
   attempts to send updated `m.room.aliases` events on the caller's
   behalf. (This is implemented in Synapse but does not appear to be explicitly
   specced.) This functionality should be removed.

 * Currently, [`DELETE /_matrix/client/r0/directory/room/{roomAlias}`](https://matrix.org/docs/spec/client_server/r0.6.0#delete-matrix-client-r0-directory-room-roomalias),
   attempts to send updated `m.room.aliases` and/or `m.room.canonical_alias`
   events on the caller's behalf, removing any aliases which have been
   deleted. (Again, this is implemented in Synapse but does not appear to be
   explicitly specced.) The `m.room.aliases` functionality should be removed,
   and the `m.room.canonical_alias` functionality should be extended to cover
   `alt_aliases`.

   The behaviour if the calling user has permission to delete the alias but
   does not have permission to send `m.room.canonical_alias` events in the room
   (for example, by virtue of being a "server administrator", or by being the
   user that created the alias) is implementation-defined. It is *recommended*
   that in this case, the alias is deleted anyway, and a successful response is
   returned to the client.

 * A new api endpoint, `GET /_matrix/client/r0/rooms/{roomId}/aliases` is
   added, which returns the list of aliases currently defined on the local
   server for the given room. The response looks like:

   ```json
   {
     "aliases": [
       "#somewhere:example.com",
       "#somewhereelse:example.com",
       "#special_alias:example.com"
     ]
   }
   ```

   This API can be called by any current member of the room (calls from other
   users result in `M_FORBIDDEN`). For rooms with `history_visibility` set to
   `world_readable`, it can also be called by users outside the room.

   Servers might also choose to allow access to other users such as server
   administrators.

 * [`GET /_matrix/client/r0/publicRooms`](https://matrix.org/docs/spec/client_server/r0.6.0#get-matrix-client-r0-publicrooms)
   (and the `POST` variant) no longer return `aliases` as part of `PublicRoomsChunk`.
   Clients do not appear to make use of this field, and `canonical_alias` is maintained
   to provide similar information.

Various APIs are currently subject to implementation-defined access
restrictions. No change to the specification is introduced in this regard
(implementations will continue to be free to impose their own
restrictions). Nevertheless as part of this MSC it is useful to consider some
proposed changes to Synapse's implementation:

 * No change: `PUT /_matrix/client/r0/directory/room/{roomAlias}`: Synapse
   only allows access to current members of the room, and also exposes some
   configuration options which allow restriction of which users are allowed to
   create aliases in general.

 * `DELETE /_matrix/client/r0/directory/room/{roomAlias}`: in this case,
   currently Synapse restricts its use to the user that created the alias, and
   server admins.

   It is proposed to extend this to local users who have a power-level
   sufficient to send an `m.room.canonical_alias` event in the room that the
   alias currently points to.

 * [`PUT /_matrix/client/r0/directory/list/room/{roomId}`](https://matrix.org/docs/spec/client_server/r0.6.0#put-matrix-client-r0-directory-list-room-roomid)
   and the corresponding unspecced `DELETE` api (both of which set the
   visibility of a room in the public directory): currently Synapse restricts
   their use to server admins and local users who have a PL sufficient to send
   an `m.room.aliases` event in the room (ignoring the special auth
   rules). This will be changed to check against the PL required to send an
   `m.room.canonical_alias` event.

It is envisaged that Matrix clients will then change their "Room Settings" user
interface to display the aliases from `m.room.canonical_alias` instead of those
in `m.room.aliases`, as well as giving moderators the ability to update that
list. Clients might also wish to use the new `GET
/_matrix/client/r0/rooms/{roomId}/aliases` endpoint to obtain and display the
currently-available local aliases, though given that this list may be subject
to abuse, it should probably not be shown by default.

### Future work

This work isn't considered part of this MSC, but rather a potential extension
for the future.

 * It may be useful to be able to query remote servers for their alias
   list. This could be done by extending `GET
   /_matrix/client/r0/rooms/{roomId}/aliases` to take a `server_name`
   parameter, and defining an API in the server_server spec which will expose
   the requested information, subject to the calling homeserver having at least
   one user with a right to see it.

 * Similarly, room moderators may wish to be able to delete aliases on a remote
   server for their room. We could envisage a federation API which allows such
   a request to be made, subject to the calling homeserver having at least one
   moderator in the room.

## Potential issues

The biggest problem with this proposal is that existing clients, which rely on
`m.room.aliases` in one way or another, will lose functionality. In particular,
they may not know about aliases that exist, or they may look at outdated
`m.room.aliases` events that list aliases that no longer exist. However, since
`m.room.aliases` is best-effort anyway, these are both problems that exist to
some extent today.

## Alternatives

We considered continuing to use `m.room.aliases` to advertise room aliases
instead of `m.room.canonical_alias`, but the significant changes in semantics
made that seem inappropriate.

We also considered using separate state events for each advertised alias,
rather than listing them all in one event. This might increase the number of
aliases which can be advertised, and help to reduce races when editing the
list. However, the 64KB limit of an event still allows room for hundreds of
aliases of any sane length, and we don't expect the list to be changing
frequently enough for races to be a practical concern. Ultimately the added
complexity seemed redundant.

A previous suggestion was
[MSC2260](https://github.com/matrix-org/matrix-doc/issues/2260), which proposed
keeping `m.room.aliases` largely as-is, but giving room moderators tools to
control who can send them via room power-levels. We dismissed it for the
reasons set out at
https://github.com/matrix-org/matrix-doc/pull/2260#issuecomment-584207073.

## Security considerations

None currently identified.

## Unstable prefix

While this feature is in development, the following names will be in use:

| Proposed final name | Name while in development |
| --- | --- |
| `GET /_matrix/client/r0/rooms/{roomId}/aliases` | `GET /_matrix/client/unstable/org.matrix.msc2432/rooms/{roomId}/aliases` |

Servers will indicate support for the new endpoint via a non-empty value for feature flag
`org.matrix.msc2432` in `unstable_features` in the response to `GET
/_matrix/client/versions`.
