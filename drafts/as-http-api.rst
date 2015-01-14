Application Services HTTP API
=============================

.. contents:: Table of Contents
.. sectnum::

Application Service -> Home Server
----------------------------------
This contains home server APIs which are used by the application service.

Registration API ``[Draft]``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This API registers the application service with its host homeserver to offer its services.

Inputs:
 - Credentials (e.g. some kind of string token)
 - Namespace[users]
 - Namespace[room aliases]
 - URL base to receive inbound comms
Output:
 - The credentials the HS will use to query the AS with in return. (e.g. some kind of string token)
 - The complete namespace prefix for each namespace requested.
Side effects:
 - The HS will start delivering events to the URL base specified if this 200s.
API called when:
 - The application service wants to register with a brand new home server.
Notes:
 - Namespaces are represented in JSON, with a well-defined conversion to IDs. This prevents
   parsing errors and allows the HS to enforce their own namespacing semantics. They look like::
     users: {
       irc: ["freenode", "rizon"]
     }
   which represents 2 namespaces: ``@.irc.freenode.*`` and ``@.irc.rizon.*``. The leaf nodes
   must be an array. Intermediate nodes must be JSON objects with the key as the desired string
   segment. A more complicated example::
     rooms: {
       irc: {
         freenode: ["matrix"],
         rizon: ["matrixorg"]
       }
     }
   which represents 2 namespaces: ``#.irc.freenode.matrix.*`` and ``#.irc.rizon.matrixorg.*``.
 - By specifying namespaces like this, you allow home servers to namespace application services
   sensibly, rather than every IRC AS trying to nab all ``@.irc.*`` users. In order for home
   servers to do this, they need to tell the application service the actual namespaces allocated
   for them. This is returned in the JSON response, with the same structure as the original request,
   but with the strings now representing the namespace prefix allocated, e.g::
     users: {
       irc: [".applicationservice_146.irc.freenode", ".applicationservice_146.irc.rizon"]
     }
   The sigil prefix ``@`` is omitted since it is clear from the ``users`` key that these namespace
   prefixes are for users.
 - This makes the request/response JSON structure deliciously symmetric.
::

 POST /register
 
 Request format
 {
   url: "https://my.application.service.com/matrix/",
   as_token: "some_AS_token",
   namespaces: {
     users: {
       irc: ["freenode", "rizon"]
     },
     rooms: {
       irc: {
         freenode: ["matrix"],
         rizon: ["matrixorg"]
       }
     }
   }
 }
 
 
 Returns:
   200 : Registration accepted.
   400 : Namespaces do not conform to regex
   401 : Credentials need to be supplied.
   403 : AS credentials rejected.
 
 
   200 OK response format
 
   {
     hs_token: "foobar",
     namespaces: {
       users: {
         irc: [".applicationservice_146.irc.freenode", ".applicationservice_146.irc.rizon"]
       },
       rooms: {
         irc: {
           freenode: [".irc.freenode.matrix"],
           rizon: [".applicationservice_146.this.can.be.any.prefix.you.like"]
         }
       }
     }
   }
   
Unregister API ``[TODO]``
~~~~~~~~~~~~~~~~~~~~~~~~~



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
       display_name: "Foo"
       avatar_url: "mxc://foo/bar"
     }
   }
   
Room Query ``[TODO]``
~~~~~~~~~~~~~~~~~~~~~
This API is called by the HS to query the existence of a room on the Application Service's namespace.

Pushing ``[TODO]``
~~~~~~~~~~~~~~~~~~
This API is called by the HS when the HS wants to push an event (or batch of events) to the AS.

- Retry semantics
- Ordering


 
Client -> Application Service
-----------------------------
This contains application service APIs which are used by the client.

Linking ``[TODO]``
~~~~~~~~~~~~~~~~~~
Clients may want to link their matrix user ID to their 3PID (e.g. IRC nick). This
API allows the AS to do this, so messages sent from the AS are sent as the client.

- Probably OAuth2

Client-Server v2 API Extensions
-------------------------------

- Identity assertion (rather than access token inference)
- timestamp massaging (for inserting messages between other messages)
- alias mastery over the ASes namespace
- user ID mastery over the ASes namespace
