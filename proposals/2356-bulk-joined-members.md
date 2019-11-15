# MSC2356 - Bulk /joined_members endpoint

[`/rooms/{roomId}/joined_members`](https://matrix.org/docs/spec/client_server/r0.6.0#get-matrix-client-r0-rooms-roomid-joined-members)
is an endpoint designed for bots and bridges that want to get the list of members
in a room, and their profile information. Because it does not try to return the full event format, 
an equivalent call in [`/rooms/{roomId}/members`](https://matrix.org/docs/spec/client_server/r0.6.0#get-matrix-client-r0-rooms-roomid-members)
will take longer to complete. 

However, bridges often need to get membership information about rooms on startup to do things like
connect Matrix users to a IRC connection or sync membership across. The matrix.org hosted Freenode
IRC bridge made 15315 requests to `/joined_members`  when it was last restarted, which took 17 minutes
to complete. Because of this delay, the bridge was unusable for that time period while it was still
connecting membership information.

Clearly, there should be a better way to pull membership for many rooms which doesn't involve making
many calls to the homeserver.

## Proposal

This proposal covers the creation of a bulk room membership endpoint. 

The new endpoint will be called `POST /_matrix/client/r0/joined_members` and will not
take a `room_id` parameter. Rather a JSON body should be posted containing the list of rooms the
user is interested in. A JSON body is used rather than a query parameter because as in the example
above, the number of rooms may spill into the 10000s range which may cause issues with URI parsers,
or any intemedary load balancers. 

[RFC7230 states](https://tools.ietf.org/html/rfc7230#section-3.1.1) that the minimum recommended
length of a URL is 8000 octets, but this means that we cannot rely on support beyond that number.

#### Example request body

```
{
    "rooms": [
        "!foo:bar",
        "!bar:baz",
        "!not:real",
    ]
}
```

The `rooms` array SHOULD be checked for duplicates and only one response should
be returned for each unique `room_id`.

#### Example response body

```
{
    "joined": {
        "!foo:bar": {
            "@bar:example.com": {
                "display_name": "Bar",
                "avatar_url": "mxc://riot.ovh/printErCATzZijQsSDWorRaK"
            }
        }
        "!bar:baz" :{
            "@foo:example.com": {
                "display_name": "Foo",
                "avatar_url": "mxc://riot.ovh/printErCATzZijQsSDWorRaK"
            },
            "@bar:example.com": {
                "display_name": "Bar",
                "avatar_url": "mxc://riot.ovh/printErCATzZijQsSDWorRaK"
            }
        }
        "!not:real": null,
    }
}
```

`joined["room_id"]` follows the same format as `joined` in `/rooms/{roomId}/joined_members`.

Any rooms where membership could not be fetched MUST be returned as null.
The reason for not throwing an error is that applications may not want to lose the 
rest of the data because a room was not available to them. Applications SHOULD infer
that a `null` value means the authenticated user does not have permission to view the
membership of that room. They should retry with a different request if they want to 
know the reason.


## Potential issues

If an implementation is done poorly, it's possible to use this request to wedge
a homeserver by requesting membership from a huge number of rooms. Homeservers COULD
limit the number of rooms that can be requested, and return an error if that number is
exceeded. In this case, it is recommended that the homeserver raise limits for 
application services independently of normal users.

The response size of this request may be rather large, so implementors should take care to
allow for large payloads.

The time taken to serve this request may exceed the timeout of the request, so similiar semantics
COULD be applied as they are in /sync where the request continues to run on the homeserver
and is resumed when the next call to the endpoint is made.

## Alternatives

The current alternative solution to this problem is to keep running many `/joined_members`
requests concurrently to achieve the same result. As explained in the
introduction, this is not ideal.

## Security considerations

None. The endpoint should follow the same authorisation checks that the `/joined_members` endpoint makes.
