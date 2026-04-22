# MSC0000: Deprecating Spoiler Fallback In Media Repository

This MSC proposes removing specification language describing unused client behaviour for spoiler
fallbacks, which is ambiguous and could be interpreted as encouraging plaintext storage of
spoilered content in End-to-end encryption contexts.

This proposal prioritizes preventing unintended disclosure of spoilered content over preserving plaintext fidelity.

## Proposal

The spec now reads that a client should provide a plaintext (`body`) of
`Alice [Spoiler](mxc://example.org/abc123) in the movie.` when a message is spoilered.

This behavior is not implemented by known clients and represents unnecessary specification complexity.
It isn't a good idea to have this in the Spec, especially considering that if a client were to
implement that it would lead to leaking message text, when spoilering a message in a E2EE message.
The current spec text doesn't specify how to handle spoilers in E2EE rooms, and could be read as
suggesting uploading the spoilered text unencrypted to the media repository.

So the proposal is removing that possibility in favor of just putting a
`Alice [Spoiler] in the movie.` in the `body`.

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
  "body": "Alice [Spoiler] in the movie.",
  "formatted_body": "Alice <span data-mx-spoiler>lived happily ever after</span> in the movie."
}
```

Clients generating messages with spoilers:

- MUST NOT include spoilered content in the `body` field
- MUST replace spoilered sections with a neutral placeholder (e.g. `[Spoiler]`)
- MUST encode the full spoilered content only in `formatted_body`

Clients rendering messages:

- SHOULD prefer `formatted_body` when available
- MAY fall back to `body` when rich formatting is unsupported

The `formatted_body` field is the authoritative source for spoiler semantics.

## Potential issues

### Reduced fidelity in plaintext contexts

Under this proposal, the `body` field no longer contains the spoilered content. As a result, clients
which rely solely on `body` (including some plaintext-only clients, bots, and bridges) will not have access to the spoilered text.

This represents a loss of information compared to approaches where the full message is included in plaintext.
In these cases, the message may appear as `Alice [Spoiler] in the movie.` without any way to recover the hidden content.

This tradeoff is intentional: the proposal prioritizes preventing unintended disclosure of spoilered content
over preserving full fidelity in plaintext representations.

### Plaintext-only clients will not receive spoilered content

Because notifications and message previews are often derived from the `body` field, they will contain less information for spoilered
messages under this proposal.

For example, a notification may display `Alice [Spoiler] in the movie.` rather than including the spoilered text itself.

While this reduces the usefulness of previews, it avoids leaking spoilered content in contexts where it may be displayed without
explicit user interaction (such as push notifications or lockscreen previews).

### Increased reliance on formatted_body

This proposal makes `formatted_body` the authoritative source for spoiler semantics. Clients which do not support or process `formatted_body`
will not be able to render spoilered content.

In practice, this increases reliance on `formatted_body` for full message fidelity and may widen the behavioral gap between clients that
support rich formatting and those that do not.

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
