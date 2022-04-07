# MSC3767: Time based notification filtering
Do not disturb / focus features are becoming standard across operating systems and networking products. Users expect to be able to manage the level of noisiness from an application based on day and time.

Users should be able to configure many periods of notification levels during the day; for example before work, lunch hour, and after work.
They should also be able to schedule notification levels for a particular day of the week; for example a quieter notification setting all day on No Meeting Wednesday, or complete silence over the weekend.

## Proposal

We introduce a push notification [condition](https://spec.matrix.org/v1.2/client-server-api/#push-rules) `time_and_day` to filter based on time of day and day of week.

This conditions specifies `intervals` and `timezone`.

`timezone` is an [Olson formatted timezone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones). This timezone format allows for automatic handling of DST.
If not set or invalid UTC will be used.

`intervals` is an array of day and time interval configurations.
Intervals in the array are an OR condition.

Each interval is an object that defines a `time_of_day` tuple and `day_of_week` array.

- `time_of_day` is a tuple of `hh:mm` [ISO 8601 formatted
  times](https://en.wikipedia.org/wiki/ISO_8601#:~:text=As%20of%20ISO%208601%2D1,minute%20between%2000%20and%2059.).
  This condition is met when the server's timezone-adjusted time is between the values of the tuple. Values are
  inclusive. If `time_of_day` is not set on an interval all times will meet the condition.
- `day_of_week` is an array of integers representing days of the week, where 1 = Monday, 7 = Sunday. This condition is met when the server's timezone-adjusted day is included in the array.

When both `time_of_day` and `day_of_week` conditions are met for one of the intervals in the`intervals` array the rule evaluates to true.

```json5
{
    "kind": "dnd_time_and_day",
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
            // no time_of_day, all day on Sunday is matched
            "day_of_week": [7] // Sunday
        }
},
```

A popular usecase for this condition is overriding default push rules to create a do not disturb behaviour.
For example, Wednesday morning focus time rule
```json5
{
    "rule_id": ".m.rule.master",
    "default": false,
    "enabled": true,
    "conditions": [
        "kind": "dnd_time_and_day",
        "intervals": [
            {
                "time_of_day": ["09:00", "11:00"],
                "day_of_week": [3] // Wednesday
            },
    ],
    "actions": [
        "dont_notify"
    ]
}
```


## Potential issues
- If a user changes timezone their push rules will not automatically update. 

## Alternatives

#### System
Some systems (e.g. iOS) have their own DND / focus mode but this is only an option if all of your devices are within that vendor ecosystem (here Apple) and doesn't help when you have e.g. an iPad and an Android phone.
This also needs to be configured per device.

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
As only one rule per `kind` + `rule_id` is allowed and rule conditions are an `AND` this allows only one contiguous range to be defined. This precludes one of the main usecases for the feature - ignoring notifications outside of work/waking hours.

#### Device assessment
An alternative version of the `time_and_day` defined above used timezone agnostic times and did not define a timezone. This rule would be assessed only on the device.

#### ms offsets for time intervals
Previous versions used ms offsets to represent time of day instead of `hh:mm`. Ms offsets may behave incorrectly on days with a DST jump.

## Security considerations
- Stores user's timezone on the server. DND periods saved to the server without timezone information would reveal information about a user's approximate timezone anyway. Users who do not wish to store their timezone can set DND periods in UTC.

## Unstable prefix

- While this MSC is not considered stable `time_and_day` should be referred to as `org.matrix.msc3767.time_and_day`

## Dependencies
None.
