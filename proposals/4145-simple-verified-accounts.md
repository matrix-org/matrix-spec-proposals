# MSC4145: Simple verified accounts

[Server notices](https://spec.matrix.org/v1.10/client-server-api/#server-notices) and similar alerts
sent by servers are typically sent by a general purpose user such as `@support:example.org`. These
messages can [look like a phishing attempt](https://github.com/element-hq/element-meta/issues/1759)
when they lack any "official" markings.

This proposal introduces a simple server-local verification mechanism to identify "verified"
accounts. This proposal does *not* introduce a mechanism to request/assign verification, nor manage
that verification - this is left as an implementation detail under this proposal, and may be
improved by a future MSC.

## Proposal

The user's [global profile](https://spec.matrix.org/v1.10/client-server-api/#profiles) has a new
*optional* `m.verified` property added, as shown by the below endpoints.

`m.verified` takes on a slightly weird shape to allow for future expansion, such as the potential
for a signed object, attestation, etc. The `m.verified` object can only contain a single boolean
currently: `verified`. When `m.verified` is supplied, `verified` can only be `true` (otherwise the
user is considered "unverified" or "default").

[`GET /_matrix/client/v3/profile/{userId}`](https://spec.matrix.org/v1.10/client-server-api/#get_matrixclientv3profileuserid)
response:
```jsonc
{
  "displayname": "Support",
  "avatar_url": "mxc://example.org/abc123",
  "m.verified": { // new!
    "verified": true
  }
}
```

If the user is not verified, `m.verified` will not be present.

**New Endpoint** - `GET /_matrix/client/v3/profile/{userId}/m.verified`

*No request body.*

Response:
```jsonc
{
  "m.verified": {
    "verified": true
  }
}
```

The endpoint behaves similar to [`GET /_matrix/client/v3/profile/{userId}/displayname`](https://spec.matrix.org/v1.10/client-server-api/#get_matrixclientv3profileuseriddisplayname):
if the user doesn't exist or is not verified locally on the server, the endpoint returns 404 `M_NOT_FOUND`.
Note that this new endpoint does *not* go over federation to determine verified status - for this
proposal, verification is very intentionally a server-local state.

Unlike `GET /displayname`, there is deliberately no `PUT /m.verified` partner endpoint.

### Applicability

Verified users SHOULD have a badge next to their name when they send a message or invite within the
client's UI, regardless of which room they're in. Clients SHOULD use a custom graphic to denote this
verified badge rather than an emoji to prevent phishing attempts from other users.

Clients SHOULD also show a warning or "unverified" badge when a sender appears to be trying to
indicate that they're verified when they're not. For example, `Alice ☑️` or `Alice [VERIFIED]`.

It is left as an implementation detail for how to assign/request verification status. A server might,
for example, put a policy in place where only specific individuals receive verification status with
no opportunity to apply. Another server might require requests to be sent to `@support:example.org`.

### Caching

A given user's name can appear in a number of places within a client, potentially leading to *thousands*
of calls for verification status. To help reduce this request spam, calls to `GET /_matrix/client/v3/profile/{userId}/m.verified`
MUST be cached by clients, either by respecting the [`Cache-Control`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Cache-Control)
header, or for a minimum of 24 hours. Similarly, `m.verified` on the general `/profile/{userId}`
endpoint must be cached for at least 24 hours.

Verification status is not expected to change often, so longer cache values are preferred.

## Potential issues

This proposal doesn't work over federation. This is a feature, not a bug. Communicating verification
over federation would ideally mean having a method for end clients to confirm the verification
without the use of the attached homeserver. Such a problem is challenging to solve quickly.

## Alternatives

Significant alternatives are implied throughout. Namely, a proper verification system could be
introduced instead, though such a system requires significant engineering effort.

## Security considerations

Clients MUST be cautious and warn users of possible phishing attempts relating to verification, as
discussed earlier in this MSC.

## Unstable prefix

While this MSC is not considered stable, the following transformations apply:

* `GET /_matrix/client/v3/profile/{userId}/m.verified` becomes `GET /_matrix/client/unstable/org.matrix.msc4145/profile/{userId}/org.matrix.msc4145.verified`
* `m.verified` becomes `org.matrix.msc4145.verified`

## Dependencies

This MSC has no direct dependencies itself.
