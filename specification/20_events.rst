Events
======

All communication in Matrix is expressed in the form of data objects called
Events. These are the fundamental building blocks common to the client-server,
server-server and application-service APIs, and are described below.



Common event fields
-------------------
All events MUST have the following fields:

``event_id``
  Type:
    String.
  Description:
    Represents the globally unique ID for this event.

``type``
  Type:
    String.
  Description:
    Contains the event type, e.g. ``m.room.message``

``content``
  Type:
    JSON Object.
  Description:
    Contains the content of the event. When interacting with the REST API, this is the HTTP body.

``room_id``
  Type:
    String.
  Description:
    Contains the ID of the room associated with this event.

``user_id``
  Type:
    String.
  Description:
    Contains the fully-qualified ID of the user who *sent* this event.

State events have the additional fields:

``state_key``
  Type:
    String.
  Description:
    Contains the state key for this state event. If there is no state key for this state event, this
    will be an empty string. The presence of ``state_key`` makes this event a state event.

``required_power_level``
  Type:
    Integer.
  Description:
    Contains the minimum power level a user must have before they can update this event.

``prev_content``
  Type:
    JSON Object.
  Description:
    Optional. Contains the previous ``content`` for this event. If there is no previous content, this
    key will be missing.

.. TODO-spec
  How do "age" and "ts" fit in to all this? Which do we expose?


Room Events
-----------
.. NOTE::
  This section is a work in progress.

This specification outlines several standard event types, all of which are
prefixed with ``m.``

``m.room.name``
  Summary:
    Set the human-readable name for the room.
  Type:
    State event
  JSON format:
    ``{ "name" : "string" }``
  Example:
    ``{ "name" : "My Room" }``
  Description:
    A room has an opaque room ID which is not human-friendly to read. A room
    alias is human-friendly, but not all rooms have room aliases. The room name
    is a human-friendly string designed to be displayed to the end-user. The
    room name is not *unique*, as multiple rooms can have the same room name
    set. The room name can also be set when creating a room using |createRoom|_
    with the ``name`` key.

``m.room.topic``
  Summary:
    Set a topic for the room.
  Type:
    State event
  JSON format:
    ``{ "topic" : "string" }``
  Example:
    ``{ "topic" : "Welcome to the real world." }``
  Description:
    A topic is a short message detailing what is currently being discussed in
    the room.  It can also be used as a way to display extra information about
    the room, which may not be suitable for the room name. The room topic can
    also be set when creating a room using |createRoom|_ with the ``topic``
    key.

``m.room.member``
  Summary:
    The current membership state of a user in the room.
  Type:
    State event
  JSON format:
    ``{ "membership" : "enum[ invite|join|leave|ban ]" }``
  Example:
    ``{ "membership" : "join" }``
  Description:
    Adjusts the membership state for a user in a room. It is preferable to use
    the membership APIs (``/rooms/<room id>/invite`` etc) when performing
    membership actions rather than adjusting the state directly as there are a
    restricted set of valid transformations. For example, user A cannot force
    user B to join a room, and trying to force this state change directly will
    fail. See the `Rooms`_ section for how to use the membership APIs.

``m.room.create``
  Summary:
    The first event in the room.
  Type:
    State event
  JSON format:
    ``{ "creator": "string"}``
  Example:
    ``{ "creator": "@user:example.com" }``
  Description:
    This is the first event in a room and cannot be changed. It acts as the
    root of all other events.

``m.room.join_rules``
  Summary:
    Descripes how/if people are allowed to join.
  Type:
    State event
  JSON format:
    ``{ "join_rule": "enum [ public|knock|invite|private ]" }``
  Example:
    ``{ "join_rule": "public" }``
  Description:
    TODO-doc : Use docs/models/rooms.rst

``m.room.power_levels``
  Summary:
    Defines the power levels of users in the room.
  Type:
    State event
  JSON format:
    ``{ "<user_id>": <int>, ..., "default": <int>}``
  Example:
    ``{ "@user:example.com": 5, "@user2:example.com": 10, "default": 0 }``
  Description:
    If a user is in the list, then they have the associated power level.
    Otherwise they have the default level. If not ``default`` key is supplied,
    it is assumed to be 0.

