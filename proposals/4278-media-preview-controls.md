# MSC4278: Media preview controls

Matrix caters to a wide variety of networks configurations. Some networks are closed and the users have a high
degree of safety, and other networks are open to the public internet and are inherently less safe. This proposal
aims to give the user more universal control over the content they see on Matrix, starting with media previews.

Most graphical Matrix clients display media in the timeline of a room with a preview. Often these are delivered
without any consent prompt, at least by default. This presents a risk to users who may be joining the network
and do not have the same safety barriers that experienced users may have configured.

With that in mind, this MSC provides a simple switch for users and homeservers to configure a global media preview
preference.

For the purposes of this MSC, the term "undesirable content" refers to images that the user does not want to see,
be it illegal, abusive or otherwise unwanted.


## Proposal

This proposal introduces a new account data key, `m.media_preview_config`.

This key contains the following content.

```json
{
  "media_previews": "off|private|on",
  "invite_avatars": "off|on"
}
```

### `media_previews`

A "media preview" is defined as any media in a room that may be rendered automatically without explicit
user consent.

Clients SHOULD show show or hide media depending upon this setting, on at least the following content types:

 - Media message types `m.image`, `m.video`, `m.file` which all can include thumbnail information or be thumbnailed
 by the homeserver.
 - The `m.sticker` event type.
 - Inline media via `img`.
 - Any event which includes thumbnail information or may be thumbnailed by the homeserver.

