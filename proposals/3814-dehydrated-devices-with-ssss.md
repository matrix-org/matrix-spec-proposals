# MSC3814: Dehydrated Devices with [SSSS]

[MSC2697] introduces device
dehydration -- a method for creating a device that can be stored in a user's
account and receive [Megolm] sessions.  In this way, if a user has no other
devices logged in, they can rehydrate the device on the next login and retrieve
the [Megolm] sessions.

However, the approach presented in that MSC has some downsides, making it
tricky to implement in some clients, and presenting some UX difficulties.  For
example, it requires that the device rehydration be done before any other API
calls are made (in particular `/sync`), which may conflict with clients that
currently assume that `/sync` can be called immediately after logging in.

In addition, the user is required to enter a key or passphrase to create a
dehydrated device.  In practice, this is usually the same as the [SSSS]
key/passphrase, which means that the user loses the advantage of verifying
their other devices via emoji or QR code: either they will still be required to
enter their [SSSS] key/passphrase (or a separate one for device dehydration), or
else that client will not be able to dehydrate a device.

This proposal introduces another way to use the dehydrated device that solves
these problems by storing the dehydration key in [SSSS], and by not changing the
client's device ID.  Rather than changing its device ID when it rehydrates the
device, it will keep its device ID and upload its own device keys. The client
will separately rehydrate the device, fetch its to-device messages, and decrypt
them to retrieve the Megolm sessions.

## Proposal

### Dehydrating a device

The dehydration process is similar as in [MSC2697]. One important change is that
the dehydrated device, the public device keys, and one-time keys are all
uploaded in the same request. This change should prevent the creation of
dehydrated devices which do not support end-to-end encryption.

To upload a new dehydrated device, a client will use `PUT /dehydrated_device`.
Each user has at most one dehydrated device; uploading a new dehydrated device
will remove any previously-set dehydrated device.

The client *must* use the public [Curve25519] [identity key] of the device,
encoded as unpadded Base64, as the device ID.

The `device_keys`, `one_time_keys`, and `fallback_keys` fields use the same
structure as for the [`/keys/upload`] request.

We add a new optional property to the device keys: `dehydrated`, which is set
to `true` for dehydrated devices.  Defaults to `false`.  Clients can use this
flag to handle the dehydrated device specially.  For example:

- display dehydrated devices differently from normal devices, to avoid
  confusing from users who do not expect to see another device
- don't send key forwarding requests to the dehydrated device, since it will
  not respond to them
- don't send room keys to the dehydrated device if the user has a sufficient
  number of other devices, with the assumption that if the user logs in to a
  new device, they can get the room keys from one of their other devices and/or
  from key backup.  This will reduce the chances that the dehydrated device
  will run out of one-time keys, and reduce the number of events that the
  dehydrated device will need to decrypt.

`PUT /dehydrated_device`

```jsonc
{
  "device_id": "dehydrated_device_id",
  "device_data": {
    "algorithm": "m.dehydration.v1.olm"
    "other_fields": "other_values"
  },
  "initial_device_display_name": "foo bar", // optional
  "device_keys": {
    "user_id": "<user_id>",
    "device_id": "<device_id>",
    "valid_until_ts": <millisecond_timestamp>,
    "dehydrated": true,
    "algorithms": [
        "m.olm.curve25519-aes-sha2",
    ]
    "keys": {
        "<algorithm>:<device_id>": "<key_base64>",
    },
    "signatures": {
        "<user_id>": {
            "<algorithm>:<device_id>": "<signature_base64>"
        }
    }
  },
  "fallback_keys": {
    "<algorithm>:<device_id>": "<key_base64>",
    "signed_<algorithm>:<device_id>": {
      "fallback": true,
      "key": "<key_base64>",
      "signatures": {
        "<user_id>": {
          "<algorithm>:<device_id>": "<key_base64>"
        }
      }
    }
  },
  "one_time_keys": {
    "<algorithm>:<key_id>": "<key_base64>"
  }
}
```

