# MSC3202: Encrypted Appservices

Presently, appservices in Matrix are capable of attaching themselves to a homeserver for high-traffic
bot-like usecases, such as bridging and operationally expensive bots. Traditionally, these appservices
only work in unencrypted rooms due to not having enough context on the encryption state to actually
function properly.

This MSC targets the missing bits to support encryption at the appservice level: other MSCs, such as
[MSC2409](https://github.com/matrix-org/matrix-doc/pull/2409) and [MSC2778](https://github.com/matrix-org/matrix-doc/pull/2778)
give appservices foundational pieces to get device IDs and to-device messages, as required by encryption.

## Proposal

This proposal takes inspiration from [MSC2409](https://github.com/matrix-org/matrix-doc/pull/2409) by
defining a new set of keys on the appservice `/transactions` endpoint, similar to sync:

```json5
{
  "events": [
    // as defined today
  ],
  "ephemeral": [
    // MSC2409
  ],
  "to_device": [
    // MSC2409
  ],
  "device_lists": {
    "changed": ["@alice:example.org"],
    "left": ["@bob:example.com"]
  },
  "device_one_time_keys_count": {
    "@_irc_bob:example.org": {
      "DEVICEID": {
        "curve25519": 10,
        "signed_curve25519": 20
      }
    }
  },
  "device_unused_fallback_key_types": {
    "@_irc_bob:example.org": {
      "DEVICEID": ["signed_curve25519"]
    }
  }
}
```

These fields are heavily inspired by [the extensions to /sync](https://matrix.org/docs/spec/client_server/r0.6.1#id84)
in the client-server API.

All the new fields can be omitted if there are no changes for the appservice to handle. For
`device_one_time_keys_count` and `device_unused_fallback_key_types`, the format is slightly different
from the client-server API to better map the appservice's user namespace users to the counts. Users
in the namespace without keys or which have unchanged keys since the last transaction can be omitted
(more details on this later on). Note that fallback keys are described in
[MSC2732](https://github.com/matrix-org/matrix-doc/pull/2732) as of writing.

Like MSC2409, any user the appservice would be considered "interested" in (user in the appservice's
namespace, or sharing a room with an appservice user/namespaced room) would qualify for the device
list changes section.

Note that it's typical for clients to pause sync loops when processing device list changes to avoid
a scenario where they are unable to decrypt/encrypt a message from/to a particular device. Appservices
are expected to mirror this by ensuring the transaction request does not complete until processing
is complete. In the worst case, the server will time out the request and retry it verbatim, so
appservices might wish to track which device list changes in which transaction they already processed
or keep processing transactions in the background while retries are attempted.

In order to allow the appservice to masquerade as its users, an extension to the existing
[identity assertion](https://matrix.org/docs/spec/application_service/r0.1.2#identity-assertion)
ability is proposed. To compliment the (optional) `user_id` when using an `as_token` as an access
token, a similarly optional `device_id` query parameter is proposed. When provided, the server asserts
that the device ID is valid for the user, and that the appservice is able to masquerade as that user.
If valid, that device ID should be assumed as being used for that request. For many requests, this
means updating the "last seen IP" and "last seen timestamp" for the device, however for some endpoints
it means interacting with that device (such as when uploading keys).

### Optimization: when to send OTKs/fallback keys

As mentioned above, in order to keep the transaction byte size down the server can (and should) exclude
OTK counts and unused fallback keys when they haven't changed since the last transaction. Appservices
however should be tolerable of the server over-communicating the counts as a quick/cheap approach would
be to *always* include the OTK counts/unused fallback keys for all known users rather than trying to
detect changes.

As a middle ground, servers might be interested in an algorithm which doesn't detect changes between
transactions but does attempt to reduce traffic. If the appservice is about to receive an event or
message typically associated with encryption, the counts for the affected users could be included. This
would result in the following rules:
* If an `m.room.encrypted` event is being included in the transaction's `events`, include OTK counts and
  unused fallback key types for all appservice users which reside in that room.
* If an appservice user is receiving a to-device message in the transaction's `to_device` array, include
  OTK counts and unused fallback key types for that user.

This approach has the advantage of typically minimal changes to the internals of the homeserver, works
similar to `/sync`, and reduces noisy traffic in the transaction sending. This additionally still honours
the "when they change, send the counts" requirement to a reasonable degree: typically a use of an OTK will
be followed by a to-device message. It is theoretically possible for an appservice to run out of OTKs if
a remote user claims all OTKs without actually using them. Implementations may be interested in
[MSC2732: Fallback keys](https://github.com/matrix-org/matrix-doc/pull/2732) which will avoid a scenario
where the appservice can no longer decrypt messages.

However, as mentioned, servers are free to include this information as little or often as they'd like,
provided they send it at least as often as when it changes.

### Optimization: Don't encrypt as often

Appservices theoretically do not need to establish Olm sessions with other appservice users as the appservice
will typically be managing the devices in one place. In short, this means that a room with 10k appservice
users and only 1 non-appservice user can be sped up by only encrypting from the appservice's users to the
non-appservice user. The appservice would not need to set up 10k * 10k Olm sessions given the encryption
and decryption all happens in the same place. As an added bonus, this improves performance of the appservice
as it doesn't have to handle to-device messages sent to itself.

Some implementations might not be able to support this sort of optimization though, so it is still permitted
to establish sessions and such between appservice users.

## Potential issues

Servers would have to track and send this information to appservices, however this is still perceived
to be more performant than appservices using potentionally thousands of `/sync` streams.

Appservices additionally cannot opt-in (or out) of this functionality unlike with MSC2409. It is
expected that servers will optimize for not including/calculating the fields if the appservice has
no interest in the information. Specifically, appservices which don't have any keys under their user
namespace can be assumed to not need device list changes and thus can be optimized out.

## Alternatives

An endpoint for appservices to poll could work, though this is extra work for the appservice and would
likely need pagination and such, which is all heavyweight for the server. Instead, having the server
batch up updates and send them to the appservice is likely faster.

## Security considerations

None relevant - this is the same information the appservice would get if it spawned `/sync` streams for
all the users in its namespace.

## Unstable prefix

While this MSC is not considered stable for implementation, implementations should use `org.matrix.msc3202.`
as a prefix to the fields on the `/transactions` endpoint. For example:
* `device_lists` becomes `org.matrix.msc3202.device_lists`
* `device_one_time_keys_count` becomes `org.matrix.msc3202.device_one_time_keys_count`

Appservices which support encryption but never see these fields (ie: server is not implementing this in an
unstable capacity) should be fine, though encryption might not function properly for them. It is the
responsibility of the appservice to try and recover safely and sanely, if desired, when the server is not
implementing this in an unstable capacity. This is not a concern once the MSC becomes stable in a released
version of the specification, as servers will be required to implement it.

For servers wishing to force appservices to opt-in to this behaviour, they may use `org.matrix.msc3202: true`
in the registration file. Servers will be able to check for "opt-in" behaviour once this MSC is stable by
seeing whether or not the appservice has an encryption-capable device recorded in its users namespaces.

To use device ID masquerading, implementations should use `org.matrix.msc3202.device_id` instead of `device_id`
in the query string while this MSC is considered unstable.
