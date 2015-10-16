Client-Server API
=================

Overview
--------

The client-server API provides a simple lightweight API to let clients send
messages, control rooms and synchronise conversation history. It is designed to
support both lightweight clients which store no state and lazy-load data from
the server as required - as well as heavyweight clients which maintain a full
local persistent copy of server state.

This mostly describes v1 of the Client-Server API as featured in the original September
2014 launch of Matrix, apart from user-interactive authentication where it is
encouraged to move to v2, therefore this is the version documented here.
Version 2 is currently in development (as of Jan-March 2015) as an incremental
but backwards-incompatible refinement of Version 1 and will be released
shortly.

Documentation for the old `V1 authentication
<../attic/v1_registration_login.rst>`_ is still available separately.

Client Authentication
---------------------
Most API endpoints require the user to identify themselves by presenting
previously obtained credentials in the form of an ``access_token`` query
parameter.

In API version 2, when credentials are missing or invalid, the HTTP call will
return with a status of 401 and the error code, ``M_MISSING_TOKEN`` or
``M_UNKNOWN_TOKEN`` respectively.

User-Interactive Authentication API
-----------------------------------
This section refers to API Version 2.

Some API endpoints such as ``login`` or ``register`` require authentication that
interacts with the user. The home server may provide many different ways of
authenticating, such as user/password auth, login via a social network (OAuth2),
login by confirming a token sent to their email address, etc. This specification
does not define how home servers should authorise their users but instead
defines the standard interface which implementations should follow so that ANY
client can login to ANY home server.

The process takes the form of one or more stages, where at each stage the client
submits a set of data for a given stage type and awaits a response from the
server, which will either be a final success or a request to perform an
additional stage. This exchange continues until the final success.

Authentication works by client and server exchanging dictionaries. This
specification covers how this is done over JSON HTTP POST.

For each endpoint, a server offers one of more 'flows' that the client can use
to authenticate itself. Each flow comprises one or more 'stages'. Flows may have
more than one stage to implement n-factor auth. When all stages are complete,
authentication is complete and the API call succeeds. To establish what flows a
server supports for an endpoint, a client sends the request with no
authentication. A request to an endpoint that uses User-Interactive
Authentication never succeeds without auth. Home Servers may allow requests that
don't require auth by offering a stage with only the ``m.login.dummy`` auth
type. The home server returns a response with HTTP status 401 and a JSON object
as follows::

  {
    "flows": [
      {
        "stages": [ "example.type.foo", "example.type.bar" ]
      },
      {
        "stages": [ "example.type.foo", "example.type.baz" ]
      }
    ],
    "params": {
        "example.type.baz": {
            "example_key": "foobar"
        }
    },
    "session": "xxxxxx"
  }

In addition to the ``flows``, this object contains some extra
information:

params
  This section contains any information that the client will need to know in
  order to use a given type of authentication. For each login stage type
  presented, that type may be present as a key in this dictionary. For example,
  the public part of an OAuth client ID could be given here.
session
  This is a session identifier that the client must pass back to the home
  server, if one is provided, in subsequent attempts to authenticate in the same
  API call.

The client then chooses a flow and attempts to complete one of the stages. It
does this by resubmitting the same request with the the addition of an 'auth'
key in the object that it submits. This dictionary contains a ``type`` key whose
value is the name of the stage type that the client is attempting to complete.
It must also contains a ``session`` key with the value of the session key given
by the home server, if one was given. It also contains other keys dependent on
the stage type being attempted. For example, if the client is attempting to
complete login type ``example.type.foo``, it might submit something like this::

  {
    "a_request_parameter": "something",
    "another_request_parameter": "something else",
    "auth": {
        "type": "example.type.foo",
        "session", "xxxxxx",
        "example_credential": "verypoorsharedsecret"
    }
  }

If the home server deems the authentication attempt to be successful but still
requires more stages to be completed, it returns HTTP status 401 along with the
same object as when no authentication was attempted, with the addition of the
``completed`` key which is an array of stage type the client has completed
successfully::

  {
    "completed": [ "example.type.foo" ],
    "flows": [
      {
        "stages": [ "example.type.foo", "example.type.bar" ]
      },
      {
        "stages": [ "example.type.foo", "example.type.baz" ]
      }
    ],
    "params": {
        "example.type.baz": {
            "example_key": "foobar"
        }
    },
    "session": "xxxxxx"
  }

If the home server decides the attempt was unsuccessful, it returns an error
message in the standard format::

  {
    "errcode": "M_EXAMPLE_ERROR",
    "error": "Something was wrong"
  }

Individual stages may require more than one request to complete, in which case
the response will be as if the request was unauthenticated with the addition of
any other keys as defined by the login type.

If the client has completed all stages of a flow, the home server performs the
API call and returns the result as normal.

