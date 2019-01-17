# Proposal for advertising capable room versions to clients

Currently clients need to guess at which room versions the server supports, if any. This is particularly
difficult to do as it generally requires knowing the state of the ecosystem and what versions are
available and how keen users are to upgrade their servers and clients. The impossible judgement call
for when to prompt people to upgrade shouldn't be impossible, or even a judgement call.


## Proposal

Building off of [MSC1753](https://github.com/matrix-org/matrix-doc/pull/1753) (capabilities API) and
the [recommendations laid out for room versions](https://github.com/matrix-org/matrix-doc/pull/1773/files#diff-1436075794bb304492ca6953a6692cd0R463),
this proposal suggests a `m.room_versions` capability be introduced like the following:

```json
{
    "capabilities": {
        "m.room_versions": {
            "m.development": ["state-res-v2-test", "event-ids-as-hashes-test", "3"],
            "m.beta": ["2"],
            "m.default": "1",
            "m.recommended": "1",
            "m.mandatory": ["1"]
        }
    }
}
```

The labels picked (`m.development`, etc) are based upon the categories for different room versions.
Note that `m.default` and `m.recommended` reinforce that there is exactly 1 version in each category.

Clients are encouraged to make use of this capability to determine if the server supports a given
version, and at what state.

Clients should prompt people with sufficient permissions to perform an upgrade to upgrade their rooms
to the `m.recommended` room version.

Similarly, clients should prompt room administrators (or those with enough permission) to upgrade
their rooms where possible.


## Potential issues

Changes aren't pushed to the client, which means clients may want to poll this endpoint on some
heuristic instead. For example, clients may want to poll the endpoint weekly or when the user relaunches
the client. Clients may also wish to provide users a way to upgrade without considering the capabilities
of the server, expecting that the server may not support the user-provided version - the intention
being such a feature would be used by eager room administrators which do not want to relaunch their
client, for example.
