# MSC0000: Encrypted event indexing

While matrix rooms make a great place to store data it is very hard to retrieve this
data in a structured way.
In encrypted rooms the only approach is to download all `m.room.encrypted` events
and then parse all of them locally. So all server optimizations an indexed database
provides are not available.

It would be phenomenal and enable new ways to use matrix if one could do things like
in an encrypted room:

- Get all events of a specific type.
- Fetch all events that are tagged with a specific usecase.
- Get all events that fullfill simple conditions event.value is in interval. e.g:
  - get all events describing users in a specific
  - age interval,
  - get all videos with a specific length interval,
  - get all images in a specific x and y geographic coordinate interval,
  - get all calender events with specific participants,
  - get all calender events within a specific date,
  - ...

Here an idea is proposed that tries to leak a limited amount of metadata but
still allow the homeserver to retrieve the correct
events and send it to the homeserver.

## Proposal

To achieve this clients can introduce indexed fields.
To the homeserver these are readable because they are stored
outside the encrypted payload (like relations) and are made out of a UUID
and a floating point value.

```json
"index":{
    "001234567890UUID0987654321": 16.0,
    "101234567890UUID0987654321": 812324567653452.1,
    ...
}
```

The goal is to make the index by itself useless because there is no immediate
pattern/structure to it. Instead the meaning of the `index` section of each
event is derived by other encrypted events. `m.index-descriptor`

```json
{
    "type": "m.index-descriptor",
    "target_value": ["content","path_to","target_property"]
    "index": "1234index-uuid4321",
    "data_type": "date", "integer", "float", "enum" "custom",
    "enum_table":{
        "value1":[100,200],
        "value1":[200,2000],
        ...
    }
    "transform":{
        //  Integral(sum_j(A_j*Re(e^(i*x_j*B_j))+C_j + A_j/2+1) + C_0)
        "function": [(A_1,B_1,C_1), (A_2,B_2,C_2)],//<- random generated approx 100 el. 
        // needs to be integrated before applying
        "value_range": [-10, 10000]
        "offset": [x,y],
        "scale_x": number,
    } 
}
```

The transform.function and transform.offset will be used to transform the values.
The full equation looks as following:

`integral(abs(transform.function(input + offset[0])))+offset[1] = index_value`

for each event the client will compute this and add it to the event outside the
encrypted content.
If the client wants to fetch a specific range it applies the transform to the
borders of the range and asks the homeserver for all events that fulfill the condition.

Request:

```json
{
    "index": "1234index-uuid4321",
    "from": 0,
    "to": 1,
    "closest_to": 100,
    "page_size": 50,
    "page_token": "token_for_next_page_acquired_by_last_request"
}
```

Since the page tokens are unique it is enough to just sent a page token.
The homeserver will reuse the page size from the previous request.
The order can be defined by swapping the value of from/to.
cloest_to can not be used in combination with from/to in case both
are provided the hs has to ignore the closest_to property.
closest to will return an array where the `abs(index_value - closest_to)` is ascending.
Response:

```json
{
    "events":[{"MatrixEvent"}],
    "next_page_token": "token_for_next_page"
}
```

All `m.index-descriptor` events are listed with index entry state events
`m.index-entry`:

```json
{
    "type": "m.index-entry",
    "index_event_id": 1234event-uuid4321
}
```

## Potential issues

## Alternatives

Using unencrypted rooms for this kind of applications.

## Security considerations