Some authentication types may be completed by means other than through the
Matrix client, for example, an email confirmation may be completed when the user
clicks on the link in the email. In this case, the client retries the request
with an auth dict containing only the session key. The response to this will be
the same as if the client were attempting to complete an auth state normally,
i.e. the request will either complete or request auth, with the presence or
absence of that login stage type in the 'completed' array indicating whether
that stage is complete.

Example
~~~~~~~
At a high level, the requests made for an API call completing an auth flow with
three stages will resemble the following diagram::
  
   _______________________
  |       Stage 1         |
  | type: "<stage type1>" |
  |  ___________________  |
  | |_Request_1_________| | <-- Returns "session" key which is used throughout.
  |  ___________________  |
  | |_Request_2_________| |
  |_______________________|
            |
            |
   _________V_____________
  |       Stage 2         |
  | type: "<stage type2>" |
  |  ___________________  |
  | |_Request_1_________| |
  |  ___________________  |
  | |_Request_2_________| |
  |  ___________________  |
  | |_Request_3_________| |
  |_______________________|
            |
            |
   _________V_____________
  |       Stage 3         |
  | type: "<stage type3>" |
  |  ___________________  |
  | |_Request_1_________| | <-- Returns API response
  |_______________________|

This specification defines the following login types:
 - ``m.login.password``
 - ``m.login.recaptcha``
 - ``m.login.oauth2``
 - ``m.login.email.identity``
 - ``m.login.token``
 - ``m.login.dummy``

Password-based
~~~~~~~~~~~~~~
:Type:
  ``m.login.password``
:Description:
  The client submits a username and secret password, both sent in plain-text.

To respond to this type, reply with an auth dict as follows::

  {
    "type": "m.login.password",
    "user": "<user_id or user localpart>",
    "password": "<password>"
  }

.. WARNING::
  Clients SHOULD enforce that the password provided is suitably complex. The
  password SHOULD include a lower-case letter, an upper-case letter, a number
  and a symbol and be at a minimum 8 characters in length. Servers MAY reject
  weak passwords with an error code ``M_WEAK_PASSWORD``.

Google ReCaptcha
~~~~~~~~~~~~~~~~
:Type:
  ``m.login.recaptcha``
:Description:
  The user completes a Google ReCaptcha 2.0 challenge

To respond to this type, reply with an auth dict as follows::

  {
    "type": "m.login.recaptcha",
    "response": "<captcha response>"
  }

Token-based
~~~~~~~~~~~
:Type:
  ``m.login.token``
:Description:
  The client submits a username and token.

To respond to this type, reply with an auth dict as follows::

  {
    "type": "m.login.token",
    "user": "<user_id or user localpart>",
    "token": "<token>",
    "txn_id": "<client generated nonce>"
  }

The ``nonce`` should be a random string generated by the client for the
request. The same ``nonce`` should be used if retrying the request.

There are many ways a client may receive a ``token``, including via an email or
from an existing logged in device.

The ``txn_id`` may be used by the server to disallow other devices from using
the token, thus providing "single use" tokens while still allowing the device
to retry the request. This would be done by tying the token to the ``txn_id``
server side, as well as potentially invalidating the token completely once the
device has successfully logged in (e.g. when we receive a request from the
newly provisioned access_token).

The ``token`` must be a macaroon.

OAuth2-based
~~~~~~~~~~~~
:Type:
  ``m.login.oauth2``
:Description:
  Authentication is supported via OAuth2 URLs. This login consists of multiple
  requests.
:Parameters:
  ``uri``: Authorization Request URI OR service selection URI. Both contain an
  encoded ``redirect URI``.

The home server acts as a 'confidential' client for the purposes of OAuth2.  If
the uri is a ``service selection URI``, it MUST point to a webpage which prompts
the user to choose which service to authorize with. On selection of a service,
this MUST link through to an ``Authorization Request URI``. If there is only one
service which the home server accepts when logging in, this indirection can be
skipped and the "uri" key can be the ``Authorization Request URI``.

The client then visits the ``Authorization Request URI``, which then shows the
OAuth2 Allow/Deny prompt. Hitting 'Allow' redirects to the ``redirect URI`` with
the auth code. Home servers can choose any path for the ``redirect URI``. Once
the OAuth flow has completed, the client retries the request with the session
only, as above.

Email-based (identity server)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:Type:
  ``m.login.email.identity``
:Description:
  Authentication is supported by authorising an email address with an identity
  server.

Prior to submitting this, the client should authenticate with an identity
server. After authenticating, the session information should be submitted to
the home server.

To respond to this type, reply with an auth dict as follows::

  {
    "type": "m.login.email.identity",
    "threepidCreds": [
      {
        "sid": "<identity server session id>",
        "client_secret": "<identity server client secret>",
        "id_server": "<url of identity server authed with, e.g. 'matrix.org:8090'>"
      }
    ]
  }

Dummy Auth
~~~~~~~~~~
:Type:
  ``m.login.dummy``
