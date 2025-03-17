# MSCXXXX: Homeserver Content Trust Level

Matrix homeservers have the flexibility to be configured in many different ways.Some are open, where they
allow free federation and/or open registration for users to participate. Others are closed, with tigher controls
over registration and which servers they federate with.

Clients are are largely unable to determine what they may be exposed to based on the server configuration, and
therefore either run the risk of potentially opening up their user to undesirable content or overly restricting
features which may be useful in a closed context.

This MSC aims to provide a starting point for clients to set "safe defaults" for their users to avoid exposing
users to "undesirable content".

For the purposes of this MSC, the term "undesirable content" refers to images that the user does not want to see,
be it illegal or abusive.


## Proposal

An additional object may be present in the .well-known configuration for the [client](/.well-known/matrix/client).

```json
{
    "m.homeserver" ...,
    "m.trust": {
      "content_trust_level": "trusted|untrusted"
    }
}
```

The new field, `content_trust_level` may be one of two values.

#### `trusted`

The content on this homeserver is trusted. Examples of "trusted" homeservers are ones where
registration and federation is controlled, or content is scanned before it is provided to the client.

Clients MAY assume that it is safe to enable media previews, url previews and render user avatars
in these cases.


### `untrusted`

The content on this homeserver is untrusted. The homeserver may have open registration or allows
open federation, or does not have tight controls over wht 

Clients SHOULD assume that it is not safe to show media previews, url previews or render user
avatars outside of ones explicitly permitted by the user.

### Notes

It's important to note is level is **advisory** only. Even on a trusted homeserver, there may be situations
where undesirable content is posted. Likewise on a untrusted homeserver, the content may be largely safe
but the risk of illegal content is greater.

The field here merely provides the client with a useful value for setting default content settings.

Clients MUST provide users with the ability to override any settings that may base their defaults on
this field. For instance if a client defaults image previews to enabled on a `trusted` homeserver, then
the user must be able to switch this setting off.


## Potential issues

### The field is extremely coarse 

This provides a blanket setting for all rooms and content recieved, rather than this applying to rooms
specifically (via a state key or otherwise). 


### Requires adjustments to well-known

This proposal requires administrators to adjust their well-known, which means that bad-actor homeservers
may potentially set the value of `content_trust_level` to `trusted` even if the content is not trusted.

This is mitigated by users being able to override settings, but does however mean that unsuspecting users
may be more exposed to content than they should be.


## Alternatives

### Use finer controls for determining trust

Rather than using a per-homeserver value, there are several existing metrics that could be used to determine
content trust.

  - Join rules: If a room has it's join rules set to `public` then it could be treated as `untrusted` v.s. other rooms.
  - Space membership: If a user/room is joined to a Space that you trust (e.g. see above), then it could be treated
    as `trusted`.

## Security considerations

None.

## Unstable prefix

The field should use `io.element.mscXXXX.trust` while the field is unstable.

## Dependencies

None.