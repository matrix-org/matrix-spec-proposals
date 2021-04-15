# MSC3124: Representing spoilers in plain-text message fallback

Spoiler messages are described in
[MSC2010](https://github.com/matrix-org/matrix-doc/pull/2010) and
[MSC2557](https://github.com/matrix-org/matrix-doc/pull/2557), but
these proposals provide unclear and partially unusable guidance on how
clients should represent spoilers in the plain-text fallback version
of a message.  As a result, most clients simply include the spoilered
content verbatim in the fallback, limiting the usefulness of spoilers
across different clients as a feature to protect users' mental health
and emotional well-being.  The goal of this proposal is to reduce
ambiguity and provide better guidance for client developers, while
ensuring that spoilers are an effective and usable feature for all
Matrix users.

## Proposal

[MSC2010](https://github.com/matrix-org/matrix-doc/pull/2010)
encourages preserving the semantics of spoilers in plain-text fallback
by representing spoilered content in a way that isn't directly
readable.  However, the proposed obfuscation method (uploading the
content as a text file, and inserting the MXC URI) is incompatible
with encrypted rooms; the file would need to be encrypted, and then
the encryption key material would need to be included alongside the
MXC URI, but there's no specification for how to include that data
inline within a message.  In addition,
[MSC2010](https://github.com/matrix-org/matrix-doc/pull/2010) and
[MSC2557](https://github.com/matrix-org/matrix-doc/pull/2557) don't
definitively require any form of obfuscation, despite acknowledging
failure to obfuscate spoilers in fallback as a potential issue.

Spoilers are a vital accessibility feature for users with mental
health issues.  The ability for communities to set guidelines on what
kinds of content should be spoiled, and for community members to
participate in discussions with confidence that they won't see that
content without their active consent, is important for communities to
be able to protect users' well-being.  If spoilers are included
verbatim in plain-text fallbacks, then such communities will need to
maintain and circulate lists of "safe" Matrix clients which never
display plain-text fallback content when spoilers are present, and
recommend their members only use clients from those lists.  This
creates an awkward user experience and requires time-consuming
research and testing by community members.  Every spec-compliant
Matrix client, including text-based clients, should be able to safely
preserve the semantic meaning of a spoiler and prevent spoilered
content from being viewed without users' active consent.

For these reasons, this proposal makes it a mandatory requirement that
when a message contains a spoiler, the fallback produced by the client
must not contain spoilered content in any directly readable form. The
following suggestion is offered as one possible method of obfuscating
spoilers, superseding the suggestion given in
[MSC2010](https://github.com/matrix-org/matrix-doc/pull/2010): the
content of the spoiler may be converted into a `data:` URL as defined
by [RFC 2397](https://tools.ietf.org/html/rfc2397) with media type
`text/plain` and base64 encoding, as follows:

```
{
    "msgtype": "m.text",
    "format": "org.matrix.custom.html",
    "body": "Hello there, the movie was [spoiler](data:text/plain;base64,YXdlc29tZQ==)",
    "formatted_body": "Hello there, the movie was <span data-mx-spoiler>awesome</span>"
}
```

This preserves the spoilered content in a standardized decodable form,
while making it not immediately readable.  Clients are not required to
use this specific obfuscation method, but must obfuscate spoilered
content in some way. Furthermore, the obfuscation method must not make
assumptions about the character set used by the spoilered content; for
example, ROT13 is not an acceptable obfuscation method, as it fails to
obfuscate content in languages that don't use the Latin alphabet.

## Potential issues

When including spoilered content as a URI of any kind, there's a risk
that some clients may attempt to proactively display a preview of the
URI's content.  Hopefully, only HTML-aware clients will attempt to
retrieve and parse URIs included in messages, and such clients should
be able to parse and display the formatted message body anyway.

When the spoilered content is not directly included in the plain text,
there is some risk that users of text-based clients may be unable to
read the content even if they want to.  Using `data:` URLs, a
standardized format that is easily detected and parsed and is
recognized by web browsers, reduces the risk of this occurring (most
browsers block top-level navigation to `data:` URLs, but exceptions
are often made for `text/plain` data and for URLs explicitly input by
users).  Even in the worst case, users being unable to read spoilered
content is a better failure mode than users being exposed to
triggering content they didn't wish to see.  The plain-text fallback
arises from a recognition that not all content can be fully
represented in all clients.  Clients that rely on plain-text fallback
are unable to show images; the best available option is to show
summary descriptions instead, which may or may not be able to properly
capture the content of the image.  Spoilers are another feature that
cannot always be represented in plain text in a way that preserves
their semantics and their value to users; the best available option is
to show an obfuscated form, while making a best effort to keep this
form decodable or retrievable.

## Alternatives

Instead of requiring all clients to obfuscate spoilers in message
fallback when sending messages, clients could be encouraged to safely
handle spoilers in received messages. Such clients would need to
always hide or obfuscate the fallback of received messages until users
explicitly request otherwise, *everywhere* it might appear in the UI,
when the formatted body contains a spoiler.  This would require even
text-only clients to do at least some rudimentary parsing of
`org.matrix.custom.html` content to detect spoilers. Upon detecting a
spoiler in the HTML, those clients would then need to choose whether
to:
- hide the entirety of the message (possibly including descriptions of
  the spoiled content, which are important to help users choose whether
  to reveal the spoiler)
- figure out which part of the fallback corresponds to the spoiler in
  the formatted body (potentially quite difficult, as there is no
  specific mandated relationship between the fallback and the
  formatted body)
- discard the fallback, and fully parse and display the HTML body in a
  text-based representation where the spoiler can be hidden or
  revealed

This severely reduces the value of having a plain-text
fallback to begin with, and unnecessarily adds cumbersome extra
dependencies and implementation burden to client developers.  Clients
sending messages already know exactly what's being spoiled, and are
best-positioned to do the work of hiding spoilers, as opposed to
pushing that work onto clients receiving messages.

Furthermore with this approach, end-users would need to be clearly
informed which clients are "spoiler-safe" as described above, and
which aren't, so they can choose a client that is safe and usable for
them. Presenting this information to users in a coherent and uniform
way is difficult.  Should it be present in clients' websites and app
store listings?  Should matrix.org maintain this information and
include it in their list of clients?  This approach is cumbersome and
would likely add an additional layer of confusion for newcomers to
Matrix, hindering adoption.
