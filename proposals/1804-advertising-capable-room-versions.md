# Proposal for advertising capable room versions to clients

Currently clients need to guess at which room versions the server supports, if any. This is particularly
difficult to do as it generally requires knowing the state of the ecosystem and what versions are
available and how keen users are to upgrade their servers and clients. The impossible judgement call
for when to encourage people to upgrade shouldn't be impossible, or even a judgement call.


## Proposal

Building off of [MSC1753](https://github.com/matrix-org/matrix-doc/pull/1753) (capabilities API) and
the [recommendations laid out for room versions](https://github.com/matrix-org/matrix-doc/pull/1773/files#diff-1436075794bb304492ca6953a6692cd0R463),
this proposal suggests a `m.room_versions` capability be introduced like the following:

```json
{
    "capabilities": {
        "m.room_versions": {
            "default": "1",
            "available": {
                "1": "stable",
                "2": "stable",
                "state-res-v2-test": "unstable",
                "event-ids-as-hashes": "unstable",
                "3": "future-scifi-label"
            }
        }
    }
}
```

Clients are encouraged to make use of this capability to determine if the server supports a given
version, and at what level of stability. Anything not flagged explicitly as `stable` should be treated
as `unstable` (ie: `future-scifi-label` is the same as `unstable`).

The default version is the version that the server is using to create new rooms with. Clients can
make the assumption that the default version is a stable version.

Clients should encourage people with sufficient permissions to perform an upgrade to upgrade their
rooms to the `default` room version when the room is using an `unstable` version.


## Potential issues

Changes aren't pushed to the client, which means clients may want to poll this endpoint on some
heuristic instead. For example, clients may want to poll the endpoint weekly or when the user relaunches
the client. Clients may also wish to provide users a way to upgrade without considering the capabilities
of the server, expecting that the server may not support the user-provided version - the intention
being such a feature would be used by eager room administrators which do not want to relaunch their
client, for example.
