---
title: "Push Gateway API"
weight: 50
type: docs
---

Clients may want to receive push notifications when events are received
at the homeserver. This is managed by a distinct entity called the Push
Gateway.

## Changelog

**Version: %PUSH\_GATEWAY\_RELEASE\_LABEL%**

{{push\_gateway\_changelog}}

This version of the specification is generated from
[matrix-doc](https://github.com/matrix-org/matrix-doc) as of Git commit
[{{git\_version}}](https://github.com/matrix-org/matrix-doc/tree/%7B%7Bgit_rev%7D%7D).

For the full historical changelog, see
<https://github.com/matrix-org/matrix-doc/blob/master/changelogs/push_gateway.rst>

### Other versions of this specification

The following other versions are also available, in reverse
chronological order:

-   [HEAD](https://matrix.org/docs/spec/push_gateway/unstable.html):
    Includes all changes since the latest versioned release.
-   [r0.1.0](https://matrix.org/docs/spec/push_gateway/r0.1.0.html)

## Overview

A client's homeserver forwards information about received events to the
push gateway. The gateway then submits a push notification to the push
notification provider (e.g. APNS, GCM).

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

## Homeserver behaviour

This describes the format used by "HTTP" pushers to send notifications
of events to Push Gateways. If the endpoint returns an HTTP error code,
the homeserver SHOULD retry for a reasonable amount of time using
exponential backoff.

When pushing notifications for events, the homeserver is expected to
include all of the event-related fields in the `/notify` request. When
the homeserver is performing a push where the `format` is
`"event_id_only"`, only the `event_id`, `room_id`, `counts`, and
`devices` are required to be populated.

Note that most of the values and behaviour of this endpoint is described
by the Client-Server API's [Push
Module](../client_server/%CLIENT_RELEASE_LABEL%.html#module-push).

{{push\_notifier\_push\_http\_api}}
