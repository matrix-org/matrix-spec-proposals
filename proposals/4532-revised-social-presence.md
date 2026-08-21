# MSC4532: Revised Social Presence

Presence and its features have remained largely untouched since its inception. Performance issues have deterred users
and operators alike from presence to the point that extensions of its features are now being proposed within completely
different systems[^1]. Further to this, many have expressed concerns over the excessive information it provides,
particularly the current "Last Active Ago" system revealing when someone last interacted with the network down to the
second, and the confusing behaviour of someone being marked online without being active or idle.

While the companion to this MSC, [MSC4495: Selective Presence][MSC4495], improved performance and privacy by
*restricting access to presence*, this proposal *reshapes presence itself*, simplifying its semantics, providing a
single consistent mechanism for managing near-term persistence, and supporting future extensions, all while furthering
those goals.

## Prior Art

In the early years of Matrix, [a discussion was held][matrix-react-sdk#1676] about the abandonment of the presence
feature and ways it might be improved. Notably, a distinction was drawn between one's presence on Matrix and one's real
status, although status was never fully split out of the presence endpoint, even in [MSC4426: User Status Profile
Fields][MSC4426].

[MSC4043: Presence Override API][MSC4043] is the closest to introducing a solution to the issue of mixing data on
different timescales, with [this remark][MSC4043-status] suggesting that statuses should be included in overrides,
although it does not go as far as to move status away from setting per-client presence.

The picture of efforts to improve presence over time would be incomplete without [MSC3026: "busy" presence
state][MSC3026], where a desired busy state is first introduced. As this proposal was unfortunately abandoned,
Revised Social Presence brings the busy state aboard with adjusted semantics to fit a new model for presence.

## Proposal

The [Presence module] of the Client-Server API and the [Presence section] of the Server-Server API are adjusted as
follows. Implementations of Matrix spec versions containing these features MUST support their datums, endpoints, and
associated behaviours, unless they are explicitly declared to be OPTIONAL.

### Revised Presence States

Ultimately, users do not care about the technical particulars of other users' reachability, they care solely about the
social qualities of their reachability itself. To better serve this need, presence must be reframed from a connection
state alone to a sense of availability. In this framing, this proposal defines the following states:
* `active`: the user is available to reply (fully reachable)
* `idle`: the user has a connected client and **may** reply (potentially reachable)
* `busy`: the user is unavailable to reply (fully unreachable)
* `offline`: the user has no connected clients and **may not** reply (potentially unreachable)

This maps to the previous states as follows:

| Old `presence` | `currently_active` | New `presence` |
|----------------|--------------------|----------------|
| `online`       | `true`             | `active`       |
| `online`       | `false`            | `idle`         |
| `unavailable`  | *                  | `idle`         |
| `offline`      | *                  | `offline`      |

From this point onwards, these terms will be used instead of their existing counterparts except for where it is
explicitly necessary to reference the existing model. The old values of **`"online"` and `"unavailable"` are
deprecated** from the federation [User Presence Update] type, the [`m.presence` Sync Event], the [Presence Client-Server
Endpoints], and [`GET /_matrix/client/v3/sync`] by this proposal. The new states `"active"`, `"idle"`, and `"busy"` are
introduced to all of these mechanisms in their place.

#### Busy State

While `"active"` and `"idle"` map cleanly from existing states encoded by the presence system, `"busy"` is a
[long-requested][MSC3026] feature representing a  connected user's voluntary declaration that they will not be reachable
for other users that wish to solicit conversation. A `"busy"` user is unique in that this state is exclusively triggered
by a curated set of user actions, rather than connection properties or general activity.

If a `"busy"` state is manually selected by a user, it is set via [Presence Overrides] to prevent autonomous regression
to other states, as with other overrides. If a client wishes to set a `"busy"` state autonomously following a select
user action \- for example, if the user joins a call \- it SHOULD do so via the [`GET /_matrix/client/v3/sync`] endpoint
or the [Presence Client-Server Endpoints], as with other states. It is by design that the latter case does not override
the overrides mechanism to prevent clients from interfering with each other's automated actions and being unsure which
state to return the override to.

### Presence Overrides

Users may wish to set their presence state manually on occasion, particularly if they need to let others know they are
temporarily unavailable. This proposal affords users the option to set a near-term persisting override state across all
of their clients, using the `m.presence.persistent` global [Account Data] event.

The new event contains two properties:
* An OPTIONAL string enumeration, `state_override`, which can be any of the previously defined states
  * For its behaviour as part of resolving a user's final presence state, see [State Determination].  
    Its default behaviour is simply to be ignored in this process if it is not set.
* An OPTIONAL object, `status`, acting as a key-value store for status information and containing one property
  (default `{}`)
  * An OPTIONAL string, `msg`, which is a free-form input corresponding with the existing `status_msg` property
    (default `""`)
    * Clients SHOULD trim trailing and leading whitespace from this field
    * Its value constraints are otherwise the same as that of `status_msg` in the [User Presence Update] type
    * For its behaviour in relation to the federation [User Presence Update] status fields, see [Extensible Status].

Any missing property MUST be assumed to use its above default.

Clients MUST NOT modify these properties unless explicitly directed to by a user. Clients and servers MUST ignore states
in `state_override` that they do not recognise, acting as if they were unset.

Any update to the `m.presence.persistent` account data event triggers an immediate presence update for the user.

Example `m.presence.persistent` event:
```json
{
    "state_override": "busy",
    "status": {
        "msg": "Partying like it's 2023!"
    }
}
```

### State Determination

A user's final presence state MUST be determined by their local server according to the first rule that applies below:

1. If all clients are offline, the state is `offline`
2. If `state_override` is set to a recognised value in `m.presence.persistent`, the state is the override
3. If any client sets a `"busy"` state, the state is `busy`
4. If any client sets an `"active"` state, the state is `active`
5. The state is `idle`

This uses the following ownership model:
* Clients determine their presence state
* Users may direct clients to set a specific shared persistent override
* Servers can determine if a client is offline on its behalf

For backwards compatibility rules, see the corresponding section in [Simplified Activity].

#### Offline Timeouts

Since clients are expected to determine when their users are idle, and servers only determine when clients are offline,
[Idle Timeouts] are replaced with offline timeouts. Servers implementing this proposal MUST NOT mark a client as idle
automatically. Servers SHOULD determine a client is offline after a threshold value of time \- for example, 5 minutes \-
has passed since the client's most recent request to [`GET /_matrix/client/v3/sync`] or [`PUT
/_matrix/client/v3/presence/{userId}/status`] completed.

#### Provisions for Application Services

In the case of Application Services, servers actively make requests to them via the [Application Service API].
Practically, this means Application Services can be reliably determined to be offline without servers timing them out
based on inactivity. In order to prevent Application Services from having to update presence for all of their namespaced
users on a given interval, servers MUST NOT apply offline timeouts to an Application Service's exclusive namespaced
users unless requests to the Application Service fail.

#### Provisions for Remote Users

Sometimes, remote servers may experience federation issues without being able to broadcast `offline` states for their
users first. In these instances, it is undesirable for their users to be stuck appearing active. When a server
determines a remote to be unreachable for some time, the server MUST:
1. Store the remote users' current presence states
2. Distribute an `"offline"` state for their `presence` in an [`m.presence` Sync Event] and responses to [`GET
   /_matrix/client/v3/presence/{userId}/status`]
3. When federation to the remote succeeds again, revert their `presence` to the state stored in step 1 in an
   [`m.presence` Sync Event] and responses to [`GET /_matrix/client/v3/presence/{userId}/status`]

Servers SHOULD exclusively monitor outbound federation when determining remotes to be unreachable. Additionally, servers
SHOULD debounce this behaviour, such that a remote becoming unreachable for a few seconds does not trigger state
transitions for all of their users in quick succession.

Implementations that currently send or expect federated rebroadcasts to affirm presence states as part of an interval
offlining system should note that this behaviour is intentionally made redundant by this proposal. Servers SHOULD NOT
perform the offlining procedure described in this section, or rebroadcast their users' states, on a time interval.

### Simplified Activity

#### Currently Active

`currently_active` is redundant because holding the existing `"online"` state without being `currently_active` is now
considered to be `"idle"`, so the only state where `currently_active` applies is `"active"`. Therefore,
`currently_active` is deprecated by this proposal in the [User Presence Update] type, the [`m.presence` Sync Event], and
the [`GET /_matrix/client/v3/presence/{userId}/status`] endpoint.

#### Last Active Ago

`last_active_ago` in the [`m.presence` Sync Event] and [`GET /_matrix/client/v3/presence/{userId}/status`] is redefined
as the number of milliseconds since a user's `presence` last updated from `"active"` to any other state, based on when
the recipient's server received the transitioning EDU. Because this information is now given by the recipient's server,
`last_active_ago` is deprecated from the federation [User Presence Update] type. Clients SHOULD ignore this property
altogether while a user is `"active"`.

Implementations should note that pro-active event tracking is not used in this redefinition of `last_active_ago`.

#### Backwards Compatibility

* Servers SHOULD reinterpret an old presence state or a `currently_active` value of `true` in an incoming presence EDU
  according to the behaviour map given in [Presence States] before passing presence onto clients. This necessarily
  causes clients that do not implement this proposal to display everyone as offline.
* Servers SHOULD ignore all incoming [User Presence Update] `last_active_ago` values and derive their own according to
  the definition above before passing presence onto clients.
* Clients SHOULD reinterpret presence states and `currently_active` values in an [`m.presence` Sync Event] from a server
  that does not advertise support for this proposal according to the behaviour map given in [Presence States].

### Extensible Status

The `status_msg` property of the federation [User Presence Update] type and [`GET
/_matrix/client/v3/presence/{userId}/status`] is **deprecated**. It is replaced with an OPTIONAL extensible `status`
object with a single OPTIONAL string property `msg`. This extensible approach provides for future expanding status
needs, as desired in proposals like [MSC4426]. Whenever this is broadcasted or requested, servers MUST use current value
of the corresponding property in `m.presence.persistent`. For backwards compatibility, servers and clients implementing
this proposal SHOULD process `status_msg` in lieu of the EDU property and endpoint response property respectively.

The same applies to the [`m.presence` Sync Event], where clients implementing this proposal SHOULD treat `status_msg`
from servers that do not advertise support for this proposal as though it were given as `msg` in `status`.

The `status_msg` request body property of the [`PUT /_matrix/client/v3/presence/{userId}/status`] endpoint is
**deprecated** altogether. Clients that wish to manage [Presence Overrides] MUST do so via the `m.presence.persistent`
account data to ensure the data is consistent across all a user's clients. It should be noted that this deprecation also
means [`PUT /_matrix/client/v3/presence/{userId}/status`] is no longer useful to clients that call [`GET
/_matrix/client/v3/sync`].

### `m.presence` EDU and Sync Event Examples

Given all the changes made in previous sections, here is an example [User Presence Update] object:
```jsonc
{
    "presence": "busy",
    "status": {
        "msg": "Partying like it's 2023!"
    },
    "user_id": "@john:example.com",
    // Deprecated:
    "last_active_ago": 0,
    // Deprecated but already optional:
    "currently_active": false,
    "status_msg": ""
}
```

And the corresponding example [`m.presence` Sync Event]:
```jsonc
{
    "content": {
        "presence": "busy",
        "status": {
            "msg": "Partying like it's 2023!"
        },
        "last_active_ago": 0,
        // Deprecated but already optional:
        "currently_active": "false",
        "status_msg": ""
    },
    "sender": "@john:example.com",
    "type": "m.presence"
}
```

## Potential Issues

### State Flapping

Clients may switch between states rapidly in short periods. The fewer clients a user has at a given state in [State
Determination], the more likely this is to cause flapping over federation. Implementations and instance operators may
wish to debounce outbound federated state transitions to mitigate this issue.

## Alternatives

### Folding Offline

It is possible to conceptualise both `"busy"` and `"offline"` as unreachable, and ignoring the potential for a user to
transition from `"offline"` to `"active"` following a notification, they can be considered to be the same state. It
would be viable, in this case, to create a three-state traffic light system that parallels the existing model by
renaming `"offline"` to `"busy"` after its reachability. This proposal includes both an `"offline"` and a `"busy"` state
for the social utility of deciding whether or not it is worth contacting someone at a given moment. For example, if you
want to play a game with someone, you may still invite them if they're `"offline"` on the basis that they might see the
push notification and become `"active"` to respond to you, while you may not invite them if they're `"busy"` on the
basis that you know you will not be getting a reply.

### [MSC4043]'s Override Endpoint

[MSC4043]'s endpoint was not chosen for the purposes of this proposal primarily for user experience. Using account data
allows your other clients to be aware of the override you have set, which also means you can safely edit your overrides
from other clients, instead of potentially having to lock other clients out of the endpoint until the original
explicitly releases its override.

### Status Separation

While status information could be decoupled from presence entirely, living either in profile fields or getting their own
EDUs, this proposal keeps statuses bundled with presence states because of their equivalent information models. Both
statuses and presence states are near-term information about a user's state of being, while profiles should convey a
user's identity, and adding a new EDU would further bloat the federation, so this proposal does not consider either
approach to be suitable. Including status information in the persistence mechanism was also [explicitly requested in a
review on MSC4043][MSC4043-status].

### Overriding Offline

Some platforms allow overrides to persist through being determined offline by the server. This proposal decided against
doing this to prevent people from having to manually set themselves as offline before they disconnect, and to avoid
eroding the social use of the system by having people appear reachable when the network cannot be certain.

### Last Active Ago

#### Declaration by Sending Clients

Some other decentralised platforms, like XMPP (defined by [XEP-0319]), allow clients to send their own "Last Active Ago"
values. However, determining your own last active time for other people carries a number of drawbacks:
* It makes the information completely untrusted, eliminating the social utility of the feature
* It creates opportunities for broken behaviour, like someone appearing to be active while they were supposedly last
  seen in 1995
* The time someone was last seen is information inherent to the observer; it makes no sense for anyone but the observer
  to determine when they last saw someone as active

Therefore, this proposal does not allow clients to set and send their own "Last Active Ago" values. Similarly, this
proposal does not allow clients to request that other users do not see their "Last Active Ago" values because the
information is inherent to presence, so if a user did not trust someone to see their "Last Active Ago," they would not
be sharing presence with them.

#### Calculation by Receiving Clients

Instead of having the homeserver tell the client when a remote user was last active based on their state transitions,
the client could determine this information themselves. This approach was not taken to allow consistency for clients
that are not always connected.

### Remote Offlines

One possible alternative to the algorithm given by this proposal would be to drop state data for remote users after a
timeout. This approach was not chosen to avoid making every presence-sending server rebroadcast their presence states on
an interval, akin to a heartbeat system, which would harm our stated aim of reducing federation traffic.

## Security Considerations

### Status

The status message field may be abused, both technically as it is unbounded, and socially as it allows users to send
free-form data. It should be noted that these apply to the existing presence system.

### State Flapping

Users may rapidly change presence states to exhaust resources on remote servers. This flaw exists in the current
presence system, and this proposal mitigates the issue by reducing the number of ways user activity triggers presence
updates, formalising collation in [State Determination] to reduce the power of individual clients, and suggesting that
servers debounce outbound presence state transitions. Malicious servers are always capable of sending large volumes of
any traffic to other servers, so noncompliance is beyond the scope of this section.

This proposal includes provisions for offline timeouts on remote users, which may be leveraged to cause remote servers
to keep track of large volumes of temporarily overriden states, or to sync large volumes of state transitions to their
users. It is precisely to mitigate this new kind of flapping that this proposal suggests debouncing the trigger
condition for marking remote users offline.

### Activity Tracking

Last active ago remains a tracking vector for user behaviours, although this proposal limits it to information already
available by tracking a user's presence state transitions.

## Unstable Prefix

| Stable Identifier        | Purpose                                                                           | Unstable Identifier                                         |
| ------------------------ | --------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `active`                 | [User Presence Update] `presence` value for a user that is online and active      | `org.continuwuity.presence_v2.msc4532.active`               |
| `idle`                   | [User Presence Update] `presence` value for a user that is online and inactive    | `org.continuwuity.presence_v2.msc4532.idle`                 |
| `busy`                   | [User Presence Update] `presence` value for a user that is online and unreachable | `org.continuwuity.presence_v2.msc4532.busy`                 |
| `status`                 | [User Presence Update] extensible object for conveying status information         | `org.continuwuity.presence_v2.msc4532.status`               |
| `m.presence.persistent`  | Account data event for allowing clients to set a persistent global presence state | `org.continuwuity.presence_v2.msc4532.presence.persistent`  |


Servers may advertise support for Revised Social Presence by listing `org.continuwuity.presence_v2.msc4532` in the
`unstable_features` section of the response to [`GET /_matrix/client/versions`][cs-versions].

Once this proposal completes FCP, servers may advertise support for the stable identifiers by listing
`org.continuwuity.presence_v2.msc4532.stable` in `unstable_features`; clients may use this while they are waiting for
the server to adopt a version of the spec that includes it.

[^1]: See [MSC4426], which proposes an extension to the presence status feature without extending presence at all,
      instead using profiles for storing intrinsically ephemeral data. This is also [acknowledged in the MSC
      itself](https://github.com/matrix-org/matrix-spec-proposals/pull/4426#discussion_r2858697464).

[matrix-react-sdk#1676]: https://github.com/matrix-org/matrix-react-sdk/pull/1676#issuecomment-353897256
[MSC3026]: https://github.com/matrix-org/matrix-spec-proposals/pull/3026
[MSC4043]: https://github.com/matrix-org/matrix-spec-proposals/pull/4043
[MSC4043-status]: https://github.com/matrix-org/matrix-spec-proposals/pull/4043#discussion_r1299165337
[MSC4426]: https://github.com/matrix-org/matrix-spec-proposals/pull/4426
[MSC4495]: https://github.com/matrix-org/matrix-spec-proposals/pull/4495
[Presence States]: #Presence-States
[State Determination]: #State-Determination
[Presence Overrides]: #Presence-Overrides
[Extensible Status]: #Extensible-Status
[Simplified Activity]: #Simplified-Activity
[User Presence Update]: https://spec.matrix.org/v1.19/server-server-api/#definition-mpresence_user-presence-update
[`m.presence` Sync Event]: https://spec.matrix.org/v1.19/client-server-api/#mpresence
[Presence Client-Server Endpoints]: https://spec.matrix.org/v1.19/client-server-api/#client-behaviour-8
[Account Data]: https://spec.matrix.org/v1.19/client-server-api/#client-config
[Idle Timeouts]: https://spec.matrix.org/v1.19/client-server-api/#idle-timeout
[Application Service API]: https://spec.matrix.org/v1.19/application-service-api
[Presence module]: https://spec.matrix.org/v1.19/client-server-api/#presence
[Presence section]: https://spec.matrix.org/v1.19/server-server-api/#presence
[`GET /_matrix/client/v3/presence/{userId}/status`]: https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3presenceuseridstatus
[`PUT /_matrix/client/v3/presence/{userId}/status`]: https://spec.matrix.org/v1.19/client-server-api/#put_matrixclientv3presenceuseridstatus
[`GET /_matrix/client/v3/sync`]: https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3sync
[cs-versions]: https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientversions
[XEP-0319]: https://xmpp.org/extensions/xep-0319.html
