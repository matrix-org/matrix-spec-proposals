# MSC4503: External Protocol Handles

Bridges commonly represent a user from another network as a dedicated "ghost" Matrix user: a
persistent puppet account that sends messages on that user's behalf. That ghost user already has
somewhere to put the remote user's display name (`displayname`) and avatar (`avatar_url`), but no
standard place to put their actual handle on the network they came from, the identifier a human
would recognize and use to find them there, which is often not the same as either the display name or
the ghost's own Matrix ID.

[matrix-appservice-activitypub](https://github.com/Haven-Organization/matrix-appservice-activitypub), a
Matrix/ActivityPub (Fediverse) bridge, is a concrete case of this: a ghost user representing a remote
Fediverse actor already uses `displayname` for that actor's ActivityPub display name (which is
free-text and often not unique, e.g. multiple accounts named "Alice"), and its Matrix ID is an internal,
bridge-generated identifier, not the actor's real handle. There is currently nowhere standard to put
`@alice@mastodon.social`, the identifier that actually lets someone find or verify who this ghost
represents, so a client showing only `displayname` and the ghost's MXID gives a viewer no reliable way
to tell one Fediverse "Alice" from another, or to know they're looking at a bridged account at all.

This proposal defines a small, optional field, `m.external_handle`, usable both on a user's profile
(via [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133) Extensible Profiles) and
on an individual event, for showing that account's identifier on whatever external network it came
from.

- A new MSC4133 profile field, `m.external_handle`, for a ghost (or any bridged) user's current handle
  on the network they represent. Any user MAY also set it on their own profile, e.g. to publish a
  Fediverse handle they control, this proposal doesn't restrict the field to bridged accounts.
- The same field, reusable directly in an event's own content, as a point-in-time snapshot of the
  sender's handle at the time that specific event was sent, since a handle can change (e.g. Fediverse
  account migration) after the fact.
- A `protocol` sub-field identifying which network the handle belongs to, reusing the same `protocol`
  object shape [MSC2346](https://github.com/matrix-org/matrix-spec-proposals/pull/2346) (Bridge
  information state event) already defines at the room level (`id`, `displayname`, `avatar_url`), so a
  client can show an appropriate label and icon without this proposal inventing a second convention for
  the same thing.
- No new client-server or server-server API surface: the event-level field is a plain content key, and
  the profile-level field rides on MSC4133's already-defined profile field endpoints.

## Proposal

### The `m.external_handle` object

Both the profile field and the event content key use the same shape. Its fields:

**Mandatory**

- `handle`: a human-readable identifier for this account on the external network, formatted however is
  conventional there, e.g. `@alice@mastodon.social` for ActivityPub, `alice` for a network with flat
  usernames, `alice@irc.libera.chat` for IRC. This proposal does not mandate a specific syntax, since
  different networks have genuinely different native handle formats.

**Optional**

- `protocol`: an object identifying the external network, using the same shape as `protocol` in
  [MSC2346](https://github.com/matrix-org/matrix-spec-proposals/pull/2346)'s `m.bridge` state event.
  RECOMMENDED, so a client can show a protocol-appropriate label and icon rather than a bare string.
  - `id`: a short identifier, e.g. `activitypub`, `irc`, `xmpp`, `discord`. Mandatory within `protocol`,
    if `protocol` is present at all.
  - `displayname`: a human-readable name for the protocol, e.g. `Fediverse` for `activitypub`, since the
    protocol's technical name and the name people actually call it aren't always the same. Optional.
  - `avatar_url`: an `mxc://` URI for an icon representing the protocol, e.g. a Fediverse logo. Optional.
- `url`: a canonical profile URL for this account on the external network, e.g.
  `https://mastodon.social/@alice`. RECOMMENDED where one exists, so a client can make the handle
  clickable, the same way `content.external_url` already works for individual bridged events in the
  Application Service API.

### On a user's profile

*Example*: Setting `PUT /_matrix/client/v3/profile/{userId}/m.external_handle` with:

```json
{
  "m.external_handle": {
    "handle": "@alice@mastodon.social",
    "protocol": {
      "id": "activitypub",
      "displayname": "Fediverse",
      "avatar_url": "mxc://example.org/fediverse-logo"
    },
    "url": "https://mastodon.social/@alice"
  }
}
```

This is the natural place for a bridge to record a ghost user's handle once, the same way it already
records `displayname`/`avatar_url` once: it's a property of the account, not of any single message. A
client showing a member list, a DM composer, mention autocomplete, or a user info panel can source the
handle straight from the profile, without needing to find one of the user's messages first.

While a bridge recording a ghost user's handle is the motivating case, `m.external_handle` isn't limited
to bridged accounts. Since it's an ordinary MSC4133 profile field, any user can set it on their own
profile the same way they'd set `displayname` or `avatar_url`, for example to publish a Fediverse handle
they personally control, with no bridge involved at all.

### On an event

```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "Hello from the Fediverse!",
    "m.external_handle": {
      "handle": "@alice@mastodon.social",
      "protocol": {
        "id": "activitypub",
        "displayname": "Fediverse",
        "avatar_url": "mxc://example.org/fediverse-logo"
      },
      "url": "https://mastodon.social/@alice"
    }
  }
}
```

The event-level field is an optional snapshot, useful specifically because a handle isn't necessarily
permanent: Fediverse account migration is the motivating example, where a user moves to
`@alice@newserver.social` and their old handle becomes, at best, a redirect. A message sent while they
were still `@alice@mastodon.social` SHOULD keep showing that handle when looking back at it later, the
same way a repost or a forward embeds a snapshot of context that might not still be current by the time
someone views it, rather than silently relabeling old messages with whatever the account's current
handle happens to be.

When both are available, clients SHOULD prefer an event's own `m.external_handle`, if present, when
rendering that specific event, and fall back to the sender's profile field otherwise, or when there is
no specific event in view at all (a member list, for instance).

## Potential issues

- **The two copies are expected to drift, not kept in sync.** An event's `m.external_handle`, once
  sent, is a fixed historical snapshot; a profile's `m.external_handle` reflects whatever is current.
  Unlike some other proposals where drift between an embedded copy and a live source is an unwanted
  side effect, here it's the intended behavior (see On an event, above), but implementers should not
  assume the two will match, or treat a mismatch as an error.
- **No live-update signal for the profile-level field.** Per MSC4133, profile fields don't trigger any
  broadcast when changed; a client showing a ghost user's handle from their profile only has whatever
  was last fetched. This is rarely a practical problem for a value that changes as infrequently as an
  account handle, but is worth noting for completeness.
- **`protocol.id` is an open, uncontrolled identifier space, not a fixed enum.** This proposal does not
  define a registry of known protocol identifiers, the same as MSC2346 doesn't for its own `protocol.id`.
  A client that doesn't recognize a given `protocol.id` SHOULD still render `handle` (and `url`, if
  present) as a generic external identifier/link, falling back to `protocol.id` itself as a label when
  `protocol.displayname` is absent, rather than hiding the field entirely.