``m.room.add_state_level``
  Summary:
    Defines the minimum power level a user needs to add state.
  Type:
    State event
  JSON format:
    ``{ "level": <int> }``
  Example:
    ``{ "level": 5 }``
  Description:
    To add a new piece of state to the room a user must have the given power
    level. This does not apply to updating current state, which is goverened
    by the ``required_power_level`` event key.

``m.room.send_event_level``
  Summary:
    Defines the minimum power level a user needs to send an event.
  Type:
    State event
  JSON format:
    ``{ "level": <int> }``
  Example:
    ``{ "level": 0 }``
  Description:
    To send a new event into the room a user must have at least this power
    level. This allows ops to make the room read only by increasing this level,
    or muting individual users by lowering their power level below this
    threshold.

``m.room.ops_levels``
  Summary:
    Defines the minimum power levels that a user must have before they can
    kick and/or ban other users.
  Type:
    State event
  JSON format:
    ``{ "ban_level": <int>, "kick_level": <int>, "redact_level": <int> }``
  Example:
    ``{ "ban_level": 5, "kick_level": 5 }``
  Description:
    This defines who can ban and/or kick people in the room. Most of the time
    ``ban_level`` will be greater than or equal to ``kick_level`` since
    banning is more severe than kicking.

``m.room.aliases``
  Summary:
    These state events are used to inform the room about what room aliases it
    has.
  Type:
    State event
  JSON format:
    ``{ "aliases": ["string", ...] }``
  Example:
    ``{ "aliases": ["#foo:example.com"] }``
  Description:
    This event is sent by a homeserver directly to inform of changes to the
    list of aliases it knows about for that room. As a special-case, the
    ``state_key`` of the event is the homeserver which owns the room alias.
    For example, an event might look like::

      {
        "type": "m.room.aliases",
        "event_id": "012345678ab",
        "room_id": "!xAbCdEfG:example.com",
        "state_key": "example.com",
        "content": {
          "aliases": ["#foo:example.com"]
        }
      }

    The event contains the full list of aliases now stored by the home server
    that emitted it; additions or deletions are not explicitly mentioned as
    being such. The entire set of known aliases for the room is then the union
    of the individual lists declared by all such keys, one from each home
    server holding at least one alias.

    Clients `should` check the validity of any room alias given in this list
    before presenting it to the user as trusted fact. The lists given by this
    event should be considered simply as advice on which aliases might exist,
    for which the client can perform the lookup to confirm whether it receives
    the correct room ID.

``m.room.message``
  Summary:
    A message.
  Type:
    Message event
  JSON format:
    ``{ "msgtype": "string" }``
  Example:
    ``{ "msgtype": "m.text", "body": "Testing" }``
  Description:
    This event is used when sending messages in a room. Messages are not
    limited to be text.  The ``msgtype`` key outlines the type of message, e.g.
    text, audio, image, video, etc.  Whilst not required, the ``body`` key
    SHOULD be used with every kind of ``msgtype`` as a fallback mechanism when
    a client cannot render the message. For more information on the types of
    messages which can be sent, see `m.room.message msgtypes`_.

``m.room.message.feedback``
  Summary:
    A receipt for a message.
    N.B. not implemented in Synapse, and superceded in v2 CS API by the 'relates_to' event field.
  Type:
    Message event
  JSON format:
    ``{ "type": "enum [ delivered|read ]", "target_event_id": "string" }``
  Example:
    ``{ "type": "delivered", "target_event_id": "e3b2icys" }``
  Description:
    Feedback events are events sent to acknowledge a message in some way. There
    are two supported acknowledgements: ``delivered`` (sent when the event has
    been received) and ``read`` (sent when the event has been observed by the
    end-user). The ``target_event_id`` should reference the ``m.room.message``
    event being acknowledged.

