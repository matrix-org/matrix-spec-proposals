Push Gateway API
================

Clients may want to receive push notifications when events are received at
the homeserver. This is managed by a distinct entity called the Push Gateway.
A client's homeserver forwards information about the event to the push gateway
and the gateway submits a push notification to the push notification provider
(e.g. APNS, GCM).


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
