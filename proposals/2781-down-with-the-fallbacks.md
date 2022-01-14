# MSC2781: Remove reply fallbacks from the specification

Currently replies require clients to send and parse a fallback representation of
the replied to message. Something similar is planned for edits. While at least
in theory fallbacks should make it simpler to start supporting replies in a new
client, they actually introduce a lot of complexity and implementation issues
and block a few valuable features. This MSC proposes to deprecate and eventually
remove those fallbacks. It is an alternative to
[MSC2589](https://github.com/matrix-org/matrix-doc/pull/2589), which intends to
double down on fallbacks.

## Proposal

Remove the rich reply fallback from the specification. Clients should stop
sending them and should consider treating `<mx-reply>` parts as either something
to be unconditionally stripped or as something to be escaped as invalid html.
Clients may send replies without a formatted_body now using arbitrary message
events (not state events).

As a result of this, you would be able to reply with an image.  New clients
would also be able to implement edits and replies more easily, as they can
sidestep a lot of pitfalls. This should improve the look and feel of replies in
Matrix across all clients in the long term.

An extended motivation is provided at [the end of this document](#user-content-appendix-b-issues-with-the-current-fallbacks).

There are similar benefits to not adding a fallback to edits. This proposal
focuses on replies for simplicity, but encourages
[MSC2676](https://github.com/matrix-org/matrix-doc/pull/2676) to drop the edit
fallback or remove it [when moving to extensible
events](https://github.com/matrix-org/matrix-doc/pull/3644).

## Potential issues

Obviously you can't remove the fallback from old events. As such clients would
still need to do something with them in the near future. I'd say just not
handling them in a special way should be okay after some unspecified period of
time.

Clients not implementing rich replies or edits may show some slightly more
confusing messages to users as well. I'd argue though that in most cases, the
reply is close enough to the replied to message, that you would be able to guess
the correct context. Replies would also be somewhat easier to implement and
worst case, a client could very easily implement a little "this is a reply"
marker to at least mark replies visually.

~~Same applies to edits. If 2 very similar messages appear after one another,
someone new to online messaging would assume, this is a correction to the
previous message. That may even be more obvious to them than if the message was
prefixed with a `*`, since that has been confusing to users in the past. Since
edits would now look exactly like a normal message, they would also be
considerably easier to implement, since you just need to replace the former
message now, similar to a redaction, and not merge `content` and `new_content`.~~

## Alternatives

[MSC2589](https://github.com/matrix-org/matrix-doc/pull/2589): This adds the
reply text as an addional key. While this solves the parsing issues, it
doesn't address the other issues with fallbacks.

One could also just stick with the current fallbacks and make all clients pay
the cost for a small number of clients actually benefitting from them.

Lastly one could introduce an alternative relation type for replies without
fallback and deprecate the current relation type (since it does not fit the new
format for relations anyway). We could specify, that the server is supposed to
send the replied_to event in unsigned to the client, so that clients just need
to stitch those two events together, but don't need to fetch the replied_to
event from the server. It would make replies slightly harder to implement for
clients, but it would be simpler than what this MSC proposes.

## Security considerations

Removing the fallback from the spec may lead to issues, when clients experience
the fallback in old events. This should not add any security issues the
client didn't already have from interpreting untrusted html, though. In all
other cases this should **reduce** security issues.

## Appendix A: Clients not supporting rich replies

Of the 23 clients listed in the [matrix client matrix](https://matrix.org/clients-matrix)
16 are listed as not supporting replies:

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

Only one client implemented rich replies in the last 1.5 years. Other clients
are either new in my list or didn't change their reply rendering. I would
appreciate to hear, why those client developers decided not to support rich
reply rendering and if dropping the reply fallback would be an issue for them.

Changes from 1.5 years ago:

- Fractal: [Seems to support replies now!](https://gitlab.gnome.org/GNOME/fractal/-/merge_requests/941)
- Commune: Seems to support rich reply rendering and style them very nicely.
- NeoChat: [Supports rich replies](https://invent.kde.org/network/neochat/-/blob/master/src/utils.h#L21)
- Cinny: [Seems to support rich replies](https://github.com/ajbura/cinny/blob/6ff339b552e242f6233abd86768bb2373b150f77/src/app/molecules/message/Message.jsx#L111)
- gomuks: [Strips the reply fallback](https://github.com/tulir/gomuks/blob/3510d223b2d765572bf2e97222f2f55d099119f0/ui/messages/html/parser.go#L361)
- Lots of other new clients!


## Appendix B: Issues with the current fallbacks

This section was moved to the back of this MSC, because it is fairly long and
exhaustive. It lists all the issues the proposal author personally experienced
with fallbacks in their client and its interactions with the ecosystem.

### Stripping the fallback

To reply to a reply, a client needs to strip the existing fallback of the first
reply. Otherwise replies will just infinitely nest replies. [While the spec doesn't necessarily require that](https://github.com/matrix-org/matrix-doc/issues/1541),
not doing so risks running into the event size limit, but more importantly, it
just leads to a bad experience for clients actually relying on the fallback.

Stripping the fallback is not trivial. Multiple implementations had bugs in
their fallback stripping logic. The edge cases are not covered in the
specification in detail and some clients have interpreted them differently.
Common mistakes include:

- Not stripping the fallback in body, which leads to a very long nested chain.
- Not dealing with mismatched `<mx-reply>` tags, which can look like you were
    impersonating someone.

Stripping the fallback from body is even more complicated, since there is no way
to distinguish a quote from a reply reliably.

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

This is also an issue with edits, where the combination of edit fallback and
reply fallback is somewhat interesting: You need to send a fallback, since the
event is still a reply, but you can't send a reply relation, since this is an
edit. Currently this is solved by not sending a reply fallback in edits, so
clients can't rely on a reply fallback in all cases.

We currently can see 2 behaviours in practice:

Client A supports rich reply rendering, Client B does not.

- A sends an edit. This according to MSC2676 does not include a reply fallback.
    A properly sees the edit still as a reply. B does not.
- B sends an edit but includes a reply fallback in the body. It can still see
    that the message is a reply. A needs to strip the invalid reply fallback, or
    it will see the reply content twice.

### Format is unreliable

Further complicating the stripping and creation portion of fallbacks is, that
they are somewhat badly specified. While the fallback and html use are required,
the spec only says how a fallback "should" look, not how it "must" look. In
practice there are various variations of the fallback floating around, where the
tame ones are just localized, but others are just straight up missing suggested
links or tags.

Basically a client can't rely on the fallback being present currently or it
following any kind of shape or form and stripping is done on a best effort
basis, especially for the fallback in `body`.

### Replies leak history

A reply includes the `body` of another event. This means a reply to an event can
leak data to users, that joined this room at a later point, but shouldn't be
able to see the event because of visibility rules or encryption. While this
isn't a big issue, there is still an issue about it: https://github.com/matrix-org/matrix-doc/issues/1654

Replies are also sometimes localized. In those cases they leak the users
language selection for their client, which may be personal information.

### Using the unmodified fallback in clients and bridges

The above issues are minor, if reply fallbacks would sufficiend value to
clients.  Bridges usually try to bridge to native replies, so they need to
strip the reply fallback
(https://github.com/matrix-org/matrix-doc/issues/1541). Even the IRC bridge
seems to send a custom fallback, because the default fallback is not that
welcome to the IRC crowd.

Some clients do choose not to implement rich reply rendering, but the experience
tends to not be ideal, especially in cases where you reply to an image and now
the user needs to guess, what image was being replied to.

As a result the fallbacks provide value to only a subset of the Matrix
ecosystem.

### Fallback increase integration work with new features

- [Edits explicitly mention](https://github.com/matrix-org/matrix-doc/pull/2676)
    that a reply fallback should not be sent in the `m.new_content`.
- [Extensible events](https://github.com/matrix-org/matrix-doc/pull/1767) would
    need to specify how the fallback should look like. [Alternatively they could
    also drop it](https://github.com/matrix-org/matrix-doc/pull/3644).

### Localization

Since the fallback is added as normal text into the message, it needs to be
localized for the receiving party to understand it. This however proves to be a
challenge, since users may switch languages freely in a room and it is not easy
to guess, which language was used in a short message. One could also use the
client's language, but that leaks the user's localization settings, which can be a
privacy concern and the other party may not speak that language. Alternatively a
client can just send english fallbacks, but that significantly worsens the
experience for casual users in non-english speaking countries.

## Unstable prefix

Clients should use the prefix `im.nheko.msc2781.` for all their event types, if
they implement this MSC in a publicly available release or events may otherwise
bleed into public rooms.
