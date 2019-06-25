# MSC2134: Identity Hash Lookups

[Issue #2130](https://github.com/matrix-org/matrix-doc/issues/2130) has been
recently created in response to a security issue brought up by an independent
party. To summarise the issue, lookups (of Matrix user IDs) are performed using
non-hashed 3PIDs (third-party IDs) which means that the identity server can
identify and record every 3PID that the user wants to check, whether that
address is already known by the identity server or not.

If the 3PID is hashed, the identity server could not determine the address
unless it has already seen that address in plain-text during a previous call of
the /bind mechanism.

Note that in terms of privacy, this proposal does not stop an identity server
from mapping hashed 3PIDs to users, resulting in a social graph. However, the
identity of the 3PID will at least remain a mystery until /bind is used.

This proposal thus calls for the Identity Service’s /lookup API to use hashed
3PIDs instead of their plain-text counterparts.

## Proposal

This proposal suggests making changes to the Identity Service API's lookup
endpoints. Due to the nature of this proposal, the new endpoints should be on a
`v2` path (we also drop the `/api` in order to preserve consistency across
other endpoints):

- `/_matrix/identity/v2/lookup`
- `/_matrix/identity/v2/bulk_lookup`

`address` MUST no longer be in a plain-text format, but rather will be a peppered hash
value, and the resulting digest MUST be encoded in unpadded base64.

Identity servers must specify their own hashing algorithms (from a list of
specified values) and pepper, which will be useful if a rainbow table is
released for their current one. Identity servers could also set a timer for
rotating the pepper value to further impede rainbow table publishing (the
recommended period is every 30 minutes, which should be enough for a client to
complete the hashing of all of a user's contacts, but also be nowhere near as
long enough to create a sophisticated rainbow table). As such, it must be
possible for clients to be able to query what pepper the identity server
requires before sending it hashes. A new endpoint must be added:

```
GET /_matrix/identity/v2/hash_details
```

This endpoint takes no parameters, and simply returns any supported hash
algorithms and pepper as a JSON object:

```
{
  "lookup_pepper": "matrixrocks",
  "algorithms": ["sha256"],
}
```

The name `lookup_pepper` was chosen in order to account for pepper values being
returned for other endpoints in the future.

Clients should request this endpoint each time before making a `/lookup` or
`/bulk_lookup` request, to handle identity servers which may rotate their
pepper values frequently. Clients must choose one of the given hash algorithms
to encrypt the 3PID during lookup.

An example of generating a hash using SHA-256 and the provided pepper is as
follows:

```python
address = "user@example.org"
pepper = "matrixrocks"
digest = hashlib.sha256((pepper + address).encode()).digest()
result_address = unpaddedbase64.encode_base64(digest)
print(result_address)
vNjEQuRCOmBp/KTuIpZ7RUJgPAbVAyqa0Uzh770tQaw
```

Possible hashing algorithms will be defined in the Matrix specification, and an
Identity Server can choose to implement one or all of them. Later versions of
the specification may deprecate algorithms when necessary. Currently the only
listed hashing algorithm is SHA-256 as defined by [RFC
4634](https://tools.ietf.org/html/rfc4634) and Identity Servers and clients
MUST agree to its use with the string `sha256`. SHA-256 was chosen as it is
currently used throughout the Matrix spec, as well as its properties of being
quick to hash. While this reduces the resources necessary to generate a rainbow
table for attackers, a fast hash is necessary if particularly slow mobile
clients are going to be hashing thousands of contacts.

When performing a lookup, the pepper and hashing algorithm the client used must
be part of the request body. If they do not match what the server has on file
(which may be the case if the pepper was rotated right after the client's
request for it), then the server must inform the client that they need to query
the hash details again, instead of just returning an empty response, which
clients would assume to mean that no contacts are registered on that identity
server.

Thus, an example client request to `/bulk_lookup` would look like the
following:

```
{
  "threepids": [
    [
      "email",
      "vNjEQuRCOmBp/KTuIpZ7RUJgPAbVAyqa0Uzh770tQaw"
    ],
    [
      "msisdn",
      "0VnvYk7YZpe08fP/CGqs3f39QtRjqAA2lPd14eLZXiw"
    ],
    [
      "email",
      "BJaLI0RrLFDMbsk0eEp5BMsYDYzvOzDneQP/9NTemYA"
    ]
  ],
  "lookup_pepper": "matrixrocks",
  "algorithm": "sha256"
}
```

If the pepper does not match the server's, the server should return a `400
M_INVALID_PARAM`.

No parameter changes will be made to /bind.

## Fallback considerations

`v1` versions of these endpoints may be disabled at the discretion of the
implementation, and should return a HTTP 403 if so.

If an identity server is too old and a HTTP 404, 405 or 501 is received when
accessing the `v2` endpoint, they should fallback to the `v1` endpoint instead.
However, clients should be aware that plain-text 3PIDs are required, and SHOULD
ask for user consent to send 3PIDs in plain-text, and be clear about where they
are being sent to.

## Tradeoffs

* This approach means that the client now needs to calculate a hash by itself,
  but the belief is that most languages provide a mechanism for doing so.
* There is a small cost incurred by performing hashes before requests, but this
  is outweighed by the privacy implications of sending plain-text addresses.

## Potential issues

This proposal does not force an identity server to stop handling plain-text
requests, because a large amount of the Matrix ecosystem relies upon this
behavior. However, a conscious effort should be made by all users to use the
privacy respecting endpoints outlined above. Identity servers may disallow use
of the v1 endpoint, as per above.

Unpadded base64 has been chosen to encode the value due to use in many other
portions of the spec.

## Other considered solutions

Ideally identity servers would never receive plain-text addresses, however it
is necessary for the identity server to send email/sms messages during a
bind, as it cannot trust a homeserver to do so as the homeserver may be lying.
Additionally, only storing 3PID hashes at rest instead of the plain-text
versions is impractical if the hashing algorithm ever needs to be changed.

Bloom filters are an alternative method of providing private contact discovery,
however does not scale well due to clients needing to download a large filter
that needs updating every time a new bind is made. Further considered solutions
are explored in https://signal.org/blog/contact-discovery/ Signal's eventual
solution of using Software Guard Extensions (detailed in
https://signal.org/blog/private-contact-discovery/) is considered impractical
for a federated network, as it requires specialized hardware.

While a bit out of scope for this MSC, there has been debate over preventing
3PIDs as being kept as plain-text on disk. The argument against this was that
if the hashing algorithm (in this case SHA-256) was broken, we couldn't update
the hashing algorithm without having the plaintext 3PIDs. @lampholder helpfully
added that we could just take the old hashes and rehash them in the more secure
hashing algorithm, thus transforming the hash from SHA-256 to
SHA-256+SomeBetterAlg. However @erikjohnston then pointed out that if
`BrokenAlgo(a) == BrokenAlgo(b)` then `SuperGreatHash(BrokenAlgo(a)) ==
SuperGreatHash(BrokenAlgo(b))`, so all you'd need to do is find a match in the
broken algo, and you'd break the new algorithm as well. This means that you
would need the plaintext 3PIDs to encode a new hash, and thus storing them
hashed on disk would require a transition period where 3pids were reuploaded in
a strong hash variant.

## Conclusion

This proposal outlines an effective method to stop bulk collection of user's
contact lists and their social graphs without any disastrous side effects. All
functionality which depends on the lookup service should continue to function
unhindered by the use of hashes.