``m.room.redaction``
  Summary:
    Indicates a previous event has been redacted.
  Type:
    Message event
  JSON format:
    ``{ "reason": "string" }``
  Description:
    Events can be redacted by either room or server admins. Redacting an event
    means that all keys not required by the protocol are stripped off, allowing
    admins to remove offensive or illegal content that may have been attached
    to any event. This cannot be undone, allowing server owners to physically
    delete the offending data.  There is also a concept of a moderator hiding a
    message event, which can be undone, but cannot be applied to state
    events.
    The event that has been redacted is specified in the ``redacts`` event
    level key.

m.room.message msgtypes
~~~~~~~~~~~~~~~~~~~~~~~

.. TODO-spec
   How a client should handle unknown message types.

.. TODO-spec
   We've forgotten m.file...

.. TODO-spec
   It's really confusing that the m. prefix is used both for event types and
   for msgtypes.  We should namespace them differently somehow.

Each ``m.room.message`` MUST have a ``msgtype`` key which identifies the type
of message being sent. Each type has their own required and optional keys, as
outlined below:

``m.text``
  Required keys:
    - ``body`` : "string" - The body of the message.
  Optional keys:
    None.
  Example:
    ``{ "msgtype": "m.text", "body": "I am a fish" }``

``m.emote``
  Required keys:
    - ``body`` : "string" - The emote action to perform.
  Optional keys:
    None.
  Example:
    ``{ "msgtype": "m.emote", "body": "tries to come up with a witty explanation" }``

``m.notice``
  Required keys:
    - ``body`` : "string" - The body of the message.
  Optional keys:
    None.
  Example:
    ``{ "msgype": "m.notice", "body": "some kind of automated announcement" }``

  A ``m.notice`` message should be considered similar to a plain ``m.text``
  message except that clients should visually distinguish it in some way. It is
  intended to be used by automated clients, such as bots, bridges, and other
  entities, rather than humans. Additionally, such automated agents which watch
  a room for messages and respond to them ought to ignore ``m.notice`` messages.
  This helps to prevent infinite-loop situations where two automated clients
  continuously exchange messages, as each responds to the other.

``m.image``
  Required keys:
    - ``url`` : "string" - The URL to the image.
  Optional keys:
    - ``info`` : "string" - info : JSON object (ImageInfo) - The image info for
      image referred to in ``url``.
    - ``thumbnail_url`` : "string" - The URL to the thumbnail.
    - ``thumbnail_info`` : JSON object (ImageInfo) - The image info for the
      image referred to in ``thumbnail_url``.
    - ``body`` : "string" - The alt text of the image, or some kind of content
      description for accessibility e.g. "image attachment".

  ImageInfo:
    Information about an image::

      {
        "size" : integer (size of image in bytes),
        "w" : integer (width of image in pixels),
        "h" : integer (height of image in pixels),
        "mimetype" : "string (e.g. image/jpeg)",
      }

``m.audio``
  Required keys:
    - ``url`` : "string" - The URL to the audio.
  Optional keys:
    - ``info`` : JSON object (AudioInfo) - The audio info for the audio
      referred to in ``url``.
    - ``body`` : "string" - A description of the audio e.g. "Bee Gees - Stayin'
      Alive", or some kind of content description for accessibility e.g.
      "audio attachment".
  AudioInfo:
    Information about a piece of audio::

      {
        "mimetype" : "string (e.g. audio/aac)",
        "size" : integer (size of audio in bytes),
        "duration" : integer (duration of audio in milliseconds),
      }

``m.video``
  Required keys:
    - ``url`` : "string" - The URL to the video.
  Optional keys:
    - ``info`` : JSON object (VideoInfo) - The video info for the video
      referred to in ``url``.
    - ``body`` : "string" - A description of the video e.g. "Gangnam style", or
      some kind of content description for accessibility e.g. "video
      attachment".

  VideoInfo:
    Information about a video::

      {
        "mimetype" : "string (e.g. video/mp4)",
        "size" : integer (size of video in bytes),
        "duration" : integer (duration of video in milliseconds),
        "w" : integer (width of video in pixels),
        "h" : integer (height of video in pixels),
        "thumbnail_url" : "string (URL to image)",
        "thumbanil_info" : JSON object (ImageInfo)
      }

