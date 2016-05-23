Event Threading
===============

This document describes the process involved in relating events into 'threads'.

Relates to (Events) ``[ONGOING]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Events may be in response to other events, e.g. comments. This is represented
by the ``relates_to`` key. This differs from the ``updates`` key as they *do
not update the event itself* , and are *not required* in order to display the
parent event. Crucially, the child events can be paginated, whereas ``updates``
child events cannot be paginated. The ``relates_to`` key is designed to support
multiple relations.


Bundling relations
++++++++++++++++++

Child events should be bundled with the parent event under the ``relates_to``
key. There should also be two limits to how many events are returned:

- A limit on the amount of events returned per thread. ``depth_limit``
- A limit on the amount of threads returned per events. ``thread_limit``

The ``relates_to`` key on an event will contain an array of every relation to
that event. The relations will contain a ``start`` and ``next`` key for
pagination. The start key is important should the client not recieve previous
events since it will be the only way to determine the root event. The chain of
events in this thread (where each event is a response to the previous event) 
will be recorded inside events up to a maximum value.

Should the chain split at any point (where two or more replies are made),
the event will contain it's own ``relates_to`` key with it's own relations.

Should the event contain more threads than the limit imposed by the
client/server, the thread will be listed but the client must paginate with the
given token to read the messages.

Main use cases for ``relates_to``:
 - Comments on a message.
 - Non-local delivery/read receipts : If doing separate receipt events for each
   message.
 - Meeting invite responses : Yes/No/Maybe for a meeting.
 - Threaded conversations within a room.
 - Forum style post responses.

Like with ``updates``, clients need to know how to apply the deltas because
clients may receive the events separately down the event stream.

TODO:
 - Can a child event reply to multiple parent events? Use case?
 - Should a parent event and its children share a thread ID? Does the
   originating HS set this ID? Is this thread ID exposed through federation?
   e.g. can a HS retrieve all events for a given thread ID from another HS?
 - Should there be a way to filter ``relates_to`` in advance?

Example of 'relates_to'
+++++++++++++++++++++++
- A message is sent to the a room.
- Replies are made as follows:

::

 ┌B─D─E─I─J─K
 A
 ├C─F
 │└─G
 └H
 └L

- A has two replies, B and C
- B has a long chain of replies which will go outside the depth limit.
- C is replied to by F and G
- H and L are two more responses that were not included to demonstrate limits.

- The client put a limit to 5 messages per thread chain.
- The client put a limit of 2 threads returned per message.

An example where message A has been delievered to the client.

.. code :: javascript

  {
    content: { body: "First!" },
    relates_to:[
      {
        "start":"ROOTTOKEN",
        "events":[
              { content: { body: "Message B" } ... },
              { content: { body: "Message D" } ... },
              { content: { body: "Message E" } ... },
              { content: { body: "Message I" } ... },
              { content: { body: "Message J" } ... }
        ],
        "next":"TOKEN"
      },
      {
        "start":"ROOTTOKEN",
        "events":[
              {
                content: { body: "Message C" }
                relates_to:[
                  {
                    "start":"ROOTTOKEN",
                    "events":[
                      { content: { body: "Message F" } ... }
                    ],
                    "next":null
                  },
                  {
                    "start":"ROOTTOKEN",
                    "events":[
                      { content: { body: "Message G" } ... }
                    ],
                    "next":null
                  }
                ]
              }
        ],
        "next":null
      },
      {
        "start":"ROOTTOKEN",
        "events":null,
        "next":"TOKEN2"
      },
      {
        "start":"ROOTTOKEN",
        "events":null,
        "next":"TOKEN3"
      }
    ]
  }
  
An example where a client recieves Message F but is missing some of the timeline.

.. code :: javascript

  {
    content: { body: "Message F" },
    relates_to:[
      {
        "start":"ROOTTOKEN",
        "events":[],
        "next":null
      }
    ]
  }

In this example, F is isolated and must use start to find the root event.
