# MSC4432: Server-wide room name overrides

Matrix tracks room names in the [`m.room.name`] state event. Once set, the value applies to all
members of the room. These global semantics can be undesirable in a corporate context when
organizations on different home servers communicate with each other. Examples include:

- Some organizations might want to prefix federated rooms with "External: ..." while others might
  not.
- When two organizations A and B share a room, A may want to refer to the room as "B" or "B \<\> A"
  whereas B may want to use "A" or "A \<\> B".
- Organizations may want to use internal project names, case references or IDs in the room name to
  help provide context.

Personalised per-user overrides of the room name as proposed by [MSC4431] are not sufficient in
these cases. Instead, organizations require the name to be shared across all users on their
homeserver without impacting the displayed room name for users on other servers.

This proposal addresses this problem by introducing a way to set server-wide overrides of the room
name via a (semi-)managed account data type.

## Proposal

A new room account data type `m.room.name.server_wide` is introduced. The schema is identical to the
schema of `content` in the [`m.room.name`] state event.

    GET /_matrix/client/v3/user/${userId}/rooms/${roomId}/account_data/m.room.name.server_wide
    {
      "name": "Project Phoenix"
    }

The `.server_wide` suffix helps clarify the semantics of the data and distinguishes it from other
types of overrides such as the personal overrides proposed by [MSC4431].

Clients MAY set the override value using the [standard endpoint for writing account data].

    PUT /_matrix/client/v3/user/${userId}/rooms/${roomId}/account_data/m.room.name.server_wide
    {
      "name": "[External] Fancy Inc."
    }

When a value is written, servers MUST propagate it into the corresponding room account data of all
local room members. If the room's join rule is set to `public`, the server MUST propagate the value
into the corresponding room account data of all its users. Similarly, if a new local user is invited
into a room where a server-wide room name exists, servers MUST replicate the value into the user's
room account data.

Servers MAY restrict which users are allowed to write the `m.room.name.server_wide` account data
type. They MAY also make the account data type fully managed and deny write-access to users
entirely. The existing 405 error response type can be used to communicate a lack of privileges back
to the client.

To let clients determine whether or not they can write the new account data type in a specific room
ahead of sending the request, a new capability `m.room.name.server_wide` is introduced. The
capability contains one of two properties `allowed` or `disallowed` both of which are lists of room
IDs. When `allowed` is present, clients can only write the account data type in the contained rooms
but not in others. Contrarily, when `disallowed` is present, clients can write the account data type
in all rooms except for the contained rooms. This is similar to the `allowed` and `disallowed`
properties in the [`m.profile_fields` capability].

``` json5
{
  "capabilities": {
    "m.room.name.server_wide": {
      // Can only write m.room.name.server_wide account data in these two rooms
      "allowed": ["!nD4Jy1hp0We0VmIM9ubjqWLBX_uV8YlTBBPa3a_v2uk", "!0KNSXYXB_2xtEUkQ9MGBRy5oNIOfAKoq2uIqPZCJbI8"]
    }
  }
}
```

``` json5
{
  "capabilities": {
    "m.room.name.server_wide": {
      // Can write m.room.name.server_wide account data in all rooms except for these two
      "disallowed": ["!nD4Jy1hp0We0VmIM9ubjqWLBX_uV8YlTBBPa3a_v2uk", "!0KNSXYXB_2xtEUkQ9MGBRy5oNIOfAKoq2uIqPZCJbI8"]
    }
  }
}
```

When the capability is missing, clients SHOULD assume that they are not allowed to write the account
data type in any rooms.

To apply an existing override, a new first step is inserted at the very beginning of the [room name
computation RECOMMENDATIONs][]: If `m.room.name.server_wide` exists in the room's account data and
is not the empty object (`{}`), use the name given by that item.

Clients should be aware that room account data changes are not communicated via `/sync` for invited
rooms. As a result, clients will have to manually load room account data to check for a potential
server-wide room name when displaying invites.

Clients MAY additionally display the room name implied by the state events [`m.room.name`] and
[`m.room.canonical_alias`] as an indicator for how the room may be displayed for other users.

Since account data cannot be deleted, clients MAY set the value to the empty object (`{}`) to remove
the override. Contrarily, to force an empty room name, clients MAY use a value of `""` for `name` in
the override.

## Potential issues

Confusion may arise when people refer to the same room under different names due to their local
server's overrides. Clients can display both the server-wide and the official name to mitigate this
problem.

Users may miss changes of a room's purpose due to their personal name override. Again, clients can
display both names to help alleviate this issue.

In some cases, users may want to use name overrides from remote servers. For instance, a user may be
joined to work rooms with both a work and a personal account and might want to see the name
overrides from work even when using their personal account. This is not possible under the current
proposal since there is no way to exchange account data between servers. A future proposal may
devise a way to enable this.

## Alternatives

[MSC4431] enables personalised and confidential room name overrides via room account data. This is
not sufficient in cases where multiple local users need to share the same room name, however.

A different, functionally equivalent alternative is using the local [server name] in `state_key`
when sending [`m.room.name`] state events. This has a number of downsides, however.

- In rooms shared by a large number of different organisations, the server-targeted room name events
  may pollute the room state.
- Outside of DMs, regular room members usually don't have the power level needed to send state
  events. As a result, rooms will have to be configured to let appropriate members send
  `m.room.name` events. There is currently no way to configure power levels on the `state_key` level
  though.
- Since state events are shared among all members of a room, server-wide room name overrides are
  exposed to users on other servers.
- To prevent abuse, servers would have to reject `m.room.name` events with a non-empty state key
  that doesn't match the sender's server name. This requires a new step in the event authorization
  rules and thereby a new room version which drastically complicates adoption of the feature.

Some of these concerns could be mitigated by preventing `m.room.name` events with a non-empty
`state_key` from being federated. This would require changes to the state resolution algorithm,
however, which would significantly increase complexity.

## Security considerations

Just like the `m.room.name` state event, server-wide room name overrides may leak metadata to the
home server. This seems like a minor concern, however, given that the feature is partly or fully
server-managed anyway.

## Unstable prefix

| Stable identifier         | Purpose           | Unstable identifier                        |
|---------------------------|-------------------|--------------------------------------------|
| `m.room.name.server_wide` | Account data type | `de.gematik.msc4432.room.name.server_wide` |
| `m.room.name.server_wide` | Capability        | `de.gematik.msc4432.room.name.server_wide` |

## Dependencies

None.

  [`m.room.name`]: https://spec.matrix.org/v1.17/client-server-api/#mroomname
  [MSC4431]: https://github.com/matrix-org/matrix-spec-proposals/pull/4431
  [standard endpoint for writing account data]: https://spec.matrix.org/v1.17/client-server-api/#put_matrixclientv3useruseridroomsroomidaccount_datatype
  [`m.profile_fields` capability]: https://spec.matrix.org/v1.17/client-server-api/#mprofile_fields-capability
  [room name computation RECOMMENDATIONs]: https://spec.matrix.org/v1.17/client-server-api/#calculating-the-display-name-for-a-room
  [`m.room.canonical_alias`]: https://spec.matrix.org/v1.17/client-server-api/#mroomcanonical_alias
  [server name]: https://spec.matrix.org/v1.17/appendices/#server-name
