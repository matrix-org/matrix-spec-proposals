# MSC4570: Remote Network Targeting Policies

This MSC introduces the `remote_network` and `remote_id` fields as optional keys for membership events.
This allows policies to target bridged users without relying on globs, while still allowing those
policies to be shared across bridges.

The exact shape of `remote_network` and `remote_id` is intentionally left loose in order to accommodate
past, current, and future bridges. This avoids requiring the spec to maintain a bridge directory or
otherwise prescribe a single canonical layout for all networks.

This is achieved by having policies match the `remote_network` and `remote_id` values supplied by the
bridge. This works on the assumption that, provided the bridge supplies trustworthy data, exact matching
is sufficient for policy application.

The policy side of this proposal is achieved by extending the current `m.policy.rule.user` policy with
`remote_network` and `remote_id` fields, mirroring the membership event shape that is being proposed.

## Proposal

`remote_network` takes the form of a string that identifies the remote side of the bridge. This proposal
does not specify strict rules for how remote networks should be identified, beyond following the Matrix
namespace rules. Typically however, bridge maintainers will use the primary domain of the network for
this identifier.

An example shape for identifying a centralized network such as Telegram is `org.telegram`. This follows
the standard Matrix naming conventions. The proposal intentionally leaves this loosely defined so that
bridges can choose a namespace scheme appropriate to the network they bridge.

`remote_id` is defined as the remote network's immutable identifier for that user. Examples include
Discord snowflakes and equivalent identifiers from other networks. For Matrix users, the equivalent would
be the MXID. The purpose of `remote_id` is to give policies an immutable identifier to target on the
remote network.

A `m.policy.rule.user` policy that contains a ban targeting one of these remote users can look like this.

```json
{
  "content": {
    "entity": "@example_bridge_example_1420070400000:example.com",
    "reason": "example",
    "recommendation": "m.ban",
    "remote_network": "com.discord",
    "remote_id": "1420070400000",
  },
  "origin_server_ts": 1420070400000,
  "sender": "@example_bot:example.com",
  "state_key": "3KQYRDed/WMEod8n6vjheIgNk/+hsW4qq7WjJg1pQAM=",
  "type": "m.policy.rule.user",
  "event_id": "$example",
  "room_id": "!example"
}
```

For bridges that do not implement this proposal, the example event targets the user in the `entity` field.

_Note: The example snowflake is actually the Unix timestamp of the Discord epoch and is used here only as a
placeholder._

For bridges compatible with this proposal, the policy instead targets any user whose membership event contains
a matching set of `remote_network` and `remote_id` fields.

When writing a policy that targets a user with `remote_network` and `remote_id`, implementations must
ensure that the supplied data is trustworthy to avoid banning innocent users. How a user is determined to
belong to a trusted namespace is left as an implementation detail.

In drafting this proposal a recommendation around bridge metadata tracked via state event was mentioned and
future work in this area is welcome to explore that avenue as a way to establish trust in a given namespace.

## Potential issues

### Inconsistent ´remote_network´ identifier

Bridges could use inconsistent `remote_network` identifiers for the same service.
For example, two distinct telegram bridges could use `org.telegram` and `im.telegram`.
Additionally a bridged network could be renamed or rebranded, for example `com.hotmail` and `com.outlook`.
To allievate this issue we propose the following solutions for further exploration in other proposals:

- Maintainers of policy consumers could collect the known inconsistencies and merge them together at ingress e.g. .

- A remote network registry containing all well-known names for the same remote network.
Including renames for a given remote network.

### Networks lacking immutable identifiers

This proposal also does not work well with networks that do not have a true immutable identifier, including
networks that allow account migration. That limitation is accepted as its not a problem for matrix to solve,
in this MSC and most commonly bridged networks do provide immutable identifiers.

## Alternatives

This metadata could be tracked via extensible profile data as in [MSC4503](https://github.com/matrix-org/matrix-spec-proposals/pull/4503),
but that approach was set aside during the initial design because it would add cost to policy application.
For this metadata to be useful, it needs to be available without additional lookup overhead.

## Security considerations

The primary security consideration introduced by this MSC is that implementations must trust the bridges
that provide the metadata and originate users.

Implementations must take care to not trust this data for invites as in the case of invites the data is able to be 
set on behalf of another user. If the sender of the membership event does not match the subject of the event its
exposed to this flaw.

Anyone can set these fields to arbitrary values, but as long as policy authors do not trust unverified data,
the harm is limited. This proposal is intended to be used with approved bridges that are trusted to supply
correct metadata. If a bridge provides incorrect values, incorrect policies may be written or applied depending on if
the bridge in question was trusted. That risk is accepted in return for the benefits of the approach.

## Unstable prefix

Before this proposal is stable the following prefix maps apply.

| Stable           | Unstable                                |
|------------------|-----------------------------------------|
| `remote_network` | `support.feline.msc4570.remote_network` |
| `remote_id`      | `support.feline.msc4570.remote_id`      |

## Dependencies

This proposal has no dependencies that are not part of the specification.
