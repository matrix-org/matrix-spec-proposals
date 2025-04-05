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

The dehydrated device MUST be cross-signed and have a fallback key.

The client MUST use the public [Curve25519] [identity key] of the device,
encoded as unpadded Base64, as the device ID.

The request body has the following properties:

- `device_id` (required): the dehydrated device's ID, which MUST be the public
  [Curve25519] [identity key] of the device, encoded as unpadded Base64.
- `device_data` (required): the data about the dehydrated device that will be
  used later to rehydrate the device.  This is a JSON object that has, at
  minimum, an `algorithm` property.  The value of the `algorithm` property
  determines the other properties in the object.  In this MSC, we define the
  `m.dehydration.v2` algorithm.
- `initial_device_display_name` (optional): the display name for the device
- `device_keys` (required), `one_time_keys` (optional), `fallback_keys`
  (optional): the dehydrated device's device keys, one-time keys, and fallback
  keys, respectively, using the same structure as for the [`/keys/upload`]
  request.

We add a new optional property to the device keys: `dehydrated`, which is set to
`true` for dehydrated devices.  Defaults to `false`.  Clients that support
dehydrated devices *must not* encrypt to devices marked as being a dehydrated
device if they are not cross-signed.  Clients should also drop any to-device
messages from a device marked as being a dehydrated device, since dehydrated
device should not be sending messages.  Clients can use also this flag for
other purposes, such as:

- Display dehydrated devices differently from normal devices, to avoid confusing
  users who do not expect to see another device.
- Don't send key forwarding or verification requests to the dehydrated device,
  since it will not respond to them.
- Don't send room keys to the dehydrated device if the user has a sufficient
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
    "algorithm": "m.dehydration.v2"
    "...": "..." // algorithm-dependent properties
  },
  "initial_device_display_name": "foo bar", // optional
  "device_keys": {
    "user_id": "<user_id>",
    "device_id": "<device_id>",
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
  "device_id": "dehydrated_device_id"
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
  "device_id": "dehydrated_device_id",
  "device_data": {
    "algorithm": "m.dehydration.v2",
    "other_fields": "other_values"
  }
}
```

The `device_id` and `device_data` properties are the same as the values given in
the previous `PUT /dehydrated_device` call.

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

The dehydrated device can be deleted by calling `DELETE /dehydrated_device`.
Note that the dehydrated device will get replaced whenever a new device gets
uploaded using the `PUT /dehydrated_device`, so calling `DELETE
/dehydrated_device` is not necessary when replacing the dehydrated device.  It
is only necessary to call when the dehydrated device is to be removed and may
not be replaced.  For example, if a client resets the user's cross-signing keys,
but does not create a new dehydrated device, it should call this endpoint, as
the dehydrated device would be signed with an outdated old cross-signing key.

`DELETE /dehydrated_device`

Response:

```json
{
  "device_id": "dehydrated_device_id"
}
```

The dehydrated can also be deleted by calling the existing [`POST
/delete_devices`](https://spec.matrix.org/unstable/client-server-api/#post_matrixclientv3delete_devices),
[`DELETE
/devices/{deviceId}`](https://spec.matrix.org/unstable/client-server-api/#delete_matrixclientv3devicesdeviceid),
and [`POST
/logout/all`](https://spec.matrix.org/unstable/client-server-api/#post_matrixclientv3logoutall)
endpoints.  In contrast with `POST /delete_devices` and `DELETE
/devices/{deviceId}`, the new `DELETE /dehydrated_device` does not use
User-Interactive Authentication, and does not require knowing the device ID of
the dehydrated device.

### Device Dehydration Format

We define the following format for storing the dehydrated device (based on the
libolm pickle format):

We store the device as a concatenation of binary values.  Multi-byte numbers are
stored in big-endian format.  The version is set to 0x80000000.  (Setting the
high bit to 1 is to avoid confusion with the libolm pickle format for accounts,
which was used in a previous version of this MSC.)

```text
   ┌───────────────────────────────────────────────────────────┐
   │                        Pickle                             │
   ├───────────────────────────────────────────────────────────┤
   │Name                    │ Type          │ Size (bytes)     │
   ├────────────────────────┼───────────────┼──────────────────┤
   │Version                 │ u32           │ 4                │
   │Curve25519 private key  │ [u8; 32]      │ 32               │
   │Ed25519 private key     │ [u8; 32]      │ 32               │
   │Number of one-time keys │ u32           │ 4                │
   │One-time keys           │ [OneTimeKey]  │ N * 32           │
   │Fallback key            │ OptFallback   │ 1 or 33          │
   └────────────────────────┴───────────────┴──────────────────┘

   ┌───────────────────────────────────────────────────────────┐
   │                      OneTimeKey                           │
   ├────────────────────────┬───────────────┬──────────────────┤
   │Name                    │ Type          │ Size (bytes)     │
   ├────────────────────────┼───────────────┼──────────────────┤
   │Curve25519 private key  │ [u8; 32]      │ 32               │
   └────────────────────────┴───────────────┴──────────────────┘

   ┌───────────────────────────────────────────────────────────┐
   │                      OptFallback                          │
   ├────────────────────────┬───────────────┬──────────────────┤
   │Name                    │ Type          │ Size (bytes)     │
   ├────────────────────────┼───────────────┼──────────────────┤
   │Fallback present        │ boolean       │ 1                │
   │Fallback private key    │ [u8; 32]      │ 0 or 32          │
   └────────────────────────┴───────────────┴──────────────────┘
