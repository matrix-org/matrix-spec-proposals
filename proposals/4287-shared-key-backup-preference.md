# MSC4287: Sharing key backup preference between clients

Matrix allows for clients to [store backups of room
keys](https://spec.matrix.org/v1.14/client-server-api/#server-side-key-backups)
(encrypted) on the server.

Some users choose to disable this feature.

Some clients enable key backup by default, meaning that if a user signs in,
their keys may be backed up even though they have chosen not to back them up on
a different client. This is probably not the behaviour the user wants.

We describe a mechanism for remembering the user's preference in this matter,
so that a new client can behave correctly without needing to be told again that
the user does not want key backups.

## Proposal

We propose an event type to be stored in global account data,
`m.key_backup` whose contents consist of a single field `enabled` whose value is
boolean.

For example, if I `GET
/_matrix/client/v3/user/{userId}/account_data/m.key_backup`, the response looks
like:

```
{
    "m.key_backup": { "enabled": true }
}
```

If `enabled` is `true`, key backup for new sign-ins is on. If `enabled` is
`false`, key backup for new sign-ins is off. Otherwise, the value is
undetermined and the client should either treat it as off, or make a choice and
update the value to reflect it.

### Behaviour on sign-in

When a user signs in:

* If this event type exists in account data and contains the specified property
  in the correct format, clients which support key backup MUST use it to determine whether key backups
  should be enabled.

* If this event type does not exist in account data, or if it does not contain
  the `enabled` property, or if the value of `enabled` is not a boolean value,
  clients MUST ignore the existing value and:

    * EITHER choose whether to perform key backup (possibly based on user input)
      and update account data to reflect the choice,

    * OR not perform key backup.

### Behaviour on setting change

If the user turns on key backups, clients MUST set this event type in account
data, to `"enabled": true`.

If the user turns off key backups, clients MUST set this event type in account
data, to `"enabled": false`.

## Potential issues

It is possible that some use cases would involve a user having several clients,
some of which are using key backups, and some of which are not. If we want to
support that use case, we should allow some clients to opt out entirely from
reading or updating this account data.

We are not aware of these use cases, so if any are known it would be helpful to
let us know.

## Alternatives

### When the value is missing or invalid

There are alternative possibilities for the default behaviour (e.g. a
missing/invalid event could simply mean "off") but the described behaviour is
intended to be unambiguous and prevent two clients interpreting the same setting
differently, while also allowing clients to choose default behaviour suitable
for their audience.

### Dynamically reacting to changes

As specified, this only affects client behaviour when a user signs in. We could
specify that clients must watch the value of this account data and dynamically
change their key backup behaviour when it changes. This would increase the
severity of the security issues discussed below. Whether this behaviour would be
more or less surprising for the user is a potential discussion point.

Note that clients should already notice if a key backup is deleted, because
attempts to upload new keys will start failing.

### A proper unstable prefix

Because an existing implementation exists, the proposed unstable prefix has
different semantics from the final proposal. If this is deemed unacceptable, a
more normal unstable prefix could be used.

## Security considerations

Unencrypted account data is under the control of the server, so a malicious
server could:

* increase the user's attack surface by tricking clients into performing key backups
  against the user's will, or

* cause data loss by tricking clients into not performing key backups. (But
  servers can delete data from key backups at will, so this seems unimportant.)

This can be mitigated if clients make the setting, or any change to the setting,
visible to users, especially at the time when it affects behaviour (on sign-in).

## Unstable prefix

This is currently partially implemented in Element clients using a
reversed-sense format like:

```
{
    "m.org.matrix.custom.backup_disabled" { "disabled": true }
}
```

so we propose to use this form as an unstable prefix, and reverse the sense of
the boolean when this feature is stabilised.

## Dependencies

None

## Implementations

This is partially implemented (with the reverse-sense boolean) in Element
clients. The part that is currently not implemented is proactively setting the
value on sign-in.
