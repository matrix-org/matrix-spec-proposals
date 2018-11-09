# MSC1714: using the TLS private key to sign federation-signing keys

Matrix servers use an ed25519 keypair (the "signing key") to sign events in a
room and federation requests. This is intended to prevent malicious servers
from masquerading as other servers, which might allow them to forge content and
access data they should not otherwise be able to.

Remote servers must be able to confirm that a given signing key actually
belongs to a given server. One way to do this is simply to ask the target
server over a secure HTTPS connection; however, we also need to verify keys
used in the past by servers which are no longer online.

In theory, this is currently done using an approach borrowed from the
[Perspectives
project](https://web.archive.org/web/20170702024706/https://perspectives-project.org/),
which involves asking a number of notary servers for a copy of the key, and
checking that they agree. However, in practice we have ended up in a situation
where almost every Matrix homeserver uses `matrix.org` as its sole notary. This
means that `matrix.org` is therefore a single, centralised, trusted point in
the federation.

[MSC1711](https://github.com/matrix-org/matrix-doc/pull/1711) discusses the
problems with the Perspectives approach in more detail. This proposal suggests
an alternative approach to the management of signing keys.

## Proposal

In brief, the proposed solution is to have the origin server (server A)
cross-sign its signing keys with the private key it uses for HTTPS connections
on the federation port. Intermediate servers (server B) keep a copy of this
signature, so that when a new server (server C) needs to validate the signing
key, it can use the certificate chain to confirm that it belonged to server A.

Each server therefore maintains a list of the signing keys it has seen for each
remote server, and the time it believes they are valid for. (It must also
retain copies of the certificate chain that it used to reach that conclusion.)

### Extending the signature algorithm to cover RSA keys

It is likely that the TLS key in use will be an RSA key, so we need to extend
the [JSON signing
format](https://matrix.org/docs/spec/appendices.html#signing-details) to cover
the use of RSA keys.

We propose:
* The *signing algorithm* identifier should be `rsa`.
* The *key identifier* should be the `sha1` hash of the `DER` encoding of the
  public key.
* The *signature* should be the RSA signature of the `sha256` hash of the
  input, encoded with unpadded Base64.

It is also possible to use other algorithms such as secp256k1 for TLS. We
propose that these not be supported for now.

### Extending the `/_matrix/key/v2/server` response

The REST endpoint for requesting a public signing key is [`GET
/_matrix/key/v2/server/{keyId}`](https://matrix.org/docs/spec/server_server/unstable.html#get-matrix-key-v2-server-keyid).
This returns the requested key, the server name, and validity period (as well
as a bunch of other stuff not entirely relevant here), all signed by the
key. To this we add a signature by the TLS key. The response would therefore
look like this (eliding irrelevant fields):

```json
{
  "server_name": "example.org",
  "verify_keys": {
    "ed25519:abc123": {
      "key": "VGhpcyBzaG91bGQgYmUgYSByZWFsIGVkMjU1MTkgcGF5bG9hZA"
    }
  },
  "signatures": {
    "example.org": {
      "ed25519:abc123": "VGhpcyBzaG91bGQgYWN0dWFsbHkgYmUgYSBzaWduYXR1cmU",
      "rsa:df88cf5955704d6e0d21feb6662c87a070db4b01": "pfUHoNUX4CNA+EUhGZDW9w1ngjuODKGTLLdwZpGCCgmPgV/QGy93Myn8XNAyQ..."
    }
  },
  "valid_until_ts": 1652262000000
}
```

When the requesting server receives this response, it uses the public key from
the TLS certificate to validate the signature.

### Extending the `/_matrix/key/v2/query` response

When a notary server returns the keys for another server, it must include the
complete certificate chain alongside the keys.

The response to either [GET /_matrix/key/v2/query/{serverName}/{keyId}](https://matrix.org/docs/spec/server_server/unstable.html#get-matrix-key-v2-query-servername-keyid)
or [POST /_matrix/key/v2/query](https://matrix.org/docs/spec/server_server/unstable.html#post-matrix-key-v2-query)
will therefore look like:

```json
{
  "server_keys": [
    {
      "server_name": "example.org",
      "verify_keys": {
        "ed25519:abc123": {
          "key": "VGhpcyBzaG91bGQgYmUgYSByZWFsIGVkMjU1MTkgcGF5bG9hZA"
        }
      },
      "signatures": {
        "example.org": {
          "ed25519:abc123": "VGhpcyBzaG91bGQgYWN0dWFsbHkgYmUgYSBzaWduYXR1cmU",
          "rsa:df88cf5955704d6e0d21feb6662c87a070db4b01": "pfUHoNUX4CNA+EUhGZDW9w1ngjuODKGTLLdwZpGCCgmPgV/QGy93Myn8XNAyQ..."
        }
      },
      "valid_until_ts": 1652262000000
    }
  ],
  "additional_certificates": [
"-----BEGIN CERTIFICATE-----
MIIHIzCCBgugAwIBAgISA+UZe4LyoLxziTfqbd/0D87vMA0GCSqGSIb3DQEBCwUA
MEoxCzAJBgNVBAYTAlVTMRYwFAYDVQQKEw1MZXQncyBFbmNyeXB0MSMwIQYDVQQD
ExpMZXQncyBFbmNyeXB0IEF1dGhvcml0eSBYMzAeFw0xODA5MTgwMDU2NDJaFw0x
ODEyMTcwMDU2NDJaMBgxFjAUBgNVBAMTDW1haWwuc3cxdi5vcmcwggIiMA0GCSqG
SIb3DQEBAQUAA4ICDwAwggIKAoICAQC6NrmFIQEbzC0An676DnDrfd5P0s0rzRY6
+TOCRbxYZVgIqzcLJze0ca2UywZ312VEAsuPDvAcnfi6Ej6xv/sizsUyGIy83nPp
qNrkiBlHS8cILVtTbVyt+ZJgU81+oyZPQG7a3dewXh9ZKim4vwWVLLJC6676t7YL
Ksfx97bbgh4xb0LaffI7fJLDH0aelV88asNmAXBsjEnNhpEriib+vxliHs79kw/2
HOP7DGTc2pxET8i6mJvgIP86aKZyaJze70oH9F5AaL3MBdtRxusYhcxNftbvb569
tX+6hN1rmsq7c1DIrHIz9sXfUFWa+qL+j8rVX19uZtSfDuznQ1g0pQAQW6ow4HxZ
zMzXW1PrrYYGF+S3lh5ozJIrbkmNCTaeiocKx5gamNZ/DchIqHB2pY3EO7UwU7Hn
8iquOoUr/QC5joq+qjYscH8LGlC0RlgU0ZdeyDeIvZreu8UYjYxfL+GuyTp5e6py
fyEpyTwMPJGkCz9Qn6iUWhRpxgAqVFbdQEO8FY4SwAdqr1JVbhcgMyudGO/ofub7
CjPNzEBT0Hz05ihW4DDoOMYXB7VGqKnnjyIKIN6bvs8ztqm//soYJaeFL71c9z8G
CGbhlImrATZe2C0qg/S9NhWUr+ESG7D7UpwK+iMPuVf+o6e+dq9/Td3rrtFpN2r1
B2lJIbFBTwIDAQABo4IDMzCCAy8wDgYDVR0PAQH/BAQDAgWgMB0GA1UdJQQWMBQG
CCsGAQUFBwMBBggrBgEFBQcDAjAMBgNVHRMBAf8EAjAAMB0GA1UdDgQWBBSgPe8H
gzqEX7m0wOqKOJVr6GZVBjAfBgNVHSMEGDAWgBSoSmpjBH3duubRObemRWXv86js
oTBvBggrBgEFBQcBAQRjMGEwLgYIKwYBBQUHMAGGImh0dHA6Ly9vY3NwLmludC14
My5sZXRzZW5jcnlwdC5vcmcwLwYIKwYBBQUHMAKGI2h0dHA6Ly9jZXJ0LmludC14
My5sZXRzZW5jcnlwdC5vcmcvMDYGA1UdEQQvMC2CDWltYXAuc3cxdi5vcmeCDW1h
aWwuc3cxdi5vcmeCDXNtdHAuc3cxdi5vcmcwgf4GA1UdIASB9jCB8zAIBgZngQwB
AgEwgeYGCysGAQQBgt8TAQEBMIHWMCYGCCsGAQUFBwIBFhpodHRwOi8vY3BzLmxl
dHNlbmNyeXB0Lm9yZzCBqwYIKwYBBQUHAgIwgZ4MgZtUaGlzIENlcnRpZmljYXRl
IG1heSBvbmx5IGJlIHJlbGllZCB1cG9uIGJ5IFJlbHlpbmcgUGFydGllcyBhbmQg
b25seSBpbiBhY2NvcmRhbmNlIHdpdGggdGhlIENlcnRpZmljYXRlIFBvbGljeSBm
b3VuZCBhdCBodHRwczovL2xldHNlbmNyeXB0Lm9yZy9yZXBvc2l0b3J5LzCCAQQG
CisGAQQB1nkCBAIEgfUEgfIA8AB2AMEWSuCnctLUOS3ICsEHcNTwxJvemRpIQMH6
B1Fk9jNgAAABZepk2FsAAAQDAEcwRQIhAPktfD8mbtvBwnCzoRY9bIeSltkPeX5d
EghHgC5UTYPFAiBtOlV1hAR72B+SWNT96ekLCPTRlnN2Z5ipmYd/FuSL/QB2ACk8
UZZUyDlluqpQ/FgH1Ldvv1h6KXLcpMMM9OVFR/R4AAABZepk2N4AAAQDAEcwRQIg
F3zx9U/eV7sQs5Civ4iMaY57aCZxsvymHL8PFPB2w4kCIQDeD9nIgQUuUWmDpPpW
3qyLV+MkT4EmEm6nXgWw/bfSGzANBgkqhkiG9w0BAQsFAAOCAQEAY/kY12CN90Y9
f83CQXxa+1ecI0iLK1VNec52cBhR4am7hmAZs4C4EGWPm7XSQH14UJbXuNS6jTd1
n/eMlz/U5+LmkV5sB2knSIywHC+kKFADjCOGk5FIZihCv1Q3dtW2l9U6mBqKswvN
O4nIXyer0XzEzq9LdOZ5QTeoAUUfQBjOHOUbV2rMk+kKm+zY26MBrkx6PKkNm68l
rJ7r96V4ML9R504090hLOfw54SkRhFDImDHqwn4nsQ8NxdDegPBVVi+WY+OIvAur
fU58EBL6OZP8RMnmH3s9qbU52mUfMVVzPtv4JQJvCZgESZR2p06qTbrpG20t+dbq
1Kl/BZOLmA==
-----END CERTIFICATE-----",
"-----BEGIN CERTIFICATE-----
MIIHIzCCBgugAwIBAgISA+UZe4LyoLxziTfqbd/0D87vMA0GCSqGSIb3DQEBCwUA
MEoxCzAJBgNVBAYTAlVTMRYwFAYDVQQKEw1MZXQncyBFbmNyeXB0MSMwIQYDVQQD
ExpMZXQncyBFbmNyeXB0IEF1dGhvcml0eSBYMzAeFw0xODA5MTgwMDU2NDJaFw0x
ODEyMTcwMDU2NDJaMBgxFjAUBgNVBAMTDW1haWwuc3cxdi5vcmcwggIiMA0GCSqG
SIb3DQEBAQUAA4ICDwAwggIKAoICAQC6NrmFIQEbzC0An676DnDrfd5P0s0rzRY6
+TOCRbxYZVgIqzcLJze0ca2UywZ312VEAsuPDvAcnfi6Ej6xv/sizsUyGIy83nPp
qNrkiBlHS8cILVtTbVyt+ZJgU81+oyZPQG7a3dewXh9ZKim4vwWVLLJC6676t7YL
Ksfx97bbgh4xb0LaffI7fJLDH0aelV88asNmAXBsjEnNhpEriib+vxliHs79kw/2
HOP7DGTc2pxET8i6mJvgIP86aKZyaJze70oH9F5AaL3MBdtRxusYhcxNftbvb569
tX+6hN1rmsq7c1DIrHIz9sXfUFWa+qL+j8rVX19uZtSfDuznQ1g0pQAQW6ow4HxZ
zMzXW1PrrYYGF+S3lh5ozJIrbkmNCTaeiocKx5gamNZ/DchIqHB2pY3EO7UwU7Hn
8iquOoUr/QC5joq+qjYscH8LGlC0RlgU0ZdeyDeIvZreu8UYjYxfL+GuyTp5e6py
fyEpyTwMPJGkCz9Qn6iUWhRpxgAqVFbdQEO8FY4SwAdqr1JVbhcgMyudGO/ofub7
CjPNzEBT0Hz05ihW4DDoOMYXB7VGqKnnjyIKIN6bvs8ztqm//soYJaeFL71c9z8G
CGbhlImrATZe2C0qg/S9NhWUr+ESG7D7UpwK+iMPuVf+o6e+dq9/Td3rrtFpN2r1
B2lJIbFBTwIDAQABo4IDMzCCAy8wDgYDVR0PAQH/BAQDAgWgMB0GA1UdJQQWMBQG
CCsGAQUFBwMBBggrBgEFBQcDAjAMBgNVHRMBAf8EAjAAMB0GA1UdDgQWBBSgPe8H
gzqEX7m0wOqKOJVr6GZVBjAfBgNVHSMEGDAWgBSoSmpjBH3duubRObemRWXv86js
oTBvBggrBgEFBQcBAQRjMGEwLgYIKwYBBQUHMAGGImh0dHA6Ly9vY3NwLmludC14
My5sZXRzZW5jcnlwdC5vcmcwLwYIKwYBBQUHMAKGI2h0dHA6Ly9jZXJ0LmludC14
My5sZXRzZW5jcnlwdC5vcmcvMDYGA1UdEQQvMC2CDWltYXAuc3cxdi5vcmeCDW1h
aWwuc3cxdi5vcmeCDXNtdHAuc3cxdi5vcmcwgf4GA1UdIASB9jCB8zAIBgZngQwB
AgEwgeYGCysGAQQBgt8TAQEBMIHWMCYGCCsGAQUFBwIBFhpodHRwOi8vY3BzLmxl
dHNlbmNyeXB0Lm9yZzCBqwYIKwYBBQUHAgIwgZ4MgZtUaGlzIENlcnRpZmljYXRl
IG1heSBvbmx5IGJlIHJlbGllZCB1cG9uIGJ5IFJlbHlpbmcgUGFydGllcyBhbmQg
b25seSBpbiBhY2NvcmRhbmNlIHdpdGggdGhlIENlcnRpZmljYXRlIFBvbGljeSBm
b3VuZCBhdCBodHRwczovL2xldHNlbmNyeXB0Lm9yZy9yZXBvc2l0b3J5LzCCAQQG
CisGAQQB1nkCBAIEgfUEgfIA8AB2AMEWSuCnctLUOS3ICsEHcNTwxJvemRpIQMH6
B1Fk9jNgAAABZepk2FsAAAQDAEcwRQIhAPktfD8mbtvBwnCzoRY9bIeSltkPeX5d
EghHgC5UTYPFAiBtOlV1hAR72B+SWNT96ekLCPTRlnN2Z5ipmYd/FuSL/QB2ACk8
UZZUyDlluqpQ/FgH1Ldvv1h6KXLcpMMM9OVFR/R4AAABZepk2N4AAAQDAEcwRQIg
F3zx9U/eV7sQs5Civ4iMaY57aCZxsvymHL8PFPB2w4kCIQDeD9nIgQUuUWmDpPpW
3qyLV+MkT4EmEm6nXgWw/bfSGzANBgkqhkiG9w0BAQsFAAOCAQEAY/kY12CN90Y9
f83CQXxa+1ecI0iLK1VNec52cBhR4am7hmAZs4C4EGWPm7XSQH14UJbXuNS6jTd1
n/eMlz/U5+LmkV5sB2knSIywHC+kKFADjCOGk5FIZihCv1Q3dtW2l9U6mBqKswvN
O4nIXyer0XzEzq9LdOZ5QTeoAUUfQBjOHOUbV2rMk+kKm+zY26MBrkx6PKkNm68l
rJ7r96V4ML9R504090hLOfw54SkRhFDImDHqwn4nsQ8NxdDegPBVVi+WY+OIvAur
fU58EBL6OZP8RMnmH3s9qbU52mUfMVVzPtv4JQJvCZgESZR2p06qTbrpG20t+dbq
1Kl/BZOLmA==
-----END CERTIFICATE-----"
  ]
}
```

The notary must present the certificates it used to validate each of the RSA
keys used in the signatures in the response. Of course, where certificates are
shared by multiple keys (for instance, because they are used as intermediate
certificates for a CA which has signed multiple leaf certificates), the
duplicates can be elided.

Where a server is asked for its own key, the relevant certificates will already
be present in the TLS connection (and it may be difficult for a homeserver to
obtain its own certificates), so it need not add them to the response.

### Requesting a signing key

A server which wishes to check if a given signing key belongs to a particular
server now has two options:

* If it only needs to check if a single key is currently valid (eg, because it
  needs to authenticate an incoming federation request), it can send a
  `/_matrix/key/v2/server` query to the server itself. It should use the public
  key from the TLS certificate to validate the signature in the response, and
  then clip the `valid_until_ts` according to the ranges in the certificate
  chain. It can then persist the key, together with the certificates, for
  future use.

* Alternatively, it can send a `/_matrix/key/v2/query` request to any other
  server - most likely the one which is providing the events which need
  verifying.

  It should collate the certificates in the REST response with those presented
  at the TLS level, and check that there is a valid trust path from a trusted
  root CA to a certificate for the relevant server name, using the correct RSA
  key, and use the key to validate the signature on the response. Again, the
  `valid_until_ts` should be clipped according to the timespans that the
  certificate chains are valid for.

## Potential issues

### Homeserver must have access to the private keys

Obviously, the homeserver must have access to the private RSA keys which are
used in the TLS connection. However, this can be non-trivial where the
homeserver is deployed behind a reverse-proxy<sup
id="a1">[1](#f1)</sup>.

Indeed, CDNs such as Cloudflare will often use a shared certificate for the
public TLS connection which means it is impossible to get the private keys
without paying for a premium offering. Of course, it would be possible to use
another certificate solely for signing the keys, but it is inconvenient for
administrators to have to maintain the additional certificate.

### Lack of agreement in CA roots

This approach relies on all servers in a federation to agree on a set of
trusted root certificates. For example, suppose Alice has a certificate whose
trust root is CheapCACertsInc. Bob joins a room where Alice has sent some
events, and uses Alice's certificate to verify that the keys she has used to
sign the events do in fact belong to Alice.

Charlie, however, has heard that CheapCACertsInc's security is weak, and
prefers not to trust certificates that they issue. He is now unable to
verify that the events which claim to originate from Alice's server actually
did so.

A similar situation arises if Alice used a trust root which is a certificate
that expired before Charlie joined (and Alice is no longer maintaining her
server, or has lost her private key, so there is no way to get a new
certificate).

In order to effectively participate in the room, Charlie therefore has to
accept the events which claim to come from Alice's server, but remember that he
has not validated them, and act as if Alice's server was not in the room. This
breaks assumptions currently made in server and client implementations, so
would require careful information.

Furthermore, if Charlie's server refuses to talk to Alice's server, we risk a
split-brain situation in the room.

### Revalidating unconfirmed keys

There are circumstances when a key that was not previously confirmed as
belonging to a given server could become confirmed. For example, perhaps a
certificate chain used a root which was not previously trusted, or a server
re-signs their key using a new certificate chain.

It may therefore be necessary to proactively re-check validity from time to
time.

## Acknowlegements

This proposal is based on a suggestion by @jevolk at
https://github.com/matrix-org/matrix-doc/issues/1685.

<a id="f1"/>[1] It's worth noting that [certbot](https://certbot.eff.org/), a
common client for Let's Encrypt, will, by default, use a new keypair each time
the certificate is renewed. It's possible to disable this behaviour in recent
versions though.[↩](#a1)
