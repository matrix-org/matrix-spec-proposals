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

This proposal builds upon the earlier MSC3414, aiming to provide a simplified approach to encrypted
state events in Matrix. Currently, all room state is unencrypted and accessible to everyone in the
room, and occasionally people outside the room (such as via the public room directory, invite state,
or peekable rooms). Most events in room state could be encrypted to provide confidentiality, which
is what this MSC seeks to achieve more straightforwardly. Some parts, however, cannot be encrypted
to maintain a functioning protocol.

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

## Potential issues

<!--_Not all proposals are perfect. Sometimes there's a known disadvantage to implementing the proposal,
and they should be documented here. There should be some explanation for why the disadvantage is
acceptable, however - just like in this example._-->

At present, MSC4268
[does not require invitees to download the key bundle upon receiving an invite](https://github.com/matrix-org/matrix-spec-proposals/blob/rav/proposal/encrypted_history_sharing/proposals/4268-encrypted-history-sharing.md#actions-as-a-receiving-client);
instead, the key bundle is only fetched when the user joins the room, which could lead to problems
displaying the room name, topic, and avatar to invitees. One way to address this is to always
download the room key bundle on invite, but as MSC4268 notes, this introduces a potential
denial-of-service (DoS) attack vector.

If the client does not receive the keys needed to decrypt state events, the room may become
unusable, as information such as the room's name, topic, avatar, and other metadata will be
inaccessible. Additionally, if there are state events sent both before and after state encryption is
enabled, existing clients might display the unencrypted, outdated state.

Encrypting certain state events would prevent servers from displaying meaningful information about
rooms, as the room directory relies on being able to read these events. Rooms with encrypted
metadata could either appear as blank, generic, or broken entries in the public room list, or could
be omitted entirely, impeding room discovery. A similar issue arises with the space room list: if
room metadata is encrypted, clients and servers will be unable to display meaningful information
about child rooms within a space. It may be necessary to introduce an unencrypted state event,
`m.space.child_info`, that stores plaintext copies of a child room's avatar, name, and topic, which
can then be used over the encrypted metadata.

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

The current implementation uses an `io.element` vendor prefix for the `encrypt_state_events` flag
(i.e. `io.element.msc3414.encrypt_state_events`) for compatibility.

## Dependencies

This MSC builds on
[MSC3414](https://github.com/matrix-org/matrix-spec-propsals/tree/main/proposals/3414-encrypted-state-events.md)
and depends on [MSC4268](https://github.com/matrix-org/matrix-spec-proposals/pull/4268), neither of
which have been accepted into the spec at the time of writing.
