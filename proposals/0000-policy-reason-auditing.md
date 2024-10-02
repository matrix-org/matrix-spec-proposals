# MSC0000: Moderation policy auditing and context

Moderation policies provide a `reason` field.
While this is designed as a freetext field, there are a number
of reasons why it is not appropriate to do so.

* The `reason` is public, and moderators may not want to provide
  context about the ban in public. But still need to keep the context
  on record. They may also need to share context with other
  moderators, but not the wider community.

* Moderation bots such as Draupnir and Mjolnir use the `reason`
  field in `m.policy.rule.user` to determine whether the user's
  events and profile should be redacted. This stops the reason
  field being used to provide context.

## Proposal

Standard Matrix, encrypted messaging threads are used to provide
context about moderation policies.

A new policy event `m.policy.rule.context` is introduced.  This is
almost identical to `m.policy.rule.*` events, except it servers as an
anchor point to open threads.  The reason why the existing policy is
not used to act as an anchor point is so that context can be provided
in a seperate, private, and encrypted policy room. And also so that
when the original policy is rescinded or expires, the context is still
available.

```json
"type": "m.policy.rule.context",
"content": {
  "recommendation": "m.ban",
  "entity": "@yarrgh:example.com",
  "rule_type": "m.policy.rule.user",
},
```

### Flow from a moderation bot

In order to provide an exapmle of how this proposal will work,
we are going to discuss a possible UX flow for a moderation bot.

Alice is a room moderator, and Neighnir is a moderation bot.

Alice has recently banned `@yarrgh:example.com` and wants to provide
some context for the ban to the other moderators in her community.

Alice repeats the arguments to the ban command to Neighnir in
the context command.

`!neighnir context ban @yarrgh:example.com`.

Neighnir then creates a new `m.policy.rule.context` policy
in a preconfigured and private policy room. If a context
policy already exists for the `recommendation` and `entity`
combination, then this step is skipped.

Neighnir then creates a threaded message referring to the
policy context. This step is skipped if a thread is already open.

```json
{
  "m.relates_to": {
    "rel_type": "m.thread",
    "event_id": "$the_context_policy_event"
  },
  "msgtype": "m.notice",
  "body": "`@yarrgh:example.com` context starts here."
}
```

Neighnir then returns a link to the thread as a response
to Alice's command.

Alice can then send normal Matrix messages in the thread in
order to provide any context, including screenshots.

## Potential issues

### GDPR compliance

It's unclear to me how this context will interact with GDPR legislation
and I have recieved no legal advice.

The risk is that in some cases it may be possible for the considered
`entity` to demand the messages in the context thread?

Moderators will have to be warned of this possibility.

### Old irrelevant context

Some context may actually be old, irrelevant, or taken out of
context itself. Moderators may need to be actively encouraged to
redact old context.

## Alternatives

### Local storage

Context could be stored locally in moderation tools, but this
restricts collaboration between different tools and moderators.
It also prevents the context being viewed as a normal matrix thread.
The context would also not be natively encrypted.

## Security considerations

### Access to context

An attacker gaining access to private policy lists containing context
could be a serious data breach. However, as the threads in the policy
lists are encrypted, they would need to obtain the decryption keys.

## Unstable prefix

*If a proposal is implemented before it is included in the spec, then implementers must ensure that the
implementation is compatible with the final version that lands in the spec. This generally means that
experimental implementations should use `/unstable` endpoints, and use vendor prefixes where necessary.
For more information, see [MSC2324](https://github.com/matrix-org/matrix-doc/pull/2324). This section
should be used to document things such as what endpoints and names are being used while the feature is
in development, the name of the unstable feature flag to use to detect support for the feature, or what
migration steps are needed to switch to newer versions of the proposal.*
