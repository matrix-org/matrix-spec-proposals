Data flows for use cases
========================

::

 <- Data from server to client
 -> Data from client to server

Instant Messaging
-----------------

Without storage
~~~~~~~~~~~~~~~

::

 Home screen
   Data required on load:
    <- For each room the user is joined: Name, topic, # members, last message, room ID, aliases
   Data required when new message arrives for a room:
    <- Room ID, message content, sender (user ID, display name, avatar url)
   Data required when someone invites you to a room:
    <- Room ID, sender (user ID, display name, avatar url), Room Name, Room Topic
   Data required when you leave a room on another device:
    <- Room ID
   Data required when you join a room on another device:
    <- Name, topic, # members, last message, room ID, aliases
   Data required when your profile info changes on another device:
    <- new profile info e.g. avatar, display name, etc.
    
   Creating a room
    -> Invitee list of user IDs, public/private, name of room, alias of room, topic of room
    <- Room ID
   
   Joining a room (and dumped into chat screen on success)
    -> Room ID / Room alias
    <- Room ID, Room aliases (plural), Name, topic, member list (f.e. member: user ID, 
       avatar, presence, display name, power level, whether they are typing), enough 
       messages to fill screen (and whether there are more)
      
 Chat Screen
   Data required when member name changes:
    <- new name, room ID, user ID, when in the context of the room did this occur
   Data required when the room name changes:
    <- new name, room ID, old room name?
   Invite a user:
    -> user ID, room ID
    <- display name / avatar of user invited (if known)
   Kick a user:
    -> user ID, room ID
    <- what message it came after
   Leave a room:
    -> room ID
    <- what message it came after
      
   Send a message
    -> Message content, room ID, message sequencing (eg sending my 1st, 2nd, 3rd msg)
    <- actual content sent (if server mods it), what message it comes after (to correctly
       display the local echo)
      
    Place a call (receive a call is just reverse)
     <- turn servers
     -> SDP offer
     -> Ice candidates (1 by 1; trickling)
     <- SDP answer
     <- Ice candidates
    
    Scrolling back (infinite scrolling)
     -> Identifier for the earliest message, # requested messages
     <- requested messages (f.e change in display name, what the old name was), whether
        there are more.


With storage
~~~~~~~~~~~~
::
    
  Home Screen
    On Load
     -> Identifier which tells the server the client's current state (which rooms it is aware
        of, which messages it has, what display names for users, etc..)
     <- A delta from the client's current state to the current state on the server (e.g. the
        new rooms, the *latest* message if different, the changed display names, the new 
        invites, etc). f.e Room: Whether the cache of the room that you have has been replaced 
        with this new state.
        
    Pre-load optimisation (not essential for this screen)
      -> Number of desired messages f.e room to cache
      <- f.e Room: the delta OR the entire state
     

Bug Tracking
------------
::

  Landing Page
    On Load
     <- Issues assigned to me, Issues I'm watching, Recent activity on other issues includes
        comments, list of projects
    
    Search for an issue (assume text)
     -> Search string
     <- List of paginated issues
       Request page 2:
        -> Page number requested
        <- Page of paginated issues
  
  Issue Page
    On Load
     -> Issue ID and Project ID (equiv to Room)
     <- Issue contents e.g. priority, resolution state, etc. All comments e.g. user ID, 
        comment text, timestamp. Entire issue history e.g. changes in priority
     
    Post a comment
     -> Issue ID, comment content, Project ID (equiv to Room)
     <- actual content sent (if modded), what comment it comes after
    
    Set issue priority
     -> Issue ID, Project ID, desired priority
     <- What action in the history it came after
     
    Someone else sets issue priority
     <- Issue ID, Project ID, new priority, where in the history


Mapping model use cases to matrix models (Room, Message, etc)
=============================================================

To think about:
 - Do we want to support the idea of forking off new rooms from existing ones? This
   and forums could benefit from it.

Bug tracking UI
---------------
::

 Projects => Rooms
 Issues => Message Events
 Comments => Message Events (relates_to key)

Projects:
 - Unlikely that there will be 100,000s of issues, so having to pull in all the issues for a project is okay.
 - Permissions are usually per project and this Just Works.
 - New issues come in automatically and Just Work.
 - Can have read-only members

Issues:
 - Don't really want 1 Room per Issue, else you can have thousands of Rooms PER PROJECT, hence choice for    
   Issues as Messages. Don't need to join a room for each issue.
 - Idea of issue owner is clear (sender of the message)
 - Updating issues requires an additional event similar to comments (with ``relates_to``)? Could possibly
   be state events? Don't really want all the history if say the priority was changed 1000 times, just want
   the current state of the key.

Comments:
 - Additional event with ``relates_to`` key.


Forum
-----
::

 Forum => Room (with pointers to Board Rooms)
 Boards => Room (with pointers to Thread Rooms)
 Threads => Room
 Messages => Message Events

Forum:
 - Contains 10s of Boards.
 - Contains special Message Events which point to different rooms f.e Board.

Boards:
 - Contains 100s of Threads.
 - Contains special Message Events which point to different rooms f.e. Thread.

Threads:
 - Contains 100s of Messages.

Can't do this nicely with the current Federation API because you have loads of
Rooms and what does posting a message look like? Creating a thread is done by..?
The user who is posting cannot create the thread because otherwise they would be
the room creator and have ultimate privileges. So it has to be created by a bot
of some kind which ties into auth (Application services?). To follow a board,
you need a bot to join the Board Room and then watch it for changes... 

Fundamental problem with forums is that there is only 1 PDU graph per room and
you either have to pull in lots of graphs separately or one graph and filter it
separately to get to the desired sub set of data. You have to subscribe into a
lot of graphs if you subscribe to a board... If you have the entire board...
good luck scrollbacking a particular thread.


Google+ Community
-----------------
::

 Community => Room (with pointers to Category Rooms)
 Category => Room
 Post => Message Events
 Comment => Message Events (relates_to key)

Community:
 - Contains 10s of categories.
 - Contains special Message Events which point to different rooms f.e Category.
 - Moderators of the community are mods in this room. They are in charge of making
   new categories and the subsequent rooms. Can get a bit funky if a mod creates a
   category room without the same permissions as the community room... but another
   mod can always delete the pointer to the buggy category room and make a new one.
 - Do we want to support the idea of forking off new rooms from existing ones? This
   and forums could benefit from it.

Category:
 - Contains 1000s of posts.
 - Same permissions as the community room. How to enforce? Fork off the community
   room?

Posts:
 - Contains 10s of comments.

This is similar to forums but you can more reasonably say "screw it, pull in the
entire community of posts."

