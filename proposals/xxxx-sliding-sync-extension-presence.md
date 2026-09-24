# MSCXXXX: Sliding Sync Extensions: Presence

[MSC4186: Simplified Sliding Sync][MSC4186] only includes core room data in the sync response. Other data, such as
presence, comes from "extensions", which clients opt into individually using the `extensions` field of the sync request.

This proposal defines the extension for [presence]. Presence allows users to learn about each other's social
availability, see whether other users have been active recently, and set statuses to show what they are up to.

This extension depends on [MSC4532: Revised Social Presence][MSC4532] for overall improvements to presence semantics and
reduced presence update volumes.

# Proposal

A new sliding sync extension is added, with the extension key `presence`.

The extension follows the common semantics defined in [MSC4508: Sliding Sync Extensions: Common format and
Typing][MSC4508]. It is a per-room extension. The common per-room fields (`lists` and `rooms`) control which rooms'
users are eligible to be included in the response.

## Extension request

The extension uses the common fields defined in [MSC4508]:

```json
{
    "extensions": {
        "presence": {
            "enabled": true,
            "lists": ["rooms", "dms"],
            "rooms": ["!milkshake-enjoyers:example.tld"]
        }
    }
}
```

## Extension response

If the `presence` extension is enabled, the server MUST include a `presence` section in the `extensions` response field
if it has presence updates to distribute. It MAY omit the section when there are no updates.

The `ExtensionResult` has the following format:

| Name         | Type                       | Required | Comment                                |
|--------------|----------------------------|----------|----------------------------------------|
| `user_ids`   | `{string: PresenceUpdate}` | No       | A map of user IDs to presence updates. |

A `PresenceUpdate` has the same format as an [`m.presence` Sync Event], as modified by [MSC4532]:

| Name              | Type              | Required | Comment                                                            |
|-------------------|-------------------|----------|--------------------------------------------------------------------|
| `presence`        | `PresenceState`   | No       | The user's current presence state                                  |
| `status`          | `Status`          | No       | The user's status object                                           |

`PresenceState` and `Status` are defined according to [MSC4532]. For the purposes of this extension, `presence` defaults
to `offline` when it is not specified, and the `msg` field of `status` defaults to an empty string. Either field SHOULD
be omitted if it holds its default value.

Note that, unlike [`GET /_matrix/client/v3/sync`], the presence states are not wrapped in an `m.presence` ephemeral
event with `type` and `content`. The extension can only ever carry presence, so the wrapper conveys no information.

Also unlike [`GET /_matrix/client/v3/sync`] is the omission of `last_active_ago`. Clients that wish to render a last
active indicator SHOULD query [`GET /_matrix/client/v3/presence/{userId}/status`][cs-get-presence]. See [Alternatives].

### Semantics

The *visible user set* is the set of all users joined to the rooms that are in scope for the extension and that the
requesting user is joined to. Note that this includes the requesting user themselves, as is required for clients to
know when other devices update their presence.

For brevity, a user in the visible user set will be herein referred to as a *visible user*. A presence *update* occurs
when a visible user's state changes from the client's last acknowledged response, or when a user enters the visible user
set **for the first time**. The visible user set is only valid for the current connection. Only the latest presence
update for a user at any given time is considered.

The server returns the full state, rather than only the changed fields, of each visible user with a presence update that
the client has not yet acknowledged by sending `pos`. Due to the nature of presence, each of a visible user's presence
updates wholly replace their previous state, so the user only needs to have their latest state returned.

Clients MUST treat any received presence updates as full new states. In particular, the client MUST interpret missing
fields according to their previously defined defaults, rather than as no change from the previously sent state.

#### Visible users

When a user meets the criteria for, and is therefore admitted into, the visible user set for the first time in a
connection, the server sends their current presence state. This is in accordance with the presence update rules given
above. The server MUST NOT include users in the response that are not in the visible user set, and the server MUST send
presence updates for users while they remain in the visible user set.

> [!IMPORTANT]
>
> The server SHOULD transmit presence updates for the visible user set in batches across sync calls to prevent unbounded
> responses. While the batch sizes are left to implementations, the server SHOULD always use the latest presence update
> for a visible user at the point where the user is included in a response, even if their presence changes partway
> through a series of batched responses.

When a user no longer meets the criteria for, and is therefore removed from the visible user set, the server MUST NOT
send any further presence updates for them until they become a visible user again. In particular, the server MUST NOT
send an update intended to invalidate or clear their most recent presence update before they left the visible user set.
Equally, clients MUST NOT interpret a user's absence from any response as the intention to invalidate or clear their
state.

For example, given the criteria for the visible user set:
* When a room enters scope for the extension, its joined users are evaluated against the criteria.
  * If any of its users becomes a visible user for the first time, their current state will be included in a response.
  * If any of its users are already a visible user, or they have been a visible user before, their latest state is only
    included in the response if it has changed since `pos`.
* When a room leaves scope for the extension, its joined users are evaluated against the criteria.
  * If any of its users are joined to another room in scope for the extension, they may remain a visible user.
  * Otherwise, they are no longer a visible user, and their updates will no longer be included in responses until they
    are a visible user again.

#### Connections

As a consequence of the way presence updates are defined, the server MUST NOT send a presence state for a given visible
user that is equivalent to their last state sent in a response acknowledged by the client. However, if a client reuses
the last given `pos` in multiple requests, the server MUST retry the response with presence updates that have not yet
been acknowledged.

