---
title: "Push Gateway API"
weight: 50
type: docs
---

Clients may want to receive push notifications when events are received
at the homeserver. This is managed by a distinct entity called the Push
Gateway.

## Overview

A client's homeserver forwards information about received events to the
push gateway. The gateway then submits a push notification to the push
notification provider (e.g. APNS, GCM).

```
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
```

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
Module](/client-server-api#push-notifications).

{{% http-api spec="push-gateway" api="push_notifier" %}}
