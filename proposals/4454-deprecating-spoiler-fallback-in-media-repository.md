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

This proposal removes the recommended fallback for spoilers in `body`. The
plaintext representation of spoilers is left as an implementation detail.

Spoiler-aware clients SHOULD NOT display body anywhere when there are spoilers
in `formatted_body`. For contexts like room list previews and notifications
where a plain text representation is needed, clients SHOULD either generate
plain text from the HTML locally, or simply display a placeholder message when
any spoilers are detected.

This proposal does not affect `formatted_body`.

## Potential issues

Inconsistent behavior between clients.

Anyhow this is already basically the reality nowadays, so nothing lost, nothing
won.

## Alternatives

This proposal removes the previous guidance that suggested a specific way to
populate the `body` for spoilered messages. It does not introduce a new required
behavior; implementations may continue using any approach that fits their design
model. In other words, removing the recommendation makes multiple client
behaviours spec-compliant rather than prescribing one.

Below are two common approaches implemented by clients today. They are shown as
examples and are not being mandated by this proposal.

### Alternative 1: Include the spoilered content verbatim in `body`

Some clients (for example Element Web) put the plaintext of the spoiler into the
`body` field and use `formatted_body` to mark the spoiler in HTML
(`data-mx-spoiler`).

Example (Element Web style):

```json
{
    "msgtype": "m.text",
    "format": "org.matrix.custom.html",
    "body": "test meow",
    "formatted_body": "<span data-mx-spoiler>test meow</span>",
    "m.mentions": {}
}
```

### Alternative 2: Mark spoilers in plaintext with delimiters (e.g. `||`)

Insert a plaintext delimiter around spoiler text (Cinny uses `||`, so just
discord-style) and also provide a `formatted_body` with a spoiler markup for
HTML renderers.

Example (Cinny style):

```json
{
    "msgtype": "m.text",
    "format": "org.matrix.custom.html",
    "body": "||test meow||",
    "formatted_body": "<span data-md=\"||\" data-mx-spoiler>test meow</span>",
    "m.mentions": {}
}
```

### Summary

This proposal intentionally removes prescriptive guidance so that clients are
free to choose an approach that balances compatibility and privacy. All of the
approaches illustrated above are spec-compliant under this change.

## Security considerations

This change reduces the risk of accidental plaintext leakage via media
repositories.

## Unstable prefix

Not applicable

## Dependencies

None
