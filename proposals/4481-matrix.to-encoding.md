# MSC4481: Use Matrix URI-style type segments in matrix.to

The spec defines [matrix.to navigation](https://spec.matrix.org/v1.18/appendices/#matrixto-navigation) NOT as a service
on the web, but instead as a namespace URI piggybacking on the `https:` scheme before the `matrix:` scheme was
registered.
The intention is to have a clearly defined format to link to Matrix room aliases, room IDs, messages within rooms, and
user IDs. Clients are supposed to parse and handle this format internally to navigate between the aforementioned Matrix
entities similarly to links between pages on the web.

Since it is based on HTTP URLs, the spec explicitly defines matrix.to as based on RFC 3986, including URL encoding.
For the purpose of this MSC, note this applies particularly to the special characters ("sigils" of the [different types
of Matrix IDs](https://spec.matrix.org/latest/appendices/#common-identifier-format)) in the URL fragment.
At the same time, the spec recommends clients also support matrix.to URLs "which are not fully encoded" for
compatibility to the more "human readable form" that some clients produced historically and continue to do today.
This includes the <https://matrix.to> web service provided by the Foundation, which coincidentally sits at and can
resolve URLs in the matrix.to shape as a kind of fallback functionality on the web.

Besides being technically incorrect, the unencoded fragments are known to cause practical issues, which are documented
and discussed across numerous issues in the ecosystem:

- <https://github.com/matrix-org/matrix.to/issues/251>
- <https://github.com/element-hq/element-web/issues/32611>
- <https://github.com/NixOS/org/pull/52>

Issues commonly center around URI parsing libraries failing to interpret URLs as intended by the user sharing links
outside of Matrix due to incorrect encoding. This is particularly prevalent where the `#` character has another assigned
meaning, such as across most social media. For example, the Foundation's own YouTube video descriptions used to
unwittingly contain improperly encoded matrix.to links copied from common client implementations, which broke when
YouTube introduced hashtags to the platform, including a parser that prefers to detect the second `#` as start of a
hashtag rather than the technically incorrect contents of the URL fragment.

## Proposal

The spec also defines the Matrix URI scheme <https://spec.matrix.org/v1.18/appendices/#matrix-uri-scheme>,
which uses a different format to differentiate between the different types of ID:

- `#` -> `r/`
- `!` -> `roomid/`
- `$` -> `e/`
- `@` -> `u/`

This MSC proposes to deprecate the current use of sigils in matrix.to's fragment, entirely eliminating the question
around encoding. Instead, the same `type` `segment-nz` as defined for `matrix:` (see the list above) SHALL be used.

For example:

- <https://matrix.to/#/r/matrix:matrix.org>
- <https://matrix.to/#/roomid/L58ME6ufiP49v97UIOBIpvWKEgj4912JmECPuDzlvCI?via=matrix.org&via=mozilla.org&via=unredacted.org>
- <https://matrix.to/#/roomid/L58ME6ufiP49v97UIOBIpvWKEgj4912JmECPuDzlvCI/e/99HwZ8FhMP_ATTGBKK80JM0wzYOfDYdSxCmLt-Fj0nk?via=matrix.org&via=mozilla.org&via=unredacted.org>
- <https://matrix.to/#/u/stammfisch:matrix.org>

Additionally, clients are advised to continue to support parsing the now-deprecated format using URL percent encoding as
well as incompletely encoded fragments for backwards compatibility. Clients SHOULD further prefer the new format over
the now-deprecated format when generating such URLs fully automatically, and reasonably convert URLs in the
now-deprecated format to the new format under circumstances not undermining user intention, e.g. when auto-completing.
It would generally be reasonable for clients to handle matrix.to URLs they cannot interpret correctly as regular HTTP
URLs instead, so users automatically fall back to the <https://matrix.to> web service, regardless of its official
relationship regarding the spec.

## Potential issues

Needs to be implemented in <https://github.com/matrix-org/matrix.to/> first to ensure fallback support.

## Alternatives

Disallowing unencoded matrix.to URLs.

## Security considerations

None known.

## Unstable prefix

Not needed.

## Dependencies

Needs to be implemented in <https://github.com/matrix-org/matrix.to/> first.
