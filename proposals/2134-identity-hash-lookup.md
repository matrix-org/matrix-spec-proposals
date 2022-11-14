# MSC2134: Identity Hash Lookups

[Issue #2130](https://github.com/matrix-org/matrix-doc/issues/2130) has been
created in response to a security issue brought up by an independent party.
To summarise the issue, when a user wants to ask an identity server which of
its contacts have registered a Matrix account, it performs a lookup against
an identity server. The client currently sends all of its contact details in
the form of plain-text addresses, meaning that the identity server can
identify and record every third-party ID (3PID) of the user's contacts. This
allows the identity server to collect email addresses and phone numbers that
have a high probability of being connected to a real person. This data could
then be used for marketing, political campaigns, etc.

However, if these email addresses and phone numbers are hashed before they are
sent to the identity server, the server would have a more difficult time of
being able to recover the original addresses. This prevents contact
information of non-Matrix users being exposed to the lookup service.

Yet, hashing is not perfect. While reversing a hash is not possible, it is
possible to build a [rainbow
table](https://en.wikipedia.org/wiki/Rainbow_table), which maps known email
addresses and phone numbers to their hash equivalents. When the identity
server receives a hash, it is then be able to look it up in its rainbow table
and find the corresponding 3PID. To prevent this, one would use a hashing
algorithm such as [bcrypt](https://en.wikipedia.org/wiki/Bcrypt) with many
rounds, making the construction of a large rainbow table an infeasibly
expensive process. Unfortunately, this is impractical for our use case, as it
would require clients to also perform many, many rounds of hashing, linearly
dependent on the size of their address book, which would likely result in
lower-end mobile phones becoming overwhelmed. We are then forced to use a
fast hashing algorithm, at the cost of making rainbow tables easy to build.

The rainbow table attack is not perfect, because one does need to know email
addresses and phone numbers to build it. While there are only so many
possible phone numbers, and thus it is relatively inexpensive to generate the
hash value for each one, the address space of email addresses is much, much
wider. If your email address does not use a common mail server, is decently long
or is not publicly known to attackers, it is unlikely that it would be
included in a rainbow table.

Thus the approach of hashing, while adding complexity to implementation and
resource consumption of the client and identity server, does provide added
difficulty for the identity server to carry out contact detail harvesting,
which should be considered worthwhile.

## Proposal

This proposal suggests making changes to the Identity Service API's lookup
endpoints, consolidating them into a single `/lookup` endpoint. The endpoint
is to be on a `v2` path, to avoid confusion with the original `v1` `/lookup`.
The `/api` part is also dropped in order to preserve consistency across other
endpoints:

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
separated by a space and a pepper, also separated by a space, appended to the
end. Note that phone numbers should be formatted as defined by
https://matrix.org/docs/spec/appendices#pstn-phone-numbers, before being
hashed). Note that "pepper" in this proposal simply refers to a public,
opaque string that is used to produce different hash results between identity
servers. Its value is not secret.

First the client must append the medium (plus a space) to the address:

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
identity servers must make the information available on the `/hash_details`
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
`lookup_pepper` MUST match the regular expression `[a-zA-Z0-9]+`, whether
hashing is being performed or not. When no hashing is occurring, a valid
pepper value of at least length 1 is still required.

If hashing, the client appends the pepper to the end of the 3PID string,
after a space.

```
"alice@example.com email" -> "alice@example.com email matrixrocks"
"bob@example.com email"   -> "bob@example.com email matrixrocks"
"carl@example.com email"  -> "carl@example.com email matrixrocks"
"12345678910 msdisn"      -> "12345678910 msisdn matrixrocks"
"denny@example.com email" -> "denny@example.com email matrixrocks"
```

Clients can cache the result of this endpoint, but should re-request it
during an error on `/lookup`, to handle identity servers which may rotate
their pepper values frequently. Clients MUST choose one of the given
`algorithms` values to hash the 3PID during lookup.

Clients and identity servers MUST support SHA-256 as defined by [RFC
4634](https://tools.ietf.org/html/rfc4634), identified by the value
`"sha256"` in the `algorithms` array. SHA-256 was chosen as it is currently
used throughout the Matrix spec, as well as its properties of being quick to
hash.

There are certain situations when an identity server cannot be expected to
compare hashed 3PID values; for example, when a server is connected to a
backend provider such as LDAP, it is not efficient for the identity server to
pull all of the addresses and hash them upon lookup. For this case, identity
servers can also support receiving plain-text 3PID addresses from clients. To
agree upon this, the value `"none"` can be added to the `"algorithms"` array
of `GET /hash_details`. The client can then choose to send plain-text values
by setting the `"algorithm"` value in `POST /lookup` to `"none"`.

No hashing nor peppering will be performed if the client and server decide on
`"none"`, and 3PIDs will be sent in plain-text, similar to the v1 `/lookup`
API. When this occurs, it is STRONGLY RECOMMENDED for the client to prompt
the user before continuing.

When performing a lookup, the pepper and hashing algorithm the client used
must be part of the request body (even when using the `"none"` algorithm
value). If they do not match what the server has on file (which may be the
case if the pepper was changed right after the client's request for it), then
the server must inform the client that they need to query the hash details
again, as opposed to just returning an empty response, which clients would
assume to mean that no contacts are registered on that identity server.

If the algorithm is not supported by the server, the server should return a `400
M_INVALID_PARAM`. If the pepper does not match the server's, the server should
return a new error code, `400 M_INVALID_PEPPER`. A new error code is not
defined for an unsupported algorithm as that is considered a client bug.

The `M_INVALID_PEPPER` error response contains the correct `algorithm` and
`lookup_pepper` fields. This is to prevent the client from needing to query
`/hash_details` again, thus saving a request. `M_INVALID_PARAM` does not
include these fields. An example response to an incorrect pepper would be:

```
{    
  "error": "Incorrect value for lookup_pepper",
  "errcode": "M_INVALID_PEPPER",
  "algorithm": "sha256",
  "lookup_pepper": "matrixrocks"
}
```

Now comes time for the lookup. We'll first cover an example of the client
choosing the `"sha256"` algorithm. Note that the resulting hash digest MUST
be encoded in URL-safe unpadded base64 (similar to [room version 4's event
IDs](https://matrix.org/docs/spec/rooms/v4#event-ids)). Once hashing has been
performed, the client sends each hash in an array.

```
"alice@example.com email matrixrocks" -> "4kenr7N9drpCJ4AfalmlGQVsOn3o2RHjkADUpXJWZUc"
"bob@example.com email matrixrocks"   -> "LJwSazmv46n0hlMlsb_iYxI0_HXEqy_yj6Jm636cdT8"
"carl@example.com email matrixrocks"  -> "jDh2YLwYJg3vg9pEn3kaaXAP9jx-LlcotoH51Zgb9MA"
"12345678910 msisdn matrixrocks"      -> "S11EvvwnUWBDZtI4MTRKgVuiRx76Z9HnkbyRlWkBqJs"
"denny@example.com email matrixrocks" -> "2tZto1arl2fUYtF6tQPJND69il3xke9OBlgFgnUt2ww"

POST /_matrix/identity/v2/lookup

{
  "addresses": [
    "4kenr7N9drpCJ4AfalmlGQVsOn3o2RHjkADUpXJWZUc",
    "LJwSazmv46n0hlMlsb_iYxI0_HXEqy_yj6Jm636cdT8",
    "jDh2YLwYJg3vg9pEn3kaaXAP9jx-LlcotoH51Zgb9MA",
    "S11EvvwnUWBDZtI4MTRKgVuiRx76Z9HnkbyRlWkBqJs",
    "2tZto1arl2fUYtF6tQPJND69il3xke9OBlgFgnUt2ww"
  ],
  "algorithm": "sha256",
  "pepper": "matrixrocks"
}
```

The identity server, upon receiving these hashes, can simply compare against
the hashes of the 3PIDs it stores. The server then responds with the Matrix
IDs of those that match:

```
{
  "mappings": {
    "4kenr7N9drpCJ4AfalmlGQVsOn3o2RHjkADUpXJWZUc": "@alice:example.com",
    "S11EvvwnUWBDZtI4MTRKgVuiRx76Z9HnkbyRlWkBqJs": "@fred:example.com"
  }
}
```

The client can now display which 3PIDs link to which Matrix IDs.

For the case of the identity server sending, and the client choosing,
`"none"` as the algorithm, we would do the following.

The client would first make `GET` a request to `/hash_details`, perhaps
receiving the response:

```
{
  "lookup_pepper": "matrixrocks",
  "algorithms": ["none", "sha256"]
}
```

The client decides that it would like to use `"none"`, and thus ignores the
lookup pepper, as no hashing will occur. Appending a space and the 3PID
medium to each address is still necessary:

```
"alice@example.com" -> "alice@example.com email"
"bob@example.com"   -> "bob@example.com email"
"carl@example.com"  -> "carl@example.com email"
"+1 234 567 8910"   -> "12345678910 msisdn"
"denny@example.com" -> "denny@example.com email"
```

The client then sends these off to the identity server in a `POST` request to
`/lookup`:

```
POST /_matrix/identity/v2/lookup

{
  "addresses": [
    "alice@example.com email",
    "bob@example.com email",
    "carl@example.com email",
    "12345678910 msisdn",
    "denny@example.com email"
  ],
  "algorithm": "none",
  "pepper": "matrixrocks"
}
```

Note that even though we haven't used the `lookup_pepper` value, we still
include the same one sent to us by the identity server in `/hash_details`.
The identity server should still return `400 M_INVALID_PEPPER` if the pepper
is incorrect. This simplifies things and can help ensure the client is
requesting `/hash_details` properly before each lookup request.

Finally, the identity server will check its database for the Matrix user IDs
it has that correspond to these 3PID addresses, and returns them:

```
{
  "mappings": {
    "alice@example.com email": "@alice:example.com",
    "12345678910 msisdn": "@fred:example.com"
  }
}
```

No parameter changes will be made to
[/bind](https://matrix.org/docs/spec/identity_service/r0.2.1#post-matrix-identity-api-v1-3pid-bind)
as part of this proposal.

## Fallback considerations

`v1` versions of these endpoints may be disabled at the discretion of the
implementation, and should return a `403 M_FORBIDDEN` error if so.

If an identity server is too old and a HTTP 400 or 404 is received when
accessing the `v2` endpoint, clients should fallback to the `v1` endpoint
instead. However, clients should be aware that plain-text 3PIDs are required
for the `v1` endpoints, and are strongly encouraged to warn the user of this.

## Tradeoffs

* There is a small cost incurred by performing hashes before requests, but this
  is outweighed by the privacy implications of sending plain-text addresses.

## Security Considerations

Hashes are still reversible with a rainbow table, but the provided pepper,
which can be rotated by identity servers at will, should help mitigate this.
Phone numbers (with their relatively short possible address space of 12
numbers), short email addresses at popular domains, and addresses of both
types that have been leaked in database dumps are more susceptible to hash
reversal.

Mediums and peppers are appended to the address as to prevent a common prefix
for each plain-text string, which prevents attackers from pre-computing the
internal state of the hash function.

## Other considered solutions

Bloom filters are an alternative method of providing private contact discovery.
However, they do not scale well due to requiring clients to download a large
filter that needs updating every time a new bind is made.

Further considered solutions are explored in
https://signal.org/blog/contact-discovery/. Signal's eventual solution of
using Software Guard Extensions (detailed in
https://signal.org/blog/private-contact-discovery/) is considered impractical
for a federated network, as it requires specialised hardware.

k-anonymity was considered as an alternative approach, in which the identity
server would never receive a full hash of a 3PID that it did not already know
about. Discussion and a walk-through of what a client/identity-server
interaction would look like are documented [in this Github
comment](https://github.com/matrix-org/matrix-doc/pull/2134#discussion_r298691748).

While this solution seems like a win for privacy, its actual benefits are a
lot more nuanced. Let's explore them by performing a threat-model analysis:

We consider three attackers:

 1. A malicious third party trying to discover the identity server mappings
    in the homeserver.

    The malicious third party scenario can only be protected against by rate
    limiting lookups, given otherwise it looks identical to legitimate traffic.

 1. An attacker who has stolen an IS db
 
    In theory the 3PIDs could be stored hashed with a static salt to protect
    a stolen DB. This has been descoped from this MSC, and is largely an
    orthogonal problem.

 1. A compromised or malicious identity server, who may be trying to
    determine the contents of a user's addressbook (including non-Matrix users)

Our approaches for protecting against a malicious identity server are:

 * We resign ourselves to the IS knowing the 3PIDs at point of bind, as
   otherwise it can't validate them.
 
 * To protect the 3PIDs of non-Matrix users:

   1. We could hash the uploaded 3PIDs with a static pepper; however, a
      malicious IS could pre-generate a rainbow table to reverse these hashes.

   1. We could hash the uploaded 3PIDs with a slowly rotating pepper; a
      malicious IS could generate a rainbow table in retrospect to reverse these
      hashes (but wouldn't be able to reuse the table)

   1. We could send partial hashes of the uploaded 3PIDs (with full salted
      hashes to disambiguate the 3PIDs), have the IS respond with anonymised
      partial results, to allow the IS to avoid reversing the 3PIDs (a
      k-anonymity approach). However, the IS could still claim to have mappings
      for all 3PIDs, and so receive all the salted hashes, and be able to
      reverse them via rainbow tables for that salt.

So, in terms of computational complexity for the attacker, respectively:

  1. The attacker has to generate a rainbow table over all possible IDs once,
     which can then be reused for subsequent attacks.

  1. The attacker has to generate a rainbow table over all possible IDs for a
     given lookup timeframe, which cannot be reused for subsequent attacks.

  1. The attacker has to generate multiple but partial rainbow tables, one
     per group of 3PIDs that share similar hash prefixes, which cannot then be
     reused for any other attack.
  
For making life hardest for an attacker, option 3 (k-anon) wins. However, it
also makes things harder for the client and server:

 * The client has to calculate new salted hashes for all 3PIDs every time it
   uploads.

 * The server has to calculate new salted hashes for all partially-matching
   3PIDs hashes as it looks them up.

It's worth noting that one could always just go and load up a malicious IS DB
with a huge pre-image set of mappings and thus see what uploaded 3PIDs match,
no matter what algorithm is used.

For k-anon this would put the most computational onus on the server (as it
would effectively be creating a partial rainbow table for every lookup), but
this is probably not infeasible - so we've gone and added a lot of complexity
and computational cost for not much benefit, given the system can still be
trivially attacked.

Finally, as more and more users come onto Matrix, their contact lists will
get more and more exposed anyway given the IS server has to be able to
identity Matrix-enabled 3PIDs to perform the lookup.

Thus the conclusion is that while k-anon is harder to attack, it's unclear
that this is actually enough of an obstacle to meaningfully stop a malicious
IS. Therefore we should KISS and go for a simple hash lookup with a rotating
pepper (which is not much harder than a static pepper, especially if our
initial implementation doesn't bother rotating the pepper). Rather than
trying to make the k-anon approach work, we'd be better off spending that
time figuring out how to store 3pids as hashes in the DB (and in 3pid
bindings etc), or how to decentralise ISes in general. It's also worth noting
that a malicious server may fail to rotate the pepper, making the rotation
logic of questionable benefit.

A radical model was also considered where the first portion of the
k-anonyminity scheme was done with an identity server, and the second would
be done with various homeservers who originally reported the 3PID to the
identity server. While interesting and more decentralised, some attacks are
still possible if the identity server is running an evil homeserver which it
can direct the client to send its hashes to. Discussion on this matter has
taken place in the MSC-specific room [starting at this
message](https://matrix.to/#/!LlraCeVuFgMaxvRySN:amorgan.xyz/$4wzTSsspbLVa6Lx5cBq6toh6P3TY3YnoxALZuO8n9gk?via=amorgan.xyz&via=matrix.org&via=matrix.vgorcum.com).

Tangentially, identity servers would ideally just never receive plain-text
addresses, just storing and receiving hash values instead. However, it is
necessary for the identity server to have plain-text addresses during a
[bind](https://matrix.org/docs/spec/identity_service/r0.2.1#post-matrix-identity-api-v1-3pid-bind)
call, in order to send a verification email or sms message. It is not
feasible to defer this job to a homeserver, as the identity server cannot
trust that the homeserver has actually performed verification. Thus it may
not be possible to prevent plain-text 3PIDs of registered Matrix users from
being sent to the identity server at least once. Yet, it is possible that with
a few changes to other Identity Service endpoints, as described in [this
review
comment](https://github.com/matrix-org/matrix-doc/pull/2134#discussion_r309617900),
identity servers could refrain from storing any plaintext 3PIDs at rest. This
however, is a topic for a future MSC.

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
