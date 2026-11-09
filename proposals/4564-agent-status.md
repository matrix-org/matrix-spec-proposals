# MSC4564: Agent status in room messages

## Introduction

AI agents increasingly use Matrix as their front end: a user sends a request in a room, an agent works on it (often for minutes) and answers, sometimes stopping to ask for approval. Clients see none of this as structure. Agents signal progress with ad-hoc conventions: a 👀 reaction on the request, an edited message listing tool steps, typing notifications, a prompt the bot reacts to itself with the choices. Clients either render these as noise or reverse-engineer each agent framework. There's no way for a client to show "working on step 3 of 5", "waiting for your approval" or "finished", or to offer an approval as buttons.

## Proposal

An agent MAY include an `m.agent` object in the content of `m.room.message` events it sends, and in the `m.new_content` of edits to them. All fields are optional:

| Field | Type | Meaning |
|---|---|---|
| `v` | integer | Version of this structure. This proposal: `1`. |
| `run` | string | Event ID of the request (the user's message) this event is about. |
| `state` | string | `working`, `waiting` (blocked on the user), `done`, or `failed`. |
| `step` | string | Short description of the current step. |
| `steps` | integer | Number of steps so far. |
| `progress` | number | 0.0–1.0, when the agent knows how far along it is. |
| `model` | string | Model in use. |
| `context` | number | Share of the model's context window in use, 0.0–1.0. |
| `cwd` | string | Working directory, where meaningful. |
| `cost_usd` | number | Spend so far in the session, in US dollars. |
| `result` | string | One-line summary of how the run ended, on the final (`done` / `failed`) status edit. |
| `choices` | array of `{key, label}` | Options for a prompt. The user answers with an `m.annotation` reaction whose `key` is one of the keys. |

### Status messages

An agent reports a run through one message, sent when work starts (`state: working`) and edited (`m.replace`) as it progresses, ending in `done` or `failed`. Clients use the latest edit. The message's `body` stays a readable fallback.

### Run result

On the final status edit the agent MAY carry `result`: a one-line summary of the outcome (what was achieved, or why it failed), written for a reader of run lists rather than the whole thread. Clients MAY show it as the run's summary body. It is untrusted sender text like every other field.

### Prompts

A message with `choices` and `state: waiting` is an open prompt. When the agent has acted on the answer (or the prompt expires) it edits the prompt to another state; clients treat only `waiting` prompts as open. The run's state is taken from its status message; an open prompt makes the run `waiting`.

### Clients

Clients MAY render runs (state, step, progress), offer open prompts as buttons that send the reaction, notify the user when a run waits on them or finishes, and show runtime information. Clients that don't understand the field show the message as usual.

### Example

```json
{
  "msgtype": "m.notice",
  "body": "Running the tests (3/5)",
  "m.relates_to": { "rel_type": "m.thread", "event_id": "$request" },
  "m.agent": { "v": 1, "run": "$request", "state": "working", "step": "Running the tests", "steps": 3, "progress": 0.6 }
}
```

## Potential issues

- **Edit volume.** Frequent status edits add events. Agents should coalesce updates (e.g. at most one edit every few seconds), as streaming bots already do.
- **Trust.** The fields are claims by the sender. Clients should only interpret them for senders the user has marked as agents (or that are otherwise trusted), and never act on them automatically: a `waiting` prompt is shown, not answered.
- **Encryption.** The fields live in the encrypted content like the rest of the message; nothing leaks to the server in encrypted rooms.

## Alternatives

- **Separate event types** (e.g. a state event per run): heavier, needs new permissions, and loses the readable fallback for clients that don't support it.
- **Reactions as status** (today's practice): clients can't distinguish them from human reactions, and they carry no step, progress or labels.
- **Polls ([MSC3381](https://github.com/matrix-org/matrix-spec-proposals/pull/3381)) for approvals:** polls collect votes over time; approvals are a single answer the agent acts on, and need to be tied to a run.

## Security considerations

A malicious sender can make a prompt look like an approval request. Clients must make clear who is asking (as they do for any message) and must not send answers without an explicit user action. Labels are untrusted text and must be rendered as such.

## Unstable prefix

Until accepted, use `org.fluxchat.agent` as the content key. Clients may read both `org.fluxchat.agent` and `m.agent` once stable.

## Implementations

- Client: [FluxChat](https://github.com/phrac/fluxchat) (run state, run bar, task board, approvals as buttons).
- Emitters: [`sdk/python` and `sdk/typescript`](https://github.com/phrac/fluxchat/tree/main/sdk) in the FluxChat repository, published as `fluxchat-agent` on PyPI and npm.
- Agent framework: [NousResearch/hermes-agent#138698](https://github.com/NousResearch/hermes-agent/pull/138698) — a 5-commit series for Hermes Agent that reports run state, steps, model, context use and spend on its progress messages and replies, settles orphaned runs, sends approval prompts with `choices`, and mirrors local sessions into a Matrix room.
