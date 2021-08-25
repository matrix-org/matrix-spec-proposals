# MSC3360: Server Status

Many service providers have some way to get status information about them. Is the service up,
is it operating as expected, is there an incident going on, is there a maintenance window etc. This is
commonly done through status pages. Some homeserver operators may have a status page for their deployment,
but not everyone does. Users also need to be aware of these status pages and check them, Matrix clients are
completely unaware of them. There might also be other avenues through which homeserver operators
share this information, for example through micro blogging platforms.

The fact that this information isn't easily discoverable and programmatically accessible makes it hard
for clients to be able to distinguish between "am I broken", "is my homeserver broken" or "is there some
scheduled unavailability going on". Clients could use this information to provide better context to their
users, or surface things like ongoing or upcoming maintenance directly in their UIs.

There is also a psychological component to this. A client being able to show a message to a user notifying
them of the fact that a homeserver operator is aware of a problem or is executing on some maintenance helps
build confidence in the service, compared to a generic "error connecting to server". It may also spare a user
from going through all kinds of troubleshooting steps only to conclude the problem is not on their side.

As we saw during the spam attacks on Matrix in summer of 2021 that caused severe federation issues,
our inability to communicate to clients what was going on caused a lot of confusion. Servers were
up, but sometimes hours behind on traffic and we had no reliable way of signalling that this was going on
to clients.

## Proposal

This proposal aims to plug this gap, by providing a channel through which a client can get status
information about its homeserver. This proposal limits itself to exchanging this information between
a client and its homeserver, and does not address sharing this information between servers in a room
or making other servers' status available to clients over federation.

We want to expose upcoming maintenance so homeservers can inform their users that during a window of time
they might experience some intermittent issues using the service, but that this is expected. During
the maintenance window clients can also display this information. We also want to be able to signal
that a server is currently experiencing issues. Server deployments can fail for all kinds of reasons
unrelated to maintenance.

The fact that we want to be able to share this information reliably with a client introduces a
challenge: how do we do this if the homeserver itself is incapacitated? If we were to implement this
as an event type that goes down `/sync`, how does the client ever get the information?

To that end, this proposal wants to introduce both a new event type and a new endpoint. The new
endpoint will only return events of our new event type and behaves like a typical REST API endpoint
immediately returning a JSON payload. By doing it this way, a front-end such as a load balancer may be used
to handle this endpoint directly itself and return maintenance events in the event of the homeserver being
unavailable. Clients should only poll this endpoint when they're experiencing problems communicating with their
homeserver. In order to help speed up the propagation of this information, we propose to still send this information
to clients in `/sync` responses too, so that we're not solely dependent on clients polling this new endpoint. To
enable this, we introduce a new event type.

### Event type: `m.server.status`

An `m.server.status` event is proposed with the following makeup:

```json
{
  "content": {
    "summary": {
      "body": "same as m.text",
      "format": "same as m.text",
      "formatted_body": "same as m.text",
    },
    "description": {
      "body": "same as m.text",
      "format": "same as m.text",
      "formatted_body": "same as m.text",
    },
    "start_ts": "start of event timestamp",
    "end_ts": "end of event timestamp",
  },
  "state_key": "non-zero length string",
  "type": "m.server.status",
}
```

The summary is a brief description of the event and should be kept to a minimum length to
give clients an opportunity to display it in full on small screens. The description is the
extended version and can contain as much detail as the homeserver operator would like to
share.

The state key is used to update the event, such as when a maintenance window is moved, or
when its description gets altered. This also allows us to have multiple events, so we can
communicate about more than one incident.

An event with a `start_ts` and `end_ts` whose `start_ts` is in the future indicates a planned
maintenance event. A `start_ts` in the past and a lack of an `end_ts` indicates an ongoing
and unplanned outage. An event with an `end_ts` in the past has concluded. `start_ts` and
`end_ts` are timestamps in milliseconds since Unix epoch.

For the event to be valid, `summary` with a `body` is required, as well as a `start_ts`.

This new event type will be sent under a new `server_status` key in the `/sync` response,
as an array of `events`. The `server_status` key is optional and may be omitted entirely
if there are no events.

```json
"server_status": {
  "events": [
    {
      ...
    }
  ]
}
```

### Retrieval of status events: `GET /_matrix/client/r0/server/status`

This endpoint will return all server status events whose `end_ts` is either:
* absent, implying an ongoing incident
* in the future, implying planned maintenance
* up to 7 days in the past, in order to provide historical context that clients
  may chose to surface

The format is the exact same as that of the sync endpoint, except that the `events`
becomes a top-level key and is not nested under `server_status`.

### Creation of status events

How to create status events is left up to each implementation. No particular endpoint
is mandated for it to exist as part of the spec. We imagine this to be made available
through each implementation's preferred administrative interface/tooling.

## Potential issues

This solution isn't fool-proof. Even with the ability to offload the endpoint to a separate
front-end, if there's no way to reach the front-end in question (such as a network outage) the
information will not make it across to clients.

## Alternatives

A different approach would be to provide a way for the server to inform the client that
there is a different resource it could load to get status information from. The client could then
decide to load this resource (for example an actual status page) and present it to users. Though
it would help make this information available, since status pages don't have a standardised API
or data model it would be much harder for the client to display this information at an appropriate
time, or use it to provide additional context when errors occur.

We also considered implementing server status messages as just another room event. The reason
for not doing that is that clients would likely need some special handling for this room (it seems
undesirable to have it show up in clients directly) and users would have to be forcefully joined
in this room and not be allowed to leave in order to ensure these events make it to their client.
There does not appear to be prior art for using rooms this way.

Using [service notices][sn] would also be a possibility to implement something like this. In
practice there are concerns around the resource intensive nature of sending a notification to
an individual room for each user on the homeserver. As we expect this mechanism to be used to
expose information about an ongoing incident, we want to limit any additional strain this
mechanism could impose on a homeserver.

Both "status messages as rooms" and "server notices" would require the homeserver to be minimally
functional. This can't be guaranteed as this endpoint is still expected to be functional when the
homeserver as a whole is incapacitated. As such both of those approaches wouldn't solve our
problem.

[sn]: https://spec.matrix.org/unstable/client-server-api/#server-notices

## Security considerations

The new server status endpoint needs to be accessible without authentication. This is necessary to
ensure we can offload the endpoint. Otherwise that other system would need an up to date copy of
the user tables, as well as re-implement the authentication mechanisms.

## Unstable prefix

Until this MSC is accepted, implementations shall use `org.matrix.msc3360` as the event
type. The endpoint should be at `/_matrix/client/unstable/org.matrix.msc3360/server/status`.
