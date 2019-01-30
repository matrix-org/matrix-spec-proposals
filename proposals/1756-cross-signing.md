# Cross-signing devices with device signing keys

## Background

A user with multiple devices will have a different key for end-to-end
encryption for each device.  Other users who want to communicate securely with
this user must then verify each key on each of their devices.  If Alice has *n*
devices, and Bob has *m* devices, then for Alice to be able to communicate with
Bob on any of their devices, this involves *n×m* key verifications.

One way to address this is for each user to use a device signing key to sign
all of their devices.  Thus another user who wishes to verify their identity
only needs to verify the device signing key and can use the signatures created
by the device signing key to verify their devices.

[MSC1680](https://github.com/matrix-org/matrix-doc/issues/1680) presents a
different solution to the problem.  A comparison between this proposal and
MSC1680 is presented below.

## Proposal

Each user has a self-signing key pair that is used to sign their own devices,
and a user-signing key pair that is used to sign other users' signing keys. A
user's user-signing key is also signed by their own self-signing key. When one
user (e.g. Alice) verifies another user's (Bob's) identity, Alice will sign
Bob's self-signing key with her user-signing key. (This will mean that
verification methods will need to be modified to pass along the self-signing
identity key.) Alice's device will trust Bob's device if:

- Alice's device is using a self-signing key that has signed her user-signing key,
- Alice's user-signing key has signed Bob's self-signing key, and
- Bob's self-signing key has signed Bob's device key.

### Key security

A user's private half of their user-signing key pair may be kept unlocked on a
device, but their self-signing key should not; the private half of the
self-signing key pair should only be stored encrypted, requiring a passphrase
to access. By keeping the user-signing key unlocked, Alice can verify Bob's
identity and distribute signatures to all her devices without needing to enter
a passphrase to decrypt the key.

If a user's device is compromised, they can issue a new user-signing key,
signed by their self-signing key, rendering the old user-signing key useless.
If they are certain that the old user-signing key has not yet been used by an
attacker, then they may also reissue signatures made by the old user-signing
key by using the new user-signing key. Otherwise, they will need to re-verify
the other users.

If a user's self-signing key is compromised, then the user will need to issue
both a new self-signing key and a new device-signing key. The user may sign
their new self-signing key with their old self-signing key, allowing other
users who have verified the old self-signing key to automatically trust the new
self-signing key if they wish to. Otherwise, the users will need to re-verify
each other.

The private halves of the user-signing key pair and self-signing key pair may
be stored encrypted on the server (possibly along with the megolm key backup)
so that they may be retrieved by new devices. FIXME: explain how to do this

### Signature distribution

Currently, users will only be allowed to see signatures made by their own
self-signing or user-signing keys, or signatures made by other users'
self-signing keys about their own devices.  This is done in order to preserve
the privacy of social connections.  Future proposals may define mechanisms for
distributing signatures to other users in order to allow for other web-of-trust
use cases.

### API description

