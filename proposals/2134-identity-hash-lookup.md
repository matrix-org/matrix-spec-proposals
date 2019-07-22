# MSC2134: Identity Hash Lookups

[Issue #2130](https://github.com/matrix-org/matrix-doc/issues/2130) has been
recently created in response to a security issue brought up by an independent
party. To summarise the issue, lookups (of Matrix user IDs) are performed using
plain-text 3PIDs (third-party IDs) which means that the identity server can
identify and record every 3PID that the user has in their contacts, whether
that email address or phone number is already known by the identity server or
not.

If the 3PID is hashed, the identity server could not determine the address
unless it has already seen that address in plain-text during a previous call
of the [/bind
mechanism](https://matrix.org/docs/spec/identity_service/r0.2.1#post-matrix-identity-api-v1-3pid-bind)
(without significant resources to reverse the hashes). This helps prevent
bulk collection of user's contact lists by the identity server and reduces
its ability to build social graphs.

This proposal thus calls for the Identity Service API's
[/lookup](https://matrix.org/docs/spec/identity_service/r0.2.1#get-matrix-identity-api-v1-lookup)
endpoint to use hashed 3PIDs instead of their plain-text counterparts (and to
deprecate both it and
[/bulk_lookup](https://matrix.org/docs/spec/identity_service/r0.2.1#post-matrix-identity-api-v1-bulk-lookup)),
which will leak less data to identity servers.

## Proposal

This proposal suggests making changes to the Identity Service API's lookup
endpoints. Instead, this proposal consolidates them into a single `/lookup`
endpoint. Additionally, the endpoint is to be on a `v2` path, to avoid
confusion with the original `/lookup`. We also drop the `/api` in order to
preserve consistency across other endpoints:

- `/_matrix/identity/v2/lookup`

A second endpoint is added for clients to request information about the form
the server expects hashes in.

- `/_matrix/identity/v2/hash_details`

The following back-and-forth occurs between the client and server.

Let's say the client wants to check the following 3PIDs:

```
alice@example.com
bob@example.com
carl@example.com
+1 234 567 8910
denny@example.com
```

The client will hash each 3PID as a concatenation of the medium and address,
separated by a space and a pepper appended to the end. Note that phone numbers
should be formatted as defined by
https://matrix.org/docs/spec/appendices#pstn-phone-numbers, before being
hashed). First the client must append the medium to the address:

```
"alice@example.com" -> "alice@example.com email"
"bob@example.com"   -> "bob@example.com email"
"carl@example.com"  -> "carl@example.com email"
"+1 234 567 8910"   -> "12345678910 msisdn"
"denny@example.com" -> "denny@example.com email"
```

Hashes must be peppered in order to reduce both the information an identity
server gains during the process, and attacks the client can perform. [0]

In order for clients to know the pepper and hashing algorithm they should use,
Identity servers must make the information available on the `/hash_details`
endpoint:

```
GET /_matrix/identity/v2/hash_details

{
  "lookup_pepper": "matrixrocks",
  "algorithms": ["sha256"]
}
```

The name `lookup_pepper` was chosen in order to account for pepper values
being returned for other endpoints in the future. The contents of
`lookup_pepper` MUST match the regular expression `[a-zA-Z0-9]+` (unless no
hashing is being performed, as described below). If hashing is being
performed, and `lookup_pepper` is an empty string, clients MUST cease the
lookup operation.

The client should append the pepper to the end of the 3PID string before
hashing.

```
"alice@example.com email" -> "alice@example.com emailmatrixrocks"
"bob@example.com email"   -> "bob@example.com emailmatrixrocks"
"carl@example.com email"  -> "carl@example.com emailmatrixrocks"
"12345678910 msdisn"      -> "12345678910 msisdnmatrixrocks"
"denny@example.com email" -> "denny@example.com emailmatrixrocks"
```

Clients SHOULD request this endpoint each time before performing a lookup, to
handle identity servers which may rotate their pepper values frequently.
Clients MUST choose one of the given hash algorithms to encrypt the 3PID
during lookup.

Clients and identity servers MUST support SHA-256 as defined by [RFC
4634](https://tools.ietf.org/html/rfc4634), identified by the `algorithm`
value `"sha256"`. SHA-256 was chosen as it is currently used throughout the
Matrix spec, as well as its properties of being quick to hash. While this
reduces the resources necessary to generate a rainbow table for attackers, a
fast hash is necessary if particularly slow mobile clients are going to be
hashing thousands of contact details. Other algorithms can be negotiated by
the client and server at their discretion.

There are certain situations when an identity server cannot be expected to
compare hashed 3PID values; for example, when a server is connected to a
backend provider such as LDAP, there is no way for the identity server to
efficiently pull all of the addresses and hash them. For this case, clients
and server MUST also support sending plain-text 3PID values. To agree upon
this, the `algorithm` field of `GET /hash_details` MUST be set to `"m.none"`,
whereas `lookup_pepper` will be an empty string. No hashing will be performed
if the client and server decide on this, and 3PIDs will be sent in
plain-text, similar to the v1 `/lookup` API. When this occurs, it is STRONGLY
RECOMMENDED for the client to prompt the user before continuing, and receive
consent for sending 3PID details in plain-text to the identity server.

When performing a lookup, the pepper and hashing algorithm the client used
must be part of the request body (even when using the `"m.none"` algorithm
value). If they do not match what the server has on file (which may be the
case if the pepper was changed right after the client's request for it), then
the server must inform the client that they need to query the hash details
again, instead of just returning an empty response, which clients would
assume to mean that no contacts are registered on that identity server.

If the algorithm does not match the server's, the server should return a `400
M_INVALID_PARAM`. If the pepper does not match the server's, the server should
return a new error code, `400 M_INVALID_PEPPER`. A new error code is not
defined for an invalid algorithm as that is considered a client bug.

The `M_INVALID_PEPPER` error response should contain the correct `algorithm`
and `lookup_pepper` fields. This is to prevent the client from needing to
query `/hash_details` again, thus saving a round-trip. `M_INVALID_PARAM` does
not include these fields. An example response to an incorrect pepper would
be:

```
{    
  "error": "Incorrect value for lookup_pepper",
  "errcode": "M_INVALID_PEPPER",
  "algorithm": "sha256",
  "lookup_pepper": "matrixrocks"
}
```

Now comes time for the lookup. Note that the resulting hash digest MUST be
encoded in URL-safe unpadded base64 (similar to [room version 4's event
IDs](https://matrix.org/docs/spec/rooms/v4#event-ids)). Once hashing has been
performed using the defined hashing algorithm, the client sends each hash in an
array.

```
NOTE: Hashes are not real values

"alice@example.com emailmatrixrocks" -> "y_TvXLKxFT9CURPXI1wvfjvfvsXe8FPgYj-mkQrnszs"
"bob@example.com emailmatrixrocks"   -> "r0-6x3rp9zIWS2suIque-wXTnlv9sc41fatbRMEOwQE"
"carl@example.com emailmatrixrocks"  -> "ryr10d1K8fcFVxALb3egiSquqvFAxQEwegXtlHoQFBw"
"12345678910 msisdnmatrixrocks"      -> "c_30UaSZhl5tyanIjFoE1IXTmuU3vmptEwVOc3P2Ens"
"denny@example.com emailmatrixrocks" -> "bxt8rtRaOzMkSk49zIKE_NfqTndHvGbWHchZskW3xmY"

POST /_matrix/identity/v2/lookup

{
  "hashes": [
    "y_TvXLKxFT9CURPXI1wvfjvfvsXe8FPgYj-mkQrnszs",
    "r0-6x3rp9zIWS2suIque-wXTnlv9sc41fatbRMEOwQE",
    "ryr10d1K8fcFVxALb3egiSquqvFAxQEwegXtlHoQFBw",
    "c_30UaSZhl5tyanIjFoE1IXTmuU3vmptEwVOc3P2Ens",
    "bxt8rtRaOzMkSk49zIKE_NfqTndHvGbWHchZskW3xmY"
  ],
  "algorithm": "sha256",
  "pepper": "matrixrocks"
}
```

The identity server, upon receiving these hashes, can simply compare against
the hashes of the 3PIDs it stores.  The server then responds with the Matrix
IDs of those that match:

```
{
  "mappings": {
    "y_TvXLKxFT9CURPXI1wvfjvfvsXe8FPgYj-mkQrnszs": "@alice:example.com",
    "c_30UaSZhl5tyanIjFoE1IXTmuU3vmptEwVOc3P2Ens": "@fred:example.com"
  }
}
```

The client can now display which 3PIDs link to which Matrix IDs.

No parameter changes will be made to
[/bind](https://matrix.org/docs/spec/identity_service/r0.2.1#post-matrix-identity-api-v1-3pid-bind)
as part of this proposal.

## Fallback considerations

`v1` versions of these endpoints may be disabled at the discretion of the
implementation, and should return a `403 M_FORBIDDEN` error if so.

If an identity server is too old and a HTTP 400 or 404 is received when
accessing the `v2` endpoint, they should fallback to the `v1` endpoint instead.
However, clients should be aware that plain-text 3PIDs are required for the
`v1` endpoint, and SHOULD ask for user consent to send 3PIDs in plain-text, and
be clear about where they are being sent to.

## Tradeoffs

* There is a small cost incurred by performing hashes before requests, but this
  is outweighed by the privacy implications of sending plain-text addresses.

## Security Considerations

Hashes are still reversible with a rainbow table, but the provided pepper,
which can be rotated by identity servers at will, should help mitigate this.
Phone numbers (with their relatively short possible address space of 12
numbers), short email addresses, and addresses of both type that have been
leaked in database dumps are more susceptible to hash reversal.

Mediums and peppers are appended to the address as to prevent a common prefix
for each plain-text string, which prevents attackers from pre-computing bits
of a stream cipher.

Additionally, this proposal does not stop an identity server from storing
plain-text 3PIDs. There is a GDPR argument in keeping email addresses, such
that if a breach happens, users must be notified of such. Ideally this would be
done over Matrix, but people may've stuck their email in an identity server and
then left Matrix forever. Perhaps if only hashes were being stored on the
identity server then that isn't considered personal information? In any case, a
discussion for another MSC.

## Other considered solutions

Ideally identity servers would never receive plain-text addresses, however it
is necessary for the identity server to send email/sms messages during a
bind, as it cannot trust a homeserver to do so as the homeserver may be lying.

Bloom filters are an alternative method of providing private contact discovery.
However, they do not scale well due to requiring clients to download a large
filter that needs updating every time a new bind is made. Further considered
solutions are explored in https://signal.org/blog/contact-discovery/. Signal's
eventual solution of using Software Guard Extensions (detailed in
https://signal.org/blog/private-contact-discovery/) is considered impractical
for a federated network, as it requires specialized hardware.

k-anonymity was considered as an alternative, in which the identity server
would never receive a full hash of a 3PID that it did not already know about.
While this has been considered plausible, it comes with heightened resource
requirements (much more hashing by the identity server). The conclusion was
that it may not provide more privacy if an identity server decided to be evil,
however it would significantly raise the resource requirements to run an evil
identity server. 

Discussion and a walk-through of what a client/identity-server interaction would
look like are documented [in this Github
comment](https://github.com/matrix-org/matrix-doc/pull/2134#discussion_r298691748).

Additionally, a radical model was also considered where the first portion of
the above scheme was done with an identity server, and the second would be done
with various homeservers who originally reported the 3PID to the identity
server. While interesting and a more decentralised model, some attacks are
still possible if the identity server is running an evil homeserver which it
can direct the client to send its hashes to. Discussion on this matter has
taken place in the MSC-specific room [starting at this
message](https://matrix.to/#/!LlraCeVuFgMaxvRySN:amorgan.xyz/$4wzTSsspbLVa6Lx5cBq6toh6P3TY3YnoxALZuO8n9gk?via=amorgan.xyz&via=matrix.org&via=matrix.vgorcum.com).

## Conclusion

This proposal outlines a simple method to stop bulk collection of user's
contact lists and their social graphs without any disastrous side effects. All
functionality which depends on the lookup service should continue to function
unhindered by the use of hashes.

## Footnotes

[0] Clients would have to generate a full rainbow table specific to the set
pepper to obtain all registered MXIDs, while the server would have to
generate a full rainbow table with the specific pepper to get the plaintext
3pids for non-matrix users.
