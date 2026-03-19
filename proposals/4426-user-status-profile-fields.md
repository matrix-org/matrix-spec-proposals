# MSC4426: User Status Profile Fields

A helpful feature in today’s messengers is the ability to communicate whether a
user is currently available to talk. This can take the form of communicating
when the user was last seen to read receipts and typing notifications.

When working in a team, it can be useful to share more rich information. A short
blurb about what you’re currently up to, whether you’re currently on holiday, or
if you’re in a meeting and won’t be looking at messages for a short while.

This proposal builds on top of the [Custom Profile
Fields](https://spec.matrix.org/v1.17/client-server-api/#profiles) feature to
provide a place to store a user’s current "status". It is made up of a short
text string and an emoji. The emoji can be anything the user wants - but it is
assumed to be used as a shorthand summary of their current state. For example:

- 🔴 Morning standup
- 🌴 On holiday til 23/08
- 🏃 AFK - out at the dentist

This primarily reduces frustrating situations when others try to contact you,
believing you’re around, and ending up waiting a while to receive a response.

While manually setting your status before going on holiday is feasible, doing so
before and after every meeting in a workday is not. Therefore, it would be ideal
if one's status could be programmatically set when they join or leave a call, while
still maintaining their manually-set status afterwards.

This proposal outlines two new custom profile fields (`m.status`, `m.call`) that
satisfy the above use cases, while leaving the door open for future fields to
further enhance a user's profile.

## Proposal

### New Profile Fields

`m.status`

A text-only field describing the user’s current state, along with an emoji. The
emoji can be useful as a compact summary, or just for fun.

| Field | Type | Required | Description | Example |
| :---- | :---- | :---- | :---- | :---- |
| `text` | `string` | Yes | The user’s chosen status text. Does not support HTML. Clients SHOULD NOT linkify links to deter users from accidentally visiting malicious content. | “On holiday in …” |
| `emoji` | `string` | Yes | The user’s chosen status emoji. | 🌴 |

*Note: A future MSC may add an additional field to support custom emotes, ala.
[MSC2545](https://github.com/matrix-org/matrix-spec-proposals/pull/2545).*

Applications SHOULD NOT automatically update this field. It’s intended to be
controlled by the user manually, and it may be confusing for most users if their
manually-set status is overridden by an application they may have no control
over.

Instead, applications should prefer to use other profile fields, such as
`m.call`, which would typically not be managed manually by a user. Future
proposal may define further fields for other applications (what game is a user
playing, etc.).

#### `text` and `emoji` field grammar

The `text` field is encoded UTF-8, and limited to 256 bytes. The `emoji` field
is limited to 32 bytes. Homeservers SHOULD reject statuses that contain fields
which exceed these limits with status code `400` and errcode `M_TOO_LARGE.`
Homeservers SHOULD NOT reject `m.status` entries containing an `emoji` field
with more than one grapheme. This is due to Unicode byte to grapheme definitions
being continuous added over time.

`m.call`

An indicator that the user is currently in a call, and optionally how long
they’ve been in the call.

| Field | Type | Required | Description | Example |
| :---- | :---- | :---- | :---- | :---- |
| `call_joined_ts` | `number` | No | The time that the user joined the call. Unix timestamp in seconds. This allows users to see how long someone has been in a call. | 1770140640 |

### Setting a status

A user can set their status by using the existing [`PUT
/_matrix/client/v3/profile/{userId}/{keyName}`](https://spec.matrix.org/v1.17/client-server-api/#put_matrixclientv3profileuseridkeyname)
endpoint.

**Example**

`PUT /_matrix/client/v3/profile/@alice:example.org/m.status`

```json
{
  "text": "AFK - out at the dentist",
  "emoji": "🏃"
}
```

### Getting a status

A user can get any of their own, or another user’s, profile fields on-demand by
using the existing specific [`GET
/_matrix/client/v3/profile/{userId}/{keyName}`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3profileuseridkeyname)
endpoint or the generic [`GET
/_matrix/client/v3/profile/{userId}`](https://spec.matrix.org/v1.17/client-server-api/#get_matrixclientv3profileuserid)
to get all profile fields.

**Example**

`GET /_matrix/client/v3/profile/@alice:example.org/m.call`

```json
{
  "call_joined_ts": 1770140640
}
```

#### Displaying status

A client that receives both `m.status` and `m.call` profile fields may choose
their own logic to display one over the other in various parts of the UI, or
both.

### Clearing a status

A user or application may remove a status field by using the existing [`DELETE
/_matrix/client/v3/profile/{userId}/{keyName}`](https://spec.matrix.org/v1.17/client-server-api/#delete_matrixclientv3profileuseridkeyname)
endpoint.

**Example**

For instance, after a user has left a call:

`DELETE /_matrix/client/v3/profile/@alice:example.org/m.call`

```json
{}
```

There is currently no mechanism to remove multiple fields in a single request,
just as there is no mechanism to set multiple fields at once.

## Potential Issues

#### Moderation

A free-form, user-controlled text field that can be displayed in clients to
other users is a prime opportunity for spammers and malicious actors. Attacks
include:
  * Displaying hate speech
  * Linking to malware/phishing content
  * With custom emoji support, displaying explicit/illegal imagery by their display name across the app

As user status is tied to a user - rather than a room - simply kicking a user
from a room may not immediately solve the issue.  

* Clients should take care not to display associated status emoji/text in
  membership change messages (i.e. “User 🌴 was kicked from the room).  
* The emoji in question may appear in the results of a user search (clients
  SHOULD NOT display these by default. Instead, require the user to perform
  some explicit action first, e.g. inviting the user to a room or DM.)  
* To remove offensive material from the room timeline and members list, a
  moderator should kick/ban the user. A client that displays the status
  information in the timeline should stop doing so if the user has left/been
  kicked from the room.

### Internationalisation

Often a user may set their status in one language, and it will be viewed by a
user who primarily uses another language. This MSC explicitly does not include a
method for setting multiple statuses in multiple languages:

1. This would expand the scope of implementation noticeably.
2. A UI where a user could set multiple statuses in different languages is not
   something users are familiar with in messaging apps today.

Clients are free to provide some suggested default status texts and emoji, and
they may do so based on the user's chosen language in the application.

A future MSC may allow setting a different status *per-community*, which would
be a more familiar way for users to communicate in different languages with
different social groups.

### The `emoji` field can accept multiple emoji

The `emoji` field in `m.status` technically allows for multiple emoji. It is
expected that client UI encourages setting only a single emoji in this field -
yet the possibility is left open to set more if desired. This allows for users
to use multiple emoji if desired, or use a unicode character that an older
homeserver doesn’t yet understand.

Expanding on the latter, if a user wanted to use some theoretical future emoji
that was “a family of firefighters”, that might be made up of
“🧑‍🚒([zwj](https://en.wikipedia.org/wiki/Zero-width_joiner))🧑‍🚒(zwj)🧑‍🚒(zwj)🧑‍🚒”.

If the homeserver was trying to limit `emoji` to a single grapheme, its emoji
parser - which hadn’t been updated to the latest unicode - may reject this
emoji, even if it’s valid to the client and other clients.

### Performance

While this MSC is intended to just add a couple new profile fields, the question
of performance came up almost immediately. Especially with the performance of
[Presence](https://spec.matrix.org/v1.17/client-server-api/#presence)
implementation being so poor today. Below are *implementation recommendations*.

While presence was mostly updated automatically, these profile fields will have
significantly different traffic patterns, and homeservers should design their
rate-limiting and debouncing mechanisms around this. It is also recommended to
allow sysadmins to configure these values based on their own deployments.

Homeservers should consider implementing limits on both a per-field and entire
profile basis for each user.

`m.status` may be be updated 1-5 times in a short burst very occasionally (as
someone updates their status, and then edits it to fix typos). Whereas `m.call`
may be updated 10 or more times (in pairs of joining/leaving) over the course of
a work day, as well as in rapid succession if someone is having issues joining a
call (debouncing would help here).

Neither of these fields need to be particularly *real-time* either, so waiting a
bit for updates before publishing them to other users can also be effective.

Much of the slow performance of presence stems from needing to inform hundreds
or thousands of other homeservers over federation after an update. Performance
over federation has been expanded upon further in MSC4259, see [this
thread](https://github.com/matrix-org/matrix-spec-proposals/pull/4259/files#r2858835260).
It's intended for federation-related performance discussion to continue there.

## Alternatives

### Single `m.status` field

Ditch `m.call` and have a single `m.status` field. Applications will have figure
out what to put in the field.  

This can lead to edge cases where an application may try to preserve the user's
chosen status by saving it locally (and restoring it later), yet this would
break down if another application tried to do the same (and couldn't access the
user's original status).

You also lose out on potentially expanding to future status-related profile
fields (what song one is currently listening to, what game one is currently
playing, etc.). Some clients may wish to display all of these independently on a
user's profile.

### Additional `m.holiday` field

It might be interesting to specify an additional `m.holiday` field, which one's
HR software could automatically update whenever a user goes on holiday at work.

Applications could take this as a stronger signal that a user is likely not to
reply, and display a warning when DM'ing or mentioning them.

This MSC proposes no downsides to specifying this field, but explicitly leaves
it out to reduce the scope of the proposal. A future MSC may add this once this
MSC has laid the groundwork.

Such a field is less pressing as `m.status` already allows a user to communicate
holiday status manually.

### Using presence as a transport

Using [Presence](https://spec.matrix.org/v1.17/client-server-api/#presence) was
initially considered for this use case. It has existed for a long time, already
features a `status_msg` field, and could easily have a `status_msg_emoji` field
added. It is already sent proactively to clients and over federation to other
homeservers.

But profile fields have a few advantages:

- They have simple semantics for multiple, distinct fields. This proposal
  introduces `m.status` and `m.call`. But if you eventually add `m.music`,
  `m.application/game`, `m.holiday` etc. you'd end up with quite a fat presence
  object with no way for clients to selectively query (or opt-in to selective
  updates via /sync) parts of it. You'd need to build out those semantics as well.
- Presence currently exists, but is disabled *everywhere*. Part of using
  presence is a political problem: you need to convince everyone to turn it back
  on. Many homeserver implementations and distributions disable it by default,
  which would significantly slow the roll-out of any feature built on top of it.

By decoupling ourselves from online/offline data, we're able to remove many
constraints that the presence feature has.

## Security Considerations

Users should not put security sensitive information in `m.status`. Clients MAY
wish to remind them of this.

## Privacy Considerations

A user status’ wouldn’t be encrypted. They’re intended to be public. Clients MAY
wish to remind them of this.

## Dependencies

None.

## Unstable Prefix

The following unstable prefixes should be used in place of the identifiers used
in this proposal.

| Stable identifier | Unstable identifier |
| :---- | :---- |
| `m.status` | `org.matrix.msc4426.status` |
| `m.call` | `org.matrix.msc4426.call` |
