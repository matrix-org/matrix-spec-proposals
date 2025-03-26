# MSC4278: Media preview controls

Matrix caters to a wide variety of networks configurations. Some networks are closed and the users have a high
degree of safety, and other networks are open to the public internet and are inheriently less safe. This proposal
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
  "media_previews": "off|on|private",
  "invite_avatars": "off|on"
}
```

`media_previews` refers to media in the room timeline, that may be thumbnailed.

`invite_avatars` refers to any *room* avatar rendered in the client, where the client has a `membership` of `invite`.

The fields `media_previews` and `invite_avatars` may be one of three values.

#### `off`

The client MUST NOT show any previews for any media in affected rooms.

Users may individually consent to seeing media, for example by clicking on a prompt to show a preview.

If consent is given, the client SHOULD then track that consent and show the media again in the future.

#### `on`

Media MAY be shown in any room without a prompt. 

Users may individually hide media, and this preference MUST be respected over any defaults defined in `m.media_preview_config`.

#### `private`

Previws for media MAY be shown in "private" rooms without a prompt. A private room is any room where:
  - The `m.room.join_rules` state exists.
  - The `join_rule` key of this state is `invite`, `knock`, `restricted`, or `knock_restricted`.

If any other `join_rule` is set, or cannot be determined by the client then the assumption MUST be that the
room is public and previews should not be shown. Future join rules may be added to this list, but it's critical
that clients adopt a safety first approach here.

This value is the **default** setting when no account data exists on the user's account.

Note that this setting has no effect for `invite_avatars`. Avatars can only be `off` or `on` for all invites. 
Bad actors can easily send a DM to a user (which would pass the `private` check) containing unwanted
content.

### Levels

The account data may exist at both the global and room level. The global setting defines the preference for
all rooms, unless a per-room setting overrides it.

It is also possible for rules to cascade via spaces. A top level space may set a specific rule, and child
rooms may set their own rules. When this is the case, the strictest rule must always be applied.

For instance, given the following hierarchy of rooms within a space tree:

- Acme Corp <"on">
  - Engineering <"private">
    - Room A <"off">
    - Room B <no-value>
  - Support <no-value>
    - Room C <"off">
  - Room D <"off">
  - Room E <no-value>
- Room F

The result would be:
 - Room A, Room C and Room D would be "off".
 - Room B would be "private".
 - Room E would be "on".
 - Room F is out of the space, and would default to the user's global rule.

### Notes

It's important here that this account data MUST be configurable by a user.

Homeservers MAY specify a default value ahead of time for the user, by setting a default
value internally for the account data. The user *must* be able to mutate this value.

Not all clients will respect this configuration initially, and many clients will continue to support
their own variant of this setting in the short term.

## Potential issues

TODO: Write this up.

## Alternatives

This MSC has been iterated on a few times before being published, and several alternatives were considered.

### A well-known field for a global trust policy

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

## Security considerations

This field is ultimately held by the homeserver, and a malicious homeserver may expose you to unwanted content. This is
true today, and users should take caution with who they choose to host their account with.

As with all account data fields, the content should be validated.

## Unstable prefix

The field should use `io.element.msc4278.media_preview_config` while the field is unstable.

## Dependencies

None.
