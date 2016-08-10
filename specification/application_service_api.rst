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

Application Service API
=======================

The Matrix client-server API and server-server APIs provide the means to
implement a consistent self-contained federated messaging fabric. However, they
provide limited means of implementing custom server-side behaviour in Matrix
(e.g. gateways, filters, extensible hooks etc). The Application Service API (AS API)
defines a standard API to allow such extensible functionality to be implemented
irrespective of the underlying homeserver implementation.

.. TODO-spec
  Add in Client-Server services? Overview of bots? Seems weird to be in the spec
  given it is VERY implementation specific.

.. contents:: Table of Contents
.. sectnum::

Specification version
---------------------

This version of the specification is generated from
`matrix-doc <https://github.com/matrix-org/matrix-doc>`_ as of Git commit
`{{git_version}} <https://github.com/matrix-org/matrix-doc/tree/{{git_rev}}>`_.

Application Services
--------------------
Application services are passive and can only observe events from a given
homeserver. They can inject events into rooms they are participating in.
They cannot prevent events from being sent, nor can they modify the content of
the event being sent. In order to observe events from a homeserver, the
homeserver needs to be configured to pass certain types of traffic to the
application service.  This is achieved by manually configuring the homeserver
with information about the application service (AS).

Registration
~~~~~~~~~~~~

.. NOTE::
  Previously, application services could register with a homeserver via HTTP
  APIs. This was removed as it was seen as a security risk. A compromised
  application service could re-register for a global ``*`` regex and sniff
  *all* traffic on the homeserver. To protect against this, application
  services now have to register via configuration files which are linked to
  the homeserver configuration file. The addition of configuration files
  allows homeserver admins to sanity check the registration for suspicious
  regex strings.

.. TODO
  Removing the API entirely is probably a mistake - having a standard cross-HS
  way of doing this stops ASes being coupled to particular HS implementations.
  A better solution would be to somehow mandate that the API done to avoid
  abuse.

Application services register "namespaces" of user IDs, room aliases and room IDs.
These namespaces are represented as regular expressions. An application service
is said to be "interested" in a given event if one of the IDs in the event match
the regular expression provided by the application service. An application
service can also state whether they should be the only ones who
can manage a specified namespace. This is referred to as an "exclusive"
namespace. An exclusive namespace prevents humans and other application
services from creating/deleting entities in that namespace. Typically,
exclusive namespaces are used when the rooms represent real rooms on
another service (e.g. IRC). Non-exclusive namespaces are used when the
application service is merely augmenting the room itself (e.g. providing
logging or searching facilities). Namespaces are represented by POSIX extended
regular expressions and look like:

.. code-block:: yaml

   users:
     - exclusive: true
       regex: @irc.freenode.net_.*


The registration is represented by a series of key-value pairs, which this
specification will present as YAML. An example HS configuration required to pass
traffic to the AS is:

.. code-block:: yaml

    id: <user-defined unique ID of AS which will never change>
    url: <base url of AS>
    as_token: <token AS will add to requests to HS>
    hs_token: <token HS will add to requests to AS>
    sender_localpart: <localpart of AS user>
    namespaces:
      users:  # Namespaces of users which should be delegated to the AS
        - exclusive: <bool>
          regex: <regex>
        - ...
      aliases: []  # Namespaces of room aliases which should be delegated to the AS
      rooms: [] # Namespaces of room ids which should be delegated to the AS

.. WARNING::
  If the homeserver in question has multiple application services, each
  ``as_token`` and ``id`` MUST be unique per application service as these are
  used to identify the application service. The homeserver MUST enforce this.


Homeserver -> Application Service API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pushing events
++++++++++++++

The application service API provides a transaction API for sending a list of
events. Each list of events includes a transaction ID, which works as follows:

::

 Typical
 HS ---> AS : Homeserver sends events with transaction ID T.
    <---    : AS sends back 200 OK.

 AS ACK Lost
 HS ---> AS : Homeserver sends events with transaction ID T.
    <-/-    : AS 200 OK is lost.
 HS ---> AS : Homeserver retries with the same transaction ID of T.
    <---    : AS sends back 200 OK. If the AS had processed these events
              already, it can NO-OP this request (and it knows if it is the same
              events based on the transaction ID).

The events sent to the application service should be linearised, as if they were
from the event stream. The homeserver MUST maintain a queue of transactions to
send to the AS. If the application service cannot be reached, the homeserver
SHOULD backoff exponentially until the application service is reachable again.
As application services cannot *modify* the events in any way, these requests can
be made without blocking other aspects of the homeserver. Homeservers MUST NOT
alter (e.g. add more) events they were going to send within that transaction ID
on retries, as the AS may have already processed the events.

Querying
++++++++

The application service API includes two querying APIs: for room aliases and for
user IDs. The application service SHOULD create the queried entity if it desires.
During this process, the application service is blocking the homeserver until the
entity is created and configured. If the homeserver does not receive a response
to this request, the homeserver should retry several times before timing out. This
should result in an HTTP status 408 "Request Timeout" on the client which initiated
this request (e.g. to join a room alias).

.. admonition:: Rationale

  Blocking the homeserver and expecting the application service to create the entity
  using the client-server API is simpler and more flexible than alternative methods
  such as returning an initial sync style JSON blob and get the HS to provision
  the room/user. This also meant that there didn't need to be a "backchannel" to inform
  the application service about information about the entity such as room ID to
  room alias mappings.


