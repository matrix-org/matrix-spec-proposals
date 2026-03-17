# MSC4435: Room slowmode

Some room administrators may want to limit the rate of
messages in a room.

## Proposal

### `m.room.slowmode`

This state event dictates the slowmode settings for the room.
Its format is:

```jsonc
{
	"events": {
		"m.sticker": {
			"rate_limit": 5000 // milliseconds
		},
		"m.room.message": {
			"rate_limit": 2000,
			"exempt_power_level": 20 // optional
		},
		"com.example.my_message_type": {
			"rate_limit": 60000
		}
	}
}
```

This state event has an empty state key (`""`). It MUST be ignored
if the state key is not empty.

Servers MUST NOT apply these limits to state PDUs.

Clients SHOULD display UI based on these settings; for example,
disabling the message input bar, or disabling certain buttons.

If this state event is not present in the room, slowmode does not apply.

Servers MUST reject PDUs sent over C2S with `M_LIMIT_EXCEEDED` if a user
attempts to send an event of a given type before `rate_limit` milliseconds
have elapsed since their last event of that type, and the user's power level
is not greater than or equal to the `exempt_power_level` key (if present)
for that event type.

If `exempt_power_level` is not present, no users are exempt from the rate
limit for that event type.

Servers MUST NOT drop PDUs that bypass the slowmode if they are received over
federation.

## Potential issues

Some servers in a room may not enforce these limits. This was deemed
acceptable as several other things in Matrix are also like this,
for example
[history visibility restrictions](https://spec.matrix.org/v1.17/client-server-api/#mroomhistory_visibility).

## Alternatives

None.

## Security considerations

None.

## Unstable prefix

| Stable            | Unstable                     |
|:------------------|:-----------------------------|
| `m.room.slowmode` | `com.nhjkl.msc4435.slowmode` |

## Dependencies

None.
