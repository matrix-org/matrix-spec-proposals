# URI scheme for Matrix

This is a proposal of a URI scheme to identify Matrix resources in a wide
range of applications (web, desktop, or mobile) both throughout Matrix software
and (especially) outside of it. It supersedes 
[MSC455](https://github.com/matrix-org/matrix-doc/issues/455) in order
to continue the discussion in the modern GFM style.

While Matrix has its own resource naming system that allows it to identify
resources without resolving them, there is a common need to provide URIs
to Matrix resources (e.g., rooms, users, PDUs) that could be transferred
outside of Matrix and then resolved in a uniform way - matching URLs
in World Wide Web.

Specific use cases include:
1. Representation in UI: as a Matrix user I want to refer to Matrix entities
   in the same way as for web pages, so that others could “follow the link”
   I sent them (not necessarily through Matrix, it can be, e.g., a web page or
   email) in order to access the referred resource.
1. Inbound integration: as an author of Matrix software, I want to have a way
   to invoke my software from the operating environment to resolve a Matrix URI
   passed from another program. This is a case of, e.g.,
   opening a Matrix client by clicking on a link in an email program.
1. Outbound integration: as an author of Matrix software, I want to have a way
   to export identifiers of Matrix resources as URIs to non-Matrix environment
   so that they could be resolved in another time-place in a uniform way.
   This is a case of "Share via…" action in a mobile Matrix client.

https://matrix.to somehow compensates for the lack of dedicated URIs; however:
* it addresses use case (1) in a somewhat clumsy way (resolving a link needs
  two interactions with the user instead of one), and 
* it can only deal with (2) within a web browser (basically limiting
  first-class support to browser-based clients).

To cover the use cases above, the following scheme is proposed for Matrix URIs
(`[]` enclose optional parts, `{}` enclose variables):
```text
matrix:[//{authority}/]{type}/{id without sigil}[/{more type/id pairs}][?{query}]
```
with `type` being one of: `user`, `room`, `roomid`, `event` and
`group`; and the only `query` defined for now is `action=join`. The Matrix
identifier (or identifiers) can be reconstructed from the URI by taking
the sigil that corresponds to `type` and appending `id without sigil` to it.
The query may alter the kind of request with respect to the Matrix resource;
and Matrix resources can be contained in each other, in which care the
`more type/id pairs` series is used to reconstruct inner identifiers.

This proposal defines initial mapping of URIs to Matrix identifiers and actions
on corresponding resources; the scheme and mapping are subject
to further extension.

Examples:
* Room `#someroom:example.org`:
  `matrix:room/someroom:example.org`
* Unfederated room `#internalroom:internal.example.org`:
  `matrix://internal.example.org/room/internalroom:internal.example.org`
* Event in a room:
  `matrix:room/someroom:example.org/event/Arbitrary_Event_Id`
* [A commit like this](https://github.com/her001/steamlug.org/commit/2bd69441e1cf21f626e699f0957193f45a1d560f)
  could make use of a Matrix URI in the form of
  `<a href="{Matrix URI}">{Matrix identifier}</a>`.
  
This MSC does not introduce new Matrix entities, nor API endpoints -
it merely defines a mapping from a URI with the scheme name `matrix:`
to Matrix identifiers and actions on them. It is deemed sufficient to
produce an implementation that would convert Matrix URIs to a series
of CS API calls, entirely on the client side. It is recognised,
however, that most of URI processing logic can and should (eventually)
be on the server side in order to facilitate adoption of Matrix URIs;
further MSCs are needed to define details for that.

## Proposal

Further text uses “Matrix identifier” with a meaning of identifiers
as described by [Matrix Specification](https://matrix.org/docs/spec/),
and “Matrix URI” with a meaning of an identifier following
the RFC-compliant URI format proposed hereby.

### Requirements

The following considerations drive the requirements for Matrix URIs:
1. Follow existing standards and practices.
1. Endorse the principle of least surprise.
1. Humans first, machines second.
1. Cover as many entities as practical.
1. URIs are expected to be extremely portable and stable;
   you cannot rewrite them once they are released to the world.
1. Ease of implementation, allowing reuse of existing codes.

The following requirements resulted from these drivers
(see [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt) for conventions
around MUST/SHOULD/MAY):
1. Matrix URI MUST comply with
   [RFC 3986](https://tools.ietf.org/html/rfc3986) and
   [RFC 7595](https://tools.ietf.org/html/rfc7595).
1. By definition, Matrix URI MUST unambiguously identify a resource
   in a Matrix network, across servers and types of resources.
   This means, in particular, that two Matrix identifiers distinct by
   [Matrix Specification](https://matrix.org/docs/spec/appendices.html#identifier-grammar)
   MUST NOT have Matrix URIs that are equal in
   [RFC 3986](https://tools.ietf.org/html/rfc3986) sense
   (but two distinct Matrix URIs MAY map to the same Matrix identifier).
1. The following classes MUST be supported:
   1. User IDs (`@user:example.org`)
   1. Room IDs (`!roomid:example.org`)
   1. Room aliases (`#roomalias:example.org`)
   1. Event IDs (`$eventid:example.org`)
1. The mapping MUST take into account that some identifiers
   (e.g. aliases) can have non-ASCII characters - reusing
   [RFC 3987](https://tools.ietf.org/html/rfc3987) is RECOMMENDED
   but an alternative encoding can be used if there are reasons
   for that.
1. The mapping between Matrix identifiers and Matrix URIs MUST
   be extensible (without invalidating previous URIs) to:
   1. new classes of identifiers (there MUST be a meta-rule to produce
      a new mapping for IDs following the `&somethingnew:example.org`
      pattern assumed for Matrix identifiers);
   1. new ways to navigate to and interact with objects in Matrix
      (e.g., we might eventually want to have a mapping for
      room-specific user profiles).
1. The mapping MUST support decentralised as well as centralised IDs.
   This basically means that the URI scheme MUST have provisions
   for mapping of `:<serverpart>` but it MUST NOT require
   `:<serverpart>` to be there.
1. Matrix URI SHOULD allow encoding of action requests such as joining
   a room.
1. Matrix URI SHOULD have a human-readable, if not necessarily
   human-friendly, representation - to allow visual sanity-checks.
   In particular, characters escaping/encoding should be reduced
   to bare minimum in that representation. As a food for thought, see
   [Wikipedia: Clean URL, aka SEF URL](https://en.wikipedia.org/wiki/Clean_URL) and
   [a very relevant use case from RFC 3986](https://tools.ietf.org/html/rfc3986#section-1.2.1).
1. It SHOULD be easy to parse Matrix URI in popular programming
   languages: e.g., one should be able to use `parseUri()`
   to dissect a Matrix URI in JavaScript.
1. The mapping SHOULD be consistent across different classes of
   Matrix identifiers.
1. The mapping SHOULD support linking to unfederated servers/networks
   (see also
   [matrix-doc#2309](https://github.com/matrix-org/matrix-doc/issues/2309)
   that calls for such linking).

The syntax and mapping discussed below meet all these requirements.
Further extensions MUST comply to them as well.

### Syntax and high-level processing

The proposed generic Matrix URI syntax is a subset of the generic
URI syntax
[defined by RFC 3986](https://tools.ietf.org/html/rfc3986#section-3):
```text
MatrixURI = “matrix:” hier-part [ “?” query ] [ “#” fragment ]
hier-part = [ “//” authority “/” ] path
```
As mentioned above, this MSC assumes client-side URI processing
(i.e. mapping to Matrix identifiers and CS API requests).
However, even when URI processing is shifted to the server side
the client will still have to parse the URI at least to find
the authority part (or lack of it) and remove the fragment part
before sending the request to the server (more on that below).

#### Scheme name
The proposed scheme name is `matrix`.
[RFC 7595](https://tools.ietf.org/html/rfc7595) states:
  
    if there’s one-to-one correspondence between a service name and
    a scheme name then the scheme name should be the same as
    the service name.

Other considered options were `mx` and `web+matrix`;
[comments to MSC455](https://github.com/matrix-org/matrix-doc/issues/455)
mention two scheme names proposed and one more has been mentioned
in `#matrix-core:matrix.org`).

The scheme name is a definitive indication of a Matrix URI and MUST NOT
be omitted. As can be seen below, Matrix URI rely heavily on [relative
references](https://tools.ietf.org/html/rfc3986#section-4.2) and
omitting the scheme name makes them indistinguishable from a local path
that might have nothing to do with Matrix. Clients MUST NOT try to
parse pieces like `room/MyRoom:example.org` as Matrix URIs; instead,
users should be encouraged to use Matrix IDs for in-text references
(`#MyRoom:example.org`) and client applications should do
the heavy-lifting of turning them into hyperlinks to Matrix URIs.

#### Authority

The authority part is used for the specific case of getting access
to a Matrix resource (such as a room or a user) through a given server.
```text
authority = host [ “:” port ]
```

Here's an example of a Matrix URI with an authority part
(the authority part is `example.org:682` here):
`matrix://example.org:682/roomid/Internal_Room_Id:example2.org`.

The main purpose of the authority part,
[as per RFC 3986](https://tools.ietf.org/html/rfc3986#section-3.2),
is to identify the authority governing the namespace for the rest
of the URI. This MSC reuses the RFC definitions for
[`host`](https://tools.ietf.org/html/rfc3986#section-3.2.2) and
[`port`](https://tools.ietf.org/html/rfc3986#section-3.2.3).
RFC 3986 also includes provisions for user information -
this MSC explicitly omits them. If providing a user identity
in the authority part is found to be of value in some case,
this can be addressed in a separate MSC.

When a Matrix client needs to obtain the resource specified by a URI
with an authority part, the client MUST,
_instead of engaging the current user's homeserver connection_:
1. resolve the homeserver (further referred to as authority server) using
   [the standard process for server discovery](https://matrix.org/docs/spec/client_server/latest#server-discovery)
   from the authority part;
1. interrogate the resolved authority server using Matrix APIs in order
   to get or interact with the resource encoded in the URI.

Importantly, the authority part is _not_ intended for usage in routing
over federation; rather, it is for cases when a given Matrix
entity is not expected to be reachable through federation (such as
unfederated rooms or non-public Matrix networks). Sending requests
to the server resolved from the authority part means that the client
should be, as the name implies, _authorised_ by the authority server
to access the requested resource. That implies that the resource
is either available to guests on the authority server, or the end user
must be authenticated (and their access rights checked)
on that server in order to access the resource.

#### Path
Unlike the very wide definition of path in RFC 3986, this MSC
restricts the path component of a Matrix URI to a simple
pattern that allows to easily reconstruct a Matrix identifier or
a chain of identifiers:
```text
path = type “/” id-without-sigil [“/” path]
type = “user” / “roomid” / “room” / “event” / “group”
id-without-sigil = string ; see below
```
The path component consists of 1 or more type-id pairs separated
by slash character both inside the pair and between pairs. While most
of the URIs considered in this MSC do not need any sort of hierarchy,
one case is standing out: as of now, events require rooms to be
resolved so an event URI for `$eventid` in the room
`!roomid:example2.org` would be
`matrix:room/roomid:example2.org/event/eventid`.

This MSC defines the following type specifiers:
`user` (user id, sigil `@`), `roomid` (room id, sigil `!`),
`room` (room alias, sigil `#`), and `event` (event id, sigil `$`).
The type `group` (group/community id, sigil `+`) is reserved for future use.

`id-without-sigil` is defined as the `string` part of Matrix
[Common identifier format](https://matrix.org/docs/spec/appendices#common-identifier-format) with percent-encoded characters that are NEITHER
unreserved, sub-delimiters, `:` nor `@`,
[as per RFC 3986 rule for pchar](https://tools.ietf.org/html/rfc3986#appendix-A).
This notably exempts `:` from percent-encoding but includes `/`.

See subsections of the same section for details on each type of
identifier.

The rationale behind dropping sigils is two-fold:
* (most important) Semantic and grammatic clashes with RFC.
  `#` delimits a fragment; `@` delimits user information. Percent-encoding
  these is not a reasonable option, given that the two are the most used sigils.
* The namespace for sigils is extremely limited. Not that Matrix showed
  any tendency to produce plenty of various classes of objects but
  that cannot be ruled out; so rather then hit the wall together
  with the institute of sigils, this MSC proposes
  a more extensible solution from the outset.
  
Clients MUST resolve all Matrix entities that they support.

Further MSCs may introduce navigation to more top-level as well as
non-top-level objects; e.g., one could conceive a URI mapping of avatars
in the form of
`matrix:user/uid:matrix.org/avatar/room:matrix.org`
(a user’s avatar for a given room).

#### Query

Matrix URI can optionally have
[the query part](https://tools.ietf.org/html/rfc3986#section-3.4).
This MSC defines only two specific forms for the query; further MSCs
may add to this as long as RFC 3986 is followed.
```text
query = query-element *( “&” query-element )
query-element = action / routing
action = “action=join”
routing = “via=” authority
```
The join action can only be used with a URI resolving to a room; applications
MUST ignore it if found and MUST NOT generate it for other Matrix resources.
This action means that rather than just navigate to the room
client applications SHOULD attempt to join it using the standard CS API means.
Client applications SHOULD ask for user confirmation before joining if the user
is not a joined member in the room nor in its immediate
[successor or predecessor](https://matrix.org/docs/spec/client_server/latest#module-room-upgrades).

The routing query is only allowed with URIs that have path starting with
`roomid/` to indicate servers that are likely involved in the room (cf.
[the feature of matrix.to](https://matrix.org/docs/spec/appendices#routing)).
For other URIs it SHOULD be ignored and clients SHOULD NOT generate it. Note
that `authority` here only represents the server grammar as defined in
the respective section above; it doesn't need to coincide with the actual
authority server if it's also supplied in the URI.


### URI semantics

The main purpose of a Matrix URI is accessing the resource specified by the
identifier, and the primary action is loading the contents of a document
corresponding to a given resource. This MSC defines the "default" action
that a client application SHOULD perform when the user activates
(e.g. clicks on) a URI; further MSCs may introduce additional actions enabled
either by passing an `action` value in the query part, or by other means.
The classes of URIs and corresponding default actions (along with relevant
CS API calls) are collected as follows:

* User ID:
  - URI example: `matrix:user/me:example.org` or
    (decentralised user id, future) `matrix:user/me_in_matrix`
  - Default action: Show user profile (`GET /profile/@me:example.org/...`,
    `GET /profile/@me_in_matrix/...`)
* Room ID:
  - URI example: `matrix:roomid/rid:example.org` or
    (decentralised id, future) `!lol823y4bcp3qo4`
  - Default action: attempt to "open" the room (usually means the client
    at least displays the room timeline at the latest or
    the last remembered position - `GET /rooms/!rid:example.org/...`,
    `GET /rooms/!lol823y4bcp3qo4/...`)
* Joining by Room ID:
  - URI example: `matrix:roomid/rid:example.org?action=join&via=example2.org`
  - Default action: if needed (see the section about the query part) ask
    the user to confirm the intention; then join the room
    (`POST /join/!rid:example.org?server_name=example2.org`)
* Room alias:
  - URI example: `matrix:room/us:example.org`
  - Default action: resolve the alias to room id
    (`GET /directory/room/#us:example.org` if needed) and attempt to "open"
    the room (same as above)
* Joining by Room alias:
  - URI example: `matrix:room/us:example.org?action=join`
  - Default action: if needed (see the section about the query part) ask
    the user to confirm the intention; then join the room
    (`POST /join/#us:example.org`)
* Event ID (as used in
  [room version 3](https://matrix.org/docs/spec/rooms/v3) and later):
  - URI example (aka "event permalink"):
    `matrix:room/us:example.org/event/UnpaddedBase64` or
    (additional routing is needed for room id)
    `matrix:roomid/rid:example.org/event/UnpaddedBase64?via=example2.org`
  - Default action:
    1. For room aliases, resolve an alias to a room id (see above)
    1. If the event is in the room that the user has joined, retrieve
       the event contents (`GET /rooms/!rid:example.org/event/UnpaddedBase64` or
       `GET /rooms/!rid:example.org/context/UnpaddedBase64`) and display them
       to the user 
    1. Otherwise try to retrieve the event in the same way but in case of
       access failure the client MAY offer the user to join the room; if
       the user agrees and joining succeeds, retry the step above.
* Group ID:
  - URI example: `matrix:group/them:matrix.org`
  - Default action: reserved for future use


## Discussion points and tradeoffs

The below documents the discussion and outcomes in various prior forums;
further discussion should happen in GitHub comments.
1. _Why no double-slashes in a typical URI?_
   Because `//` is used to mark the beginning of an authority
   part. RFC 3986 explicitly forbids to start the path component with
   `//` if the URI doesn't have an authority component. In other words,
   `//` implies a centre of authority, and the (public) Matrix
   federation is not supposed to have one; hence no `//` in most URIs.
1. _Why type specifiers use singular rather than plural
   as is common in RESTful APIs?_
   Unlike in actual RESTful APIs, this MSC does not see `rooms/` or
   `users/` as collections to browse. The type specifier completes
   the id specification in the URI, defining a very specific and
   easy to parse syntax for that. Future MSCs may certainly add
   collection URIs, but it is recommended to use more distinct naming
   for such collections. In particular, `rooms/` is ambiguous, as
   different sets of rooms are available to any user at any time
   (e.g., all rooms known to the user; or all routable rooms; or
   public rooms known to the user's homeserver).
1. (still open)
   _Should we advise using the query part for collections then?_
1. (still open)
   _Why not Reddit-style single-letter type specifiers? That's almost
   as compact as a sigil, still pretty clearly conveys the type,
   and nicely avoids the confusion described in the previous question._
   Readability?
1. _Why event URI cannot use the fragment part for the event id?_
   Because fragment is a part processed exclusively by the client
   in order to navigate within a larger document, and room cannot
   be considered a "document". Each event can be retrieved from the server
   individually, so each event can be viewed as a self-contained document.
   When URI processing is shifted to the server-side, servers are not even
   going to receive fragments (as per RFC 3986).
1. _Interoperability with
   [Linked Data](https://en.wikipedia.org/wiki/Linked_data)_ is out of
   scope of this MSC but worth being considered separately.
1. _How does this MSC work with closed federations?_ If you need to
   communicate a URI to the bigger world where you cannot expect
   the consumer to know in advance which federation they should use -
   supply any server of the closed federation in the authority part.
   Users inside the closed federation can omit the authority part if
   they know the URI is not going to be used outside this federation.
   Clients can facilitate that by having an option to always add or omit
   the authority part in generated URIs for a given user account.


## Further evolution

This MSC is obviously just the first step, opening the door for a range of
extensions, especially to the query part. Possible actions may include
opening the
[canonical direct chat](https://github.com/matrix-org/matrix-doc/pull/2199)
(`action=chat`, following the existing convention in Riot),
leaving a room (`action=leave`); bounds for a segment of the room timeline
(`from=$evtid1&to=$evtid2`) also look worthwhile.


## Alternatives

The discussion in
[MSC455](https://github.com/matrix-org/matrix-doc/issues/455)
mentions an option to standardise URNs rather than URLs/URIs,
with the list of resolvers being user-specific. While a URN namespace
such as `urn:matrix:`, along with a URN scheme, might be deemed useful
once we shift to (even) more decentralised structure of the network,
`urn:` URIs must be managed entities (see
[RFC 8141](https://tools.ietf.org/html/rfc8141)) which is not always
the case in Matrix (consider room aliases, e.g.).

With that said, a URN-styled (`matrix:room:example.org:roomalias`)
option was considered. However, Matrix already uses colon (`:`) as
a delimiter of id parts and, as can be seen above, reversing the parts
to meet the URN's hierarchical order would look confusing for Matrix
users.

Yet another alternative considered was to go "full REST" and build
a more traditional looking URL structure with serverparts coming first
followed by type grouping (sic - not specifiers) and then by localparts,
i.e. `matrix://example.org/rooms/roomalias`. This is even more
difficult to comprehend for a Matrix user than the previous alternative
and besides it conflates the notion of an authority server with
that of a namespace (`example.org` above is a server part of an alias,
not the name of a homeserver that should be used to resolve the URI).


## Potential issues

Despite the limited functionality of URIs as proposed in this MSC,
Matrix authors are advised to use tools that would process URIs just
like an http(s) URI instead of making a quick home-baked
parsers/emitters. Even with that in mind, not all tools normalise and
sanitise all cases in a fully RFC-compliant way. This MSC tries to keep
the required transformations to the minimum and will likely not bring
much grief even with naive implementations; however, as functionality
of Matrix URI grows, the number of corner cases will increase.


## Security considerations

This MSC mostly builds on RFC 3986 but tries to reduce the scope
as much as possible. Notably, it avoids introducing complex traversable
structures and defines the URI grammar quite strictly. Notably,
dot path segments (`.` and `..`), while potentially useful when URIs
become richer, would come too much ahead of time for now. Care is taken
to not make essential parts of the URI omittable to avoid
even accidental misrepresentation of a local resource for a remote one
in Matrix and vice versa. One part still omittable - authority - can
result in leaks if a non-fully-qualified URI from one closed federation
is sent to another closed federation; this is considered an extremely
corner case.

The MSC intentionally doesn't support conveying any kind of user
information in URIs.


## Conclusion

A dedicated URI scheme is well overdue for Matrix. Many other networks
already have got one for themselves, benefiting both in terms of
branding (compare `matrix:room/weruletheworld:example.org` vs.
`#weruletheworld:example.org` from the standpoint of someone who
hasn't been to Matrix) and interoperability (`matrix.to` requires
opening a browser while clicking a `tg:` link dumped to the terminal
application will open the correct application for Telegram without
user intervention or can even offer to install one, if needed).
The proposed syntax makes conversion between Matrix URIs
and Matrix identifiers as easy as a bunch of regular expressions; so
even though client-side processing of URIs might not be optimal
longer-term, it's a very simple and quick way that allows plenty
of experimentation early on.
