# MSC4226: Reports as rooms

Currently it is possible to report users, rooms, and events to the Matrix
homeserver. However there are missing parts of the specification:

1. Receiving reports in a Matrix client is entirely unspecified.
2. There is no way to report any content to room moderators.

## Proposal

Compared to the alternative proposals, this MSC requires significantly
less supporting infrastructure, and is both very simple and
extensible.

We propose a new room type `m.report` which will be used to present
reports to Matrix server admins or room moderators.  This method of
reporting is expected to replace the legacy methods of reporting, via
the `/report` endpoints in the client-server API.

Although each of these flows are written from the perspective of a
client, it is an implementation detail whether Alice's client, Alice's
server, or Mike's server creates the room. This is in order to support
compatibility with the existing reporting endpoints or those found in
similar proposals.

### Report to room moderator flow

Alice is participating in a Matrix room dedicated to sharing Cat
pictures that is moderated by Mike and Laura.

Bob is also in the room, and keeps uploading memes from ifunny.co
while Mike and Laura are busy.  Alice decides to report Bob.

1. Alice selects Bob's most recent message in her client
2. Alice selects report.
3. Alice is presented with a view showing the event that is being
   reported. Mike and Laura's profiles are also shown in the view and
   it is clear to Alice they will be the moderators of the report.
4. Alice explains the situation in the `reason` field and submits the
   report.
5. Alice's client creates a new Matrix room with the type
   `m.room.report`.  Alice's client invites both Mike and Laura as
   part of the `createRoom` process.
6. Alice can find the report in her client under a reports tab, and
   can see that neither Mike or Laura have responded yet.

### Report moderator flow

Mike receives a notification within his client that a new report has
been received with minimal detail.

1. Mike opens a report view where he can see an overview of the new
   report. Mike reads the MXID of the report submitter,
   `@alice:amazing-linux.example.com`, and the entity that is the the
   subject of the report. In this instance the entity is the mxid
   `@bob:example.com`. Mike also notes that the report has been
   submitted within the context of the room
   `#cats:meow.example.com`. No further details are visible from the
   overview.

2. Mike opens the report, and then reveals the report reason, which is
   hidden behind spoiler text.

3. Mike opens `#cats:meow.example.com` and while his client is
   blurring the images, he can still read from the room that Bob has
   been uploading memes from ifunny.co.

4. Mike writes a warning to Bob and temporarily mutes him.

5. Mike returns to Alice's report and asks Alice if she has seen Bob
   behave this way in any other rooms.

6. Mike allows Alice to speak in the report room, and his client sets
   Alice's power level to `0`.

7. Alice gets a notification that her report has been responded to.
   Alice replies and says she hasn't.

8. The report is marked as resolved by Mike.

### Report to server administrator flow

Alice `@alice:amazing-linux.example.com` is providing technical
support as a volunteer for a popular linux distro in one of their
support rooms.

Alice notices a spam bot join the room with the mxid `@spam:matrix.org`.
Alice removes the spam sent by the bot, and bans the user from the room.

Alice decides to follow up by reporting the bot to `matrix.org` for
deactivation.

1. Alice selects `@spam:matrix.org` in the user pane from her client while
   focussed on the support room.
2. Alice selects report and her client displays the profiles of the report
   moderators for `matrix.org`.
3. Alice adds an explanation and submits the report.
4. Alice's client creates a new Matrix room with the type `m.report`.
   Alice's client invites the `matrix.org` report moderators as part of the
   process.
5. Alice can find the report in her client under a reports tab,
   and can see that the `matrix.org` report moderators have
   not responded.

### Escalation flow

Consider the flow from report to room moderator.

Alice has reported Bob, and Mike, a room moderator, is reviewing the report.

Bob is still misbehaving and has now started harassing the room moderators.

Mike decides to escalate the report to bob's server admins.

1. Mike selects `escalate` option in his client, opening a view with the
   profiles of the report moderators of Bob's server.
2. Mike's client invites the report moderators of Bob's server to the room.

### Report content mixin

When the `m.room.create` content has the `type` `m.report`, a mixin
should be embedded under the property `m.report.*`.

The `m.report.*` property has 4 specified variants:

- `m.report.room`, `m.report.user`, `m.report.server`, and
  `m.report.event`.

In the section below, `m.report.*` denotes properties that are common
to all of the variants.

#### `m.report.*`, `m.report.room`

- `entity`: The entity being reported, possibly a room, user, event, or server similar
  to the events specified by `m.policy.rule.*`.
- `reason`: A reason for the report.

#### `m.report.user`, `m.report.server`

