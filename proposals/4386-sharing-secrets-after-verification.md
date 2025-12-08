# MSC4386: Automatically sharing secrets after device verification

Currently, after a user verifies a new device, in many clients, the new device
[requests secrets](https://spec.matrix.org/v1.16/client-server-api/#sharing)
(such as the private parts of the cross-signing keys and the backup decryption
key) from the old device, and the old device sends the secrets to the new
device.

This is inefficient as the new device sends a separate request for each secret,
and receives a separate event for each secret.  The new device also has no way
to know, prior to verifying, whether old device has the secrets that it needs.
This may result in a successful verification, but the new device is not in a
fully functioning state.  We propose to allow clients to indicate what secrets
they need and automatically send all the necessary secrets to the new device
before a verification completes.

## Proposal

A new `secrets` property is added to the
[`m.key.verification.request`](https://spec.matrix.org/v1.16/client-server-api/#mkeyverificationrequest)
and
[`m.key.verification.ready`](https://spec.matrix.org/v1.16/client-server-api/#mkeyverificationready)
events.  The `secrets` property is only allowed when verifying a device
belonging to the same user, and is an object with the following properties:

- `available`: an array listing secrets that the client is able to provide to
  the other client
- `requested`: an array listing secrets that the client would like to receive
  from the other client

For example:

```json
{
  "type": "m.key.verification.request",
  "content": {
    "from_device": "DEVICEA",
    "methods": ["m.sas.v1"],
    "timestamp": 1234567890123,
    "transaction_id": "a_unique_string",
    "secrets": {
      "available": [],
      "requested": [
        "m.cross_signing.master",
        "m.cross_signing.self_signing",
        "m.cross_signing.user_signing",
        "m.megolm_backup.v1"
      ]
    }
  }
}
```

A new step is added to the [Key verification
framework](https://spec.matrix.org/v1.16/client-server-api/#key-verification-framework),
before the last step in which devices send the `m.key.verification.done` events:
an event with type `m.key.verification.secrets` is sent when a device can
provide secrets requested by the other device.  The `m.key.verification.secrets`
MUST be sent encrypted.  The `content` of the event has the following
properties:

- `secrets` (required) is a map of secret names to secret contents.
- `transaction_id` (required) is the transaction ID of the verification request,
  as given in the `m.key.verification.request` message.

For example:

```json
{
  "type": "m.key.verification.secrets",
  "content": {
    "secrets": {
      "m.megolm_backup.v1": "private+backup+key",
      "m.cross_signing.self_signing": "private+self+signing+key"
    },
    "transaction_id": "id_from_request"
  }
}
```

The event MUST contain all the secrets that were in the recipient's `requested`
array that are also present in the sender's `available` array from their
respective `m.key.verification.request`/`m.key.verification.ready` events, and
MUST be sent if and only if this set of secrets is non-empty.  Secrets MUST only
be sent if both devices included a `secrets` property in their
`m.key.verification.request`/`m.key.verification.ready` events.  This allows for
compatibility with clients that do not support this proposal.

The client MUST NOT send an `m.key.verification.done` event until it sends
and/or receives the secrets to/from the other client, whichever is needed.

A new `m.missing_secrets` [code for
`m.key.verification.cancel`](https://spec.matrix.org/v1.16/client-server-api/#mkeyverificationcancel)
is added, which is sent when the other client does not have secrets that are
required.  A new `secrets` property is added to `m.key.verification.cancel` when
the code is `m.missing_secrets`, which is an array listing the secrets that the
client needs, but that cannot be provided by the other client.  This allows a
client to request secrets, but treat certain secrets as requirements, and other
secrets as optional.  `m.missing_secrets` is also sent if an
`m.key.verification.secrets` is missing secrets that should have been sent, with
the `secrets` property listing the names of the missing secrets.

### Example:

DEVICEA sends a verification request:

```json
{
  "type": "m.key.verification.request",
  "content": {
    "from_device": "DEVICEA",
    "methods": ["m.sas.v1"],
    "timestamp": 1234567890123,
    "transaction_id": "a_unique_string",
    "secrets": {
      "available": [],
      "requested": [
        "m.cross_signing.master",
        "m.cross_signing.self_signing",
        "m.cross_signing.user_signing",
        "m.megolm_backup.v1"
      ]
    }
  }
}
```

DEVICEB responds:

```json
{
  "type": "m.key.verification.ready",
  "content": {
    "from_device": "DEVICEB",
    "methods": ["m.sas.v1"],
    "transaction_id": "a_unique_string",
    "secrets": {
      "available": [
        "m.cross_signing.master",
        "m.cross_signing.self_signing",
        "m.cross_signing.user_signing"
      ],
      "requested": ["org.example.custom"]
    }
  }
}
```

DEVICEA and DEVICEB then proceed with the verification.  After the verification
is complete, secrets are exchanged.  Since DEVICEB's `requested` secrets have
nothing in common with DEVICEA's `available` secrets, DEVICEA does not send any
`m.key.verification.secrets` event to DEVICEB.  Since there are three secrets from
DEVICEA's `requested` secrets that are also in DEVICEB's `available` secrets,
DEVICEB sends (encrypted) an `m.key.verification.secrets` event:

```json
{
  "type": "m.key.verification.secrets",
  "content": {
    "secrets": {
      "m.cross_signing.master": "private_master_key",
      "m.cross_signing.self_signing": "private_self_signing_key",
      "m.cross_signing.user_signing": "private_user_signing_key"
    },
    "transaction_id": "a_unique_string"
  }
}
```

After DEVICEB sends the `m.key.verification.secrets` event, and checks that it
doesn't expect one from DEVICEA, it sends an `m.key.verification.done` event.

DEVICEA checks that it doesn't need to send an `m.key.verification.secrets` to
DEVICEB, and so doesn't send one.  But notices that it expects to receive one,
so it waits until it receives the `m.key.verification.secrets` event from
DEVICEB, and then sends an `m.key.verification.done` event.

FIXME: add some examples of how clients could use the `secrets` property and
`m.missing_secrets` code to provide feedback to user.

## Potential issues

None?

## Alternatives

Clients can continue as they currently do, requesting secrets after verification.

## Security considerations

When sending secrets between devices, clients must be careful to ensure that the
recipient device is trusted.  However, since secrets are only sent after
verification, this is not a problem.

## Unstable prefix

Before this MSC is accepted, the following names are used:

- `io.element.msc4386.secrets` instead of `secrets` for the property name in
  `m.key.verification.request`/`m.key.verification.ready` events, and
- `io.element.msc4386.key.verification.secrets` instead of `m.key.verification.secrets`
  for the event type.

## Dependencies

None
