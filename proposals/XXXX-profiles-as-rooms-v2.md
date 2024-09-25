# MSC0000: Profiles as Rooms v2

## Introduction

### Acknowledgements

This MSC exists to realise the vision that was set out in [MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769)
this vision has served to guide the ecosystem for a long time but its time to finally realise it.

This proposal aims to provide a pathway to take us from the limitations of today that shaped the competing proposal
[MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133) to the future where we have fed peeking
fully working in the hopeful event that said future happens.

A thanks has to be issued to everyone who gave feedback on [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133)
as this feedback has helped shape this competing proposal. Also thanks to Tom for the proposal it self as it has inspired parts of this
proposal.

Thanks to Gnuxie for being the source of the peeking bypass idea as far as Cat remembers.

### Proposal Introduction

Profiles as rooms is a long established dream in the matrix ecosystem that has been declared as the solution
to a whole bunch of our problems. This MSC aims to realise that dream via packaging up a idea that has been circulating
in the spec room. Just abuse /profile and the nature of profiles to bypass the Peeking problems.

This proposal uses profile rooms and state events to define profile information. Profile information
is defined via a `m.profile` state event in your profile room that uses state keys to differentiate values.

To get around the fact that we do not have federated peeking yet this proposal will use the /profile federation API
to simply ask the users homeserver about their profiles. This proposal supports per room profiles and viewing
restricted profiles.

Restricted viewing is done via a check of is the person asking in a room where you are pointing to that profile.
Public profiles without viewing restrictions are also considered valid as you want to be able to present
a profile before you share a room if your privacy settings allow for this.

## Proposal

This proposal is split into 2 primary categories. Profile room and the APIs.

Profile Room section deals with the state events that control your profile room and the API section
deals with defining the APIs involved in this process.

### Profile Rooms

