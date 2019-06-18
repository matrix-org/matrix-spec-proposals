# MSC2134: Identity Hash Lookups

[Issue #2130](https://github.com/matrix-org/matrix-doc/issues/2130) has been
recently created in response to a security issue brought up by an independent
party. To summarise the issue, lookups (of matrix user ids) are performed using
non-hashed 3pids (third-party IDs) which means that the identity server can
identify and record every 3pid that the user wants to check, whether that
address is already known by the identity server or not.

If the 3pid is hashed, the identity service could not determine the address
unless it has already seen that address in plain-text during a previous call of
the /bind mechanism.

Note that in terms of privacy, this proposal does not stop an identity service
from mapping hashed 3pids to users, resulting in a social graph. However, the
identity of the 3pid will at least remain a mystery until /bind is used.

This proposal thus calls for the Identity Service’s /lookup API to use hashed
3pids instead of their plain-text counterparts.

## Proposal

This proposal suggests making changes to the Identity Service API's lookup
endpoints. Due to the nature of this proposal, the new endpoints should be on a
`v2` path (we also drop the `/api` in order to preserve consistency across
other endpoints):

- `/_matrix/identity/v2/lookup`
- `/_matrix/identity/v2/bulk_lookup`

The parameters will remain the same, but `address` should no longer be in a
plain-text format. `address` will now take a hash value, and the resulting
digest should be encoded in unpadded base64. For example:

```python
address = "user@example.org"
salt = "matrix"
digest = hashlib.sha256((salt + address).encode()).digest()
result_address = unpaddedbase64.encode_base64(digest)
print(result_address)
CpvOgBf0hFzdqZD4ASvWW0DAefErRRX5y8IegMBO98w
```

### Example request

SHA-256 has been chosen as it is [currently used
elsewhere](https://matrix.org/docs/spec/server_server/r0.1.2#adding-hashes-and-signatures-to-outgoing-events)
in the Matrix protocol. Additionally a hardcoded salt (“matrix” or something)
must be prepended to the data before hashing in order to serve as a weak
defense against existing rainbow tables. As time goes on, this algorithm may be
changed provided a spec bump is performed. Then, clients making a request to
`/lookup` must use the hashing algorithm defined in whichever version of the CS
spec they and the IS have agreed to speaking.

No parameter changes will be made to /bind, but identity services should keep a
hashed value for each address it knows about in order to process lookups
quicker. It is the recommendation that this is done during the act of binding.

`v1` versions of these endpoints may be disabled at the discretion of the
implementation, and should return a `M_FORBIDDEN` `errcode` if so.


## Tradeoffs

* This approach means that the client now needs to calculate a hash by itself, but the belief
  is that most languages provide a mechanism for doing so.
* There is a small cost incurred by doing hashes before requests, but this is outweighed by
  the privacy implications of sending plain-text addresses.

## Potential issues

This proposal does not force an identity service to stop handling plain-text
requests, because a large amount of the matrix ecosystem relies upon this
behavior. However, a conscious effort should be made by all users to use the
privacy respecting endpoints outlined above. Identity services may disallow use
of the v1 endpoint.

Unpadded base64 has been chosen to encode the value due to its ubiquitous
support in many languages, however it does mean that special characters in the
address will have to be encoded when used as a parameter value.

## Other considered solutions

Ideally identity servers would never receive plain-text addresses, however it
is necessary for the identity server to send an email/sms message during a
bind, as it cannot trust a homeserver to do so as the homeserver may be lying.
Additionally, only storing 3pid hashes at rest instead of the plain-text
versions is impractical if the hashing algorithm ever needs to be changed.

Bloom filters are an alternative method of providing private contact discovery, however does not scale well due to clients needing to download a large filter that needs updating every time a new bind is made. Further considered solutions are explored in https://signal.org/blog/contact-discovery/ Signal's eventual solution of using SGX is considered impractical for a Matrix-style setup.

## Security considerations

None

## Conclusion

This proposal outlines an effective method to stop bulk collection of user's
contact lists and their social graphs without any disastrous side effects. All
functionality which depends on the lookup service should continue to function
unhindered by the use of hashes.

