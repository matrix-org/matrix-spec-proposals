# MSC2579: Improved room tagging support

Currently the specification supports 2 kinds of ordering rooms: whatever the client decides and
manually specified ordering through [room tagging](https://matrix.org/docs/spec/client_server/r0.6.0#room-tagging).

Clients and users alike would like to be able to keep room tagging, but let the client's default
ordering take effect (typically most recently active first). The room tagging specification as
written at the moment prohibits this from happening.

## Proposal

Users can pick what sort of behaviour they want out of their room tags by specifying a configuration
event on their own (not-room) account data. The configuration object takes the shape of:

```json
{
  "ordering": "m.client_default"
}
```

The event type is `m.tag.TheTag`, which leads to slightly ugly-looking event types like
`m.tag.m.favourite`, however account data does not support state_key semantics. Introducing
state_key semantics for account data is best left for another MSC, as even this use case is
not a strong one for such semantics.

The `ordering` is optional and is either `m.client_default` or `m.manual`. Clients can specify
their own types using the standard namespace conventions within the spec (Java package name
style) - clients which do not recognize the `ordering` are to use `m.client_default` instead as
it most closely resembles what the client's custom algorithm will be doing (deciding how best
to represent the rooms).

`m.manual` means to use the `order` property as currently specified on individual room tags (`m.tag`
room account data).

`m.client_default` is used to indicate that the client should order the rooms how it feels is
best represented, which is typically going to be most recently active rooms first. Clients are
encouraged to use namespaced values instead if they intend to use an ordering that is different from \
the typical case.

The lack of a tag configuration in account data implies the defaults are to be used instead. This
means that tags defined on rooms *do not* need to be configured in account data as well. Clients
remain expected to figure out the list of rooms a tag contains on their own.

The defaults for the configuration also mean that no changes are required to the endpoints supplied
for room tagging. Clients are still able to specify an `order` on any tag, however this is a largely
futile effort if the `ordering` is not `m.manual` (though it is possible that a client's custom
`ordering` takes the property into account).

The `ordering` has the following default values:

* For `m.favourite`, `m.manual`
* For all other `m.*` tags, `m.client_default`
* For all other tags, `m.manual`

The rationale for these complicated defaults is to better match the current typical user expectation
with respect to tags: users tend to expect that the low priority rooms will behave similar to their
untagged rooms, and that all other tags can be manually ordered. Some users are an exception to this
common expectation though, hence this proposal to allow them to decide.

## Potential issues

The various defaults and default conditions could lead to bugs due to their complexity, however it
is believed these defaults best capture the typical user's expectation of a Matrix client.

## Alternatives

A total revamp of tags could be done here, requiring a configuration object and the server to track
which rooms belong to which tags for example, however Occam's Razor begins to take effect.

## Unstable prefix

While this MSC is not merged to the spec, clients are to use `org.matrix.msc2579` in place of the
new `m.*` prefixes defined in this proposal.

For clarity, that means `m.tag.m.favourite` becomes `org.matrix.msc2579.m.favourite` and `m.manual`
becomes `org.matrix.msc2579.manual`.
