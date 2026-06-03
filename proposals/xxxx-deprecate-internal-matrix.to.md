# MSC0000: Deprecate internal use of matrix.to navigation

The spec defines [matrix.to navigation](https://spec.matrix.org/v1.18/appendices/#matrixto-navigation) NOT as a service
on the web, but instead as a namespace URI piggybacking on the `https:` scheme before the `matrix:` scheme
was registered.
The intention is to have a clearly defined format to link to Matrix room aliases, room IDs, messages within rooms, and
user IDs. Clients are supposed to parse and handle this format internally to navigate between the aforementioned Matrix
entities similarly to links between pages on the web.

The <https://matrix.to> web service provided by the Foundation is available at and can resolve URLs in the matrix.to
shape as a kind of fallback functionality on the web. This is a very convenient workaround for any client not wanting to
spend the effort to special case internal navigation, and even when not showing a plain text matrix.to URL as a
clickable link many users understand the idea that they can copy this URL to their web browser to continue on.
Unfortunately this fallback remains a centralised crutch in an otherwise decentralised ecosystem when not resolved
inside of a client.

Matrix has introduced and registered the `matrix:` URI scheme as a parallel system with the major advantages of being
independent of the `https:` scheme, hence allowing deeper integration in URI handlers, while still remaining generalised
to fit the principle of free client choice in Matrix. It also simplifies parsing in clients significantly since special
casing `https://matrix.to` for internal routing is not a standard use case and often requires painful manual parsing.

## Proposal

Sending matrix.to URLs over Matrix is deprecated.

Clients SHALL instead generate `matrix:` URIs when it is clear that:

- a reference to a Matrix entity (room alias, room ID, event within a room, user ID) is going to be sent over Matrix,
  i.e. via message event, and
- unless breaking user intent, i.e. manually pasted links would not convert while tab-completed IDs would.

Features such as "share room by link" or a generic "right click to copy link" remain unchanged, since falling back to
the <https://matrix.to> web service remains reasonable outside of Matrix until browsers and/or operating systems widely
implement a default handler for `matrix:` to an appropriate onboarding experience.

This proposal is submitted in the hope that it supports the blanket adoption of `matrix:` URIs to work towards the
greater goal of maximising decentralisation per the [Matrix Manifesto](https://matrix.org/foundation/about/).

## Potential issues

There might be "growing pains" as implementing this MSC effectively forces the ecosystem to at least support parsing
`matrix:` URIs. In reality, most clients already support this as of today.

## Alternatives

1. Use [plain IDs](https://spec.matrix.org/v1.18/appendices/#common-identifier-format) instead of `matrix:` URIs with the
RECOMMENDATION to display them as navigable UX (e.g. links, "pills").
2. The outcome of this MSC could be the decision to stay with the preference for matrix.to for the fallback-to-the-web
benefit even for what is supposed to be Matrix-internal communication, and live with the consequence of not reaching the
same level of deeplinking other platforms have.
3. A more radical approach to deprecate matrix.to not only internally, but also generally, would be possible. The author
believes the consequences of this would be too harsh, particularly towards onboarding, even though issues with the
current onboarding experience via <https://matrix.to> persist.

## Security considerations

None known.

## Unstable prefix

Not needed.

## Dependencies

None.
