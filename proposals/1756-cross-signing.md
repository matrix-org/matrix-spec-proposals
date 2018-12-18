# Cross-signing devices with master keys

## Background

A user with multiple devices will have a different key for end-to-end
encryption for each device.  Other users who want to communicate securely with
this user must then verify each key on each of their devices.  If Alice has *n*
devices, and Bob has *m* devices, then for Alice to be able to communicate with
Bob on any of their devices, this involves *n×m* key verifications.

One way to addresss this is for each user to use a "master key" for their
identity which signs all of their devices.  Thus another user who wishes to
verify their identity only needs to verify their master, key and can use the
master key to verify their devices.

[MSC1680](https://github.com/matrix-org/matrix-doc/issues/1680) presents a
different solution to the problem.

## Proposal

Each user has a "master identity key" that is used to sign their devices, and
is signed by all of their devices.  When one user (Alice) verifies another
user's (Bob's) identity, Alice will sign Bob's master identity key with her
master identity key.  (This will mean that verification methods will need to be
modified to pass along the master identity key.)  Alice's device will trust
Bob's device if:

- Alice's device is using a master identity key that has signed Bob's master
  identity key,
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

### API description

#### Possible API 1

Use the same API as MSC1680, but with additions.

API to create new virtual device:

`POST /devices/create`

returns

``` json
{
  "device_id": "ABCDEFG"
}
```

The server should not allow any client to use this device ID when logging in or
registering; if a client tries to log in using this device ID, then the server
must respond with an error. (FIXME: what error?)

Send public key using `/keys/upload` as a normal device, but with a special
"algorithms" list:

`POST /keys/upload`

``` json
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

#### Possible API 2

Treat master key separately from normal devices and adding special handling for
them.  This might result in a nicer API, but make the implementation more
complicated.  For example, the server could automatically add master key
signatures into a device's `signatures` field, rather than shipping the
attestations separately.

Send public key using `/keys/upload`, under the `master_key` property.
(Alternatively, could use a special endpoint, like `/keys/master/upload`.)

`POST /keys/upload`

``` json
{
  "master_key": {
    "user_id": "@alice:example.com",
    "key_id": "ABCDEFG",
    "algorithm": "ed25519",
    "key": "base64+public+key",
    "signatures": {
      "@alice:example.com": {
        "ed25519:ABCDEFG": "base64+self+signature"
      }
    }
  }
}
```

The key ID must be unique within the scope of a given user, and must not match
any device ID.  This is required so that there will be no collisions in the
`signatures` property.

(FIXME: how do we make sure that the key ID doesn't collide with an existing
device ID?  Just send an error and let the client retry?)

The server should not allow any client to use the key ID as their device ID
when logging in or registering; if a client tries to log in using this device
ID, then the server must respond with an error. (FIXME: what error?)

Uploading a new master key should invalidate any previous master key.

After uploading a master key, it will be included under the `/keys/query`
endpoint under the `master_key` property.

`GET /keys/query`

``` json
{
  "failures": {},
  "master_key": {
    "@alice:example.com": {
      "user_id": "@alice:example.com",
      "key_id": "ABCDEFG",
      "algorithm": "ed25519",
      "key": "base64+public+key",
      "signatures": {
        "@alice:example.com": {
          "ed25519:ABCDEFG": "base64+self+signature"
        }
      }
    }
  }
}
```

Signatures can be uploaded using `/keys/upload`, under the `signatures`
property.  (Alternatively, could use a special endpoint, like
`/keys/signatures/upload`.)

For example, Alice signs one of her devices (HIJKLMN), and Bob's master key.

`POST /keys/upload`

``` json
{
  "signatures": {
    "@alice:example.com": {
      "HIJKLMN": {
        "user_id": "@alice:example.com",
        "device_id": "HIJKLMN",
        "algorithms": [
          "m.olm.curve25519-aes-sha256",
          "m.megolm.v1.aes-sha"
        ],
        "keys": {
          "curve25519:HIJKLMN": "base64+curve25519+key",
          "ed25519:HIJKLMN": "base64+ed25519+key"
        },
        "signatures": {
          "@alice:example.com": {
            "ed25519:ABCDEFG": "base64+signature+of+HIJKLMN"
          }
        }
      }
    },
    "@bob:example.com": {
      "OPQRSTU": {
        "user_id": "@bob:example.com",
        "key_id": "OPQRSTU",
        "algorithm": "ed25519",
        "key": "base64+ed25519+key",
        "signatures": {
          "@alice:example.com": {
            "ed25519:ABCDEFG": "base64+signature+of+OPQRSTU"
          }
        }
      }
    }
  }
}
```

After Alice uploads a signature for her own devices, her signature will be
included in the results of the `/keys/query` request when *anyone* requests her
keys:

`GET /keys/query`

``` json
{
  "failures": {},
  "device_keys": {
    "@alice:example.com": {
      "HIJKLMN": {
        "user_id": "@alice:example.com",
        "device_id": "HIJKLMN",
        "algorithms": [
          "m.olm.v1.curve25519-aes-sha256",
          "m.megolm.v1.aes-sha"
        ],
        "keys": {
          "curve25519:HIJKLMN": "base64+curve25519+key",
          "ed25519:HIJKLMN": "base64+ed25519+key"
        },
        "signatures": {
          "@alice:example.com": {
            "ed25519:HIJKLMN": "base64+self+signature",
            "ed25519:ABCDEFG": "base64+signature+of+HIJKLMN"
          }
        },
        "unsigned": {
          "device_display_name": "Alice's Osborne 2"
        }
      }
    }
  },
  "master_keys": {
    "@alice:example.com": {
      "user_id": "@alice:example.com",
      "key_id": "ABCDEFG",
      "algorithm": "ed25519",
      "key": "base64+public+key",
      "signatures": {
        "@alice:example.com": {
          "ed25519:ABCDEFG": "base64+self+signature"
        }
      }
    }
  }
}
```

After Alice uploads a signature for Bob's master key, her signature will be
included in the results of the `/keys/query` request when Alice requests Bob's
key:

`GET /keys/query`

``` json
{
  "failures": {},
  "master_key": {
    "@bob:example.com": {
      "user_id": "@bob:example.com",
      "key_id": "OPQRSTU",
      "algorithm": "ed25519",
      "key": "base64+ed25519+key",
      "signatures": {
        "@alice:example.com": {
          "ed25519:OPQRSTU": "base64+self+signature+OPQRSTU",
          "ed25519:ABCDEFG": "base64+signature+of+OPQRSTU"
        }
      }
    }
  }
}
```

## Comparison with MSC1680

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

## Security considerations

## Conclusion

This proposal presents an alternative cross-signing mechanism to MSC1680.
