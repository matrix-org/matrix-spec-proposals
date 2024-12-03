# MSC3865: User-given attributes for users

> This MSC is similar to [MSC3864](https://github.com/matrix-org/matrix-spec-proposals/pull/3864),
> which specifies user-given attributes for rooms.
> They were split because it makes more sense for now to store user attributes in another way
> and because it shall be possible to set a user-given name for any MXID restricted to a single room.
> However, they may share the same ideas and reasonings.

User-given displaynames loaded from an addressbook are great,
they allow you to personalize your experience in using an IM
while others do not need to change anything.
Like when you write with privacy-concerned users,
they might use a nickname for their account on their own,
but you may want to have them listed by their real name
or any other funny nickname you've given them.
Or people are using their display name to present statements like "(away until X)"
and you want to set an end to that (for yourself).
Or because you prefer them in another language to make your daily life easier.

Also, sometimes you just may want to append a description to a user,
so you know why you are messanging with the user.
Descriptions like "old class mate from XYZ School" can certainly improve your UX,
especially when users change their names due to personal reasons ("new name is cooler, duh")
and you stop recognizing who they are and need to ask them for their real life name
or read through the chat history (happened multiple times to me personally).

The same reasons apply to the user's avatar.
If you have a better one, you shall be able to select that one for yourself.


## Definitions

Further on, for the sake of simplicity and clarity:
- the prefix **global** refers to the attribute which a user set for itself,
  visible globally to all other Matrix users.
- the prefix **user-given** refers to the overrided/extended attribute a user defines for another user,
  only visible to the former user.
  These are newly defined by this MSC.
  They may be scoped for all occurencies or for a single room only.
- the prefixes **room-scoped** and **global-scoped** may specify the scope of *user-given* attributes


## Proposal


### Reasoning

Allowing users to set user-given attributes for other users is useful
because it let users increase their usability and accessibility to the Matrix infrastructure on their own and as required.
These attributes shall stay private to the user itself and may not be seen to others,
so users are able to choose what they see fit best
without thinking about privacy issues or the feelings of the users affected.

Adding this feature to the spec has the advantage
that presumable most clients will implement support for displaying
and hopefully also setting these user-given attributes.
It also allows a more unified experience accross all clients and devices
because user-given attributes are synced using the home server of the user.
For the same reason, this proposal includes a description of the expected user experience.

This proposal takes advantage of the already implemented
[client config feature](https://spec.matrix.org/unstable/client-server-api/#client-config) (a.k.a. `account_data`)
so the API and the server implementations do not need to change.
The user-given attributes will be saved in the global `account_data` for the user,
if the attributes shall be used globally.
The user-given attributes can also be room-scoped,
if they shall only apply for this certain room.
Both kinds of client configs are only visible to the user who set them
and are synced across all devices of the user,
which makes them a perfect fit for storing user-given attributes.


### Implementation

For each attribute of a user profile, a new event type shall be defined.
To get the new event type, the prefix `m.user_given.user.` shall be appended to the attribute's name.
The subpart `user` is added to prevent name clashings with room's user-defined attributes
from [MSC3864](https://github.com/matrix-org/matrix-spec-proposals/pull/3864).
Additionally, as users do not have any kind of description,
a new type for that shall be defined with the name `description` and type `string`.
For some existing attributes, their event types are listed below.

| Current user attribute event type | User-defined event type         | Content type     |
| --------------------------------- | ------------------------------- | ---------------- |
| `displayname`                     | `m.user_given.user.displayname` | `mxid -> string` |
| `avatar_url`                      | `m.user_given.user.avatar_url`  | `mxid -> URL`    |
| does not exist                    | `m.user_given.user.description` | `mxid -> string` |

However, when the user profile get a new attribute,
the same rules may apply to it to store its user-defined counterparts.

Because the `account_config`'s of one user cannot be mapped to another one like they can be mapped to rooms,
a single event type may store all user-given attributes a user has set in a mapping (a.k.a JSON object).
The keys of this mapping may be the affected user's Matrix IDs.
The values of this mapping must be of the same type as defined for the overriden/extended user attribute
(e.g. `string` for `displayname` and an URL for `avatar_url`).
The mapping will be stored in a key called `content` along its explicit event `type`.
The following shall serve as an example value of the event type `m.user_given.user.displayname`,
which a client requested with one of both listed requests:

- `GET /_matrix/client/v3/user/{userId}/account_data/m.user_given.user.displayname`
  for global-scoped user-given attributes
- `GET /_matrix/client/v3/user/{userId}/room/{roomId}/account_data/m.user_given.user.displayname`
  for room-scoped user-given attributes

```json
{
    "content": {
        "@alice:example.com": "My Wife",
        "@bob:example.com": "Bobby",
        "@eve:example.com": "My Lifelong Rival"
    },
    "type": "m.user_given.user.displayname"
}
```

The defined new event types for `account_data` may be global-scoped or room-scoped,
depending on the intended scope of the user-given attribute.
The latter takes precendence.


### User Experience

Clients shall replace most occurencies of another user's global attribute with its user-given attribute.
When the user gets informed about a change of a global attribute of an user,
this occurency may not be replaced with the user-given attribute.
Clients shall also replace the global displayname in auto-generated names,
for example for direct messaging rooms.
However, in such events, the user-given attribute may be displayed as well, if possible and not already.
The client must not replace the Matrix ID of these users.

In some cases, the client may display both attributes (global and user-given) alongside each other,
if it makes sense in context of the attribute
and both attributes can be distinguished from one and another
(see [User Experience Issues](#user-experience-issues) for approaches on how to make them distinguishable).
However, the user-given attribute shall take precendece over the global one,
especially if the client can or wants to only display one of both
(see [Alternatives](#alternatives) for reasoning).
As an example, the client may display the displayname of an user as `USER_GIVEN_DISPLAYNAME (GLOBAL_DISPLAYNAME)`
with only the user-given avatar
but both the user-given description and the global description in this order
(assuming a user could have a global description (may be added in the future)
and all user-given attributes were set).

This exception does not apply to user-given room-scoped attributes and user-given global attributes.
If both a room-scoped and global-scoped user-given attributes are defined,
first the room-scoped user-given attribute takes precendece,
then the exception from above applies to the room-scoped user-given attribute and the global attribute.

Clients may choose do not support setting room-scoped user-given attributes
(e.g. because the client tries to be simplistic and easy-to-use),
however, if set by another client,
they should still be able to display them correctly.
The may make it configurable to the user if they shall use room-scoped attributes.

If clients want to divert from the user experience declared here,
but still want to confirm to this MSC,
they may implement the user experience from above and their own approach
and make them configurable for the user.
As long as a configuration option is easily available,
clients may choose their own approach as the default.


## Potential Issues


### Privacy Issues

Because `account_data` in general is sent unencrypted to the home server (for now),
the administrators of the HS or hackers who gained access to the HS may be able to retrieve these names and descriptions.
This may lead into privacy issues the user may not be aware of.
This could be prevented to encrypt account data before storing it on the server,
however this is a task for another MSC to solve, preferably for all account data.


### User Experience Issues

Using user-given attributes forgetting that the user has configured them
could lead into the bad UX that users think their client stopped working correctly,
as a new attribute of the user is not updated correctly.
This may be mitigated by clients by informing users about that the attribute is custom, either by:

- displaying user-given attributes in a custom style (e.g. **bold** or *italics*), border or color,
- displaying the global attribute aside ("USER_GIVEN_DISPLAYNAME (GLOBAL_DISPLAYNAME)", e.g. "My Wife (Alice)"),
- displaying the global attribute when hovering with the cursor over the user-given attribute,
- or by another, similar approach.

Clients may choose how they want to display and annotate user-given attributes and global attributes
by implementing none or any or some or all points from above as they see fit.


## Alternatives

At first, this MSC was combined with [MSC3864](https://github.com/matrix-org/matrix-spec-proposals/pull/3864)
to reuse the same implementation, which works for rooms,
for users by storing the user-given attributes in the `account_config` scoped the 1:1 DM room.
However, as a pair of users can have multiple DM rooms,
clients may not to choose the same DM room for these attributes and so become out of sync.
To circumvent this problem, the global `account_config` with a mapping was choosen.
This way, the same implementation can be reused to define room-scoped user-given attributes.

Conceptually, the user-given attribute could also be displayed as a secondary attribute alongside the global attribute
("GLOBAL_DISPLAYNAME (USER_GIVEN_DISPLAYNAME)", e.g. "Alice (My Wife)").
This could prevent some [UX issues](#user-experience-issues),
however this prevents users to customize their experience in certain ways
(e.g. when they don't want to read the global name).
With this implementation, a user is still able to display (parts of) the global name
as they like by adding it to the user-given name theirselves.
It only would not be updated automatically.
Clients which do not want to agree may implement both approaches and make the configurable to the user
as stated above in [User Experience](#user-experience).


## Security considerations

This proposal should not touch any security-sensitive components
ans so should not create any security-releated issues.


## Unstable prefix

Until this MSC is merged, clients shall use event type names
where the `m.` prefix is replaced with `work.banananet.msc3865.`
(e.g. use `work.banananet.msc3865.user_given.user.displayname` instead of `m.user_given.user.displayname`).
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