HTTP APIs
+++++++++

This contains application service APIs which are used by the homeserver. All
application services MUST implement these APIs. These APIs are defined below.

{{application_service_as_http_api}}


.. _create the user: `sect:asapi-permissions`_

Client-Server API Extensions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Application services can use a more powerful version of the
client-server API by identifying itself as an application service to the
homeserver.

Identity assertion
++++++++++++++++++
The client-server API infers the user ID from the ``access_token`` provided in
every request. It would be an annoying amount of book-keeping to maintain tokens
for every virtual user. It would be preferable if the application service could
use the CS API with its own ``as_token`` instead, and specify the virtual user
they wish to be acting on behalf of. For real users, this would require
additional permissions granting the AS permission to masquerade as a matrix user.

Inputs:
 - Application service token (``access_token``)
 - User ID in the AS namespace to act as.

Notes:
 - This will apply on all aspects of the CS API, except for Account Management.
 - The ``as_token`` is inserted into ``access_token`` which is usually where the
   client token is. This is done on purpose to allow application services to
   reuse client SDKs.

::

 /path?access_token=$token&user_id=$userid

 Query Parameters:
   access_token: The application service token
   user_id: The desired user ID to act as.

Timestamp massaging
+++++++++++++++++++
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
++++++++++++++++++++++++++++++

.. _sect:asapi-permissions:

The homeserver needs to give the application service *full control* over its
namespace, both for users and for room aliases. This means that the AS should
be able to create/edit/delete any room alias in its namespace, as well as
create/delete any user in its namespace. No additional API changes need to be
made in order for control of room aliases to be granted to the AS. Creation of
users needs API changes in order to:

- Work around captchas.
- Have a 'passwordless' user.

This involves bypassing the registration flows entirely. This is achieved by
including the AS token on a ``/register`` request, along with a login type of
``m.login.application_service`` to set the desired user ID without a password.

::

  /register?access_token=$as_token

  Content:
  {
    type: "m.login.application_service",
    username: "<desired user localpart in AS namespace>"
  }

Application services which attempt to create users or aliases *outside* of
their defined namespaces will receive an error code ``M_EXCLUSIVE``. Similarly,
normal users who attempt to create users or aliases *inside* an application
service-defined namespace will receive the same ``M_EXCLUSIVE`` error code,
but only if the application service has defined the namespace as ``exclusive``.

ID conventions
~~~~~~~~~~~~~~
.. TODO-spec
  - Giving HSes the freedom to namespace still feels like the Right Thing here.
  - Exposing a public API provides the consistency which was the main complaint
    against namespacing.
  - This may have knock-on effects for the AS registration API. E.g. why don't
    we let ASes specify the *URI* regex they want?

This concerns the well-defined conventions for mapping 3P network IDs to matrix
IDs, which we expect clients to be able to do by themselves.

User IDs
++++++++
Matrix users may wish to directly contact a virtual user, e.g. to send an email.
The URI format is a well-structured way to represent a number of different ID
types, including:

- MSISDNs (``tel``)
- Email addresses (``mailto``)
- IRC nicks (``irc`` - https://tools.ietf.org/html/draft-butcher-irc-url-04)
- XMPP (XEP-0032)
- SIP URIs (RFC 3261)

As a result, virtual user IDs SHOULD relate to their URI counterpart. This
mapping from URI to user ID can be expressed in a number of ways:

- Expose a C-S API on the HS which takes URIs and responds with user IDs.
- Munge the URI with the user ID.

Exposing an API would allow HSes to internally map user IDs however they like,
at the cost of an extra round trip (of which the response can be cached).
Munging the URI would allow clients to apply the mapping locally, but would force
user X on service Y to always map to the same munged user ID. Considering the
exposed API could just be applying this munging, there is more flexibility if
an API is exposed.

::

  GET /_matrix/app/%CLIENT_MAJOR_VERSION%/user?uri=$url_encoded_uri

  Returns 200 OK:
  {
    user_id: <complete user ID on local HS>
  }

Room Aliases
++++++++++++
We may want to expose some 3P network rooms so Matrix users can join them directly,
e.g. IRC rooms. We don't want to expose every 3P network room though, e.g.
``mailto``, ``tel``. Rooms which are publicly accessible (e.g. IRC rooms) can be
exposed as an alias by the application service. Private rooms
(e.g. sending an email to someone) should not
be exposed in this way, but should instead operate using normal invite/join semantics.
Therefore, the ID conventions discussed below are only valid for public rooms which
expose room aliases.

Matrix users may wish to join XMPP rooms (e.g. using XEP-0045) or IRC rooms. In both
cases, these rooms can be expressed as URIs. For consistency, these "room" URIs
SHOULD be mapped in the same way as "user" URIs.

::

  GET /_matrix/app/%CLIENT_MAJOR_VERSION%/alias?uri=$url_encoded_uri

  Returns 200 OK:
  {
    alias: <complete room alias on local HS>
  }

Event fields
++++++++++++
We recommend that any events that originated from a remote network should
include an ``external_url`` field in their content to provide a way for Matrix
clients to link into the 'native' client from which the event originated.
For instance, this could contain the message-ID for emails/nntp posts, or a link
to a blog comment when bridging blog comment traffic in & out of Matrix.
