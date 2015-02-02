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


Push Rules
----------
Home Servers have an interface to configure what events trigger notifications.
This behaviour is configured through 'Push Rules'. Push Rules come in a variety
of different kinds and each kind of rule has an associated priority. The
different kinds of rule, in descending order of priority, are:

Override Rules
  The highest priority rules are user-configured overrides.
Content Rules
  These configure behaviour for (unencrypted) messages that match certain
  patterns. Content rules take one parameter, 'pattern', that gives the pattern
  to match against. This is treated in the same way as pattern for event_match
  conditions, below.
Room Rules
  These change the behaviour of all messages to a given room. The rule_id of a
  room rule is always the room that it affects.
Sender
  These rules configure notification behaviour for messages from a specific,
  named Matrix user ID. The rule_id of Sender rules is always the Matrix user
  ID of the user whose messages theyt apply to.
Underride
  These are identical to override rules, but have a lower priority than content,
  room and sender rules.
Default
  These are rules provided by the home server and cannot be changed by the user.
  They are the lowest priority rule and establish baseline behaviour.

In addition, each kind of rule except default may be either global or
device-specific. Device specific rules only affect delivery of notifications via
pushers with a matching instance_handle. All device-specific rules are higher
priority than all global rules. Thusly, the full list of rule kinds, in
descending priority order, is as follows:

 * Device-specific Override
 * Device-specific Content
 * Device-specific Room
 * Device-specific Sender
 * Device-specific Underride
 * Global Override
 * Global Content
 * Global Room
 * Global Sender
 * Global Underride
 * Global Default

For some kinds of rule, rules of the same kind also have an ordering with
respect to one another. The kinds that do not are room and sender rules where
the rules are mutually exclusive by definition and therefore an ordering would
be redundant. Actions for the highest priority rule and only that rule apply
(for example, a set_sound action in a lower priority rule will not apply if a
higher priority rule matches, even if that rule does not specify a sound).

Rules also have an identifier, rule_id, which is a string.

Push Rules: Actions:
--------------------
All rules have an associated list of 'actions'. An action affects if and how a
notification is delievered for a matching event. This standard defines the
following actions, although if Home servers wish to support more, they are free
to do so:

notify
  This causes each matching event to generate a notification.
dont_notify
  Prevents this event from generating a notification
coalesce
  This enables notifications for matching events but activates Home Server
  specific behaviour to intelligently coalesce multiple events into a single 
  notification. Not all Home Servers may support this. Those that do not should
  treat it as the 'notify' action.
set_sound
  Sets the value 'sound' key that is sent in the notification poke. This has an
  associated string which is the value to set the 'sound' key to.

Actions that have no parameter are represented as a string. Those with a
parameter are represented as a dictionary with a single key/value pair where the
key is the name of the action and the value is the parameter, eg. { "set_sound":
"ping.wav" }

Push Rules: Conditions:
-----------------------
Override, Underride and Default rules have a list of 'conditions'. All
conditions must hold true for an event in order for a rule to be applied to an
event. Matrix specifies the following conditions, although if Home Servers wish
to support others, they are free to do so:

event_match
  This is a glob pattern match on a field of the event. Parameters:
   * 'key': The dot-separated field of the event to match, eg. content.body
   * 'pattern': The glob-style pattern to match against. Patterns with no
                special glob characters should be treated as having asterisks
                prepended and appended when testing the condition.
device
  Matches the instance_handle of the device that the notification would be
  delivered to. Parameters:
   * 'instance_handle': The instance_handle of the device.
contains_display_name
  This matches unencrypted messages where content.body contains the owner's
  display name in that room. This is a separate rule because display names may
  change and as such it would be hard to maintain a rule that matched the user's
  display name. This condition has no parameters.
room_member_count
  This matches the current number of members in the room.
   * 'is': A decimal integer optionally prefixed by one of, '==', '<', '>',
     '>=' or '<='. A prefix of '<' matches rooms where the member count is
     strictly less than the given number and so forth. If no prefix is present,
     this matches rooms where the member count is exactly equal to the given
     number (ie. the same as '==').

Room, Sender, User and Content rules do not have conditions in the same way,
but instead have predefined conditions, the behaviour of which can be configured
using parameters named as described above. In the cases of room and sender
rules, the rule_id of the rule determines its behaviour.

