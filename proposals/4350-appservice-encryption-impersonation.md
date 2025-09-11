# MSC4350: Permitting encryption impersonation for appservices
Bridges that currently support end-to-bridge encryption do so by creating a
single encryption identity for the bridge bot and using that identity to send
and receive keys. The single identity method is much more efficient than
creating separate identities for each ghost user, but has the downside of not
being technically correct, as it abuses a lack of validation in where e2ee keys
come from.

Fixing the lack of validation is planned as a part of [MSC4153]. However, just
adding validation without creating any exceptions would force bridges to either
use the inefficient method of redundant crypto identities or simply turn
encryption off, neither of which are good options.

In addition to ghost users, some bridges have the concept of "double puppeting",
where the bridge is given access to send messages as a real Matrix user instead
of an appservice ghost.

[MSC4153]: https://github.com/matrix-org/matrix-spec-proposals/pull/4153

## Proposal
The proposed solution is defining special device metadata to indicate that
another user is allowed to cryptographically impersonate the owner of the
device.

The device keys object, which is written by `/keys/upload` and read by
`/keys/query`, gets a new optional `impersonator` field. The field contains a
full device keys object, excluding `signatures`.

The device owned by the ghost user (or real Matrix user in case of double
puppeting) with the `impersonator` field will be referred to as the
"impersonatable" device, while the bridge bot's device is the "impersonator"
device.

The `algorithms` and `keys` fields are still present and required, but MUST be
an empty list and an empty object respectively when an impersonator is defined.
Because there are no keys, `signatures` will not include a signature from the
device itself. Instead, there MUST be a signature from the user/device
combination defined in the `impersonator` field.

The lack of keys is used to signal that the impersonatable device can't receive
keys on its own. Instead, the impersonator user should be a member of the room
to receive keys the standard way.

### Client behavior
Following the rules of [MSC4153], an impersonated message is considered to be
from a "non-cross-signed device" if:

* the user specified in `impersonator` is not a member of the room
* the device specified in `impersonator` is not cross-signed itself
* the user who owns the impersonatable device has cross-signing keys and the
  impersonatable device is not signed by the user's self-signing key

If any of the above conditions match, clients should behave as they do with
other non-cross-signed messages under [MSC4153]. If not, then the impersonated
message is trusted and should be displayed as usual. Clients MAY still choose to
display an indication that the message is from an impersonator device.

The requirement for cross-signing means that bridges will have to get double
puppeting devices verified, either by asking for the user's recovery key, or
having the user upload a signature themselves. However, ghost users owned by
the appservice will not be required to upload cross-signing keys at all.

To help verify double puppeting sessions, clients can offer a button to easily
cross-sign impersonatable devices. When offering such a button, clients SHOULD
prominently display the impersonator user ID and make it clear that the bot will
be able to send messages as the user. Clients MAY also suggest or require that
the impersonator device is marked as verified before the impersonatable device
can be signed. However, interactive verification SHOULD NOT be required, as it
doesn't make much sense when the other party is a bot.

### Server behavior
When `impersonator` is present in device keys, servers MUST include signatures
from the impersonator user in `/keys/query` responses both in the C-S and S-S
APIs regardless of who is querying the keys.

### Example
<details>
<summary>Bridge ghost device keys</summary>

```jsonc
{
    "algorithms": [],
    "device_id": "ZVYTEW6WS0",
    "impersonator": {
        "algorithms": [
            "m.olm.v1.curve25519-aes-sha2",
            "m.megolm.v1.aes-sha2"
        ],
        "device_id": "JLAFKJWSCS",
        "keys": {
            "curve25519:JLAFKJWSCS": "[bridge-device-curve25519-key]",
            "ed25519:JLAFKJWSCS": "[bridge-device-ed25519-key]"
        },
        "user_id": "@bridgebot:example.com"
    },
    "keys": {},
    "signatures": {
        "@bridgebot:example.com": {
            "ed25519:JLAFKJWSCS": "[signature-from-bridge-device]"
        }
    },
    "user_id": "@bridge_123456:example.com"
}
```

</details>
<details>
<summary>Double puppeting device keys, note the added cross-signing signature</summary>

```jsonc
{
    "algorithms": [],
    "device_id": "S9ON0B1TCA",
    "impersonator": {
        "algorithms": [
            "m.olm.v1.curve25519-aes-sha2",
            "m.megolm.v1.aes-sha2"
        ],
        "device_id": "JLAFKJWSCS",
        "keys": {
            "curve25519:JLAFKJWSCS": "[bridge-device-curve25519-key]",
            "ed25519:JLAFKJWSCS": "[bridge-device-ed25519-key]"
        },
        "user_id": "@bridgebot:example.com"
    },
    "keys": {},
    "signatures": {
        "@bridgebot:example.com": {
            "ed25519:JLAFKJWSCS": "[signature-from-bridge-device]"
        },
        "@user:example.com": {
            "ed25519:selfsigningkey": "[signature-from-user-cross-signing-key]"
        }
    },
    "user_id": "@user:example.com"
}
```

</details>

## Potential issues
The approach taken by this MSC assumes that the bridge bot will be present in
all rooms (see alternative below).

## Alternatives
### Send room keys to impersonator devices
To remove the requirement for the bridge bot being a member of all rooms, we
could define that clients must send keys to any impersonator devices in the
room. However, we prefer an explicit bot membership over a hidden key sharing
mechanism. Additionally, there would need to be a way to turn off sending
message keys to impersonator devices to avoid the bridge receiving message keys
in all encrypted rooms when using double puppeting.

### Disable encryption
As mentioned in the introduction, bridges could simply not use encryption. This
is not considered an acceptable alternative, as there are valid reasons to use
encryption with bridges, where disabling it would reduce privacy.

### Separate encryption identities for all ghosts
The other option is creating separate full encryption identities for each ghost.
However, that would require a lot more key management for bridges, plus it would
require users' devices to encrypt every megolm session for every ghost
separately even though all the ghosts are in the same bridge process.

[MSC4261](https://github.com/matrix-org/matrix-spec-proposals/pull/4261) could
be used to avoid receiving keys for the ghost users, but it would still require
the bridge to create Olm sessions between each ghost and recipient device to
share keys to users.

## Security considerations
The requirement to cross-sign the impersonatable device could be bypassed by a
malicious server that hides the user's cross-signing keys. However, hiding
cross-signing will also prevent other devices of that user from working, so it
should be easily noticeable.

## Unstable prefix
`fi.mau.msc4350.impersonator` should be used instead of `impersonator` in
device metadata.

## Dependencies
This MSC enhances [MSC4153], but does not formally depend on it.
