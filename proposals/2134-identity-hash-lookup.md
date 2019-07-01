# MSC2134: Identity Hash Lookups

[Issue #2130](https://github.com/matrix-org/matrix-doc/issues/2130) has been
recently created in response to a security issue brought up by an independent
party. To summarise the issue, lookups (of Matrix user IDs) are performed using
plain-text 3PIDs (third-party IDs) which means that the identity server can
identify and record every 3PID that the user has in their contacts, whether
that email address or phone number is already known by the identity server or
not.

If the 3PID is hashed, the identity server could not determine the address
unless it has already seen that address in plain-text during a previous call of
the /bind mechanism (without significant resources to reverse the hashes).

This proposal thus calls for the Identity Service API's /lookup endpoint to use
a back-and-forth mechanism of passing partial hashed 3PIDs instead of their
plain-text counterparts, which should leak mess less data to either party.

## Proposal

This proposal suggests making changes to the Identity Service API's lookup
endpoints. Instead of the `/lookup` and `/bulk_lookup` endpoints, this proposal
replaces them with endpoints `/lookup` and `/lookup_hashes`. Additionally, the
endpoints should be on a `v2` path, to avoid confusion with the original
`/lookup`. We also drop the `/api` in order to preserve consistency across
other endpoints:

- `/_matrix/identity/v2/lookup`
- `/_matrix/identity/v2/lookup_hashes`

A third endpoint is added for clients to request information about the form
the server expects hashes in.

- `/_matrix/identity/v2/hash_details`

The following back-and-forth occurs between the client and server.

Let's say the client wants to check the following 3PIDs:

    alice@example.com
    bob@example.com
    carl@example.com
    +1 234 567 8910
    denny@example.com

The client will hash each 3PID as a concatenation of the medium and address,
separated by a space and a pepper appended to the end. Note that phone numbers
should be formatted as defined by
https://matrix.org/docs/spec/appendices#pstn-phone-numbers, before being
hashed). First the client must prepend the medium to the address:

     "alice@example.com" -> "email alice@example.com"
     "bob@example.com"   -> "email bob@example.com"  
     "carl@example.com"  -> "email carl@example.com" 
     "+1 234 567 8910"   -> "msisdn 12345678910"     
     "denny@example.com" -> "email denny@example.com"

Hashes must be peppered in order to reduce both the information a client gains
during the process, and attacks the identity server can perform (namely sending
a rainbow table of hashes back in the response to `/lookup`).

In order for clients to know the pepper and hashing algorithm they should use,
Identity Servers must make the information available on the `/hash_details`
endpoint:

    GET /_matrix/identity/v2/hash_details

    {
      "lookup_pepper": "matrixrocks",
      "algorithms": ["sha256"]
    }

The name `lookup_pepper` was chosen in order to account for pepper values being
returned for other endpoints in the future. The contents of `lookup_pepper`
MUST match the regular expression `[a-zA-Z0-9]*`.

    The client should append the pepper to the end of the 3pid string before
    hashing.

    "email alice@example.com" -> "email alice@example.commatrixrocks"
    "email bob@example.com"   -> "email bob@example.commatrixrocks"  
    "email carl@example.com"  -> "email carl@example.commatrixrocks" 
    "msisdn 12345678910"      -> "msisdn 12345678910matrixrocks"     
    "email denny@example.com" -> "email denny@example.commatrixrocks"

Clients SHOULD request this endpoint each time before performing a lookup, to
handle identity servers which may rotate their pepper values frequently.
Clients MUST choose one of the given hash algorithms to encrypt the 3PID during
lookup.

