# MSC4325: Presence Privacy

Sharing [presence](https://spec.matrix.org/v1.15/server-server-api/#presence) in Matrix currently has the following problems [acknowledged in the specification](https://spec.matrix.org/v1.15/client-server-api/#security-considerations-4):

- The specification itself does not limit who can access the presence of a specific user. The only methods of limiting presence are thus:
  - As client, to not send presence.
  - As server admin, disabling the presence feature entirely (or only over federation). In theory e.g. synapse's module API allows writing a module for block/allowlisting to only fan out presence to
    certain servers or users. However, presence is commonly disabled server-wide, as it is known to be resource heavy.
- Consequently, users can not choose with whom they want to share their presence:
  - Either they go fully private and disable presence in their client,
  - or they accept that their presence will be shared with anyone they share a room with (depending on server behavior; the spec also leaves the option for servers to not limit this at all).

## Prior Art

Prior to [MSC1819](https://github.com/matrix-org/matrix-spec-proposals/pull/1819), there existed a mechanism to
subscribe to other users' presence updates via "presence lists".
Users would have to request and the request be approved in order to subscribe and receive presence info.
While in theory this was more privacy-preserving than the status quo, it never was implemented in a way that let users
choose by approving requests.
We consider that the back and forth of requesting and approving requests is likely tiring UX, and the ability to send requests added a possible spam vector.

In contrast to this now historic concept, the approach in this MSC gives the opportunity to users to manage their
presence visibility proactively, including some comfort features with globs and room IDs.

## Proposal

Presence is currently sent over federation as an object containing the sending user's info.
Determining the destination of the info is left up to the receiving homeserver.

From a user perspective, it may make sense to limit sharing presence, e.g. in the following ways:
- A default value (allow or deny)
- A list of MXIDs to be treated as exceptions to the default
- A list of servers to be treated as exceptions to the default
- Allowing to share presence with all users the user shares a DM with
- Per-room settings to share presence with everyone in this room

Clients can choose to implement UI for this as they consider appropriate.
Regardless of this MSC, clients retain the option to not send presence at all.

This improves user choice, privacy, and has the potential to reduce server load
significantly.

### Client-Server API

Clients change the presence configuration by modifying a new `m.presence_sharing_config` event in the account data with the following content:

```jsonc
{
    "allowed_users": [
        "@alice:example.org",
        "@b*:example.org",
        "@*:matrix.org",
        "!co1dcoffee"
    ],
    "denied_users": [
        "@bob:example.org"
    ]
}
```

The sending user's homeserver reads these settings to determine to which users to send presence updates.
To do this, the server follows this algorithm:
1. Send presence to all users matching a user ID explicitly listed, or matching a glob in, `allowed_users`
2. Send presence to all users in a room with a room ID listed in `allowed_users` in membership state `join` (here, we do *not* allow globs, since there generally are no groups of rooms sharing useful patterns in their room ID), **unless**
  1. The user is [ignored](https://spec.matrix.org/latest/client-server-api/#ignoring-users)
  2. The receiving user is listed in `denied_users` explicitly or by matching a glob
3. Send presence to all users the user shares a room with, **unless**
  1. The user is [ignored](https://spec.matrix.org/latest/client-server-api/#ignoring-users)
  2. The receiving user is listed in `denied_users` explicitly or by matching a glob
  3. The room's ID is listed under `denied_users`

This makes it explicit that a server MUST NOT send presence to any user that the sending user does not share a room with or lists in `allowed_users`.

Servers MAY pre-configure arbitrary values for this event.

For clarity, we make it explicit that in cases where a user has multiple common rooms with the sending user and
some of these rooms are listed under `denied_users`, the user still receives presence, as long as they share at
least one room which is not listed in `denied_users`. If *all* shared rooms are listed under `denied_users`, the user does not receive presence.

Clients SHOULD update the list of room IDs in the exception list when following room upgrades.

Servers SHOULD ignore rooms on the list when the user is not a member and remove rooms from either allow or denied list when the user
leaves the room.
This is to avoid users "subscribing" to rooms that the server is not a member of anymore and thus has stale membership info about.

### Server-Server API

To the `m.presence` EDU ([spec](https://spec.matrix.org/v1.15/server-server-api/#presence)), we add the `allowed_recipients` field:

```jsonc
{
  "content": {
    "push": [
      {
        "currently_active": true,
        "last_active_ago": 5000,
        "presence": "online",
        "status_msg": "Making cupcakes",
        "user_id": "@john:matrix.org",
        "allowed_recipients": ["@alice:example.org", "@b*:example.org"]
      }
    ]
  },
  "edu_type": "m.presence"
}
```

`allowed_recipients` is a list of MXIDs or MXID-globs. This means that the sending server has to resolve
room IDs to their joined members before sending this event. The receiving homeserver MUST only distribute the presence update
to local users whose MXIDs match this list. The sending server SHOULD NOT include any MXIDs or globs not matching the
receiving homeserver.

If `allowed_recipients` is not present, empty, or null, the update is to be treated as before this MSC for backwards compatibility.
This typically means sending the presence to all users the respective user shares a room with.

## Potential issues

Presence is resource-heavy. We don't expect this change to increase the resource usage in any relevant way.

The list of `allowed_recipients` in the federation EDU may get very large.
A possible solution would be for servers to federate presence to servers with many recipients less frequently or based
on additional heuristics (e.g. prioritise DMs, invite-only rooms, etc).

Though the spec does not currently limit the size of EDUs, this proposal can lead to extremely long lists of `allowed_recipients` being sent over federation, e.g. when presence is shared with big rooms.
We recommend to chunk the presence EDUs to chunks of 256 MXIDs per presence EDU.
This is trivial to implement: any remaining MXIDs can be transmitted in a second EDU.

## Alternatives

Many variations of the allow/blocklist configuration mechanism are possible, such as with or without globs, including or not
including rooms, setting a default value, splitting user IDs and room IDs into separate lists, etc.
For consistency, we consider to align the mechanism with similar ones in other places in spec or similar MSCs, such as
[MSC4155](https://github.com/matrix-org/matrix-spec-proposals/pull/4155).

It would be a possible variation of the proposed Server-Server API to leave resolving of room IDs to user IDs to the receiving server.
This has the potential to reduce the size of the EDU sent over federation when allowing room IDs.
However this would introduce the minor risk of discrepancy that the receiving server sees a different member
list than the sending server.

## Security considerations

Since presence is sent non-e2ee via federation, the homeserver of a receiving user will know the presence and could also show it to more of its users than intended.
This can break user expectations when a user denies sending presence to `@alice:example.org` but allows
`@bob:example.org` and `example.org` delivers the presence to Alice regardless.
We regard this as acceptable since it's similar to regular metadata leaks in Matrix and realistically still an improvement over the current situation.

## Unstable prefix

Instead of `m.presence_sharing_config`, unstable implementations shall use the unstable identifier
`events.matrix-community.presence_sharing_config`.

To detect server support, clients can either rely on the spec version (when stable)
or the presence of a `events.matrix-community.presence_sharing_config` flag in `unstable_features` on `/versions`.

## Dependencies

While not strictly a dependency, we consider to align the mechanism with similar ones in other places in spec or similar MSCs,
such as [MSC4155](https://github.com/matrix-org/matrix-spec-proposals/pull/4155) for the sake of consistency.
