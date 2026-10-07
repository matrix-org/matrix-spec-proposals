# MSC3394: new auth rule that only allows someone to post a message in relation to another message

Today, chat platforms are used broadly in order to broadcast information to large audiences.
An example of this are [Telegram channels](https://telegram.org/tour/channels/).

Matrix rooms can be used to a similar effect, if permissions are set so that regular
users can't post any messages. Subscribers are fine with this most of the time, because
they're usually more interested in reading new content by the room's owner than in
replying to that content, or in reading what other subscribers have to say.

But some times they may want to give feedback, or read other people's opinions; and that
can't be done today because, by definition, this kind of room prevents any type of conversation.

## Proposal

In the context of this proposal, and based on [MSC3440](https://github.com/matrix-org/matrix-doc/pull/3440),
a "message inside a thread" is defined as an `m.room.message` event containing an `m.relates_to` field
with a relation type of `m.thread` and a "top-level message" is defined as an `m.room.message` event
NOT containing such a field.

I propose a new auth rule that only allows room members to post a message if it is
in relation to another message.

This will mean that regular users can't post top-level messages, but they can start threads
and reply to them; this will allow for conversation inside the room while keeping the room
clean for subscribers who just want the news; because the main timeline will only contain
posts by the room's owner, and all the conversations will take place within threads.

It may also be useful for additional purposes: for example a [client focused on social networking](https://matrix.org/blog/2020/12/18/introducing-cerulean) could use a room
to store a user's posts, which could then be followed by other users; or a [matrix-based comment system](https://cactus.chat/) could show
every post on a webpage in the same room, with all the discussions happening inside threads.

Based on [existing auth rules](https://spec.matrix.org/latest/rooms/v7/#authorization-rules), the new auth rule I'm proposing
could probably look like this:

1. If type is m.room.message:
  1. If the user's power level is higher than the power level for m.room.message events, allow.
  2. Otherwise, check the new power level I want to introduce. If it is is higher than the user's power level, reject.
  3. Otherwise, if the event doesn't have a relation, reject.
  4. Otherwise, allow.

As an example, let's say I want to set up my room so that only moderators can post top-level messages,
but regular users can comment those messages inside a thread. I will set a power level of 50 for the
"send messages" permission, and a power level of 0 for the new "send messages to threads" permission.

When a user tries to send a message:

1. If they are a moderator (PL of 50) they are allowed.
2. Otherwise, if they are a regular user (PL of 0) and the message is inside a thread (it has a relation) they are allowed.
3. Otherwise, they're not allowed.

It is possible that the proposal above has errors of form, since I'm not familiar with auth rules. In that
case I would welcome suggestions on how to improve it.

## Alternatives

It would also be possible to achieve the same result with threads-as-rooms; this would
also allow for greater flexibility (e.g. allowing regular users to comment some posts,
but not others) but it would also probably be more expensive.
