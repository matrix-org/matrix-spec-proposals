# MSC3639: Matrix for the social media use case

Matrix is currently mainly used for chats, however, recent projects
have shown that it is possible to use it for social media.

This proposal is to formally specify this usage and ensure
a compatibility between the different projects.

## The idea

This MSC tries to cover those following social media cases:

* **'Regular'** social media (Twitter style, Facebook : Circles, MinesTRIX)
* **'Art'** social media (Matrix Art)

## The proposal


To cover those use case, we will separate our proposal in two part.

* the room types: the container which will store the events
* special events types: dedicated to the social media use cased
which will be filtered depending on the client type/UI.
(displaying a feed or a grid of pictures...).

It is up to the client to filter the room event's and display only
the one which are relevant on the client purpose.

### Room

We propose two room types.

* m.social.feed
* m.social.group

Those two rooms will act as a container for events of different
types, which will be displayed only on a specific client.

The type is used to set the general purpose of the room.

#### Social media : 'Regular' or 'feed'

```
m.social.feed
```

**Usage:**

Used by a user to share content with his friends or the world.

* Owned by a single user
* Writing in this room could be owner only or any member. Up to the user.
* Room visibility : public / private. Up to the user.
* A user could have multiple of them

Small note about encryption:

Clients should notify the user that encryption shouldn't be enabled on 'big room'. (1)
On a side note, end-to-end encrypted rooms with a very large number of 'followers'
don't make a lot of change. 

TODO (1) : Define what large room means and what is the recommended maximum number of
participants in a E2EE room.

**UI considerations :**

* Should make clear that this room is owned by a specific user.
* UI type is up to the client (feed, pictures waterfall ...)

#### Social media : Groups

```
m.social.group
```

**Usage:**

* For group discussion

Group is just a regular profile room `m.social.feed` but with a
slightly different UI as there is no single owner of the room.


### Room content

Require

