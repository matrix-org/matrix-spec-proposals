# MSC4571: FLOE-encrypted attachments
[Currently](https://spec.matrix.org/v1.19/client-server-api/#sending-encrypted-attachments),
attachments in encrypted rooms are encrypted with a fairly simple AES-256-CTR algorithm.
It has a few problems:

* The key format is unnecessarily generic. A whole JWK object is shipped for no reason, even
  though most of the keys are hardcoded.
* It only has a hash covering the ciphertext, not the key and IV, so invisible salamander
  attacks are technically possible: <https://lotte.chir.rs/lw/h/missing-salamanders/>
  (though in practice it's not a problem).
* Streaming is unsafe, because there's nothing else guaranteeing authenticity than the hash
  covering the entire file.

## Proposal
A new attachment encryption scheme is defined using [FLOE](https://github.com/Snowflake-Labs/floe-specification/blob/main/spec/README.md).
The keys are placed in `file` objects just like v2 encryption, but the fields are different. The
version (`v`) is `v3`. The `key` and `iv` fields are no longer used. Instead, the `floe_key` and
`floe_header` fields contain the FLOE key and header respectively as unpadded standard base64.

Additional authenticated data (AAD) is not used by this MSC. Clients MUST use an empty value as the
AAD. Only the `FLOE_BODY` part of the FLOE ciphertext is uploaded to the media repository.

The `hashes` -> `sha256` field is used as before, covering the entire `FLOE_BODY`. However, the hash
is no longer required for data that is not fully available at message send time, like a video stream.
Clients MUST still include the hash for normal file uploads. If the hash is present, it MUST be
verified when downloading the file.

FLOE only has one parameter which can take different values: `ENC_SEG_LEN`. This MSC restricts that
parameter to 4 KiB, i.e. `4096`. The value has to be restricted, because it determines how large
chunks the receiving client has to buffer in memory. The only benefit of larger segments would be
slightly faster decryption, but that's unlikely to be a problem for attachments in a chat room.

All other parameters are also hardcoded as they are in the FLOE specification:
`AEAD` is `AES-GCM-256`, `KDF` is `HKDF-EXPAND-SHA-384`, `FLOE_IV_LEN` is 32.

As per the FLOE spec, clients MUST verify that the parameters embedded in the header sent over the
wire match the hardcoded parameters. This includes the ENC_SEG_LEN hardcoded to 4096 by this MSC.

The `size` field under `info` is now defined to be the unencrypted file length, which means it will
be less than the ciphertext length when using FLOE. The field is still informational and doesn't
have any additional behavior (for instance, it is not used to truncate the file after decryption).
For the old AES-CTR encryption, the ciphertext and plaintext are the same length, so the distinction
doesn't matter.

### Example
```json
{
  "body": "cat.jpg",
  "file": {
    "floe_header": "AAAAABAAAAAAIEAEdNga2y5bl1DLr4SWyc5LqujDxTe11MvN0/xV0PaNbDEf641UUqBZ19mMpJnNOIXK3dge5cevhV/a7rwfS6E",
    "floe_key": "igAFh5gtEMIC+jDZ1pY9u1sOgsEAnqsbbPu3+vqjFO0",
    "hashes": {
      "sha256": "Yb1ZnFrVyRHQYKz4MIRyJG9vFIrjdCrBGCXR9wBmlLo"
    },
    "url": "mxc://maunium.net/NnLIbFTdLrekiiodajhUGtCA",
    "v": "v3"
  },
  "info": {
    "h": 640,
    "mimetype": "image/jpeg",
    "size": 22104,
    "w": 479
  },
  "m.mentions": {},
  "msgtype": "m.image"
}
```

## Potential issues
The new encryption algorithm is not backwards-compatible. Old clients will be unable to view
attachments encrypted with the new algorithm. Clients SHOULD NOT use this for sending normal files
before the algorithm is in the spec and decryption is widely supported.

Unlike the old AES-CTR scheme, the ciphertext length is no longer equal to the plaintext length,
which could complicate implementation in SDKs that assumed the length to be the same.

FLOE is quite new and not widely adopted by the industry yet, so only a few independent
implementations exist.

## Alternatives
### Other streaming encryption schemes
[MSC4016](https://github.com/matrix-org/matrix-spec-proposals/pull/4016) proposed a custom
scheme based on AES-GCM. FLOE is also based on AES-GCM, but has been externally reviewed,
which makes it a better option.

libsodium has an [encrypted stream API](https://doc.libsodium.org/secret-key_cryptography/secretstream),
which uses XChaCha20-Poly1305 instead of AES-GCM + SHA2. Neither it nor FLOE is formally standardized
by a standards organization, but FLOE at least has a specification and [a security analysis paper].

[a security analysis paper]: https://eprint.iacr.org/2025/2275.pdf

### Alternative JSON structuring
The `key` field could technically be reused for the FLOE key. However, as mentioned in the opening,
JWK is a bad format and we don't want to keep using it. To avoid mixed types where `key` can be
either an object or a string depending on the version, a new field is used instead. Also, the header
doesn't really map to any existing field neatly.

## Security considerations
Omitting the full-file hash means a server with the FLOE key and header could substitute the file
in an undetectable manner. This is considered acceptable for the streaming use cases and MSC4016
had the same caveat. FLOE still ensures that an attacker without the key can't modify the ciphertext,
so only room members who received the key can modify it. Omitting the hash when there's no technical
reason to do so is forbidden.

## Unstable prefix
`com.beeper.floe.v1` is used as the attachment encryption version instead of `v3` until this
proposal is accepted. Other fields are not prefixed.

## Dependencies
None.