:Description:
  Dummy authentication always succeeds and requires no extra parameters. Its
  purpose is to allow servers to not require any form of User-Interactive
  Authentication to perform a request.

To respond to this type, reply with an auth dict with just the type and session,
if provided::

  {
    "type": "m.login.dummy",
  }


Fallback
~~~~~~~~
Clients cannot be expected to be able to know how to process every single login
type. If a client does not know how to handle a given login type, it can direct
the user to a web browser with the URL of a fallback page which will allow the
user to complete that login step out-of-band in their web browser. The URL it
should open is the Home Server base URL plus prefix, plus::

  /auth/<stage type>/fallback/web?session=<session ID>

Where ``stage type`` is the type name of the stage it is attempting and
``session id`` is the ID of the session given by the home server.

This MUST return an HTML page which can perform this authentication stage. This
page must attempt to call the JavaScript function ``window.onAuthDone`` when
the authentication has been completed.

Pagination
----------

Querying large datasets in Matrix always uses the same pagination API pattern to
to give clients a consistent way of selecting subsets of a potentially changing
dataset. Requests pass in ``from``, ``to`` and ``limit`` parameters which describe
where to read from the stream. ``from`` and ``to`` are opaque textual 'stream
tokens' which describe positions in the dataset. The response returns new
``start`` and ``end`` stream token values which can then be passed to subsequent
requests to continue pagination.

Pagination Request Query Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
       
Query parameters:
  from:
    $streamtoken - The opaque token to start streaming from.
  to:
    $streamtoken - The opaque token to end streaming at. Typically,
    clients will not know the item of data to end at, so this will usually be 
    omitted.
  limit:
    integer - An integer representing the maximum number of items to 
    return.

'START' and 'END' are placeholder values used in these examples to describe the
start and end of the dataset respectively.

Unless specified, the default pagination parameters are from=START, to=END, 
without a limit set. This allows you to hit an API like
/events without any query parameters to get everything.

For example, the event stream has events E1 -> E15. The client wants the last 5 
events and doesn't know any previous events::

    S                                                    E
    |-E1-E2-E3-E4-E5-E6-E7-E8-E9-E10-E11-E12-E13-E14-E15-|
    |                               |                    |
    |                          _____|                    |
    |__________________       |       ___________________|
                       |      |      |
     GET /events?to=START&limit=5&from=END
     Returns:
       E15,E14,E13,E12,E11


Another example: a public room list has rooms R1 -> R17. The client is showing 5 
rooms at a time on screen, and is on page 2. They want to
now show page 3 (rooms R11 -> 15)::

    S                                                           E
    |  0  1  2  3  4  5  6  7  8  9  10  11  12  13  14  15  16 | stream token
    |-R1-R2-R3-R4-R5-R6-R7-R8-R9-R10-R11-R12-R13-R14-R15-R16-R17| room
                      |____________| |________________|
                            |                |
                        Currently            |
                        viewing              |
                                             |
                             GET /rooms/list?from=9&to=END&limit=5
                             Returns: R11,R12,R13,R14,R15
                         
Note that tokens are treated in an *exclusive*, not inclusive, manner. The end 
token from the initial request was '9' which corresponded to R10. When the 2nd
request was made, R10 did not appear again, even though from=9 was specified. If
you know the token, you already have the data.

Pagination Response
~~~~~~~~~~~~~~~~~~~

Responses to pagination requests MUST follow the format::

  {
    "chunk": [ ... , Responses , ... ],
    "start" : $streamtoken,
    "end" : $streamtoken
  }

Where $streamtoken is an opaque token which can be used in another query to
get the next set of results. The "start" and "end" keys can only be omitted if
the complete dataset is provided in "chunk".

Events
------

.. _sect:events:

Overview
~~~~~~~~

The model of conversation history exposed by the client-server API can be
considered as a list of events. The server 'linearises' the
eventually-consistent event graph of events into an 'event stream' at any given
point in time::

  [E0]->[E1]->[E2]->[E3]->[E4]->[E5]->[E6]->[E7]->[E8]->[E9]
  
Clients can add to the stream by POSTing message or state events, and can read
from the stream via the |initialSync|_, |/rooms/<room_id>/initialSync|_, `Event
Stream`_ and |/rooms/<room_id>/messages|_ APIs.

For reading events, the intended flow of operation is to call
$PREFIX/initialSync, which returns all of the state and the last N events in the
event stream for each room, including ``start`` and ``end`` values describing the
pagination of each room's event stream. For instance,
$PREFIX/initialSync?limit=5 might return the events for a room in the
rooms[0].messages.chunk[] array, with tokens describing the start and end of the
range in rooms[0].messages.start as '1-2-3' and rooms[0].messages.end as
'a-b-c'.

You can visualise the range of events being returned as::

  [E0]->[E1]->[E2]->[E3]->[E4]->[E5]->[E6]->[E7]->[E8]->[E9]
                              ^                             ^
                              |                             |
                        start: '1-2-3'                end: 'a-b-c'
                             
