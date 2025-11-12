# MSC4362: Simplified Encrypted State Events

<!--_Note: Text written in italics represents notes about the section or proposal process. This document
serves as an example of what a proposal could look like (in this case, a proposal to have a
template) and should be used where possible._

_In this first section, be sure to cover your problem and a broad overview of the solution. Covering
related details, such as the expected impact, can also be a good idea. The example in this document
says that we're missing a template and that things are confusing and goes on to say the solution is
a template. There's no major expected impact in this proposal, so it doesn't list one. If your
proposal was more invasive (such as proposing a change to how servers discover each other) then that
would be a good thing to list here._

_If you're having troubles coming up with a description, a good question to ask is "how does this
proposal improve Matrix?" - the answer could reveal a small impact, and that is okay._-->

Currently, all state events are unencrypted. This allows the homeserver to read state event content
in order to do its job in implementing the Matrix protocol: processing room membership and power
levels, and performing state resolution. A side effect of homeservers being able to read state event
content is that anyone with access to the homeserver's data (such as an administrator or a
successful attacker) can also read these events.

The set of events that are actually needed by the homeserver is quite small, so we propose
encrypting everything else. This provides a significant reduction in the amount of visible metadata,
at the cost of some user inconvenience (because users need decryption keys to see state information
like room names).

