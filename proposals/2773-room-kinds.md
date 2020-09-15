# MSC2773: Room kinds

This is an alternative to [MSC1840](https://github.com/matrix-org/matrix-doc/pull/1840) with inspiration
taken from canonical DMs ([MSC2199](https://github.com/matrix-org/matrix-doc/pull/2199)).

Currently rooms are implicitly for conversation purposes, however there are several use cases where
non-conversational data might be present. Typically this could be avoided by using "protocol"
(non-conversational) rooms only on dedicated accounts, however this isn't always possible. MSC1840
solves the problem by specifying a state event which indicates a type of room with an opportunity to
filter them out.

This MSC uses a similar approach, though puts the burden on the homeserver to figure out.

## Proposal

In the `summary` of `/sync`, a field named `m.kind` is introduced. Like other fields in the summary,
the `m.kind` can be omitted if unchanged since the last sync.

The `m.kind` value grammar follows [MSC2758](https://github.com/matrix-org/matrix-doc/pull/2758)'s
proposal.

Specified types are currently:

* `m.conversational` - General conversational room. This is the default.
* `m.protocol` - A "protocol" room where the information contained within is not intended to be consumed
  by humans. Further identification of the room is left to the individual functionality of the room. For
  example, a profile room might be identified by the presence of a `m.profile` state event.

It is the intention of this MSC to allow protocol rooms to mix different functionality into them where
possible. For example, a protocol room could mix moderation policies, profiles, and groups into a single
room where the context could be left ambiguous (ie: moderation policies could be related to the user
represented by the profile, or could just be a dumping ground - implementation behaviour is not a concern
for this MSC).

MSC2199 defines `m.dm` as an `m.kind` - this proposal does not alter that behaviour and assumes it
is a more specific type for `m.conversational`.

Conversational-focused clients SHOULD hide any kinds of rooms they do not recognize or cannot support.
Typically this means that clients would show `m.dm` and `m.conversational` rooms only, leaving all the
protocol and custom kinds out of view of the user.

**TODO: Clarify this next paragraph to make sense.**

Clients are expected to use the rooms in the `/sync` for some purpose, however. Typically protocol rooms
will be functionality such as profiles, groups, or something else relevant to a more abstract feature
of the client.

**TODO: How is a server expected to know what kind something is.**

## Potential issues

**TODO**.

## Alternatives

As mentioned, MSC1840 solves a similar problem. This MSC might work well in conjunction with it rather
than against it.

**TODO: Formalize a comparison.**

## Security considerations

**TODO**.

## Unstable prefix

Implementations should use `org.matrix.msc2773.` instead of `m.` while this MSC has not entered a released
version of the specification.
