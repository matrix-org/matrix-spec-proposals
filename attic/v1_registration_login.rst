Registration and Login
----------------------

Clients must register with a homeserver in order to use Matrix. After
registering, the client will be given an access token which must be used in ALL
requests to that homeserver as a query parameter 'access_token'.

If the client has already registered, they need to be able to login to their
account. The homeserver may provide many different ways of logging in, such as
user/password auth, login via a social network (OAuth2), login by confirming a
token sent to their email address, etc. This specification does not define how
homeservers should authorise their users who want to login to their existing
accounts, but instead defines the standard interface which implementations
should follow so that ANY client can login to ANY homeserver. Clients login
using the |login|_ API. Clients register using the |register|_ API.
Registration follows the same general procedure as login, but the path requests
are sent to and the details contained in them are different.

In both registration and login cases, the process takes the form of one or more
stages, where at each stage the client submits a set of data for a given stage
type and awaits a response from the server, which will either be a final
success or a request to perform an additional stage. This exchange continues
until the final success.

In order to determine up-front what the server's requirements are, the client
can request from the server a complete description of all of its acceptable
flows of the registration or login process. It can then inspect the list of
returned flows looking for one for which it believes it can complete all of the
required stages, and perform it. As each homeserver may have different ways of
logging in, the client needs to know how they should login. All distinct login
stages MUST have a corresponding ``type``. A ``type`` is a namespaced string
which details the mechanism for logging in.

A client may be able to login via multiple valid login flows, and should choose
a single flow when logging in. A flow is a series of login stages. The home
server MUST respond with all the valid login flows when requested by a simple
``GET`` request directly to the ``/login`` or ``/register`` paths::

  {
    "flows": [
      {
        "type": "<login type1a>",
        "stages": [ "<login type 1a>", "<login type 1b>" ]
      },
      {
        "type": "<login type2a>",
        "stages": [ "<login type 2a>", "<login type 2b>" ]
      },
      {
        "type": "<login type3>"
      }
    ]
  }

The client can now select which flow it wishes to use, and begin making
``POST`` requests to the ``/login`` or ``/register`` paths with JSON body
content containing the name of the stage as the ``type`` key, along with
whatever additional parameters are required for that login or registration type
(see below). After the flow is completed, the client's fully-qualified user
ID and a new access token MUST be returned::

  {
    "user_id": "@user:matrix.org",
    "access_token": "abcdef0123456789"
  }

The ``user_id`` key is particularly useful if the homeserver wishes to support
localpart entry of usernames (e.g. "user" rather than "@user:matrix.org"), as
the client may not be able to determine its ``user_id`` in this case.

If the flow has multiple stages to it, the homeserver may wish to create a
session to store context between requests. If a homeserver responds with a
``session`` key to a request, clients MUST submit it in subsequent requests
until the flow is completed::

  {
    "session": "<session id>"
  }

This specification defines the following login types:
 - ``m.login.password``
 - ``m.login.oauth2``
 - ``m.login.email.code``
 - ``m.login.email.url``
 - ``m.login.email.identity``

Password-based
~~~~~~~~~~~~~~
:Type:
  ``m.login.password``
:Description:
  Login is supported via a username and password.

To respond to this type, reply with::

  {
    "type": "m.login.password",
    "user": "<user_id or user localpart>",
    "password": "<password>"
  }

The homeserver MUST respond with either new credentials, the next stage of the
login process, or a standard error response.

Captcha-based
~~~~~~~~~~~~~
:Type:
  ``m.login.recaptcha``
