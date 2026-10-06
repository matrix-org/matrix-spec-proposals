# MSC4522: Username colors

For a long while users have wanted a way to declare what color their name/message should be displayed with, 
and with the advent of extensible events clients have started to create unique implementations for users
that are not cross compatible.

There needs to be a way to tell a client that your name/messages should have a specific color, ideally one 
that could be specific to a room


## Proposal

Color selection should have a unified cross platform solution in order to best represent every case.

For standardization:
 - per-account colors, profiles may have an optional `m.color_preference` field object relying on [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133).
 - per-room colors may be set through a `m.color_preference` field within the `m.room.member` state event

If a custom color is wished to be set for an ID of a Per-Message Profiles (PMP) it may be set through a `m.color_preference` field within the 
`m.per_message_profile` of the message

  The `m.color_preference` object contains 2 fields for the potential colors to be displayed but are named by the theme kind that the name/message is to be displayed over, 
the `on_dark` value represents the color that should be used when the client uses a dark theme (ie the color itself should be bright) and `on_light` on light themes (ie the color itself should be dark).

The field within the extended profile can be for example:
```json
{
  "avatar_url": "mxc://matrix.org/example",
  "displayname": "Shea Butter",
  "m.banner_url": "mxc://matrix.org/example_banner",
  "m.tz": "Europe/Troll",
  "m.color_preference": {
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
  "m.color_preference": {
    "on_dark": "#f00",
    "on_light": "#400" 
  }
}
```

The `m.color_preference` for PMPs may look for example:
```json
"m.per_message_profile": {
  "id": "nough",
  "displayname": "Nough",
  "avatar_url": "mxc://example.com/example_url",
  "has_fallback": true,
  "m.color_preference": {
    "on_dark": "#82F2A3",
    "on_light": "#11403A" 
  }
},
```

  The order of precedence for the color values must be: 
   - PMP color, 
   - per-room color, 
   - account profile color, 
   - [MSC3949](https://github.com/matrix-org/matrix-spec-proposals/pull/3949) colors if the client implements this MSC, 
   - default fallback that a client SHOULD have

  The color fields must be a hex color (#RGB or #RRGGBB) for consistency and ease of use for the end-user.

  A client may adjust the final displayed color to accommodate theming, technical and accessibility requirements.
However, The client should preserve the hue where possible, and may alter the Saturation/Chroma/Lightness.
  
  For example a terminal-based client might have a very limited color palette and might end up compressing 
all the color options set by the users to an 8-32 selection and that client could still be compliant with the 
msc as it would be within its limitations.

## Potential issues

  A user may choose to set the color that has poor visibility to the background but that may be mitigated by
either choosing the color for the opposite theme if it fits better or refusing both and going one step lower
whenever that is detected (ie so it would ignore the PMP color and use the per-room color)

  A user may choose to mimic the color of a moderator of a room for impersonation reasons, but this may be easily detected as a 
per room setting and is mitigated by [the name disambiguation algorithm](https://spec.matrix.org/latest/client-server-api/#calculating-the-display-name-for-a-user)

## Alternatives

  One alternative is setting only one hex value for the color but that was dismissed as it reduces the pool of
potential colors, a client might have to choose from when there is poor visibility resulting in a less
personalized experience. Or, makes them use colors that are less relevant to the user's taste in coloring

 For example this could result in completely ignoring the lightness for a dark color making it light, which would result in a fully different color

  (i.e. a user that has chosen navy blue because they are using a light theme might have no wish to have a baby blue color for dark theme usecases, a user that has chosen an orange color might not want a brown color when using a light theme, a user selecting a pastel pink name in a dark theme might not want a murky pink in a light theme).

  Another potential change would be the usage of a standard different from 24bit RGB, and while there are substantial benefits to many other standards 
in their respective usecases, 24bit RGB is the most interoperable color standard, being supported by ANSI for terminal clients, natively by browsers, and by
most platforms that support other color standards. So, by choosing a color standard other than RGBG (or CYMK but, no, CYMK is not an option for this), many 
clients would have to devise conversion algorithms for their platform or implement entire color libraries for a very limited scope.            
  Another alternative in this situation is to not set a color standard but that would result in applications needing to understand dozens of standards only for one
setting, which would increase the cost unreasonably, requiring either to be able to convert between every existant standard and the client's prefered one or to 
be able to process directly every color standard

  Lastly, the standard could allow a user to set an arbitrary amount of prefered colors in an array that a client might choose from in the form:
  ```json
  m.preferred_colors = ["#ffd9f5", "#440000", "#460333"]
  ```
  And while that method would be a very pleasant and elegant way to set colors, it would present an increased cost of implementation, allowing arbitrarily long lists of 
colors across 3 of the stages of the order of precedence.

## Security considerations

There are no new security issues introduced by this proposal

## Unstable prefix

`eu.she-a.color` should be used instead of `m.color_preference`      

## Dependencies

This MSC builds on:
 - [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133) for per-account colors,
 - [MSC4144](https://github.com/matrix-org/matrix-spec-proposals/pull/4144) for the per-message-profile object, 

And wishes that more clients would implement [MSC3949](https://github.com/matrix-org/matrix-spec-proposals/pull/3949) or some other standard powerlevel specific customization