Note that possible hashing algorithms will be defined in the Matrix
specification, and an Identity Server can choose to implement one or all of
them. Later versions of the specification may deprecate algorithms when
necessary. Currently the only listed hashing algorithm is SHA-256 as defined by
[RFC 4634](https://tools.ietf.org/html/rfc4634) and Identity Servers and
clients MUST agree to its use with the string `sha256`. SHA-256 was chosen as
it is currently used throughout the Matrix spec, as well as its properties of
being quick to hash. While this reduces the resources necessary to generate a
rainbow table for attackers, a fast hash is necessary if particularly slow
mobile clients are going to be hashing thousands of contact details.

When performing a lookup, the pepper and hashing algorithm the client used must
be part of the request body. If they do not match what the server has on file
(which may be the case if the pepper was changed right after the client's
request for it), then the server must inform the client that they need to query
the hash details again, instead of just returning an empty response, which
clients would assume to mean that no contacts are registered on that identity
server.

If the algorithm does not match the server's, the server should return a `400
M_INVALID_PARAM`. If the pepper does not match the server's, the server should
return a new error code, 400 `M_INVALID_PEPPER`. A new error code is not
defined for an invalid algorithm as that is considered a client bug.

Each of these error responses should contain the correct `algorithm` and
`lookup_pepper` fields. This is to prevent the client from needing to query
`/hash_details` again, thus saving a round-trip. An example response to an
incorrect pepper would be:

    {    
      "error": "Incorrect value for lookup_pepper",
      "errcode": "M_INVALID_PEPPER",
      "algorithm": "sha256",
      "lookup_pepper": "matrixrocks"
    }

Now comes time for the lookup. Note that the resulting hash digest MUST be
encoded in URL-safe unpadded base64 (similar to [room version 4's event
IDs](https://matrix.org/docs/spec/rooms/v4#event-ids)). Once hashing has been
performed using the defined hashing algorithm, the client sends the first `k`
characters of each hash in an array, deduplicating any matching entries.

`k` is a value chosen by the client. It is a tradeoff between leaking the
hashes of 3PIDs that the Identity Server doesn't know about, and the amount of
hashing the server must perform. In addition to k, the client can also set a
`max_k` that it is comfortable with. The recommended values are `k = 4` and
`max_k = 6` (see below for the reasoning behind this). Let's say the client
chooses these values.

    NOTE: Example digests, not real hash values.

    "email alice@example.commatrixrocks" -> "70b1b5637937ab99f6aad01f694b3665541a5b9cbdfe54880462b3f1ad35d1f4"
    "email bob@example.commatrixrocks"   -> "21375b56a47c2cdc41a0596549a16ec51b64d26eb47b8e915d45b18ed17b72ff"
    "email carl@example.commatrixrocks"  -> "758afda64cb6a86ee6d540fa7c8b803a2479863e369cbafd71ffd376beef5d5f"
    "msisdn 12345678910matrixrocks"      -> "21375b3f1b61c975b13c8cecd6481a82e239e6aad644c29dc815836188ae8351"
    "email denny@example.commatrixrocks" -> "70b1b5637937ab9846a94a8015e12313643a2f5323ca8f5b4ed6982fc8c3619b"

    Also note that pairs (bob@example.com, 12345678910) and (alice@example.com,
    denny@example.com) have the same leading characters in their hashed
    representations.

    POST /_matrix/identity/v2/lookup

    {
      "hashes": [
        "70b1",
        "2137",
        "758a"
      ],
      "algorithm": "sha256",
      "pepper": "matrixrocks"
    }

The identity server, upon receiving these partial hashes, can see that the
client chose `4` as its `k` value, which is the length of the shortest hash
prefix. The identity server has a "minimum k", which is a function of the
amount of 3PID hashes it currently holds and protects it against computing too
many per lookup. Let's say the Identity Server's `min_k = 5` (again, see below
for details). 

The client's `k` value (4) is less than the Identity Server's `min_k` (5), so
it will reject the lookup with the following error:

    {
      "errcode": "M_HASH_TOO_SHORT",
      "error": "Sent partial hashes are too short",
      "minimum_length": "5"
    }

The client then knows it must send values of at least length 5. It's `max_k` is
6, so this is fine. The client sends the values again with `k = 5`:

    POST /_matrix/identity/v2/lookup

    {
      "hashes": [
        "70b1b",
        "21375",
        "758af"
      ],
      "algorithm": "sha256",
      "pepper": "matrixrocks"
    }

The Identity Server sees the hashes are within an acceptable length (5 >= 5),
then checks which hashes it knows of that match the given leading values. It
will then return the next few characters (`n`; implementation-specific; lower
means less information leaked to clients at the result of potentially more
hashing to be done) of each that match:

    The identity server found the following hashes that contain the leading
    characters:

    70b1b5637937ab99f6aad01f694b3665541a5b9cbdfe54880462b3f1ad35d1f4
    70b1b1b28dcfcc179a54983f46e1753c3fcdb0884d06fad741582c0180b56fc9
    21375b3f1b61c975b13c8cecd6481a82e239e6aad644c29dc815836188ae8351

    And if n = 7, the identity server will send back the following payload:

    {
      "hashes": {
        "70b1b": ["5637937", "1b28dcf"],
        "21375": ["b3f1b61"]
      }
    }

The client can then deduce which hashes actually lead to Matrix IDs. In this
case, `70b1b5637937` are the leading characters of "alice@example.com" and
"denny@example.com", while `21375b3f1b61` are the leading characters of
"+12345678910" and `70b1b1b28dcf` does not match any of the hashes the client
has locally, so it is ignored. "bob@example.com" and "carl@example.com" do not
seem to have Matrix IDs associated with them.

Finally, the client salts and hashes 3PID hashes that it believes are
associated with Matrix IDs and sends them to the identity server on the
`/lookup_hashes` endpoint. Instead of hashing the 3PIDs again, clients should
reuse the peppered hash that was previously sent to the server. Salting is
performed to prevent an identity server generating a rainbow table to reverse
any non-Matrix 3PIDs that slipped in. Salts MUST match the regular expression
`[a-zA-Z0-9]*`.

    Computed previously:

    "email alice@example.commatrixrocks"
    becomes
    "70b1b5637937ab99f6aad01f694b3665541a5b9cbdfe54880462b3f1ad35d1f4"

    The client should generate a salt. Let's say it generates "salt123". This
    value is appended to the hash.

    "70b1b5637937ab99f6aad01f694b3665541a5b9cbdfe54880462b3f1ad35d1f4"
    becomes
    "70b1b5637937ab99f6aad01f694b3665541a5b9cbdfe54880462b3f1ad35d1f4salt123"

    And then hashed:

    "70b1b5637937ab99f6aad01f694b3665541a5b9cbdfe54880462b3f1ad35d1f4salt123"
    becomes
    "1f64ed6ac9d6da86b65bcc68a39c7c4d083f77193ec7e5adc4b09617f8d0d81a"

A new salt is generated per **hash prefix** and applied to each hash
individually. Doing so requires the identity server to only rehash the 3PIDs
whose unsalted hashes matched the earlier prefixes (in the case of `70b1b`,
hashes `5637937...`  and `1b28dcf...`). This adds only a small multiplier of
additional hashes needing to be performed by the Identity Server (the median
number of hashes that fit each prefix, a function of the chosen `k` value).

An attacker would now need to create a new rainbow table per hash prefix, per
lookup. This reduces the attack surface significantly to only very targeted
attacks.

    POST /_matrix/identity/v2/lookup_hashes

    {
      "hashes": {
        "70b1b": {
          "1": "1f64ed6ac9d6da86b65bcc68a39c7c4d083f77193ec7e5adc4b09617f8d0d81a", 
          "2": "a32e1c1f3b9e118eab196b0807443871628eace587361b7a02adfb2b77b8d620"
        },
        "21375": {
          "1": "372bf27a4e7e952d1e794f78f8cdfbff1a3ab2f59c6d44e869bfdd7dd1de3948"
        }
      },
      "salts": {
        "70b1b": "salt123",
        "21375": "salt234"
      }
    }

The server reads the prefixes and only rehashes those 3PIDs that match these
hashes (being careful to continue to enforce its `min_k` requirement), and
returns them:

    {
      "mappings": {
        "70b1b": {
          "2": "@alice:example.com"
        },
        "21375": {
          "1": "@fred:example.com"
        }
      }
    }

The client can now display which 3PIDs link to which Matrix IDs.

### How to pick k

The `k` value is a tradeoff between the privacy of the user's contacts, and the
resource-intensiveness of lookups for the identity server. Clients would rather
have a smaller `k`, while servers a larger `k`. A larger `k` also allows the
identity server to learn more about the contacts the client has that are not
Matrix users. Ideally we'd like to balance these two, and with the value also
being a factor of how many records an identity server has, there's no way to
simply give a single `k` value that should be used from the spec.

Instead, we can have the client and identity server decide it amongst
themselves. The identity server should pick a `k` value based on how many 3PIDs
records they have, and thus how much hashes they will need to perform. An ideal
value can be calculated from the following function:

    C <= N / (64 ^ k)

    Where N is the number of 3PID records an identity server has, k is the number of
    characters to truncate each hash to, and C is the median number of hashing rounds
    an identity server will need to perform per hash (denoted complexity). 64 is the
    number of possible characters per byte in a hash, as hash digests are encoded in
    url-safe base64.

    Identity servers should choose a complexity value they're comfortable with.
    Let's say 5 (for reference, HIBP's service has set their k value for a complexity
    of 478: https://blog.cloudflare.com/validating-leaked-passwords-with-k-anonymity/)

    When C is set (implementation specific), k can then be solved for:

    k >= - log(C/N)
         ----------
         - log(64)
         
    Taking HIBP's amount of passwords as an example, 600,000,000, as N and solving for k, we get:
    
    k >= 4.47
    
    We round k to 5 for it to be a whole number.
    
    As this is quite a lot of records, we advise clients to start with k = 4, and go from there.
    
    For reference, a very small identity server with only 600 records would produce a
    minimum k of 0.628, or 1.
    
    From this we can see that even low k values scale to quite a lot of records.

Clients themselves should pick a reasonable default `k`, and a maximum value
that they are comfortable extending towards if the identity server requests a
higher minimum number. If the identity server requests too high of a minimum
number, clients will need to inform the user, either with an error message, or
more advanced clients could allow users to tweak their k values.

---

Past what they already knew, from this exchange the client and server have learned:

Client:

* Unsalted, peppered partial 3PID hash "70b1b1b28dcf"
  of some matrix user
  (harder to crack, and new rainbow table needed)
* alice@example.com -> @alice:example.com (required)
* +1 234 567 8910 -> @fred:example.com (required)

Server:

* Partial hash "758af" (likely useless)
* The server knows some salted hash
  70b1b5637937ab9846a94a8015e12313643a2f5323ca8f5b4ed6982fc8c3619bf
  (crackable, new rainbow table needed)

---

No parameter changes will be made to /bind.

## Fallback considerations

`v1` versions of these endpoints may be disabled at the discretion of the
implementation, and should return a 403 `M_FORBIDDEN` error if so.

If an identity server is too old and a HTTP 404, 405 or 501 is received when
accessing the `v2` endpoint, they should fallback to the `v1` endpoint instead.
However, clients should be aware that plain-text 3PIDs are required, and SHOULD
ask for user consent to send 3PIDs in plain-text, and be clear about where they
are being sent to.

## Tradeoffs

* There is a small cost incurred by performing hashes before requests, but this
  is outweighed by the privacy implications of sending plain-text addresses.
* Identity services will need to perform a lot of hashing, however with
  authentication being added in MSC 2140, effective rate-limiting is possible.

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

Bloom filters are an alternative method of providing private contact discovery.
However, they do not scale well due to requiring clients to download a large
filter that needs updating every time a new bind is made. Further considered
solutions are explored in https://signal.org/blog/contact-discovery/. Signal's
eventual solution of using Software Guard Extensions (detailed in
https://signal.org/blog/private-contact-discovery/) is considered impractical
for a federated network, as it requires specialized hardware.

While a bit out of scope for this MSC, there has been debate over preventing
3PIDs as being kept as plain-text on disk. The argument against this was that
if the hashing algorithm (in this case SHA-256) was broken, we couldn't update
the hashing algorithm without having the plain-text 3PIDs. @lampholder helpfully
added that we could just take the old hashes and rehash them in the more secure
hashing algorithm, thus transforming the hash from SHA-256 to
SHA-256+SomeBetterAlg. However @erikjohnston then pointed out that if
`BrokenAlgo(a) == BrokenAlgo(b)` then `SuperGreatHash(BrokenAlgo(a)) ==
SuperGreatHash(BrokenAlgo(b))`, so all you'd need to do is find a match in the
broken algo, and you'd break the new algorithm as well. This means that you
would need the plain-text 3PIDs to encode a new hash, and thus storing them
hashed on disk would require a transition period where 3PIDs were reuploaded in
a strong hash variant.

## Conclusion

This proposal outlines an effective method to stop bulk collection of user's
contact lists and their social graphs without any disastrous side effects. All
functionality which depends on the lookup service should continue to function
unhindered by the use of hashes.
