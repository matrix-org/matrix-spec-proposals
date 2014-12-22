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

