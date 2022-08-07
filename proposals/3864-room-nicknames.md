# MSC3864: User-given nicknames & descriptions for rooms & users

User-given Nicknames or names loaded from an addressbook are great,
they allow you to personalize your experience in using an IM
while others do not need to change anything.
Like when you write with privacy-concerned users,
they might use a nickname for their account on their own,
but you may want to have them listed by their real name
or any other funny nickname you've given them.
Or people are using their display name to present statements like "(away until X)"
and you want to set an end to that (for yourself).

The same for groups, sometimes, the *global* room name works fine,
but it would be funnier or easier for you to use another one.
Maybe because you've grouped similar rooms together into a (personal) space,
so parts of the name become irrelevant.
Like in a space called "My Long Cooperation Name",
where every room is called like "My Long Cooperation Name - IT Team Chat",
maybe shorter names like "IT Team" or "MLCN - IT Team" are better suited to you.
Or maybe because the admin is just too lazy or stubborn to improve the room name.

Also, sometimes you just may want to append a description to a room or user,
so you know why you joined the room or are knowning the user.
Descriptions like "old class mate from XYZ School" can certainly improve your UX,
especially when users or rooms change their names due to personal reasons ("new name is cooler, duh")
and you stop recognizing who they are and need to ask them for their real life name
or read through the chat history (happened multiple times to me personally).


## Definitions

Further on, for the sake of simplicity and clarity:
- **global name** is the display name
  - a user set for itself, visible globally to all other Matrix users.
  - a room was given, visible globally to all other users who can see the room.
- **user-given name** refers to the name defined here a user shall be able to set,
  only visible for itself, for other users or rooms,
  replacing the global name.
- **global description** is the display description
  a room was given, visible globally to all other users who can see the room.
- **user-given description** refers to the description defined here a user shall be able to set,
  only visible for itself, for rooms,
  extending the global description.


## Proposal


### Reasoning

Allowing users to set user-given names and descriptions for rooms and other users is useful
because it let users increase their usability and accessibility to the Matrix infrastructure on their own and as required.
These names shall stay private to the user itself and may not be seen to others,
so users are able to choose what they see fit best
without thinking about privacy issues or the feelings of the room or users renamed.

Adding this feature to the spec has the advantage that presumable most clients will implement support for displaying and hopefully also setting names and descriptions.
It also allows a more unified experience accross all clients and devices
because user-given names and descriptions are synced using the home server of the user.
For the same reason, this proposal includes a description of the expected user experience.

