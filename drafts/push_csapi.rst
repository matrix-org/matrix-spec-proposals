Push Notifications
==================

Pushers
-------
To receive any notification pokes at all, it is necessary to configure a
'pusher' on the Home Server that you wish to receive notifications from. There
is a single API endpoint for this::

Fetching a user account displayname::

	POST $PREFIX/pushers/set

This takes a JSON object with the following keys:

pushkey
  This is a unique identifier for this pusher. The value you should use for this
  is the routing or destination address information for the notification, for
  example, the APNS token for APNS or the Registration ID for GCM. If your
  notification client has no such concept, use any unique identifier.
kind
  The kind of pusher to configure. 'http' makes a pusher that sends HTTP pokes.
  null deletes the pusher.
instance_handle
  This is an identifier for the device which owns the pusher. It may be up to 32
  characters long. It must be unique among all the pushers for a given user
  (therefore the device ID may not be used). It is advised that when an app's
  data is copied or restored to a different device, this ID remain the same (ie.
  be shared by multiple pushers for multiple devices). Client apps should be
  aware that this situation can occur and be able to rectify it (eg. by
  offerring to reset the instance_hanlde, optionally duplicating all push rules
  to new instance handle).
app_id
  appId is a reverse-DNS style identifier for the application. It is recommended
  that this end with the platform, such that different platform versions get
  different app identifiers. Max length, 64 chars.
app_display_name
  A string that will allow the user to identify what application owns this
  pusher.
device_display_name
  A string that will allow the user to identify what device owns this pusher.
lang
  The preferred language for receiving notifications (eg, 'en' or 'en-US')
data
  A dictionary of information for the pusher implementation itself. For HTTP
  pushers, this must contain a 'url' key which is a string of the URL that
  should be used to send notifications.

If the pusher was created successfully, an empty JSON dictionary is returned.



