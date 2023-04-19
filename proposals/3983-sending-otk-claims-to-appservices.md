# MSC3983: Sending One-Time Key (OTK) claims to appservices

Presently in Matrix, the public portion of OTKs are [uploaded](https://spec.matrix.org/v1.6/client-server-api/#uploading-keys)
to the homeserver to ensure other devices can encrypt new messages without requiring the device to
be online and responsive. This works for devices operating exclusively over the Client-Server API,
however [appservices](https://spec.matrix.org/v1.6/application-service-api/) looking to support
encryption (through [MSC3202](https://github.com/matrix-org/matrix-spec-proposals/pull/3202) or
similar) could have millions or billions of users on them, which can easily translate to quite a
few public keys needing to be uploaded to the homeserver.

Given appservices *generally* have an uptime which is equivalent to the homeserver itself, and will
have already stored the public portion of its OTKs somewhere, we can save a bit of duplication by
having the homeserver delegate [`/keys/claim`](https://spec.matrix.org/v1.6/client-server-api/#post_matrixclientv3keysclaim)
requests to the appservice.

In numbers, a conservative estimate for an interoperable messaging bridge (appservice) would be
500 million users. Each user generates between 50 and 100 OTKs, so we'll pick the low end at 50.
That's 25 **billion** public keys. Currently in Matrix, that means the appservice stores 25 billion
keys and the homeserver stores a copy of those 25 billion keys.

This proposal introduces a mechanism for saving the homeserver from duplicating 25 billion keys.

## Background

Appservices can register a [namespace](https://spec.matrix.org/v1.6/application-service-api/#registration)
of users either exclusively (no one else can register users matching the regex) or implicitly (the
appservice receives events about those users, but can't prevent registration). Implicit namespaces
can be shared across multiple appservices.

## Proposal

For users under an appservice's explicit namespace, if that user has no unused OTKs (excluding fallback
keys) on the homeserver, the homeserver proxies the following APIs to the appservice using the new
API described below:
* [`/_matrix/client/v3/keys/claim`](https://spec.matrix.org/v1.6/client-server-api/#post_matrixclientv3keysclaim)
* [`/_matrix/federation/v1/user/keys/claim`](https://spec.matrix.org/v1.6/server-server-api/#post_matrixfederationv1userkeysclaim)

**`POST /_matrix/app/v1/keys/claim`**
```jsonc
// Request
{
  "@alice:example.org": {
    "DEVICEID": ["signed_curve25519", "signed_curve25519"] // device ID to algorithm names
  },
  // ...
}
```
```jsonc
// Response
{
  "@alice:example.org": {
    "DEVICEID": {
      "signed_curve25519:AAAAHg": {
        "key": "...",
        "signatures": {
          "@alice:example.org": {
            "ed25519:DEVICEID": "..."
          }
        }
      },
      "signed_curve25519:BBBBHg": {
        "key": "...",
        "signatures": {
          "@alice:example.org": {
            "ed25519:DEVICEID": "..."
          }
        }
      }
    }
  },
  // ...
}
```

*Note*: Like other appservice endpoints, this endpoint should *not* be ratelimited and *does* require
normal [authentication](https://spec.matrix.org/v1.6/application-service-api/#authorization).

Multiple users, devices, and keys for those devices can be claimed in a single request. This is to
allow homeservers to batch multiple client/federation requests into a single request on the appservice,
if desirable. This is an optional optimization for homeserver implementations. In the example above, 2
keys are claimed for one device.

If the appservice responds with an error of any kind (including timeout), the homeserver uses the
fallback key, if known. The homeserver additionally uses the fallback key (if known) to fill in
missing keys from the appservice. For example, if the homeserver requested 2 keys for Alice but
the appservice only provided 1, the homeserver would use the fallback key to fulfill the second.

In this case, the appservice is responsible for ensuring it doesn't use a key twice. The
`device_one_time_keys_count` field for the appservice (over MSC3202, for example) would be zero. In
many implementations, when this field falls below a threshold it is common for upload requests to
happen: appservices intending on using the new API should not perform those uploads as it means,
quite simply, not using the new API.

Normally the homeserver would be [ensuring](https://spec.matrix.org/v1.6/client-server-api/#one-time-and-fallback-keys)
OTKs are only used once, however with the appservice serving the endpoint it becomes the responsibility
of the appservice to perform this check.

If the homeserver uses the fallback key, that will be communicated in the traditional ways to the
appservice (namely through `device_unused_fallback_key_types` in the case of MSC3202).

We don't apply this API to implicit (non-exclusive) users as it's possible for multiple appservices
to have a namespace covering the user: instead of guessing or going around to each, we require the
user to be in an exclusive namespace. This guarantees that there's only one appservice responsible
for the user.

## Returning extra keys

**TODO**: This is probably best as its own MSC.

Independent of the appservice having `/keys/claim` proxied to it, it may be desirable for both the
fallback and one-time key to be returned. Servers should *always* include the fallback key alongside
the requested OTKs. When using this proposal's new endpoint, the server should use the fallback key
from the appservice's response rather than a previously stored fallback key, if present (if the
appservice doesn't respond with a fallback key then the server uses the stored fallback key instead,
if known). 

The server SHOULD NOT replace any uploaded fallback keys with ones returned by the appservice via
this proposal. The appservice MUST re-upload the fallback key if it wants to replace it, as it would
do upon first (known) use.

Clients can determine which of the keys returned is the fallback key by `fallback: true` on the returned
keys.

Servers MUST NOT mark the fallback key as "used" unless no other OTKs are returned.

## Potential issues

As described, the appservice could be offline or in fact experience a worse uptime than the homeserver.
This new API is optional for appservices: if they don't want to use it (because they know their uptime
will be bad), they can simply upload keys in advance, just like before this proposal. Similarly, if
the appservice is trying to use the API but is offline, they *should* have a fallback key to continue
using as, well, a fallback.

For appservices which never intend to upload keys there is a bit of a wasted lookup to see if there are
any keys for the user(s). This could be mitigated with an implementation-specific flag to skip the lookup
and just do proxying, though for the general case in this MSC the fallback key consideration is kept for
reliability concerns.

Similarly, if an appservice doesn't intend on uploading keys (because it doesn't support encryption) and
indicates the route is [unknown](https://spec.matrix.org/v1.6/application-service-api/#unknown-routes),
the homeserver could avoid calling appservice with a backoff to prevent excessive calls.

## Alternatives

Many encryption-capable bridges today can avoid uploading OTKs (and sometimes even device keys) because
they have a bot user in the room. The bot user uploads its keys, but the remaining bridge users do not.
This works if the bridge users don't need to be involved in rooms without the bot user present, though
being able to (securely) DM bridge users is a valuable consideration for this MSC. In future, scalable
encryption for appservices might take the shape of an appservice-wide device of some sort.

It could be argued that supporting a fallback key for appservices is too much considering their uptime,
however in practice appservices are not quite able to achieve 100% uptime. This proposal doesn't propose
proxying device/signing key queries to the appservice for the same reliability concerns, though appservices
which wish to opt to do so anyways could use [MSC3984](https://github.com/matrix-org/matrix-spec-proposals/pull/3984).

## Additional uses

An appservice aiming to bridge two different encryption systems might use this endpoint to save on data,
though currently the encryption used on both sides of the bridge would need to be compatible (ie: signatures
from device IDs and user IDs need to exist). In future, other MSCs might make encryption bridges easier to
build.

## Security considerations

No major considerations.

## Unstable prefix

While this MSC is not considered stable, implementations should use
`/_matrix/app/unstable/org.matrix.msc3983/keys/claim` as the endpoint instead. There is no version
compatibility check: homeservers implementing this functionality would receive an error from appservices
which don't support the endpoint and thus engage in the behaviour described by the MSC.

## Dependencies

This MSC has no direct dependencies, however is of little use without being partnered with something
like [MSC3202](https://github.com/matrix-org/matrix-spec-proposals/pull/3202).

This MSC is additionally useful when paired with [MSC3984](https://github.com/matrix-org/matrix-spec-proposals/pull/3984),
though has no direct dependency.
