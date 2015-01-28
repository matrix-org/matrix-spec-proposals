Push Notifications
==================

Matrix supports push notifications as a first class citizen. Home Servers send
notifications of user events to user-configured HTTP endpoints. User may also
configure a number of rules that determine what events generate notifications.
These are all stored and managed by the users home server such that settings can
be reused between client apps as appropriate.

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
  gateway, 'sygnal'.

For information on the client-server API for setting pushers and push rules, see
the Client Server API section. For more information on the format of HTTP
notifications, see the HTTP Notification Protocol section.
