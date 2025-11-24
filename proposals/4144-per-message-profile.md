# MSC4144: Per-message profiles
Currently profiles in Matrix are defined by `m.room.member` state events, and
there is no easy way to have different profiles per message.

## Proposal
The proposed solution is a new field called `m.per_message_profile`, which
contains a displayname and/or avatar URL to override the default profile,
plus an ID to identify different profiles within the same Matrix user.

```json
{
  "msgtype": "m.text",
  "body": "Hello, World!",
  "m.per_message_profile": {
    "id": "meow",
    "displayname": "cat",
    "avatar_url": "mxc://maunium.net/hgXsKqlmRfpKvCZdUoWDkFQo"
  }
}
```

The `id` field is required and is an opaque string. Clients may use it to group
messages with the same ID like they would group messages from the same sender.
For example, bridges would likely set it to the immutable remote user ID.

This ID is scoped to the real MXID used to send the event, but is otherwise
global. In other words, the same ID in different rooms from the same account
can be considered to be the same user, but the same ID in the same room from
different accounts are considered to be different users.

The field is allowed for all message events, which currently means
`m.room.message` and `m.sticker`. A future MSC may expand the field to other
events, such as reactions.

### Field limits
After JSON decoding, `id` and `displayname` MUST be at most 255 bytes of UTF-8
and every code point MUST be a Unicode scalar. Null bytes (`\u0000`) are not
allowed.

Like with other images and avatars, clients should ignore any avatar URL that
is not a `mxc://` URI.

### Encrypted avatars
Because the profile is inside the ciphertext in encrypted events, the entire
profile can be hidden from the server, as long as the avatar is also encrypted.
Encrypted avatars are placed under `avatar_file` instead of `avatar_url`.
The `avatar_file` field has the same schema as the `file` field in
`m.room.message` events.

<details>
<summary>Encrypted avatar example</summary>

```json
{
  "msgtype": "m.text",
  "body": "Hello, World!",
  "m.per_message_profile": {
    "id": "meow",
    "displayname": "cat",
    "avatar_file": {
      "v": "v2",
      "key": {
        "alg": "A256CTR",
        "ext": true,
        "k": "8dXeBMBMthuXGY5zmUh9Mi0aqC1kndMZ4NCa-0RhELc",
        "key_ops": [
          "encrypt",
          "decrypt"
        ],
        "kty": "oct"
      },
      "iv": "L6zup2cR570AAAAAAAAAAA",
      "hashes": {
        "sha256": "/cTs+PajUcznbV3h1w5gh1AHnLjrKQVl2jU3xLCqoBI"
      },
      "url": "mxc://maunium.net/eKLhozQduElYSgBkWjtwSXoi"
    }
  }
}
```

</details>

### Behavior of omitted and empty fields
If the `displayname` field is omitted, null, or an empty string, the
displayname from the member event should be used instead. Setting an empty
displayname using a per-message profile is not supported, as there aren't any
clear use cases for it.

However, there are use cases for setting an empty avatar, so `avatar_url` being
an empty string should be treated as clearing the avatar and falling back to
the client's default blank avatar behavior (e.g. generating one based on the
displayname). If both `avatar_url` and `avatar_file` are omitted or null, the
avatar from the member event should be used instead. If the member event does
not have an avatar defined either, and the client uses the displayname to
generate fallback avatars, it should use the per-message displayname for the
fallback avatar rather than the global one.

### Extensible profiles
This MSC is not related to extensible profiles and does not attempt to
implement them. However, in case extensible profiles are implemented as
something that can be referenced (e.g. room IDs), the MSC adding them could
allow per-message profiles to specify which extensible profile is used.

### Fallbacks for old clients
In order for users on old clients to see the per-message profile data, sending
clients SHOULD include a fallback containing the per-message displayname.
When a fallback is used, the per-message profile object MUST include
`"has_fallback": true`.

#### Plaintext fallback
The fallback MUST be at the beginning of the plaintext `body` and consist of
the exact value of the `displayname` property, followed by a colon (`:`) and
a space (`\x20`), e.g. `cat: original message`.

To remove the plaintext fallback, trim the prefix `{displayname}: ` from the body.

#### HTML fallback
If a `formatted_body` of type `org.matrix.custom.html` is present, it SHOULD
include the same fallback text inside a `strong` tag with the `data-mx-profile-fallback`
attribute, e.g. `<strong data-mx-profile-fallback>cat: </strong>original message`.

