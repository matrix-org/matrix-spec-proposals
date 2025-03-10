# MSC4114: Matrix as a password manager

Password managers are used in abundance in both the personal and corporate
space to securely and conveniently store and share secrets. A whole ecosystem
of apps and services has sprouted and users have come to trust them for
their advanced security features.

Matrix, in turn, is a generalized protocol for securely storing and exchanging
data in a federated network, the primary use case being encrypted messaging.
This proposal outlines a scheme for extending Matrix to act as a password
manager by borrowing from built-in concepts such as encryption, rooms and
spaces. The underlying premise of this is that if it's secure enough to handle
personal communication, it should be secure enough to store passwords. Or put
another way, if you cannot trust Matrix to store your passwords, how can you
trust it to store your potentially equally sensitive private communication? The
truthiness of this assumption is underpinned later in this proposal by
comparing the cryptographic primitives used in Matrix and Bitwarden.

## Proposal

On a high level, vaults and secrets are represented as encrypted spaces and
rooms, respectively. Both use the existing encryption mechanics without
introducing further layers.

Home servers that support storing secrets can generally also allow messaging
via normal rooms and spaces. However, from a client perspective, it's
undesirable to have vaults constantly unlocked. Therefore, the messaging
capabilities should only be used for things like service announcements
and not for general chatting.

Federation is explicitly excluded from this proposal to reduce its scope.

### Vaults as spaces / secrets as rooms

Two new room types `m.vault` and `m.vault.secret` are introduced. Vault-rooms
work similar to [spaces] and can group other vault-rooms or secret-rooms.
Secret-rooms store the actual sensitive data, such as passwords.

Sending normal `m.room.message` events within vault- and secret-rooms is
discouraged - clients are not generally expected to have a way to render the
timeline of these rooms. As such, vault- and secret-rooms should be created
with `m.room.power_levels` which prohibit normal events by setting
`events_default` to a suitably high number. In the default power level
structure, this would be 100.

Additionally, vault- and secret-rooms should be created with encryption enabled
and a join rule of `invite` to prevent unintended access without explicit
sharing.

To include a secret (or another vault) in a vault, an `m.vault.child` state
event is introduced. The state key of the event is the room ID of the secret
(or vault) to include. In `content`, the event has a single field `via`
that lists servers to try and join through.

```
{
  "type": "m.vault.child",
  "state_key": "!roomid:example.org",
  "content": {
    "via": [
      "example.org",
      "other.example.org"
    ]
  },
  ...
}
```

No rooms other than those of type `m.vault` and `m.vault.secret` are allowed to
be stored in `m.vault.child` events.

Unlike with spaces, there is no corresponding `m.vault.parent` event, meaning a
vault or secret does not know which parent vaults it is contained in. While
this backlink exists in spaces to aid discoverability, this feature appears
unessential for secret hierarchies.

### Secret events

To store secrets, a new room event type `m.secret` is introduced. Building upon
[MSC1767], secret-events contain a single `m.secret.sections` content block that
holds an ordered array of section definitions with the following properties:

- `title` – A textual description (optional)
- `fields` – An ordered array of field definitions (required)

Fields in turn have the following properties:

- `title` – A textual description (optional)
- `type` – An identifier for the type of value stored (optional). One of:
  - `text` – Any text. If `type` is omitted, this is the default.
  - `username` – A username or other account identifier
  - `password` – A password or other account secret
  - `url` – A web address
  - `email` – An email address
  - `address` – A street or postal address
  - `date` – A date represented as a UNIX timestamp
  - `monthyear` – A month / year combination expressed as `MM/YY`
  - `phonenumber` – A phone number
  - `security_question` – A security question answer. The question itself is to be
    put into the `title` field.
- `value` – The content stored (required). For fields of type `date`, this is an
  integer, otherwise a string.
- `conceal` – Display hint indicating whether or not clients should obscure the value
  by default (optional). Defaults to `false` for all field types except `password`.

```
{
  "type": "m.secret",
  "content": {
    "m.secret.sections": [{
      "fields": [{
        "type": "username",
        "value": "johndoe"
      }, {
        "type": "password",
        "value": "johnboy84"
      }]
    }, {
      "title": "Security questions",
      fields: [{
        "type": "security_question",
        "title": "What is your favorite ice cream flavor?",
        "value": "Lemon"
      }]
    }]
  }
}
```

