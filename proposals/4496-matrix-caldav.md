# MSC 4496: Calendar Events, Invites, and Availability in Matrix

_This proposal introduces a general-purpose calendaring system for Matrix, covering event
creation and sharing, invite/RSVP flows, attendee tracking, location and video conference
attachments, recurrence, and user availability. It is intended to supersede the earlier
attempt in [MSC1116](https://github.com/matrix-org/matrix-spec-proposals/pull/1116) and to
incorporate the community feedback that drove that proposal toward
an iCalendar-compatible semantic model. It deliberately avoids a meetings-specific scope so
that higher-level applications (including video conferencing schedulers) can build on top._

Matrix currently has no first-class representation of calendar data. Users who wish to
schedule events with others over Matrix must either use an out-of-band calendar system and
paste details into chat, or rely on bespoke application-layer solutions that do not
interoperate.

**Motivation.** The driving use case is letting Matrix serve as a complete communication
stack for an organisation — the role Microsoft Teams / Outlook, Google Workspace, or open
suites such as openDesk (the ZenDiS Sovereign Workplace) fill today. In those products the
calendar is a distinct component (in openDesk's case a bundled Nextcloud) with no link
between an event and the room where it was arranged. Matrix has the chat and the calls but
not the calendar, and for some organisations that gap may be enough to keep them on a stack
where scheduling lives elsewhere. Concretely, this MSC targets:

- Sharing an event into a room a group already shares, with RSVPs visible inline.
- Inviting someone by their Matrix ID, with proper RSVP tracking, without knowing or
  exchanging an email address.
- Running an organisation's calendaring on its own homeserver rather than a hosted tenant.

It is explicitly fine for this to be an enterprise-leaning feature that not every client
implements, and for clients to ship partial support (e.g. a read-only event calendar in a
community room).

**Interoperability, not reimplementation.** Most of the world runs on iCalendar and CalDAV
and always will; there is no point at which everyone is on Matrix. This proposal therefore
treats CalDAV as a third-party network — reached, in the usual Matrix way, through a bridge
(Appendix A) — rather than reimplementing CalDAV inside Matrix. The client-server API
surface added here is kept to the bare minimum; everything that can be expressed as ordinary
room events is. The data model stays close to JSCalendar (see design philosophy below) so
conversion in either direction is straightforward, and an enterprise deployment that still
needs email invites can bridge those too.

**Privacy.** Meeting metadata — who, when, where, with whom — is sensitive, so the
availability query API (§4) is server-mediated: the queried user's homeserver filters
results by the caller's granted tier before responding, which a purely client-side scheme
could not do (the server could not withhold private events from the other side). E2EE comes
for free because calendar events are ordinary timeline events; §5 exists mainly to confirm
that and flag the plaintext-fallback pitfall, not as a headline feature.

A general, privacy-respecting, federated calendaring primitive in Matrix fills this gap
while keeping transparent interop with the iCalendar/CalDAV ecosystem that the majority of
the world already uses.

## Proposal

### Design philosophy

This proposal is guided by four core principles:

1. **Matrix-native first.** Events are Matrix timeline and state events, not iCalendar payloads
   embedded in Matrix. iCalendar/CalDAV compatibility is a translation concern at the bridge or
   client layer.

2. **Extensible events throughout.** All event types defined here use the content-block model
   from [MSC1767](https://github.com/matrix-org/matrix-spec-proposals/pull/1767). Clients
   without calendar support can render a meaningful `m.text` fallback. The relationship between
   this MSC and encryption is discussed in §7.

3. **Semantic alignment with JSCalendar.** Rather than inventing new field semantics, this
   proposal deliberately stays close to the data model of JSCalendar (RFC 8984 /
   draft-ietf-calext-jscalendarbis), which is itself designed to be a modern, JSON-native
   alternative and eventual successor to iCalendar (RFC 5545). This makes round-tripping with
   iCalendar and CalDAV straightforward while keeping the representation idiomatic Matrix JSON.
   Where JSCalendar and iCalendar semantics agree, we follow them; where JSCalendar improves on
   iCalendar (e.g. storing named timezones alongside UTC rather than UTC-only), we follow
   JSCalendar.

4. **Privacy by design (GDPR-compatible).** Availability queries reveal only time-slot
   occupancy, not event titles or attendee lists, unless the queried user explicitly grants
   more. No personally identifying information is required in federation-visible room state.

---

### 1. Calendar rooms

A **calendar room** is a Matrix room whose room type (the `type` field in the
`m.room.create` event content) is `m.calendar`. It acts as a
container for a user's or group's calendar events. Each user's personal calendar is a
private (invite-only) `m.calendar` room on their homeserver. Shared/group calendars are
`m.calendar` rooms with multiple members.

#### 1.1 Room creation

```json
{
  "type": "m.room.create",
  "content": {
    "type": "m.calendar",
    "m.federate": true
  }
}
```

Calendar metadata is stored in a dedicated state event:

```json
{
  "type": "m.calendar.info",
  "state_key": "",
  "content": {
    "m.text": [{ "body": "Personal calendar", "mimetype": "text/plain" }],
    "m.calendar.info": {
      "color": "#3c82f6",
      "timezone": "Europe/Berlin"
    }
  }
}
```

The `m.text` block (MSC1767) MUST be present as a human-readable fallback for unaware clients.

`m.calendar.info` fields:

- `timezone`: OPTIONAL IANA timezone identifier. Advisory only. It is the calendar's
  "home" timezone and is used by clients as (a) the default timezone for newly authored
  events and (b) the fallback timezone for rendering the calendar grid and all-day event
  boundaries when the viewing user has expressed no preference of their own. It MUST NOT
  override the per-event `start`/`end` timezone of any `m.calendar.event`. For shared /
  group calendars it represents the calendar's primary locale (e.g. a team's main office);
  members in other timezones SHOULD have times presented in their own local timezone
  regardless of this value.
- `color`: OPTIONAL. A suggested display colour as a `#rrggbb` hex string, carrying the
  calendar owner's intent across clients (equivalent to the CalDAV `calendar-color`
  property). It is purely advisory: clients MAY let the viewing user override it, and MUST
  cope with two calendars declaring the same value by disambiguating in their own UI (for
  example by reassigning one). Clients that do not support per-calendar colouring MAY
  ignore it entirely.

---

### 2. Calendar event type: `m.calendar.event`

A calendar event is a **timeline message event** sent into a calendar room. Using timeline
events preserves the append-only audit log, supports reactions, threading, and E2EE without
special-casing.

#### 2.1 Content structure

```json
{
  "type": "m.calendar.event",
  "content": {
    "m.text": [
      {
        "body": "Team standup – 2026-07-01 09:00–09:30 (Europe/Berlin)",
        "mimetype": "text/plain"
      }
    ],
    "m.calendar.event": {
      "uid": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Team standup",
      "start": {
        "utc": "2026-07-01T07:00:00Z",
        "localtime": "2026-07-01T09:00:00",
        "timezone": "Europe/Berlin"
      },
      "end": {
        "utc": "2026-07-01T07:30:00Z",
        "localtime": "2026-07-01T09:30:00",
        "timezone": "Europe/Berlin"
      },
      "all_day": false,
      "status": "confirmed",
      "transparency": "opaque",
      "description": "Daily sync with engineering team.",
      "organizer": "@alice:example.com",
      "location": null,
      "conference": null,
      "recurrence": null
    }
  }
}
```

**Field definitions:**

- `uid`: Stable UUID v4 (RFC 4122) that persists across edits, recurrences, and
  CalDAV round-trips. Maps to iCalendar `UID` and JSCalendar `uid`.
- `start` / `end`: Both UTC and named IANA timezone local time are stored. This mirrors
  JSCalendar's approach and avoids the UTC-only pitfall where stored times become incorrect
  when a timezone's DST rules change in the future (a known iCalendar pain point). Named IANA
  timezone identifiers MUST be used; numeric offsets alone are not acceptable.
- `transparency`: `"opaque"` (blocks availability) or `"transparent"` (does not block).
  Maps to iCalendar `TRANSP` and JSCalendar `freeBusyStatus`.
- `status`: One of `"confirmed"`, `"tentative"`, `"cancelled"`. Maps to iCalendar `STATUS`.
- `organizer`: The Matrix ID of the event organiser.
- The `m.text` content block MUST be included and SHOULD summarise title, time, and timezone
  so that clients without calendar support can display something useful.

#### 2.2 All-day events

When `all_day` is `true`, `start` and `end` contain only date strings:

```json
"start": { "date": "2026-12-25" },
"end":   { "date": "2026-12-26" }
```

Following iCalendar (and JSCalendar) convention, `end` for all-day events is exclusive.

#### 2.3 Location

The `location` field supports both a plain-text address and an optional `geo:` URI
(RFC 5870) for coordinates. Using `geo:` URIs follows the same convention as the existing
`m.location` event type (MSC3488), allowing clients that already know how to render
`m.location` coordinates to reuse that logic here without any special-casing. The `name`
field maps to JSCalendar's `Location.name` and iCalendar `LOCATION`; the `uri` field maps
to JSCalendar's `Location.coordinates` (which also uses `geo:` URIs).

```json
"location": {
  "type": "physical",
  "name": "Konferenzraum 3, Beispielstraße 1, 24943 Flensburg",
  "uri": "geo:54.7833,9.4333"
}
```

The `uri` field is OPTIONAL; a plain name without coordinates is valid for locations that
cannot be precisely geocoded. The `name` field is REQUIRED when `location` is present.

For virtual locations (web meeting URLs that are not Matrix-native calls), a `"virtual"`
type is used:

```json
"location": {
  "type": "virtual",
  "name": "Jitsi Meet",
  "uri": "https://meet.example.com/standup"
}
```

For virtual locations, `uri` is a plain `https:` URL that the user follows to join, rather
than a `geo:` URI.

#### 2.4 Video conference attachment (MatrixRTC)

When the event is associated with a Matrix-native video call, a dedicated `conference` block
is used rather than a generic virtual location. This enables clients to offer a one-tap
"Join call" action and allows bridges to emit a `CONFERENCE` property (RFC 9073) in
iCalendar output.

```json
"conference": {
  "type": "m.rtc",
  "application": "m.call",
  "room_id": "!callroom:example.com",
  "slot_id": "...",
  "via": ["example.com", "matrix.org"],
  "label": "Join call"
}
```

`type` is `m.rtc`, marking this a MatrixRTC conference. `application` names the MatrixRTC
application type (`m.call` today; MatrixRTC is expected to define further application types
in future, which slot in here without a schema change).

The `room_id` MUST be the Matrix room ID of an active MatrixRTC-enabled room. The
`via` field is a list of server names through which the room can be joined, following the
same convention as `m.space.child` state events and `matrix.to` links. Clients MUST include
at least one `via` entry when constructing this block; a `conference` block without a `via`
array SHOULD be treated as unresolvable and clients SHOULD disable the join button rather
than silently failing.

`slot_id` is OPTIONAL. A single MatrixRTC room can host multiple concurrent sessions
("slots"); when set, `slot_id` is the `state_key` of the `m.rtc.slot` state event
identifying the specific slot this calendar event refers to, as defined in
[MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143). When omitted, the
event refers to the room's default slot. The concrete slot-ID grammar is
application-specific (e.g. `m.call#ROOM` from
[MSC4196](https://github.com/matrix-org/matrix-spec-proposals/pull/4196)); this MSC does not
constrain it beyond deferring to the MatrixRTC definition, which is still in progress.

The call room is managed independently of the calendar event; this
MSC does not specify how it is created. Clients MUST NOT join a call room referenced by a
`conference` block without explicit user confirmation; see the "Call room linkage" security
consideration for how clients should help the user vet the target room before that.

`label` is a free-form action string chosen by whoever authored the block (e.g. "Join
call"). It is not the room's name and MUST NOT be presented to the user as the identity of
the room being joined.

#### 2.5 Recurring events

Recurrence rules use the iCalendar RRULE grammar (RFC 5545 §3.3.10) expressed as a
structured JSON object, avoiding the need to embed a raw RRULE string while retaining full
semantic compatibility:

```json
"recurrence": {
  "rrule": {
    "freq": "WEEKLY",
    "byday": ["MO"],
    "until": "2026-12-31"
  },
  "exdates": ["2026-08-05T07:00:00Z"]
}
```

Each **instance override** (e.g. a one-off change to a single occurrence of a recurring
event) is a separate `m.calendar.event` timeline event relating to the original:

```json
"m.relates_to": {
  "rel_type": "m.calendar.override",
  "event_id": "$original_event_id"
},
"m.calendar.event": {
  "uid": "550e8400-e29b-41d4-a716-446655440000",
  "recurrence_id": "2026-07-08T07:00:00Z",
  ...
}
```

`recurrence_id` identifies the specific instance being overridden by its original UTC start
time, matching JSCalendar's `recurrenceId` semantics.

#### 2.6 Editing and cancelling

Because timeline events are immutable and only replaceable by their original sender, only
the organiser can update or cancel their own `m.calendar.event`. Edits use
[MSC2676](https://github.com/matrix-org/matrix-spec-proposals/pull/2676)-style
`m.new_content` replacements sent by the same user who sent the original event.
Cancellation is an edit by the organiser setting `"status": "cancelled"`. No other party
can modify the event; if an invitee wants to counter-propose a different time, they do so
via an `m.calendar.invite` with `method: "COUNTER"` (§3.1), not by editing the original.

---

### 3. Attendees and RSVP

Matrix timeline events are immutable once sent: only the original sender can replace their
own event via `m.new_content`, and no power level (including admin) grants the ability to
edit another user's timeline event. Moderators and admins can redact events, but redaction
is destructive and removes content entirely. Attendee responses therefore cannot be written
back onto the organiser's original event by anyone other than the organiser themselves. This
proposal models attendees as separate per-user events that _relate to_ the calendar event,
each authored by the participant who owns them. This also means the full attendee list is
never baked into the immutable original event body; responses can accumulate, be updated, or be withdrawn over time without touching the original event.

#### 3.1 Invite: `m.calendar.invite`

The organiser sends an `m.calendar.invite` timeline event into the shared room between
organiser and invitee (a DM room or any other shared room). Room timeline events are the
sole specified transport for invites.

```json
{
  "type": "m.calendar.invite",
  "content": {
    "m.text": [
      {
        "body": "You are invited to: Team standup\n2026-07-01 09:00–09:30 (Europe/Berlin)\nOrganised by @alice:example.com",
        "mimetype": "text/plain"
      }
    ],
    "m.calendar.invite": {
      "uid": "550e8400-e29b-41d4-a716-446655440000",
      "sequence": 0,
      "method": "REQUEST",
      "calendar_event": {
        "title": "Team standup",
        "start": { "utc": "2026-07-01T07:00:00Z", "localtime": "2026-07-01T09:00:00", "timezone": "Europe/Berlin" },
        "end": { "utc": "2026-07-01T07:30:00Z", "localtime": "2026-07-01T09:30:00", "timezone": "Europe/Berlin" },
        "organizer": "@alice:example.com",
        "conference": { "type": "m.rtc", "application": "m.call", "room_id": "!callroom:example.com", "via": ["example.com"], "label": "Join call" }
      }
    }
  }
}
```

`method` maps to iTIP (RFC 5546) scheduling methods: `"REQUEST"`, `"CANCEL"`, `"COUNTER"`.
`sequence` is incremented with each revision of the invite, matching iCalendar `SEQUENCE`.

For **cross-ecosystem invites by email**, a CalDAV/SMTP bridge translates an incoming
iCalendar `METHOD:REQUEST` email into an `m.calendar.invite` in a room with the invitee.
The `uid` MUST be preserved verbatim from the iCalendar `UID` to enable round-tripping.

#### 3.2 RSVP: `m.calendar.rsvp`

The invitee replies in the same room with an `m.calendar.rsvp` event relating to the invite:

```json
{
  "type": "m.calendar.rsvp",
  "content": {
    "m.text": [{ "body": "Accepted: Team standup on 2026-07-01", "mimetype": "text/plain" }],
    "m.calendar.rsvp": {
      "uid": "550e8400-e29b-41d4-a716-446655440000",
      "sequence": 0,
      "partstat": "ACCEPTED",
      "comment": "See you then!"
    },
    "m.relates_to": {
      "rel_type": "m.reference",
      "event_id": "$invite_event_id"
    }
  }
}
```

`partstat` follows iTIP (RFC 5546): `"ACCEPTED"`, `"DECLINED"`, `"TENTATIVE"`,
`"NEEDS-ACTION"`.

The organiser's client aggregates all `m.calendar.rsvp` events relating to a given `uid` to
build the attendee list. Because each RSVP is its own timeline event authored by the
responding user, no event editing permissions are needed: each participant owns their own
response.

#### 3.3 Attendee list visibility

The complete attendee list is observable by any room member who can read the timeline of the
shared room where invites and RSVPs are exchanged. In E2EE rooms, attendee data is encrypted
and not visible to the homeserver. Organisers who wish to keep the attendee list private
SHOULD use a separate DM per invitee rather than a group room. This MSC does not define a
mechanism for the organiser to publish a consolidated attendee roster to all participants;
that is left to a future dependent MSC.

---

### 4. User availability

#### 4.1 Privacy model

Availability data is personal data under GDPR Article 4(1) and is subject to the data
minimisation principle (Article 5(1)(c)). This proposal therefore defines three tiers:

- **Tier 0 (default):** No availability information is shared. Queries are rejected with
  `M_FORBIDDEN`.
- **Tier 1 (explicit opt-in):** The user shares busy/free slot times only (no event titles, no attendee information) with specific Matrix users or all users on a trusted homeserver.
- **Tier 2 (contact grant):** The user additionally shares event titles with specific trusted
  contacts.

No tier shares attendee lists without a further explicit grant.

#### 4.2 Availability policy in the calendar room

The user's grant policy is stored as a state event in their `m.calendar` room:

```json
{
  "type": "m.calendar.availability_policy",
  "state_key": "",
  "content": {
    "default_tier": 0,
    "grants": [
      { "subject": "@bob:example.com", "tier": 1 },
      { "subject": "*:trusted-corp.example", "tier": 1 }
    ]
  }
}
```

#### 4.3 Working-hours window

A user may optionally publish their general working hours, analogous to RFC 7953
VAVAILABILITY, so that scheduling assistants know when slots are even worth querying:

```json
{
  "type": "m.calendar.availability_window",
  "state_key": "",
  "content": {
    "windows": [
      {
        "days": ["MO", "TU", "WE", "TH", "FR"],
        "start_time": "09:00",
        "end_time": "17:00",
        "timezone": "Europe/Berlin"
      }
    ]
  }
}
```

#### 4.4 Relationship to MSC4133 / MSC4175 (extensible profiles)

MSC4133 (merged in Matrix 1.16) allows arbitrary key-value pairs in user profiles. MSC4175
already uses this to expose `m.tz` (the user's IANA timezone). Extending this mechanism to
expose availability is appealing as it is already widely implemented, but profile fields are
public and non-granular: there is no per-contact access control. This MSC therefore uses
calendar room state events (which benefit from room ACLs and E2EE) for tier-controlled
availability grants, and proposes only that a user's _working hours window_ (§4.3) MAY
additionally be published as a profile field under
`m.calendar.working_hours` for use by clients that want a lightweight,
no-calendar-room indicator. Servers and clients SHOULD treat the calendar room state event
as authoritative if both exist.

#### 4.5 Availability query API

A new client-server endpoint allows a client to query another user's availability:

```
POST /_matrix/client/v1/user/{userId}/availability
```

Request body:

```json
{
  "range_start": "2026-07-01T00:00:00Z",
  "range_end": "2026-07-07T23:59:59Z"
}
```

The target user's homeserver evaluates the caller's tier:

- Tier 0 → `403 M_FORBIDDEN`
- Tier 1 → returns opaque busy intervals
- Tier 2 → returns busy intervals with titles

Response body (Tier 1):

```json
{
  "user_id": "@alice:example.com",
  "range_start": "2026-07-01T00:00:00Z",
  "range_end": "2026-07-07T23:59:59Z",
  "busy": [
    {
      "start": "2026-07-01T07:00:00Z",
      "end": "2026-07-01T07:30:00Z",
      "type": "BUSY"
    },
    {
      "start": "2026-07-03T08:00:00Z",
      "end": "2026-07-03T17:00:00Z",
      "type": "BUSY-UNAVAILABLE"
    }
  ]
}
```

`type` values mirror iCalendar FREEBUSY types: `"BUSY"`, `"BUSY-UNAVAILABLE"`,
`"BUSY-TENTATIVE"` (RFC 5545 §3.2.9). Events with `transparency: "transparent"` MUST NOT
appear as `BUSY`. The endpoint is placed under `/user/{userId}/` rather than a separate
`/calendar/` namespace to align with existing Matrix conventions for per-user resources.

#### 4.6 Federation

The requesting homeserver proxies the query to the target homeserver via a federation
endpoint:

```
GET /_matrix/federation/v1/user/{userId}/availability?start=...&end=...
```

The target homeserver applies tier evaluation before responding, keeping schedule data
within the user's own server by default.

---

### 5. Encryption considerations

#### 5.1 E2EE in calendar rooms

Calendar rooms that are E2EE-enabled encrypt all timeline events (including
`m.calendar.event`, `m.calendar.invite`, and `m.calendar.rsvp`) using the standard
`m.room.encrypted` wrapper, exactly as any other room message. No special handling is
needed because calendar events in this proposal are ordinary timeline events, not state
events. The homeserver cannot read event titles, descriptions, attendees, or locations in
an encrypted calendar room.

An encrypted calendar event on the wire looks like any other encrypted Matrix event. The
calendar-specific content sits entirely inside the ciphertext:

```json
{
  "type": "m.room.encrypted",
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "sender_key": "...",
    "session_id": "...",
    "ciphertext": "..."
  }
}
```

Once decrypted by a client, the plaintext payload contains the full calendar event:

```json
{
  "type": "m.calendar.event",
  "content": {
    "m.text": [
      {
        "body": "Team standup – 2026-07-01 09:00–09:30 (Europe/Berlin)",
        "mimetype": "text/plain"
      }
    ],
    "m.calendar.event": {
      "uid": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Team standup",
      "start": { "utc": "2026-07-01T07:00:00Z", "localtime": "2026-07-01T09:00:00", "timezone": "Europe/Berlin" },
      "end": { "utc": "2026-07-01T07:30:00Z", "localtime": "2026-07-01T09:30:00", "timezone": "Europe/Berlin" }
    }
  }
}
```

Note that `m.relates_to` is always outside the encrypted payload (per current Matrix spec).
This means that the relationship between an RSVP and its invite event ID is visible to
the server, though the content of both events is not. For example, an encrypted RSVP on
the wire exposes only the relationship:

```json
{
  "type": "m.room.encrypted",
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "sender_key": "...",
    "session_id": "...",
    "ciphertext": "...",
    "m.relates_to": {
      "rel_type": "m.reference",
      "event_id": "$invite_event_id"
    }
  }
}
```

The server can observe that some event relates to `$invite_event_id`, but cannot read the
RSVP content (the `partstat`, comment, or uid). Clients should be aware of this when
designing privacy-sensitive workflows.

#### 5.2 Relationship to MSC3956 (Extensible Events – Encrypted Events)

[MSC3956](https://github.com/matrix-org/matrix-spec-proposals/pull/3956) is a WIP MSC that
proposes an `m.encrypt` content block within the extensible events framework, allowing event
encryption to be expressed as a content block rather than a wrapping event type. There is
significant open discussion on that MSC about whether partial encryption (e.g. encrypting
only some content blocks) is desirable; reviewers have raised the concern that placing
`m.markup` as a plaintext fallback next to an encrypted calendar block would defeat
encryption entirely.

This MSC deliberately takes no dependency on MSC3956. Calendar events encrypted in calendar
rooms are encrypted at the room level via `m.room.encrypted` in the standard way. **Clients
MUST NOT include plaintext `m.text` fallback content alongside an encrypted calendar event
in a room where E2EE is enabled**, as doing so would leak the event title and description to
the homeserver and any eavesdropper who can read the unencrypted portion of the room
timeline.

To illustrate the problem: the following is an example of what a client MUST NOT send in an
E2EE room, because the `m.text` block is visible in plaintext to the server even though the
rest of the content is encrypted:

```json
{
  "type": "m.room.encrypted",
  "content": {
    "algorithm": "m.megolm.v1.aes-sha2",
    "ciphertext": "...",
    "m.text": [
      {
        "body": "Team standup – 2026-07-01 09:00–09:30 (Europe/Berlin)",
        "mimetype": "text/plain"
      }
    ]
  }
}
```

When E2EE is enabled in a calendar room, the `m.text` fallback block SHOULD be omitted from
the plaintext content entirely and MAY be included inside the encrypted payload for the
benefit of calendar-unaware clients that can decrypt but not render `m.calendar.event`.

---

## Potential issues

**Recurrence complexity.** RRULE is notoriously hard to implement correctly (EXDATE, RDATE,
override stacking, timezone-aware expansion). This proposal reuses the iCalendar grammar
verbatim so that existing RRULE parser libraries can be reused, but implementations MUST
correctly handle timezone-aware expansion and MUST NOT expand recurrences using UTC-only
arithmetic.

**Large calendar rooms.** A personal calendar room used over years could accumulate tens of
thousands of events. Clients will need server-side filtered pagination (e.g. by time range).
This is out of scope for this MSC but should be addressed in the Matrix room history API.

**Single invite transport.** This MSC specifies room timeline events as the sole invite
transport. The trade-off is that the existence of an invite (though not its content in E2EE
rooms) is visible to the homeserver as a room event.

**Attendee list is derived, not declared.** There is no single authoritative attendee list
event on the calendar event itself. Clients must aggregate RSVP events to build the list. This
is the correct approach given Matrix's permission model, but clients need to be careful about
handling late RSVPs, withdrawn RSVPs (a new RSVP with `partstat: "DECLINED"` superseding an
earlier `"ACCEPTED"`), and clock skew in `origin_server_ts`. The latest RSVP by
`origin_server_ts` for a given `uid` and sender SHOULD be treated as authoritative.

**No attendee data on recurring overrides.** When a single instance of a recurring event is
modified, the attendee RSVPs for that instance should ideally be re-solicited. This MSC
leaves the handling of per-instance RSVP state for a dependent MSC.

---

## Alternatives

**Embedding raw iCalendar blobs.** MSC1116 (2018) started as a custom event type; community
feedback pointed toward iCalendar mapping. One approach would be to embed `.ics` content as
an `m.file` attachment. This would achieve basic interop but loses Matrix-native features
(room ACLs, reactions, search, E2EE, threading) and makes availability queries impossible
without an out-of-band parse step. Rejected.

**Adopting JSCalendar as the verbatim content schema.** JSCalendar (RFC 8984 /
jscalendarbis draft-15) is the IETF's JSON-native calendar format and a strong semantic
match. We deliberately align with its data model (see design philosophy §3) but do not embed
it as a verbatim JSON object because: (a) its extension points conflict with MSC1767's
content-block model; (b) the jscalendarbis revision is still in active flux; (c) profiling
its ~80 optional fields for Matrix use would produce a much larger MSC. A JSCalendar ↔
Matrix conversion companion document is a natural follow-up.

**Using `m.room.member` membership for RSVP.** Room membership could model attendance:
"joined" = accepted, "invited" = pending, "left" = declined. Rejected because it conflates
room ACL with calendar semantics, would produce calendar rooms with potentially hundreds of
members, makes "tentative" attendance unrepresentable, and means the invite list drives room
access in ways the organiser may not intend.

---

## Security considerations

**Availability data leakage.** The tiered grant model (§4.1) is the primary mitigation.
Homeservers MUST enforce tier evaluation server-side. Rate limiting MUST be applied to the
`/user/{userId}/availability` endpoint to prevent timing-based calendar enumeration.

**Event UID collision / spoofing.** A malicious actor could emit an `m.calendar.event` with
a `uid` matching an existing event in the victim's calendar. Clients MUST scope UID
uniqueness to the `sender` MXID: UIDs are only globally meaningful in combination with the
organiser's identity. Bridges MUST validate that the sender MXID matches the iCalendar
`ORGANIZER` before accepting a cross-protocol invite.

**E2EE and plaintext leakage.** As noted in §5.2, including a plaintext `m.text` fallback in
an E2EE calendar room leaks event titles to the homeserver. Clients MUST suppress the
plaintext fallback when E2EE is active.

**GDPR.** Calendar data is personal data under GDPR Article 4(1). Homeservers that store and
federate `m.calendar.event` events act as data processors. The Matrix spec's existing account
data deletion and room purge mechanisms are the means to exercise the right to erasure
(Article 17). Server administrators should document data retention policies accordingly.

**Timezone manipulation.** Crafted timezone strings could cause denial-of-service in naive
parsers. Implementations MUST validate timezone identifiers against the IANA Time Zone
Database and reject unknown values with a 400 error.

**Call room linkage (phishing).** The `conference.room_id` field links a calendar event to a
Matrix call room, but nothing binds that room to the event's organiser or subject: a
malicious event can point it at an attacker-controlled room to lure users into joining. The
`label` field is a free-form string chosen by whoever authored the block and MUST NOT be
presented as the room's identity. A human-readable name carried inside the block would not
help either — it would still be an unbound string in the event and equally usable for
phishing. Therefore:

- Clients MUST require explicit user confirmation before joining a call room referenced by a
  `conference` block, and MUST NOT act on a block missing a `via` array.
- Before that confirmation, clients SHOULD present information that lets the user judge
  whether the target room is the one they expect — for example the room's own name and
  membership as resolved from the room itself (by peeking it, or resolving it via the `via`
  servers). This MSC does not define how a client obtains that information.
- Where the target room's identity cannot be resolved, clients SHOULD fall back to showing
  the raw `room_id`, so the user is never asked to join an entirely unidentified room.

---

## Unstable prefix

All snippets in this proposal use the stable identifiers. While this MSC is not yet
accepted, implementations MUST use the unstable identifier from the right-hand column
in their place.

| Stable identifier                                   | Unstable identifier                                                          |
| --------------------------------------------------- | --------------------------------------------------------------------------- |
| `m.calendar` (room type)                            | `org.matrix.msc4496.calendar`                                                |
| `m.calendar.info` (state event)                     | `org.matrix.msc4496.calendar_info`                                           |
| `m.calendar.event` (event type + content block)     | `org.matrix.msc4496.calendar_event`                                          |
| `m.calendar.invite` (event type + content block)    | `org.matrix.msc4496.calendar_invite`                                         |
| `m.calendar.rsvp` (event type + content block)      | `org.matrix.msc4496.calendar_rsvp`                                           |
| `m.calendar.override` (rel_type)                    | `org.matrix.msc4496.calendar_override`                                       |
| `m.calendar.availability_policy` (state event)      | `org.matrix.msc4496.availability_policy`                                     |
| `m.calendar.availability_window` (state event)      | `org.matrix.msc4496.availability_window`                                     |
| `m.calendar.working_hours` (profile field)          | `org.matrix.msc4496.working_hours`                                           |
| `/_matrix/client/v1/user/{userId}/availability`     | `/_matrix/client/unstable/org.matrix.msc4496/user/{userId}/availability`     |
| `/_matrix/federation/v1/user/{userId}/availability` | `/_matrix/federation/unstable/org.matrix.msc4496/user/{userId}/availability` |

---

## Prior art and related MSCs

- [MSC1116](https://github.com/matrix-org/matrix-spec-proposals/pull/1116) – Original
  calendar proposal by @Half-Shot (closed; this MSC supersedes it).
- [MSC3956](https://github.com/matrix-org/matrix-spec-proposals/pull/3956) – Extensible
  Events encryption (WIP; relationship discussed in §5.2).
- [MSC4133](https://github.com/matrix-org/matrix-spec-proposals/pull/4133) – Extensible user
  profiles (merged in Matrix 1.16; discussed in §4.4).
- [MSC4175](https://github.com/matrix-org/matrix-spec-proposals/pull/4175) – User timezone
  profile field (merged in Matrix 1.16; discussed in §4.4).
- [MSC3160](https://github.com/matrix-org/matrix-spec-proposals/pull/3160) – Message timezone
  markup (addresses timezone display in freeform messages; this MSC's structured event type
  supersedes that use case for scheduled events).
- [MSC4143](https://github.com/matrix-org/matrix-spec-proposals/pull/4143) – MatrixRTC
  (Matrix-native real-time communication; `conference.room_id` points to a MatrixRTC-enabled
  room and `conference.slot_id` to an `m.rtc.slot` defined there). Supersedes the earlier
  [MSC3401](https://github.com/matrix-org/matrix-spec-proposals/pull/3401).
- [MSC4196](https://github.com/matrix-org/matrix-spec-proposals/pull/4196) – Voice and video
  calling application for MatrixRTC (defines the `m.call` application type and its slot-ID
  grammar used in `conference`).
- [MSC3488](https://github.com/matrix-org/matrix-spec-proposals/pull/3488) – Location data
  (`m.location`; this MSC's `location.uri` field reuses the same `geo:` URI convention).
- [RFC 5546](https://www.rfc-editor.org/rfc/rfc5546) – iTIP scheduling methods.
- [RFC 6638](https://www.rfc-editor.org/rfc/rfc6638) – CalDAV scheduling extensions.
- [RFC 7953](https://www.rfc-editor.org/rfc/rfc7953) – VAVAILABILITY.
- [RFC 8984](https://www.rfc-editor.org/rfc/rfc8984) – JSCalendar 1.0.
- [draft-ietf-calext-jscalendarbis](https://datatracker.ietf.org/doc/draft-ietf-calext-jscalendarbis/) – JSCalendar 2.0.
- [RFC 9073](https://www.rfc-editor.org/rfc/rfc9073) – Event Publishing Extensions to
  iCalendar (defines `CONFERENCE` property used in §2.4 bridge mapping).

---

## Appendix A: CalDAV/iCalendar bridge guidance

_This appendix is informative. It describes how an Application Service or client-layer bridge
can expose this MSC's events to existing CalDAV/iCalendar tooling. It is not normative and
bridge implementors may deviate where needed._

A CalDAV bridge (e.g. implemented as a Matrix Application Service) can expose each user's
`m.calendar` room as a CalDAV calendar collection. The suggested field mapping is:

| Matrix                                  | CalDAV / iCalendar                  |
| --------------------------------------- | ----------------------------------- |
| `m.calendar` room                       | `VCALENDAR` collection              |
| `m.calendar.event` timeline event       | `VEVENT` resource                   |
| `uid`                                   | `UID`                               |
| `start.utc` + `start.timezone`          | `DTSTART;TZID=...`                  |
| `end.utc` + `end.timezone`              | `DTEND;TZID=...`                    |
| `transparency`                          | `TRANSP`                            |
| `status`                                | `STATUS`                            |
| `location.uri` (`geo:` URI, physical)   | `GEO` property                      |
| `location.name` (physical)              | `LOCATION`                          |
| `location.uri` (virtual) / `conference` | `CONFERENCE` (RFC 9073)             |
| `recurrence.rrule`                      | `RRULE`                             |
| `recurrence.exdates`                    | `EXDATE`                            |
| `m.calendar.invite` (METHOD:REQUEST)    | `VEVENT` in CalDAV scheduling inbox |
| `m.calendar.rsvp` (`partstat`)          | `ATTENDEE;PARTSTAT=...`             |
| `/user/{userId}/availability` response  | `VFREEBUSY`                         |

The bridge MUST strip event titles from `VFREEBUSY` responses unless the requesting
CalDAV principal holds a Tier 2 grant under the availability policy (§4.1).

For incoming iCalendar invites received via email (iTIP `METHOD:REQUEST`), a bridge MAY
synthesize an `m.calendar.invite` event into a Matrix room shared between the organiser
(bridged identity) and the Matrix invitee. The `uid` MUST be preserved verbatim from the
iCalendar `UID`. When the Matrix user RSVPs, the bridge SHOULD generate a
`text/calendar; method=REPLY` email to the organiser.