* [MSC1767 - Extensible event types & fallback in Matrix (v2)](https://github.com/matrix-org/matrix-doc/pull/1767)

We propose two events type to categorize the content of the event.

**Why ?**

As the room is displayed alongside the user' regular chats rooms we need
to make it clear to the user that it's a specific room.
Thus, we need to avoid that a user end up "spamming" his room thinking
the room is a regular chat room.

The solution is to separate the regular messaging from the social 
media posts. Thus, defining special events different from the regular
messaging events.

It will still be possible to send room message. But those should not
be displayed on the user wall / in the group.

**Types:**

* m.social.post
* m.social.pictures

**Why defining a specific m.social.pictures event ?**

When sending events, we want to be sure that the other users will
be able to see our posts. Thus, it might be problematic with image
only social media if we send a post with only text and then want to
display it in a image only social media or is not able to render
a fraction of the post (like a post with text, video, image).
This becomes problematic when the user start making reference
to previously sent post.

> We define separate types to make sure the app displaying them
is able to support all the content of this specific event type and
make sure image only and regular feeds don't mix.

See the later point for regular room message fallback. 

#### Base event

The structure of the event should just be extensible events.

#### Social: Post
```
m.social.post
```

A type for general content.

Could be text, pictures, video ...

**TODO:**

Define what base events the clients supporting those events
should be able to display.

like:

* m.text
* m.image
* m.video
* m.file

**Example:**
```json
{
  "type": "m.social.post", 
  "content": {
    "msgtype": "m.text",
    "body": "<h1>The awesome story</h1><p>A long time ago in a galaxy far, far away...</p><a href='...'>Read full post</a>",
    "m.social.post": [
      {
        "msgtype": "m.text",
        "body": "The first part of full text of story, located before image.",
      },
      {
        "msgtype": "m.image",
        "url": "mxc://example.com/KUAQOesGECkQTgdtedkftISg",
        "body": "Image 1.jpg",
        "info": {
          "mimetype": "image/jpg",
          "size": 1153501,
          "w": 963,
          "h": 734,
        }
      },
      {
        "msgtype": "m.text",
        "body": "The ending text of full story after image.",
      }
    ]
  }
}
```

Using an array for `m.social.post` will help define the order in which
content should be displayed.

#### Social: Image

Base : [MSC3552 - Extensible Events - Images and Stickers](https://github.com/matrix-org/matrix-doc/blob/travis/msc/extev/images/proposals/3552-extensible-events-images.md)

```
m.social.image
```

Events adapted to client like Matrix Art to build pictures only
social media.

UI could be a grid or a list view of pictures.

**Required content:**

The list of arguments that should be part of event["content"]

// TODO

like :

* m.image

**Example:**

```json
{
  "type": "m.social.image",
  "content": {
    "m.social.image": [
      "m.caption": [
          {
              "m.text": "Tramline in Berlin"
          },
          {
              "body": "Tramline in Berlin",
              "mimetype": "text/html"
          }
      ],
      "m.file": {
          "mimetype": "image/jpeg",
          "name": "_MG_0641.jpg",
          "size": 10158773,
          "url": "mxc://"
      },
      "m.image": {
        "height": 3456,
        "width": 5184
      },
      "m.text": "Tramline Berlin",
      "m.thumbnail": [
        {
            "height": 533,
            "mimetype": "image/jpeg",
            "size": 215496,
            "url": "mxc://nordgedanken.dev/",
            "width": 800
        }
      ],
    ]
  },   
}
```

#### Linking posts/pictures to the regular chat

One may want to advertise the room that he posted a specific content
(only visible in a social media client) that may be of interest to user
and provide a link to it.

This should be up to the user. The client could display a 'advertise in the chat room' button.

A [solution adapted from the one proposed by @MurzNN](https://github.com/matrix-org/matrix-doc/pull/1767#issuecomment-787431678)
is to define events like this one

```json
{
  "type": "m.room.message", // will be m.text in the future. According to extensible events
  "content": {
    "msgtype": "m.text",
    "body": "<h1>The awesome story</h1><p>A long time ago in a galaxy far, far away...
      </p><a href='...'>Read the full post in your favorite social matrix client</a>",
    "m.social.post": [
      {
        "msgtype": "m.text",
        "body": "The first part of full text of story, located before image.",
      },
      {
        "msgtype": "m.image",
        "url": "mxc://example.com/KUAQOesGECkQTgdtedkftISg",
        "body": "Image 1.jpg",
        "info": {
          "mimetype": "image/jpg",
          "size": 1153501,
          "w": 963,
          "h": 734,
        }
      },
      {
        "msgtype": "m.text",
        "body": "The ending text of full story after image.",
      }
    ]
  }
}
```

On a regular chat client like element, it should render as a simple link.

Another solution is to just send two events, one m.post.post or m.social.image
and a summary in the form of a room message.

##### Todo

Some client may not be web pages, thus a `href=""` may not make sense.
A text fall back, `Open in xxx to see the whole post` could make sense.

### Reactions

* Emoji reaction will use the regular event.
* However, post comment will be threads.

For rooms where only the user can write, it could be interesting to
allow other users to have a comment only permission.
See [MSC3394 -  new auth rule that only allows someone to post a message in relation to another message](https://github.com/frandavid100/matrix-doc/blob/threaded-replies/proposals/3394-new-auth-rule-that-only-allows-someone-to-post-a-message-in-relation-to-another-message.md)
for such a proposal.

### Tagging

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

## Alternative

There has been some discussion about whether we should restrict the
room to a specific type of content (i.e. the type of the room define
the UI and how the content should be treated). Here is some consideration about the alternative proposal.

### Advantage of this approach (the main one)

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

### Alternative proposal

Instead of filtering the room events according to their types,
we could filter the room directly according to his type.
Thus defining how the room UI.

We could define

* m.social.feed : for regular social media
* m.social.image : for image social media

This solution solve the main disadvantages of the previous solution
but lacks the flexibility.

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


Proposed final identifier | Purpose | Development identifier
------------------------------- | ------- | ----
`m.social.feed` | 'wall' room | `org.matrix.msc3639.social.feed`
`m.social.group` | group room | `org.matrix.msc3639.social.group`
`m.social.post` | post event | `org.matrix.msc3639.social.post`
`m.social.image` | image event | `org.matrix.msc3639.social.image`
`m.social.tags` | tags property of `m.social.post` or `m.social.image` event | `org.matrix.msc3639.social.tag`
