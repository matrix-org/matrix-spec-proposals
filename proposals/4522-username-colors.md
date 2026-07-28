# MSC4522: Username colors

For a long while users have wanted a way to declare what color their name should be displayed with, 
and with the advent of extensible events clients have started to create unique implementations for users
that are not cross compatible.

There needs to be a way to tell a client that your name should have a specific color, ideally one 
that could be specific to a room, a powerlevel, or PMP


## Proposal

Color selection should have a unified cross platform solution in order to best represent every case.

For standardization:
 - per-account colors, profiles may have an optional `m.colors` field object relying on [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133).
 - per-room colors may be set through a `m.colors` field within the `m.room.member` state event
 - per-powerlevel colors may be set through a `colors` field within a new `m.powerlevels_style` room state object

If a custom color is wished to be set for an ID of a PMP it may be set through a `m.colors` field within the 
`m.per_message_profile` of the message

  The `m.colors` and `color` fields represent arrays of objects for the color. Each object of the array
should contain the color that is to be displayed and may contain a `background` that it is meant to 
represent the ideal background the `color` should be displayed over. The background SHOULD NOT be 
displayed but should only serve as a way for the client to determine which color best fits the background 
it is displayed against. 
  The `m.colors` array and color arrays MUST have at most one object that has no background color that SHOULD
serve as a fallback.

The field within the extended profile can be for example:
```json
{
  "avatar_url": "mxc://matrix.org/example",
  "displayname": "Shea Butter",
  "m.banner_url": "mxc://matrix.org/example_banner",
  "m.tz": "Europe/Troll",
  "m.colors": [
    { "color": "#ffd9f5", "background": "#000000" },
    { "color": "#440000", "background": "#fff" },
    { "color": "#f0f", "background": "#888" },
    { "color": "#ff0000" }
  ]
}
```

The room state `m.room.member` may be updated to for example:
```json
{
  "membership": "join",
  "displayname": "User",
  "avatar_url": "mxc://example.com/code",
  "m.colors": [
    {"color": "#ff0", "background": "000"}
  ]
}
```

The room state `m.powerlevels_style` represents a potential override, and an array of objects with powerlevels with and a colors array as for example:
```json
{
    "override_other_colors": false,
    "powerlevels": [
      {
        "powerlevel": 51,
        "colors": [
          { "color": "#00f", "background": "#818181" },
          { "color": "#88f", "background": "#808080" }
        ]
      },
      {
        "powerlevel": 1,
        "colors": [
          { "color": "#000", "background": "#ffffff" },
          { "color": "#fff", "background": "#000000" }
        ]
      }
    ]
  },
```

The `m.colors` for PMPs may look for example:
```json
"m.per_message_profile": {
  "id": "nough",
  "displayname": "Nough",
  "avatar_url": "mxc://example.com/example_url",
  "has_fallback": true,
  "m.colors": [
    { "color": "#f0f", "background": "#818181" },
    { "color": "#88f", "background": "#808080" }
  ]
},
```

  The `override_other_colors` key may be set in order to define whether or not the powerlevels of a room should take precedence 
to the other colors in order to reduce ambiguity between the moderators of a community and its participants,
but if it is missing clients should consider that as being set to false.

  Every `color` and `background` field must be a hex color for consistency.

  The order of the color values should be: PMP color, per-room color, 
account profile color, powerlevel color, default fallback that a client SHOULD have. This order may be
overridden for powerlevels to take precedence above every other color however.

## Potential issues

A user may choose to set their per-room or per account color to match one of a modertator of a room, but this
may be mitigated by setting `override_other_colors` to true if needed.

A user may choose to set the color and background within one item to the same value but this may be mitigated
by clients by removing these values from the pool of potential colors to choose from.

## Alternatives

One alternative is setting only one hex value for the color but that was dismissed as that would force clients
to either fully dismiss the color option of an individual when using a color that clashes with the background it
is set over or display a color that has poor visibility, and does not offer an alternative color that the user 
might prefer instead.

## Security considerations

**All proposals must now have this section, even if it is to say there are no security issues.**

There are no new security issues introduced by this proposal

## Unstable prefix

`eu.she-a.colors` should be used instead of `m.colors`       

`eu.she-a.powerlevels_style` should be used instead of `m.powerlevels_style`


## Dependencies

This MSC builds on [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133) for per-account colors and [MSC4144](https://github.com/matrix-org/matrix-spec-proposals/pull/4144) for the per-message-profile object