Result:

```json
{
  "device_id": "dehydrated device's ID"
}
```

### Rehydrating a device

To rehydrate a device, a client first calls `GET /dehydrated_device` to see if
a dehydrated device is available.  If a device is available, the server will
respond with the dehydrated device's device ID and the dehydrated device data.

`GET /dehydrated_device`

Response:

```json
{
  "device_id": "dehydrated device's ID",
  "device_data": {
    "algorithm": "m.dehydration.v1.olm",
    "other_fields": "other_values"
  }
}
```

If no dehydrated device is available, the server responds with an error code of
`M_NOT_FOUND`, HTTP code 404.

If the client is able to decrypt the data and wants to use the dehydrated
device, the client retrieves the to-device messages sent to the dehydrated
device by calling `POST /dehydrated_device/{device_id}/events`, where
`{device_id}` is the ID of the dehydrated device.  Since there may be many
messages, the response can be sent in batches: the response must include a
`next_batch` parameter, which can be used in a subsequent call to `POST
/dehydrated_device/{device_id}/events` to obtain the next batch.

```
POST /dehydrated_device/{device_id}/events
{
  "next_batch": "token from previous call" // (optional)
}
```

Response:

```jsonc
{
  "events": [
    // array of to-device messages, in the same format as in
    // https://spec.matrix.org/unstable/client-server-api/#extensions-to-sync
  ],
  "next_batch": "token to obtain next events"
}
```

Once a client calls `POST /dehydrated_device/{device_id}/events` with a
`next_batch` token, unlike the `/sync` endpoint, the server should *not* delete
any to-device messages delivered in previous batches. This should prevent the
loss of messages in case the device performing the rehydration gets deleted. In
the case the rehydration process gets aborted, another device will be able to
restart the process.

For the last batch of messages, the server will still send a
`next_batch` token, and return an empty `events` array when called with that
token, this signals to the client that it has received all to-device events and
it can delete the dehydrated device and create a new one.

If the given `device_id` is not the dehydrated device ID, the server responds
with an error code of `M_FORBIDDEN`, HTTP code 403.

### Deleting a dehydrated device

A dehydrated device will get replaced whenever a new device gets uploaded using
the `PUT /dehydrated_device`, this makes a `DELETE /dehydrated_device`
unnecessary, though for completeness sake and to give client authors to get back
to a state where no dehydrated device exists for a given user we will introduce
one.

`DELETE /dehydrated_device`

Response:

```json
{
  "device_id": "dehydrated device's ID"
}
```

### Device Dehydration Format

TODO: define a format.  Unlike MSC2679, we don't need to worry about the
dehydrated device being used as a normal device, so we can omit some
information.  So we should be able to get by with defining a fairly simple
standard format, probably just the concatenation of the private device keys and
the private one-time keys.  This will come at the expense of implementations
such as libolm needing to implement extra functions to support dehydration, but
will have the advantage that we don't need to figure out a format that will fit
into every possible implementation's idiosyncrasies.  The format will be
encrypted, which leads to ...

