# MSC4357: Live Messages via Event Replacement

## Introduction

This proposal introduces **Live Messages** for Matrix: recipients can see a message evolve in near real time while it is
being typed. The user experience is similar to streaming answers from LLMs (token-by-token) and to Simplex.chat's
mutable "chat items", but without introducing a new event type. Instead, we rely on Matrix's existing edit mechanism
(`m.replace` on `m.room.message`). Non-supporting clients degrade gracefully: they see a normal message which was edited
a few times and always end up with the final content.

Motivation includes more natural conversation flow, better perceived responsiveness, and resilience in unstable
environments (e.g., live reporting): every chunk that was sent remains stored, so the last known state is preserved even
if the sender disconnects prematurely.

## Proposal

A Live Message is a session of high-frequency edits applied to a single persistent `m.room.message`. The session starts
when the user enables "live mode" and ends when the user finalizes the message. We introduce an **unstable marker** in
event content to identify a live session and specify client/server behavior that reuses existing primitives.

### Event identification

- **Initial event**: a normal `m.room.message` whose `content` **MUST** include the unstable key
  `"org.matrix.msc4357.live": {}` (empty JSON object). This marks the start of a live message session.
- **Update events**: each update **MUST** be a `m.room.message` with `m.relates_to.rel_type = "m.replace"` and
  `m.relates_to.event_id` referencing the initial event; its `m.new_content` **MUST** contain the *full* updated body
  (and formatted body if applicable).
- **Final update**: when the user completes the message, the last update **SHOULD NOT** include the live marker. The
  absence of the live marker in the aggregated content signals session completion.

### Client behavior (sending)

- **Activation**: when the user toggles live mode, clients provide a clear UI affordance (e.g., lightning icon).
- **First send**: upon a natural boundary (e.g., finishing a word) or a short delay, send the initial message with the
  live marker and retain its `event_id` for subsequent `m.replace`.
- **Periodic updates**: send updates every ~2–3 seconds and/or on natural boundaries. Avoid per-keystroke updates. Each
  update replaces the entire content (`m.new_content` reflects the complete current text).
- **Completion**: on explicit send or mode exit, send a final update without the live marker. After this, do not send
  further updates for this session.
- **Rate limiting**: clients **MUST** avoid flooding and respect server guidance; batching is encouraged.

### Client behavior (receiving)

- When the initial event contains the live marker, supporting clients **SHOULD** render it in a "live" state (e.g.,
  subtle animation / icon). Updates targeting the same message via `m.replace` **SHOULD** update the displayed text in
  place, without showing a separate "(edited)" marker or spamming notifications. When a final update arrives without the
  live marker, the client **SHOULD** transition the message to a normal finalized state.
- Non-supporting clients treat the flow as "message followed by edits", ending with the correct final content.

### Server behavior

- No new endpoints or types are required. Homeservers store and federate the initial message and its `m.replace` updates
  as usual. Existing aggregation behavior applies. Homeservers **MAY** apply rate limits to high-frequency edits and/or
  offer retention policies for rooms with heavy live usage.

## Room-level control: `m.room.live_messaging` (optional)

To allow administrators and room moderators to control the feature, we introduce a room state event:

- **Type**: `m.room.live_messaging` (unstable: `org.matrix.msc4357.live_messaging` until accepted)
- **State key**: `""`
- **Content**:
  ``` json
  {
    "enabled": true
  }
  ```

### Semantics:

- If absent, default is enabled (unless server policy states otherwise).
- If `enabled: false`, clients **MUST NOT** offer live mode in this room.
- Servers **MAY** enforce rejection of events that carry live markers in rooms where it is disabled.

## Backwards compatibility

Because live sessions are realized as normal edits, older clients retain a consistent view: they see a message which was
edited. Users always end up with the final text. Supporting clients provide a richer in-place progressive rendering.

## Security and abuse considerations

- **Spam / flooding**: A malicious client could emit updates too frequently. Mitigations include server rate-limits,
  client batching, and room-level disabling via `m.room.live_messaging`. This is not a new class of risk compared to
  rapid normal edits; existing controls apply.
- **Privacy**: Live updates reveal intermediate drafts. This is a user-experience choice; clients should clearly label
  the mode and allow users to opt out. The content remains subject to the same E2EE/federation properties as standard
  messages.
- **Storage**: Live sessions produce more events. Deployments can rely on retention policies and rate-limits.

## Alternatives

- **Ephemeral chunks** (`m.ephemeral...`): reduces storage, but loses data on disconnect and degrades UX on older
  clients (they see nothing until the final send). Not recommended.
- **New relation type** (e.g., `m.live_update`): adds semantic clarity but provides limited practical benefits over
  `m.replace` and worsens compatibility; clients can already infer live sessions via the marker and frequency.

## Use cases

- Natural real-time conversations.
- Live reporting in unstable networks (maximize delivered information).
- Streaming responses from bots/LLMs (token-by-token rendering inside Matrix).
- Customer support scenarios where reduced response latency improves user experience.
- Real-time collaborative environments where immediate feedback is valuable.

## Unstable identifiers

- Content marker: `"org.matrix.msc4357.live": {}`
- Room state: `org.matrix.msc4357.live_messaging`

After acceptance, the stable equivalents **MAY** be standardized if needed.

## Implementations

- **Client (qualifying)**: TBD — a reference client implementing live mode UI, periodic `m.replace`, in-place rendering,
  and room state enforcement.
- **Bot/AS (optional)**: a demo streaming LLM output as live updates.

## Conclusion

This MSC introduces Live Messages with minimal protocol surface by reusing `m.replace`. It preserves compatibility,
improves perceived responsiveness, and supports important real-time scenarios. With optional room-level control and
existing server safeguards (rate-limits, retention), it provides a pragmatic, adoptable path to streaming-like UX in
Matrix.