This extends the properties described for `m.report.*`.

- `room_id` (Optional): If the entity was reported from the timeline view of a specific room.
  For instance, if a user was reported by clicking on their profile pane in a matrix
  room, then the room_id will be included.

#### `m.report.event`

This extends the properties described for `m.report.*`.

- `room_id` (Required): The room that the event can be found within.
- `sender` (Required): The mxid of the event sender.

### Power level event

In order to give the moderators and server admins control over the
report room, and protect the moderators and server admins from further
abuse, there are specific requirements on the power level event that
need to be fulfilled when creating the room. These may be checked by
clients or servers check before they show the report to report
moderators, in order to maintain safety (See [Consistency
checks](#consistency-checks)).

1. The reporter needs to immediately remove their ambient authority in
   the first `m.room.power_levels` event sent to the room by setting
   their power level to `-1`.

2. Any report moderators that have been invited to the room need to be
   given the "admin" role or a power level of `100`.

### Consistency checks

There are a number of consistency checks that the homeserver and the
client should perform upon receipt of a report before making the report
visible in any part of the client UX or notifications.

Reports that do not pass these checks should be marked as suspicious
or otherwise hidden completely. In any case they should not
be displayed alongside reports that have passed the consistency checks.

#### Power levels

1. Check whether the reporter has the power level to send any event.
   If so, reject the invitation or part the report room.

#### `m.report.event` `sender` property.

Check that the `sender` provided matches with the event sender.
If this is not possible, then a warning should be displayed
alongside the report.

#### report moderators

1. Check whether we are designated as a report moderator
   in the room relevant to the report, if so allow.
2. Check whether we are designated as a report moderator
   in the `.well-known/matrix/support` for our homeserver,
   if so allow.
3. reject.

### Sourcing report moderators for client authored reports

As reports can be created by using the `/createRoom` endpoint, there
is no longer a need for new endpoints to facilitate reports over
federation, report-to-moderator, and report reviewing.

#### The `m.report_moderators` state event, `state_key: ""`

In order to customize report-to-moderator functionality, rooms can
specify the users that are eligible to receive reports, so that they
can be invited to the report room when a report is created.

`reporters:` An array of mxids.

If this array is not provided, fallback to using all the members with
power level at `ban` or above.

#### Extending `/.well-known/matrix/support` (already accepted into spec via MSC1929)

For reporting to server administrators, we propose a new support role,
`m.role.report_moderator`.

When a report needs to be sent to server administrators, each of the
the `m.role.report_moderator`'s will be invited to the report room.

## Potential issues

### Legacy clients

Legacy clients which are unaware of the `m.report` room type will
display reports as standard room invitations.  If the reporting UX is
out of scope for the client to implement, they can simply ignore or
hide any invitations to rooms with the type `m.report`.

## Security considerations

### Displaying reports

Unless opened, all UI element and notifications should display no more
than the fields embedded in the `m.report.*` mixin and the bare mxid
of the reporter. Displaynames and avatars must be hidden until the
report is opened. Clients SHOULD also take pre-cautions to spoiler
any report content, and blur any images in the report room
(which may have been added by moderators for context).

### Spam reports

It is already possible to send spam invitations to room moderators and
server admins. Mechanisms for better handling of invitations generally
need to be expanded upon urgently in Matrix.  The only novel
mitigation presented in this MSC is that the reporter profile is
hidden from any listing of reports and any notification.

## Alternatives

### [MSC4121](https://github.com/matrix-org/matrix-spec-proposals/pull/4121):  The `m.role.moderator` `/.well-known/matrix/support` role

This role could be reused instead of the proposed `m.role.report_moderator`.

### [MSC3834](https://github.com/matrix-org/matrix-spec-proposals/pull/3843): Reporting content over federation

This MSC proposes a federation endpoint for receiving reports.

### [MSC3215](https://github.com/matrix-org/matrix-spec-proposals/pull/3215): Aristotle - Moderation in all things

This MSC proposes report rooms for report-to-moderator
functionality. Rooms name a routing bot in a state event that is used
to forward reports to a report room.

### [MSC2938](https://github.com/matrix-org/matrix-spec-proposals/pull/2938): Report content to moderators

This MSC proposes a way to report content to room moderators by adding
a new endpoint to the client server API and receiving reports in the
client via EDUs.

This MSC has an extensive alternatives section that you should read.
Both MSC2938 and MSC3215 authored by @Yoric provide the inspiration
and prior art for the proposed MSC.

## Unstable prefix

`m.report` -> `org.matrix.msc4226.report`


## Dependencies

None.