```text
   ┌───────────────────────────────────────────────────────────┐
   │                        Pickle                             │
   ├───────────────────────────────────────────────────────────┤
   │Name                    │ Type          │ Size (bytes)     │
   ├────────────────────────┼───────────────┼──────────────────┤
   │Version                 │ u32           │ 4                │
   │Ed25519 key pair        │ KeyPair       │ 64               │
   │Curve25519 key pair     │ KeyPair       │ 64               │
   │Number of one-time keys │ u32           │ 4                │
   │One-time keys           │ [OneTimeKey]  │ N * 69           │
   │Fallback keys           │ FallbackKeys  │ 2 * 69           │
   │Next key ID             │ u32           │ 4                │
   └────────────────────────┴───────────────┴──────────────────┘
   ┌───────────────────────────────────────────────────────────┐
   │                        KeyPair                            │
   ├────────────────────────┬───────────────┬──────────────────┤
   │Name                    │ Type          │ Size (bytes)     │
   ├────────────────────────┼───────────────┼──────────────────┤
   │Public key              │ [u8; 32]      │ 32               │
   │Private key             │ [u8; 32]      │ 32               │
   └────────────────────────┴───────────────┴──────────────────┘

   ┌───────────────────────────────────────────────────────────┐
   │                      OneTimeKey                           │
   ├────────────────────────┬───────────────┬──────────────────┤
   │Name                    │ Type          │ Size (bytes)     │
   ├────────────────────────┼───────────────┼──────────────────┤
   │Key ID                  │ u32           │ 4                │
   │Is published            │ u8            │ 1                │
   │Curve 25519 key pair    │ KeyPair       │ 69               │
   └────────────────────────┴───────────────┴──────────────────┘

   ┌───────────────────────────────────────────────────────────┐
   │                     FallbackKeys                          │
   ├────────────────────────┬───────────────┬──────────────────┤
   │Name                    │ Type          │ Size (bytes)     │
   ├────────────────────────┼───────────────┼──────────────────┤
   │Number of fallback keys │ u8            │ 1                │
   │Fallback-key            │ OneTimeKey    │ 69               │
   │Previous fallback-key   │ OneTImeKey    │ 69               │
   └────────────────────────┴───────────────┴──────────────────┘
```

TODO: Explain why we must ignore public keys when decoding them and why they are
included in the first place.

When decoding, clients *must* ignore the public keys and instead derive the
public key from the private one.

#### Encryption key

TODO: Explain why the double derivation is necessary.

The encryption key used for the dehydrated device will be randomly generated
and stored/shared via SSSS using the name `m.dehydrated_device`.

The randomly generated encryption key *must* be expanded using the HMAC-based
Key Derivation function defined in [RFC5869].

```math
\begin{aligned}
    DEVICE\_KEY
    &= \text{HKDF} \left(\text{``Device ID``}, RANDOM\_KEY, \text{``dehydrated-device-pickle-key"}, 32\right)
\end{aligned}
```

The `device_key` is then further expanded into a AES256 key, HMAC key and
initialization vector.


```math
\begin{aligned}
    AES\_KEY \parallel HMAC\_KEY \parallel AES\_IV
    &= \text{HKDF}\left(0,DEVICE\_KEY,\text{``Pickle"},80\right)
\end{aligned}
```

