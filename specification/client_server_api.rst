.. Copyright 2016 OpenMarket Ltd
..
.. Licensed under the Apache License, Version 2.0 (the "License");
.. you may not use this file except in compliance with the License.
.. You may obtain a copy of the License at
..
..     http://www.apache.org/licenses/LICENSE-2.0
..
.. Unless required by applicable law or agreed to in writing, software
.. distributed under the License is distributed on an "AS IS" BASIS,
.. WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
.. See the License for the specific language governing permissions and
.. limitations under the License.

Client-Server API
=================

The client-server API provides a simple lightweight API to let clients send
messages, control rooms and synchronise conversation history. It is designed to
support both lightweight clients which store no state and lazy-load data from
the server as required - as well as heavyweight clients which maintain a full
local persistent copy of server state.

.. contents:: Table of Contents
.. sectnum::

Changelog
---------

.. topic:: Version: %CLIENT_RELEASE_LABEL%
{{client_server_changelog}}

This version of the specification is generated from
`matrix-doc <https://github.com/matrix-org/matrix-doc>`_ as of Git commit
`{{git_version}} <https://github.com/matrix-org/matrix-doc/tree/{{git_rev}}>`_.

For the full historical changelog, see
https://github.com/matrix-org/matrix-doc/blob/master/changelogs/client_server.rst

If this is an unstable snapshot, any changes since the last release may be
viewed using ``git log``.

Other versions of this specification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following other versions are also available, in reverse chronological order:

- `HEAD <https://matrix.org/speculator/spec/HEAD/client_server/unstable.html>`_: Includes all changes since the latest versioned release.
- `r0.2.0 <https://matrix.org/docs/spec/client_server/r0.2.0.html>`_
- `r0.1.0 <https://matrix.org/docs/spec/client_server/r0.1.0.html>`_
- `r0.0.1 <https://matrix.org/docs/spec/r0.0.1/client_server.html>`_
- `r0.0.0 <https://matrix.org/docs/spec/r0.0.0/client_server.html>`_
- `Legacy <https://matrix.org/docs/spec/legacy/#client-server-api>`_: The last draft before the spec was formally released in version r0.0.0.


API Standards
-------------

.. TODO
  Need to specify any HMAC or access_token lifetime/ratcheting tricks
  We need to specify capability negotiation for extensible transports

The mandatory baseline for client-server communication in Matrix is exchanging
JSON objects over HTTP APIs. HTTPS is recommended for communication, although
HTTP may be supported as a fallback to support basic
HTTP clients. More efficient optional transports
will in future be supported as optional extensions - e.g. a
packed binary encoding over stream-cipher encrypted TCP socket for
low-bandwidth/low-roundtrip mobile usage. For the default HTTP transport, all
API calls use a Content-Type of ``application/json``.  In addition, all strings
MUST be encoded as UTF-8. Clients are authenticated using opaque
``access_token`` strings (see `Client Authentication`_ for details), passed as a
query string parameter on all requests.

The names of the API endponts for the HTTP transport follow a convention of
using underscores to separate words (for example ``/delete_devices``). The key
names in JSON objects passed over the API also follow this convention.

.. NOTE::
   There are a few historical exceptions to this rule, such as
   ``/createRoom``. A future version of this specification will address the
   inconsistency.


Any errors which occur at the Matrix API level MUST return a "standard error
response". This is a JSON object which looks like:

.. code:: json

  {
    "errcode": "<error code>",
    "error": "<error message>"
  }

The ``error`` string will be a human-readable error message, usually a sentence
explaining what went wrong. The ``errcode`` string will be a unique string
which can be used to handle an error message e.g. ``M_FORBIDDEN``. These error
codes should have their namespace first in ALL CAPS, followed by a single _ to
ease separating the namespace from the error code. For example, if there was a
custom namespace ``com.mydomain.here``, and a
``FORBIDDEN`` code, the error code should look like
``COM.MYDOMAIN.HERE_FORBIDDEN``. There may be additional keys depending on the
error, but the keys ``error`` and ``errcode`` MUST always be present.

Some standard error codes are below:

:``M_FORBIDDEN``:
  Forbidden access, e.g. joining a room without permission, failed login.

:``M_UNKNOWN_TOKEN``:
  The access token specified was not recognised.

:``M_BAD_JSON``:
  Request contained valid JSON, but it was malformed in some way, e.g. missing
  required keys, invalid values for keys.

:``M_NOT_JSON``:
  Request did not contain valid JSON.

:``M_NOT_FOUND``:
  No resource was found for this request.

:``M_LIMIT_EXCEEDED``:
  Too many requests have been sent in a short period of time. Wait a while then
  try again.

Some requests have unique error codes:

:``M_USER_IN_USE``:
  Encountered when trying to register a user ID which has been taken.

:``M_INVALID_USERNAME``:
  Encountered when trying to register a user ID which is not valid.

