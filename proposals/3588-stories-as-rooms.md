# MSC3588: Stories As Rooms

Stories are a feature mostly known from Instagram, WhatsApp, Facebook and SnapChat. They are a way to share text, images or videos with all of your friends at once while they have a limited lifetime of mostly 24 hours. In contrast to microblogging, stories are ephemeral and therefore users are motivated to speek freely.

We have some requirements for this feature here:

* Posts in a story should disappear after a certain lifetime
* The user should be able to configure who can see their story
* The user should be able to opt-out of receiving stories from specific users (without the need to fully ignore such users)
* Posts in a story should be end-to-end encrypted (and therefore not be public)
* Stories are **not** public. Users need to have some kind of relationship to see the each others stories

To have a channel where a user can broadcast messages to everyone who wants to follow them, it would be obvious to use the Profiles As Rooms feature. Unfortunately this doesn't seem to have much progress in the last months. Also Profiles As Rooms may be public rooms while we want to have private and encrypted rooms for this. So while Room Profiles may fit perfect for microblogging, we need another room for our stories.

The solution in this document works fully client side and requires no changes on the server. It is intended to be an optional feature for Matrix clients who would like to implement this feature, while it stays compatible with all other clients as well. Stories rooms will just be displayed as normal read-only rooms for them.


## Proposal

The solution in this document works fully client side and requires no changes on the server. It is intended to be an optional feature for Matrix clients who would like to implement this feature, while it stays compatible with all other clients as well. Stories rooms will just be displayed as normal read-only rooms for them.

### Stories Room

Before a user posts their first story, they need to create a story room. This room should be marked with a creation type of `msc3588.stories.stories-room`. The stories room should not be created before the user actually wants to post their first story.

The room should be private, encrypted and read only for all other users. While creating this room, the user should already invite all "contacts" they would like to share their story with. Apps should display a list of possible contacts to choose, which could be just a list of all users, the user shares a DM room with.

If a user has less than 30 DM rooms, it should be fine that the client just preselects all of them but the user must be informed that they is going to invite those 30 people to a new room and that these people will be able to see each other's MXID which might not be wanted. All contacts which should **not** be invited to the room, should be added to a block list in a private account data object.

#### Example of the /createRoom payload:

```json
{
  "creation_content": {
    "type": "msc3588.stories.stories-room"
  },
  "preset": "private_chat",
  "power_level_content_over": {
    "events_default": 100
  },
  "initial_state": [
    {
      "type": "m.room.encryption",
      "state_key": "",
      "content": {
        "algorithm": "m.megolm.v1.aes-sha2"
      }
    }
  ],
  "invite": [
    "@alice:example.com",
    "@bob:example.com"
  ]
}
```

#### Example of the block list account data object:

```json
{
  "type": "msc3588.stories.block-list",
  "content": {
    "users": [
      "@charley:example.com"
    ]
  }
}
```

Clients should display such rooms in a different manner. Every user should have only one stories room but can in theory have multiple of them. The user must never give admin permissions to another person and should be aware, that all users in this room in theory can see each other's MXID.

After creation, users might want to be able to invite or kick other users to their stories room. Clients should offer a UI for it. Every time the user posts a new story, the client should check if there are new contacts (users the user shares a DM room with and who are not on the block list). If there are, the UI should display another list view where the user can decide if they want to invite these contacts to the stories room **before** the new story is posted, or if they want to add some or all of the new contacts to the block list.

In this way, we make sure that every invitation to a new stories room actually contains at least one new post.

Invitations to a new story room could be displayed as a normal new story in the UI while there should be a way to decline such an invitation, for example with a long press context menu.

A post in a story room can then just be a normal `m.room.message` event of any message type, which then would be end-to-end encrypted.

## Potential issues

All posts in a story should disappear after 24 hours. In the future it might be easy to implement this using "Self destructive messages" <https://github.com/matrix-org/matrix-doc/pull/2228> but at the moment the only way we can do this, is to manage this on both sides:

* Sending clients should be configured to automatically redact all messages in stories rooms, which are older than 24 hours
* Receiving clients should ignore messages in stories rooms, which are older than 24 hours

Therefore, it **will** be possible that stories are visible after 24 hours if one or both parts are not following these rules. However, it will always be possible to capture screenshots or to copy contents before they get redacted, regardless of what we try to prevent this. The automatic disappearing of stories is **not** a privacy feature. It just assumes that stories, older than a specific amount of time, are no longer relevant to the users.


## Alternatives

Profiles as rooms can be used to post content to a wider audiance.


## Security considerations

The GUI should make clear who can see the stories and should inform the user that all subscribers can potentially see each others Matrix IDs.

## Unstable prefix

`msc3588.stories.stories-room`

`msc3588.stories.block-list`

## Dependencies

None.