[MSC3414](https://github.com/matrix-org/matrix-spec-proposals/pull/3414) has similar goals to this
proposal, but it specifies a concrete mechanism for hiding encrypted event types, and resolving
state where it cannot be fully resolved by the server. We think this approach could be problematic,
and may effectively require us to implement full state resolution on the client. Here, we simply
propose the "easy" part: encrypting state events without hiding their types from the server.

The intent is to allow real-world usage of encrypted state, accepting the limitations imposed
because state is hidden from users in situations where they might want it, without requiring us to
draw conclusions on the trickiest parts (sharing historical state, resolving state the server can't
identify, and exposing room names and topics).

## Proposal

<!--_Here is where you'll reinforce your position from the introduction in more detail, as well as cover
the technical points of your proposal. Including rationale for your proposed solution and detailing
why parts are important helps reviewers understand the problem at hand. Not including enough detail
can result in people guessing, leading to confusing arguments in the comments section. The example
here covers why templates are important again, giving a stronger argument as to why we should have a
template. Afterwards, it goes on to cover the specifics of what the template could look like._-->

Under this proposal, all room state events can be encrypted, except events critical to maintain the
protocol. Those critical events are:

- `m.room.create`
- `m.room.member`
- `m.room.join_rules`
- `m.room.power_levels`
- `m.room.third_party_invite`
- `m.room.history_visibility`
- `m.room.guest_access`
- `m.room.encryption`

An encrypted state event looks very similar to a regular encrypted room message: the `type` becomes
`m.room.encrypted` and the `content` is the same shape as a regular `m.room.encrypted` event. The
`state_key` for encrypted state events is constructed from the plaintext `type` and `state_key`
fields, formatted as `{type}:{state_key}`, preserving the uniqueness of the `type`-`state_key`
mapping required for the server to perform state resolution.

To track whether a room has state encryption enabled, and to preserve compatibility with older
clients that cannot work with encrypted state events, a new boolean field `encrypt_state_events` is
introduced to the content of `m.room.encryption`, which determines if clients should send state
encrypted events.

Clients are expected to decrypt all room state on reception and validate the packed state key
matches the decrypted type and state key. This ensures malicious clients cannot send state events
that masquerade as message events and vice versa.

This MSC relies on the room key sharing mechanism outlined in
[MSC4268](https://github.com/matrix-org/matrix-spec-proposals/pull/4268), which enables clients to
decrypt historical state events.

## Limitations

### Room names and topics are not visible from outside

The name and topic of a room with encrypted state will not be visible without access to the keys
used to encrypt them. Without additional proposals, this will make it impossible to provide a room
directory entry, list the room inside a space, or display room details when invited.

### State sent before joining the room is inaccessible

Upon joining a room with encrypted state, new users will not be able to decrypt room state, making
the room name, topic and other information (e.g. ongoing whiteboard sessions or call) inaccessible.

This limitation does not apply if
[MSC4268](https://github.com/matrix-org/matrix-spec-proposals/pull/4268) is available and the room
settings allow sharing the relevant events.

## Potential issues

<!--_Not all proposals are perfect. Sometimes there's a known disadvantage to implementing the proposal,
and they should be documented here. There should be some explanation for why the disadvantage is
acceptable, however - just like in this example._-->

The `:` delimiter may not be suitable in all cases. Additionally, string packing introduces size
limitations, as the combined length of the packed string cannot exceed the 255-byte maximum for a
state key. This effectively reduces the available space for both event types and state keys.

## Alternatives

<!--
_This is where alternative solutions could be listed. There's almost always another way to do things
and this section gives you the opportunity to highlight why those ways are not as desirable. The
argument made in this example is that all of the text provided by the template could be integrated
into the proposals introduction, although with some risk of losing clarity._-->

A number of alternatives to string-packing the plaintext `type` and `state_key` are possible:

- Preserving the values of `type` and `state_key`;
- Introducing an adjacent `true_type` field;
- Hashing `type` and `state_key` with HMAC.

### Preserved Fields

Rather than string-packing the `type` and `state_key` together, we could preserve these values on
the encrypted event, but still encrypt the event content. This provides the same (lack of)
confidentiality as the approach laid out in this MSC while avoiding string packing. However, this
approach would introduce a difference between the encryption of message events and state events,
which may be undesirable.

### Adjacent Type Field

In a similar manner to preserved fields, we could introduce a new `true_type` field to the events
`content`, which holds the plaintext type of the state event. This would require modifying the
server to utilise this field over the value of the `type` field, which may be undesirable.

### HMAC-hashed `state_key`s

This is the _ideal solution_, as it hides the state key and type from the server entirely; however,
there are some considerable downsides. We have two choices:

- Use a static key generated on room creation to encrypt all state events for the duration of the
  room's existence;
- Rotate the key periodically, perhaps deriving it from the current Megolm session key.

The former case lacks post-compromise confidentiality (PCS), which, although quite hard to pull off
as an attacker, makes this approach undesirable. This approach is also vulnerable to frequency
analysis through comparison between the distribution of state key hashes and a known distribution of
public `type`-`state_key` pairs.

The latter option has issues too: rotating the key breaks the server's ability to track room state,
since two events with identical state keys will produce encrypted events with different hashed state
keys when using different (HMAC) keys. The server will treat each as unique and send both to
clients. This would require clients to perform state resolution locally (to decide which of two
clashing events to accept), which in turn would require them to consume and understand the room DAG.
This approach may also be vulnerable to frequency analysis, but, based on some naive calculations,
the probability a malicious server is able to infer the hash to `type`-`state_key` mapping correctly
becomes increasingly unlikely as the number of state events encrypted by any given key decreases.

## Security considerations

This proposal relies on the security of the Olm/Megolm primitives, and an attack against them could
be a viable method to derive partial or complete knowledge of the encrypted content.

Confidential information **should not** be stored in the `type` and `state_key` fields, since both
are present in plaintext.

## Unstable prefix

<!-- _If a proposal is implemented before it is included in the spec, then implementers must ensure that
the implementation is compatible with the final version that lands in the spec. This generally means
that experimental implementations should use `/unstable` endpoints, and use vendor prefixes where
necessary. For more information, see [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324).
This section should be used to document things such as what endpoints and names are being used while
the feature is in development, the name of the unstable feature flag to use to detect support for
the feature, or what migration steps are needed to switch to newer versions of the proposal._-->

| Name | Stable name | Unstable name |
| - | - | - |
| Property in `m.room.encryption` event | `encrypt_state_events` | `io.element.msc4362.encrypt_state_events` |

## Dependencies

This proposal is a more limited alternative to
[MSC3414](https://github.com/matrix-org/matrix-spec-propsals/tree/main/proposals/3414-encrypted-state-events.md).

The limitations of this proposal are improved somewhat if
[MSC4268](https://github.com/matrix-org/matrix-spec-proposals/pull/4268) is available.
