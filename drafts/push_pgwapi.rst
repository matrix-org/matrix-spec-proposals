Push Notifications: HTTP Notification Protocol
==============================================
This describes the format used by "http" pushers to send notifications of
events.

Notifications are sent as HTTP POST requests to the URL configured when the
pusher is created, but Matrix strongly recommends that the path should be::

  /_matrix/push/v1/notify

The body of the POST request is a JSON dictionary. The format
is as follows::

  {
    "notification": {
      "id": "$3957tyerfgewrf384",
      "type": "m.room.message",
      "sender": "@exampleuser:matrix.org",
      "sender_display_name": "Major Tom",
      "room_name": "Mission Control",
      "room_alias": "#exampleroom:matrix.org",
      "prio": "high",
      "content": {
        "msgtype": "m.text",
        "body": "I'm floating in a most peculiar way."
      }
     },
     "counts": {
       "unread" : 2,
       "missed_calls": 1
     }
     "devices": [
       {
         "app_id": "org.matrix.matrixConsole.ios",
         "pushkey": "V2h5IG9uIGVhcnRoIGRpZCB5b3UgZGVjb2RlIHRoaXM/",
         "pushkey_ts": 12345678,
         "data" : {
         },
         "tweaks": {
           "sound": "bing.wav"
          }
        }
      ]
    }
  }

The contents of this dictionary are defined as follows:

id
  An identifier for this notification that may be used to detect duplicate
  notification requests. This is not necessarily the ID of the event that
  triggered the notification.
type
  The type of the event as in the event's 'type' field.
sender
  The sender of the event as in the corresponding event field.
sender_display_name
  The current display name of the sender in the room in which the event
  occurred.
room_name
  The name of the room in which the event occurred.
room_alias
  An alias to display for the room in which the event occurred.
prio
  The priority of the notification. Acceptable values are 'high' or 'low. If
  omitted, 'high' is assumed. This may be used by push gateways to deliver less
  time-sensitive notifications in a way that will preserve battery power on
  mobile devices.
content
  The 'content' field from the event, if present. If the event had no content
  field, this field is omitted.
counts
  This is a dictionary of the current number of unacknowledged communications
  for the recipient user. Counts whose value is zero are omitted.
unread
  The number of unread messages a user has accross all of the rooms they are a
  member of.
missed_calls
  The number of unacknowledged missed calls a user has accross all rooms of
  which they are a member.
device
  This is an array of devices that the notification should be sent to.
app_id
  The app_id given when the pusher was created.
pushkey
  The pushkey given when the pusher was created.
pushkey_ts
  The unix timestamp (in seconds) when the pushkey was last updated.
data
  A dictionary of additional pusher-specific data. For 'http' pushers, this is
  the data dictionary passed in at pusher creation minus the 'url' key.
tweaks
  A dictionary of customisations made to the way this notification is to be
  presented. These are added by push rules.
sound
  Sets the sound file that should be played. 'default' means that a default
  sound should be played.

The recipient of an HTTP notification should respond with an HTTP 2xx response
when the notification has been processed. If the endpoint returns an HTTP error
code, the Home Server should retry for a reasonable amount of time with a
reasonable backoff scheme.

The endpoint should return a JSON dictionary as follows::

  {
    "rejected": [ "V2h5IG9uIGVhcnRoIGRpZCB5b3UgZGVjb2RlIHRoaXM/" ]
  }

Whose keys are:

rejected
  A list of all pushkeys given in the notification request that are not valid.
  These could have been rejected by an upstream gateway because they have
  expired or have never been valid. Home Servers must cease sending notification
  requests for these pushkeys and remove the associated pushers. It may not
  necessarily be the notification in the request that failed: it could be that
  a previous notification to the same pushkey failed.

Push: Recommendations for APNS
------------------------------
For sending APNS notifications, the exact format is flexible and up to the
client app and its push gateway to agree on (since APNS requires that the sender
have a private key owned by the app developer, each app must have its own push
gateway). However, Matrix strongly recommends:

 * That the APNS token be base64 encoded and used as the pushkey.
 * That a different app_id be used for apps on the production and sandbox
   APS environments.
 * That APNS push gateways do not attempt to wait for errors from the APNS
   gateway before returning and instead to store failures and return
   'rejected' responses next time that pushkey is used.
