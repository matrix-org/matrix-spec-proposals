# MSC3864: User-given nicknames & descriptions for rooms

> This MSC is similar to [MSC3865](https://github.com/matrix-org/matrix-spec-proposals/pull/3865),
> which specifies user-given attributes for rooms.
> They were split because it makes more sense for now to store user attributes in another way
> and because it shall be possible to set a user-given name for any MXID restricted to a single room.
> However, they may share the same ideas and reasonings.

Sometimes, the *global* room name works fine,
but it would be funnier or easier for you to use another one.
Maybe because you've grouped similar rooms together into a (personal) space,
so parts of the name become irrelevant.
Like in a space called "My Long Cooperation Name",
where every room is called like "My Long Cooperation Name - IT Team Chat",
maybe shorter names like "IT Team" or "MLCN - IT Team" are better suited to you.
Or maybe because the admin is just too lazy or stubborn to improve the room name.
Or because you prefer them in another language to make your daily life easier.

Also, sometimes you just may want to append a description to a room,
so you know why you joined the room of have fast access to more information.
Especially when rooms change their descriptions,
but you still want to retain some links you connect to this group,
or these links do only apply for you.

The same reasons apply to the room's avatar.
If you have a better one, you shall be able to select that one for yourself.


## Definitions

Further on, for the sake of simplicity and clarity:
- the prefix **global** refers to the attribute which are set for a room,
  visible globally to all Matrix users.
- the prefix **user-given** refers to the overrided/extended attribute a user defines for a room,
  only visible to the former user.
  These are newly defined by this MSC.


## Proposal


### Reasoning

Allowing users to set user-given attributes for rooms is useful
because it let users increase their usability and accessibility to the Matrix infrastructure on their own and as required.
These attributes shall stay private to the user itself and may not be seen to others,
so users are able to choose what they see fit best
without thinking about privacy issues or the feelings of the users in the rooms affected.

Adding this feature to the spec has the advantage
that presumable most clients will implement support for displaying
and hopefully also setting these user-given attributes.
It also allows a more unified experience accross all clients and devices
because user-given attributes are synced using the home server of the user.
For the same reason, this proposal includes a description of the expected user experience.

This proposal takes advantage of the already implemented
[client config feature](https://spec.matrix.org/unstable/client-server-api/#client-config) (a.k.a. `account_data`)
so the API and the server implementations do not need to change.
The user-given attributes will be saved scoped to the room and in an own event type.
Client configs are only visible to the user who set them and are synced across all devices of the user,
which makes them a perfect fit for storing user-given names and user-given description.


### Implementation

For each state event of a room which present the aesthetic information about the room,
a new event type for the user-given counterpart shall be defined.
To get the new event type, the prefix `m.` will be replaced with `m.user_given.`.
Keeping the subpart `room` prevents name clashings with user's user-defined attributes
from [MSC3865](https://github.com/matrix-org/matrix-spec-proposals/pull/3865).
For the currently defined aesthetic state events, the new event types are listed below.

| Current room attribute name | User-defined event type         | Content type |
| --------------------------- | ------------------------------- | ------------ |
| `m.room.name`               | `m.user_given.room.name`        | `string`     |
| `m.room.avatar`             | `m.user_given.room.avatar`      | `URI`        |
| `m.room.topic`              | `m.user_given.room.description` | `string`     |

However, when rooms get a new aesthetic state event,
the same rules may apply to it to store its user-defined counterparts.

The user-defined event must contain the keys `type` with its event type
and `content` which must have the same type as the overriden/extended room state event.
The following shall serve as an example value of the event type `m.user_given.room.name`,
which a client requested with the listed request:

- `GET /_matrix/client/v3/user/{userId}/room/{roomId}/account_data/m.user_given.room.name`

```json
{
    "content": "Support Group: Gaming",
    "type": "m.user_given.room.name"
}
```


### User Experience

Clients shall replace most occurencies of a room's global attribute with its user-given attribute.
When the user gets informed about a change of a global attribute of a room,
this occurency may not be replaced with the user-given attribute.
However, in such events, the user-given attribute may be displayed as well, if possible and not already.
The client must not replace the IDs of these rooms.

In some cases, the client may display both attributes (global and user-given) alongside each other,
if it makes sense in context of the attribute
and both attributes can be distinguished from one and another
(see [User Experience Issues](#user-experience-issues) for approaches on how to make them distinguishable).
However, the user-given attribute shall take precendece over the global one,
especially if the client can or wants to only display one of both
(see [Alternatives](#alternatives) for reasoning).
As an example, the client may display the name of a room as `USER_GIVEN_NAME (GLOBAL_NAME)`
with only the user-given avatar
but both the user-given description and the global description in this order
(assuming all user-given attributes were set).

If clients want to divert from the user experience declared here,
but still want to confirm to this MSC,
they may implement the user experience from above and their own approach
and make them configurable for the user.
As long as a configuration option is easily available,
clients may choose their own approach as the default.


## Potential Issues


### Privacy Issues

Because account data in general is sent unencrypted to the home server (for now),
the administrators of the HS or hackers who gained access to the HS may be able to retrieve these names and descriptions.
This may lead into privacy issues the user may not be aware of.
This could be prevented to encrypt account data before storing it on the server,
however this is a task for another MSC to solve, preferably for all account data.


### User Experience Issues

Using user-given attributes forgetting that the user has configured them
could lead into the bad UX that users think their client stopped working correctly,
as a new attribute of the room is not updated correctly.
This may be mitigated by clients by informing users about that the attribute is custom, either by:

- displaying user-given attributes in a custom style (e.g. **bold** or *italics*), border or color,
- displaying the global attribute aside ("USER_GIVEN_NAME (GLOBAL_NAME)", e.g. "Support Group: Gaming (Gaming Buddies)"),
- displaying the global attribute when hovering with the cursor over the user-given attribute,
- or by another, similar approach.

Clients may choose how they want to display and annotate user-given attributes and global attributes
by implementing none or any or some or all points from above as they see fit.


## Alternatives

Conceptually, the user-given attribute could also be displayed as a secondary attribute alongside the global attribute
("GLOBAL_NAME (USER_GIVEN_NAME)", e.g. "Gaming Buddies (Support Group: Gaming)").
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
where the `m.` prefix is replaced with `work.banananet.msc3864.`
(e.g. use `work.banananet.msc3864.user_given.room.name` instead of `m.user_given.room.name`).
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
