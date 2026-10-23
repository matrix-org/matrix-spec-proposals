# MSC3767: Time based notification filtering
Do not disturb / focus features are becoming standard across operating systems and networking products. Users expect to
be able to manage the level of noisiness from an application based on day and time.

Users should be able to configure many periods of notification levels during the day; for example before work, lunch
hour, and after work. They should also be able to schedule notification levels for a particular day of the week; for
example a quieter notification setting all day on No Meeting Wednesday, or complete silence over the weekend.

## Proposal

We introduce a push notification [condition](https://spec.matrix.org/v1.2/client-server-api/#push-rules) `time_and_day`
to filter based on time of day and day of week.

**`time_and_day` condition definition**

| key | type | value | description | Required |
| ---- | ----| ----- | ----------- | -------- |
| `kind` | string | 'dnd_time_of_day' | | **Required** |
| `timezone` | string | user's [Olson formatted timezone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) | The timezone to use for time comparison. This format allows for automatic DST handling | Optional. Defaults to UTC |
| `intervals` | array | array of time matching intervals (see below) | Intervals representing time periods in which the rule should match. Evaluated with an OR condition | **Required** |

**Time matching interval definition**

| key | type | value | description | Required |
| ---- | ----| ----- | ----------- | -------- |
| `time_of_day` | string[] | tuple of `hh:mm` time | Tuple representing start and end of a time interval in which the rule should match. Times are [ISO 8601 formatted times](https://en.wikipedia.org/wiki/ISO_8601#:~:text=As%20of%20ISO%208601%2D1,minute%20between%2000%20and%2059.). Times are inclusive | Optional. When omitted all times are matched.  |
| `day_of_week` | number[] | array of integers 0-7 | An array of integers representing days of the week on which the rule should match, where 0 = Sunday, 1 = Monday, 7 = Sunday | **Required** |


- `time_of_day` condition is met when the server's timezone-adjusted time is between the values of the tuple, or when no
  `time_of_day` is set on the interval. Values are inclusive.
- `day_of_week` condition is met when the server's timezone-adjusted day is included in the array.

When both `time_of_day` and `day_of_week` conditions are met for an interval in the `intervals` array the rule evaluates
to true.

```json5
{
    "kind": "time_and_day",
    "timezone": "Europe/Berlin",
    "intervals": [
        {
            "time_of_day": ["00:00", "09:00"],
            "day_of_week": [1, 2, 3, 4, 5] // Monday - Fri
        },
        {
            "time_of_day": ["17:00", "23:59"],
            "day_of_week": [1, 2, 3, 4, 5] // Monday - Fri
        },
        {
            // no time_of_day, all day is matched
            "day_of_week": [6, 7] // Weekend
        }
},
```

A primary usecase for this condition is creating 'do not disturb' behaviour.
For example, Wednesday morning focus time rule:
```json5
{
    "rule_id": ".m.rule.master",
    "default": true,
    "enabled": true,
    "conditions": [
        "kind": "time_and_day",
        "timezone": "Europe/Berlin",
        "intervals": [
            {
                "time_of_day": ["09:00", "11:00"],
                "day_of_week": [3] // Wednesday
            },
    ],
    "actions": [
        "dont_notify" // See note below
    ]
}
```

##### `dont_notify` and Do Not Disturb behaviour
`dont_notify` will stop badges from being
updated in the client during 'do not disturb' hours, so the user will not be
able to locate messages that were silenced when they are back online.
To silence push notifications but allow discovery of missed messages in app, `notify_in_app` as proposed in
[MSC3768](https://github.com/matrix-org/matrix-spec-proposals/pull/3768) should
be used.

## Potential issues
- If a user changes timezone their push rules will not automatically update. 

## Alternatives

#### System
Some systems (e.g. iOS) have their own DND / focus mode but this is only an option if all of your devices are within
that vendor ecosystem (here Apple) and doesn't help when you have e.g. an iPad and an Android phone. This also needs to
be configured per device.

#### `room_member_count` style comparison
```json5
"conditions": [
        {
            "kind": "time_of_day",
            "is": ">=18000000" // 17:00 NZST, 5:00 UTC 
        },
        {
            "kind": "time_of_day",
            "is": "<=75600000" // 9:00 NZST, 21:00 UTC
        },
        
    ]
```
As only one rule per `kind` + `rule_id` is allowed and rule conditions are an `AND` this allows only one contiguous
range to be defined. This precludes one of the main usecases for the feature - ignoring notifications outside of
work/waking hours.

#### Device assessment
An alternative version of the `time_and_day` defined above used timezone agnostic times and did not define a timezone.
This rule would be assessed only on the device. This is not easily achieved on every platform. 

#### ms offsets for time intervals
Previous proposals used ms offsets to represent time of day instead of `hh:mm`. Ms offsets may behave incorrectly on
days with a DST jump and are less intuitive.

## Security considerations
- Stores user's timezone on the server. DND periods saved to the server without timezone information would reveal
  information about a user's approximate timezone anyway. Users who do not wish to store their timezone can set DND
  periods in UTC (this option should be available in clients implementing time based notification filtering).

## Unstable prefix

- While this MSC is not considered stable `time_and_day` should be referred to as `org.matrix.msc3767.time_and_day`

## Dependencies
None.
