# MSC3944: Dropping stale send-to-device messages

Matrix allows devices to send messages [directly to other
devices](https://spec.matrix.org/unstable/client-server-api/#send-to-device-messaging).
This is used in end-to-end encryption, such as for sending keys, and performing
device verification.

However some devices, particularly those that are offline for an extended
period of time, accumulate many to-device messages that become stale.  This can
impede normal operation of the device when it comes back online: servers only
send a limited number of to-device messages in each call to `/sync`, so a
device with many to-device messages waiting for it may require several calls to
`/sync` in order to, for example, receive the Megolm sessions needed to decrypt
in-room messages.

We propose to allow servers to drop to-device messages that are no longer
needed: room key, secret, and verification requests that have been cancelled,
and verification requests that are too old.

## Proposal

Servers may drop the following to-device messages from a device's inbox:

- `m.room_key_request` with `action: request`, if there is a corresponding
  `m.room_key_request` message with `action: request_cancellation` and the same
  `request_id` and `requesting_device_id` fields, sent by the same user after
  the request was made.  If the request message is dropped, the cancellation
  message is dropped as well.  Room key requests can use the same transaction
  ID if they are requesting the same room key, so a request could be made, then
  cancelled, and then re-requested.  Thus the request(s) sent before the
  cancellation should be dropped, but the request (if any) sent after the
  cancellation should be kept.
- `m.room_key_request` with `action: request`, if there are other identical
  requests that are currently in the devices inbox, sent before this request.
  Room key requests can use the same transaction ID if they are requesting the
  same room key.  This can happen, for example, if a key gets requested, and
  later re-requested.  However, if a device was offline during the initial
  request and has not received it yet, it is redundant for it to receive both
  requests.  The server only needs to keep the most recent copy (unless it has
  been cancelled - see above - in which case it does not need to keep any
  copy).
- `m.secret.request` with `action: request`, if there is a corresponding
  `m.secret.request` with `action: request_cancellation` and the same
  `request_id` and `requesting_device_id` fields, sent by the same user.  If
  the request message is dropped, the cancellation message is dropped as well.
- `m.key.verification.request`, if there is a corresponding
  `m.key.verification.cancel` with the same `transaction_id` field, sent by the
  same user.  If the request message is dropped, the cancellation message is
  dropped as well.
- `m.key.verification.request` when the `timestamp` is more than 10 minutes in
  the past.  Since clients are to ignore verification requests that are older
  than this, they can be safely dropped.  The server may wish to remember the
  `transaction_id` and sender for some time, so that it can also drop the
  `m.key.verification.cancel` message with the same `transaction_id` and
  sender, if such a message gets sent.
- `m.room_key_request`, `m.secret.request`, or `m.key.verification.request`
  messages (along with any corresponding cancellation messages, if any), where
  the `requesting_device_id` (in the case of `m.room_key_request` and
  `m.secret.request`), or `device_id` (in the case of
  `m.key.verification.request`) refers to a device that no longer exists.

## Potential issues

None.  The messages that are dropped are messages that clients would ignore
anyways.

## Alternatives

We could just do nothing.

## Security considerations

This requires the server to inspect to-device events, but this is something
servers are already capable of doing, so this does not introduce any new
security issues.

## Unstable prefix

No new event types or endpoints are introduced, so no unstable prefix is
needed.  This is just a change in behaviour.

## Dependencies

None
