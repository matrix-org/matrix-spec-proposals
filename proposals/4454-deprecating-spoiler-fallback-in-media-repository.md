# MSC4454: Deprecating Spoiler Fallback In Media Repository

This MSC proposes removing specification language describing unused client behaviour for spoiler
fallbacks, which is ambiguous and could be interpreted as encouraging plaintext storage of
spoilered content in End-to-end encryption contexts.

This proposal prioritizes preventing unintended disclosure of spoilered content over preserving plaintext fidelity.

## Proposal

The [spec now (10.2.2.6 in v1.18)](https://spec.matrix.org/v1.18/client-server-api/#spoiler-messages) reads that a client should provide a plaintext (`body`) of
`Alice [Spoiler](mxc://example.org/abc123) in the movie.` when a message is spoilered.

This behavior is not implemented by known clients and represents unnecessary specification complexity.
It isn't a good idea to have this in the Spec, especially considering that if a client were to
implement that it would lead to leaking message text, when spoilering a message in a E2EE message.
The current spec text doesn't specify how to handle spoilers in E2EE rooms, and could be read as
suggesting uploading the spoilered text unencrypted to the media repository.

So the proposal is removing that possibility in favor of just putting a
`Alice [Spoiler](lived happily ever after) in the movie.` in the `body`.

So instead of

```json
{
  "msgtype": "m.text",
  "format": "org.matrix.custom.html",
  "body": "Alice [Spoiler](mxc://example.org/abc123) in the movie.",
  "formatted_body": "Alice <span data-mx-spoiler>lived happily ever after</span> in the movie."
}
```

we would send

```json
{
  "msgtype": "m.text",
  "format": "org.matrix.custom.html",
  "body": "Alice [Spoiler](lived happily ever after) in the movie.",
  "formatted_body": "Alice <span data-mx-spoiler>lived happily ever after</span> in the movie."
}
```

If a reason is supplied we would send

```json
{
  "msgtype": "m.text",
  "format": "org.matrix.custom.html",
  "body": "Alice [Spoiler for health of Alice](lived happily ever after) in the movie.",
  "formatted_body": "Alice <span data-mx-spoiler='health of alice'>lived happily ever after</span> in the movie."
}
```

instead of:

```json
{
  "msgtype": "m.text",
  "format": "org.matrix.custom.html",
  "body": "Alice [Spoiler for health of Alice](mxc://example.org/abc123) in the movie.",
  "formatted_body": "Alice <span data-mx-spoiler='health of alice'>lived happily ever after</span> in the movie."
}
```


Clients generating messages with spoilers:

- MAY NOT include spoilered content in the `body` field
- SHOULD wrap the spoilered text in `[Spoiler](spoilered text goes here)`
- if a reason is supplied the spoilered text SHOULD be wrapped like `[Spoiler for REASON](spoilered text goes here)`
- MAY encode the full spoilered content only in `formatted_body`

Clients rendering messages:

- SHOULD prefer `formatted_body` when available
- MAY fall back to `body` when rich formatting is unsupported

The `formatted_body` field is the authoritative source for spoiler semantics.

## Potential issues

Clients which don't consider this and just display the plain text message in some contexts including the spoilered message in the plain `body` could cause undesired behavior, but as they most likely also don't support spoilers at all or are plain text clients increasing the reliance on rich text wouldn't do any good.

Note this MSC has changed how spoilered text should be included in the plain text since the creation of the MSC

## Alternatives

### including the spoilered content in the body, without marker

When the spoiler in the plaintext would just be something like `Alice lived happily ever after in the movie.`
it could possibly *leak* the spoiler in notifications, message previews, or reply-rendering, which is generally not wanted.

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

### Marking spoilers in plaintext with `||`

An alternative would be inserting `||` around the spoiler (this is how cinny does it). 

This has significant drawbacks, as it would disregard the possibility of clients not implementing the spoiler, and then just showing
the spoilered text even when unwanted (aka in notifications, message previews and reply headings).

On the other hand, this would allow plain text clients, bots, and bridges (which only relay the `body` and don't consider `formatted_body`)
to still display the spoilered text which this proposal wouldn't.

Example (as sent in cinny):

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

This change reduces the risk of accidental plaintext leakage via media repositories.

## Unstable prefix

not applicable

## Dependencies

none
