# MSC2758: Common grammar for textual identifiers

The matrix specification uses textual identifiers for a wide range of
concepts. Examples include "event types" and "room versions".

In the past, these identifiers have often lacked a formal grammar, leaving
servers and clients to make assumptions about questions such as which
characters are permitted, minimum and maximum lengths, etc.

This proposal suggests a common grammar which can be used as a basis for
*future* identifier types, to reduce the work involved in future specification
work.

No attempt is made here to bring existing identifiers into line; however
examples of identifiers which might have benefitted from such a grammar in the
past include:

 * [`capabilities`](https://matrix.org/docs/spec/client_server/r0.6.0#get-matrix-client-r0-capabilities)
   identifiers.
 * authentication types for the [User-Interactive Authentication mechanism](https://matrix.org/docs/spec/client_server/r0.6.0#user-interactive-authentication-api).
 * login types for [`/_matrix/client/r0/login`](https://matrix.org/docs/spec/client_server/r0.6.0#post-matrix-client-r0-login).
 * event types
 * [`m.room.message` `msgtypes`](https://matrix.org/docs/spec/client_server/r0.6.0#m-room-message-msgtypes)
 * `app_id` for [`POST /_matrix/client/r0/pushers/set`](https://matrix.org/docs/spec/client_server/r0.6.0#post-matrix-client-r0-pushers-set).
 * `rule_ids`, `actions` and `tweaks` for [push rules](https://matrix.org/docs/spec/client_server/r0.6.0#push-rules).
 * [E2E messaging algorithm names](https://matrix.org/docs/spec/client_server/r0.6.0#messaging-algorithm-names).

## Proposal

We define a "common namespaced identifier grammar". This can then be referenced
by other parts of the grammar, in much the same way as [Unpadded
Base64](https://matrix.org/docs/spec/appendices#unpadded-base64) is defined
today.

The grammar is defined as follows:

 * An identifier may not be less than one character or more than 255 characters
   in length.
 * Identifiers must start with one of the characters `[a-z]`, and be entirely
   composed of the characters `[a-z]`, `[0-9]`, `-`, `_` and `.`.
 * Identifiers starting with the characters `m.` are reserved for use by the
   formal matrix specification.
 * Implementations wishing to implement unspecified identifiers should follow
   the Java Package Naming convention of starting with a reversed domain
   name (with a dot after the domain name part). For example, for the 
   organisation `example.com`, a valid identifier would be
   `com.example.identifier`.

This grammar is intended for use entirely by internal identifiers, and *not*
for user-visible strings.

### Rationale

 * Avoiding non-ascii characters sidesteps any issues with homoglyphs or
   alternative encodings of the same characters.
 * Avoiding upper-case character sidesteps any concerns over case-sensitivity.
