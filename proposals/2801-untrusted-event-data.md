# MSC2801: Make it explicit that event bodies are untrusted data

As the Matrix Specification stands today, it is easy for client developers to
assume that all events will be structured as documented. For example, the
`displayname` key of an [`m.room.member`
event](https://matrix.org/docs/spec/client_server/r0.6.1#m-room-member) is
specified to be "`string` or `null`"; and the `info` key of an [`m.image`
message event](https://matrix.org/docs/spec/client_server/r0.6.1#m-image) must
be a Javascript object.

In reality, these are not safe assumptions. This MSC proposes that the
specification be updated to make it clear that developers should treat all
event data as untrusted.

## Reasons why events may not match the specification

Firstly, let's examine the reasons why such malformed events can exist. Some of
these reasons may appear to have trivial solutions; these are discussed below.

 1. Most obviously, Synapse as it currently stands does very little validation
    of event bodies sent over the Client-Server API. There is nothing stopping
    any user sending a malformed `m.room.message` event with a simple `curl`
    command or Element-Web's `/devtools`.

    Any event sent in this way will be returned to the clients of all the other
    users in the room.

 2. Events may be encrypted. Any client implementing E2EE must be prepared to
    deal with any encrypted content, since by definition a server cannot
    validate it.

 3. In order to allow the Matrix protocol to be extensible, server
    implementations must tolerate unknown event types, and allow them to be
    passed between clients. It is obvious that a pair of custom clients
    implementing a `com.example.special.event` event type cannot rely on a
    standard server implementation to do any validation for them.

    However, this problem extends to event types and keys which have been added
    to the specification. For example, the [`m.room.encrypted` event
    type](https://matrix.org/docs/spec/client_server/r0.6.1#m-room-encrypted)
    was added in Client-Server API r0.4.0. It therefore follows that a server
    implementing CS-API r0.3.0 would have no way to validate an
    `m.room.encrypted` event, so if a client is connected to such a server, it
    could receive malformed events.

 4. To extend from point 3, the problem is not even resolved by upgrading the
    server. There may now be rooms which contain historical events which would
    no longer be accepted, but these will still be served by the server.

    This problem also applies to non-room data such as account data. For
    example, Client-Server API r0.6.0 added the [`m.identity_server` account
    data event
    type](https://matrix.org/docs/spec/client_server/r0.6.1#m-identity-server).
    It is possible, if unlikely, that a client could have uploaded an
    `m.identity_server` event before the administrator upgraded the server.

 5. Event redaction removes certain keys from an event. This is a bit of a
    trivial case, though it is worth noting that the rules for event redaction
    vary between room versions, so it's possible to see a variety of "partial"
    events.

 6. All the cases above can occur without federation. Federation adds
    additional complexities due to the structure of Matrix rooms. In
    particular, a server implementation cannot simply ignore any malformed
    events since such events may either be critical to the structure of the
    room (for example, they may be `m.room.membership` events), or at the very
    least ignoring them would leave "holes" in the event graph which would
    prevent correct back-pagination.

## Ideas for mitigating the problem

The problems above appear to have some easy solutions. Let's describe some of
those ideas, before considering the fundamental problem that none of them can
solve.

### Validate all events when they are submitted

In this idea, we would require all server implementations to strictly validate
any data which is sent over the Client-Server API, to ensure that it complied
with the specified formats.

This evidently solves problem 1 above, in that it would prevent local users from
creating malformed events of any event types that the server supports; however,
it would do nothing to address any of the other problems.

### Validate events at the point they are served to a client

We could require that server implementations validate any data that they are
about to serve to a client; we might recommend that malformed data be stripped
out of the response, or redacted, or similar.

It is worth mentioning that this would be tricky to implement efficiently on
the server side, but it at least helps address most of the problems above, such
as historical data, or malformed events received over federation.

### Have servers re-validate data on upgrade

Similar to the previous idea, but rather than validating data each time it is
served to a client, any stored data could be re-validated to check that it
complies with new validation requirements.

This could be more efficient in the case that changes to validation rules are
rare, but it could still be a huge amount of data processing on a large server.

### Create new room versions which require events to be well-formed

As outlined above, one of the big problems in this area is how we deal with
events sent over federation; in particular, if subsets of the servers in a room
have different ideas as to which events are "valid", then their concepts of the
room state can begin to drift, and the room can eventually become
"split-brained". This makes it hard to simply say, for example,
"`m.room.member` events with a non-string `displayname` are invalid and should
not form part of the room state": we have a risk that some servers will accept
the event, and some will not.

One approach to solving this is via [room versions](https://spec.matrix.org/unstable/rooms/).
By specifying that a change of rules only applies for a future room version,
we can eliminate this potential disagreement.

The process of changing a room from one version to another is intrusive, not
least because it requires that all servers in a room support the new room
version (or risk being locked out). For that reason, it is extremely
undesirable that any new feature require a new room version: whenever possible,
it should be possible to use new features in existing rooms. It therefore
follows that we cannot rely on room versions to provide validation of event
data.

### Create a single new room version which applies all event validation rules

This idea is included for completeness, though it is unclear how it would work
in practice.

It has been suggested that we create a new room version which explicitly states
that events which fail the current event schema, whatever that is at that
moment in time, should be rejected.

Let's imagine that in future, the `m.room.member` event schema is extended to
include an optional `location` key, which, if given, must be a string. The
implication of this idea is that servers should reject any `m.room.member`
event whose `location` is not a string. We now have a problem: any servers in
the room which are updated to the latest spec will reject such malformed
events, but any other servers yet to be upgraded will allow it. So is that user
in the room or not?

Even if all the servers in the room can be upgraded at once, what about any
`m.room.member` events which were sent before the rule change?

## The fundamental problem

The ideas above all mitigate the problems discussed earlier to a greater or
lesser extent, and may indeed be worth doing on their own merits. However, none
of them can address the problem of outdated server implementations.

For example, consider the case of a new key being added to an event body, say
`m.relates_to`. Now, we may have decided as above that all new specced keys
must be validated by the server, so `vN+1` of Synapse dutifully implements such
validation and refuses to accept events with a malformed `m.relates_to`.

The problem comes for users whose server is still Synapse `vN`. It knows
nothing of `m.relates_to`, so accepts and passes it through even if
malformed. The only potential solution is for clients seeking to implement
`m.relates_to` to refuse to talk to servers which do not declare support for
it.

However, this is an entirely client-side feature: it is illogical to require
that servers must be upgraded before it can be used. Consider that the hosted
element-web at `https://app.element.io` is upgraded to support the new feature;
in this scenario, that would lock out any user whose homeserver had not yet
been upgraded. This is not an acceptable user experience.

In short, we are left with the reality that clients must still handle the
unvalidated data.

## Conclusions

Short of closely coupling server and client versions - which violates the
fundamental ethos of the Matrix project - there is nothing that can completely
prevent clients from having to handle untrusted data. In addition, encrypted
events eliminate any possibility of server-side validation.

With that in mind, the advantages of the ideas above are diminished. If clients
must handle untrusted data in some circumstances, why not in all? "You can
trust the content of this data structure, provided you have checked that the
server knows how to validate it, in which case you need to treat it as
untrusted" is not a useful message for a client developer.

It may be possible to assert that specific, known cases can be treated as
trusted data, but these should be called out as specific cases. The default
message should be that clients must treat all event data as untrusted.
