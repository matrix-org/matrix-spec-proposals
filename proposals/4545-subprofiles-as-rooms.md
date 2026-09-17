# MSC4545: Subprofiles as Rooms

This proposal builds upon [MSC4144: Per Message Profiles](https://github.com/beeper/matrix-spec-proposals/blob/per-message-profile/proposals/4144-per-message-profile.md) and [MSC4201: Profiles as Rooms v2](https://github.com/FSG-Cat/matrix-spec-proposals/blob/FSG-Cat/Profiles-as-rooms/proposals/4201-profiles-as-rooms-v2.md) to allow for deeper integration of Per Message Profiles.

## Use Cases

### Bridges

In order to make a bridged account feel more integrated with Matrix, a bridge could copy over profile
data (e.g. the description of a Discord account.)

### Plural users

Being able to set a profile biography is standard in some plural accessibility tooling, for example
[Pluralkit](https://pluralkit.me) and [/plu/ral](https://plural.gg/). Providing parity here would
allow for such use cases, and would make these 'subprofiles' more customisable.

## Proposal

The solution is to have a new field within PMPs that link to a profile room.

```json
{
  "msgtype": "m.text",
  "body": "Hello, World!",
  "m.per_message_profile": {
    "id": "meow",
    "displayname": "cat",
    "avatar_url": "mxc://maunium.net/hgXsKqlmRfpKvCZdUoWDkFQo",
    "m.profile" : "!meow_profile:maunium.net"
  }
}
```

`m.profile` MUST link to a valid `m.profile`-type room if set.

In order to support looking up profiles that do not necessarily have a 1:1 relationship with a user, changes to
the Server-Server and Server-Client APIs must be added.

### Server-server

`GET /_matrix/federation/v1/query/profile`'s parameters are extended to include another field:

|Name| 	Type| 	Description|
|----|------|--------------|
| field | string | ... |
| user_id |	string | ... |
| subprofile_id | string | If specified, the server will query the matching subprofile instead of the main profile for the user. |

### Server-Client

Mirroring the `/profile` endpoints, new `/subprofile` endpoints are added: 
- `GET /_matrix/client/v3/subprofile/{userId}/{subprofileId}`
- `GET /_matrix/client/v3/subprofile/{userId}/{subprofileId}/{keyName}`
- `PUT /_matrix/client/v3/subprofile/{userId}/{subprofileId}/{keyName}`
- `DELETE /_matrix/client/v3/subprofile/{userId}/{subprofileId}/{keyName}`

### Profile extensions

A user may want to advertise their subprofiles (or a subset of them), so a new profile key is added: `subprofiles`.

```json
  [
    {
      "id": "cat",
      "displayname": "Cat 🐈️",
      "m.profile" : "!cat_profile:maunium.net"
    },
    {
      "id": "black_cat",
      "displayname": "🐈‍⬛",
      "avatar_url": "mxc://maunium.net/hgXsKqlmRfpKvCZdUoWDkFQo",      
      "m.profile" : "!black_cat_profile:maunium.net"
    }
  ]
```

A client may read this and display it with a profile to allow a user to view another user's subprofiles.

## Potential issues

### Privacy

Someone might desire to have a subprofile to be private-unless-discovered. We believe that `m.profile.privacy`
values of `public` or `restricted` should be enough for this use case. (Optionally restricting a subprofile
to being discovered if the profile's user shares a room with the requesting user.) Further feedback is required
on if further privacy options are needed (for example, encrypted subprofiles.)

### Trust and safety

This may add a further trust-and-safety 'cost', as the nature of subprofiles means that they might not be discovered
until a message is sent.

## Alternatives

Instead of Profiles-as-rooms, this proposal could instead have used
[MSC4440: Profile Biography via Global Profiles](https://github.com/RoootTheFox/matrix-spec-proposals/blob/main/proposals/4440-profile-biography.md)
as the technological basis for subprofiles. However, there's no way to specify any privacy for keys in
global profiles, as far as we can tell.

Alternatively, profile data could be added as an extension to `m.per_message_profile`, but this may
result in the size of messages with an attached profile getting impractically large.

Alternatively, subprofiles could be added as a new event.

### Using MSC4611

Profile data could also be stored in account data as an extension to [MSC4611: Storing per-message profiles for users](https://github.com/matrix-org/matrix-spec-proposals/blob/tulir/per-message-profile-storage/proposals/4461-per-message-profile-storage.md):

```json
{
  "type": "m.per_message_profiles",
  "content": {
    "default_profile_id": null,
    "profiles": [
      {
        "id": "cat",
        "displayname": "Cat 🐈️",
        "triggers": [
          {"prefix": "meow ", "suffix": " meow", "keep_trigger": true},
          {"prefix": "cat: "}
        ],
        "m.biography": {
          "m.text": [
            { "body": "hello world!\n\ninterests:\n-  programming\n-  matrix\n-  sleeping\n-  petting cats" }
          ]
        }
      }
    ]
  }
}
```

This could also be surfaced as `/subprofile` endpoints, using the `id` to query the correct profile. Profile data is 'unlisted'. (It can be reached only through its identifier, it must be known before viewing a profile.) This lacks the `restricted` privacy control.

## Security considerations

Due to the small scope of this change, there should be not be many security considerations that would not
be considered by this proposal's dependants.

## Unstable prefix

* `subprofiles` key → `net.f0rest.subprofiles`
* `m.profile` key in `m.per_message_profile` → `net.f0rest.subprofiles.profile`

## Dependencies

This proposal builds upon [MSC4144: Per Message Profiles](https://github.com/beeper/matrix-spec-proposals/blob/per-message-profile/proposals/4144-per-message-profile.md) and [MSC4201: Profiles as Rooms v2](https://github.com/FSG-Cat/matrix-spec-proposals/blob/FSG-Cat/Profiles-as-rooms/proposals/4201-profiles-as-rooms-v2.md) (which at the time of writing have not yet been accepted into the spec).
