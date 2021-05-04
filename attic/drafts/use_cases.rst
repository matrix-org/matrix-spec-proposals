General UI/UX requirements:
===========================
- Live updates
- No flicker:
   * Sending message (local echo)
   * Receiving images (encoding w/h)
   * Scrollback
   * Resolving display names (from user ID)
- Fast startup times
- Fast "opening room" times (esp. when clicking through from a notification)
- Low latency file transfer.

Use cases
---------
- #1: Lightweight IM client (no perm storage) - e.g. Web client
- #2: Bug tracking software
- #3: Forum
- #4: Google + style communities
- #5: Email style threading
- #6: Multi-column threaded IM
- #7: Mobile IM client (perm storage)
- #8: MIDI client
- #9: Animatrix client
- #10: Unity object trees
- #11: Social Network ("Walls", PMs, groups)
- #12: Minecraft-clone
- #13: Global 'Like' widget, which links through to a room.


#1 Web client UI
================

Model::

 Rooms ----< Messages 
 - name     - type (call/image)
 - topic    

Home Screen
 What's visible:
  - Recent chats ordered by timestamp of latest event (with # users)
  - Your own display name, user ID and avatar url
  - A searchable list of public rooms (with # users and alias + room name + room topic)
 What you can do:
  - Create a room (public/private, with alias)
  - Join a room from alias
  - Message a user (with user ID)
  - Leave a recent room
  - Open a room
  - Open a chat history link.
  - Search for a public room.

Chat Screen
 What's visible:
  - Enough scrollback to fill a "screen full" of content.
  - Each message: timestamp, user ID, display name at the time the message was
    sent, avatar URL at the time the message was sent, whether it was a bing message
    or not.
  - User list: for each user: presence, current avatar url in the room, current
    display name in the room, power level, ordered by when they were last speaking.
  - Recents list: (same as Home Screen)
  - Room name
  - Room topic
  - Typing notifications
  - Desktop/Push Notifications for messages
 What you can do:
  - Invite a user
  - Kick a user
  - Ban/Unban a user
  - Leave the room
  - Send a message (image/text/emote)
  - Change someone's power level
  - Change your own display name
  - Accept an incoming call
  - Make an outgoing call
  - Get older messages by scrolling up (scrollback)
  - Redact a message
  - Resend a message which was not sent
 Message sending:
  - Immediate local echo
  - Queue up messages which haven't been sent yet
  - Reordering local echo to where it actually happened
 VoIP:
  - One entry in your display for a call (which may contain duration, type, status)
  - Glare resolution
 Scrollback:
  - Display in reverse chronological order by the originating server's timestamp
  - Terminates at the start of the room (which then makes it impossible to request
    more scrollback)
 Local storage:
  - Driven by desire for fast startup times and minimal network traffic
  - Display messages from storage and from the network without any gaps in messages.
  - Persist scrollback if possible: Scrollback from storage first then from the 
    network.
 Notifications:
  - Receive notifications for rooms you're interested in (explicitly or from a default)
  - Maybe per device.
  - Maybe depending on presence (e.g. idle)
  - Maybe depending on message volume
  - Maybe depending on room config options.
 Message contents:
  - images
  - video
  - rich text
  - audio
  - arbitrary files
  - location
  - vcards (potentially)

Chat History Screen
 What's visible:
  - The linked message and enough scrollback to fill a "screen full" of content.
  - Each message: timestamp, user ID, display name at the time the message was
    sent, avatar URL at the time the message was sent, whether it was a bing message
    or not.
  - The historical user list. *TODO: Is this taken at the linked message, or at
    wherever the user has scrolled to?*
 What you can do:
  - Get older messages by scrolling up (scrollback)
  - Get newer messages by scrolling down

Public Room Search Screen
 What's visible:
  - The current search text.
  - The homeserver being searched (defaults to the HS the client is connected to).
  - The results of the current search with enough results to fill the screen
    with # users and alias + room name + room topic.
 What you can do:
  - Change what you are searching for.
  - Change the server that's being searched.
  - Scroll down to get more search results.

User screen
 What's visible:
  - Display name
  - Avatar
  - User ID
 What you can do:
  - Start a chat with the user


#2 Bug tracking UI
==================

Model::

 Projects ----< Issues ---< Comments
 - key        - summary     - user
 - name       - ID          - message
  SYN         SYN-52       Fix it nooow!

Landing page
 What's visible:
  - Issues assigned to me
  - Issues I'm watching
  - Recent activity on other issues (not refined to me)
  - List of projects
 What you can do:
  - View an issue
  - Create an issue
  - Sort issues
  - View a user
  - View a project
  - Search for issues (by name, time, priority, description contents, reporter, etc...)

Issue page
 What's visible:
  - Summary of issue
  - Issue key
  - Project affected
  - Description
  - Comments
  - Priority, labels, type, purpose, etc..
  - Reporter/assignee
  - Creation and last updated times
  - History of issue changes
 What you can do:
  - Comment on issue
  - Change issue info (labels, type, purpose, etc..)
  - Open/Close/Resolve the issue
  - Edit the issue
  - Watch/Unwatch the issue
 
 
#3 Forum UI
===========

Model::

 Forum ----< Boards ----< Threads ----< Messages
 - Matrix   - Dev        - HALP!        - please halp!

Main page
 What's visible:
  - Categories (containing boards)
  - Boards (with names and # posts and tagline and latest post)
 What you can do:
  - View a board
  - View the latest message on a board
 
Board page
 What's visible:
  - Threads (titles, OP, latest post date+author, # replies, # upvotes, whether 
    the OP contains an image or hyperlink (small icon on title))
  - Whether the thread is answered (with link to the answer)
  - Pagination for posts within a thread (1,2,3,4,5...10)
  - Pagination for threads within a board 
  - List of threads in chronological order
  - Stickied threads
 What you can do:
  - View a user
  - View a thread on a particular page
  - View the latest message on a thread
  - View older threads (pagination)
  - Search the board
 
Thread page
 What's visible:
  - Messages in chronological order
  - For each message: author, timestamp, # posts by author, avatar, registration
    date, status message, message contents, # views of message
 What you can do:
  - Upvote the message
  - Flag the message for a mod
  - Reply to the message
  - Subscribe to thread or message's RSS feed
  - Go to previous/next thread

 
#4 Google+ community
====================

Model::

 Community -----< Categories ----< Posts ---< Comments
 Kerbal SP       Mods, Help        Text        Text
                                 (no title!)

Communities page
 What's visible:
  - List of communities
  - For each community: # users, # posts, group pic, title
 What you can do:
  - Join a community
  - View a community
  
Community Page
 What's visible:
  - Title, pic
  - List of categories
  - List of members with avatars (+ total #)
  - Most recent posts with comments (most recent comment if >1)
 What you can do:
  - Join the group
  - Post a post (with voting and options)
  - Report abuse
  - View member
  - Expand comments
  - Infinite scrolling
  - Add a comment to a post
  - Share a post
  - +1 a post

#5 Email style threading
========================

Chat Screen
 What's visible:
  - Enough scrollback to fill a "screen full" of content.
  - Threads:

    - Initially will only display the timestamp and user ID of the *first*
      message. But can expand to show the entire tree.
    - Tree of messages indicating which message is a reply to which.
    - Ordered by the arbitrary field (timestamp of oldest message in thread;
      newest message in thread; sender id; sender display name; etc)
    - Each message: timestamp, user ID, display name at the time of the message
  - Room name
  - Room topic
  - Typing notifications
  - Desktop/Push Notifications for messages
 What you can do:
  - Send a message in reply to another message:

    - Immediate local echo, may cause messages to re-order
    - Messages that haven't reached the server are queued.
    - Thread is displayed where it should be in the thread order once the
      message is sent.
  - Start a new thread by sending a message.

#6 Multi-threaded IM
====================

Chat Screen
 What's visible:
  - A multi-column grid of threads from a number of chatrooms
    Each concurrent thread is displayed in a different column.
    The columns start and end as threads split and rejoin the main conversation
    The messages for each thread are ordered by how recent they are::

      Room #1        Room # 2           Room # 2
      +------------+ +----------------+ Side thread.
      | * Message1 | | * Root         | +--------------+
      | * Message2 | | * A1 -> Root   | | * B1 -> Root |
      +------------+ | * A2 -> A1     | | * B2 -> B1   |
                     | * M -> A2, B2  | +--------------+
                     +----------------+

  - Typing notifications. Displayed within the correct thread/column.

 What you can do:
   - Send a message into a particular thread/column.
   - Move an *existing* message into a new thread creating a new column
   - Move an existing message into an existing thread, causing the threads to
     reconverge (i.e. provide a route from the sidebar back into the existing
     thread).  This does not imply terminating the thread, which can continue
     independently of the merge.
