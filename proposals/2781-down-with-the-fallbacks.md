# MSC2781: Remove reply fallbacks from the specification

Currently the specification suggests clients should send and strip a
[fallback representation](https://spec.matrix.org/v1.10/client-server-api/#fallbacks-for-rich-replies)
of a replied to message. The fallback representation was meant to simplify
supporting replies in a new client, but in practice they add complexity, are
often implemented incorrectly and block new features.

This MSC proposes to **remove** those fallbacks from the specification.

Some of the known issues include:
* The content of reply fallback is [untrusted](https://spec.matrix.org/v1.10/client-server-api/#stripping-the-fallback).
* Reply fallbacks may leak history. ([#368](https://github.com/matrix-org/matrix-spec/issues/368))
* Parsing reply fallbacks can be tricky. ([#350](https://github.com/matrix-org/matrix-spec/issues/350))
* It is unclear how to handle a reply to a reply. ([#372](https://github.com/matrix-org/matrix-spec/issues/372))
* Localization of replies is not possible when the content is embedded into the event.
* It is not possible to fully redact an event once it is replied to. This causes issues with Trust & Safety where
  spam or other removed content remains visible, and may cause issues with the GDPR Right to be Forgotten.
* There are a variety of implementation bugs related to reply fallback handling.

More details and considerations are provided in the appendices, but these are
provided for convenience and aren't necessary to understand this proposal.

## Proposal

Remove the [rich reply fallback from the
specification](https://spec.matrix.org/v1.10/client-server-api/#fallbacks-for-rich-replies).
Clients should stop sending them and should consider treating `<mx-reply>` parts
as they treat other invalid html tags.

Clients are not required to include a fallback in a reply since version 1.3 of
the
[specification](https://spec.matrix.org/v1.10/client-server-api/#rich-replies).
For this reason the reply fallback can be removed from the specification without
any additional deprecation period.

A suggestion for the spec PR: An info box could be included to mention
the historical use of the reply fallback, suggesting that clients may encounter
such events sent by other clients and that clients may need to strip out such
fallbacks.

Given clients have had enough time to implement replies completely, the
overall look & feel of replies should be unchanged or even improved by this
proposal. Implementing replies in a client should also be a bit easier with this
change.

An extended motivation is provided at [the end of this document](#user-content-appendix-b-issues-with-the-current-fallbacks).

## Potential issues

Old events and events sent by clients implementing an older version of the
Matrix specification might still contain a reply fallback. So for at least some
period of time clients will still need to strip reply fallbacks from messages.

Clients which don't implement rich replies may see messages without context,
confusing users. However, most replies are in close proximity to the original
message, making context likely to be nearby. Clients should also have enough
information in the event to render helpful indications to users while they work
on full support.

Clients which aren't using
[intentional mentions](https://spec.matrix.org/v1.7/client-server-api/#mentioning-the-replied-to-user)
may cause some missed notifications on the receiving side.
[MSC3664](https://github.com/matrix-org/matrix-doc/pull/3664) and similar aim to
address this issue, and
[MSC4142](https://github.com/matrix-org/matrix-spec-proposals/pull/4142) tries
to improve the intentional mentions experience for replies generally.
Because intentional mentions are already part of the Matrix specification since
version 1.7, clients can be expected to implement those first, which should make
the impact on notifications minimal in practice.

## Alternatives

[MSC2589](https://github.com/matrix-org/matrix-doc/pull/2589): This adds the
reply text as an additional key. While this solves the parsing issues, it
doesn't address the other issues with fallbacks.

One could also just stick with the current fallbacks and make all clients pay
the cost for a small number of clients actually benefitting from them.

Lastly one could introduce an alternative relation type for replies without
fallback and deprecate the current relation type (since it does not fit the
[new format for relations](https://github.com/matrix-org/matrix-doc/pull/2674)
anyway). We could specify, that the server is supposed to send the replied_to
event in unsigned to the client, so that clients just need to stitch those two
events together, but don't need to fetch the replied_to event from the server.
It would make replies slightly harder to implement for clients, but it would be
simpler than what this MSC proposes.

## Security considerations

Overall this should **reduce** security issues as the handling of untrusted
HTML is simplified. For an example security issue that could be avoided, see
https://github.com/vector-im/element-web/releases/tag/v1.7.3 and the appendix.

## Unstable prefix

No unstable prefix should be necessary as clients aren't required to send reply
fallbacks for all messages since version 1.3 of the Matrix specification, which
changed the wording from "MUST" to "SHOULD".

## Appendix A: Support for rich replies in different clients

### Clients without rendering support for rich replies

Of the 23 clients listed in the [Matrix client matrix](https://matrix.org/clients-matrix)
16 are listed as not supporting replies (updated January 2022):

- Element Android: Relies on the reply fallback.
- Element iOS: [Does not support rich replies](https://github.com/vector-im/element-ios/issues/3517)
- weechat-matrix: Actually has an [implementation](https://github.com/poljar/weechat-matrix/issues/86) to send replies although it seems to be [broken](https://github.com/poljar/weechat-matrix/issues/233). Doesn't render rich replies. Hard to implement because of the single socket implementation, but may be easier in the Rust version.
- Quaternion: [Blocked because of fallbacks](https://github.com/quotient-im/libQuotient/issues/245).
- matrixcli: [Doesn't support formatted messages](https://github.com/ahmedsaadxyzz/matrixcli/issues/10).
- Ditto Chat: [Seems to rely on the fallback](https://gitlab.com/ditto-chat/ditto/-/blob/main/mobile/scenes/chat/components/Html.tsx#L38)
- Mirage: Supports rich replies, but [doesn't strip the fallback correctly](https://github.com/mirukana/mirage/issues/89) and uses the fallback to render them.
- Nio: [Unsupported](https://github.com/niochat/nio/issues/85).
- Pattle: Client is not being developed anymore.
- Seaglass: Doesn't support rich replies, but is [unhappy with how the fallback looks](https://github.com/neilalexander/seaglass/issues/51)?
- Miitrix: Somewhat unlikely to support it, I guess?
- matrix-commander: No idea, but doesn't look like it.
- gotktrix: [Seems to rely on the reply fallback](https://github.com/diamondburned/gotktrix/blob/5f2783d633560421746a82aab71d4f7421e4b99c/internal/app/messageview/message/mcontent/text/html.go#L437)
- Hydrogen: [Seems to use the reply fallback](https://github.com/vector-im/hydrogen-web/blob/c3177b06bf9f760aac2bfd5039342422b7ec8bb4/doc/impl-thoughts/PENDING_REPLIES.md)
- kazv: Doesn't seem to support replies at all
- Syphon: [Uses the reply fallback in body](https://github.com/syphon-org/syphon/blob/fa44c5abe37bdd256a9cb61cbc8552e0e539cdce/lib/views/widgets/messages/message.dart#L368)

So in summary, 3/4 of the listed clients don't support replies. At least one
client doesn't support it because of the fallback (Quaternion). 3 of the command
line clients probably won't support replies, since they don't support formatted
messages and replies require html support for at least sending.

Only one client implemented rich replies in the last 1.5 years after the
original list was done in October 2020. Other clients are either new in my list
or didn't change their reply rendering. I would appreciate to hear, why those
client developers decided not to support rich reply rendering and if dropping
the reply fallback would be an issue for them.

Changes from 1.5 years ago as of January 2022:

- Fractal: [Seems to support replies now!](https://gitlab.gnome.org/GNOME/fractal/-/merge_requests/941)
- Commune: Seems to support rich reply rendering and style them very nicely.
- NeoChat: [Supports rich replies](https://invent.kde.org/network/neochat/-/blob/master/src/utils.h#L21)
- Cinny: [Seems to support rich replies](https://github.com/ajbura/cinny/blob/6ff339b552e242f6233abd86768bb2373b150f77/src/app/molecules/message/Message.jsx#L111)
- gomuks: [Strips the reply fallback](https://github.com/tulir/gomuks/blob/3510d223b2d765572bf2e97222f2f55d099119f0/ui/messages/html/parser.go#L361)
- Lots of other new clients!


### Results of testing replies without fallback

So far I haven't found a client that completely breaks without the fallback.
All clients that support rendering rich replies don't break, when there is no
fallback according to my tests (at least Nheko, Element/Web, FluffyChat and
NeoChat were tested and some events without fallback are in #nheko:nheko.im and
I haven't heard of any breakage). Those clients just show the reply as normal
and otherwise seem to work completely fine as well. Element Android and Element
iOS just don't show what message was replied to. Other clients haven't been
tested by the author, but since the `content` of an event is untrusted, a client
should not break if there is no reply fallback. Otherwise this would be a
trivial abuse vector.


## Appendix B: Issues with the current fallbacks

This section was moved to the back of this MSC, because it is fairly long and
exhaustive. It lists all the issues the proposal author personally experienced
with fallbacks in their client and its interactions with the ecosystem.

### Stripping the fallback

To reply to a reply, a client needs to strip the existing fallback of the first
reply. Otherwise replies will just infinitely nest replies.
[While the spec doesn't necessarily require stripping the fallback in replies to replies (only for rendering)](https://spec.matrix.org/v1.1/client-server-api/#fallback-for-mtext-mnotice-and-unrecognised-message-types),
not doing so risks running into the event size limit, but more importantly, it
just leads to a bad experience for clients actually relying on the fallback.

Stripping the fallback is not trivial. Multiple implementations had bugs in
their fallback stripping logic. The edge cases are not covered in the
specification in detail and some clients have interpreted them differently.
Common mistakes include:

- Not stripping the fallback in body, which leads to a very long nested chain.
- Not dealing with mismatched `<mx-reply>` tags, which can look like you were
    impersonating someone.

For the `body` extra attention needs to be paid to only strip lines starting
with `>` until the first empty line. Implementations either only stripped the
first line, stripped all lines starting with `>` until the first non empty line,
that does not start with `>` or stripped only the `formatted_body`. While those
are implementation bugs, they can't happen if you don't need to strip a
fallback.

### Creating a new fallback

To create a new fallback, a client needs to add untrusted html to its own
events. This is an easy attack vector to inject your own content into someone
elses reply. While this can be prevented with enough care, since Riot basically
had to fix this issue twice, it can be expected that other clients can also be
affected by this.

### Requirement of html for replies

The spec requires rich replies to have a fallback using html:

> Rich replies MUST have a format of org.matrix.custom.html and therefore a formatted_body alongside the body and appropriate msgtype.

This means you can't reply using only a `body` and you can't reply with an
image, since those don't have a `formatted_body` property currently. This means
a text only client, that doesn't want to display html, still needs to support
html anyway and that new features are blocked, because of fallbacks.

### Format is unreliable

While the spec says how a fallback "should" look, there are variations in use
which further complicates stripping the fallback or are common mistakes, when
emitting the fallback. Some variations include localizing the fallback,
missing suggested links or tags, using the body in replies to files or images
or using the display name instead of the matrix id.

As a result the experience in clients relying on the fallback or stripping the
fallback varies depending on the sending client.

### Replies leak history

A reply includes the `body` of another event. This means a reply to an event can
leak data to users, that joined this room at a later point, but shouldn't be
able to see the event because of visibility rules or encryption. While this
isn't a big issue, there is still an issue about it: https://github.com/matrix-org/matrix-doc/issues/1654

This history leak can also cause abusive or redacted messages to remain visible
to other room members, depending on the client implementation of replies.

Historically clients have also sometimes localized the fallbacks. In those cases
they leak the users language selection for their client, which may be personal
information.

### Using the unmodified fallback in clients and bridges

The above issues are minor, if reply fallbacks added sufficient value to
clients.  Bridges usually try to bridge to native replies, so they need to
strip the reply fallback
(https://github.com/matrix-org/matrix-doc/issues/1541). Even the IRC bridge
seems to send a custom fallback, because the default fallback is not that
welcome to the IRC crowd, although the use cases for simple, text only bridges
is often touted as a good usecase for the fallback (sometimes even explicitly
mentioning bridging to IRC). As a result there are very few bridges, that
benefit from the fallback being present.

Some clients do choose not to implement rich reply rendering, but the experience
tends to not be ideal, especially in cases where you reply to an image and now
the user needs to guess, what image was being replied to.

As a result the fallbacks provide value to only a subset of the Matrix
ecosystem.

### Fallbacks increase integration work with new features

- [Edits explicitly mention](https://github.com/matrix-org/matrix-doc/pull/2676)
    that a reply fallback should not be sent in the `m.new_content`. This causes
    issues for clients relying on the fallback, because they won't show replies
    once a message has been edited (see Element Android as a current example)
    and similar edge cases.
- [Extensible events](https://github.com/matrix-org/matrix-doc/pull/1767)
    require an update to the specification for fallbacks (because there is no
    `body` or `formatted_body` anymore after the transition period).
    [The current proposal](https://github.com/matrix-org/matrix-doc/pull/3644)
    also intends to just drop the fallbacks in extensible events.

### Localization

Since the fallback is added as normal text into the message, it needs to be
localized for the receiving party to understand it. This however proves to be a
challenge, since users may switch languages freely in a room and it is not easy
to guess, which language was used in a short message. One could also use the
client's language, but that leaks the user's localization settings, which can be a
privacy concern and the other party may not speak that language. Alternatively a
client can just send english fallbacks, but that significantly worsens the
experience for casual users in non-english speaking countries. The specification
currently requires them to not be translated (although some clients don't follow
that), but not sending a fallback at all completely sidesteps the need for the
spec to specify that and clients relying on an english only fallback.