``m.location``
  Required keys:
    - ``geo_uri`` : "string" - The geo URI representing the location.
  Optional keys:
    - ``thumbnail_url`` : "string" - The URL to a thumnail of the location
      being represented.
    - ``thumbnail_info`` : JSON object (ImageInfo) - The image info for the
      image referred to in ``thumbnail_url``.
    - ``body`` : "string" - A description of the location e.g. "Big Ben,
      London, UK", or some kind of content description for accessibility e.g.
      "location attachment".

``m.file``
  Required keys:
    - ``url`` : "string" - The URL for the file
    - ``filename`` : "string" - The original filename of the uploaded file
  Optional keys:
    - ``info`` : JSON object (FileInfo) - The info for the file
      referred to in ``url``.
    - ``thumbnail_url`` : "string" - The URL to a thumnail of the location
      being represented.
    - ``thumbnail_info`` : JSON object (ImageInfo) - The image info for the
      image referred to in ``thumbnail_url``.
    - ``body`` : "string" - A human-readable description of the file for
      backwards compatibility. This is recommended to be the filename of the
      original upload.

  FileInfo:
    Information about a file::

      {
        "size" : integer (size of file in bytes),
        "mimetype" : "string (e.g. image/jpeg)",
      }

.. TODO-spec
    Make the definitions "inherit" from FileInfo where necessary...

Presence Events
~~~~~~~~~~~~~~~

``m.presence``
  Summary:
    Informs you of a user's presence state changes.
    
  Type:
    Presence event
    
  JSON format::
  
    { 
      "displayname": "utf-8 string",
      "avatar_url": "url",
      "presence": "enum [ online|unavailable|offline|free_for_chat|hidden ]",
      "last_active_ago": "milliseconds"
    }
    
  Example::
  
    {
      "displayname": "Matthew",
      "avatar_url": "mxc://domain/id",
      "presence": "online",
      "last_active_ago": 10000
    }
    
  Description:
    Each user has the concept of presence information. This encodes the
    "availability" of that user, suitable for display on other user's clients.
    This is transmitted as an ``m.presence`` event and is one of the few events
    which are sent *outside the context of a room*. The basic piece of presence
    information is represented by the ``presence`` key, which is an enum of one
    of the following:

      - ``online`` : The default state when the user is connected to an event
        stream.
      - ``unavailable`` : The user is not reachable at this time.
      - ``offline`` : The user is not connected to an event stream.
      - ``free_for_chat`` : The user is generally willing to receive messages
        moreso than default.
      - ``hidden`` : Behaves as offline, but allows the user to see the client
        state anyway and generally interact with client features. (Not yet
        implemented in synapse).

    In addition, the server maintains a timestamp of the last time it saw a
    pro-active event from the user; either sending a message to a room, or
    changing presence state from a lower to a higher level of availability
    (thus: changing state from ``unavailable`` to ``online`` counts as a
    proactive event, whereas in the other direction it will not). This timestamp
    is presented via a key called ``last_active_ago``, which gives the relative
    number of milliseconds since the message is generated/emitted that the user
    was last seen active.
    

Events on Change of Profile Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Because the profile displayname and avatar information are likely to be used in
many places of a client's display, changes to these fields cause an automatic
propagation event to occur, informing likely-interested parties of the new
values. This change is conveyed using two separate mechanisms:

 - a ``m.room.member`` event is sent to every room the user is a member of,
   to update the ``displayname`` and ``avatar_url``.
 - a ``m.presence`` presence status update is sent, again containing the new values of the
   ``displayname`` and ``avatar_url`` keys, in addition to the required
   ``presence`` key containing the current presence state of the user.

Both of these should be done automatically by the home server when a user
successfully changes their displayname or avatar URL fields.

Additionally, when home servers emit room membership events for their own
users, they should include the displayname and avatar URL fields in these
events so that clients already have these details to hand, and do not have to
perform extra roundtrips to query it.

Voice over IP
-------------
Matrix can also be used to set up VoIP calls. This is part of the core
specification, although is at a relatively early stage. Voice (and video) over
Matrix is built on the WebRTC 1.0 standard.

