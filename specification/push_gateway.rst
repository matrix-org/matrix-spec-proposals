.. Copyright 2016 OpenMarket Ltd
.. Copyright 2018 New Vector Ltd
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

{{unstable_warning_block_PUSH_GATEWAY_RELEASE_LABEL}}

Clients may want to receive push notifications when events are received at
the homeserver. This is managed by a distinct entity called the Push Gateway.

.. contents:: Table of Contents
.. sectnum::

Changelog
---------

.. topic:: Version: %PUSH_GATEWAY_RELEASE_LABEL%
{{push_gateway_changelog}}

This version of the specification is generated from
`matrix-doc <https://github.com/matrix-org/matrix-doc>`_ as of Git commit
`{{git_version}} <https://github.com/matrix-org/matrix-doc/tree/{{git_rev}}>`_.

For the full historical changelog, see
https://github.com/matrix-org/matrix-doc/blob/master/changelogs/push_gateway.rst

Other versions of this specification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following other versions are also available, in reverse chronological order:

- `HEAD <https://matrix.org/docs/spec/push_gateway/unstable.html>`_: Includes all changes since the latest versioned release.
- `r0.1.0 <https://matrix.org/docs/spec/push_gateway/r0.1.0.html>`_

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

When pushing notifications for events, the homeserver is expected to include all of
the event-related fields in the ``/notify`` request. When the homeserver is performing
a push where the ``format`` is ``"event_id_only"``, only the ``event_id``, ``room_id``,
``counts``, and ``devices`` are required to be populated.

{{push_notifier_push_http_api}}