The plain-text is encrypted with [AES-256] in [CBC] mode with [PKCS#7] padding,
using the key $`AES\_KEY`$ and the IV $`AES\_IV`$ to give the cipher-text.

Then the cipher-text are passed through [HMAC-SHA-256]. The first 8 bytes of the
MAC are appended to the cipher-text.

The cipher-text, including the appended MAC tag, are encoded using unpadded
Base64 to give the device pickle.

The device pickle is then inserted into the `device_pickle` field of the
`device_data` JSON message.

 ```json
{
  "device_data": {
    "algorithm": "m.dehydration.v1.olm",
    "device_pickle": "encrypted dehydrated device"
  }
}
```

#### Test vectors

Device pickle:
```
Gc0elC7k7NISzWW/C2UIuzRMDSHzzRLfM3lMnJHMLMcuyLtZHljhV/YvIctIlepxevznEcwBc40Q0CtS3k5SI9gGyN7G+95hnQan0rKe64a1Vx1Vx4Ky8i+m1y9JVT++WcQ54CGhMuCGoN2O1xEQb+4fM+UVS/bLNJ4Pzzqa1ilzCrs4SCTz70eriShvzt7y1cn2A6ABNhK4aXnLB8gK9HuMLyctyX5ikvIjkAIAdVr1EI1azetZDQ
```


## Potential issues

The same issues as in
[MSC2697](https://github.com/matrix-org/matrix-doc/pull/2697) are present for
this proposal.  For completeness, they are repeated here:

### One-time key exhaustion

The dehydrated device may run out of one-time keys, since it is not backed by
an active client that can replenish them.  Once a device has run out of
one-time keys, no new olm sessions can be established with it, which means that
devices that have not already shared megolm keys with the dehydrated device
will not be able to share megolm keys.  This issue is not unique to dehydrated
devices; this also occurs when devices are offline for an extended period of
time.

This may be addressed by using [fallback keys](https://spec.matrix.org/v1.9/client-server-api/#one-time-and-fallback-keys).

To reduce the chances of one-time key exhaustion, if the user has an active
client, it can periodically replace the dehydrated device with a new dehydrated
device with new one-time keys.  If a client does this, then it runs the risk of
losing any megolm keys that were sent to the dehydrated device, but the client
would likely have received those megolm keys itself.

Alternatively, the client could perform a `/sync` for the dehydrated device,
dehydrate the olm sessions, and upload new one-time keys.  By doing this
instead of overwriting the dehydrated device, the device can receive megolm
keys from more devices.  However, this would require additional server-side
changes above what this proposal provides, so this approach is not possible for
the moment.

### Accumulated to-device messages

If a dehydrated device is not rehydrated for a long time, then it may
accumulate many to-device messages from other clients sending it Megolm
sessions.  This may result in a slower initial sync when the device eventually
does get rehydrated, due to the number of messages that it will retrieve.
Again, this can be addressed by periodically replacing the dehydrated device,
or by performing a `/sync` for the dehydrated device and updating it.

## Alternatives

As mentioned above,
[MSC2697](https://github.com/matrix-org/matrix-doc/pull/2697) tries to solve
the same problem in a similar manner, but has several disadvantages that are
fixed in this proposal.

Rather than keep the name "dehydrated device", we could change the name to
something like "shrivelled sessions", so that the full expansion of this MSC
title would be "Shrivelled Sessions with Secure Secret Storage and Sharing", or
SSSSSS.  However, despite the alliterative property, the term "shrivelled
sessions" is less pleasant, and "dehydrated device" is already commonly used to
refer to this feature.

The alternatives discussed in MSC2697 are also alternatives here.


## Security considerations

A similar security consideration to the one in MSC2697 also applies to this
proposal: if SSSS is encrypted using a weak passphrase or key, an attacker
could access it and rehydrate the device to read the user's encrypted
messages.

## Unstable prefix

While this MSC is in development, the `/dehydrated_device` endpoints will be
reached at `/unstable/org.matrix.msc3814.v1/dehydrated_device`, and the
`/dehydrated_device/{device_id}/events` endpoint will be reached at
`/unstable/org.matrix.msc3814.v1/dehydrated_device/{device_id}/events`.  The
dehydration algorithm `m.dehydration.v1.olm` will be called
`org.matrix.msc3814.v1.olm`.  The SSSS name for the dehydration key will be
`org.matrix.msc3814` instead of `m.dehydrated_device`.

## Dependencies

None

[RFC5869]: https://datatracker.ietf.org/doc/html/rfc5869
[AES-256]: http://csrc.nist.gov/publications/fips/fips197/fips-197.pdf
[CBC]: http://csrc.nist.gov/publications/nistpubs/800-38a/sp800-38a.pdf
[PKCS#7]: https://tools.ietf.org/html/rfc2315
[Curve25519]: http://cr.yp.to/ecdh.html
[identity key]: https://gitlab.matrix.org/matrix-org/olm/-/blob/master/docs/olm.md#initial-setup
[Megolm]: https://gitlab.matrix.org/matrix-org/olm/blob/master/docs/megolm.md
[SSSS]: https://spec.matrix.org/v1.7/client-server-api/#storage
[MSC2697]: https://github.com/matrix-org/matrix-doc/pull/2697
[`/keys/upload`]: https://spec.matrix.org/v1.7/client-server-api/#post_matrixclientv3keysupload
[device keys]: https://spec.matrix.org/v1.7/client-server-api/#device-keys
[HMAC-SHA-256]: https://datatracker.ietf.org/doc/html/rfc2104