Profile rooms are special rooms with the dedicated purpose of storing profiles. These rooms will be created
with the `type` being `m.profile` in line with [MSC1772](https://github.com/matrix-org/matrix-doc/pull/1772)
established precedent on that specialised rooms like these are what room types are for.

They are plain old normal matrix rooms except for that they store profile information as their defined
purpose and server implementations or future MSCs are free to provide powerlevel templates that reflect this purpose.

These rooms contain `m.profile` state events to store profile data as the state key determines the profile key this data is for.
The `m.profile.privacy` event controls the privacy rules for the profile in question. This state event
with a blank state key and contains a `visibility` flag as its initial contents but future proposals are welcome to elaborate.
This `visibility` flag accepts the values of `public` and `restricted`.

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

`visibility` of `public` means that anyone is allowed to look up this profile. This value is primarily intended for your global profile
for when you do not yet share a room with the subject. Like when they are doing a lookup in the user directory when starting a DM.

`visibility` of `restricted` restricts who can look up a profile to users who are in a room that has a pointer to this profile.
For a pointer to be valid said pointer must be issued by the creator of the profile if the profile is restricted. This means that
invites can only set `public` profiles without causing the server to 404 the request.

To use a given profile you set a `profile` value in your `m.room.member` event for a given room. The value of `profile` is the room ID
of the profile you want to use in that room.

`m.profile` events are limited only to all the normal event size rules but clients are allowed to enforce whatever limits they find resonable
on data that they will render when given this data.

### Client-Server API Changes

The contents of a profile are accessed via the following endpoints

<details>
  <summary>Get Profile Endpoint</summary>
  
- **Endpoint**: `GET /_matrix/client/v1/profile/{roomID}`
  - **Description**: Get a profile. If the request body contains a list of keys only those events will be returned.
  Omit request body to fetch all profile information.
  - **Query Param**: Use `auth_event` query parameter to point to what event grants you access to the profile.
  - **Errors**: If the requesting user does not have access to the provided `auth_event` 403 the request.
  If a specific state key has empty contents omit returning said profile field.
  - **Response**:

```json
{
  "key_name": "field_value"
}
```

</details>

### Server-Server API Changes

The federation endpoint `GET /_matrix/federation/v1/profile/{roomID}` will mirror the client-server
API endpoint in behaviour except that it also adds a query parameter of `requesting_user` where the mxid
of the requesting user is defined. This is so that the server can verify if the requesting user has
access to a event points to the given profile if its a `restricted` profile.

As this proposal is avoiding the use of peeking the validity of a profile can not be verified over
federation and therefore we have to just trust the server of the user. Therefore this API can only be called
against the server that the profile was created on for now.

A federated peeking MSC is free to propose an API that can be used to access this data with less restrictions.

A profile with `m.federate` set to `false` in its creation event is not allowed to be requested over federation.

The rules configured in the `m.room.server_acl` event are to be respected for all profile requests. This means that
if a server is ACL banned from a profile room said server is not allowed to request the contents of this profile.
This function exists so that users are able to block servers that they want to not have profile access from having profile access.

### Limitations

The completely freeform nature of this proposal raises Trust and Safety Concerns. To mitigate at least
one of these concerns servers are completely welcome to run allow and deny lists on state keys for profiles.

Servers that wish to guarantee that no disallowed data exists in the room state of a profile are allowed to
under this proposal enforce strict access controls on what events can be sent into the profile room.
This is to ensure that the server can not loose control over the state by allowing remote users in for example.

Profiles have no size caps set in stone in this proposal as of version 1 of the proposal. This is seen as
acceptable because rooms are currently also unbound and servers are happy with requests like /state on the
matrix.org coc policy list. The policy list in question is of a decent size.

### Trust and Safety

To address the T&S question on a room level clients are supposed to display no profile what so ever for a user
if their membership event is redacted as this is the current status quo and this MSC does not wish to disrupt this.

Homeserver administrators are liberally able to go in and modify users profiles to comply with server policy.

Its preferred if homeserver admins redact the state events in question that they find disagrees with homeserver policy.

The omit empty fields policy for the endpoint is to mitigate this specific T&S concern and privacy concern. Empty
state events should be hidden as they are empty for a reason.

### Field Name Rules

Homeservers should be very careful about how they enforce profile field rules as to balance their T&S concerns and
the ability for users to access the full power of this proposal and future extensions.

Spec defined profile fields come with state keys that carry the reserved `m.` prefix.

User defined profile fields come with the `u.` prefix copied from tags.

Lastly Clients and Servers and MSCs are ofc allowed to use custom prefixes that follow the Java naming
conventions that we follow in matrix. An example could be `support.feline.cat`.

Spec defined fields and fields that follow the java naming conventions can have specified validation
rules that go beyond the general rules that this MSC imposes. For example if [MSC4175](https://github.com/matrix-org/matrix-spec-proposals/pull/4175)
is used with this proposal that MSC could define that the `m.tz / us.cloke.msc4175.tz` field it defines
has a maximum size of 50 characters.

## Potential issues

This MSC has the problem of that its adding freeform fields and attempting to guarantee wide ecosystem
support for all of them is well hard. But this challenge i think is warranted as this MSC represents
a faithful hopefully version of the vision that the community had for [MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769).

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

The Problems related to that this MSC allows you to essentially ask to be vomited data at are hopefully explained
away to an acceptable degree.

No further Security considerations not covered elsewhere in this MSC or in this Section are known to the author at this time.

## Unstable prefix

While this proposal is unstable the following substitutions are to be made.

`m.profile.privacy` becomes `support.feline.mscXXXX.profile.privacy.v1`
`m.profile` state event becomes `support.feline.mscXXXX.profile.v1`
`m.profile` room type becomes `support.feline.mscXXXX.profile`

## Dependencies

This MSC does not have any unstable dependencies known to the author but does build on the
work in [MSC1769](https://github.com/matrix-org/matrix-spec-proposals/pull/1769)
