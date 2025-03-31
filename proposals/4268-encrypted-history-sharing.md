# MSC4268: Sharing room keys for past messages

In Matrix, rooms can be configured via the
[`m.room.history_visibility`](https://spec.matrix.org/v1.14/client-server-api/#room-history-visibility)
state event such that previously-sent messages can be visible to users that
join the room. However, this is ineffective in encrypted rooms, where new
joiners will lack the keys necessary to decrypt historical messages.

This proposal defines a mechanism by which existing room members can share the
decryption keys with new members, for example when inviting them, thus giving
the new members access to historical messages.

A previous propsal,
[MSC3061](https://github.com/matrix-org/matrix-spec-proposals/pull/3061) aimed
to solve a similar problem; however, the mechanism used did not scale well. In
addition, the implementation in `matrix-js-sdk` was subject to a [security
vulnerability](https://matrix.org/blog/2024/10/security-disclosure-matrix-js-sdk-and-matrix-react-sdk/)
which this proposal addresses.

## Proposal

### `shared_history` property in `m.room_key` events

Suppose Alice and Bob are participating in an encrypted room, and Bob now
wishes to invite Charlie to join the chat. If the [history
visibility](https://spec.matrix.org/v1.14/client-server-api/#room-history-visibility)
settings allow, Bob can share the message decryption keys for previously sent
messages with Charlie. However, it is dangerous for Bob to take the server's
word for the history visibility setting: a malicious server admin collaborating
with Charlie could tell Bob that the history visibility was open when in fact
it was restricted. In addition, the history visibility in a given room may have
been changed over time and it can be difficult for clients to estalish which
setting was in force for a particular Megolm session.

To counter this, we add a `shared_history` property to `m.room_key` messages,
indicating that the creator of that Megolm session understands and agrees that
the session keys may be shared with newly-invited users in future. For example:

```json
{
  "type": "m.room_key",
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "room_id": "!room_id",
    "session_id": "session_id",
    "session_key": "session_key",
    "shared_history": true
  }
}
```

In other words: when Alice wants to send a message in the room she shares with
Bob, she first checks the `history_visibility`. If it is `shared` or
`world_readable`, then when she sends the Megolm keys to Bob, she sets
`shared_history` to `true`.

Clients SHOULD show a visual indication to users that their encrypted messages
may be shared with future room members in this way.

If the history visibility changes in a way that would affect the
`shared_history` flag (i.e., it changes from `joined` or `invited` to `shared`
or `world_readable`, or vice versa), then clients MUST rotate their outbound
megolm session before sending more messages.

In addition, a `shared_history` property is added to the [`BackedUpSessionData`
type](https://spec.matrix.org/v1.14/client-server-api/#definition-backedupsessiondata)
in key backups (that is, the plaintext object that gets encrypted into the
`session_data` field) and the [`ExportedSessionData`
type](https://spec.matrix.org/v1.14/client-server-api/#definition-exportedsessiondata). In
both cases, the new property is set to `true` if the session was shared with us
with `shared_history: true`, and `false` otherwise.

For example:

```json
{
  "algorithm": "m.megolm.v1.aes-sha2",
  "forwarding_curve25519_key_chain": [
    "hPQNcabIABgGnx3/ACv/jmMmiQHoeFfuLB17tzWp6Hw"
  ],
  "sender_claimed_keys": {
    "ed25519": "aj40p+aw64yPIdsxoog8jhPu9i7l7NcFRecuOQblE3Y"
  },
  "sender_key": "RF3s+E7RkTQTGF2d8Deol0FkQvgII2aJDf3/Jp5mxVU",
  "session_key": "AgAAAADxKHa9uFxcXzwYoNueL5Xqi69IkD4sni8Llf...",
  "shared_history": true
}
```

In all cases, an absent or non-boolean `shared_history` property is treated the same as
`shared_history: false`.


### Key bundle format

TODO

### To-device message format

## Potential issues

*Not all proposals are perfect. Sometimes there's a known disadvantage to implementing the proposal,
and they should be documented here. There should be some explanation for why the disadvantage is
acceptable, however - just like in this example.*

Someone is going to have to spend the time to figure out what the template should actually have in it.
It could be a document with just a few headers or a supplementary document to the process explanation,
however more detail should be included. A template that actually proposes something should be considered
because it not only gives an opportunity to show what a basic proposal looks like, it also means that
explanations for each section can be described. Spending the time to work out the content of the template
is beneficial and not considered a significant problem because it will lead to a document that everyone
can follow.


## Alternatives

*This is where alternative solutions could be listed. There's almost always another way to do things
and this section gives you the opportunity to highlight why those ways are not as desirable. The
argument made in this example is that all of the text provided by the template could be integrated
into the proposals introduction, although with some risk of losing clarity.*

Instead of adding a template to the repository, the assistance it provides could be integrated into
the proposal process itself. There is an argument to be had that the proposal process should be as
descriptive as possible, although having even more detail in the proposals introduction could lead to
some confusion or lack of understanding. Not to mention if the document is too large then potential
authors could be scared off as the process suddenly looks a lot more complicated than it is. For those
reasons, this proposal does not consider integrating the template in the proposals introduction a good
idea.


## Security considerations

**All proposals must now have this section, even if it is to say there are no security issues.**

*Think about how to attack your proposal, using lists from sources like
[OWASP Top Ten](https://owasp.org/www-project-top-ten/) for inspiration.*

*Some proposals may have some security aspect to them that was addressed in the proposed solution. This
section is a great place to outline some of the security-sensitive components of your proposal, such as
why a particular approach was (or wasn't) taken. The example here is a bit of a stretch and unlikely to
actually be worthwhile of including in a proposal, but it is generally a good idea to list these kinds
of concerns where possible.*

MSCs can drastically affect the protocol. The authors of MSCs may not have a security background. If they
do not consider vulnerabilities with their design, we rely on reviewers to consider vulnerabilities. This
is easy to forget, so having a mandatory 'Security Considerations' section serves to nudge reviewers
into thinking like an attacker.

## Unstable prefix

*If a proposal is implemented before it is included in the spec, then implementers must ensure that the
implementation is compatible with the final version that lands in the spec. This generally means that
experimental implementations should use `/unstable` endpoints, and use vendor prefixes where necessary.
For more information, see [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324). This section
should be used to document things such as what endpoints and names are being used while the feature is
in development, the name of the unstable feature flag to use to detect support for the feature, or what
migration steps are needed to switch to newer versions of the proposal.*

## Dependencies

This MSC builds on MSCxxxx, MSCyyyy and MSCzzzz (which at the time of writing have not yet been accepted
into the spec).
