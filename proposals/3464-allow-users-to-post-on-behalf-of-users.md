# MSC3464: Allow Users to Post on Behalf of Other Users

Often, bots (and sometimes other types of users) may wish to post on behalf of
another user. This proposal adds the ability to specify the user that a message
is being posted on behalf of, and provides controls for users to set who is
allowed to post on their behalf.

Some bot designs are based around a single bot user posting on behalf of
multiple other users. For example,
[standupbot](https://git.sr.ht/~sumner/standupbot) posts standup posts into the
standup room on behalf of the user who composed the standup post. Ideally, the
message would appear as if it came from the user who composed the standup post,
rather than from the standupbot since the standupbot is just an intermediary.

Additionally, other bots may want to perform actions based on the user that the
bot is posting on behalf of. For example,
[linear-maubot](https://gitlab.com/beeper/linear-maubot) only responds with
issue details if the user who posted the message is logged in to Linear. If the
standupbot posts on behalf of a user, the Linear bot may want to use that user
to authenticate to Linear.

## Proposal

This proposal adds an optional `m.on_behalf_of` field to the `m.room.message`
content, and creates a new `m.allows_on_behalf_of` state event which determines
on a per-user basis whether or not the `m.on_behalf_of` field should be
respected by clients.

### `m.on_behalf_of` field in `m.room.message`

This proposal adds an optional field to the `content` of `m.room.message`
events: `m.on_behalf_of`. If specified, the `m.on_behalf_of` field MUST be a
string containing the MXID of the user that the message is being posted on
behalf of.

For example, if `@bob:example.com` wanted to post on behalf of
`@alice:example.com`:

```
{
  "type": "m.room.message",
  "sender": "@bob:example.com",
  "content": {
    "msgtype": "m.text",
    "body": "I am posting on behalf of Alice",
    "m.on_behalf_of": "@alice:example.com"
  }
}
```

### `m.allows_on_behalf_of` state event

Users can configure which users are allowed to post on their behalf using the
`m.allows_on_behalf_of` state event.

The state event's state key MUST be the MXID of the user who is allowing/denying
other users to post on their behalf.

The content of the state event MUST have two fields (`allow` and `deny`; both
lists MUST be a list of MXIDs) indicating which MXIDs are allowed or denied the
ability to be rendered as posting on the users behalf.

For example, if `@alice:example.com` wants to allow `@bob:example.com` to post
on her behalf, but deny `@evil:impersonate.er` the ability to do so, she would
send the following state event:
```
{
  "type": "m.allows_on_behalf_of",
  "state_key": "@alice:example.com",
  "sender": "@alice:example.com",
  "content": {
    "allow": [
      "@bob:example.com"
    ],
    "deny": [
      "@evil:impersonate.er"
    ]
  }
}
```

### Client Behaviour

This proposal is backwards compatible. If a client does not support the
`m.on_behalf_of` field, then nothing will change about the presentation of the
event or any other client behaviour.

If a client does not support `m.on_behalf_of` at all, then none of the following
applies. However, if the client supports `m.on_behalf_of` in any capacity, then
all of the following applies.

#### Prompting users to allow/deny other users to post on their behalf

When a user (Bob) sends a message on behalf of another user (Alice), and there
is no entry for Bob in Alice's allow/deny lists, then the client MUST prompt
Alice to confirm whether she wants Bob to be able to post on her behalf in the
room.

A confirmation MUST add Bob's MXID to the `allow` list of Alice's
`m.allows_on_behalf_of` state event. Similarly, rejecting MUST add Bob's MXID to
the `deny` list of Alice's `m.allows_on_behalf_of` state event so that she does
not get prompted again. Dismissing the prompt MUST not change the
`m.allows_on_behalf_of` state event.

#### Per-member controls

Clients MUST provide a way for a user to move an MXID from the `allow` list to
the `deny` list and vice versa.

Outside of the prompt described above, clients do not have to provide a way for
a user to add an MXID to the `allow` or `deny` list if it was not already in one
of those lists.

#### Timeline display

If the message content does not have an `m.on_behalf_of` field, then clients
MUST display the message as if it came from the sender.

If the message content has an `m.on_behalf_of` field, but the user listed in
that field is not in the room, then clients MUST display the message as if it
came from the sender.

If the message content has an `m.on_behalf_of` field and the message sender is
in in neither the `allow` nor the `deny` list for the user listed in
`m.on_behalf_of`, then clients MUST display the message as if it came from the
sender.

If the message content has an `m.on_behalf_of` field and the message sender is
in the `deny` list for the user listed in `m.on_behalf_of`, then clients MUST
display the message as if it came from the sender.

If the message content has an `m.on_behalf_of` field and the message sender is
in the `allow` list for the user listed in `m.on_behalf_of`, then

* Clients MUST render the message as if the user in the `m.on_behalf_of` field
  sent it.
* Clients MUST render an indicator of the user who actually sent the message.
* Some clients don't render a header indicating who the message is from on every
  message so as not to clutter the timeline. These clients MUST take into
  account changes in the `m.on_behalf_of` user when calculating whether the
  message requires a header.

For example, if the standupbot is posting on behalf of Sumner Evans, the
client could render the message header like:

```
Sumner Evans via standupbot
```

## Potential issues

## Alternatives

### Per-room `m.allows_on_behalf_of` state event

The `m.allows_on_behalf_of` setting could be a per-room setting (not per-user),
but this puts too much power in the hands of room admins.

### Change the Bot's Name and Avatar Manually

In the situation of standupbot, it could manually change its avatar and display
name to the avatar of the person who it is posting on behalf of by sending a new
`m.room.member` state event.

This approach has a few problems:

* Clients may end up showing a large number of "user changed their avatar"
  messages.
* Some clients show all messages from a user with the latest avatar, rather than
  with the avatar at the time the message was sent, meaning that message display
  would be highly client-dependent.
* Clients cannot show that the bot was posting on behalf another user.

### Allow Changing the Display Name and Avatar Per-Message

Similar to the above alternative, this would allow users to change their avatar
on each message. This runs into the same issues as mentioned above, except for
the "user changed their display name/avatar" events would not be necessary and
wouldn't show up on the timeline.

## Security considerations

None

## Unstable prefix

While this MSC is unstable `space.nevarro.msc3464.` should be used as a prefix
instead of `m.` So `m.on_behalf_of` would become
`space.nevarro.msc3464.on_behalf_of`.