## Alternatives

- **Baking the handle into `displayname`** (e.g. `"Alice (@alice@mastodon.social)"`), the de facto
  convention several bridges already use in the absence of anything better. Rejected as the sole
  mechanism: it conflates two different pieces of information, a human display name and a stable
  protocol identifier, into one free-text field a client can't reliably parse back apart, and is
  actively awkward when `displayname` is already meaningfully used for something else, exactly
  matrix-appservice-activitypub's situation, where `displayname` already holds the actor's real
  ActivityPub display name.
- **Only a profile field, with no event-level snapshot.** Rejected: loses point-in-time accuracy for
  messages sent before a handle changes, e.g. Fediverse account migration (see On an event, above).
- **Only an event-level field, with no profile field.** Rejected: leaves no source for a handle in any
  context that isn't "looking at a specific message," such as a member list or DM composer, forcing a
  client to scan the timeline for one of the user's messages just to learn their handle.
- **Reusing MSC2346's `m.bridge` shape wholesale**, instead of a new field. Considered, but MSC2346 is
  explicitly a room-level state event describing what a *room* is bridged to (protocol/network/channel),
  not a per-user field describing what an *account* represents; this proposal only reuses its `protocol`
  object shape (`id`/`displayname`/`avatar_url`), for consistency between the two rather than introducing
  a second one, without pulling in the room-scoped `network`/`channel`/`bridgebot`/`creator` fields that
  don't apply here.
- **Mandating a specific handle syntax** (e.g. WebFinger-style `@user@domain` for every protocol).
  Rejected: different networks have genuinely different native handle formats (IRC, XMPP, ActivityPub,
  and others all differ), so `handle` is kept as an opaque, protocol-defined display string.

## Security considerations

- **`m.external_handle` is a self-asserted, unverified claim**, the same trust model as
  `displayname`/`avatar_url` today. Nothing in this proposal ties a `handle` to actual proof of control
  over the named account on the external network. For a bridge, this means the burden of not claiming a
  handle it hasn't actually verified (e.g. by resolving it via WebFinger, for ActivityPub) falls
  entirely on the bridge implementation; this proposal provides no protocol-level verification of its
  own, the same way it provides none for `displayname` either.
- **`url` can point anywhere.** As with `content.external_url` in the existing Application Service API,
  nothing validates that `url` actually corresponds to `handle`, or is safe to visit. Clients SHOULD
  treat it with the same caution as any other user-supplied or bridge-supplied link.
- **No new client-server or server-server API surface.** The event-level field is a plain content key;
  the profile-level field uses MSC4133's existing profile field endpoints. This proposal introduces no
  new endpoints and no attack surface beyond what those existing mechanisms already carry.

## Unstable prefix

Until this proposal is accepted into the spec, implementations should use the following identifier:

| Stable (once accepted) | Unstable (for now)                     |
| ------------------------ | ----------------------------------------- |
| `m.external_handle`      | `org.matrix.msc4503.external_handle`      |

As a profile field, `m.external_handle` additionally depends on whatever unstable identifier the
implementing homeserver uses for MSC4133 support itself (e.g. some deployments currently advertise
`uk.tcpip.msc4133`/`uk.tcpip.msc4133.stable` in `/_matrix/client/versions`), and, per MSC4133's own
unstable-prefix convention for fields in the `m.*` namespace, would need to be set as
`uk.tcpip.msc4133.org.matrix.msc4503.external_handle` until both proposals are stable. The event-level
use of `m.external_handle` has no such dependency and can use its own unstable prefix directly.

## Dependencies

The event-level use of `m.external_handle` has no dependencies; it is a plain content key on an
ordinary event.

The profile-level use of `m.external_handle` depends on
[MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133) (Extensible Profiles), which
has not been accepted into the spec at the time of writing. This dependency is not load-bearing for the
rest of this proposal: without MSC4133, the event-level field still works exactly as described; a
bridge simply has no way to publish a ghost user's handle independent of any specific message.
