# MSC3814: Dehydrated Devices with SSSS

[MSC2697](https://github.com/matrix-org/matrix-doc/pull/2697) introduces device
dehydration -- a method for creating a device that can be stored in a user's
account and receive Megolm sessions.  In this way, if a user has no other
devices logged in, they can rehydrate the device on the next login and retrieve
the Megolm sessions.

However, the approach presented in that MSC has some downsides, making it
tricky to implement in some clients, and presenting some UX difficulties.  For
example, it requires that the device rehydration be done before any other API
calls are made (in particular `/sync`), which may conflict with clients that
currently assume that `/sync` can be called immediately after logging in.

In addition, the user is required to enter a key or passphrase to create a
dehydrated device.  In practice, this is usually the same as the SSSS
key/passphrase, which means that the user loses the advantage of verifying
their other devices via emoji or QR code: either they will still be required to
enter their SSSS key/passphrase (or a separate one for device dehydration), or
else that client will not be able to dehydrate a device.

This proposal introduces another way to use the dehydrated device that solves
these problems by storing the dehydration key in SSSS, and by not changing the
client's device ID.  Rather than changing its device ID when it rehydrates the
device, it will keep its device ID and upload its own device keys. The client
will separately rehydrate the device, fetch its to-device messages, and decrypt
them to retrieve the Megolm sessions.

## Proposal

### Dehydrating a device

The dehydration process is similar as in MSC2697. One important change is that
the dehydrated device, the public device keys, and one-time keys are all
uploaded in the same request. This change should prevent the creation of
dehydrated devices which do not support end-to-end encryption.

To upload a new dehydrated device, a client will use `PUT /dehydrated_device`.
Each user has at most one dehydrated device; uploading a new dehydrated device
will remove any previously-set dehydrated device.

The client *should* use the public Curve25519 identity key of the device,
encoded as unpadded base64, as the device ID.

The `device_keys`, `one_time_keys`, and `fallback_keys` fields use the same
structure as for the `/keys/upload` response.

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
    "algorithms": [
        "m.olm.curve25519-aes-sha2",
    ]
    "keys": {
        "<algorithm>:<device_id>": "<key_base64>",
    },
    "signatures:" {
        "<user_id>" {
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
messages, the response can be sent in batches: the response can include a
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
  "next_batch": "token to obtain next events" // optional
}
```

Once a client calls `POST /dehydrated_device/{device_id}/events`, the server
can delete the device (though not necessarily its to-device messages).  Once a
client calls `POST /dehydrated_device/{device_id}/events` with a `next_batch`
token, the server will delete any to-device messages delivered in previous
batches.  For the last batch of messages, the server will still send a
`next_batch` token, and return an empty `events` array when called with that
token, so that it knows that the client has successfully received all the
messages and can clean up all the to-device messages for that device.

If the given `device_id` is not the dehydrated device ID, the server responds
with an error code of `M_FORBIDDEN`, HTTP code 403.

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

#### Encryption key

The encryption key used for the dehydrated device will be randomly generated
and stored/shared via SSSS using the name `m.dehydrated_device`.

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

This may be addressed by using fallback keys as described in
[MSC2732](https://github.com/matrix-org/matrix-doc/pull/2732).

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
