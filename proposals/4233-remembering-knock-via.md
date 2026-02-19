# MSC4233: Remembering which server a user knocked through

[Knocking](https://spec.matrix.org/v1.12/client-server-api/#knocking-on-rooms) allows users to request
an invite into a semi-public room from members already in that room. The use cases for this feature
vary, though it is relatively common that the room isn't already known to the user's homeserver. For
this reason, the [API endpoint for knocking](https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3knockroomidoralias)
accepts `via` parameters to assist the homeserver in locating another server to knock through.

Later, when the client wishes to show the user's pending knocks, it may wish to show the user more
information, or possibly even detect that the room became public and offer a direct join button. It
may do this through an API like the summary endpoint proposed in [MSC3266](https://github.com/matrix-org/matrix-spec-proposals/pull/3266).
When trying to call such endpoints, the client may only have a room ID, [which is unroutable](https://spec.matrix.org/v1.12/appendices/#room-ids),
leading to errors if the room is unknown to the server.

This proposal requires the server to remember what server(s) were used by a user to knock on a room,
making it available to clients to use in subsequent API calls. This proposal doesn't address invites
or other membership states because the client can parse the user ID which sent the membership change.

## Proposal

Within the [`GET /_matrix/client/v3/sync`](https://spec.matrix.org/v1.12/client-server-api/#get_matrixclientv3sync)
response is a `knock` section to denote which rooms the user has knocked on. This currently contains
a single property, `knock_state`, which is the [stripped state](https://spec.matrix.org/v1.12/client-server-api/#stripped-state)
for the room. This stripped state can be used for simple rendering of the room, but may be outdated
and require a refresh from the server using an API like the one proposed in [MSC3266](https://github.com/matrix-org/matrix-spec-proposals/pull/3266).

A new property next to `knock_state` is added, denoting the servers specified by the client at the
time of the most recent knock. This property is called `knock_servers`.

Example `/sync` response (irrelevant details not shown):

```json5
{
  "rooms": {
    "knock": {
      "!opaque:example.org": {
        "knock_state": {
          "events": [
            {"type": "m.room.name", "state_key": "", "content": {"name": "My Room"}}
          ]
        },
        "knock_servers": [ // new property
          "a.example.org",
          "b.example.org",
          "c.example.org"
        ]
      }
    }
  }
}
```

Servers SHOULD put the server name used to complete the [federation knock dance](https://spec.matrix.org/v1.12/server-server-api/#knocking-rooms)
first in the array. This is to help speed up API calls on servers which sequentially check `via`
parameters rather than process them in parallel. There's also a small amount of debugging benefit,
when troubleshooting knocks.

Servers MUST track the server names specified in `via` parameters on [`POST /_matrix/client/v3/knock/{roomIdOrAlias}`](https://spec.matrix.org/v1.12/client-server-api/#post_matrixclientv3knockroomidoralias)
when called with a room ID. Tracking server names specified as `server_name`s is optional due to the
parameter being [slated for removal](https://github.com/matrix-org/matrix-spec-proposals/pull/4213).
Servers MUST expose this information through `knock_servers`, as described above. Only the most recent
knock is required to be tracked, though prior knocks may be stored at the server's discretion.

Servers SHOULD impose a maximum limit of not less than 3 server names to track from a client's call.
This is to avoid a database disk fill if a malicious client decides to try knocking through a few
thousand servers, for example.

Clients MUST be tolerable to `knock_servers` being empty or missing as the knock may have happened
before the server tracked this information. Servers SHOULD use an empty array rather than lack of
field to denote this case, indicating that it is tracking server names for future knocks.

### Simplified sliding sync considerations

Simplified sliding sync is currently described as [MSC4186](https://github.com/matrix-org/matrix-spec-proposals/pull/4186)
and is set to overhaul the sync model for clients. This proposal doesn't change MSC4186, but does
suggest that the `knock_servers` field be similarly kept next to `knock_state` on a room subscription.

## Potential issues

Servers may not have already tracked this, so information will be lacking for already-knocked rooms.
Clients should expect errors, per usual, when attempting to call the summary API or any other endpoint.

## Alternatives

A client could track this information on its own, however this is not shared to other clients under
the user's account. This effectively leaves other clients operated by the user broken.

## Security considerations

As mentioned in the above proposal text, servers are encouraged to apply two limits:

1. Only record the most recent knock attempt.
2. Limit to 3 or more server names from that knock attempt.

Both of these limitations are to prevent unbounded data being stored on the server, leading to disk
fill or similar availability concerns.

## Safety considerations

No significant safety considerations identified.

## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc4233.knock_servers`
in place of `knock_servers`.

Simplified sliding sync may wish to include `knock_servers`'s behaviour independent to this MSC,
avoiding a complex MSC dependency tree.

## Dependencies

This proposal does not have formal dependencies, though clients bitten by the described bug are most
likely using [MSC3266](https://github.com/matrix-org/matrix-spec-proposals/pull/3266).