Call events are sent to a room, like any other event. This means that clients
must only send call events to rooms with exactly two participants as currently
the WebRTC standard is based around two-party communication.

Events
~~~~~~
``m.call.invite``
This event is sent by the caller when they wish to establish a call.

  Required keys:
    - ``call_id`` : "string" - A unique identifier for the call
    - ``offer`` : "offer object" - The session description
    - ``version`` : "integer" - The version of the VoIP specification this
      message adheres to. This specification is version 0.
    - ``lifetime`` : "integer" - The time in milliseconds that the invite is
      valid for. Once the invite age exceeds this value, clients should discard
      it. They should also no longer show the call as awaiting an answer in the
      UI.

  Optional keys:
    None.
    
  Example::

    {
      "version" : 0,
      "call_id": "12345",
      "offer": {
        "type" : "offer",
        "sdp" : "v=0\r\no=- 6584580628695956864 2 IN IP4 127.0.0.1[...]"
      }
    }

``Offer Object``
  Required keys:
    - ``type`` : "string" - The type of session description, in this case
      'offer'
    - ``sdp`` : "string" - The SDP text of the session description

``m.call.candidates``
This event is sent by callers after sending an invite and by the callee after
answering.  Its purpose is to give the other party additional ICE candidates to
try using to communicate.

  Required keys:
    - ``call_id`` : "string" - The ID of the call this event relates to
    - ``version`` : "integer" - The version of the VoIP specification this
      messages adheres to. his specification is version 0.
    - ``candidates`` : "array of candidate objects" - Array of object
      describing the candidates.

``Candidate Object``

  Required Keys:
    - ``sdpMid`` : "string" - The SDP media type this candidate is intended
      for.
    - ``sdpMLineIndex`` : "integer" - The index of the SDP 'm' line this
      candidate is intended for
    - ``candidate`` : "string" - The SDP 'a' line of the candidate

``m.call.answer``

  Required keys:
    - ``call_id`` : "string" - The ID of the call this event relates to
    - ``version`` : "integer" - The version of the VoIP specification this
      messages
    - ``answer`` : "answer object" - Object giving the SDK answer

``Answer Object``

  Required keys:
    - ``type`` : "string" - The type of session description. 'answer' in this
      case.
    - ``sdp`` : "string" - The SDP text of the session description

``m.call.hangup``
Sent by either party to signal their termination of the call. This can be sent
either once the call has has been established or before to abort the call.

  Required keys:
    - ``call_id`` : "string" - The ID of the call this event relates to
    - ``version`` : "integer" - The version of the VoIP specification this
      messages

Message Exchange
~~~~~~~~~~~~~~~~
A call is set up with messages exchanged as follows:

::

   Caller                   Callee
 m.call.invite ----------->
 m.call.candidate -------->
 [more candidates events]
                         User answers call
                  <------ m.call.answer
               [...]
                  <------ m.call.hangup

Or a rejected call:

::

   Caller                   Callee
 m.call.invite ----------->
 m.call.candidate -------->
 [more candidates events]
                        User rejects call
                 <------- m.call.hangup

Calls are negotiated according to the WebRTC specification.


Glare
~~~~~
This specification aims to address the problem of two users calling each other
at roughly the same time and their invites crossing on the wire. It is a far
better experience for the users if their calls are connected if it is clear
that their intention is to set up a call with one another.

In Matrix, calls are to rooms rather than users (even if those rooms may only
contain one other user) so we consider calls which are to the same room.

The rules for dealing with such a situation are as follows:

 - If an invite to a room is received whilst the client is preparing to send an
   invite to the same room, the client should cancel its outgoing call and
   instead automatically accept the incoming call on behalf of the user.
 - If an invite to a room is received after the client has sent an invite to
   the same room and is waiting for a response, the client should perform a
   lexicographical comparison of the call IDs of the two calls and use the
   lesser of the two calls, aborting the greater. If the incoming call is the
   lesser, the client should accept this call on behalf of the user.

The call setup should appear seamless to the user as if they had simply placed
a call and the other party had accepted. Thusly, any media stream that had been
setup for use on a call should be transferred and used for the call that
replaces it.