Now, to receive future events in real-time on the eventstream, you simply GET
$PREFIX/events with a ``from`` parameter of 'a-b-c': in other words passing in the
``end`` token returned by initial sync. The request blocks until new events are
available or until your specified timeout elapses, and then returns a
new paginatable chunk of events alongside new start and end parameters::

  [E0]->[E1]->[E2]->[E3]->[E4]->[E5]->[E6]->[E7]->[E8]->[E9]->[E10]
                                                            ^      ^
                                                            |      |
                                                            |  end: 'x-y-z'
                                                      start: 'a-b-c'

To resume polling the events stream, you pass in the new ``end`` token as the
``from`` parameter of $PREFIX/events and poll again.

Similarly, to paginate events backwards in order to lazy-load in previous
history from the room, you simply GET $PREFIX/rooms/<room_id>/messages
specifying the ``from`` token to paginate backwards from and a limit of the number
of messages to retrieve. For instance, calling this API with a ``from`` parameter
of '1-2-3' and a limit of 5 would return::

  [E0]->[E1]->[E2]->[E3]->[E4]->[E5]->[E6]->[E7]->[E8]->[E9]->[E10]
  ^                            ^
  |                            |
  start: 'u-v-w'          end: '1-2-3'

To continue paginating backwards, one calls the /messages API again, supplying
the new ``start`` value as the ``from`` parameter.


Receiving live updates on a client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clients receive new events by long-polling the home server via the
$PREFIX/events API, specifying a timeout in milliseconds in the timeout
parameter. This will hold open the HTTP connection for a short period of time
waiting for new events, returning early if an event occurs. This is called the
`Event Stream`_. All events which are visible to the client will appear in the
event stream. When the request returns, an ``end`` token is included in the
response. This token can be used in the next request to continue where the
last request left off.

All events must be de-duplicated based on their event ID.

.. TODO
  is deduplication actually a hard requirement in CS v2?

.. TODO-spec
  Do we ever return multiple events in a single request?
  Don't we get lots of request setup RTT latency if we only do one event per request?
  Do we ever support streaming requests? Why not websockets?

When the client first logs in, they will need to initially synchronise with
their home server. This is achieved via the |initialSync|_ API. This API also
returns an ``end`` token which can be used with the event stream.  See the 'Room Sync' section below.

Events in a room
~~~~~~~~~~~~~~~~

Room events are split into two categories:

:State Events:
  These are events which update the metadata state of the room (e.g. room topic,
  room membership etc). State is keyed by a tuple of event ``type`` and a
  ``state_key``. State in the room with the same key-tuple will be overwritten.

:Message events:
  These are events which describe transient "once-off" activity in a room:
  typically communication such as sending an instant message or setting up a
  VoIP call. These used to be called 'non-state' events.

This specification outlines several events, all with the event type prefix
``m.``. However, applications may wish to add their own type of event, and this
can be achieved using the REST API detailed in the following sections. If new
events are added, the event ``type`` key SHOULD follow the Java package naming
convention, e.g. ``com.example.myapp.event``.  This ensures event types are
suitably namespaced for each application and reduces the risk of clashes.

State events
~~~~~~~~~~~~

State events can be sent by ``PUT`` ing to
|/rooms/<room_id>/state/<event_type>/<state_key>|_.  These events will be
overwritten if ``<room id>``, ``<event type>`` and ``<state key>`` all match.
If the state event has no ``state_key``, it can be omitted from the path. These
requests **cannot use transaction IDs** like other ``PUT`` paths because they
cannot be differentiated from the ``state_key``. Furthermore, ``POST`` is
unsupported on state paths. Valid requests look like::

  PUT /rooms/!roomid:domain/state/m.example.event
  { "key" : "without a state key" }

  PUT /rooms/!roomid:domain/state/m.another.example.event/foo
  { "key" : "with 'foo' as the state key" }

In contrast, these requests are invalid::

  POST /rooms/!roomid:domain/state/m.example.event/
  { "key" : "cannot use POST here" }

  PUT /rooms/!roomid:domain/state/m.another.example.event/foo/11
  { "key" : "txnIds are not supported" }

Care should be taken to avoid setting the wrong ``state key``::

  PUT /rooms/!roomid:domain/state/m.another.example.event/11
  { "key" : "with '11' as the state key, but was probably intended to be a txnId" }

The ``state_key`` is often used to store state about individual users, by using
the user ID as the ``state_key`` value. For example::

  PUT /rooms/!roomid:domain/state/m.favorite.animal.event/%40my_user%3Adomain.com
  { "animal" : "cat", "reason": "fluffy" }

In some cases, there may be no need for a ``state_key``, so it can be omitted::

  PUT /rooms/!roomid:domain/state/m.room.bgd.color
  { "color": "red", "hex": "#ff0000" }

See `Room Events`_ for the ``m.`` event specification.

