Push Notifications
==================

Pushers
-------
To receive any notification pokes at all, it is necessary to configure a
'pusher' on the Home Server that you wish to receive notifications from. There
is a single API endpoint for this::

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
profile_tag
  This is a string that determines what set of device rules will be matched when
  evaluating push rules for this pusher. It is an arbitrary string. Multiple
  devices maybe use the same profile_tag. It is advised that when an app's
  data is copied or restored to a different device, this value remain the same.
  Client apps should offer ways to change the profile_tag, optionally copying
  rules from the old profile tag.
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
  room rule is always the ID of the room that it affects.
Sender
  These rules configure notification behaviour for messages from a specific,
  named Matrix user ID. The rule_id of Sender rules is always the Matrix user
  ID of the user whose messages theyt apply to.
Underride
  These are identical to override rules, but have a lower priority than content,
  room and sender rules.

In addition, each kind of rule may be either global or device-specific. Device
specific rules only affect delivery of notifications via pushers with a matching
profile_tag. All device-specific rules are higher priority than all global
rules. Thusly, the full list of rule kinds, in descending priority order, is as
follows:

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

For some kinds of rule, rules of the same kind also have an ordering with
respect to one another. The kinds that do not are room and sender rules where
the rules are mutually exclusive by definition and therefore an ordering would
be redundant. Actions for the highest priority rule and only that rule apply
(for example, a set_tweak action in a lower priority rule will not apply if a
higher priority rule matches, even if that rule does not specify any tweaks).

Rules also have an identifier, rule_id, which is a string. The rule_id may
alphanumeric characters only. The rule_id is unique within the kind of rule and
scope: rule_ids need not be unique between rules of the same kind on different
devices. 

A home server may also have server default rules of each kind and in each scope.
Server default rules are lower priority than user-defined rules in eacgh scope.
Server defined rules do not have a rule_id. A rule has a rule_id if and only if
it is a user-defined rule.

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
set_tweak
  Sets an entry in the 'tweaks' dictionary key that is sent in the notification
  poke. This takes the form of a dictionary with a 'set_tweak' key whose value
  is the name of the tweak to set.  It must also have a 'value' key which is
  the value to which it should be set.

Actions that have no parameters are represented as a string. Otherwise, they are
represented as a dictionary with a key equal to their name and other keys as
their parameters, eg. { "set_tweak": "sound", "value": "default" }

Push Rule Actions: Tweaks
-------------------------
The 'set_tweak' key action is used to add an entry to the 'tweaks' dictionary
that is sent in the notification poke. The following tweaks are e defined:

sound
  A sound to be played when this notification arrives. 'default' means to
  play a default sound.

Tweaks are passed transparently through the Home Server so client applications
and push gateways may agree on additional tweaks, for example, how to flash the
notification light on a mobile device.

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
profile_tag
  Matches the profile_tag of the device that the notification would be
  delivered to. Parameters:
   * 'profile_tag': The profile_tag to match with.
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

Push Rules: API
---------------
Rules live under a hierarchy in the REST API that resembles::

  $PREFIX/pushrules/<scope>/<kind>/<rule_id>

The component parts are as follows:

scope
  Either 'global' or 'device/<profile_tag>' to specify global rules or
  device rules for the given profile_tag.
kind
  The kind of rule, ie. 'override', 'underride', 'sender', 'room', 'content'.
rule_id
  The identifier for the rule.

To add or change a rule, a client performs a PUT request to the appropriate URL.
When adding rules of a type that has an ordering, the client can add parameters
that define the priority of the rule:

before
  Use 'before' with a rule_id as its value to make the new rule the next-more
  important rule with respect to the given rule.
after
  This makes the new rule the next-less important rule relative to the given
  rule.

All requests to the push rules API also require an access_token as a query
paraemter.

The content of the PUT request is a JSON object with a list of actions under the
'actions' key and either conditions (under the 'conditions' key) or the
appropriate parameters for the rule (under the appropriate key name).

Examples:

To create a rule that suppresses notifications for the room with ID '!dj234r78wl45Gh4D:matrix.org'::

  curl -X PUT -H "Content-Type: application/json" -d '{ "actions" : ["dont_notify"] }' "http://localhost:8008/_matrix/client/api/v1/pushrules/global/room/%21dj234r78wl45Gh4D%3Amatrix.org?access_token=123456"

To suppress notifications for the user '@spambot:matrix.org'::

  curl -X PUT -H "Content-Type: application/json" -d '{ "actions" : ["dont_notify"] }' "http://localhost:8008/_matrix/client/api/v1/pushrules/global/sender/%40spambot%3Amatrix.org?access_token=123456"

To always notify for messages that contain the work 'cake' and set a specific sound (with a rule_id of 'SSByZWFsbHkgbGlrZSBjYWtl')::

  curl -X PUT -H "Content-Type: application/json" -d '{ "pattern": "cake", "actions" : ["notify", {"set_sound":"cakealarm.wav"}] }' "http://localhost:8008/_matrix/client/api/v1/pushrules/global/content/SSByZWFsbHkgbGlrZSBjYWtl?access_token=123456"

To add a rule suppressing notifications for messages starting with 'cake' but ending with 'lie', superseeding the previous rule::

  curl -X PUT -H "Content-Type: application/json" -d '{ "pattern": "cake*lie", "actions" : ["notify"] }' "http://localhost:8008/_matrix/client/api/v1/pushrules/global/content/U3BvbmdlIGNha2UgaXMgYmVzdA?access_token=123456&before=SSByZWFsbHkgbGlrZSBjYWtl"

To add a custom sound for notifications messages containing the word 'beer' in any rooms with 10 members or fewer (with greater importance than the room, sender and content rules)::

  curl -X PUT -H "Content-Type: application/json" -d '{ "conditions": [{"kind": "event_match", "key": "content.body", "pattern": "beer" }, {"kind": "room_member_count", "is": "<=10"}], "actions" : ["notify", {"set_sound":"beeroclock.wav"}] }' "http://localhost:8008/_matrix/client/api/v1/pushrules/global/override/U2VlIHlvdSBpbiBUaGUgRHVrZQ?access_token=123456


To delete rules, a client would just make a DELETE request to the same URL::

  curl -X DELETE "http://localhost:8008/_matrix/client/api/v1/pushrules/global/room/%23spam%3Amatrix.org?access_token=123456"


Retrieving the current ruleset can be done either by fetching individual rules
using the scheme as specified above. This returns the rule in the same format as
would be given in the PUT API with the addition of a rule_id::

  curl "http://localhost:8008/_matrix/client/api/v1/pushrules/global/room/%23spam%3Amatrix.org?access_token=123456"

Returns::

  {
    "actions": [
        "dont_notify"
    ],
    "rule_id": "#spam:matrix.org"
  }

Clients can also fetch broader sets of rules by removing path components.
Requesting the root level returns a structure as follows::

  {
      "device": {
          "exampledevice": {
              "content": [],
              "override": [],
              "room": [
                  {
                      "actions": [
                          "dont_notify"
                      ],
                      "rule_id": "#spam:matrix.org"
                  }
              ],
              "sender": [],
              "underride": []
          }
      },
      "global": {
          "content": [],
          "override": [],
          "room": [],
          "sender": [],
          "underride": []
      }
  }

Adding patch components to the request drills down into this structure to filter
to only the requested set of rules.