Public keys for the self-signing and user-signing keys are uploaded to the
servers using `/keys/device_signing/upload`.  This endpoint requires [UI
Auth](https://matrix.org/docs/spec/client_server/r0.4.0.html#user-interactive-authentication-api).

`POST /keys/device_signing/upload`

``` json
{
  "self_signing_key": {
    "user_id": "@alice:example.com",
    "usage": ["self_signing"],
    "keys": {
      "ed25519:base64+self+signing+public+key": "base64+self+signing+public+key",
    }
  },
  "user_signing_key": {
    "user_id": "@alice:example.com",
    "keys": {
      "ed25519:base64+device+signing+public+key": "base64+device+signing+public+key",
    },
    "usage": ["user_signing"],
    "signatures": {
      "@alice:example.com": {
        "ed25519:base64+self+signing+public+key": "base64+signature"
      }
    }
  }
}
```

In order to ensure that there will be no collisions in the `signatures`
property, the server must respond with an error (FIXME: what error?) if any of
the uploaded public keys match an existing device ID for the user.  Similarly,
if a user attempts to log in specifying a device ID matching one of the signing
keys, the server must respond with an error (FIXME: what error?).

If a user-signing key is uploaded, it must be signed by the current
self-signing key (or the self-signing key that is included in the request)

If a previous self-signing key exists, then the new self-signing key must have
a `replaces` property whose value is the previous public self-signing key.
Otherwise the server must respond with an error (FIXME: what error?).  The new
self-signing key may also be signed with the old self-signing key.

FIXME: document `usage` property

After uploading self-signing and user-signing keys, they will be included under
the `/keys/query` endpoint under the `self_signing_key` and `user_signing_key`
properties, respectively.  The `user_signing_key` will only be included when a
user requests their own keys.

`POST /keys/query`

``` json
{
   "device_keys": {
      "@alice:example.com": []
   },
   "token": "string"
}
```

response:

``` json
{
  "failures": {},
  "device_keys": {
    "@alice:example.com": {
      // ...
    }
  },
  "self_signing_keys": {
    "@alice:example.com": {
      "user_id": "@alice:example.com",
      "usage": ["self_signing"],
      "keys": {
        "ed25519:base64+self+signing+public+key": "base64+self+signing+public+key"
      }
    }
  }
}
```

After uploading self-signing and user-signing keys, the user will show up in
the `changed` property of the `device_lists` field of the sync result of any
others users who share an encrypted room with that user.

Signatures of keys can be uploaded using `/keys/signatures/upload`.

For example, Alice signs one of her devices (HIJKLMN), and Bob's self-signing key.

`POST /keys/signatures/upload`

``` json
{
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
          "ed25519:base64+user+signing+public+key": "base64+signature+of+HIJKLMN"
        }
      }
    }
  },
  "@bob:example.com": {
    "bobs+base64+self+signing+public+key": {
      "user_id": "@bob:example.com",
      "keys": {
        "ed25519:bobs+base64+self+signing+public+key": "bobs+base64+self+signing+public+key"
      },
      "usage": ["self_signing"],
      "signatures": {
        "@alice:example.com": {
          "ed25519:base64+user+signing+public+key": "base64+signature+of+bobs+self+signing+key"
        }
      }
    }
  }
}
```

After Alice uploads a signature for her own devices, her signature will be
included in the results of the `/keys/query` request when *anyone* requests her
keys:

`POST /keys/query`

``` json
{
   "device_keys": {
      "@alice:example.com": []
   },
   "token": "string"
}
```

response:

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
            "ed25519:base64+user+signing+public+key": "base64+signature+of+HIJKLMN"
          }
        },
        "unsigned": {
          "device_display_name": "Alice's Osborne 2"
        }
      }
    }
  },
  "self_signing_keys": {
    "@alice:example.com": {
      "user_id": "@alice:example.com",
      "usage": ["self_signing"],
      "keys": {
        "ed25519:base64+self+signing+public+key": "base64+self+signing+public+key",
      }
    }
  }
}
```

After Alice uploads a signature for Bob's user-signing key, her signature will
be included in the results of the `/keys/query` request when Alice requests
Bob's key:

`GET /keys/query`

``` json
{
  "failures": {},
  "device_keys": {
    "@bob:example.com": {
      // ...
    }
  },
  "self_signing_keys": {
    "@bob:example.com": {
      "user_id": "@bob:example.com",
      "keys": {
        "ed25519:bobs+base64+self+signing+public+key": "bobs+base64+self+signing+public+key"
      },
      "usage": ["self_signing"],
      "signatures": {
        "@alice:example.com": {
          "ed25519:base64+user+signing+public+key": "base64+signature+of+bobs+self+signing+key"
        }
      }
    }
  }
}
```

FIXME: s2s stuff

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
contrast, in this proposal, Alice and Bob sign each other's self-signing key
with their user-signing keys, and the attestation graph would look like:

![](images/1756-graph2.dot.png)

In this case, Bob's Dynabook can be replaced without breaking the graph.

With normal cross-signing, it is not clear how to recover from a stolen device.
For example, if Mallory steals one of Alice's devices and revokes Alice's other
devices, it is unclear how Alice can rebuild the attestation graph with her
devices, as there may be stale attestations and revocations lingering around.
(This also relates to the question of whether a revocation should only revoke
the signature created previously by the device making the attestation, or
whether it should be a statement that the device should not be trusted at all.)
In contrast, with this proposal, if a device is stolen, then only the
user-signing key must be re-issued.

## Security considerations

This proposal relies on servers to communicate when self-signing or
user-signing keys are deleted and replaced.  An attacker who is able to both
steal a user's device and control their homeserver could prevent that device
from being marked as untrusted.

## Conclusion

This proposal presents an alternative cross-signing mechanism to MSC1680.
