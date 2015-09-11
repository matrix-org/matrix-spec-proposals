Push Notifications
==================

Overview
--------

::

                                   +--------------------+ +-------------------+
                  Matrix HTTP      |                    | |                   |
             Notification Protocol |   App Developer    | |   Device Vendor   |
                                   |                    | |                   |
           +-------------------+   | +----------------+ | | +---------------+ |
           |                   |   | |                | | | |               | |
           | Matrix Home Server+----->  Push Gateway  | +---> Push Provider | |
           |                   |   | |                | | | |               | |
           +-^-----------------+   | +----------------+ | | +----+----------+ |
             |                     |                    | |      |            |
    Matrix   |                     |                    | |      |            |
 Client/Server API  +              |                    | |      |            |
             |      |              +--------------------+ +-------------------+
             |   +--+-+                                          |             
             |   |    <------------------------------------------+             
             +---+    |                                                        
                 |    |          Provider Push Protocol                        
                 +----+                                                        
                                                                               
         Mobile Device or Client                                               


Matrix supports push notifications as a first class citizen. Home Servers send
notifications of user events to user-configured HTTP endpoints. User may also
configure a number of rules that determine what events generate notifications.
These are all stored and managed by the users home server such that settings can
be reused between client apps as appropriate.

The above diagram shows the flow of push notifications being sent to a handset
where push notifications are submitted via the handset vendor, such as Apple's
APNS or Google's GCM. This happens as follows:

 1. The client app signs in to a Matrix Home Server
 2. The client app registers with its vendor's Push Notification provider and
    obtains a routing token of some kind.
 3. The mobile app, uses the Matrix client/server API to add a 'pusher',
    providing the URL of a specific Push Gateway which is configured for that
    application. It also provides the routing token it has acquired from the
    Push Notification Provider.
 4. The Home Server starts sending notification HTTP requests to the Push
    Gateway using the supplied URL. The Push Gateway relays this notification to
    the Push Notification Provider, passing the routing token along with any
    necessary private credentials the provider requires to send push
    notifications.
 5. The Push Notification provider sends the notification to the device.

Nomenclature
------------

Pusher
  A 'pusher' is an activity in the Home Server that manages the sending
  of HTTP notifications for a single device of a single user.

Push Rules
  A push rule is a single rule, configured by a matrix user, that gives
  instructions to the Home Server about whether an event should be notified
  about and how given a set of conditions. Matrix clients allow the user to
  configure these. They create and view them via the Client to Server REST API.

Push Gateway
  A push gateway is a server that receives HTTP event notifications from Home
  Servers and passes them on to a different protocol such as APNS for iOS
  devices or GCM for Android devices. Matrix.org provides a reference push
  gateway, 'sygnal'. A client app tells a Home Server what push gateway
  to send notifications to when it sets up a pusher.

For information on the client-server API for setting pushers and push rules, see
the Client Server API section. For more information on the format of HTTP
notifications, see the HTTP Notification Protocol section.

