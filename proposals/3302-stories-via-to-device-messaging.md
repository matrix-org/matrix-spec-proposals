# MSC3302: Stories via To-Device-Messaging

Stories are a very common feature for messaging and social media apps. The
concept is simple:
- Users can post a short text, an image or a video.
- All posts of a given user which are not older than 24 hours (or whatever timeframe we set) are visible for all their friends in this app as their **story**.
- Posts in a story are normally displayed full screen and may disappear after they are seen.
- Posts are ephemeral, have a time to live -> this should motivate the user to share stuff with less pressure.

This feature is known by apps like:
- SnapChat
- Instagram
- WhatsApp
- Facebook
- Twitter (cancelled fleets feature)

The use cases are simple:
- User wants to add a post to their story.
- User wants to delete a single post from their story.
- User wants to display all stories from all contacts.
- User wants to make their story not visible for a single contact.
- User wants to hide the stories of a single contact.

This feature is just broadcasting content from `one` to `n` users and therefore
not really related to rooms. This approach uses To-Device-Messaging for this.


## Proposal

This feature doesn't need any server-side changes and can be implemented by any client.

### User wants to add a post to their story

First the client creates a list of all "contacts" or "friends". This is just the
list of all users, the user shares a DM-room with. A peek into the `m.direct` event
in account data can solve this. Once we have **Canonical DMs** we would need to
iterate through all of the users rooms.

Using the To-Device-Messaging we can send to all those contact at once with one
API-call:

#### PUT [/_matrix/client/r0/sendToDevice/m.stories.message/{txnid}](https://spec.matrix.org/unstable/client-server-api/#put_matrixclientr0sendtodeviceeventtypetxnid)
```json
{
  "messages": {
    "@alice:example.com": {
      "*": {
        "content": {
          "body": "This is an example story",
          "format": "org.matrix.custom.html",
          "formatted_body": "<b>This is an example story</b>",
          "msgtype": "m.text"
        },
        "story_id": "ABDH238sHSwl",
        "time_of_death": 1627715426640,
      }
    },
    "@charley:example.com": {
      "*": {
        "content": {
          "body": "This is an example story",
          "format": "org.matrix.custom.html",
          "formatted_body": "<b>This is an example story</b>",
          "msgtype": "m.text"
        },
        "story_id": "ABDH238sHSwl",
        "time_of_death": 1627715426640,
      }
    }
  }
}
```

For the content we can just reuse the same content like in `m.room.message` events.
This allows us to send all kind of stories (text, images, videos, audios) we like.

Clients can also set an optional `story_id` which should be unique. This can later
be used to send a delete request.

**Event Type**: `m.stories.message`

| Name | Type | Description |
| -------- | -------- | -------- |
| `content`     | `object`     | **Required**: The fields in this object will varydepending on the type of event.|
| `story_id` | `string` | Unique ID set by the client to be able to send a delete request.|
| `time_of_death` | `int` | **Required**: Timestamp when this post should be deleted by all clients.|


### User wants to delete a single post from their story
If the user has set a `story_id` they can send a delete request to their contacts:

#### PUT [/_matrix/client/r0/sendToDevice/m.stories.delete_request/{txnid}](https://spec.matrix.org/unstable/client-server-api/#put_matrixclientr0sendtodeviceeventtypetxnid)
```json
{
  "messages": {
    "@alice:example.com": {
      "*": {
        "story_id": "ABDH238sHSwl"
      }
    },
    "@charley:example.com": {
      "*": {
        "story_id": "ABDH238sHSwl"
      }
    }
  }
}
```
The list of contacts may be different now since the user has posted this story. A client
should therefore make sure that it sends the delete request to all users who received
the previous story.

Delete requests should be encrypted with OLM if possible! Clients should be able to
handle unencrypted delete requests as well.

Clients receiving a delete request should search for the post with the given `story_id`
in their local cache and delete it if it is found. If they can't find the story they
should just ignore the request.

**Event Type**: `m.stories.delete_request`

| Name | Type | Description |
| -------- | -------- | -------- |
| `story_id` | `string` | **Required**: Unique ID set by the client to be able to send
a delete request.|

### User wants to display all stories from all contacts.
Clients should be able to collect and persist all incoming stories. But clients should
also make sure that a story which is older than the `time_of_death` will get deleted.

### End-to-end encrypted stories
Using OLM all stories can be sent end-to-end encrypted! This should be the default for
sending but clients should display received unencrypted stories as well.

### User wants to make their story not visible for a single contact.
Sometimes you don't want your grandma seeing your story from the last party. For this the
user should store a blocklist of user IDs in **Account Data** which should be leaved out
when sending a new post to the story.

```json
{
    "type": "m.stories.blocklist",
    "content": {
        "users": ["@charley:example.com"]
    }
}
```

The absent of this **Account Data** event should be interpreted as an empty list.

**Event Type**: `m.stories.blocklist`

| Name | Type | Description |
| -------- | -------- | -------- |
| `users` | `[string]` | **Required**: List of users the client should not send stories to. |

### User wants to hide the stories of a single contact.
You may find the stories of a single user annoying or offensive but you still want to share a
DM room with this user. For this we need a ignore list. Stories per To-Device messages from
these users should just be thrown away.

```json
{
    "type": "m.stories.ignore",
    "content": {
        "users": ["@charley:example.com"]
    }
}
```

The absent of this **Account Data** event should be interpreted as an empty list.

**Event Type**: `m.stories.ignore`

| Name | Type | Description |
| -------- | -------- | -------- |
| `users` | `[string]` | **Required**: List of users the client should ignore. |


## Potential issues

- If you have around 100 contacts with a lot of devices, sending end-to-end encrypted stories can
- take a while. The client should display a nice progress bar here.
- A client can never be sure that all other clients will fulfill the delete request.
- Currently there is no moderation tool for stories. As they are end-to-end encrypted this is not
- possible at all.


## Alternatives

The timeline in [extensible profiles as rooms](https://github.com/matrix-org/matrix-doc/blob/matthew/msc1769/proposals/1769-extensible-profiles-as-rooms.md) may be able to solve this
too but it probably means that the user needs to join all profile rooms manually or needs to peek
in `N` rooms which could be a performance issue.


## Security considerations

The client should let the user know if it is able to encrypted stories.

## Unstable prefix

Until this MSC is merged, clients should use the prefix `im.fluffychat.stories.*` instead of
`m.stories.*`
