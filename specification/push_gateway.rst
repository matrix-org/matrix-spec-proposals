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