Message events
~~~~~~~~~~~~~~

Message events can be sent by sending a request to
|/rooms/<room_id>/send/<event_type>|_.  These requests *can* use transaction
IDs and ``PUT``/``POST`` methods. Message events allow access to historical
events and pagination, making it best suited for sending messages.  For
example::

  POST /rooms/!roomid:domain/send/m.custom.example.message
  { "text": "Hello world!" }

  PUT /rooms/!roomid:domain/send/m.custom.example.message/11
  { "text": "Goodbye world!" }

See `Room Events`_ for the ``m.`` event specification.

Syncing rooms
~~~~~~~~~~~~~

.. NOTE::
  This section is a work in progress.

When a client logs in, they may have a list of rooms which they have already
joined. These rooms may also have a list of events associated with them. The
purpose of 'syncing' is to present the current room and event information in a
convenient, compact manner. The events returned are not limited to room events;
presence events will also be returned. A single syncing API is provided:

 - |initialSync|_ : A global sync which will present room and event information
   for all rooms the user has joined.

.. TODO-spec room-scoped initial sync
 - |/rooms/<room_id>/initialSync|_ : A sync scoped to a single room. Presents
   room and event information for this room only.
 - Room-scoped initial sync is Very Tricky because typically people would
   want to sync the room then listen for any new content from that point
   onwards. The event stream cannot do this for a single room currently.
   As a result, commenting room-scoped initial sync at this time.

The |initialSync|_ API contains the following keys:

``presence``
  Description:
    Contains a list of presence information for users the client is interested
    in.
  Format:
    A JSON array of ``m.presence`` events.

``end``
  Description:
    Contains an event stream token which can be used with the `Event Stream`_.
  Format:
    A string containing the event stream token.

``rooms``
  Description:
    Contains a list of room information for all rooms the client has joined,
    and limited room information on rooms the client has been invited to.
  Format:
    A JSON array containing Room Information JSON objects.

Room Information:
  Description:
    Contains all state events for the room, along with a limited amount of
    the most recent events, configured via the ``limit`` query
    parameter. Also contains additional keys with room metadata, such as the
    ``room_id`` and the client's ``membership`` to the room.
  Format:
    A JSON object with the following keys:
      ``room_id``
        A string containing the ID of the room being described.
      ``membership``
        A string representing the client's membership status in this room.
      ``messages``
        An event stream JSON object containing a ``chunk`` of recent
        events (both state events and non-state events), along with an ``end`` token.
      ``state``
        A JSON array containing all the current state events for this room.

Getting events for a room
~~~~~~~~~~~~~~~~~~~~~~~~~

There are several APIs provided to ``GET`` events for a room:

{{rooms_http_api}}

Redactions
~~~~~~~~~~
Since events are extensible it is possible for malicious users and/or servers
to add keys that are, for example offensive or illegal. Since some events
cannot be simply deleted, e.g. membership events, we instead 'redact' events.
This involves removing all keys from an event that are not required by the
protocol. This stripped down event is thereafter returned anytime a client or
remote server requests it. Redacting an event cannot be undone, allowing server
owners to delete the offending content from the databases. Events that have been
redacted include a ``redacted_because`` key whose value is the event that caused
it to be redacted, which may include a reason.

.. TODO
  Currently, only room admins can redact events by sending a ``m.room.redaction``
  event, but server admins also need to be able to redact events by a similar
  mechanism.

Upon receipt of a redaction event, the server should strip off any keys not in
the following list:

 - ``event_id``
 - ``type``
 - ``room_id``
 - ``user_id``
 - ``state_key``
 - ``prev_state``
 - ``content``

The content object should also be stripped of all keys, unless it is one of
one of the following event types:

 - ``m.room.member`` allows key ``membership``
 - ``m.room.create`` allows key ``creator``
 - ``m.room.join_rules`` allows key ``join_rule``
 - ``m.room.power_levels`` allows keys ``ban``, ``events``, ``events_default``,
   ``kick``, ``redact``, ``state_default``, ``users``, ``users_default``.
 - ``m.room.aliases`` allows key ``aliases``

.. TODO
  Need to update m.room.power_levels to reflect new power levels formatting

The redaction event should be added under the key ``redacted_because``. When a
client receives a redaction event it should change the redacted event
in the same way a server does.

Rooms
-----

Creation
~~~~~~~~
To create a room, a client has to use the |createRoom|_ API. There are various
options which can be set when creating a room:

``visibility``
  Type:
    String
  Optional:
    Yes
  Value:
    Either ``public`` or ``private``.
  Description:
    A ``public`` visibility indicates that the room will be shown in the public
    room list. A ``private`` visibility will hide the room from the public room
    list. Rooms default to ``private`` visibility if this key is not included.

``room_alias_name``
  Type:
    String
  Optional:
    Yes
  Value:
    The room alias localpart.
  Description:
    If this is included, a room alias will be created and mapped to the newly
    created room.  The alias will belong on the same home server which created
    the room, e.g.  ``!qadnasoi:domain.com >>> #room_alias_name:domain.com``