```

The data is then encrypted and encoded as follows.

#### Encryption key

The encryption key used for the dehydrated device will be randomly generated
and stored/shared via SSSS using the name `m.dehydrated_device`, encoded using
unpadded base64.

A 96-bit (12-byte) nonce is randomly generated; each time a device is
dehydrated, a new nonce must be generated.

The plain-text is encrypted with ChaCha20-Poly1305 as defined in
[RFC8439](https://datatracker.ietf.org/doc/html/rfc8439) using the encryption
key and nonce.

The ciphertext and nonce are then encoded as [unpadded
Base64](https://spec.matrix.org/v1.12/appendices/#unpadded-base64) and inserted
into the `device_pickle` and `nonce` properties, respectively, of the
`device_data` JSON message.  The `algorithm` property is set to `m.dehydration.v2`.

 ```json
{
  "device_data": {
    "algorithm": "m.dehydration.v2",
    "device_pickle": "encrypted dehydrated device"
    "nonce": "random nonce"
  }
}
```

#### Test vectors

TODO: put a test vector here

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

This may be addressed by using [fallback
keys](https://spec.matrix.org/v1.9/client-server-api/#one-time-and-fallback-keys),
and clients are recommended to create a fallback key for the dehydrated device.

To reduce the chances of one-time key exhaustion, if the user has an active
client, it should periodically (e.g. once a week) replace the dehydrated device
with a new dehydrated device with new one-time keys.  If a client does this,
then it runs the risk of losing any megolm keys that were sent to the dehydrated
device, but the client should have received those megolm keys itself, so this
should not be a problem.

Alternatively, we could provide a new API to allow the client to perform a
`/sync`-like call for the dehydrated device, dehydrate the olm sessions, and
upload new one-time keys.  By doing this instead of overwriting the dehydrated
device, the device can receive megolm keys from more devices.  However, this
would require additional server-side changes above what this proposal provides,
adds more complexity, and does not provide any practical benefits.

### Accumulated to-device messages

If a dehydrated device is not rehydrated for a long time, then it may
accumulate many to-device messages from other clients sending it Megolm
sessions.  This may result in a slower initial sync when the device eventually
does get rehydrated, due to the number of messages that it will retrieve.
Again, this can be addressed by periodically replacing the dehydrated device.

## Alternatives

As mentioned above,
[MSC2697](https://github.com/matrix-org/matrix-doc/pull/2697) tries to solve
the same problem in a similar manner, but has several disadvantages that are
fixed in this proposal.

Since the device ID is used in URL path parameters, we could use URL-safe base64
to derive the device ID.  However, this would result in the identity key being
represented in two similar-but-different ways (URL-safe base64 in the device ID,
and regular base64 in the device keys structure), which could lead to confusion.

Rather than keep the name "dehydrated device", we could change the name to
something like "shrivelled sessions", so that the full expansion of this MSC
title would be "Shrivelled Sessions with Secure Secret Storage and Sharing", or
SSSSSS.  However, despite the alliterative property, the term "shrivelled
sessions" is less pleasant, and "dehydrated device" is already commonly used to
refer to this feature.

The alternatives discussed in MSC2697 are also alternatives here.


## Security considerations

### Weak SSSS passphrase/key

A similar security consideration to the one in MSC2697 also applies to this
proposal: if SSSS is encrypted using a weak passphrase or key, an attacker
could access it and rehydrate the device to read the user's encrypted
messages.

### Display of dehydrated devices

As mentioned earlier, clients may wish to display dehydrated devices differently
from normal devices by checking the `dehydrated` flag in the device's keys.
Clients must exercise care when doing so, as this may allow a attacker to hide a
malicious device.  Clients *must not* encrypt messages to a dehydrated device
that is not cross-signed.  Clients should indicate the presence of the
dehydrated device, even if it is not listed along with the normal devices.  For
example, a client could hide the dehydrated device from the device list, but
indicate that "The dehydrated device feature is enabled".  A user can only have
one dehydrated device available at a time, so if more than one device is marked
as `dehydrated: true`, the client should display them all as normal devices.
Clients can also display a warning in such a situation.

## Unstable prefix

While this MSC is in development, the `/dehydrated_device` endpoints will be
reached at `/unstable/org.matrix.msc3814.v1/dehydrated_device`, and the
`/dehydrated_device/{device_id}/events` endpoint will be reached at
`/unstable/org.matrix.msc3814.v1/dehydrated_device/{device_id}/events`.  The
dehydration algorithm `m.dehydration.v2` will be called
`org.matrix.msc3814.v2`.  The SSSS name for the dehydration key will be
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