This proposal takes advantage of the already implemented
[client config feature](https://spec.matrix.org/unstable/client-server-api/#client-config) (a.k.a. `account_data`)
so the API and the server implementations do not need to change.
The user-given names and descriptions will be saved scoped to the room and in an own namespace.
Client configs are only visible to the user who set them and are synced accross all devices of the user,
which makes them a perfect fit for storing user-given names and user-given description.


### Implementation

For user-given names, a new event type called `m.name.user_given` may be added.
The content of this event will be `{"content": "<USER_GIVEN_NAME>"}`

For user-given descriptions, a new event type called `m.description.user_given` may be added.
The content of this event will be `{"content": "<USER_GIVEN_DESCRIPTION>"}`

Clients shall store & read those event types scoped to the selected / affected room.
This means they will GET / PUT following URL:
`/_matrix/client/v3/user/{userId}/rooms/{roomId}/account_data/{type}`
with parameters as follows:
- `{userId}`: The user id of the current user.
- `{roomId}`: The room id of the selected / affected room id.
- `{type}`: Either `m.name.user_given` or `m.description.user_given`

When setting user-given names and descriptions to other users,
clients shall scope the events to the room both users use to exchange 1:1 direct messages
(according to [MSC2199](https://github.com/matrix-org/matrix-spec-proposals/pull/2199)).
If a user may leave the last DM room, the user-given names and descriptions may be lost as well.
This behavior may or may not be expected, depending on the user's preference.
Clients may inform the user about this circumstance so they can make an informed choice.


### User Experience

Clients shall replace most occurencies of the global name of a room with user-given name, if set.
Clients may still display the global name in some occurencies
according to the section [User Experience Issues](#user-experience-issues) below.
When the user wants to change the global name of a room,
or the user gets informed about a change of the global name of a room,
the global name may also not be replaced with the user-given name.
However in such events, the user-given name may be displayed as well.

Clients shall append the user-given description to most occurencies of the global description of a room.
Clients shall display both in a way so the user can separate them and interpret them correctly.

Clients shall also replace most occurencies of another user's global name with its user-given name.
Aside from the DM room both users are using to exchange DMs,
this may include occurencies like in events or in member lists of other rooms.
When the user gets informed about a change of the global name of an user,
the global name may also not be replaced with the user-given name.
However in such events, the user-given name may be displayed as well, if not already.

For both rooms and other users, the client must not replace the Matrix ID of rooms / users.


## Potential Issues


### Implementation Issues

Some issues I discovered while writing or applying this MSC.
These are listed here as points open to discuss further.

#### Non-unique DM room

This issue will be solved by [MSC2199](https://github.com/matrix-org/matrix-spec-proposals/pull/2199).


### Privacy Issues

Because account data in general is sent unencrypted to the home server (for now),
the administrators of the HS or hackers who gained access to the HS may be able to retrieve these names and descriptions.
This may lead into privacy issues the user may not be aware of.
This could be prevented to encrypt account data before storing it on the server,
however this is a task for another MSC to solve, preferably for all account data.


### User Experience Issues

Using user-given names and forgetting that the user has configured them
could lead into the bad UX that users think their client stopped working correctly,
as a new name of the room or user is not displayed correctly.
This may be mitigated by clients by informing users about that the name is custom, either by:
- displaying user-given names in a custom font, style (e.g. **bold** or *italics*) or color
- displaying the global name aside in brackets ("USER_GIVEN_NAME (GLOBAL_NAME)", e.g. "Sweatheart (Erika Musterfrau)")
  - this may only happen when reading messages of the room
- displaying the global name when hovering with the cursor over the user-given name

Clients may choose how they want to display and annotate user-given name and global name
by implementing none or any or some or all points from above as they see fit.
However, the user-given name shall be displayed as the primary name
(e.g. displaying as "**GLOBAL_NAME** (USER_GIVEN_NAME)"
or displaying the user-given name with less contrast than the global name
shall be prohibited, see [Alternatives](#alternatives) for reasoning).

The same problem should not occur in the same way to the user-given descriptions
as they shall expand the global description instead of replacing it.
However, clients should still display them either separated and labeled
or at least in way so users can separate them from one and another easily.


## Alternatives

User-given names and descriptions set for others users only may be stored into the general account data.
This would circumvent the problem with [non-unique DM rooms](#non-unique-dm-room) particular for this MSC.
However, clients may still need to solve this problem for other implementations,
so no complexity would be saved in the end.
It instead places them near other configurations like client-dependent (not room-dependent) configuration options,
and the user-given names and description may be lost when another user changes its Matrix ID
and it also lets the implementation for rooms and users differ more.

Conceptually, the user-given name could also be displayed as a secondary attribute alongside the global name
("GLOBAL_NAME (USER_GIVEN_NAME)", e.g. "Erika Musterfrau (Sweatheart)").
This could prevent some [UX issues](#user-experience-issues),
however this prevents users to customize their experience in certain ways
(e.g. when they don't want to read the global name).
With this implementation, a user is still able to display (parts of) the global name
as they like by adding it to the user-given name theirselves.
It only would not be updated automatically.


## Security considerations

This proposal should not touch any security-sensitive components
ans so should not create any security-releated issues.


## Unstable prefix

Until this MSC is merged, clients shall use event type names
where the `m.` prefix is replaced with `work.banananet.msc3864.`
(e.g. use `work.banananet.msc3864.name.user_given` instead of `m.name.user_given`).
Event types with the former prefix are further called *official event types*.
event types with the latter *unstable event types*.

After this MSC is merged, they shall begin to use the official event type.
and also migrate from an unstable event type to an official event type,
prefereable automtatically and in the background when finding such a event type.
However, for a reasonable time, the unstable event types shall still be set along the official ones.
If the clients detect, that the unstable event type's and official event type's contents differ,
they may prefer the content of the official ones.

After the reasonable migration time, clients may remove the unstable event types unconditionally,
prefereable automtatically and in the background when finding such a event type.
The migration policy might cause old clients to "lose" the user-given ones,
however hopefully this will move clients to migrate as well
and users to update their clients.


## Dependencies

This MSC formaly depends on [MSC2199](https://github.com/matrix-org/matrix-spec-proposals/pull/2199).
However, as long as clients can resolve an 1:1 DM room successfully by other means
(hopefully compatible to other clients as well),
clients should be able to implement this one.
