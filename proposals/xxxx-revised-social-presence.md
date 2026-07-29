# MSCXXXX: Revised Social Presence

Presence and its features have remained largely untouched since its inception. Performance issues have deterred users and operators alike from presence to the point that extensions of its features are now being proposed within completely different systems[^1]. Further to this, many have expressed concerns over the excessive information it provides, particularly the current "Last Active Ago" system revealing when somene last interacted with the network down to the second, and the confusing behaviour of someone being marked online without being active or idle.

While the companion to this MSC, [MSC4495: Selective Presence][MSC4495], improved performance and privacy by *restricting access to presence*, this proposal *reshapes presence itself*, simplifying its semantics, providing a single consistent mechanism for managing near-term persistence, and supporting future extensions, all while furthering those goals.

## Prior Art

In the early years of Matrix, [a discussion was held][matrix-react-sdk#1676] about the abandonment of the presence feature and ways it might be improved. Notably, a distinction was drawn between one's presence on Matrix and one's real status, although status was never fully split out of the presence endpoint, even in [MSC4426: User Status Profile Fields][MSC4426].

[MSC4043: Presence Override API][MSC4043] is the closest to introducing a solution to the issue of mixing data on different timescales, with [this remark][MSC4043-status] suggesting that statuses should be included in overrides, although it does not go as far as to move status away from setting per-client presence.

The picture of efforts to improve presence over time would be incomplete without [MSC3026: "busy" presence state][MSC3026], where a heavily desired busy state is first introduced. As this proposal was unfortunately abandoned, Revised Social Presence brings the busy state aboard with adjusted semantics to fit a new model for presence.

## Proposal

### Presence States

Ultimately, other users do not care about the technical particulars of your reachability, they care solely about the social qualities of your reachability itself. In practice, this means reframing presence from a connection state to a sense of availability, where we define the following states:
* `active`: fully reachable; available to reply
* `idle`: maybe-reachable; connected and may reply
* `busy`: fully unreachable; unavailable to reply
* `offline`: maybe-unreachable; disconnected and may not reply

This maps to the previous states as follows:

| Old `presence` | `currently_active` | New `presence` |
|----------------|--------------------|----------------|
| `online`       | `true`             | `active`       |
| `online`       | `false`            | `idle`         |
| `unavailable`  | *                  | `idle`         |
| `offline`      | *                  | `offline`      |

From this point onwards, these terms will be used instead of their existing counterparts except for where it is explicitly necessary to reference the existing model. The old values of **`"online"` and `"unavailable"` are deprecated** from the federation [User Presence Update] type, the [`m.presence` Sync Event], the [Presence Client-Server Endpoints], and [`GET /_matrix/client/v3/sync`] by this proposal. The new states `"active"`, `"idle"`, and `"busy"` are introduced to all of these mechanisms in their place.

#### Near-Term Persistent Data

Users may wish to set their presence state manually on occasion, particularly if they need to let others know they are temporarily unavailable. This proposal affords users the option to set a persistent override state across all of their clients, using the `m.presence.persist` account data event.

The new event contains two properties:
* An optional string enumeration, `presence_override`, which can be any of the previously defined states.
  * For its behaviour as part of resolving a user's final presence state, see [State Determination].
* An optional object, `status`, acting as a key-value store for status information and containing one property.
  * An optional string, `msg`, which is a free-form input corresponding with the existing `status_msg` property.
    * For its behaviour in relation to the federation [User Presence Update] status fields, see [Extensible Status].

Clients MUST NOT modify these properties unless explicitly directed to by a user. Clients and servers MUST ignore states in `presence_override` that they do not recognise, acting as they were unset, rather than clearing it automatically. Clients MUST manage near-term persistent data via this account data to ensure they have a single source of truth for this information, rather than managing it with endpoints.

Example `m.presence.persist` event:
```json
{
    "presence_override": "busy",
    "status": {
        "msg": "Partying like it's 2023!"
    }
}
```

#### State Determination

A user's final presence state is determined by their local server according to the first rule that applies below:

1. If all clients are offline, the state is `offline`
2. If `presence_override` in `m.presence.persist` is set, the state is the override
3. If any client sets a `"busy"` state, the state is `"busy"`
4. If any client sets an `"active"` state, the state is `active`
5. The state is `idle`

This uses the following ownership model:
* Clients determine their presence state
* Users may direct clients to set a specific shared persistent override
* Servers can determine if a client is offline on its behalf

Since clients are expected to determine when their users are idle, and servers only determine when clients are offline, [Idle Timeouts] are replaced with offline timeouts. That is, servers may determine a client is offline after a threshold value of time \- for example, 5 minutes \- has passed since the client's most recent request to [`GET /_matrix/client/v3/sync`] completed.

In the case of Application Services, servers actively make requests to them via the [Application Service API]. Practically, this means Application Services can be reliably determined to be offline without servers timing them out based on inactivity. In order to prevent Application Services from having to update presence for all of their namespaced users on a given interval, servers MUST NOT offline an Application Service's namespaced users unless requests to the Application Service fail.

#### Busy State

While `"active"` and `"idle"` map cleanly from existing states encoded by the presence system, `"busy"` is a [long-requested][MSC3026] feature representing a  connected user's voluntary declaration that they will not be reachable for other users that wish to solicit conversation. A `"busy"` user is unique in that this state is exclusively triggered by a curated set of user actions, rather than connection properties or general activity.

If a `"busy"` state is manually selected by a user, it SHOULD always be set via [Near-Term Persistent Data] to prevent autonomous regression to other states, as with other overrides. If a client wishes to set a `"busy"` state autonomously following a select user action \- for example, if the user joins a call \- it SHOULD do so via the [`GET /_matrix/client/v3/sync`] endpoint or the [Presence Client-Server Endpoints], as with other states. It is by design that the latter case does not override the overrides mechanism to prevent clients from interfering with each other's automated actions and being unsure which state to return the override to.

### Simplified Activity

You may observe that none of the new [Presence States] require the `currently_active` marker, since holding the existing `"online"` state without being `currently_active` is considered to be idle, and the only state where `currently_active` applies is `"active"`. You may also observe that the `last_active_ago` federation [User Presence Update] property can be redefined using a user's last state transition from `"active"` to any other state, which is also known to the receiving server. Given these redundancies:
* Both `currently_active` and `last_active_ago` are deprecated from the [User Presence Update] type
* `currently_active` is also deprecated from the [`m.presence` Sync Event] and [`GET /_matrix/client/v3/presence/{userId}/status`] endpoint

`last_active_ago` in the [`m.presence` Sync Event] and [`GET /_matrix/client/v3/presence/{userId}/status`] is redefined as the number of milliseconds since a user's `presence` last updated from `"active"` to any other state, based on when the user's server received the transitioning EDU. Clients SHOULD ignore this property altogether while a user is `"active"`.

For backwards compatibility:
- Servers implementing this proposal SHOULD ignore all incoming [User Presence Update] `last_active_ago` values and derive their own according
- Clients and servers SHOULD apply the behaviour map given in [Presence States] if they receive an old presence state or a `true` `currently_active` value

### Extensible Status

The `status_msg` property of the federation [User Presence Update] type and [`GET /_matrix/client/v3/presence/{userId}/status`] is **deprecated**, to be replaced with an extensible `status` object with a single string property `msg`  for any future expanding status needs, as desired in proposals like [MSC4426]. Whenever this is broadcasted or requested, servers MUST use current value of the corresponding property in `m.presence.persist`. For backwards compatibility, servers and clients implementing this proposal SHOULD process `status_msg` in lieu of the EDU property and endpoint response property respectively.

The same applies to the [`m.presence` Sync Event], where clients implementing this proposal should accept `status_msg` in lieu of the `status` property.

The `status_msg` request body property of the [`PUT /_matrix/client/v3/presence/{userId}/status`] endpoint is **deprecated** altogether. Clients that wish to manage [Near-Term Persistent Data], like overrides and statuses, MUST do so via the `m.presence.persist` account data to ensure the data is consistent across all a user's clients. It should be noted that this deprecation also means [`PUT /_matrix/client/v3/presence/{userId}/status`] is no longer useful to clients that call [`GET /_matrix/client/v3/sync`].

## Alternatives

### Folding Offline

It is possible to conceptualise both `"busy"` and `"offline"` as unreachable, and ignoring the potential for a user to transition from `"offline"` to `"active"` following a notification, they can be considered to be the same state. It would be viable, in this case, to create a three-state traffic light system that parallels the existing model by renaming `"offline"` to `"busy"` after its reachability. This proposal includes both an `"offline"` and a `"busy"` state for the social utility of deciding whether or not it is worth contacting someone at a given moment. For example, if you want to play a game with someone, you may still invite them if they're `"offline"` on the basis that they might see the push notification and become `"active"` to respond to you, while you may not invite them if they're `"busy"` on the basis that you know you will not be getting a reply.

### [MSC4043]'s Override Endpoint

[MSC4043]'s endpoint was not chosen for the purposes of this proposal primarily for user experience. Using account data allows your other clients to be aware of the override you have set, which also means you can safely edit your overrides from other clients, instead of potentially having to lock other clients out of the endpoint until the original explicitly releases its override.

### Status Separation

While status information could be decoupled from presence entirely, living either in profile fields or getting their own EDUs, this proposal keeps statuses bundled with presence states because of their equivalent information models. Both statuses and presence states are near-term information about a user's state of being, while profiles should convey a user's identity, and adding a new EDU would further bloat the federation, so this proposal does not consider either approach to be suitable. Including status information in the persistence mechanism was also [explicitly requested in a review on MSC4043](https://github.com/matrix-org/matrix-spec-proposals/pull/4043#discussion_r1299165337).

### Overriding Offline

Some platforms allow overrides to persist through being determined offline by the server. This proposal decided against doing this to prevent people from having to manually set themselves as offline before they disconnect, and to avoid eroding the social use of the system by having people appear reachable when the network cannot be certain.

### Declaring Last Active Ago

Some other decentralised platforms, like XMPP (defined by [XEP-0319]), allow clients to send their own "Last Active Ago" values. However, determining your own last active time for other people carries a number of drawbacks:
* It makes the information completely untrusted, eliminating the social utility of the feature
* It creates opportunities for broken behaviour, like someone appearing to be active while they were supposedly last seen in 1995
* The time someone was last seen is information inherent to the observer; it makes no sense for anyone but the observer to determine when they last saw someone as active

Therefore, this proposal does not allow clients to set and send their own "Last Active Ago" values. Similarly, this proposal does not allow clients to request that other users do not see their "Last Active Ago" values because the information is inherent to presence, so if a user did not trust someone to see their "Last Active Ago," they would not be sharing presence with them.

## Unstable Prefix

| Stable Identifier     | Purpose                                                                           | Unstable Identifier                                      |
| --------------------- | --------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `active`              | [User Presence Update] `presence` value for a user that is online and active      | `org.continuwuity.presence_v2.mscXXXX.active`            |
| `idle`                | [User Presence Update] `presence` value for a user that is online and inactive    | `org.continuwuity.presence_v2.mscXXXX.idle`              |
| `busy`                | [User Presence Update] `presence` value for a user that is online and unreachable | `org.continuwuity.presence_v2.mscXXXX.busy`              |
| `status`              | [User Presence Update] extensible object for conveying status information         | `org.continuwuity.presence_v2.mscXXXX.status`            |
| `m.presence.persist`  | Account data event for allowing clients to set a persistent global presence state | `org.continuwuity.presence_v2.mscXXXX.presence.persist`  |


Servers may advertise support for Revised Social Presence by listing `org.continuwuity.presence_v2.mscXXXX` in the `unstable_features` section of the response to [`GET /_matrix/client/versions`][cs-versions].

Once this proposal completes FCP, servers may advertise support for the stable identifiers by listing `org.continuwuity.presence_v2.mscXXXX.stable` in `unstable_features`; clients may use this while they are waiting for the server to adopt a version of the spec that includes it.

[^1]: See [MSC4426], which proposes an extension to the presence status feature without extending presence at all, instead using profiles for storing intrinsically ephemeral data. This is also [acknowledged in the MSC itself](https://github.com/matrix-org/matrix-spec-proposals/pull/4426#discussion_r2858697464).

[matrix-react-sdk#1676]: https://github.com/matrix-org/matrix-react-sdk/pull/1676#issuecomment-353897256
[MSC3026]: https://github.com/matrix-org/matrix-spec-proposals/pull/3026
[MSC4043]: https://github.com/matrix-org/matrix-spec-proposals/pull/4043
[MSC4043-status]: https://github.com/matrix-org/matrix-spec-proposals/pull/4043#discussion_r1299165337
[MSC4426]: https://github.com/matrix-org/matrix-spec-proposals/pull/4426
[MSC4495]: https://github.com/matrix-org/matrix-spec-proposals/pull/4495
[Presence States]: #Presence-States
[State Determination]: #State-Determination
[Near-Term Persistent Data]: #Near-Term-Persistent-Data
[Extensible Status]: #Extensible-Status
[User Presence Update]: https://spec.matrix.org/v1.19/server-server-api/#definition-mpresence_user-presence-update
[`m.presence` Sync Event]: https://spec.matrix.org/v1.19/client-server-api/#mpresence
[Presence Client-Server Endpoints]: https://spec.matrix.org/v1.19/client-server-api/#client-behaviour-8
[Idle Timeouts]: https://spec.matrix.org/v1.19/client-server-api/#idle-timeout
[Application Service API]: https://spec.matrix.org/v1.19/application-service-api
[`GET /_matrix/client/v3/presence/{userId}/status`]: https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3presenceuseridstatus
[`PUT /_matrix/client/v3/presence/{userId}/status`]: https://spec.matrix.org/v1.19/client-server-api/#put_matrixclientv3presenceuseridstatus
[`GET /_matrix/client/v3/sync`]: https://spec.matrix.org/v1.19/client-server-api/#get_matrixclientv3sync
[cs-versions]: https://spec.matrix.org/v1.18/client-server-api/#get_matrixclientversions
[XEP-0319]: https://xmpp.org/extensions/xep-0319.html
