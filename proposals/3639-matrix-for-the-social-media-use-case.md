# MSC3639: Matrix for the social media use case

Matrix is currently mainly used for chats, however, recent projects
have shown that it is possible to use it for social media.

This proposal is to formally specify this usage and ensure
a compatibility between the different social media projects.

## The idea

This MSC tries to cover those following social media cases:

* **'Regular'** social media like Circles or MinesTRIX
* **'Art'** social media like Matrix Art

## The proposal

To cover those use case, we will separate our proposal in two part.

* **Room types**: the container which will store the events.
* **Special events types**: to differentiate post and comment from room messages.


### Room

Social media generally allow the user to have a profile where he can
post content visible to all his followers. Others allow also creating
groups which allow the same things without being owned by a specific
user. This is the two functions that we want to add.

Therefore, we propose two room types. Types are defined according to 
[MSC1772 - Matrix spaces](https://github.com/matrix-org/matrix-doc/pull/1772).

* `m.social.profile`
* `m.social.group`

Those two rooms will act as a container for events of different types, which
will be displayed only on a specific client. The type is used to set the
general purpose of the room.

#### Social media : The user profile

```
m.social.profile
```

**Usage:**

Used by a user to share content with his friends or the world.

* Owned by a single user.
* The user can choose who can write on his profile.
* Room visibility : public / private. Up to the user.
* The user can have multiple profile (private / public ...)

This MSC remains voluntarily open as user may want to configure the room as he wishes.

*Small note about encryption:*

Clients should notify the user that encryption shouldn't be enabled
on 'big / public room'. On a side note, enabling end-to-end encrypted
rooms with a very large number of participants don't have a lot of sense. 

**UI considerations :**

* Should make clear that this room is owned by a specific user.
* UI type is up to the client (feed (list view), pictures waterfall (grid) ...)

##### Room visibility

Most users will want to have a private profile. However, the question
is now how can other user follow our profile ? It is always possible to
invite them in the room but in the world of social media, this is kind
of weird. This will be like sending a follow proposal.

This could be solved with knocking. The question being how do we discover the room ?

* room alias could be an answer (TODO: is it possible to get the room type ?)
* An other way could be to use a kind of profile as space. i.e. a place where a user can publicly advertise room that are related to him. This idea could be the topic of a following MSC.

#### Social media : Groups

```
m.social.group
```

**Usage:**

* For group discussion

Group is just a regular profile room `m.social.feed` but with a
slightly different UI as there is no single owner of the room.


### Sending posts

We propose to define a custom type for posts.

```
m.social.post
```

**Why ?**

As the room is displayed alongside the user's regular chats rooms, we need
to make it clear to the user that it's a specific room.
Thus, we need to avoid that a user end up "spamming" his room thinking
the room is a regular chat room.

Therefore, we use different event type to separate the regular messaging
from the social media posts. It will still be possible to send room message.
However, those should not be displayed on the user wall / group.

**NB:** An initial version of the proposal was using extensible events but
we decided to fall back to regular event while waiting for the extensible events
proposal to stabilize.


A type for general content. Its structure is of type:

```json
{
  "type": "m.social.post", 
  "content": {
    "body": "The content of the post, can be Markdown",
    "m.social.image-ref": [ // optional
      "$<event_id>",
    ]
  }
}
```

#### Embedding images in the post

If we want to embed images in the post, we should first send the image as a regular
event and then put the image event id in the `m.social.image-ref` attribute of the
post content. This, to allow user to allow a user to comment an image individually
or to reuse it in different posts. This allows us also to display more easily all
the images who have been posted in the room.


### Reactions

* Emoji reactions are standard matrix reactions.
* However, comments on posts will be threads.

Comments will have the same structure as post but will have the 'm.social.comment'
type to allow the owner of the room to allow commenting but preventing the other users
to send posts on this group. As said, comment need to have a thread relation to a post
event. Failing to do so will have no impact, but the event shouldn't be displayed.

**Example:**

```
{
  "type": "org.matrix.msc3639.social.comment",
  "content": {
    "body": "ok",
    "m.relates_to": {
      "rel_type": "m.thread",
      "event_id": "$GKhFi7r_7bFx4pWUPfPox8nbCM27aqRkFHwK0PG-Avw"
    }
  }
}
```

## Alternative

There has been some discussion about whether we should restrict the
room to a specific type of content (i.e. the type of the room define
the UI and how the content should be treated). Here is some consideration about the alternative proposal.

### Advantage of this approach 

* flexibility

If one day we use another client which could display video only
feed, then we could reuse this room and start posting other events
type to this room.

It will help as we have all our followers in the same room.

### Disadvantages of this approach

#### Complexity / room size

This approach comes with a higher complexity.

* filter algorithm more complex because we need to take into account
the multiple events type.
* higher room size (the ratio event displayed / event in the room will
be higher). May lead to slower client.

We need to take into account that there might be content which just
can't be displayed by the social media app that we are using.

The app should warn the user about this.

// TODO : See how the room size impact the time to join.
The discussion may need to take into account the time it takes to join one large room
with many states vs many small ones. (Is it preferable to have many small rooms
that are auto joined or one big room with multiple 'feeds' (different event types)
in it.)

#### Moderation

* if we let the user post content in a room it may be more complex
to moderate the room as the user could write event using an event
type that we don't use. Means longer time before removing those events.


## Privacy

The permissions of the rooms should be easily editable by the user.

Special attention should be accorded to those events,

```
m.room.join_rules
m.room.encryption
m.room.power_levels
```

* It must be clear to the user if the actual room is private or not.
* It must be clear to the user if the actual room is end-to-end encrypted.
* The user should be able to restrict the users able to write in his room.
* The user should be that all the followers can see each others.



## Unstable prefix

The following mapping will be used for identifiers in this MSC during development:


| Proposed final identifier | Purpose                 | Development identifier                |
| ------------------------- | ----------------------- | ------------------------------------- |
| `m.social.profile`        | Profile room            | `org.matrix.msc3639.social.profile`   |
| `m.social.group`          | Group room              | `org.matrix.msc3639.social.group`     |
| `m.social.post`           | Post event              | `org.matrix.msc3639.social.post`      |
| `m.social.comment`        | Comment on a post event | `org.matrix.msc3639.social.comment`   |
| `m.social.image-ref`      | Link to an image event  | `org.matrix.msc3639.social.image-ref` |



## Further idea

### Image post

An earlier version of the proposal allowed to define custom events for 

### Alternative proposal

Instead of filtering the room events according to their types,
we could filter the room directly according to his type.
Thus defining how the room UI.

We could define

* m.social.feed : for regular social media
* m.social.image : for image social media

This solution solve the main disadvantages of the previous solution
but lacks the flexibility.


### Idea: Tagging

*NB:* This is only an idea

We could add a `tags` entry in the event content. The content of those
tags could be 'hashtags'.

This will be useful for art social media. But we could also see an
implementation in regular social media like to tag other person.

```json
{
  "m.social.post": [/* the post content */],
  "m.social.tag": [
    "@mxid",
    "my chair"
  ]
}
```
### Unstable prefix

| Proposed final identifier | Purpose                                                          | Development identifier            |
| ------------------------- | ---------------------------------------------------------------- | --------------------------------- |
| `m.social.image`          | Image event (deprecated, could be restored in a further version) | `org.matrix.msc3639.social.image` |
| `m.social.tags`           | Tags property of `m.social.post` or `m.social.image` event       | `org.matrix.msc3639.social.tag`   |


