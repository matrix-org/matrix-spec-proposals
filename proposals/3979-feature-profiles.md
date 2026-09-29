# MSC3979: Revised feature profiles

The spec currently has a "[Feature
Profiles](https://spec.matrix.org/v1.6/client-server-api/#feature-profiles)"
section, which indicates what functionality clients should implement.
Unfortunately, this section has several deficiencies:

- the section focuses on the platform or type of UI, rather than the type of
  client.  For example, a Matrix client that is web-based could be a
  full-featured chat app (e.g. Element Web or Fluffy Chat); a client focused on
  making group calls (e.g. Element Calls), which may not need instant messaging
  features; or a commenting, forum, or social media system (e.g. Cactus
  Comments, MinesTRIX, ~matrix-social~ somix, etc.), which may not need certain
  features such as VoIP or Direct Messaging.
- it only gives a binary "Required" or "Optional", but some features are likely
  to be more useful for some types of clients than for others.  For example,
  "Event Context" is currently marked as "Optional" for all client types.  But
  it is likely to be quite useful in an Instant Messaging-type client, to allow
  the user to navigate history, while it is unlikely to be useful in an
  embedded situation, where clients generally just send messages or read the
  latest message.

## Proposal

We propose replacing the current profiles with new profiles that are based on
the type of functionality that a client is focused on.  A client can implement
multiple profiles, or no profile; the set of profiles is not meant to be
exhaustive, so clients there may be clients that do not fit into any of the
profiles.  The profiles will indicate whether a module is required (the module
must be implemented), recommended (the module should be implemented), or
suggested (the module may be relevant to the client type and may enhance user
experience, but many clients can get by without implementing them); if a module
is not mentioned, it is likely that it is not relevant for the profile.  (FIXME:
define what the levels mean.)  Profiles can have sub-profiles for clients that
want to provide a more focused interface

Below are the initial profiles.  Additional profiles can be added in the
future.

Changes to the recommendation levels of modules, including setting the initial
requirement level for new modules, is up to the discretion of the Spec Core
Team; this is to avoid adding unnecessary overhead in the spec process.
However the Spec Core Team is expected to consider feedback from client authors
when determining the recommendation levels.

### Chat

The chat profile is for communication that is primarily textual in nature, but
can sometimes include other features such as media.

There are sub-profiles for clients that are focused on one-on-one chats, or on
group chats.

Required modules:

- Instant Messaging (there are many events defined in this module, some of
  which may not be applicable to all clients.  Can we say that only part of the
  "Instant Messaging" profile is required?)
- Direct Messaging (required for the chat profile, recommended for both
  sub-profiles -- clients that are focused on one-on-one chats or on group
  chats will likely want to distinguish between Direct Messaging rooms and
  non-Direct Messaging rooms so that they can hide the rooms that are not
  of the type that the client is focused on, or to present them differently)
- Mentions
- Push Notifications
- Receipts
- Typing Notifications
- Ignoring Users
- Room Upgrades
- Client Config (currently marked as "Optional", but the "Direct Messaging"
  module uses it, so it probably should be "Required")

Recommended modules:

- Rich Replies
- Presence (currently marked as "Required", but in practice, several large
  servers have presence disabled, so many users cannot make use of this
  anyways)
- Fully Read Markers
- Reporting Content (only "Suggested" for the one-on-one chat sub-profile)
- Content Repository (currently marked as "Required" for most client types)
- Managing History Visibility (currently marked as "Required" for most client
  types, but it requires that clients provide a way for users to set the
  history visibility settings, which is only applicable to room admins.)
- Server Side Search
- Event Context
- Third Party Networks
- Send-to-Device Messaging (needed for End-to-end Encryption)
- Device Management (needed for End-to-end Encryption)
- End-to-end Encryption (may not be applicable to clients focused on public chats)
- Secrets (currently missing from the table; may not be applicable to clients
  focused on public group chats)
- Room Previews (not applicable to the one-on-one chat sub-profile)
- SSO Login
- Server Notices
- Event Replacements
- Threading (only "Suggested" for the one-on-one chat sub-profile)
- Third Party Invites (currently missing from the table)
- Room Tagging

Suggested modules:
- Guest Accounts (only for clients that implement group chats -- not as useful
  for the one-on-one chat sub-profile)
- Stickers
- Server ACLs (only for clients that implement group chats -- not as useful for
  the one-on-one chat sub-profile)
- Spaces

Additional notes
- VoIP is currently marked as "Required" for most client types.  Instead, we
  will create a new "VoIP" profile.  Clients that want to provide both Chat and
  VoIP features can implement both profiles.

### Voice/video calls

The voice/video calls profile is for real-time communication over voice and/or
video channels.  Currently the spec only supports one-to-one calls, but
eventually there should be one-to-one and [group
call](https://github.com/matrix-org/matrix-spec-proposals/pull/3401)
sub-profiles, similar to the chat profile.  Adding group call support will make
more modules relevant, such as Ignoring Users.

Required modules:

- VoIP
- Room Upgrades

Recommended modules:

- Direct Messaging
- Send-to-device Messaging
- End-to-end Encryption
- Secrets
- Client Config

Suggested modules:

- SSO Login
- Device Management

### Chat-based bots

The chat-based bots profile is for bots that interact with humans over a chat
interface.  Due to the variety of tasks that bots can perform, bots will likely
need to implement more modules than the ones listed; this profile merely tries
to provide the modules that are likely to be useful to most bots.

Required modules:

- Instant Messaging
- Room Upgrades (bots should join upgraded versions of rooms)

Recommended modules:

- Send-to-Device Messaging
- End-to-end Encryption
- Event Replacements (bots that respond to messages should detect edits and
  avoid sending duplicate responses and/or amend their response)
- Threading (bots that respond to messages should put their responses in a
  thread, if the message that they are responding to is in a thread)

Suggested modules:

- Rich replies
- Mentions

### Embedded Devices

The embedded devices profile is for clients that run on embedded devices such
as a kettle, fridge or car.  These clients tend to perform a few operations and
run in a resource constrained environment.

Since these devices will often have limited interaction with Matrix rooms, and
may use custom events to communicate with other rooms, the modules are not
generally applicable to these types of clients, though some clients will
implement the modules that do apply to their situations.

Clients that are intended to interact with human over a chat interface should
implement the "Chat-based bots" profile.

Clients should implement the Send-to-device Messaging and End-to-end Encryption
modules whenever possible.  However, since the device may have limited
computing capabilities and encryption could be difficult for it to do, clients
can ensure confidentiality of sensitive data by only connecting to trusted
homeservers and only posting in rooms whose only members are on trusted
homeservers.

## Potential issues

Not all client types can be represented.

Opinions may differ between what should be considered "recommended" or
"suggested".

## Alternatives

There are probably a multitude of ways of changing this section.

## Security considerations

The "End-to-end Encryption" module (and associated modules) should be
encouraged as much as possible, except for in situations where the server is
trusted (for example, for client types where it is likely that the homeserver
is operated by the client operators), or where the room contents are intended
to be public (for example, public group chats).

## Unstable prefix

Since no new endpoints or event types are introduced, no unstable prefix is needed.

## Dependencies

None
