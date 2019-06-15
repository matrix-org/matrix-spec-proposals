# MSC2134: Identity Hash Lookups

[Issue #2130](https://github.com/matrix-org/matrix-doc/issues/2130) has been recently
created in response to a security issue brought up by an independant party. To summarise
the issue, lookups (of matrix userids) are performed using non-hashed 3pids which means
that the 3pid is identifiable to anyone who can see the payload (e.g. willh AT matrix.org
can be identified by a human).

The problem with this, is that a malicious identity service could then store the plaintext
3pid and make an assumption that the requesting entity knows the holder of the 3pid, even
if the identity service does not know of the 3pid beforehand.

If the 3pid is hashed, the identity service could not determinethe owner of the 3pid
unless the identity service has already been made aware of the 3pid by the owner
themselves (using the /bind mechanism).

Note that this proposal does not stop a identity service from mapping hashed 3pids to many
users, in an attempt to form a social graph. However the identity of the 3pid will remain
a mystery until /bind is used.

It should be clear that there is a need to hide any address from the identity service that
has not been explicitly bound to it, and this proposal aims to solve that for the lookup API.


## Proposal

This proposal suggests making changes to the Identity Service API's lookup endpoints. Due
to the nature of this proposal, the new endpoints should be on a `v2` path:

- `/_matrix/identity/api/v2/lookup`
- `/_matrix/identity/api/v2/bulk_lookup`

The parameters will remain the same, but `address` should no longer be in a plain-text
format. Medium will now take a SHA-256 format hash value, and the resulting digest should
be encoded in base64 format. For example:

```python
address = "willh@matrix.org"
digest = hashlib.sha256(address.encode()).digest()
result_address = base64.encodebytes(digest).decode()
print(result_address)
CpvOgBf0hFzdqZD4ASvWW0DAefErRRX5y8IegMBO98w=
```

SHA-256 has been chosen as it is [currently used elsewhere](https://matrix.org/docs/spec/server_server/r0.1.2#adding-hashes-and-signatures-to-outgoing-events) in the Matrix protocol, and the only
requirement for the hashing algorithm is that it cannot be used to guess the real value of the address

No parameter changes will be made to /bind, but identity services should keep a hashed value
for each address it knows about in order to process lookups quicker and it is the recommendation
that this is done at the time of bind.

`v1` versions of these endpoints may be disabled at the discretion of the implementation, and
should return a `M_FORBIDDEN` `errcode` if so.


## Tradeoffs

* This approach means that the client now needs to calculate a hash by itself, but the belief
  is that most librarys provide a mechanism for doing so.
* There is a small cost incurred by doing hashes before requests, but this is outweighed by
  the privacy implications of sending plaintext addresses.


## Potential issues

This proposal does not force a identity service to stop handling plaintext requests, because
a large amount of the matrix ecosystem relies upon this behavior. However, a conscious effort
should be made by all users to use the privacy respecting endpoints outlined above. Identity
services may disallow use of the v1 endpoint.


## Security considerations

None

## Conclusion

This proposal outlines a quick and effective method to stop bulk collection of users contact
lists and their social graphs without any disasterous side effects. All functionality which
depends on the lookup service should continue to function unhindered by the use of hashes.