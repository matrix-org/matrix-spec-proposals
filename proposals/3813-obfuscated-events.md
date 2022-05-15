# MSC3813: Obfuscated events

Currently, event content can be end-to-end encrypted, but the metadata cannot. This means that if
someone inspects the Matrix homeservers, they can see in what rooms one is most active, and at what
time they are most active.

We propose that clients send "dummy" events from time to time, at random intervals and times, in
random rooms to obfuscate the user's online times and relationships. It is mainly intended to
imitate the structure of two-sided conversations.

## Proposal
TBD
### Introduction
TBD
### Events

We add the following types of events:

#### `m.obfuscate.request`

Initiates a request to send obfuscated events to the other party.

Content attributes:

| Name | Type | Comments |
|------|------|----------|
| version | string | Must be `v0`. |
| min_interval | number | Minimum interval, in seconds, between two keepalive events. |
| max_interval | number | Maximum interval, in seconds, between two keepalive events. |
| retries | number | The number of retries that can be sent in keepalive events if the other party does not respond in a timely manner. |
| payload | string | Can be arbitrary content. |

The attributes `min_interval`, `max_interval` and `retries` indicates the parameters this party will stick to, not the parameters it expects the other party to stick to.

#### `m.obfuscate.accept`

Indicates that this party is willing to exchange obfuscated events with the other party.

| Name | Type | Comments |
|------|------|----------|
| version | string | Must be `v0`. |
| min_interval | number | Minimum interval, in seconds, between two keepalive events. |
| max_interval | number | Maximum interval, in seconds, between two keepalive events. |
| retries | number | The number of retries that can be sent in keepalive events if the other party does not respond in a timely manner. |
| payload | string | Can be arbitrary content. |

The attributes `min_interval`, `max_interval` and `retries` indicates the parameters this party will stick to, not the parameters it expects the other party to stick to.

#### `m.obfuscate.reject`

Indicates that this party is not willing to exchange obfuscated events with the other party, or wants to stop doing so.

| Name | Type | Comments |
|------|------|----------|
| version | string | Must be `v0`. |
| duration | number | Tells the other party how long, in seconds, they should not send a request again. -1 means they should never send requests again. 0 means they can send again immediately. |
| payload | string | Can be arbitrary content. |

#### `m.obfuscate.keepalive`

The keepalive message that imitates the structure of a conversation.

| Name | Type | Comments |
|------|------|----------|
| version | string | Must be `v0`. |
| payload | string | Can be arbitrary content. |

### Client behaviour

Clients MUST negotiate to exchange obfuscated events before sending the keepalive messages.

### Server behaviour
TBD
## Potential issues
TBD
## Alternatives
TBD
## Security considerations

The events MUST be sent in end-to-end encrypted rooms.


The payload SHOULD be randomly generated, and with random lengths. It SHOULD ideally be similar in length to other non-obfuscated
events in the room.

## Unstable prefix

Please use `moe.kazv.mxc.msc.obfuscated-events` as the unstable prefix.

## Dependencies

No hard dependencies.
