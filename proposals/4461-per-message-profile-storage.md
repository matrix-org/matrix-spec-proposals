# MSC4461: Storing per-message profiles for users
[MSC4144] introduces per-message profiles, which allow users and bots to
override their profile info for a single message. The original use case was
primarily bots, but the feature is useful for humans too. However, humans don't
like re-entering their profile info every time they send a message. Therefore,
a method for storing reusable profiles is needed.

[MSC4144]: https://github.com/matrix-org/matrix-spec-proposals/pull/4144

## Proposal
A new `m.per_message_profiles` account data event is introduced. The event
contains a list of [MSC4144] profiles in the `profiles` array, plus an optional
`default_profile_id` indicating which profile to use if none of the triggers
match. The event can be used both in global account data and room account data.

```json
{
  "type": "m.per_message_profiles",
  "content": {
    "default_profile_id": null,
    "profiles": [
      {
        "id": "cat",
        "displayname": "Cat 🐈️",
        "triggers": [
          {"prefix": "meow ", "suffix": " meow", "keep_trigger": true},
          {"prefix": "cat: "}
        ]
      },
      {
        "id": "black_cat",
        "displayname": "🐈‍⬛",
        "avatar_url": "mxc://maunium.net/hgXsKqlmRfpKvCZdUoWDkFQo",
        "triggers": [
          {"prefix": "mrrp:"}
        ]
      }
    ]
  }
}
```

`id`, `displayname` and `avatar_url` come from MSC4144 and are copied as-is when
sending a message. All unknown fields (i.e. everything except `triggers` defined
below) SHOULD be copied into the message as well.

### Triggers
In addition to the standard MSC4144 fields, each profile can contain a new field
called `triggers`, which defines ways to use the profile conveniently. It's
intended to be private and MUST be excluded when copying the profile into an
outgoing message. Specifying triggers is not required.

Each trigger can contain one or more conditions. This MSC defines two: `prefix`
and `suffix`, which require the input text to start with or end with the
specified string respectively. When a trigger matches, the relevant prefix
and/or suffix is removed from the text, unless the `keep_trigger` field is set
to `true`. If both are present, the input must both start with the prefix and
end with the suffix to match, and the prefix and suffix must not overlap.

Triggers are checked in order such that all triggers of the first profile take
priority over the second profile. Per-room profiles always take priority over
global profiles.

The triggers defined in this MSC are case-sensitive. They don't require extra
whitespace or any special characters, but the string itself can contain those.
For example, `cat:meow` would not match any of the profiles above, only
`cat: meow` would. Clients MAY trim out additional leading or trailing
whitespace after removing the trigger.

For example, with the profiles above, if the user types `mrrp:hello`, it would
send the following message event:

```json
{
  "type": "m.room.message",
  "content": {
    "msgtype": "m.text",
    "body": "🐈‍⬛: hello",
    "format": "org.matrix.custom.html",
    "formatted_body": "<p><strong data-mx-profile-fallback>🐈‍⬛: </strong>hello</p>",
    "m.per_message_profile": {
      "id": "black_cat",
      "displayname": "🐈‍⬛",
      "avatar_url": "mxc://maunium.net/hgXsKqlmRfpKvCZdUoWDkFQo",
      "has_fallback": true
    }
  }
}
```

### Default profile
If none of the triggers match and the user hasn't otherwise indicated a specific
profile they want to use, clients SHOULD use the profile whose `id` is set in
the `default_profile_id` field.

Room account data is preferred for choosing the default profile. If no
`default_profile_id` field is set in room account data, or if the value is
`null`, the global value is used instead. If the value is an empty string, then
no profile is used by default, even if there is a global value.

Note: Disabling the default profile is done using an empty string instead of
`null` because telling apart `null` and `undefined` is difficult in many
languages.

## Potential issues
Users with lots of profiles can end up with a large account data event, but
it's unlikely to be larger than existing big account data like push rules or
`m.direct`.

Since it's a single account data event, editing can hit race conditions. It's
likely not a problem, as it's only edited directly by humans (as opposed to
something like `m.direct`, which clients may update in the background).

## Alternatives
There are various other user-local places where profiles could be stored. Some
options that weren't chosen:

* Dedicated [profile rooms](https://github.com/matrix-org/matrix-spec-proposals/pull/4201)
  for each profile.
  * Rejected as it's much more complicated
* State events in rooms
  * Normal users can't send custom state events in most rooms, plus it would
    require duplicating profiles in each room.
* Multiple account data events (à la Sable's original implementation)
  * The only benefit would be avoiding race conditions if the user modifies
    profiles from multiple clients at once, which isn't really worth the extra
    complication.

Instead of an array, the event could be a map of shortcode to profile. However,
that would require duplicating the content if the user wants multiple prefixes
for the same profile. It would also not allow extensibility for triggers.

## Security considerations
This proposal only adds a way to store reusable profile data.
Security considerations with per-message profiles are covered in [MSC4144]

## Unstable prefix
`fi.mau.msc4461.per_message_profiles.v3` can be used instead of
`m.per_message_profiles` in global account data.

`triggers` doesn't have a prefix as it's only contained inside the already
prefixed account data event, and it must not be sent in actual messages.

### Earlier revisions
`fi.mau.msc4461.per_message_profiles.v2` used a different format for triggers
and only defined prefixes. It can be found at [8a8cfa7](https://github.com/matrix-org/matrix-spec-proposals/blob/8a8cfa7c0e94cd58f540ca4233a5a25fe80b7a61/proposals/4461-per-message-profile-storage.md).

`fi.mau.msc4461.per_message_profiles` used a map instead of an array.
It can be found at [c42d954a](https://github.com/matrix-org/matrix-spec-proposals/blob/c42d95a3c171e2d7e355f89d50b7d0e918c73248/proposals/4461-per-message-profile-storage.md).

## Dependencies
This MSC builds on [MSC4144], which at the time of writing has not yet been
accepted into the spec.
