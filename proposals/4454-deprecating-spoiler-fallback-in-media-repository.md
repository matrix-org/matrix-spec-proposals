# MSC4454: Deprecating Spoiler Fallback In Media Repository

This MSC removes specification text that describes unused client behavior for
spoiler fallbacks, since it is ambiguous and could be interpreted as encouraging
plaintext storage of spoilered content in end-to-end encrypted contexts.

This proposal prioritizes preventing unintended disclosure of spoilered content
over preserving plaintext fidelity.

## Proposal

The
[spec now (10.2.2.6 in v1.18)](https://spec.matrix.org/v1.18/client-server-api/#spoiler-messages)
reads that a client should provide a plaintext (`body`) of
`Alice [Spoiler](mxc://example.org/abc123) in the movie.` when a message is
spoilered.

This behavior is not implemented by known clients and represents unnecessary
specification complexity. It is not appropriate to keep this text in the spec,
because a client implementing it could leak message text when sending spoilered
content in an end-to-end encrypted (E2EE) room. The current spec does not
specify how spoilers should be handled in E2EE rooms and could be read as
suggesting uploading spoilered text unencrypted to the media repository.

This proposal removes those recommendations on how clients should set the `body`
for spoilered messages.

## Potential issues

Inconsistent behavior between clients.

## Alternatives

### Including the spoilered content in the body (without marker)

When the spoiler in the plaintext is a short sentence such as
`Alice lived happily ever after in the movie.`.

This reflects current client behavior.

A spoilered message sent in Element Web:

```json
{
    "msgtype": "m.text",
    "format": "org.matrix.custom.html",
    "body": "test meow",
    "formatted_body": "<span data-mx-spoiler>test meow</span>",
    "m.mentions": {}
 }
```

### Marking spoilers in plaintext with ||

An alternative is inserting `||` around the spoiler (this is how Cinny does it).

Example (as sent in Cinny):

```json
{
    "body": "||test meow||",
    "format": "org.matrix.custom.html",
    "formatted_body": "<span data-md=\"||\" data-mx-spoiler>test meow</span>",
    "m.mentions": {},
    "msgtype": "m.text"
}
```

## Security considerations

This change reduces the risk of accidental plaintext leakage via media
repositories.

## Unstable prefix

Not applicable

## Dependencies

None