The displayname MUST be HTML-escaped and there MUST NOT be any HTML tags inside
the fallback. The tag MUST NOT have any other attributes. The attribute MAY
have an empty string as its value (`=""`) for compatibility with all HTML
generators, but MUST NOT have any other value. The HTML fallback is not mandated
to be at the beginning of the string, as there may be valid reasons to put it
inside another tag, such as a `<p>` tag.

To remove the HTML fallback, either use a HTML parser to drop the entire `strong`
tag with a `data-mx-profile-fallback` attribute, or replace matches of the
following regex with an empty string: `<strong\s+data-mx-profile-fallback(?:="")?\s*>([^<]+): </strong\s*>`

#### Other details
If a fallback is used in a media message, the `filename` property MUST be set
to ensure the `body` is treated as a caption rather than a file name.

Fallbacks MUST only be used when the `displayname` property is a non-empty
string, i.e. they are not used when falling back to the member event name.

#### Example with fallback
```json
{
  "msgtype": "m.text",
  "body": "cat: Hello, World!",
  "format": "org.matrix.custom.html",
  "formatted_body": "<p><strong data-mx-profile-fallback>cat: </strong>Hello, World!</p>",
  "m.per_message_profile": {
    "id": "meow",
    "displayname": "cat",
    "avatar_url": "mxc://maunium.net/hgXsKqlmRfpKvCZdUoWDkFQo",
    "has_fallback": true
  }
}
```

## Use cases

### Bridging
Per-message profiles will allow making "lighter-weight" bridges that don't need
appservice access. Currently the only option for such bridges is to prepend the
displayname to the message, which is extremely ugly. Even though they're ugly,
there are still rooms that use bot-based bridges like matterbridge, which shows
there's demand for bridging without requiring server admin access.

Such bridges would obviously have downsides, like not being able to start chats
via standard mechanisms, and not being able to see the member list on Matrix.
However, those may be acceptable compromises for non-puppeting bridges that
only operate in specific predetermined rooms. Non-message events like reactions
are also not supported by this MSC, but they could be allowed in the future.

This method also allows encrypting profile info, which reduces metadata leaked
by bridging.

### Feature-parity with other platforms
Other chat applications such as Slack and Discord have "webhooks" which allow
per-message profile overrides. This MSC effectively enables the same on Matrix.

For example, Discord's [execute webhook](https://discord.com/developers/docs/resources/webhook#execute-webhook)
API takes `username` and `avatar_url` as optional parameters.

### Roleplaying, plural users, etc
Some users want to be able to switch between profiles quickly, which would be
much easier using this MSC. Currently easiest way is to have multiple accounts,
which has other benefits, but is much more cumbersome to manage.

## Potential issues
Implementing encrypted avatars could cause difficulty for clients that assume
that avatars are always unencrypted mxc URIs.

When per-message profiles are used for bridging, there's no way to mention
specific users, as mentions will just target the single bridge bot. A future
MSC could define a way to specify which profile to mention.

## Alternatives
### New state events
Per-message profiles could be transmitted more compactly by defining the profile
in a new state event and only referencing the state key in the message event.
However, that approach wouldn't enable encrypting per-message profiles without
inventing encrypted state events. Additionally, even with encrypted state
events, some kind of sender identifiers would be leaked via state keys.

### Appservices
Appservices work perfectly fine for bridging already now, but they require
admin access to a server, which is not available for everyone. Additionally,
they have similar metadata issues as the "New state events" alternative above.

For use cases involving a single human user, having multiple mxids (regardless
of whether they're registered manually or via an appservice) complicates things
unnecessarily.

## Security considerations

### Preventing impersonation
To prevent impersonation using per-message profiles, clients MUST somehow
indicate to the user that the message has a per-message profile with an easy
way to see the user's MXID or default profile. For example, a client could have
a small `via @user:example.com` text next to the per-message displayname.

To improve user experience, clients MAY omit the indicator when the sender
account has sufficiently high power level, and the displayname is unique among
members of the room (i.e. it does not require disambiguation in the
["Calculating the display name for a user" spec](https://spec.matrix.org/v1.12/client-server-api/#calculating-the-display-name-for-a-user)).

The recommended power level to check is the level for a `m.per_message_profile`
state event (i.e. check `events` -> `m.per_message_profile` and fall back to
`state_default` if not set).

## Unstable prefix
`com.beeper.per_message_profile` should be used instead of `m.per_message_profile`
until this MSC is accepted.
