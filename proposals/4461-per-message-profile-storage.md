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
    "meow": {
      "id": "cat",
      "displayname": "Cat 🐈️"
    },
    "mrrp": {
      "id": "black_cat",
      "displayname": "🐈‍⬛",
      "avatar_url": "mxc://maunium.net/hgXsKqlmRfpKvCZdUoWDkFQo"
    }
  }
}
```

A client could then have a `/profile` command to pick a profile when sending
a message, such that `/profile mrrp hello` turns into

```
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

## Security considerations
This proposal only adds a way to store reusable profile data.
Security considerations with per-message profiles are covered in [MSC4144]

## Unstable prefix
`fi.mau.msc4461.per_message_profiles` can be used instead of
`m.per_message_profiles` in global account data.

## Dependencies
This MSC builds on [MSC4144], which at the time of writing has not yet been
accepted into the spec.
