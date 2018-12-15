# Background

FIXME: something something

# Proposal

Each user has a "master identity key" that is used to sign their devices, and
is signed by all of their devices.  When one user (Alice) verifies another
user's (Bob's) identity, Alice will sign Bob's master identity key with her
master identity key.  (This will mean that verification methods will need to be
modified to pass along the master identity key.)  Alice's device will trust
Bob's device if:

- Alice's device has signed her master identity key,
- her master identity key has signed Bob's master identity key,
- Bob's master identity key has signed Bob's device, and
- none of those signatures have been revoked.

If Alice believes that her master identity key has been compromised, she can
revoke it and create a new one.  This means that all trust involving Alice
(i.e. Alice trusting other people and other people trusting Alice) needs to
start from scratch.

The master identity key's private key can be stored encrypted on the server
(possibly along with the megolm key backup).  Clients may or may not want to
store a copy of the private key locally.  Doing so would mean that an attacker
who steals a device has access to the private key, and so can forge trusted
devices until the user notices and resets their master key.  However, not doing
so means that when the user verifies another user, they will need to re-fetch
the private key, which means that they will need to re-enter their recovery
key to decrypt it.

When a user logs in with a new device, they will fetch and decrypt the private
master key, sign the new device's key with the master key, and sign the master
key with the device's key.

Users will only be allowed to see signatures made by their own master identity
key, or signatures made by other users' master identity keys on their own
devices.

# API description

## Possible API 1

Use the same API as MSC1680, but with additions.

API to create new virtual device:

`POST /devices/create`

returns

``` javascript
{
  "device_id": "ABCDEFG"
}
```

Send public key using `/keys/upload` as a normal device, but with a special
"algorithms" list:

`POST /keys/upload`

``` javascript
{
  "device_keys": {
    "user_id": "@alice:example.com",
    "device_id": "ABCDEFG",
    "algorithms": ["m.master"],
    "keys": {
      "ed25519:ABCDEFG": "base64+public+key"
    },
    "signatures": {
      "@alice:example.com": {
        "ed25519:ABCDEFG": "base64+self+signature"
      }
    }
  }
}
```

(This may require changes in what `device_id`s are accepted by `/keys/upload`.)

Attestations/revocations will be uploaded and retrieved as described in
MSC1680.  Creating a new master key would involve revoking the old master key
by sending a signed revocation and deleting the device using `DELETE
/devices/{deviceId}`, and then creating a new master key.

Private master key could be stored as part of the key backup (MSC1219), maybe
as a special room ID + session ID, or possibly in the `auth_data` for the
backup version (the latter would mean that changing the master key would
require creating a new backup version, which may be what users need to do
anyways).  Or the private master key could be stored in account data,
e.g. `/user/{userId}/account_data/m.master.{deviceId}`.

## Possible API 2

Treat master key separately from normal devices and adding special handling for
them.  This might result in a nicer API, but make the implementation more
complicated.  For example, the server could automatically add master key
signatures into a device's `signatures` field, rather than shipping the
attestations separately.

TODO: write this option out

# Comparison with MSC1680

MSC1680 suffers from the fact that the attestation graph may be arbitrarily
complex and may become ambiguous how the graph should be interpreted.  In
particular, it is not obvious exactly how revocations should be interpreted --
should they be interpreted as only revoking the signature created previously by
the device making the revocation, or should it be interpreted as a statement
that the device should not be trusted at all?  As well, a revocation may split
the attestation graph, causing devices that were previously trusted to possibly
become untrusted.  Logging out a device may also split the attestation graph.
Moreover, it may not be clear to a user what device verifications would be
needed to reattach the parts of the graph.

One way to solve this is by registering a "virtual device", which is used to
sign other devices.  This solution would be similar to this proposal.  However,
real devices would still form an integral part of the attestation graph.  For
example, if Alice's Osborne 2 verifies Bob's Dynabook, the attestation graph might
look like:

![](images/1756-graph1.dot.png)

If Bob replaces his Dynabook without re-verifying with Alice, this will split
the graph and Alice will not be able to verify Bob's other devices.  In
contrast, in this proposal, Alice and Bob's master keys directly sign each
other, and the attestation graph would look like:

![](images/1756-graph2.dot.png)

In this case, Bob's Dynabook can be replaced without breaking the graph.

With normal cross-signing, it is not clear how to recover from a stolen device.
For example, if Mallory steals one of Alice's devices and revokes Alice's other
devices, it is unclear how Alice can rebuild the attestation graph with her
devices, as there may be stale attestations and revocations lingering around.
(This also relates to the question of whether a revocation should only revoke
the signature created previously by the device making the attestation, or
whether it should be a statement that the device should not be trusted at all.)
In contrast, with this proposal, there is a clear way to rebuild the
attestation graph: create a new master identity key, and re-verify all devices
with it.

# Conclusion

This proposal presents an alternative cross-signing mechanism to MSC1680.
