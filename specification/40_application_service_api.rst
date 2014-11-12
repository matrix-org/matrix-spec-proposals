Application Service API
=======================

The Matrix client-server API and server-server APIs provide the means to
implement a consistent self-contained federated messaging fabric. However, they
provide limited means of implementing custom server-side behaviour in Matrix
(e.g. gateways, filters, extensible hooks etc).

Defining a standard API to allow such extensible functionality to be implemented
irrespective of the underlying homeserver implementation is key to enabling
these services.

Client-Server Services
----------------------

.. TODO-spec
  Overview of bots

Passive Application Services
----------------------------

.. TODO-spec 
  API that extends the client-server API to allow events to be
  received with better-than-client permissions.

Active Application Services
----------------------------

.. TODO-spec
  API that provides hooks into the server so that you can intercept and
  manipulate events, and/or insert virtual users & rooms into the server.

