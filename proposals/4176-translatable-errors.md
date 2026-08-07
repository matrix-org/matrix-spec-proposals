# MSC4176: Translatable Errors

[Errors in Matrix](https://spec.matrix.org/v1.11/client-server-api/#standard-error-response) contain
a "human-readable" message which is often shown to users verbatim. Typically, these errors are written
in English and hardcoded by the server authors, which can be a challenge for users who don't understand
English or for servers with primarily non-English users.

This proposal clarifies the requirements around `error` alongside a structure for serving different
language variations of the message for a client to choose from.

## Proposal

`error` is currently described as:

> The `error` string will be a human-readable error message, usually a sentence explaining what went wrong.

This definition is expanded to say it is a *UTF-8-encoded Unicode string* and that only printable
characters should be used. Clients *should* be aware of Right-to-Left (RTL) and other similar markers
being used, which may affect their rendering of the error.

The [standard error response](https://spec.matrix.org/v1.11/client-server-api/#standard-error-response)
is additionally expanded to contain an *optional* mapping object of language code to error message.
This map *should* be used by clients to pick the most applicable representation of the error for the
user, falling back to `error` when not available. It is left as an implementation detail for how to
pick the "most applicable" representation. This map is found under `messages`, a new property:

```jsonc
{
  "errcode": "M_WHATEVER",
  "error": "You can't send that message.",
  "messages": {
    "en-US": "You can't send that message.",
    "fr": "Tu ne peux pas envoyer ce message."
  }
}
```

The language of `error` is left undefined, though is anticipated to remain as typically English.

The language codes under `messages` use the same specification as the `policies` map's language codes
on [`m.login.terms`](https://spec.matrix.org/v1.11/client-server-api/#definition-mloginterms-params).
That is, language codes *should* be formatted as per [Section 2.2 of RFC 5646](https://datatracker.ietf.org/doc/html/rfc5646#section-2.2),
though *may* contain an underscore instead of a dash (`en_US` instead of `en-US`).

A client rendering the error to the user might use the following implementation-specific logic:

1. Check if `messages[user.lang]` is a string. If true, render that. If false, continue.
2. Check if `messages[config.default_lang]` is a string. If true, render. If false, continue.
3. Render `error`.

## Potential issues

Servers might end up incorporating relatively complex translation frameworks, or require extensive
changes to support multiple written languages.

This could potentially be an undesirable feature. Users could instead prefer to have `error` simply
use their language.

## Alternatives

Request headers may give hints as to what language the user/client prefers, and could be used to
populate `error` accordingly. This may lead to errors still being French when the user has deliberately
selected US English for a demo, unless they also change their browser/system settings, for example.

We may wish to consider making the mapping under `messages` be language code to object to support
future non-text error messages. We may in the future have a need/want for Markdown or HTML error
messages to provide rich context to the user.

## Security considerations

The error messages could be different depending on the language chosen. Specific groups may also be
targeted with their language of choice. For example, the error being a permissions issue but `en_US`
users seeing "Vote for X!" instead. This is primarily a risk when the server project accepts contributions
from unverified sources on translations. Projects should exercise care when accepting contributions.

## Unstable prefix

While this proposal is not considered stable, `messages` should be accessed as `org.matrix.msc4176.messages`
instead.

## Dependencies

This proposal has no direct dependencies, though may be depended on.
