# MSC0000: New auth rule that only allows someone to post a message in relation to another message

Today, chat platforms are used broadly in order to broadcast information to large audiences. An example of this are [Telegram channels](https://telegram.org/tour/channels).

Matrix rooms can be used to a similar effect, if permissions are set so that regular users can't post any messages. Subscribers are fine with this most of the time, because they're usually more interested in reading new content by the room's owner than in replying to that content, or in reading what other subscribers have to say.

But some times they may want to give feedback, or read other people's opinions; and that can't be done today because, by definition, this kind of room prevents any type of conversation.  

## Proposal

I propose a new auth rule that only allows room members to post a message if it's in relation to another message.

This will mean that regular users can't post top-level messages, but they can start threads and reply to them; this will allow for conversation inside the room while keeping the room clean for subscribers who just want the news; because the main timeline will only contain posts by the room's owner, and all the conversations will take place within threads.

It may also be useful for additional purposes: for example [a client focused on social networking](https://matrix.org/blog/2020/12/18/introducing-cerulean) could use a room to store a user's posts, which could then be followed by other users; or [a matrix-based comment system](https://cactus.chat/) could show every post on a webpage in the same room, with all the discussions happening inside threads.

## Alternatives

It would also be possible to achieve the same result with threads-as-rooms; this would also allow for greater flexibility (e.g. allowing regular users to comment some posts, but not others) but it would also probably be more expensive.