The above list is not exhaustive. Other MSCs SHOULD take this setting into account when rendering content that could
be considered a media preview, such as [MSC4027](https://github.com/matrix-org/matrix-spec-proposals/pull/4027). 

The one exception to the rule for now is user avatars in rooms the user has joined. For the purposes of this MSC,
by joining a room the user *has* consented to seeing the user avatars contained within. See the potential issues
section for a deeper explanation.

### `invite_avatars`

`invite_avatars` refers to any **room** avatar rendered in the client, where the client has a `membership` of `invite`.

This may typically be rendered in the form of an invite dialog, or a room list preview of a room.

The avatar may refer to:

 - The `m.room.avatar` state event.
 - The inviting user's `avatar_url` from their profile (in the case of a DM).

In *all* cases where an avatar may be rendered for a room invite, the preview MUST be controlled by this setting.

### Property value

#### `off`

The client MUST NOT show any previews for any media in affected rooms. Clients will hide the media entirely,
behind a click-to-view prompt, or some other mechanism where a user is either prevented entirely or must consent
to see the media.

Users MAY individually consent to seeing media, for example by clicking on a prompt to show a preview.
If consent is given, the client SHOULD then track that consent and show the media again in the future. The
mechanism for tracking opt-in/opt-out of media is left as an implementation detail.

#### `private`

Previews for media MAY be shown in "private" rooms without a prompt.
A private room is any room where:

 - The `m.room.join_rules` state exists
 - The `join_rule` key of this state is `invite`, `knock`, `restricted`, or `knock_restricted`.

If any other `join_rule` is set, or cannot be determined by the client then the assumption MUST be that the
room is public and previews MUST not be shown. Future join rules may be added to this list, but it's critical
that clients adopt a safety first approach here.

The user MAY still opt-in to media if the room is "public", and opt-out if the room is "private".

Note that this setting has no effect for `invite_avatars`. Avatars can only be `off` or `on` for all invites. 
Bad actors can easily send a DM to a user (which would pass the `private` check) containing unwanted
content.

#### `on`

Media SHOULD be shown in any room without a prompt.

Users SHOULD be able to individually hide media, and this preference MUST be respected over any defaults defined in `m.media_preview_config`.

This value is the **default** setting for both properties when no value is set, to keep with the previous defaults.

### Other values

Clients MUST treat any unknown property value in either defined property as `off`, for safety reasons.

### Levels

The account data may exist at both the global and room level. The global setting defines the preference for
all rooms, unless a per-room setting overrides it.

If `m.media_preview_config` is set at both global and room levels, the client MUST prefer using a defined value
over a default value. E.g. account data of:

```jsonc
{ // Room-level account data
  "media_previews": "on"
}
```

```jsonc
{ // Global account data
  "media_previews": "off",
  "invite_avatars": "off"
}
```

would resolve to:

```jsonc
{
  "media_previews": "on"
  "invite_avatars": "off"
}
```


### Notes

Homeservers MAY specify a default value ahead of time for the user, by setting a default
value internally for the account data. The user *must* be able to mutate this value, as it's
considered a safety feature.

Not all clients will respect this configuration initially, and many clients will continue to support
their own variant of this setting in the short term.

## Potential issues

### Holding more state

This requires clients to hold more state about the room than they would do previously to render a room. This may
present a challenge, particularly for mobile clients who may need this information to render push notifications.

### Spaces

A previous version of this MSC also explored the idea of the setting cascading through a space tree, but
it was difficult to design for both because it required clients to hold more state about the room (e.g. traversing
a large amount of state locally to determine the rules) as well as challenges in rendering the setting to users.

A future MSC may explore the possibility of this applying to spaces, but this initial version will operate only
globally and per-room.

However, not having this feature means many room may need apply their own rules.

#### User Avatars

This MSC explicitly rules out controlling room avatars in joined rooms. Conveying to users why avatars are not
rendering, and giving the ability to explicitly opt-in/opt-out of user avatars felt beyond the scope of this MSCs
room focus.

A future MSC may be considered to give greater protection for user avatars.

## Alternatives

This MSC has been iterated on a few times before being published, and several alternatives were considered.

### A well-known property for a global trust policy

This was [originally considered](https://github.com/matrix-org/matrix-spec-proposals/tree/hs/homeserver-content-trust-level)
to change the default policy on a server, so that users on that server would see previews based on their admin's preferences.

This was rejected as it was far too coarse. Expressing a different rule based on the room you are in
was not possible, and wouldn't allow homeservers to store different preferences. Also, confusingly
if the server was a closed registration personal server that happened to federate with the internet
then it would require you to mark your own server as untrusted, which felt wrong in practice.

### Use join rules to determine safety

This is actually part of the proposal under the "private" flag, but this alone wasn't satisfactory for all users. The join
rules have no direct bearing on the content in the room, and bad actors inviting many people to a private room
containing undesirable content would slip under this check.

### Use space membership

Like the above, we could determine that rooms within a trusted space are safe and rooms outside of it are
not. However, this also comes with drawbacks. It would raise the bar for all clients to expose spaces
as a feature in order to make their users safer, and in practice spaces are not fully supported either
by the ecosystem (e.g. Element X) or organisations yet.

### Room state safety flag

Rooms could expose their safeness via a state event, similar to how this proposal does for account data.
However, this would give administrators too much control over your own client experience. It would put the
responsibility on safety on room administrators, who may lack the knowledge or time for proper room configuration.

It also exposes another possible attack where users are invited to a room similar to a phishing attack, and the
room state would override their personal safety settings to deliver undesirable content.

### Trust users you share a DM with

We could seek to trust media if we share a room with a user (e.g. the `m.direct`), which might be a cheap way to
establish a basis of trust for users.

### Blurring previews

One suggestion would be to blur untrusted previews rather than keeping them as off. There are a few ways that this
could be achieved, but each have downsides.

1. Use [MSC2448](https://github.com/matrix-org/matrix-spec-proposals/pull/2448) client-side blurhashes. Would prevent
   downloading blocked media but the blurhash is attacker controlled, and can't be trusted for accuracy.
2. Above, but reciever-side calculation. Would require downloading potentially offensive media to the client and is
   a non-starter for potentially dangerous content.
3. Server-side generated previews. Does not work for encrypted rooms, and [were ripped out of MSC2448 anyway](https://github.com/matrix-org/matrix-spec-proposals/pull/2448#discussion_r1089753289)

For the moment, hiding media entirely is a simpler and safer solution.

## Security considerations

This property is ultimately held by the homeserver, and a malicious homeserver may expose you to unwanted content. This is
true today, and users should take caution with who they choose to host their account with.

As with all account data properties, the content MUST be validated.

## Unstable prefix

The property MUST use `io.element.msc4278.media_preview_config` while the property is unstable.

## Dependencies

None.