:Description:
  Login is supported by responding to a captcha (in the case of the Synapse
  implementation, Google's Recaptcha library is used).

To respond to this type, reply with::

  {
    "type": "m.login.recaptcha",
    "challenge": "<challenge token>",
    "response": "<user-entered text>"
  }

.. NOTE::
  In Synapse, the Recaptcha parameters can be obtained in Javascript by calling:
    Recaptcha.get_challenge();
    Recaptcha.get_response();

The homeserver MUST respond with either new credentials, the next stage of the
login process, or a standard error response.

OAuth2-based
~~~~~~~~~~~~
:Type:
  ``m.login.oauth2``
:Description:
  Login is supported via OAuth2 URLs. This login consists of multiple requests.

To respond to this type, reply with::

  {
    "type": "m.login.oauth2",
    "user": "<user_id or user localpart>"
  }

The server MUST respond with::

  {
    "uri": <Authorization Request URI OR service selection URI>
  }

The homeserver acts as a 'confidential' client for the purposes of OAuth2.  If
the uri is a ``sevice selection URI``, it MUST point to a webpage which prompts
the user to choose which service to authorize with. On selection of a service,
this MUST link through to an ``Authorization Request URI``. If there is only 1
service which the homeserver accepts when logging in, this indirection can be
skipped and the "uri" key can be the ``Authorization Request URI``.

The client then visits the ``Authorization Request URI``, which then shows the
OAuth2 Allow/Deny prompt. Hitting 'Allow' returns the ``redirect URI`` with the
auth code.  Homeservers can choose any path for the ``redirect URI``. The
client should visit the ``redirect URI``, which will then finish the OAuth2
login process, granting the homeserver an access token for the chosen service.
When the homeserver gets this access token, it verifies that the cilent has
authorised with the 3rd party, and can now complete the login. The OAuth2
``redirect URI`` (with auth code) MUST respond with either new credentials, the
next stage of the login process, or a standard error response.

For example, if a homeserver accepts OAuth2 from Google, it would return the
Authorization Request URI for Google::

  {
    "uri": "https://accounts.google.com/o/oauth2/auth?response_type=code&
    client_id=CLIENT_ID&redirect_uri=REDIRECT_URI&scope=photos"
  }

The client then visits this URI and authorizes the homeserver. The client then
visits the REDIRECT_URI with the auth code= query parameter which returns::

  {
    "user_id": "@user:matrix.org",
    "access_token": "0123456789abcdef"
  }

Email-based (code)
~~~~~~~~~~~~~~~~~~
:Type:
  ``m.login.email.code``
:Description:
  Login is supported by typing in a code which is sent in an email. This login
  consists of multiple requests.

To respond to this type, reply with::

  {
    "type": "m.login.email.code",
    "user": "<user_id or user localpart>",
    "email": "<email address>"
  }

After validating the email address, the homeserver MUST send an email
containing an authentication code and return::

  {
    "type": "m.login.email.code",
    "session": "<session id>"
  }

The second request in this login stage involves sending this authentication
code::

  {
    "type": "m.login.email.code",
    "session": "<session id>",
    "code": "<code in email sent>"
  }

The homeserver MUST respond to this with either new credentials, the next
stage of the login process, or a standard error response.

Email-based (url)
~~~~~~~~~~~~~~~~~
:Type:
  ``m.login.email.url``
:Description:
  Login is supported by clicking on a URL in an email. This login consists of
  multiple requests.

To respond to this type, reply with::

  {
    "type": "m.login.email.url",
    "user": "<user_id or user localpart>",
    "email": "<email address>"
  }

After validating the email address, the homeserver MUST send an email
containing an authentication URL and return::

  {
    "type": "m.login.email.url",
    "session": "<session id>"
  }

The email contains a URL which must be clicked. After it has been clicked, the
client should perform another request::

  {
    "type": "m.login.email.url",
    "session": "<session id>"
  }

The homeserver MUST respond to this with either new credentials, the next
stage of the login process, or a standard error response.

A common client implementation will be to periodically poll until the link is
clicked.  If the link has not been visited yet, a standard error response with
an errcode of ``M_LOGIN_EMAIL_URL_NOT_YET`` should be returned.


Email-based (identity server)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
:Type:
  ``m.login.email.identity``
:Description:
  Login is supported by authorising an email address with an identity server.

Prior to submitting this, the client should authenticate with an identity
server.  After authenticating, the session information should be submitted to
the homeserver.

To respond to this type, reply with::

  {
    "type": "m.login.email.identity",
    "threepidCreds": [
      {
        "sid": "<identity server session id>",
        "clientSecret": "<identity server client secret>",
        "idServer": "<url of identity server authed with, e.g. 'matrix.org:8090'>"
      }
    ]
  }



N-Factor Authentication
~~~~~~~~~~~~~~~~~~~~~~~
Multiple login stages can be combined to create N-factor authentication during
login.

This can be achieved by responding with the ``next`` login type on completion
of a previous login stage::

  {
    "next": "<next login type>"
  }

If a homeserver implements N-factor authentication, it MUST respond with all
``stages`` when initially queried for their login requirements::

  {
    "type": "<1st login type>",
    "stages": [ <1st login type>, <2nd login type>, ... , <Nth login type> ]
  }

This can be represented conceptually as::

   _______________________
  |    Login Stage 1      |
  | type: "<login type1>" |
  |  ___________________  |
  | |_Request_1_________| | <-- Returns "session" key which is used throughout.
  |  ___________________  |
  | |_Request_2_________| | <-- Returns a "next" value of "login type2"
  |_______________________|
            |
            |
   _________V_____________
  |    Login Stage 2      |
  | type: "<login type2>" |
  |  ___________________  |
  | |_Request_1_________| |
  |  ___________________  |
  | |_Request_2_________| |
  |  ___________________  |
  | |_Request_3_________| | <-- Returns a "next" value of "login type3"
  |_______________________|
            |
            |
   _________V_____________
  |    Login Stage 3      |
  | type: "<login type3>" |
  |  ___________________  |
  | |_Request_1_________| | <-- Returns user credentials
  |_______________________|

Fallback
~~~~~~~~
Clients cannot be expected to be able to know how to process every single login
type. If a client determines it does not know how to handle a given login type,
it should request a login fallback page::

  GET matrix/client/api/v1/login/fallback

This MUST return an HTML page which can perform the entire login process.