``name``
  Type:
    String
  Optional:
    Yes
  Value:
    The ``name`` value for the ``m.room.name`` state event.
  Description:
    If this is included, an ``m.room.name`` event will be sent into the room to
    indicate the name of the room. See `Room Events`_ for more information on
    ``m.room.name``.

``topic``
  Type:
    String
  Optional:
    Yes
  Value:
    The ``topic`` value for the ``m.room.topic`` state event.
  Description:
    If this is included, an ``m.room.topic`` event will be sent into the room
    to indicate the topic for the room. See `Room Events`_ for more information
    on ``m.room.topic``.

``invite``
  Type:
    List
  Optional:
    Yes
  Value:
    A list of user ids to invite.
  Description:
    This will tell the server to invite everyone in the list to the newly
    created room.

``creation_content``
  Type:
    Object
  Optional:
    Yes
  Value:
    Extra keys to be added to the content of the ``m.room.create``. The server
    will clober the following keys: ``creator``. Future versions of this
    spec may allow the server to clobber other keys if required.
  Description:
    Allows clients to add keys to the content of ``m.room.create``.

``preset``
  Type:
    String
  Optional:
    Yes
  Value:
    ``private_chat``, ``trusted_private_chat`` or ``public_chat``
  Description:
    Convenience parameter for setting various default state events based on a
    preset.

    Three presets are defined:

    - ``private_chat``: Sets the ``join_rules`` to ``invite`` and
      ``history_visibility`` to ``shared``
    - ``trusted_private_chat``: Set the ``join_rules`` to ``invite``,
      ``history_visibility`` to ``shared`` and gives all invitees the same
      power level as the creator.
    - ``public_chat``: Sets the ``join_rules`` to ``public`` and
      ``history_visibility`` to ``shared``

``initial_state``
  Type:
    List
  Optional:
    Yes
  Value:
    A list of state events to set in the new room.
  Description:
    Allows the user to override the default state events set in the new room.

    The expected format of the state events are an object with ``type``,
    ``state_key`` and ``content`` keys set.

    Takes precedence over events set by ``presets``, but gets overriden by
    ``name`` and ``topic`` keys.

Example::

  {
    "preset": "public_chat",
    "room_alias_name": "thepub",
    "name": "The Grand Duke Pub",
    "topic": "All about happy hour",
    "creation_content": {
        "m.federate": false
    }
  }

The home server will create a ``m.room.create`` event when the room is created,
which serves as the root of the PDU graph for this room. This event also has a
``creator`` key which contains the user ID of the room creator. It will also
generate several other events in order to manage permissions in this room. This
includes:

 - ``m.room.power_levels`` : Sets the power levels of users and required power
    levels.
 - ``m.room.join_rules`` : Whether the room is "invite-only" or not.

See `Room Events`_ for more information on these events.

Room aliases
~~~~~~~~~~~~
.. NOTE::
  This section is a work in progress.

Room aliases can be created by sending a ``PUT /directory/room/<room alias>``::

  {
    "room_id": <room id>
  }

They can be deleted by sending a ``DELETE /directory/room/<room alias>`` with
no content. Only some privileged users may be able to delete room aliases, e.g.
server admins, the creator of the room alias, etc. This specification does not
outline the privilege level required for deleting room aliases.

As room aliases are scoped to a particular home server domain name, it is
likely that a home server will reject attempts to maintain aliases on other
domain names. This specification does not provide a way for home servers to
send update requests to other servers.

Rooms store a *partial* list of room aliases via the ``m.room.aliases`` state
event. This alias list is partial because it cannot guarantee that the alias
list is in any way accurate or up-to-date, as room aliases can point to
different room IDs over time. Crucially, the aliases in this event are
**purely informational** and SHOULD NOT be treated as accurate. They SHOULD
be checked before they are used or shared with another user. If a room
appears to have a room alias of ``#alias:example.com``, this SHOULD be checked
to make sure that the room's ID matches the ``room_id`` returned from the
request.

Room aliases can be checked in the same way they are resolved; by sending a
``GET /directory/room/<room alias>``::

  {
    "room_id": <room id>,
    "servers": [ <domain>, <domain2>, <domain3> ]
  }

Home servers can respond to resolve requests for aliases on other domains than
their own by using the federation API to ask other domain name home servers.


Permissions
~~~~~~~~~~~
.. NOTE::
  This section is a work in progress.

Permissions for rooms are done via the concept of power levels - to do any
action in a room a user must have a suitable power level. Power levels are
stored as state events in a given room. The power levels required for operations
and the power levels for users are defined in ``m.room.power_levels``, where
both a default and specific users' power levels can be set.
By default all users have a power level of 0, other than the room creator whose
power level defaults to 100. Users can grant other users increased power levels
up to their own power level. For example, user A with a power level of 50 could
increase the power level of user B to a maximum of level 50. Power levels for
users are tracked per-room even if the user is not present in the room.
The keys contained in ``m.room.power_levels`` determine the levels required for
certain operations such as kicking, banning and sending state events. See
`m.room.power_levels`_ for more information.