Given that the visible user set is only valid for the current connection, a user becoming a visible user for the first
time also only applies to the current connection. After a connection is reset with `M_UNKNOWN_POS`, the client discards
all presence updates sent. The visible user set is evaluated when the extension is enabled in the new connection, and
users entering the new visible user set will have their initial states synchronised.

When the extension is enabled on a connection, regardless of if it was previously disabled, its scope is used to
evaluate the visible user set. As previously described, users entering the visible user set will either have their
initial states sent, or they will begin to have their presence updates sent again.

When the extension is disabled on a connection, all users are removed from the visible user set. If the client wishes to
enable the extension again, it MUST retain the information acknowledged by sending `pos` so far, because it will not be
retransmitted on the same connection.

#### Long-polling

A presence update does not count as an update for the purposes of long-polling; that is, the server MAY not return
immediately when one exists. This is to prevent presence from incurring a large resource and performance penalty, at the
cost of potentially delayed delivery.

## Potential issues

### Performance

Presence is historically known to be a performance-intensive feature of the protocol. If the homeserver selects a
sufficiently small batch size and is participating in sufficiently large rooms, the queue of updates to send may grow
indefinitely as more users undergo state transitions than are being synchronised. The use of  [MSC4532]'s
simplifications is intended to mitigate this by significantly reducing the volumes of data to be handled. Also of note
is the provision to entirely omit offline users with no status set.

## Alternatives

### Ephemeral Wrapper

The response could wrap each room's receipts in an `m.presence` ephemeral event with `type` and `content` fields,
matching [`GET /_matrix/client/v3/sync`]. The wrapper would let a client reuse its ephemeral event parsing, but it is
redundant when the extension only carries presence updates. [MSC4508] already drops the ephemeral event wrapper for
typing notifications.

### Access Control

The response could, instead of returning presence data for all users joined to rooms that are in scope for the
extension, follow [MSC4495]'s access control. This has been deferred to [MSC4495] itself, as it would unnecessarily
expand the scope of this proposal.

### Data Retention

The server could retransmit current states for newly-visible users whenever a room enters scope for the extension. This
would allow clients to forget data for users leaving the visible user set. However, it would also require the
transmission of potentially large volumes of duplicated data in a given connection. Additionally, doing so may require
the server to send removal markers for users leaving the visible user set, which would compound the bandwidth
requirements of the extension.

### Full Transmission

Instead of only transmitting states for users with updates, the server could sync the full visible user set on each
response. While this would simplify the extension, it would violate the incremental sync model, and put significant
pressure on both servers and clients to send and handle the unnecessary data.

### Room Scoping

Rather than accumulating a global set of users with updates, the extension's response could be scoped per room selected
in the configuration. This would make the relationship between the rooms and the visible user set more obvious, and
potentially make it easier for clients to select the relevant data to the room they are currently displaying. However,
the global response model was chosen to ensure each user can only be included in the response once. 

This does have the side effect of preventing users from appearing to have different presence states in different rooms,
but the authors of this proposal consider the UX implications of differing presence per room to be unnecessarily complex
and confusing for end users to reason about.

### Last Active Ago

This extension does not transmit `last_active_ago` values, instead leaving clients to request [`GET
/_matrix/client/v3/presence/{userId}/status`][cs-get-presence]. The response could include `last_active_ago`, but this
would involve syncing data for all non-active users. Given that clients typically only render last active indicators in
DMs, rather than full sets of room members, the authors of this proposal determined that transmitting the values would
be a substantial and needless burden on sync traffic.

## Security considerations

This extension exposes most of the same data as the [`m.presence` Sync Event] in [`GET /_matrix/client/v3/sync`],
subject to [MSC4532]'s removal of user activity tracking.

Implementations must be careful not to leak information for previously visible users that have exited the visible user
set after an update has been queued. For example, if a user exits the visible user set partway through a queue of
updates being processed, there is potential for the server to continue to send their queued update if it does not
validate their status as a visible user at response time. This requirement is given in the proposal under [Visible
Users](#Visible-Users).

If [MSC4495] is accepted, there is the same potential that servers may ignore the remote users' recipient selections if
any of the local users are in their recipient sets. This is considered acceptable by the authors of this proposal on the
basis that the remote user implicitly trusts the receiving server to handle their presence by explicitly selecting one
or more local users.

## Unstable prefix

| Stable identifier         | Purpose                                                            | Unstable identifier                                          |
| ------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------ |
| `presence`                | The extension key for [MSC4186]'s `POST /_matrix/client/v4/sync`   | `org.continuwuity.presence_v2.mscXXXX.presence`              |

Servers may advertise support for this extension by listing `org.continuwuity.presence_v2.mscXXXX` in the
`unstable_features` section of the response to [`GET /_matrix/client/versions`].

Once this proposal completes FCP, servers may advertise support for the stable identifiers by listing
`org.continuwuity.presence_v2.mscXXXX.stable` in `unstable_features`; clients may use this while they are waiting for
the server to adopt a version of the spec that includes it.

[MSC4186]: https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/4186-simplified-sliding-sync.md
[MSC4495]: https://github.com/matrix-org/matrix-spec-proposals/pull/4495
[MSC4508]: https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/4508-sliding-sync-extension-typing.md
[MSC4532]: https://github.com/matrix-org/matrix-spec-proposals/pull/4532
[presence]: https://spec.matrix.org/v1.19/client-server-api/#presence
[`m.presence` Sync Event]: https://spec.matrix.org/v1.19/client-server-api/#mpresence
[cs-get-presence]: https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientv3presenceuseridstatus
[`GET /_matrix/client/v3/sync`]: https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3sync
[`GET /_matrix/client/versions`]: https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientversions
[Alternatives]: #Alternatives
