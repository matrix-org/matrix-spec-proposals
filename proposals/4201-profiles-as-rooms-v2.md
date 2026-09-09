# MSC4201: Profiles as Rooms v2

- [MSC4201: Profiles as Rooms v2](#msc4201-profiles-as-rooms-v2)
  - [Introduction](#introduction)
  - [Proposal](#proposal)
    - [Profile Rooms](#profile-rooms)
    - [Using and Accessing Profiles](#using-and-accessing-profiles)
    - [Limitations](#limitations)
    - [Trust and Safety](#trust-and-safety)
    - [Field Name Rules](#field-name-rules)
  - [Potential issues](#potential-issues)
  - [Alternatives](#alternatives)
  - [Security considerations](#security-considerations)
  - [Unstable prefix](#unstable-prefix)
  - [Dependencies](#dependencies)
  - [Acknowledgements](#acknowledgements)

## Introduction

Profiles as rooms is a long established dream in the matrix ecosystem that has been declared as the solution
to a whole bunch of our problems. This MSC aims to realise that dream via packaging up a idea that has been circulating
in the spec room. Just abuse /profile and the nature of profiles to bypass the Peeking problems.

This proposal uses profile rooms and state events to define profile information. Profile information
is defined via a `m.profile` state event in your profile room that uses state keys to differentiate values.

To get around the fact that we do not have federated peeking yet this proposal will use the /profile federation API
to simply ask the users homeserver about their profiles. This proposal supports per room profiles and viewing
restricted profiles.

Public profiles without viewing restrictions are also considered valid as you want to be able to present
a profile before you share a room if your privacy settings allow for this.

## Proposal

### Profile Rooms

Profile rooms are special rooms with the dedicated purpose of storing profiles. These rooms will be created
with the `type` being `m.profile` in line with [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772)
established precedent on that specialised rooms like these are what room types are for.

They are plain old normal matrix rooms except for that they store profile information as their defined
purpose and server implementations or future MSCs are free to provide powerlevel templates that reflect this purpose.

These rooms contain `m.profile` state events to store profile data as the state key determines
the profile field this data is for.

The `m.profile.privacy` event controls the privacy rules for the profile in question. This state event
with a blank state key contains a `visibility` value as its initial contents but future proposals
are welcome to elaborate.

This `visibility` value accepts the values of `public` and `restricted`.

Example of the `m.profile.privacy` event.

```json
{
  "content": {
    "visibility": "restricted"
  },
  "sender": "@alice:example.com",
  "state_key": "",
  "type": "m.profile.privacy",
  "event_id": "exampleid",
  "room_id": "!alice_profile:example.com"
}
```

`visibility` of `public` means that anyone is allowed to look up this profile. This value is primarily intended for
your global profile for when you do not yet share a room with the subject. Like when they are doing a lookup in
the user directory when starting a DM.

`visibility` of `restricted` restricts who can look up a profile to users who are
in a room that has a `m.profile` value set to this profile.
For this value to be legal it must be sent by the creator of the profile.
This means that invites can only set `public` profiles without causing the server to 404 the request.

`m.profile` events abide by normal event size rules but clients are allowed to enforce whatever
limits they find reasonable on data that they will render.

### Using and Accessing Profiles

To use a profile you set `m.profile` to the room ID of a profile room in your `m.room.member` event in that room.

<details>
  <summary>Example membership event with profile set.</summary>

```json
{
  "content": {
    "avatar_url": "Avatar URL",
    "displayname": "Cat",
    "membership": "join",
    "m.profile" : "!cats_public_profile:feline.support"
  },
  "origin_server_ts": 2147483648000,
  "sender": "@cat:cat:feline.support",
  "state_key": "@cat:cat:feline.support",
  "type": "m.room.member",
  "event_id": "example_event_id",
  "room_id": "example_room_id"
}
```

</details>

To access a profile you issue a request to `GET /_matrix/client/v1/profile/{roomID}` and provide the following parameters.

Query Parameter of `auth_event` pointing to a `m.room.member` that has a `m.profile` field that matches the profile
being requested. If the profile is public like in a use case where your presenting profile information before
a room is shared `auth_event` must to be omitted.

The user making the request must have history visibility for the `auth_event`

A subset of the profile fields can be requested using the `filter` query parameter type being `string`.

The response to a `GET /_matrix/client/v1/profile/{roomID}` is a set of Stripped state events responsive to the query.

To Access a profile over federation you use `GET /_matrix/federation/v1/profile/{roomID}`.

The result of a profile inquiry may be cached for a reasonable period of time not exceeding 24 hours.

The federation version of this endpoint mirrors its behaviour mostly with the client server API version of this endpoint.
The federation version of the endpoint adds the `requesting_user` query parameter. This parameter is required when
the `auth_event` parameter is present. Its used to indicate on whose behalf the request is made as this changes if
a profile lookup fails or succeeds, due to that the `requesting_user` must have history visibility for `auth_event`.

The history visibility check is done from the perspective of the resident server for the profile owner.

Profile rooms that have `m.federate` = `false` are not allowed to be requested over federation and `m.room.server_acl`
is to be honoured for all profile requests based on profile room.

Any profile field that is empty is omitted from profile lookups.

### Limitations

The completely freeform nature of this proposal raises Trust and Safety Concerns. To mitigate at least
one of these concerns servers are completely welcome to run allow and deny lists on state keys for profiles.

Profiles have no size caps set in stone in this proposal as of version 1 of the proposal. This is seen as
acceptable because rooms are currently also unbound and servers are happy with requests like /state on the
matrix.org coc policy list. The policy list in question is of a decent size.

### Trust and Safety

To continue to allow for moderation of profiles that are not aligned with policy in a given room, this MSC
keeps the behaviour of that redacting someone's membership event stops profile information from rendering.

Homeserver administrators are welcome to redact or modify user profiles to comply with server policy, in accordance
with server policies.

Its preferred if homeserver moderators / administrators redact state events that are not aligned with server policy.

The omit empty fields policy for the endpoint is to mitigate this specific T&S concern and privacy concern.

### Field Name Rules

Homeservers should be very careful about how they enforce profile field rules as to balance their T&S concerns and
the ability for users to access the full power of this proposal and future extensions.

Spec defined profile fields come with state keys that carry the reserved `m.` prefix.

User defined profile fields come with the `u.` prefix copied from tags.

Lastly Clients and Servers and MSCs are ofc allowed to use custom prefixes that follow the Java naming
conventions that we follow in matrix. An example could be `support.feline.cat`.

Spec defined fields and fields that follow the java naming conventions can have specified validation
rules that go beyond the general rules that this MSC imposes. For example if
[MSC4175](https://github.com/matrix-org/matrix-spec-proposals/pull/4175) is used with this proposal that MSC
could define that the `m.tz / us.cloke.msc4175.tz` field it defines has a maximum size of 50 characters.

## Potential issues

This MSC has the problem of that its adding freeform fields and attempting to guarantee wide ecosystem
support for all of them is well hard. But this challenge I think is warranted as this MSC represents
a faithful hopefully version of the vision that
the community had for [MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769).

This MSC is intentionally more complex to allow for a single proposal to do everything that was
dreamed about for [MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769) over the years.

This MSC on its own is very weakly useful as it needs proposals that build upon it to achieve full potential.

This MSC is intentionally leaving all the possible fields out of scope as that's not important. The
desire is proven for years in the ecosystem so this proposals job is not to prove that the people want this,
just to provide it.

This MSC also has no way to broadcast changes to users but that could easily be added in a future proposal.

Mechanisms to indicate this change include EDUs or timeline events but state events are considered too heavy
for this purpose at this time.

## Alternatives

The primary alternative to this MSC is [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133).

This MSC sees it self as the better alternative if perfected because it brings Per room and private profiles
and a path to the original vision of Profiles as Rooms that use Federated peeking. This proposal brings
Trust and Safety as a Nr 1 priority but ofc this is a very hard thing to deal with as we are essentially
bringing something akin to a steam profile with this MSC. That's very intentional as Steam profiles are a
inspiration for this MSC UX wise.

## Security considerations

This MSC has covered its various security related aspects throughout the whole MSC but lets boil it down to one
place.

Privacy of profiles is only loosely enforceable over federation. But so is all of matrix. We simply can not guarantee
that someone is who they claim to be outside of E2EE. This also applies with our profile lookups. But
we do mitigate the abuse aspect by requiring that you not only know the event ID of a event that points
to a profile but have all the validation be done by the server who controls said user.

Public profiles are a risk that users need to be informed of but its seen as an acceptable risk as its simply
paramount to offer this option. Users are not expected to be happy when told you can not see any profile what so
ever for someone you don't share a room with when trying to invite them. Especially local users on private servers.

A public profile is not mandatory under this proposal very much on purpose. This is one of the details of this
MSC informed by Steam. They also have rich profile visibility settings and they are very popular, while we are
not copying all of their settings in this proposal with the right use of this proposal you can achieve mostly similar
results.

There is the concern that users can ACL ban the mods from their profile and this concern is lessened if moderators are
informed of this situation and simply disallow such profiles in their rooms.

The Problems related to that this MSC allows you to essentially ask to be vomited data at are hopefully explained
away to an acceptable degree.

No further Security considerations not covered elsewhere in this MSC
or in this Section are known to the author at this time.

## Unstable prefix

While this proposal is unstable the following substitutions are to be made.

`m.profile.privacy` becomes `support.feline.msc4201.profile.privacy.v1`
`m.profile` state event becomes `support.feline.msc4201.profile.v1`
`m.profile` room type becomes `support.feline.msc4201.profile`
`m.profile` value in `m.room.member` becomes `support.feline.msc4201.profile.v1`

`GET /_matrix/client/v1/profile/{roomID}` becomes `GET /_matrix/client/unstable/support.feline.msc4201.v1/profile/{roomID}`
`GET /_matrix/federation/v1/profile/{roomID}` becomes `GET /_matrix/federation/unstable/support.feline.msc4201.v1/profile/{roomID}`

## Dependencies

This MSC does not have any unstable dependencies known to the author but does build on the
work in [MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769)

## Acknowledgements

This MSC exists to realise the vision that was set out in
[MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769)
this vision has served to guide the ecosystem for a long time but its time to finally realise it.

This proposal aims to provide a pathway to take us from the limitations of today that shaped the competing proposal
[MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133) to the future where we have fed peeking
fully working in the hopeful event that said future happens.

A thanks has to be issued to everyone who gave feedback on
[MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133)
as this feedback has helped shape this competing proposal.
Also thanks to Tom for the proposal it self as it has inspired parts of this proposal.

Thanks to Gnuxie for being the source of the peeking bypass idea as far as Cat remembers.