Joining rooms
-------------
Users need to be a member of a room in order to send and receive events in that
room. There are several states in which a user may be, in relation to a room:

 - Unrelated (the user cannot send or receive events in the room)
 - Invited (the user has been invited to participate in the room, but is not
   yet participating)
 - Joined (the user can send and receive events in the room)
 - Banned (the user is not allowed to join the room)

Some rooms require that users be invited to it before they can join; others
allow anyone to join. Whether a given room is an "invite-only" room is
determined by the room config key ``m.room.join_rules``. It can have one of the
following values:

``public``
  This room is free for anyone to join without an invite.

``invite``
  This room can only be joined if you were invited.

{{membership_http_api}}

Leaving rooms
~~~~~~~~~~~~~
.. TODO-spec - HS deleting rooms they are no longer a part of. Not implemented.
  - This is actually Very Tricky. If all clients a HS is serving leave a room,
  the HS will no longer get any new events for that room, because the servers
  who get the events are determined on the *membership list*. There should
  probably be a way for a HS to lurk on a room even if there are 0 of their
  members in the room.
  - Grace period before deletion?
  - Under what conditions should a room NOT be purged?


A user can leave a room to stop receiving events for that room. A user must
have joined the room before they are eligible to leave the room. If the room is
an "invite-only" room, they will need to be re-invited before they can re-join
the room.  To leave a room, a request should be made to
|/rooms/<room_id>/leave|_ with::

  {}

Alternatively, the membership state for this user in this room can be modified
directly by sending the following request to
``/rooms/<room id>/state/m.room.member/<url encoded user id>``::

  {
    "membership": "leave"
  }

See the `Room events`_ section for more information on ``m.room.member``. Once a
user has left a room, that room will no longer appear on the |initialSync|_ API.
If all members in a room leave, that room becomes eligible for deletion.

Banning users in a room
~~~~~~~~~~~~~~~~~~~~~~~
A user may decide to ban another user in a room. 'Banning' forces the target
user to leave the room and prevents them from re-joining the room. A banned
user will not be treated as a joined user, and so will not be able to send or
receive events in the room. In order to ban someone, the user performing the
ban MUST have the required power level. To ban a user, a request should be made
to |/rooms/<room_id>/ban|_ with::

  {
    "user_id": "<user id to ban"
    "reason": "string: <reason for the ban>"
  }

Banning a user adjusts the banned member's membership state to ``ban`` and
adjusts the power level of this event to a level higher than the banned person.
Like with other membership changes, a user can directly adjust the target
member's state, by making a request to
``/rooms/<room id>/state/m.room.member/<user id>``::

  {
    "membership": "ban"
  }


Account operations
------------------

Registration
~~~~~~~~~~~~
This API endpoint uses the `User-Interactive Authentication API`_.

{{v2_registration_http_api}}

Login
~~~~~

{{login_http_api}}

Changing Password
~~~~~~~~~~~~~~~~~
This section refers to API Version 2. These API calls currently use the prefix
``/_matrix/client/v2_alpha``.

Request::

  POST $V2PREFIX/account/password

This API endpoint uses the User-Interactive Authentication API. An access token
should be submitted to this endpoint if the client has an active session. The
Home Server may change the flows available depending on whether a valid access
token is provided.

The body of the POST request is a JSON object containing:

new_password
  The new password for the account.

On success, an empty JSON object is returned.

The error code M_NOT_FOUND is returned if the user authenticated with a third
party identifier but the Home Server could not find a matching account in its
database.

Adding a Third Party Identifier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This section refers to API Version 2. These API calls currently use the prefix
``/_matrix/client/v2_alpha``.

Request::

  POST $V2PREFIX/account/3pid

Used to add a third party identifier to the user's account.

The body of the POST request is a JSON object containing:

threePidCreds
  An object containing third party identifier credentials.
bind
  Optional. A boolean indicating whether the Home Server should also bind this
  third party identifier to the account's matrix ID with the Identity Server. If
  supplied and true, the Home Server must bind the 3pid accordingly.

The third party identifier credentials object comprises:

id_server
  The colon-separated hostname and port of the Identity Server used to
  authenticate the third party identifier. If the port is the default, it and the
  colon should be omitted.
sid
  The session ID given by the Identity Server
client_secret
  The client secret used in the session with the Identity Server.

On success, the empty JSON object is returned.

May also return error codes:

M_THREEPID_AUTH_FAILED
  If the credentials provided could not be verified with the ID Server.

Fetching Currently Associated Third Party Identifiers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This section refers to API Version 2. These API calls currently use the prefix
``/_matrix/client/v2_alpha``.

