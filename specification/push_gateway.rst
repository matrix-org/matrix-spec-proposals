Push Gateway API
================

Clients may want to receive push notifications when events are received at
the homeserver. This is managed by a distinct entity called the Push Gateway.

.. contents:: Table of Contents
.. sectnum::

Specification version
---------------------

This version of the specification is generated from
`matrix-doc <https://github.com/matrix-org/matrix-doc>`_ as of Git commit
`{{git_version}} <https://github.com/matrix-org/matrix-doc/tree/{{git_rev}}>`_.

Overview
--------

A client's homeserver forwards information about received events to the push
gateway. The gateway then submits a push notification to the push notification
provider (e.g. APNS, GCM).


::

                                   +--------------------+  +-------------------+
                  Matrix HTTP      |                    |  |                   |
             Notification Protocol |   App Developer    |  |   Device Vendor   |
                                   |                    |  |                   |
           +-------------------+   | +----------------+ |  | +---------------+ |
           |                   |   | |                | |  | |               | |
           | Matrix homeserver +----->  Push Gateway  +------> Push Provider | |
           |                   |   | |                | |  | |               | |
           +-^-----------------+   | +----------------+ |  | +----+----------+ |
             |                     |                    |  |      |            |
    Matrix   |                     |                    |  |      |            |
 Client/Server API  +              |                    |  |      |            |
             |      |              +--------------------+  +-------------------+
             |   +--+-+                                           |
             |   |    <-------------------------------------------+
             +---+    |
                 |    |          Provider Push Protocol
                 +----+

         Mobile Device or Client


Homeserver behaviour
--------------------

This describes the format used by "HTTP" pushers to send notifications of
events to Push Gateways. If the endpoint returns an HTTP error code, the
homeserver SHOULD retry for a reasonable amount of time using exponential backoff.

{{push_notifier_push_http_api}}