Clients may choose to use the order of sections and fields in the event for
sorting data in the UI but are not required to do so.

`m.secret` events are not allowed to be used in rooms other than those of type
`m.vault.secret` and should always be encrypted.

When updating secrets, clients should use [event replacements] which allows
building a history of changes. Similarly, clients can use [redactions] to
clear parts of the change history. At any given time, a secret-room should,
thus, contain at most one non-redacted, non-replaced `m.secret` event which
gives the current state of the secret.

### Other aspects

Vaults and secrets can be shared through standard room membership. When adding
a secret-room (or another vault-room) to a vault-room, a restricted [join rule]
should be set so that being invited into a vault-room enables users to also
join all of its child-rooms.

The standard `m.room.name` and `m.room.avatar` state events can be used to label
and decorate vaults and secrets. These are not currently encryptable but will be
once [MSC3414] lands. While exposing vault and secret names is not considered a
security concern by other password managers such as [pass], it can still be a
privacy concern. Therefore, clients should warn users appropriately in the meantime.

### Matrix vs. Bitwarden

#### Login

[Bitwarden's protocol] uses key stretching on several levels to make it harder
to brute-force a login. The client uses PBKDF2 with 600,000 iterations to
derive a 256-bit master key from the account password and email. The account
password and master key are then turned into a master password hash using
PBKDF-SHA256. This hash is sent to the server where it is hashed again using
PBKDF2-SHA256 with 600,000 iterations before verifying the login.

Matrix, on the other hand, doesn't mandate the use of key derivation functions
during login and instead makes this aspect an implementation detail. Synapse,
for instance, uses [bcrypt] with a default of [12 iterations][^1] for
`m.login.password` flows. Keycloak, as an exemplary OIDC provider, uses
[PBKDF2-SHA512 with 210,000 iterations] by default.

It's important to note here that login to a Matrix account doesn't actually
give access to the Megolm keys required to decrypt historic events. The keys
have to either be shared from another existing device or retrieved from the
server-side key backup. The latter is encrypted using AES-256 CBC where the
[256-bit curve25519 private key] is commonly stored in 4S. The key that
unlocks 4S itself can be derived from a passphrase using PBKDF2 where the
number of iterations is [configurable].

In summary, Matrix can be configured to provide a similar level of brute-force
login protection as Bitwarden using key stretching on multiple levels.

#### Encryption

Bitwarden uses a single 512-bit key, consisting of a 256-bit encryption key
and a 256-bit MAC key, to symmetrically encrypt all vault items using
[AES-256 CBC]. To protect this key, it is encrypted with the HKDF-stretched
master key using AES-256 and a random 128-bit initialization vector. The
encrypted key is then synced across clients via the server.

Matrix, on the other hand, employs [Megolm] which also uses AES-256 CBC for
symmetric encryption but obtains the key differently. Megolm is session-based
where each session uses a ratchet that is initialized with 1024-bit
cryptographically secure random data. The ratchet is wound forward through
hashing on each encrypted message and the symmetric encryption key is derived
by hashing the ratchet value. Additionally Megaolm uses Ed25519 to provide
message authenticity through signatures. Megolm keys are synced among clients
via either key requests in encrypted to-device messages or the server-side key
backup.

To sum up, the main difference here is that Bitwarden uses a single symmetric
key to encrypt everything whereas Matrix uses per-event keys.

#### Sharing

Bitwarden only allows sharing vault items through organizations. Like users,
organizations have a single symmetric key that is used to encrypt all vault
items. The symmetric key is encrypted with the public part of the organization
creator's RSA key and synced across the creator's devices via Bitwarden's
servers. Each user's RSA key pair is generated upon account creation using
RSA-2048 which, interestingly, is below what the NSA [recommends]. When another
user is invited into the organization, the inviter encrypts the symmetric key
with the invitee's public RSA key and shares it via Bitwarden's servers.
Bitwarden doesn't appear to detail what happens when a user leaves an
organization.

In Matrix, users are invited into rooms to share future encrypted events with
them but clients don't currently share keys for past events with other users.
For rooms that use the `shared` history visibility setting, the accepted
[MSC3061] defines a way for the inviter to share keys for past messages with
the invitee – even without a key share request. The sharing is done via
[`m.forwarded_room_key`] to-device messages that are encrypted using Olm which
uses Curve25519.

In summary, there are no material differences here other than the RSA vs.
Curve25519 discrepancy and the already known fact that Bitwarden relies on a
single key while Matrix uses per-message keys.

## Potential issues

When not sharing, UTDs on encrypted secrets would be fatal and result in loss
of access to the secret. Clients might be able to mitigate this by offering
offline encrypted backups.

## Alternatives

Instead of dedicated space-like `m.vault` rooms, normal [spaces] could be used to
group secret-rooms. This has the downside that secret-rooms and other room types
can mingle in the hierarchy which makes it harder for clients to recognise spaces
devoted exclusively to storing secrets.

Multiple `m.secret` events could be stored in the same room, eliminating the
need to have different room types for vaults and secrets. However, this doesn't
allow for fine-grained sharing of secrets with other users and would make it
impossible to reuse `m.room.name` and `m.room.avatar` events to annotate secrets.

Secrets could be stored in state events which already have replacement semantics.
As mentioned earlier though, state events are not encryptable yet.

The sections and fields of `m.secret` events could be broken out into separate
events. This would, however, complicate client display logic and require an
additional way of sorting sections and fields.

## Security considerations

Until [MSC3414] lands, `m.room.name` and `m.room.avatar` events will leak meta
data of vaults and secrets.

## Unstable prefix

Until this proposal is accepted into the spec implementations should refer to:

- `m.vault` as `org.matrix.msc4114.vault`
- `m.vault.secret` as `org.matrix.msc4114.vault.secret`
- `m.vault.child` as `org.matrix.msc4114.vault.child`
- `m.secret` as `org.matrix.msc4114.secret`
- `m.secret.sections` as `org.matrix.msc4114.secret.sections`

## Dependencies

None.

[12 iterations]: https://github.com/element-hq/synapse/blob/develop/synapse/config/registration.py?rgh-link-date=2024-03-07T20%3A31%3A39Z#L79
[256-bit curve25519 private key]: https://spec.matrix.org/v1.10/client-server-api/#recovery-key
[AES-256 CBC]: https://bitwarden.com/help/what-encryption-is-used
[Bitwarden's protocol]: https://bitwarden.com/help/bitwarden-security-white-paper/
[bcrypt]: https://github.com/element-hq/synapse/blob/develop/synapse/handlers/auth.py?rgh-link-date=2024-03-07T20%3A31%3A39Z#L1642
[configurable]: https://spec.matrix.org/v1.10/client-server-api/#deriving-keys-from-passphrases
[event replacements]: https://spec.matrix.org/latest/client-server-api/#event-replacements
[join rule]: https://spec.matrix.org/v1.3/client-server-api/#mroomjoin_rules
[Megolm]: https://gitlab.matrix.org/matrix-org/olm/blob/master/docs/megolm.md
[MSC1767]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767
[MSC3061]: https://github.com/matrix-org/matrix-spec-proposals/pull/3061
[MSC3414]: https://github.com/matrix-org/matrix-spec-proposals/pull/3414
[`m.forwarded_room_key`]: https://spec.matrix.org/v1.10/client-server-api/#mforwarded_room_key
[pass]: https://www.passwordstore.org/
[PBKDF2-SHA512 with 210,000 iterations]: https://www.keycloak.org/docs/latest/server_admin/#hashing-iterations
[recommends]: https://en.wikipedia.org/wiki/Commercial_National_Security_Algorithm_Suite
[redactions]: https://spec.matrix.org/latest/client-server-api/#redactions
[spaces]: https://spec.matrix.org/v1.3/client-server-api/#spaces

[^1]: For a high-level comparison of bcrypt and PBKDF2 performance, see https://security.stackexchange.com/questions/4781/do-any-security-experts-recommend-bcrypt-for-password-storage/6415#6415.
