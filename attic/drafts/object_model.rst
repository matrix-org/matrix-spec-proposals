..TODO
  What are the start & end tokens doing here?!

::

 +---------------+
 | Room          |
 |   "Room-ID"   |
 |   {State}     |         +----------------------+
 |     Name------|-------->| Event m.room.name    |
 |     Topic     |         |   "Name"             |
 |     [Aliases] |         +----------------------+      +-------------+
 |     [Members]-|---+     +----------------------+ <----| Start Token |
 |   [Messages]  |   |     | Event m.room.member  |      +-------------+
 |     |   |     |   +---->|   "invite/join/ban"  |
 +---------------+         |   "User-ID"          |
       |   |               +----------------------+
       |   |               +----------------------+
       |   | Message       | Event m.room.message |
       |   +-------------->|   {content}          |<--+
       |                   +----------------------+   |
       | Comment           +----------------------+   |
       +------------------>| Event m.room.message |   |
                           |   {content}          |   |
                           |   "relates-to"-------|---+  +-------------+
                           +----------------------+ <----|  End Token  |
                                                         +-------------+
