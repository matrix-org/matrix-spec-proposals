# MSC3015: Room personal name

Very often users want to personally rename rooms to see it in list like they wants, especially for DM rooms. But room
name is shared thing, so if they rename it for yourself, all other members will see this rename too. 

Examples of problem: 

1. Very often other people want to rename DM rooms with me and can do this, because we both are admins. So they set the
   alternative name of that DM room (eg `Korepov Alexey` instead of `Alexey Murz Korepov`) - this works well on their
   side. But, as result on my side, I see that room in my rooms list with my name, instead of remote user name.

2. The user have two DM rooms with different Matrix users, but both have name "Alice" without avatar. As result he see
   two identical rooms in list with same name and can understand which Alice is where only via reading recent messages.
   And he can solve this problem via renaming rooms, that give the result from item 1, descibed above.

3. This problem often happens for rooms from bridged networks, when we talk with same person via different networks, and
   want to mark each room personally. This can be solved via adding suffixes with remote network name to room name on
   Bridge side, but people want to change other parts of room name too. For example, one person can have different names
   in each network (eg "Alexey Korepov" on VK, "Korepov Alexey" on Skype, "Alex" on WhatsApp, "Murz" on Telegram), and I
   want to see all rooms with him as similar names.

Most of other modern messengers (Telegram, Skype, Viber, WhatsApp) already have this feature, but only for DM rooms via
reusing smartphone's addressbook to store personal names of contacts. And moving from that messengers to Matrix confuses
the people, because they can't rename personal chats in his own list like before.

# Proposal

For solve this problem I propose to use [room's
account_data](https://matrix.org/docs/spec/client_server/r0.6.0#put-matrix-client-r0-user-userid-rooms-roomid-account-data-type)
item with key `m.room_name_personal` to store custom name of any room for each user individually, with filling personal
name in content with `room_name_personal` type:

```json
{
  "room_name_personal": "Alice Liddell"
}
```

By default this item is absent. It is added only when user make the personal renaming of room, and cleared if user
remove the personal name for room (or make it empty).

Regarding to spec, the account data's key can't be deleted, so if user wants to clean the personal name or "Reset to
default", the value of the `m.room_name_personal` key should become empty (`{}`).

# Client support

## Displaying:

When client displays the room in list, it should lookup the `m.room_name_personal` key, if it exists and have not empty
value - use it's value for display name in room list instead of global room name. In room page header (over timeline)
clients may show both names (global and personal) with explaining that this room have alternative personal name, that is
seen only for current user.

## Adding, removing, renaming:

Clients should provide the way to privately rename room and clearly explain the difference between global room name and
personal name.

In room list this can be implemented via "Rename room personally" or "Set personal name for room" menu item in
right-click menu.

In room settings page personal name can be implemented via button "Set personal name for this room", which will be
available even if user have no permission to change the room name. If room personal name is filled, it should be shown
near the global room name, with ability to remove it.

# Server support

This MSC does not need any changes on server side.

# Potential issues

1. Users can set personal name for room identical as global name of room - this will give little negative effect: all
   further global room name changes will not change room name in client list. This can be solved via clearly describe
   the difference between global room name and personal name, and some warning that those names are identical with
   ability to remove personal name.

# Alternatives

1. Instead of setting personal name for rooms via [room's
   account_data](https://matrix.org/docs/spec/client_server/r0.6.0#put-matrix-client-r0-user-userid-rooms-roomid-account-data-type)
   we can set personal names directly for Matrix users (mxid), like other messengers (Telegram, WhatsApp, etc) doing.
   This will give similar behavior for DM rooms, but will make impossible to set personal names of rooms with several
   users (or DM rooms with bots), and intersects with per-room display names feature. And this way will be better to
   implement together with "[Contacts](https://github.com/vector-im/roadmap/issues/10)" feature, which is planned in
   Element, also her is issue about this: [Contact List & Renaming
   Contacts](https://github.com/matrix-org/matrix-doc/issues/2936).

2. This feature can be extended via storing personal avatar for room to, but, as I think, for multi-user rooms this is
   unnecessary, and for DM rooms will be better to implement personal avatars together with "Contacts" feature,
   mentioned above, instead of use the room's account data for this.

# Unstable prefix

Clients should use `org.matrix.msc3015.room_name_personal` for room account data key instead of proposed, while this MSC
has not been included in a spec release.
