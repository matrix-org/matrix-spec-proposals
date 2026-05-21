# MSC4481: Use Matrix URI-style type segments in matrix.to

The spec defines matrix.to navigation as a web-compatible way to link to Matrix room aliases, room ids, messages within
rooms, and user ids at <https://spec.matrix.org/v1.18/appendices/#matrixto-navigation>.

The spec prescribes proper URL encoding for them, which applies particularly to the special characters
("sigils") in the URL fragment.
At the same time, unencoded ones should also be supported for compatibility to the more "human readable form".

This has some issues as noted e.g. at <https://github.com/matrix-org/matrix.to/issues/251>.

## Proposal

The spec also defines the Matrix URI scheme <https://spec.matrix.org/v1.18/appendices/#matrix-uri-scheme>,
which uses a different format to differentiate between the different types of ID:

- `#` -> `r/`
- `!` -> `roomid/`
- `$` -> `e/`
- `@` -> `u/`

This MSC proposes to deprecate the current use of sigils in matrix.to's fragment.
Instead, the same `type` `segment-nz` is used.

For example:

- <https://matrix.to/#/r/matrix:matrix.org>
- <https://matrix.to/#/roomid/L58ME6ufiP49v97UIOBIpvWKEgj4912JmECPuDzlvCI?via=matrix.org&via=mozilla.org&via=unredacted.org>
- <https://matrix.to/#/roomid/L58ME6ufiP49v97UIOBIpvWKEgj4912JmECPuDzlvCI/e/99HwZ8FhMP_ATTGBKK80JM0wzYOfDYdSxCmLt-Fj0nk?via=matrix.org&via=mozilla.org&via=unredacted.org>
- <https://matrix.to/#/u/stammfisch:matrix.org>

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
