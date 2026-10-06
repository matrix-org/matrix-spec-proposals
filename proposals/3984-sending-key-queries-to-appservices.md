# MSC3984: Sending key queries to appservices

As mentioned in [MSC3983](https://github.com/matrix-org/matrix-spec-proposals/pull/3983), appservices
can save some data by accepting OTK claims directly, however they would still need to upload device
keys for their users. If an appservice wanted to be completely independent from the homeserver and
avoid uploading any keys, it would use this MSC to proxy the `/keys/query` endpoint alongside MSC3983.

*Note*: Readers are encouraged to read MSC3983 for background on this problem space.

Appservices which implement this MSC would generally be expected to *not* upload fallback keys or
one-time keys - implementations can make decisions to optimize for this usecase if they choose.

## Proposal

Similar to MSC3983, the homeserver *always* proxies the following APIs for an appservice's exclusive users
to the appservice using the new API described below:
* [`/_matrix/client/v3/keys/query`](https://spec.matrix.org/v1.6/client-server-api/#post_matrixclientv3keysquery)
* [`/_matrix/federation/v1/user/keys/query`](https://spec.matrix.org/v1.6/server-server-api/#post_matrixfederationv1userkeysquery)

**`POST /_matrix/app/v1/keys/query`**
```jsonc
// Request
{
  "@alice:example.org": ["DEVICEID"],
  "@bob:example.org": [], // indicates "all device IDs"
  // ...
}
```
```jsonc
// Response
// This is the same response format as `/_matrix/client/v3/keys/query`
{
  "device_keys": {
    "@alice:example.org": {
      "DEVICEID": {
        "algorithms": [
          "m.olm.v1.curve25519-aes-sha2",
          "m.megolm.v1.aes-sha2"
        ],
        "device_id": "DEVICEID",
        "keys": {
          "curve25519:DEVICEID": "3C5BFWi2Y8MaVvjM8M22DBmh24PmgR0nPvJOIArzgyI",
          "ed25519:DEVICEID": "lEuiRJBit0IG6nUf5pUzWTUEsRVVe/HJkoKuEww9ULI"
        },
        "signatures": {
          "@alice:example.org": {
            "ed25519:DEVICEID": "dSO80A01XiigH3uBiDVx/EjzaoycHcjq9lfQX0uWsqxl2giMIiSPR8a4d291W1ihKJL/a+myXS367WT6NAIcBA"
          }
        },
        "unsigned": {
          "device_display_name": "Alice's mobile phone"
        },
        "user_id": "@alice:example.org"
      }
    },
    // ... also a @bob:example.org record if appropriate
  },
  "master_keys": {
    "@alice:example.org": {
      "keys": {
        "ed25519:base64+master+public+key": "base64+master+public+key"
      },
      "usage": [
        "master"
      ],
      "user_id": "@alice:example.org"
    }
    // ... also a @bob:example.org record if appropriate
  },
  "self_signing_keys": {
    "@alice:example.org": {
      "keys": {
        "ed25519:base64+self+signing+public+key": "base64+self+signing+master+public+key"
      },
      "signatures": {
        "@alice:example.org": {
          "ed25519:base64+master+public+key": "signature+of+self+signing+key"
        }
      },
      "usage": [
        "self_signing"
      ],
      "user_id": "@alice:example.org"
    }
    // ... also a @bob:example.org record if appropriate
  },
  "user_signing_keys": {
    "@alice:example.org": {
      "keys": {
        "ed25519:base64+user+signing+public+key": "base64+user+signing+master+public+key"
      },
      "signatures": {
        "@alice:example.org": {
          "ed25519:base64+master+public+key": "signature+of+user+signing+key"
        }
      },
      "usage": [
        "user_signing"
      ],
      "user_id": "@alice:example.org"
    }
    // ... also a @bob:example.org record if appropriate
  }
}
```

*Note*: Like other appservice endpoints, this endpoint should *not* be ratelimited and *does* require
normal [authentication](https://spec.matrix.org/v1.6/application-service-api/#authorization).

If the appservice responds with an error of any kind (including timeout), the homeserver should treat
the appservice's response as `{}`. If the appservice indicates that the route is
[unknown](https://spec.matrix.org/v1.6/application-service-api/#unknown-routes), homeservers can back
off to avoid slowing down requests. It would be assumed that if the endpoint is unknown to the appservice
that the appservice is uploading keys rather than aiming to proxy them.

The appservice's response is then merged on top of any details the homeserver currently holds, up to the
device level. For example, if the homeserver believes the following for Alice:

```jsonc
{
  "device_keys": {
    "@alice:example.org": {
      "DEVICEID_1": { /* ... */ },
      "DEVICEID_2": { /* ... */ }
    }
  },
  "master_keys": {
    "@alice:example.org": { /* ... */ }
  },
  "self_signing_keys": {
    "@alice:example.org": { /* ... */  }
  },
  "user_signing_keys": {
    "@alice:example.org": { /* ... */  }
  }
}
```

... and the appservice responds with:

```jsonc
{
  "device_keys": {
    "@alice:example.org": {
      "DEVICEID_1": { /* ... */ }
      // note lack of DEVICEID_2
    }
  },
  "master_keys": {
    "@alice:example.org": { /* ... */ }
  }
  // note lack of self/user signing keys (an appservice doing this is unlikely, but here for illustrative purposes)
}
```

... the homeserver would merge the two, prioritizing the appservice's details.

```jsonc
{
  "device_keys": {
    "@alice:example.org": {
      "DEVICEID_1": { /* ... */ }, // as per appservice response
      "DEVICEID_2": { /* ... */ } // as per homeserver's existing knowledge
    }
  },
  "master_keys": {
    "@alice:example.org": { /* ... */ } // as per appservice response
  },
  "self_signing_keys": {
    "@alice:example.org": { /* ... */  } // as per homeserver's existing knowledge
  },
  "user_signing_keys": {
    "@alice:example.org": { /* ... */  } // as per homeserver's existing knowledge
  }
}
```

## Potential issues

No major issues.

## Alternatives

No major alternatives.

## Security considerations

No major considerations.

## Unstable prefix

While this MSC is not considered stable, implementations should use
`/_matrix/app/unstable/org.matrix.msc3984/keys/query` as the endpoint instead. There is no version
compatibility check: homeservers implementing this functionality would receive an error from appservices
which don't support the endpoint and thus engage in the behaviour described by the MSC.

## Dependencies

This MSC has no direct dependencies, however is of little use without being partnered with something
like [MSC3202](https://github.com/matrix-org/matrix-spec-proposals/pull/3202) and
[MSC3983](https://github.com/matrix-org/matrix-spec-proposals/pull/3983).