Request::

  GET $V2PREFIX/account/3pid

This returns a list of third party identifiers that the Home Server has
associated with the user's account. This is *not* the same as the list of third
party identifiers bound to the user's Matrix ID in Identity Servers. Identifiers
in this list may be used by the Home Server as, for example, identifiers that it
will accept to reset the user's account password.

Returns a JSON object with the key ``threepids`` whose contents is an array of
objects with the following keys:

medium
  The medium of the 3pid (eg, ``email``)
address
  The textual address of the 3pid, eg. the email address


Profiles
--------

{{profile_http_api}}

Events on Change of Profile Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Because the profile display name and avatar information are likely to be used in
many places of a client's display, changes to these fields cause an automatic
propagation event to occur, informing likely-interested parties of the new
values. This change is conveyed using two separate mechanisms:

 - a ``m.room.member`` event is sent to every room the user is a member of,
   to update the ``displayname`` and ``avatar_url``.
 - a ``m.presence`` presence status update is sent, again containing the new
   values of the ``displayname`` and ``avatar_url`` keys, in addition to the
   required ``presence`` key containing the current presence state of the user.

Both of these should be done automatically by the home server when a user
successfully changes their display name or avatar URL fields.

Additionally, when home servers emit room membership events for their own
users, they should include the display name and avatar URL fields in these
events so that clients already have these details to hand, and do not have to
perform extra round trips to query it.

Security
--------

Rate limiting
~~~~~~~~~~~~~
Home servers SHOULD implement rate limiting to reduce the risk of being
overloaded. If a request is refused due to rate limiting, it should return a
standard error response of the form::

  {
    "errcode": "M_LIMIT_EXCEEDED",
    "error": "string",
    "retry_after_ms": integer (optional)
  }

The ``retry_after_ms`` key SHOULD be included to tell the client how long they
have to wait in milliseconds before they can try again.

.. TODO-spec
  - Surely we should recommend an algorithm for the rate limiting, rather than letting every
    homeserver come up with their own idea, causing totally unpredictable performance over
    federated rooms?


.. Links through the external API docs are below
.. =============================================

.. |createRoom| replace:: ``/createRoom``
.. _createRoom: /docs/api/client-server/#!/-rooms/create_room

.. |initialSync| replace:: ``/initialSync``
.. _initialSync: /docs/api/client-server/#!/-events/initial_sync

.. |/rooms/<room_id>/initialSync| replace:: ``/rooms/<room_id>/initialSync``
.. _/rooms/<room_id>/initialSync: /docs/api/client-server/#!/-rooms/get_room_sync_data

.. |login| replace:: ``/login``
.. _login: /docs/api/client-server/#!/-login

.. |register| replace:: ``/register``
.. _register: /docs/api/client-server/#!/-registration

.. |/rooms/<room_id>/messages| replace:: ``/rooms/<room_id>/messages``
.. _/rooms/<room_id>/messages: /docs/api/client-server/#!/-rooms/get_messages

.. |/rooms/<room_id>/members| replace:: ``/rooms/<room_id>/members``
.. _/rooms/<room_id>/members: /docs/api/client-server/#!/-rooms/get_members

.. |/rooms/<room_id>/state| replace:: ``/rooms/<room_id>/state``
.. _/rooms/<room_id>/state: /docs/api/client-server/#!/-rooms/get_state_events

.. |/rooms/<room_id>/send/<event_type>| replace:: ``/rooms/<room_id>/send/<event_type>``
.. _/rooms/<room_id>/send/<event_type>: /docs/api/client-server/#!/-rooms/send_non_state_event

.. |/rooms/<room_id>/state/<event_type>/<state_key>| replace:: ``/rooms/<room_id>/state/<event_type>/<state_key>``
.. _/rooms/<room_id>/state/<event_type>/<state_key>: /docs/api/client-server/#!/-rooms/send_state_event

.. |/rooms/<room_id>/invite| replace:: ``/rooms/<room_id>/invite``
.. _/rooms/<room_id>/invite: /docs/api/client-server/#!/-rooms/invite

.. |/rooms/<room_id>/join| replace:: ``/rooms/<room_id>/join``
.. _/rooms/<room_id>/join: /docs/api/client-server/#!/-rooms/join_room

.. |/rooms/<room_id>/leave| replace:: ``/rooms/<room_id>/leave``
.. _/rooms/<room_id>/leave: /docs/api/client-server/#!/-rooms/leave

.. |/rooms/<room_id>/ban| replace:: ``/rooms/<room_id>/ban``
.. _/rooms/<room_id>/ban: /docs/api/client-server/#!/-rooms/ban

.. |/join/<room_alias_or_id>| replace:: ``/join/<room_alias_or_id>``
.. _/join/<room_alias_or_id>: /docs/api/client-server/#!/-rooms/join

.. _`Event Stream`: /docs/api/client-server/#!/-events/get_event_stream

