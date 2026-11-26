# Exactly 256 bits for m.secret_storage.v1.aes-hmac-sha2

[MSC2472: Symmetric SSSS](https://github.com/matrix-org/matrix-spec-proposals/pull/2472)
specified a secret storage method `m.secret_storage.v1.aes-hmac-sha2` and stated
"With this method, the Secret Storage key may be any size (though 256 bits is
recommended)".

For passphrase, it also specified "an optional `bits` parameter that defaults to
256, and indicates the number of bits that should be generated from PBKDF2 (in
other words, the size of the key)."

Additionally, the `AesHmacSha2KeyDescription` specified in [section 10.13.1.1.1
m.secret_storage.v1.aes-hmac-sha2
](https://spec.matrix.org/v1.19/client-server-api/#msecret_storagev1aes-hmac-sha2)
of the spec makes the `iv` and `mac` properties optional. If these properties
are omitted, it is impossible for clients to check whether a particular key is
correct and give the user feedback.

This means that it is possible to specify short keys (e.g. 8 bits) that are easy
to brute-force. A malicious server could delete secrets and replace passphrase
metadata, specifying a small `bits` value and missing out `iv` and `mac`, thus
persuading a spec-compliant client to generate a weak key and upload secrets
using that key.

Note: a survey of the most popularly-used clients indicated that none of them
were actually vulnerable to this type of attack, since they all ignore the
`bits` value and unconditionally use 256 bits.

We propose:

* mandating a key length of 256 in `m.secret_storage.v1.aes-hmac-sha2`,
* making `iv` and `mac` required properties of `AesHmacSha2KeyDescription`,
* removing `bits` from passphrase.

## Proposal

* When using the `m.secret_storage.v1.aes-hmac-sha2` algorithm clients MUST
  generate a key of length 256 bits. If clients encounter existing keys that are
  not 256 bits (e.g. if a user provides such a key when asked), they MUST
  consider them invalid and SHOULD encourage the user to generate a new key.
* In `AesHmacSha2KeyDescription`, `iv` and `mac` become required properties. If
  clients find an existing key without these properties, they MUST consider the
  key invalid. They SHOULD warn the user and encourage them to generate a new
  key.
* When using the `m.pbkdf2` algorithm to derive a key from a passphrase, clients
  MUST generate a key with the number of bits corresponding to the algorithm
  (i.e. 256 bits). They MUST omit the `bits` property from the `passphrase`
  property.
* If clients receive `m.pbkdf2` passphrase metadata that includes the `bits`
  property, they MUST behave as if the `bits` property were unset.

## Potential issues

None known, except that there may be keys in the wild of different lengths,
which should be handled as described above. This may force users to regenerate
their secret storage keys.

## Alternatives

### Do nothing

Doing nothing leaves a security vulnerability in place for clients that
implement the spec. (We have checked several clients and not yet found one that
actually has this vulnerability, since they do not comply with the spec on this
point.)

### Specify a minimum length

We could state a minimum length for the key, perhaps 256, and allow clients to
use longer lengths if they prefer.

However, we prefer to be explicit and exact in security-critical code and
suggest that if a longer key length is required, this should be done using a new
algorithm rather than a parameter on this algorithm.