:``M_ROOM_IN_USE``:
  Sent when the room alias given to the ``createRoom`` API is already in use.

:``M_INVALID_ROOM_STATE``:
  Sent when the intial state given to the ``createRoom`` API is invalid.

:``M_BAD_PAGINATION``:
  Encountered when specifying bad pagination query parameters.

:``M_THREEPID_IN_USE``:
  Sent when a threepid given to an API cannot be used because the same threepid is already in use.

:``M_THREEPID_NOT_FOUND``:
  Sent when a threepid given to an API cannot be used because no record matching the threepid was found.

:``M_SERVER_NOT_TRUSTED``:
  The client's request used a third party server, eg. ID server, that this server does not trust.

.. _sect:txn_ids:

The client-server API typically uses ``HTTP PUT`` to submit requests with a
client-generated transaction identifier. This means that these requests are
idempotent. The scope of a transaction identifier is a particular access token.
It **only** serves to identify new
requests from retransmits. After the request has finished, the ``{txnId}``
value should be changed (how is not specified; a monotonically increasing
integer is recommended).

Some API endpoints may allow or require the use of ``POST`` requests without a
transaction ID. Where this is optional, the use of a ``PUT`` request is strongly
recommended.

{{versions_cs_http_api}}

Client Authentication
---------------------

Most API endpoints require the user to identify themselves by presenting
previously obtained credentials in the form of an ``access_token`` query
parameter. An access token is typically obtained via the `Login`_ or
`Registration`_ processes.

When credentials are required but missing or invalid, the HTTP call will
return with a status of 401 and the error code, ``M_MISSING_TOKEN`` or
``M_UNKNOWN_TOKEN`` respectively.

.. NOTE::

   This specification does not mandate a particular format for the access
   token. Clients should treat it as an opaque byte sequence. Servers are free
   to choose an appropriate format. Server implementors may like to investigate
   `macaroons <macaroon_>`_.

Relationship between access tokens and devices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Client `devices`_ are closely related to access tokens.  Matrix servers should
record which device each access token is assigned to, so that subsequent
requests can be handled correctly.

By default, the `Login`_ and `Registration`_ processes auto-generate a new
``device_id``. A client is also free to generate its own ``device_id`` or,
provided the user remains the same, reuse a device: in ether case the client
should pass the ``device_id`` in the request body. If the client sets the
``device_id``, the server will invalidate any access token previously assigned
to that device. There is therefore at most one active access token assigned to
each device at any one time.

User-Interactive Authentication API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Overview
<<<<<<<<

Some API endpoints require authentication that
interacts with the user. The homeserver may provide many different ways of
authenticating, such as user/password auth, login via a social network (OAuth2),
login by confirming a token sent to their email address, etc. This specification
does not define how homeservers should authorise their users but instead
defines the standard interface which implementations should follow so that ANY
client can login to ANY homeserver.

The process takes the form of one or more 'stages'. At each stage the client
submits a set of data for a given authentication type and awaits a response
from the server, which will either be a final success or a request to perform
an additional stage. This exchange continues until the final success.

For each endpoint, a server offers one or more 'flows' that the client can use
to authenticate itself. Each flow comprises a series of stages, as described
above. The client is free to choose which flow it follows. When all stages in a
flow are complete, authentication is complete and the API call succeeds.

User-interactive API in the REST API
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

In the REST API described in this specification, authentication works by the
client and server exchanging JSON dictionaries. The server indicates what
authentication data it requires via the body of an HTTP 401 response, and the
client submits that authentication data via the ``auth`` request parameter.

