# MSC4569: Calendar

Matrix is currently optimized for real-time chat and native calls (via MatrixRTC). However, the protocol lacks
first-class support for organizing people to meet at specific times, managing invitations, and sending alerts for
upcoming events. Currently, such coordination relies on informal text messages or external, non-federated tools.

Modern digital calendars often suffer from friction when interacting across different vendors. When users from different
ecosystems are invited to an event, coordination often relies on email-based copies of calendar entries. This leads
to several synchronization and usability issues:

- **Sync Issues:** Calendar events can fall out of sync if email notifications are missed or ignored.
- **Fragmentation:** Users often need external links to bridge chat rooms with scheduled video calls.
- **Discovery/Sharing Difficulties:** Sharing entire calendars (including updates) is often cumbersome or impossible
  without third-party tools.
- **Scheduling Friction:** Finding mutually available time slots requires manual communication or external polling
  tools.

This proposal introduces a lightweight model for calendars, including events and tasks, directly within the Matrix
protocol. By utilizing a standardized data model, Matrix can provide federated, synchronized calendar functionality that
remains backwards compatible with existing ecosystems via email and guest access.

This MSC provides the foundational primitives required for calendar-based features.

## Proposal

This MSC adopts [IETF JSCalendar 2.0](https://datatracker.ietf.org/doc/draft-ietf-calext-jscalendarbis/) as the basis
for the calendar data model. Using an established specification allows for easier implementation of UI components,
import/export functionality, and bridging to existing services (such as CalDAV/iCalendar).

JSCalendar 2.0 defines three primary objects: `Event`, `Task`, and `Group`. To distinguish them from standard Matrix
events, these are referred to as `@type:Event`, `@type:Task`, and `@type:Group` from now on.

The following sections define various Matrix components for mapping JSCalendar data to Matrix. Here is a table for a
better overview.

| Matrix component                                   | Purpose                                                              |
|----------------------------------------------------|----------------------------------------------------------------------|
| `m.calendar` room type                             | Optional container for a single `@type:Group`                        |
| `m.jscalendar.group` state event                   | Stores the `@type:Group`, such as its title and description          |
| `m.jscalendar.event` state event                   | Stores an individual `@type:Event`                                   |
| `m.jscalendar.task` state event                    | Stores an individual `@type:Task`                                    |
| `m.jscalendar.patch` message event                 | Updates participant information within `@type:Event` or `@type:Task` |
| `m.jscalendar.patch.<state_key>` room account data | Stores private changes within `@type:Event` or `@type:Task`          |

### New room type

A new room type `m.calendar` is introduced.

An `m.calendar` room MUST contain a single `m.jscalendar.group` state event. If this state event is missing, the room is
considered "empty," and any other calendar-related events MUST NOT be processed as part of a valid group.

Effectively, an `m.calendar` room acts as a container for a `@type:Group`.

This room type does not act as a calendar unconditionally itself. Instead, it just marks the rooms main purpose to
contain calendar events. Similar to the room type `m.space`, the room can still be used for e.g. sending messages.

Clients MUST NOT rely on `m.room.name` or `m.room.topic` for these rooms. Instead, they should use the `title` and
`description` provided in the `m.jscalendar.group` state event.

### New state events

#### `m.jscalendar.group`

A new state event `m.jscalendar.group` is introduced.
This event MUST have an empty `state_key`.
Consequently, a room can only host one `@type:Group` at a time.

The content of this state event contains a `m.jscalendar.group` block. The following properties MUST NOT be included in
this content block:

- `@type`: This is inferred from the event type.
- `entries`: This array is derived from `m.jscalendar.event` and `m.jscalendar.task` events.

**Example `m.jscalendar.group` state event:**

```json
{
  "content": {
    "m.jscalendar.group": {
      "version": "2.0",
      "uid": "bf0ac22b-4989-4caf-9ebd-54301b4ee51a",
      "updated": "2020-01-15T18:00:00Z",
      "title": "A simple group",
      "description": "Let's have fun!"
    }
  },
  "event_id": "$143273976499sgjks",
  "origin_server_ts": 1432735824242,
  "sender": "@example:example.org",
  "state_key": "",
  "type": "m.jscalendar.group"
}
```

**JSCalendar reconstruction:**

To produce a full JSCalendar-compliant `@type:Group` object (e.g., for export), clients MUST:

1. Add `"@type": "Group"`.
2. Include all `@type:Event`s (via `m.jscalendar.event`) and `@type:Task`s (via `m.jscalendar.task`) into the `entries`
   array.

#### `m.jscalendar.event` and `m.jscalendar.task`

The new state events `m.jscalendar.event` and `m.jscalendar.task` are introduced.
The `state_key` MUST be a random string representing the object's `uid`.
The content of the state event contains a content block `m.jscalendar.event`/`m.jscalendar.task` matching `@type:Event`/
`@type:Task`. These content blocks MUST NOT contain the following JSON properties:

- `@type`: Inferred from the event type.
- `uid`: Inferred from the `state_key`.
- `version`: This is derived from the parent `@type:Group`.
- `participants/<user_id>`: The `<user_id>` MUST be a valid MXID (this also applies within `recurrenceOverrides`). Other
  participants are allowed. This maintains the ability to add participants via email invites, for example.

**Example `m.jscalendar.event` state event:**

```json
{
  "content": {
    "m.jscalendar.event": {
      "updated": "2020-01-02T18:23:04Z",
      "title": "Some event",
      "start": "2020-01-15T13:00:00",
      "timeZone": "America/New_York",
      "duration": "PT1H"
    }
  },
  "event_id": "$143273976499sgjks",
  "origin_server_ts": 1432735824242,
  "sender": "@example:example.org",
  "state_key": "a8df6573-0474-496d-8496-033ad45d7fea",
  "type": "m.jscalendar.event"
}
```

**JSCalendar reconstruction:**

1. Add `"@type": "Event"` or `"@type": "Task"`.
2. Add `uid` using the value from `state_key`.
3. Apply patches from `m.jscalendar.patch` message events.
4. Apply patches from `m.jscalendar.patch.<state_key>` room account data events.

Redacting an `m.jscalendar.event` or `m.jscalendar.task` removes it from the `@type:Group`.

### Patching participants via message events

To update participant information (e.g., `participationStatus`) with some room-accessible information, a new message
event `m.jscalendar.patch` is introduced. It contains the content block `m.jscalendar.patch` of the JSCalendar type
`PatchObject`.

This event MUST include a `m.relates_to` relation of type `m.jscalendar.patch` pointing to the target state event.

A pointer within the `PatchObject` MUST only modify the following properties, where `<user_id>` is the MXID of the
sender of the patch:

- `participants/<user_id>/*`
- `recurrenceOverrides/*/participants/<user_id>/*`

> [!WARNING]
> Clients MUST ignore any `m.jscalendar.patch` events where the `<user_id>` does not match the `sender_id` of the
message.

**Example `m.jscalendar.patch` message event:**

```json
{
  "content": {
    "m.jscalendar.patch": {
      "recurrenceOverrides/2020-01-15T13:00:00/participants/@example:example.org": {
        "participationStatus": "declined"
      },
      "m.relates_to": {
        "rel_type": "m.jscalendar.patch",
        "event_id": "$143273976499sgjks"
      }
    }
  },
  "event_id": "$14327werw499sgjks",
  "origin_server_ts": 1432735824242,
  "sender": "@example:example.org",
  "type": "m.jscalendar.patch"
}
```

Since patches target specific state versions, clients SHOULD follow the `replaces_state` history of an event to find
relevant relations and attempt to apply them to the current state. Clients SHOULD notify users if participant
information may be outdated due to state changes.

### Patching privately via room account data events

For private metadata (e.g., `alerts` or snoozed notifications), a room account data event
`m.jscalendar.patch.<state_key>` is introduced. The `<state_key>` corresponds to the `state_key` of the target event.
It contains the content block `m.jscalendar.patch` of the JSCalendar type `PatchObject`.


> [!WARNING]
> A pointer in the PatchObject MUST NOT change:
>
> - `@type`
> - `uid`
> - `participants`
> - `organizerCalendarAddress`
> - `sentBy`
> - `recurrenceId`
> - `recurrenceIdTimeZone`
> - `recurrenceRule`

**Example `m.jscalendar.patch` account data event:**

```json
{
  "content": {
    "m.jscalendar.patch": {
      "recurrenceOverrides/2020-01-15T13:00:00/alerts/snooze-id": {
        "@type": "Alert",
        "trigger": {
          "@type": "AbsoluteTrigger",
          "when": "2026-10-12T09:55:00Z"
        },
        "relatedTo": {
          "reminder-id": {
            "relation": "snooze"
          }
        }
      }
    }
  },
  "type": "m.jscalendar.patch.a8df6573-0474-496d-8496-033ad45d7fea"
}
```

### Calendar

While rooms with calendar events can exist independently, users may want to group them. Usually, this is referred to
as a calendar. This is possible by adding rooms with a `m.jscalendar.group` state event into a Matrix space. All data of
`@type:Group` still lies within these rooms. This is intentional, because being a member of a space (e.g., a
company) does not mean that one has access to all calendar data. If, for example, a company wants to share events for
all members, these JSCalendar data could be put directly into the space room.

## Appendix

### Use cases

To better understand the use cases this proposal covers, here are a few examples and how they could
be mapped:

* **Business Meeting:** A single `m.calendar` room containing one `@type:Event` object and a MatrixRTC call.
* **Team Calendar:** A single `m.space` room containing multiple `@type:Event` objects for daily standups or weekly
  meetings and multiple children for external business meetings.
* **Hybrid Conferences:** A single `m.space` with multiple children, where each room represents a different track
  or session including a widget for live-streaming.
* **Friend Group:** A single `m.room` room containing multiple `@type:Event` objects.
* **Public Holiday Subscription List:** A single `m.calendar` room containing multiple `@type:Event` objects.
* **TODO List:** A single `m.calendar` room containing multiple `@type:Task` objects.

There are a few other use cases that would require further MSCs based on this proposal:

* **Event Scheduling:** A mediator-like feature within a room to automatically share free time-slots.
* **Shadow Copies:** Using a specialized room to act as a bridge for "family" or "work" calendars.

### Compatibility with existing systems

For calendars based on Matrix to have a future, compatibility must be considered from the very beginning. While
JSCalendar already addresses this for the data model, the issue of communication remains unresolved. Since nearly all
existing systems use email to exchange copies of calendar entries, the following section examines various approaches to
backward compatibility. These are merely suggestions. What all these ideas have in common is that Matrix rooms should be
guest accessible (via a link) so that external users can also join video calls, for example.

#### Matrix client with integrated email client

For sending and receiving emails with iCal-based calendar event copies, a Matrix client could integrate an email client.
This works best when the user has only one Matrix-email-bridged client, is receiving calendar events, and there is no
other Matrix user involved. As soon as the event is managed in Matrix and other Matrix users are involved, there are
many open questions, such as who is sending the email.

#### Matrix Bot

A Matrix bot gets its own email address. A user can delegate email sending to a bot by inviting it to Matrix calendar
event rooms. The bot can then send email copies of the exported JSCalendar event by reading the participants field and
changing the participants field based on received emails. It could even further bridge regular chat messages. When a
user receives an email calendar event copy, they can forward it to the bot's email address to have it bridged to Matrix.

#### Matrix Appservice

Based on the ideas in the Matrix bot section, an appservice could be more integrative. For example, a company could
connect the appservice to an email backend to filter, send, and receive email calendar event copies on behalf of a
user via a double-puppeting bridge. This would make integration almost invisible for both sides.

## Potential issues

### Using JSCalendar 2.0 specification

The JSCalendar 2.0 specification was designed around a "copy-and-share" model. Matrix, however, uses a
"state-synchronization" model. This transition requires the adaptations detailed in this proposal (such as the `entries`
reconstruction) to ensure that the distributed state remains consistent and functional across federated servers.

## Alternatives

### One room as one calendar

Instead a calendar being a view of various rooms containing synchronized calendar events, a calendar could always be
exactly one room and the updates are sent and received via copy-share, similar to email. This approach is used
in [MSC4496](https://github.com/matrix-org/matrix-spec-proposals/pull/4496). While this mimics the way
calendar events are shared today via email, it also inherits all the problems discussed in the introduction of this
proposal.

### Matrix native events

Designing a new, custom data structure specifically for Matrix would avoid the need for JSCalendar. However, this would
sacrifice the interoperability, import/export capabilities, and the massive ecosystem of existing tools that a
standardized specification provides.

### Re-use Matrix relations

Both Matrix and JSCalendar define a relation system. Because Matrix only allows one relation per event and JSCalendar
requires multiple relations, JSCalendar relations are re-used. This also makes it easier to form the final obtained
`@type:Group`.

## Security considerations

### Encrypted state and account data

This proposal introduces additional metadata to Matrix rooms. All data defined in this proposal is intended to be
compatible with current encryption standards. However, because current Matrix implementations do not support the
encryption of state events or a general way to encrypt account data without new secrets, some data remains
unencrypted. Implementers should be aware that calendar metadata (titles, times, participants) might be visible to the
home server and any room members. [MSC4362](https://github.com/matrix-org/matrix-spec-proposals/pull/4362) would be a
candidate for encrypting state events.

## Unstable prefix

To ensure compatibility during development, the following prefixes MUST be used:

- room type `m.calendar` → `de.connect2x.msc4569.calendar`
- state event type `m.jscalendar.group` → `de.connect2x.msc4569.jscalendar.group`
- state event type `m.jscalendar.event` → `de.connect2x.msc4569.jscalendar.event`
- state event type `m.jscalendar.task` → `de.connect2x.msc4569.jscalendar.task`
- message event type `m.jscalendar.patch` → `de.connect2x.msc4569.jscalendar.patch`
- room account data type `m.jscalendar.patch.*` → `de.connect2x.msc4569.jscalendar.patch.*`
- content block type `m.jscalendar.group` → `de.connect2x.msc4569.jscalendar.group`
- content block type `m.jscalendar.event` → `de.connect2x.msc4569.jscalendar.event`
- content block type `m.jscalendar.task` → `de.connect2x.msc4569.jscalendar.task`
- event relation type `m.jscalendar.patch` → `de.connect2x.msc4569.jscalendar.patch`

## Dependencies

This MSC builds on:

- [MSC4565: Share additional invite state](https://github.com/matrix-org/matrix-spec-proposals/pull/4565)
