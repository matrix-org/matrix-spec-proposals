# MSC4427: Custom banners for user profiles

On many platforms, users have additional customization options for 
their profile, including but not limited to banners.

Banners are displayed above, and often slightly behind a users' avatar,
most commonly featuring landscape content.

This MSC aims to standardize these banners across the matrix ecosystem.

## Proposal

Banners are something that is already widely represented on instant
messaging platforms, and even in some UI designs in the Matrix
ecosystem. Yet, there isn't a standardized field (outside of 
non-specced implementations in some clients) to read banners from.

We add a new field to represent banners:
```json
{
  "avatar_url": "mxc://matrix.org/SDGdghriugerRg",
  "displayname": "Alice Margatroid",
  "m.example_field": "custom_value",
  "m.tz": "Europe/London",
  "m.banner_url": "mxc://matrix.org/example123"
}
```

Clients can then use this field to load user banners.

It is recommended that clients stick to a horizontal aspect ratio, 
like 3:1 or 2.8:1.

## Potential issues

Some clients, like [extera](https://matrix.org/ecosystem/clients/extera-next/)
already had user banners in the past. This field may not be read by
those clients and users which wish to keep their banners once this is
implemented will have to reupload their banner.

## Security considerations

The same security precautions apply here as they do for avatars. Uploaded 
banners should always be some kind of image data (i.e image/* mime-type)
and never other arbitrary files.

## Unstable prefix

`chat.commet.profile_banner`

## Dependencies

None
