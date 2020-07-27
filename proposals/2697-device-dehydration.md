# MSC2697: Device Dehydration

End-to-end encryption in Matrix relies on the sending device being able to send
megolm sessions to the recipients' devices.  When a
user logs into a new device, they can obtain the megolm sessions using key
backup or key sharing if another of their devices had previously received the
session.  However, when a user has no logged-in devices when a message is sent,
they are unable to receive incoming megolm sessions.

One solution to this is have a dehydrated device stored (encrypted)
server-side, which may be rehydrated and used when the user creates a new
login rather than creating a new device from scratch.  The new login will
receive any to-device messages that were sent to the dehydrated device.

## Proposal

### Rehydrating a device

A new parameter, `restore_device` is added to `POST /login`, indicating that the
client can restore a previously stored device.  If the parameter is not
present, it defaults to `false`.  If the server has a stored device that can be
used, it will respond with:

```json
{
  "user_id": "full MXID",
  "home_server": "home server address",
  "device_data": "base64+encoded+device+data",
  "device_id": "ID of dehydrated device",
  "dehydration_token": "opaque+token"
}
```

If the server does not have a stored device, or does not understand device
dehydration, then it will respond as if a normal login request were made.

The client will try to decrypt the device data (see below for encryption).  The
client will then make a `POST /restore_device` request, with the
`dehydration_token` body parameter set to the token received from the server.
If it was successful and it wishes to use the device, then it will set the
`rehydrate` body parameter set to `true`.  Otherwise, it will set `rehydrate`
to `false`.  The server will return an object with properties:

- `user_id`: the user's full MXID
- `access_token`: the access token the client will use
- `home_server`: the home server's address
- `device_id`: the device ID for the client to use.

The client will use the device ID given to determine if it should use the
dehydrated device, or if it should use a new device.  Even if the client was
able to successfully decrypt the device data, it may not able to allowed to use
it.  For example, two clients may race in trying to dehydrate the device; only
one client should use the dehydrated device.

### Dehydrating a device

To upload a new dehydrated device, a client will use `POST /device/dehydrate`.
Each user has at most one dehydrated device; uploading a new dehydrated device
will remove any previously-set dehydrated device.

```json
{
  "device_data": "base64+encoded+device+data",
  "initial_device_name": "foo bar",
}
```

Result:

```json
{
  "device_id": "deviceid"
}
```

After the dehydrated device is uploaded, the client will upload the encryption
keys using `POST /keys/upload/{device_id}`, where the `device_id` parameter is
the device ID given in the response to `/device/dehydrate`.

FIXME: synapse already supports `POST /keys/upload/{device_id}`, but requires
that the given device ID matches the device ID of the client that made the
call.  We need to (re-)add the endpoint, and allow uploading keys for the
dehydrated device.

### Device dehydration format

FIXME: should we just reuse libolm's pickle format?

## Potential issues

FIXME:

## Alternatives

Rather than uploading a dehydrated device to the server, we could instead have
the sender resend the megolm session in the case where a user had no active
devices at the time that a message was sent.  However this does not solve the
issue for users who happen to never be online at the same time.  But this could
be done in addition to the solution proposed here.

The sender could also send the megolm session to a the user using a public key
using some per-user mechanism.

## Security considerations

If the dehydrated device is encrypted using a weak password or key, an attacker
could access it and read the user's encrypted messages.

## Unstable prefix

While this MSC is in development, the `POST /restore_device` endpoint will be
reached at `POST /unstable/org.matrix.msc2697/restore_device`, and the `POST
/device/dehydrate` endpoint will be reached at `POST
/unstable/org.matrix.msc2697/device/dehydrate`.  The `restore_device` parameter
for `POST /login` will be called `org.matrix.msc2697.restore_device`.
