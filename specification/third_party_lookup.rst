Application Services
====================

An application service is a separate program that interacts with a homeserver
and provides various bits of functionality that would otherwise not make
sense to include directly in the homeserver. This ranges from bots, which can
often be interacted with, to bridges, which allow Matrix users to communicate
with users on third party networks. The following describes endpoints that a
Matrix client can use to interact with an application service through the
facilitation of the homeserver.

Third Party Lookups
------------------

Application services can provide access to third party networks via bridging.
This allows Matrix users to communicate with users on other communication
platforms, with messages ferried back and forth by the application service. A
single application service may bridge multiple third party networks, and many
individual locations within those networks. A single third party network
location may be bridged to multiple Matrix rooms.

In order for a client to join one of these bridged rooms, or communicate
directly with a user on a third party network, the following endpoints can be
used.

{{third_party_lookup_cs_http_api}}