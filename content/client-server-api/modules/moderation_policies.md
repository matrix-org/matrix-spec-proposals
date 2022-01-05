---
type: module
---

### Moderation policy lists

With Matrix being an open network where anyone can participate, a very
wide range of content exists and it is important that users are
empowered to select which content they wish to see, and which content
they wish to block. By extension, room moderators and server admins
should also be able to select which content they do not wish to host in
their rooms and servers.

The protocol's position on this is one of neutrality: it should not be
deciding what content is undesirable for any particular entity and
should instead be empowering those entities to make their own decisions.
As such, a generic framework for communicating "moderation policy lists"
or "moderation policy rooms" is described. Note that this module only
describes the data structures and not how they should be interpreting:
the entity making the decisions on filtering is best positioned to
interpret the rules how it sees fit.

Moderation policy lists are stored as room state events. There are no
restrictions on how the rooms can be configured (they could be public,
private, encrypted, etc).

There are currently 3 kinds of entities which can be affected by rules:
`user`, `server`, and `room`. All 3 are described with
`m.policy.rule.<kind>` state events. The `state_key` for a policy rule
is an arbitrary string decided by the sender of the rule.

Rules contain recommendations and reasons for the rule existing. The
`reason` is a human-readable string which describes the
`recommendation`. Currently only one recommendation, `m.ban`, is
specified.

#### `m.ban` recommendation

When this recommendation is used, the entities affected by the rule
should be banned from participation where possible. The enforcement of
this is deliberately left as an implementation detail to avoid the
protocol imposing its opinion on how the policy list is to be
interpreted. However, a suggestion for a simple implementation is as
follows:

-   Is a `user` rule...
    -   Applied to a user: The user should be added to the subscriber's
        ignore list.
    -   Applied to a room: The user should be banned from the room
        (either on sight or immediately).
    -   Applied to a server: The user should not be allowed to send
        invites to users on the server.
-   Is a `room` rule...
    -   Applied to a user: The user should leave the room and not join
        it
        ([MSC2270](https://github.com/matrix-org/matrix-doc/pull/2270)-style
        ignore).
    -   Applied to a room: No-op because a room cannot ban itself.
    -   Applied to a server: The server should prevent users from
        joining the room and from receiving invites to it.
-   Is a `server` rule...
    -   Applied to a user: The user should not receive events or invites
        from the server.
    -   Applied to a room: The server is added as a denied server in the
        ACLs.
    -   Applied to a server: The subscriber should avoid federating with
        the server as much as possible by blocking invites from the
        server and not sending traffic unless strictly required (no
        outbound invites).

#### Subscribing to policy lists

This is deliberately left as an implementation detail. For
implementations using the Client-Server API, this could be as easy as
joining or peeking the room. Joining or peeking is not required,
however: an implementation could poll for updates or use a different
technique for receiving updates to the policy's rules.

#### Sharing

In addition to sharing a direct reference to the room which contains the
policy's rules, plain http or https URLs can be used to share links to
the list. When the URL is approached with a `Accept: application/json`
header or has `.json` appended to the end of the URL, it should return a
JSON object containing a `room_uri` property which references the room.
Currently this would be a `matrix.to` URI, however in future it could be
a Matrix-schemed URI instead. When not approached with the intent of
JSON, the service could return a user-friendly page describing what is
included in the ban list.

#### Events

The `entity` described by the state events can contain `*` and `?` to
match zero or more and one or more characters respectively. Note that
rules against rooms can describe a room ID or room alias - the
subscriber is responsible for resolving the alias to a room ID if
desired.

{{% event event="m.policy.rule.user" %}}

{{% event event="m.policy.rule.room" %}}

{{% event event="m.policy.rule.server" %}}

#### Client behaviour

As described above, the client behaviour is deliberately left undefined.

#### Server behaviour

Servers have no additional requirements placed on them by this module.

#### Security considerations

This module could be used to build a system of shared blacklists, which
may create a divide within established communities if not carefully
deployed. This may well not be a suitable solution for all communities.

Depending on how implementations handle subscriptions, user IDs may be
linked to policy lists and therefore expose the views of that user. For
example, a client implementation which joins the user to the policy room
would expose the user's ID to observers of the policy room. In future,
[MSC1228](https://github.com/matrix-org/matrix-doc/pulls/1228) and
[MSC1777](https://github.com/matrix-org/matrix-doc/pulls/1777) (or
similar) could help solve this concern.
