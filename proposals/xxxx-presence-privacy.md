# MSC0000: Template for new MSCs

Sharing [presence](https://spec.matrix.org/v1.15/server-server-api/#presence) in Matrix currently has the following problem [currently acknowledged in spec](https://spec.matrix.org/v1.15/client-server-api/#security-considerations-4):

- Presence currently has an all or nothing approach on two levels:
  - As client, you can opt to not (explicitly) send presence.
  - Not as part of spec, but commonly done in practice: As server admin, you can disable the presence feature fully server-wide in some server implementations, for example
    in synapse. In theory e.g. synapse's module API allows writing a module for block/allowlisting to only fan out presence to
    certain servers or users. However, presence is commonly simply disabled server-wide, as it is known as a resource hog.
- Consequently, as a user, I can not choose with whom I want to share my presence:
  - Either I go fully private and disable presence in my client,
  - or I accept that my presence will be shared with anyone I share a room with and not only those I want to.


## Proposal

Presence is currently sent over federation as an object containing the sending user's info.
Determining the destination of the info is left up to the receiving homeserver.

From a user perspective, it may make sense to limit sharing presence e.g. in the following ways:
- default allow/deny
- list of MXID exceptions to the default
- list of server exceptions to the default
- share with DMs toggle
- per-room settings to share with everyone in this room

Clients can choose to implement UI for this as they consider appropriate.
Clients could additionally e.g. choose to disable presence for this session entirely as before this MSC.

This improvese user choice, privacy, and depending on user choices has the potential to reduce server load
significantly.


### Client-Server API

Introduce privacy settings for presence in the account data using a new `m.presence_sharing_config` event with the following
content:

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

The sending user's homeserver reads these settings to determine to whom to fan out my presence updates.
It likely makes sense to align the logic for applying these rules with
[MSC4155](https://github.com/matrix-org/matrix-spec-proposals/pull/4155).

Compared to the above, the special case is that we also allow room IDs, which the server should resolve to the currently known list of
room members (`membership: join`) of that room to apply the matching algorithm.

Clients SHOULD update the list of room IDs in the exception list when following room upgrades.

Anecdotally, servers could add configuration options for server admins to set e.g. a privacy preserving default
configuration or overrides as an implementation detail.


### Server-Server API

Based on <https://spec.matrix.org/v1.15/server-server-api/#presence> we add the `allowed_recipients` field:

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

`allowed_recipients` is a list of MXIDs or MXID-globs. The receiving homeserver MUST only distribute the presence update
to local users whose MXID matches this list. The sending server SHOULD NOT include any MXIDs or globs not matching the
receiving homeserver.

If `allowed_recipients` is not present, empty, or null, the update is to be treated as before this MSC (backwards compatibility).


## Potential issues

None known.


## Alternatives

It would be a possible variation of the proposed Server-Server API to also allow listing room IDs, which get resolved
again on the receiving server. This would introduce the minor risk that the receiving server sees a different member
list than the sending server.

Many variations of the allow/blocklist configuration mechanism are possible, such as with/out globs, including or not
including rooms, setting a default value, etc.
For consistency, we consider to align the mechanism with similar ones in other places in spec or similar MSCs, such as
[MSC4155](https://github.com/matrix-org/matrix-spec-proposals/pull/4155).


## Security considerations

Since presence is sent non-e2ee via federation, the homeserver of a receiving user will know my presence and could also show it to more of its users than intended by me.
We regard this as acceptable since it's similar to regular metadata leaks in matrix and still an improvement over the current situation.


## Unstable prefix

Instead of `m.presence_sharing_config`, unstable implementations shall use the unstable identified
`events.matrix-community.presence_sharing_config`.


## Dependencies

For consistency, we consider to align the mechanism with similar ones in other places in spec or similar MSCs, such as [MSC4155](https://github.com/matrix-org/matrix-spec-proposals/pull/4155).