A client should first make a request with no ``auth`` parameter [#]_. The
homeserver returns an HTTP 401 response, with a JSON body, as follows:

.. code::

  HTTP/1.1 401 Unauthorized
  Content-Type: application/json

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
  order to use a given type of authentication. For each authentication type
  presented, that type may be present as a key in this dictionary. For example,
  the public part of an OAuth client ID could be given here.
session
  This is a session identifier that the client must pass back to the home
  server, if one is provided, in subsequent attempts to authenticate in the same
  API call.

The client then chooses a flow and attempts to complete one of the stages. It
does this by resubmitting the same request with the addition of an ``auth``
key in the object that it submits. This dictionary contains a ``type`` key whose
value is the name of the authentication type that the client is attempting to complete.
It must also contain a ``session`` key with the value of the session key given
by the homeserver, if one was given. It also contains other keys dependent on
the auth type being attempted. For example, if the client is attempting to
complete auth type ``example.type.foo``, it might submit something like this:

.. code::

  POST /_matrix/client/r0/endpoint HTTP/1.1
  Content-Type: application/json

  {
    "a_request_parameter": "something",
    "another_request_parameter": "something else",
    "auth": {
        "type": "example.type.foo",
        "session": "xxxxxx",
        "example_credential": "verypoorsharedsecret"
    }
  }

If the homeserver deems the authentication attempt to be successful but still
requires more stages to be completed, it returns HTTP status 401 along with the
same object as when no authentication was attempted, with the addition of the
``completed`` key which is an array of auth types the client has completed
successfully:

.. code::

  HTTP/1.1 401 Unauthorized
  Content-Type: application/json

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

Individual stages may require more than one request to complete, in which case
the response will be as if the request was unauthenticated with the addition of
any other keys as defined by the auth type.

If the homeserver decides that an attempt on a stage was unsuccessful, but the
client may make a second attempt, it returns the same HTTP status 401 response
as above, with the addition of the standard ``errcode`` and ``error`` fields
describing the error. For example:

.. code::

  HTTP/1.1 401 Unauthorized
  Content-Type: application/json

  {
    "errcode": "M_FORBIDDEN",
    "error": "Invalid password",
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

If the request fails for a reason other than authentication, the server returns an error
message in the standard format. For example:

.. code::

  HTTP/1.1 400 Bad request
  Content-Type: application/json

  {
    "errcode": "M_EXAMPLE_ERROR",
    "error": "Something was wrong"
  }

If the client has completed all stages of a flow, the homeserver performs the
API call and returns the result as normal.

Some authentication types may be completed by means other than through the
Matrix client, for example, an email confirmation may be completed when the user
clicks on the link in the email. In this case, the client retries the request
with an auth dict containing only the session key. The response to this will be
the same as if the client were attempting to complete an auth state normally,
i.e. the request will either complete or request auth, with the presence or
absence of that auth type in the 'completed' array indicating whether
that stage is complete.

.. [#] A request to an endpoint that uses User-Interactive Authentication never
       succeeds without auth. Homeservers may allow requests that don't require
       auth by offering a stage with only the ``m.login.dummy`` auth type, but
       they must still give a 401 response to requests with no auth data.

Example
+++++++
At a high level, the requests made for an API call completing an auth flow with
three stages will resemble the following diagram::

   _______________________
  |       Stage 0         |
  | No auth               |
  |  ___________________  |
  | |_Request_1_________| | <-- Returns "session" key which is used throughout.
  |_______________________|
            |
            |
   _________V_____________
  |       Stage 1         |
  | type: "<auth type1>"  |
  |  ___________________  |
  | |_Request_1_________| |
  |_______________________|
            |
            |
   _________V_____________
  |       Stage 2         |
  | type: "<auth type2>"  |
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
  | type: "<auth type3>"  |
  |  ___________________  |
  | |_Request_1_________| | <-- Returns API response
  |_______________________|


Authentication types
++++++++++++++++++++

This specification defines the following auth types:
 - ``m.login.password``
 - ``m.login.recaptcha``
 - ``m.login.oauth2``
 - ``m.login.email.identity``
 - ``m.login.token``
 - ``m.login.dummy``

Password-based
<<<<<<<<<<<<<<
:Type:
  ``m.login.password``
:Description:
  The client submits a username and secret password, both sent in plain-text.

To use this authentication type, clients should submit an auth dict as follows:

.. code:: json

  {
    "type": "m.login.password",
    "user": "<user_id or user localpart>",
    "password": "<password>",
    "session": "<session ID>"
  }

Alternatively reply using a 3pid bound to the user's account on the homeserver
using the |/account/3pid|_ API rather then giving the ``user`` explicitly as
follows:

.. code:: json

  {
    "type": "m.login.password",
    "medium": "<The medium of the third party identifier. Must be 'email'>",
    "address": "<The third party address of the user>",
    "password": "<password>",
    "session": "<session ID>"
  }

In the case that the homeserver does not know about the supplied 3pid, the
homeserver must respond with 403 Forbidden.

Google ReCaptcha
<<<<<<<<<<<<<<<<
:Type:
  ``m.login.recaptcha``
:Description:
  The user completes a Google ReCaptcha 2.0 challenge

To use this authentication type, clients should submit an auth dict as follows:

.. code:: json

  {
    "type": "m.login.recaptcha",
    "response": "<captcha response>",
    "session": "<session ID>"
  }

Token-based
<<<<<<<<<<<
:Type:
  ``m.login.token``
:Description:
  The client submits a login token.

To use this authentication type, clients should submit an auth dict as follows:

.. code:: json

  {
    "type": "m.login.token",
    "token": "<token>",
    "txn_id": "<client generated nonce>",
    "session": "<session ID>"
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

The server must encode the user id in the ``token``. There is therefore no need
for the client to submit a separate username.

OAuth2-based
<<<<<<<<<<<<
:Type:
  ``m.login.oauth2``
:Description:
  Authentication is supported via OAuth2 URLs. This login consists of multiple
  requests.
:Parameters:
  ``uri``: Authorization Request URI OR service selection URI. Both contain an
  encoded ``redirect URI``.

The homeserver acts as a 'confidential' client for the purposes of OAuth2.  If
the uri is a ``service selection URI``, it MUST point to a webpage which prompts
the user to choose which service to authorize with. On selection of a service,
this MUST link through to an ``Authorization Request URI``. If there is only one
service which the homeserver accepts when logging in, this indirection can be
skipped and the "uri" key can be the ``Authorization Request URI``.

The client then visits the ``Authorization Request URI``, which then shows the
OAuth2 Allow/Deny prompt. Hitting 'Allow' redirects to the ``redirect URI`` with
the auth code. Homeservers can choose any path for the ``redirect URI``. Once
the OAuth flow has completed, the client retries the request with the session
only, as above.

Email-based (identity server)
<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
:Type:
  ``m.login.email.identity``
:Description:
  Authentication is supported by authorising an email address with an identity
  server.

Prior to submitting this, the client should authenticate with an identity
server. After authenticating, the session information should be submitted to
the homeserver.

To use this authentication type, clients should submit an auth dict as follows:

.. code:: json

  {
    "type": "m.login.email.identity",
    "threepidCreds": [
      {
        "sid": "<identity server session id>",
        "client_secret": "<identity server client secret>",
        "id_server": "<url of identity server authed with, e.g. 'matrix.org:8090'>"
      }
    ],
    "session": "<session ID>"
  }

Dummy Auth
<<<<<<<<<<
:Type:
  ``m.login.dummy``
:Description:
  Dummy authentication always succeeds and requires no extra parameters. Its
  purpose is to allow servers to not require any form of User-Interactive
  Authentication to perform a request.

To use this authentication type, clients should submit an auth dict with just
the type and session, if provided:

.. code:: json

  {
    "type": "m.login.dummy",
    "session": "<session ID>"
  }


Fallback
++++++++
Clients cannot be expected to be able to know how to process every single login
type. If a client does not know how to handle a given login type, it can direct
the user to a web browser with the URL of a fallback page which will allow the
user to complete that login step out-of-band in their web browser. The URL it
should open is::

  /_matrix/client/%CLIENT_MAJOR_VERSION%/auth/<auth type>/fallback/web?session=<session ID>

Where ``auth type`` is the type name of the stage it is attempting and
``session ID`` is the ID of the session given by the homeserver.

This MUST return an HTML page which can perform this authentication stage. This
page must use the following JavaScript when the authentication has been
completed:

.. code:: javascript

   if (window.onAuthDone) {
       window.onAuthDone();
   } else if (window.opener && window.opener.postMessage) {
       window.opener.postMessage("authDone", "*");
   }

This allows the client to either arrange for the global function ``onAuthDone``
to be defined in an embedded browser, or to use the HTML5 `cross-document
messaging <https://www.w3.org/TR/webmessaging/#web-messaging>`_ API, to receive
a notification that the authentication stage has been completed.

Once a client receives the notificaton that the authentication stage has been
completed, it should resubmit the request with an auth dict with just the
session ID:

.. code:: json

  {
    "session": "<session ID>"
  }


Example
<<<<<<<
A client webapp might use the following javascript to open a popup window which will
handle unknown login types:

.. code:: javascript

  /**
   * Arguments:
   *     homeserverUrl: the base url of the homeserver (eg "https://matrix.org")
   *
   *     apiEndpoint: the API endpoint being used (eg
   *        "/_matrix/client/%CLIENT_MAJOR_VERSION%/account/password")
   *
   *     loginType: the loginType being attempted (eg "m.login.recaptcha")
   *
   *     sessionID: the session ID given by the homeserver in earlier requests
   *
   *     onComplete: a callback which will be called with the results of the request
   */
  function unknownLoginType(homeserverUrl, apiEndpoint, loginType, sessionID, onComplete) {
      var popupWindow;

      var eventListener = function(ev) {
          // check it's the right message from the right place.
          if (ev.data !== "authDone" || ev.origin !== homeserverUrl) {
              return;
          }

          // close the popup
          popupWindow.close();
          window.removeEventListener("message", eventListener);

          // repeat the request
          var requestBody = {
              auth: {
                  session: sessionID,
              },
          };

          request({
              method:'POST', url:apiEndpint, json:requestBody,
          }, onComplete);
      };

      window.addEventListener("message", eventListener);

      var url = homeserverUrl +
          "/_matrix/client/%CLIENT_MAJOR_VERSION%/auth/" +
          encodeURIComponent(loginType) +
          "/fallback/web?session=" +
          encodeURIComponent(sessionID);


     popupWindow = window.open(url);
  }


Login
~~~~~

A client can obtain access tokens using the ``/login`` API.

Note that this endpoint does `not` currently use the user-interactive
authentication API.

For a simple username/password login, clients should submit a ``/login``
request as follows:

.. code:: json

  {
    "type": "m.login.password",
    "user": "<user_id or user localpart>",
    "password": "<password>"
  }

Alternatively, a client can use a 3pid bound to the user's account on the
homeserver using the |/account/3pid|_ API rather then giving the ``user``
explicitly, as follows:

.. code:: json

  {
    "type": "m.login.password",
    "medium": "<The medium of the third party identifier. Must be 'email'>",
    "address": "<The third party address of the user>",
    "password": "<password>"
  }

In the case that the homeserver does not know about the supplied 3pid, the
homeserver must respond with ``403 Forbidden``.

To log in using a login token, clients should submit a ``/login`` request as
follows:

.. code:: json

  {
    "type": "m.login.token",
    "token": "<login token>"
  }

As with `token-based`_ interactive login, the ``token`` must encode the
user id. In the case that the token is not valid, the homeserver must respond
with ``403 Forbidden`` and an error code of ``M_FORBIDDEN``.

{{login_cs_http_api}}

{{logout_cs_http_api}}

Login Fallback
<<<<<<<<<<<<<<

If a client does not recognize any or all login flows it can use the fallback
login API::

    GET /_matrix/static/client/login/

This returns an HTML and JavaScript page which can perform the entire login
process. The page will attempt to call the JavaScript function
``window.onLogin`` when login has been successfully completed.

.. _Registration:

Account registration and management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

{{registration_cs_http_api}}

Notes on password management
++++++++++++++++++++++++++++

.. WARNING::
  Clients SHOULD enforce that the password provided is suitably complex. The
  password SHOULD include a lower-case letter, an upper-case letter, a number
  and a symbol and be at a minimum 8 characters in length. Servers MAY reject
  weak passwords with an error code ``M_WEAK_PASSWORD``.


Adding Account Administrative Contact Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A homeserver may keep some contact information for administrative use.
This is independent of any information kept by any Identity Servers.

{{administrative_contact_cs_http_api}}

Pagination
----------

.. NOTE::
  The paths referred to in this section are not actual endpoints. They only
  serve as examples to explain how pagination functions.

Pagination is the process of dividing a dataset into multiple discrete pages.
Matrix makes use of pagination to allow clients to view extremely large datasets.
These datasets are not limited to events in a room (for example clients may want
to paginate a list of rooms in addition to events within those rooms). Regardless
of *what* is being paginated, there is a common underlying API which is used to
to give clients a consistent way of selecting subsets of a potentially changing
dataset. Requests pass in ``from``, ``to``, ``dir`` and ``limit`` parameters
which describe where to read from the stream. ``from`` and ``to`` are opaque
textual 'stream tokens' which describe the current position in the dataset.
The ``dir`` parameter is an enum representing the direction of events to return:
either ``f`` orwards or ``b`` ackwards. The response returns new ``start`` and
``end`` stream token values which can then be passed to subsequent requests to
continue pagination. Not all endpoints will make use of all the parameters
outlined here: see the specific endpoint in question for more information.

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
  dir:
    f|b - The direction to return events in. Typically this is ``b`` to paginate
    backwards in time.

'START' and 'END' are placeholder values used in these examples to describe the
start and end of the dataset respectively.

Unless specified, the default pagination parameters are ``from=START``,
``to=END``, without a limit set.

For example, if an endpoint had events E1 -> E15. The client wants the last 5
events and doesn't know any previous events::

    S                                                    E
    |-E1-E2-E3-E4-E5-E6-E7-E8-E9-E10-E11-E12-E13-E14-E15-|
    |                               |                    |
    |                          _____|  <--backwards--    |
    |__________________       |         |        ________|
                       |      |         |        |
     GET /somepath?to=START&limit=5&dir=b&from=END
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
                             GET /roomslist?from=9&to=END&limit=5
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

Filtering
---------

Filters can be created on the server and can be passed as as a parameter to APIs
which return events. These filters alter the data returned from those APIs.
Not all APIs accept filters.

{{filter_cs_http_api}}

Events
------

.. _sect:events:

The model of conversation history exposed by the client-server API can be
considered as a list of events. The server 'linearises' the
eventually-consistent event graph of events into an 'event stream' at any given
point in time::

  [E0]->[E1]->[E2]->[E3]->[E4]->[E5]



Types of room events
~~~~~~~~~~~~~~~~~~~~

Room events are split into two categories:

:State Events:
  These are events which update the metadata state of the room (e.g. room topic,
  room membership etc). State is keyed by a tuple of event ``type`` and a
  ``state_key``. State in the room with the same key-tuple will be overwritten.

:Message events:
  These are events which describe transient "once-off" activity in a room:
  typically communication such as sending an instant message or setting up a
  VoIP call.

This specification outlines several events, all with the event type prefix
``m.``. (See `Room Events`_ for the m. event specification.) However,
applications may wish to add their own type of event, and this can be achieved
using the REST API detailed in the following sections. If new events are added,
the event ``type`` key SHOULD follow the Java package naming convention,
e.g. ``com.example.myapp.event``.  This ensures event types are suitably
namespaced for each application and reduces the risk of clashes.


Syncing
~~~~~~~

To read events, the intended flow of operation is for clients to first call the
|/sync|_ API without a ``since`` parameter. This returns the most recent
message events for each room, as well as the state of the room at the start of
the returned timeline. The response also includes a ``next_batch`` field, which
should be used as the value of the ``since`` parameter in the next call to
``/sync``. Finally, the response includes, for each room, a ``prev_batch``
field, which can be passed as a ``start`` parameter to the
|/rooms/<room_id>/messages|_ API to retrieve earlier messages.

You can visualise the range of events being returned as::

  [E0]->[E1]->[E2]->[E3]->[E4]->[E5]
             ^                      ^
             |                      |
       prev_batch: '1-2-3'        next_batch: 'a-b-c'


Clients then receive new events by "long-polling" the homeserver via the
``/sync`` API, passing the value of the ``next_batch`` field from the response
to the previous call as the ``since`` parameter. This involves specifying a
timeout in the request which will hold open the HTTP connection for a short
period of time waiting for new events, returning early if an event occurs. Only
the ``/sync`` API (and the deprecated ``/events`` API) support long-polling in
this way.

The response for such an incremental sync can be visualised as::

  [E0]->[E1]->[E2]->[E3]->[E4]->[E5]->[E6]
                                    ^     ^
                                    |     |
                                    |  next_batch: 'x-y-z'
                                  prev_batch: 'a-b-c'


Normally, all new events which are visible to the client will appear in the
response to the ``/sync`` API. However, if a large number of events arrive
between calls to ``/sync``, a "limited" timeline is returned, containing only
the most recent message events. A state "delta" is also returned, summarising
any state changes in the omitted part of the timeline. The client may therefore
end up with "gaps" in its knowledge of the message timeline. The client can
fill these gaps using the |/rooms/<room_id>/messages|_ API. This situation
looks like this::

                                     | gap |
                                     | <-> |
   [E0]->[E1]->[E2]->[E3]->[E4]->[E5]->[E6]->[E7]->[E8]->[E9]->[E10]
                                           ^                        ^
                                           |                        |
                                      prev_batch: 'd-e-f'       next_batch: 'u-v-w'


.. Warning::
  Events are ordered in this API according to the arrival time of the event on
  the homeserver. This can conflict with other APIs which order events based on
  their partial ordering in the event graph. This can result in duplicate events
  being received (once per distinct API called). Clients SHOULD de-duplicate
  events based on the event ID when this happens.

.. NOTE::

  The ``/sync`` API returns a ``state`` list which is separate from the
  ``timeline``. This ``state`` list allows clients to keep their model of the
  room state in sync with that on the server. In the case of an initial
  (``since``-less) sync, the ``state`` list represents the complete state of
  the room at the **start** of the returned timeline (so in the case of a
  recently-created room whose state fits entirely in the ``timeline``, the
  ``state`` list will be empty).

  In the case of an incremental sync, the ``state`` list gives a delta
  between the state of the room at the ``since`` parameter and that at the
  start of the returned ``timeline``. (It will therefore be empty
  unless the timeline was ``limited``.)

  In both cases, it should be noted that the events returned in the ``state``
  list did **not** necessarily take place just before the returned
  ``timeline``, so clients should not display them to the user in the timeline.

.. admonition:: Rationale

  An early design of this specification made the ``state`` list represent the
  room state at the end of the returned timeline, instead of the start. This
  was unsatisfactory because it led to duplication of events between the
  ``state`` list and the ``timeline``, but more importantly, it made it
  difficult for clients to show the timeline correctly.

  In particular, consider a returned timeline [M0, S1, M2], where M0 and M2 are
  both messages sent by the same user, and S1 is a state event where that user
  changes their displayname. If the ``state`` list represents the room state at
  the end of the timeline, the client must take a copy of the state dictionary,
  and *rewind* S1, in order to correctly calculate the display name for M0.

.. TODO-spec
  Do we ever support streaming requests? Why not websockets?

{{sync_cs_http_api}}

{{old_sync_cs_http_api}}


Getting events for a room
~~~~~~~~~~~~~~~~~~~~~~~~~

There are several APIs provided to ``GET`` events for a room:

{{rooms_cs_http_api}}

{{message_pagination_cs_http_api}}

{{room_initial_sync_cs_http_api}}


Sending events to a room
~~~~~~~~~~~~~~~~~~~~~~~~

{{room_state_cs_http_api}}


**Examples**

Valid requests look like::

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

{{room_send_cs_http_api}}


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


Upon receipt of a redaction event, the server should strip off any keys not in
the following list:

- ``event_id``
- ``type``
- ``room_id``
- ``sender``
- ``state_key``
- ``prev_content``
- ``content``

The content object should also be stripped of all keys, unless it is one of
one of the following event types:

- ``m.room.member`` allows key ``membership``
- ``m.room.create`` allows key ``creator``
- ``m.room.join_rules`` allows key ``join_rule``
- ``m.room.power_levels`` allows keys ``ban``, ``events``, ``events_default``,
  ``kick``, ``redact``, ``state_default``, ``users``, ``users_default``.
- ``m.room.aliases`` allows key ``aliases``

The server should add the event causing the redaction to the ``unsigned``
property of the redacted event, under the ``redacted_because`` key. When a
client receives a redaction event it should change the redacted event in the
same way a server does.

Events
++++++

{{m_room_redaction_event}}

Client behaviour
++++++++++++++++

{{redaction_cs_http_api}}

Rooms
-----

Creation
~~~~~~~~
The homeserver will create an ``m.room.create`` event when a room is created,
which serves as the root of the event graph for this room. This event also has a
``creator`` key which contains the user ID of the room creator. It will also
generate several other events in order to manage permissions in this room. This
includes:

- ``m.room.power_levels`` : Sets the power levels of users and required power
   levels for various actions within the room such as sending events.
- ``m.room.join_rules`` : Whether the room is "invite-only" or not.

See `Room Events`_ for more information on these events. To create a room, a
client has to use the following API.

{{create_room_cs_http_api}}

Room aliases
~~~~~~~~~~~~

Servers may host aliases for rooms with human-friendly names. Aliases take the
form ``#friendlyname:server.name``.

As room aliases are scoped to a particular homeserver domain name, it is
likely that a homeserver will reject attempts to maintain aliases on other
domain names. This specification does not provide a way for homeservers to
send update requests to other servers. However, homeservers MUST handle
``GET`` requests to resolve aliases on other servers; they should do this using
the federation API if necessary.

Rooms store a *partial* list of room aliases via the ``m.room.aliases`` state
event. This alias list is partial because it cannot guarantee that the alias
list is in any way accurate or up-to-date, as room aliases can point to
different room IDs over time. Crucially, the aliases in this event are
**purely informational** and SHOULD NOT be treated as accurate. They SHOULD
be checked before they are used or shared with another user. If a room
appears to have a room alias of ``#alias:example.com``, this SHOULD be checked
to make sure that the room's ID matches the ``room_id`` returned from the
request.

{{directory_cs_http_api}}


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

Clients may wish to assign names to particular power levels. A suggested mapping is as follows:
- 0   User
- 50  Moderator
- 100 Admin


Room membership
~~~~~~~~~~~~~~~
Users need to be a member of a room in order to send and receive events in that
room. There are several states in which a user may be, in relation to a room:

- Unrelated (the user cannot send or receive events in the room)
- Invited (the user has been invited to participate in the room, but is not
  yet participating)
- Joined (the user can send and receive events in the room)
- Banned (the user is not allowed to join the room)

There is an exception to the requirement that a user join a room before sending
events to it: users may send an ``m.room.member`` event to a room with
``content.membership`` set to ``leave`` to reject an invitation if they have
currently been invited to a room but have not joined it.

Some rooms require that users be invited to it before they can join; others
allow anyone to join. Whether a given room is an "invite-only" room is
determined by the room config key ``m.room.join_rules``. It can have one of the
following values:

``public``
  This room is free for anyone to join without an invite.

``invite``
  This room can only be joined if you were invited.

The allowable state transitions of membership are::

                                       /ban
                  +------------------------------------------------------+
                  |                                                      |
                  |  +----------------+  +----------------+              |
                  |  |    /leave      |  |                |              |
                  |  |                v  v                |              |
    /invite    +--------+           +-------+             |              |
  ------------>| invite |<----------| leave |----+        |              |
               +--------+  /invite  +-------+    |        |              |
                 |                   |    ^      |        |              |
                 |                   |    |      |        |              |
           /join |   +---------------+    |      |        |              |
                 |   | /join if           |      |        |              |
                 |   | join_rules         |      | /ban   | /unban       |
                 |   | public      /leave |      |        |              |
                 v   v               or   |      |        |              |
               +------+            /kick  |      |        |              |
  ------------>| join |-------------------+      |        |              |
   /join       +------+                          v        |              |
   if             |                           +-----+     |              |
   join_rules     +-------------------------->| ban |-----+              |
   public                   /ban              +-----+                    |
                                                ^ ^                      |
                                                | |                      |
  ----------------------------------------------+ +----------------------+
                  /ban


Joining rooms
+++++++++++++

{{inviting_cs_http_api}}

{{joining_cs_http_api}}

Leaving rooms
+++++++++++++
A user can leave a room to stop receiving events for that room. A user must
have been invited to or have joined the room before they are eligible to leave
the room. Leaving a room to which the user has been invited rejects the invite.
Once a user leaves a room, it will no longer appear in the response to the
|/sync|_ API unless it is explicitly requested via a filter with the
``include_leave`` field set to ``true``.

Whether or not they actually joined the room, if the room is an "invite-only"
room the user will need to be re-invited before they can re-join the room.

A user can also forget a room which they have left. Rooms which have been
forgotten will never appear the response to the |/sync|_ API, until the user
re-joins or is re-invited.

A user may wish to force another user to leave a room. This can be done by
'kicking' the other user. To do so, the user performing the kick MUST have the
required power level. Once a user has been kicked, the behaviour is the same as
if they had left of their own accord. In particular, the user is free to
re-join if the room is not "invite-only".

{{leaving_cs_http_api}}

{{kicking_cs_http_api}}

Banning users in a room
+++++++++++++++++++++++
A user may decide to ban another user in a room. 'Banning' forces the target
user to leave the room and prevents them from re-joining the room. A banned
user will not be treated as a joined user, and so will not be able to send or
receive events in the room. In order to ban someone, the user performing the
ban MUST have the required power level. To ban a user, a request should be made
to |/rooms/<room_id>/ban|_ with::

  {
    "user_id": "<user id to ban>"
    "reason": "string: <reason for the ban>"
  }

Banning a user adjusts the banned member's membership state to ``ban``.
Like with other membership changes, a user can directly adjust the target
member's state, by making a request to
``/rooms/<room id>/state/m.room.member/<user id>``::

  {
    "membership": "ban"
  }

A user must be explicitly unbanned with a request to |/rooms/<room_id>/unban|_
before they can re-join the room or be re-invited.

{{banning_cs_http_api}}



Listing rooms
~~~~~~~~~~~~~

{{list_public_rooms_cs_http_api}}

Profiles
--------

{{profile_cs_http_api}}

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

Both of these should be done automatically by the homeserver when a user
successfully changes their display name or avatar URL fields.

Additionally, when homeservers emit room membership events for their own
users, they should include the display name and avatar URL fields in these
events so that clients already have these details to hand, and do not have to
perform extra round trips to query it.

Security
--------

Rate limiting
~~~~~~~~~~~~~
Homeservers SHOULD implement rate limiting to reduce the risk of being
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

.. References

.. _`macaroon`: http://research.google.com/pubs/pub41892.html
.. _`devices`: ../intro.html#devices

.. Links through the external API docs are below
.. =============================================

.. |/initialSync| replace:: ``/initialSync``
.. _/initialSync: #get-matrix-client-%CLIENT_MAJOR_VERSION%-initialsync

.. |/sync| replace:: ``/sync``
.. _/sync: #get-matrix-client-%CLIENT_MAJOR_VERSION%-sync

.. |/events| replace:: ``/events``
.. _/events: #get-matrix-client-%CLIENT_MAJOR_VERSION%-events

.. |/createRoom| replace:: ``/createRoom``
.. _/createRoom: #post-matrix-client-%CLIENT_MAJOR_VERSION%-createroom

.. |/rooms/<room_id>/initialSync| replace:: ``/rooms/<room_id>/initialSync``
.. _/rooms/<room_id>/initialSync: #get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-initialsync

.. |/rooms/<room_id>/messages| replace:: ``/rooms/<room_id>/messages``
.. _/rooms/<room_id>/messages: #get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-messages

.. |/rooms/<room_id>/members| replace:: ``/rooms/<room_id>/members``
.. _/rooms/<room_id>/members: #get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-members

.. |/rooms/<room_id>/state| replace:: ``/rooms/<room_id>/state``
.. _/rooms/<room_id>/state: #get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-state

.. |/rooms/<room_id>/send| replace:: ``/rooms/<room_id>/send``
.. _/rooms/<room_id>/send: #put-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-send-eventtype-txnid

.. |/rooms/<room_id>/invite| replace:: ``/rooms/<room_id>/invite``
.. _/rooms/<room_id>/invite: #post-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-invite

.. |/rooms/<room_id>/join| replace:: ``/rooms/<room_id>/join``
.. _/rooms/<room_id>/join: #post-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-join

.. |/rooms/<room_id>/leave| replace:: ``/rooms/<room_id>/leave``
.. _/rooms/<room_id>/leave: #post-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-leave

.. |/rooms/<room_id>/ban| replace:: ``/rooms/<room_id>/ban``
.. _/rooms/<room_id>/ban: #post-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-ban

.. |/rooms/<room_id>/unban| replace:: ``/rooms/<room_id>/unban``
.. _/rooms/<room_id>/unban: #post-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-unban

.. |/rooms/{roomId}/context/{eventId}| replace:: ``/rooms/{roomId}/context/{eventId}``
.. _/rooms/{roomId}/context/{eventId}: #get-matrix-client-%CLIENT_MAJOR_VERSION%-rooms-roomid-context-eventid

.. |/account/3pid| replace:: ``/account/3pid``
.. _/account/3pid: #post-matrix-client-%CLIENT_MAJOR_VERSION%-account-3pid

.. |/user/<user_id>/account_data/<type>| replace:: ``/user/<user_id>/account_data/<type>``
.. _/user/<user_id>/account_data/<type>: #put-matrix-client-%CLIENT_MAJOR_VERSION%-user-userid-account-data-type

.. _`Unpadded Base64`:  ../appendices.html#unpadded-base64
