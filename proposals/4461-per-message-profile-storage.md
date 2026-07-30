# MSC4461: Storing per-message profiles for users
[MSC4144] introduces per-message profiles, which allow users and bots to
override their profile info for a single message. The original use case was
primarily bots, but the feature is useful for humans too. However, humans don't
like re-entering their profile info every time they send a message. Therefore,
a method for storing reusable profiles is needed.

[MSC4144]: https://github.com/matrix-org/matrix-spec-proposals/pull/4144

## Proposal
A new `m.per_message_profiles` account data event is introduced. The event
content is a map from a user-defined profile "shortcode" to the per-message
profile data that gets sent in events. All fields inside the profile object
are defined by [MSC4144].

The shortcode is an arbitrary user-defined string, which can be used as a key
when selecting a profile to use. Arbitrary unicode is allowed, but spaces
SHOULD NOT be used, as clients that use a command-based UI might split
parameters on spaces.

```json
{
  "type": "m.per_message_profiles",
  "content": {
    "profiles": [
      {
        "id": "cat",
        "displayname": "Cat 🐈️",
        "trigger": {
          "prefix": ["meow ", "cat: "]
        }
      },
      {
        "id": "black_cat",
        "displayname": "🐈‍⬛",
        "avatar_url": "mxc://maunium.net/hgXsKqlmRfpKvCZdUoWDkFQo",
        "trigger": {
          "prefix": ["mrrp:"]
        }
      }
    ]
  }
}
```

`id`, `displayname` and `avatar_url` come from MSC4144 and are copied as-is when
sending a message.

`trigger` is a new field, which defines ways to use the profile conveniently.
It's defined as an object to allow future extensibility, such as suffix matches
or other kinds of triggers. It's intended to be private and MUST be excluded
when copying the profile into an outgoing message.

`prefix` is the only trigger defined by this MSC. It contains an array of
strings. If a message starts with one of the strings, the prefix is removed and
that profile is used for the message. Prefixes are checked in order such that
all prefixes of the first profile take priority over the second profile.
Prefixes are case-sensitive.

Using prefixes doesn't require extra whitespace or any special characters, but
the prefix itself can contain those. For example, `cat:meow` would not match any
of the profiles above, only `cat: meow` would. Clients MAY trim out additional
leading whitespace after removing the matched prefix.

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

## Potential issues
Users with lots of profiles can end up with a large account data event, but
it's unlikely to be larger than existing big account data like push rules or
`m.direct`.

Since it's a single account data event, editing can hit race conditions. It's
likely not a problem, as it's only edited directly by humans (as opposed to
something like `m.direct`, which clients may update in the background).

## Alternatives
There are various other places where profiles could be stored, like
[rooms](https://github.com/matrix-org/matrix-spec-proposals/pull/4201)
or multiple account data events. This proposal uses a single account
data event for simplicity.

Instead of an array, the event could be a map of shortcode to profile. However,
that would require duplicating the content if the user wants multiple prefixes
for the same profile. It would also not allow extensibility for triggers.

## Security considerations
This proposal only adds a way to store reusable profile data.
Security considerations with per-message profiles are covered in [MSC4144]

## Unstable prefix
`fi.mau.msc4461.per_message_profiles.v2` can be used instead of
`m.per_message_profiles` in global account data.

`trigger` doesn't have a prefix as it's only contained inside the already
prefixed account data event, and it must not be sent in actual messages.

## Dependencies
This MSC builds on [MSC4144], which at the time of writing has not yet been
accepted into the spec.
