# MSC4114: Matrix as a password manager

Password managers are used in abundance in both the personal and corporate
space to securely and conveniently store and share secrets. This proposal
outlines a scheme for storing a hierarchy of secrets in Matrix by borrowing
from standard concepts such as rooms and spaces.

## Proposal

### Secret hierarchy

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
(or other vault) to include. In `content`, the event has a single field `via`
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
vault or secret does not know which parent vaults contain it. While in spaces
this backlink exists to aid discoverability, this feature appears unessential
for secret hierarchies.

### Storing secrets

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

Clients can choose to use the order of sections and fields in the event for
sorting data in the UI but are not required to do so.

`m.secret` events are not meant to be used in rooms other than those of type
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

## Potential issues

When sharing _and_ federating, secrets can end up being stored on different home
servers over time. However, federation is probably not a desirable feature of
password managers anyway.

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

- `m.vault` as `org.matrix.mscXXXX.vault`
- `m.vault.secret` as `org.matrix.mscXXXX.vault.secret`
- `m.vault.child` as `org.matrix.mscXXXX.vault.child`
- `m.secret` as `org.matrix.mscXXXX.secret`
- `m.secret.sections` as `org.matrix.mscXXXX.secret.sections`

## Dependencies

None.

[event replacements]: https://spec.matrix.org/latest/client-server-api/#event-replacements
[join rule]: https://spec.matrix.org/v1.3/client-server-api/#mroomjoin_rules
[MSC1767]: https://github.com/matrix-org/matrix-spec-proposals/pull/1767
[MSC3414]: https://github.com/matrix-org/matrix-spec-proposals/pull/3414
[pass]: https://www.passwordstore.org/
[redactions]: https://spec.matrix.org/latest/client-server-api/#redactions
[spaces]: https://spec.matrix.org/v1.3/client-server-api/#spaces
