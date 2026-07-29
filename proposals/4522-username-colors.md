# MSC4522: Username colors

For a long while users have wanted a way to declare what color their name should be displayed with, 
and with the advent of extensible events clients have started to create unique implementations for users
that are not cross compatible.

There needs to be a way to tell a client that your name should have a specific color, ideally one 
that could be specific to a room, a powerlevel, or PMP


## Proposal

Color selection should have a unified cross platform solution in order to best represent every case.

For standardization:
 - per-account colors, profiles may have an optional `m.color` field object relying on [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133).
 - per-room colors may be set through a `m.color` field within the `m.room.member` state event
 - per-powerlevel colors may be set through a `color` field within a new `m.powerlevels_style` room state object

If a custom color is wished to be set for an ID of a PMP it may be set through a `m.color` field within the 
`m.per_message_profile` of the message

  The `m.color` and `color` fields represent the theme that the color is to be displayed over, 
the `on_dark` value represents the color that should be used when the client uses a dark theme and `on_light` on light themes.

The field within the extended profile can be for example:
```json
{
  "avatar_url": "mxc://matrix.org/example",
  "displayname": "Shea Butter",
  "m.banner_url": "mxc://matrix.org/example_banner",
  "m.tz": "Europe/Troll",
  "m.color": {
    "on_dark": "#ffd9f5",
    "on_light": "#440000" 
  }
}
```

The room state `m.room.member` may be updated to for example:
```json
{
  "membership": "join",
  "displayname": "User",
  "avatar_url": "mxc://example.com/code",
  "m.color": {
    "on_dark": "#f00",
    "on_light": "#400" 
  }
}
```

The room state `m.powerlevels_style` represents a potential override, and an array of objects with powerlevels with and a colors array as for example:
```json
{
    "override_other_colors": false,
    "powerlevels": [
      {
        "powerlevel": 51,
        "color": {
          "light_color": "#f00",
          "dark_color": "#400" 
        }
      },
      {
        "powerlevel": 1,
        "color": {
          "on_dark": "#f8f",
          "on_light": "#404" 
        }
      }
    ]
  },
```

The `m.color` for PMPs may look for example:
```json
"m.per_message_profile": {
  "id": "nough",
  "displayname": "Nough",
  "avatar_url": "mxc://example.com/example_url",
  "has_fallback": true,
  "m.color": {
    "on_dark": "#82F2A3",
    "on_light": "#11403A" 
  }
},
```

  The `override_other_colors` key may be set in order to define whether or not the powerlevels of a room should take precedence 
to the other colors in order to reduce ambiguity between the moderators of a community and its participants,
but if it is missing clients should consider that as being set to false.

  The color fields must be a hex color for consistency.

  The order of the color values should be: PMP color, per-room color, account profile color, 
powerlevel color, default fallback that a client SHOULD have. This order may be overridden 
for powerlevels to take precedence above every other color.

## Potential issues

A user may choose to set their per-room or per account color to match one of a modertator of a room, but this
may be mitigated by setting `override_other_colors` to true if needed.

A user may choose to set the color that has poor visibility to the background but that may be mitigated by
either choosing the color for the opposite theme if it fits better or refusing both and going one step lower
whenever that is detected (ie so it would ignore the PMP color and use the per-room color)

## Alternatives

One alternative is setting only one hex value for the color but that was dismissed as it reduces the pool of
potential colors that a client might have to choose from when there is poor visiblity resulting in a less
personalized experience.

## Security considerations

**All proposals must now have this section, even if it is to say there are no security issues.**

There are no new security issues introduced by this proposal

## Unstable prefix

`eu.she-a.color` should be used instead of `m.color`       

`eu.she-a.powerlevels_style` should be used instead of `m.powerlevels_style`


## Dependencies

This MSC builds on [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133) for per-account colors and [MSC4144](https://github.com/matrix-org/matrix-spec-proposals/pull/4144) for the per-message-profile object
