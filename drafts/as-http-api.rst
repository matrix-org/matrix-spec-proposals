Application Services HTTP API
=============================

.. contents:: Table of Contents
.. sectnum::

Application Service -> Home Server
----------------------------------
This contains home server APIs which are used by the application service.

Registration API ``[Draft]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. NOTE::
  - Do we really have to use regex for this? Can't we do this a nicer way?

This API registers the application service with its host homeserver to offer its services.

Inputs:
 - Credentials (e.g. some kind of string token)
 - Namespace[users]
 - Namespace[room aliases]
 - URL base to receive inbound comms
Output:
 - The credentials the HS will use to query the AS with in return. (e.g. some kind of string token)
Side effects:
 - The HS will start delivering events to the URL base specified if this 200s.
API called when:
 - The application service wants to register with a brand new home server.
Notes:
 - Namespaces are represented by POSIX extended regular expressions in JSON. 
   They look like::
     users: [
       "@irc\.freenode\.net/.*", 
     ]
::

 POST /register
 
 Request format
 {
   url: "https://my.application.service.com/matrix/",
   as_token: "some_AS_token",
   namespaces: {
     users: [
       "@irc\.freenode\.net/.*"
     ],
     aliases: [
       "#irc\.freenode\.net/.*"
     ],
     rooms: [
       "!irc\.freenode\.net/.*"
     ]
   }
 }
 
 
 Returns:
   200 : Registration accepted.
   400 : Namespaces do not conform to regex
   401 : Credentials need to be supplied.
   403 : AS credentials rejected.
 
 
   200 OK response format
 
   {
     hs_token: "string"
   }
   
Unregister API ``[Draft]``
~~~~~~~~~~~~~~~~~~~~~~~~~
This API unregisters a previously registered AS from the home server.

Inputs:
 - AS token
Output:
 - None.
Side effects:
 - The HS will stop delivering events to the URL base specified for this AS if this 200s.
API called when:
 - The application service wants to stop receiving all events from the HS.
 
::

  POST /unregister

  Request format
  {
    as_token: "string"
  }


Home Server -> Application Service
----------------------------------
This contains application service APIs which are used by the home server.

User Query ``[Draft]``
~~~~~~~~~~~~~~~~~~~~~~

This API is called by the HS to query the existence of a user on the Application Service's namespace.

Inputs:
 - User ID
 - HS Credentials
Output:
 - Profile info
Side effects:
 - User is created on the HS if this response 200s.
API called when:
 - HS receives an event for an unknown user ID in the AS's namespace.
Notes:
 - The created user will have their profile info set based on the output.
 
::

 GET /users/$user_id?access_token=$hs_token
 
 Returns:
   200 : User is recognised.
   404 : User not found.
   401 : Credentials need to be supplied.
   403 : HS credentials rejected.
 
 
   200 OK response format
 
   {
     profile: {
       display_name: "string"
       avatar_url: "string(uri)"
     }
   }
   
Room Alias Query ``[TODO]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~
This API is called by the HS to query the existence of a room alias on the Application 
Service's namespace.


Pushing ``[TODO]``
~~~~~~~~~~~~~~~~~~
This API is called by the HS when the HS wants to push an event (or batch of events) to the AS.

- Retry semantics
- Ordering


 
Client -> Server -> Application Service
---------------------------------------
This contains home server APIs which are used by the client, to communicate with
the application service.

Linking ``[Draft]``
~~~~~~~~~~~~~~~~~~
.. NOTE::
 - How does the application service know that the matrix user really is the virtual
   user they claim to be? If we force an IS lookup, then this would resolve on its
   own as anyone who wants to talk to the virtual user will do a lookup before trying
   the application service...
 - In other words, what is preventing ``@bob:matrix.org`` masquerading as 
   ``@.irc.freenode.alice:matrix.org``?

Clients may want to link their matrix user ID to their virtual user ID. This
API allows the AS to do this, so messages sent from the AS are sent as the client's
user ID, instead of the virtual user ID.

This is not achieved using OAuth2 or similar because the trust relationships are
different. The application service already has a huge amount of trust from the
home server, unlike a random third-party web app. As a result, the data flow is
different because the third-party (the application service) is trusted by the
authorisation entity (the home server). Furthermore, it is desirable to not have
the clients communicate directly with the application service in order to 
decrease the complexity of AS design.

To grant permission for an application service to masquerade as a user:

Inputs:
 - Credentials of user (e.g. ``access_token``)
 - The user ID within an application service's namespace to claim.
 - Restrictions if any (e.g. only for rooms X,Y,Z. Only for 10 hours. etc)
Output:
 - None.
Side effects:
 - The home server will generate an ``access_token`` and push it to the 
   application service along with both user IDs if this response 200s.
Notes:
 - Repeated calls to this API should invalidate any existing token for this
   user ID / application service combo and provision a new token which is then
   pushed.
 - The generated access token MUST honour the restrictions laid out by the 
   client.
   
::

 PUT /appservices/$virtual_user_id?access_token=$token
 
 Request format
 {
   restrictions: {
     expires_in: 3600,
     rooms: [
      "!fl3rwfehw:matrix.org",
      "!fwet2yugs:matrix.org"
     ]
   }
 }

To revoke permission for an application service to masquerade as a user:

Inputs:
 - Credentials of user (e.g. ``access_token``)
 - The user ID within an application service's namespace to revoke. If blank,
   revokes all virtual user IDs linked to this matrix user ID.
Output:
 - None.
Side effects:
 - The home server invalidate all access tokens for this user ID / AS combo
   and push this invalidation to the application service if this response 200s.
   
::

 DELETE /appservices/$virtual_user_id?access_token=$token


Client-Server v2 API Extensions
-------------------------------

Identity assertion
~~~~~~~~~~~~~~~~~~
The client-server API infers the user ID from the ``access_token`` provided in every
request. It would be an annoying amount of book-keeping to maintain tokens for every
virtual user. It would be preferable if the application service could use the CS API
with its own ``as_token`` instead, and specify the virtual user they wish to be 
acting on behalf of. For real users, this would require additional permissions (see
"C-AS Linking").

Inputs:
 - Application service token (``access_token``)
 Either:
   - User ID in the AS namespace to act as.
 Or:
   - OAuth2 token of real user (which may end up being an access token) 
Notes:
 - This will apply on all aspects of the CS API, except for Account Management.
 - The ``as_token`` is inserted into ``access_token`` which is usually where the client
   token is. This is done on purpose to allow application services to reuse client
   SDKs.

::

 /path?access_token=$token&user_id=$userid

 Query Parameters:
   access_token: The application service token
   user_id: The desired user ID to act as.
   
 /path?access_token=$token&user_token=$token

 Query Parameters:
   access_token: The application service token
   user_token: The token granted to the AS by the real user

Timestamp massaging
~~~~~~~~~~~~~~~~~~~
The application service may want to inject events at a certain time (reflecting
the time on the network they are tracking e.g. irc, xmpp). Application services
need to be able to adjust the ``origin_server_ts`` value to do this.

Inputs:
 - Application service token (``as_token``)
 - Desired timestamp
Notes:
 - This will only apply when sending events.
 
::

 /path?access_token=$token&ts=$timestamp

 Query Parameters added to the send event APIs only:
   access_token: The application service token
   ts: The desired timestamp

Server admin style permissions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The home server needs to give the application service *full control* over its
namespace, both for users and for room aliases. This means that the AS should
be able to create/edit/delete any room alias in its namespace, as well as
create/delete any user in its namespace. This does not require any additional
public APIs.
