# MSCXXXX: Symmetric megolm backup
The current megolm backup is asymmetric. This was chosen so that clients without the private key can
still add their own megolm sessions to the backup. This, however, allows a homeserver admin to inject
their own malicious megolm session into someones backup and then send an encrypted message as that user.
A symmetric megolm backup would fix this attack vector. Additionally, many clients cache the megolm
private key anyways, making the original factor for choosing asymmetric encryption obsolete.

## Proposal
This proposal introduces a new megolm backup algorithm, `m.megolm_backup.v2.aes-hmac-sha2`.
It works basically the same as the encryption in symmetric SSSS. The backup method `m.megolm_backup.v1.curve25519-aes-sha2`
is deprecated and clients are expected to not use it anymore, when creating a new megolm backup. Ideally
clients would allow migration to symmetric megolm backup.

### `session_data`
The session data of the megolm backup is an object containing the `iv` property, the `ciphertext`
property and the `mac` property. Below is described how to generate these from the megolm backup key.
The data to be encoded is the same JSON-encoded data as in `m.megolm_backup.v1.curve25519-aes-sha2`.

As such, a complete `KeyBackupData` object could look as follows:

```json
{
  "first_message_index": 0,
  "forwarded_count": 0,
  "is_verified": true,
  "session_data": {
    "iv": "cL/0MJZaiEd3fNU+I9oJrw==",
    "ciphertext": "WL73Pzdk5wZdaaSpaeRH0uZYKcxkuV8IS6Qa2FEfA1+vMeRLuHcWlXbMX0w=",
    "mac": "+xozp909S6oDX8KRV8D8ZFVRyh7eEYQpPP76f+DOsnw="
  }
}
```

### Encryption
Encryption works the same as asymmetric SSSS (as such, this section is in parts taken off of the unstable
spec). The secret name in symmetric SSSS is replaced with the session ID. They are encrypted using
AES-CTR-256 and authenticated using HMAC-SHA-256. The process works as follows:
1. Given the megolm backup key, generate 64 bytes by performing an HKDF with SHA-256 as the hash, a
   salt of 32 bytes of 0, and with the session ID as the info. The first 32 bytes are used as the AES
   key, the next 32 bytes are used as teh MAC key.
2. Generate 16 random bytes, set bit 63 to 0 (in order to work around differences in AES-CTR implementations),
   and use this as the AES initialization vector. This becomes the `iv` property, encoded using base64.
3. Encrypt the data using AES-CTR-256 using the AES key generated above. This encrypted data, encoded
   using base64, becomes the `ciphertext` property.
4. Pass the raw encrypted data (prior to base64 encoding) through HMAC-SHA-256 using the MAC generated
   above. The resulting MAC is base64-encoded and becomes the `mac` property.

### `auth_data`
Similar to symmetric SSSS, the `auth_data` object in the `versions` reply contains a mac to verify
that you indeed have the correct private key. For that, you encrypt 32 bytes of 0's using the above
mentioned algorithm and put the `iv` and the `mac` into the `auth_data` object. As name / session ID
an empty string is used. As such, a reply to the `versions` endpoint could look as follows:

```json
{
  "algorithm": "m.megolm_backup.v2.aes-hmac-sha2",
  "auth_data": {
    "iv": "cL/0MJZaiEd3fNU+I9oJrw==",
    "mac": "+xozp909S6oDX8KRV8D8ZFVRyh7eEYQpPP76f+DOsnw="
  },
  "count": 42,
  "etag": "meow",
  "version": "foxies"
}
```

### Secret key storage
The secret key for symmetric megolm is stored in SSSS base64-encoded with the name `m.megolm_backup.v2`.

## Potential issues
Many users already have an asymmetric megolm backup and rely on it. In order to not lose any megolm
keys, clients would have to implement a migration to symmetric megolm backup.

## Alternatives
Many different alternatives on how specifically to do the symmetric encryption can be thought of.
Keeping this the same as symmetric SSSS, however, gives the advantage that clients likely already
have the needed algorithms implemented and can just re-use them.

## Security considerations
If a client supports migration a bad system administrator could create a fake old megolm backup and
inject new megolm sessions that way, expecting the client to migrate them to the new backup.

As the proposed method requires the key to be stored in SSSS, the user will likely have to enter their
SSSS passphrase / recovery key, and thus the migration couldn't happen without user interaction. This
could raise suspicion to the user, however non-tech-savvy ones might fall for this attack and just
blindly enter their passphrase / recovery key.
