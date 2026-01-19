# MSC4203: Sending to-device events to appservices
This MSC is a part of adding end-to-end encryption support to application services.
It was split off from [MSC2409]. The parent MSC for encrypted appservices is [MSC3202].

[MSC2409]: https://github.com/matrix-org/matrix-spec-proposals/pull/2409
[MSC3202]: https://github.com/matrix-org/matrix-spec-proposals/pull/3202

## Proposal
A new key, `to_device`, is added to the request body of the appservice API
`/transactions` endpoint. The key contains a list of all to-device events
sent to users who are covered by the namespaces of the appservice. If there are
no new to-device events, the key can be omitted.

In addition to the usual keys that are included in to-device events in the
client-server `/sync` API, appservice to-device events include `to_user_id` and
`to_device_id` fields to specify which user and device the event was sent to.

```jsonc
{
  "to_device": [
    {
      "to_user_id": "@appservice_12345:example.com",
      "to_device_id": "VPLQFIDCIT",
      "type": "m.room.encrypted",
      "sender": "@user:example.com",
      "content": {
        "algorithm": "m.olm.v1.curve25519-aes-sha2",
        "sender_key": "...",
        "ciphertext": {
          "...": {}
        }
      }
    }
  ],
  "events": [
    // ...
  ],
  "ephemeral": [
    // MSC2409...
  ]
}
```

Like [MSC3202], this MSC does not have an opt-in/out flag, as there usually
aren't any devices or to-device traffic if the appservice doesn't support
encryption.

### Implementation detail: when to delete a to-device message

Not defined by this MSC is an explicit algorithm for when to delete a to-device message (mark
it as sent). This is left as an implementation detail, though a suggested approach is as
follows:

* If the message is sent to a user under an appservice's *exclusive* namespace mark it as sent
  and delete it. Note that retried transactions will still need to include the message.
* If the message is sent to a user under an appservice's *inclusive* namespace, mark it as sent
  to the appservice but do not delete it until a `/sync` request is completed which includes the
  message. Note that retried transactions will still need to include the message.

This approach is largely to align with how namespaces are used by appservices in practice, but
is not applicable to all scenarios (and thus is an implementation detail). The majority of known
appservices use exclusive namespaces, which typically also means that those users will not be
calling `/sync`. Because of this, the server may never get another opportunity to delete the
messages until it has confirmed that the appservice received the transaction successfully. Inclusive
namespaces are typically used when the appservice wants to impact a subset of users, but without
controlling those users explicitly. Typically, inclusive users are also calling `/sync` and so
the appservice should be CC'd on the to-device messages that would normally go down `/sync`.

For inclusive namespaces, servers may also track who created a device, and not wait for `/sync`
if the device was created using [appservice login] or [appservice device management].

[appservice login]: https://spec.matrix.org/v1.17/application-service-api/#server-admin-style-permissions
[appservice device management]: https://spec.matrix.org/v1.17/application-service-api/#device-management

## Potential issues
If servers forget to delete to-device events, they may accumulate in the
database and fill up the disk.

## Alternatives
Appservices can use `/sync` (as they already do), but it's rather clunky to
need a different way to receive to-device events than normal events.

Appservices can also be unencrypted, which mostly removes the need for
to-device events.

### Nested event data
Instead of mixing `to_user_id` and `to_device_id` in with the existing fields,
the existing fields could be nested inside another object. However, unlike room
events, custom fields are not allowed in the top level of to-device events. The
federation format is already quite different than the client-server format:
<https://spec.matrix.org/v1.17/server-server-api/#definition-mdirect_to_device>.
Existing server implementations ignore custom top-level fields over federation
when converting to the client format.

## Security considerations
Receiving to-device events does not have any inherent security implications.
Appservices are already able to log in as users in their namespace and use
`/sync` to receive to-device events, which means no additional privileges are
granted. As always, care should be taken when specifying appservice namespaces.

## Unstable prefix
Until this MSC is accepted, `de.sorunome.msc2409.to_device` should be used as
the key in transactions requests instead of `to_device`. The key is different
than the MSC number to preserve compatibility with the older version which was
a part of [MSC2409].

[MSC2409]: https://github.com/matrix-org/matrix-spec-proposals/pull/2409
