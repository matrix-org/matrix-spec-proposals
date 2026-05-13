# MSC4470: Routing reports to non-local destinations

*This MSC is part of “Reporting v2” - a project led by the Foundation’s T&S team to improve communication
and effectiveness of reports on Matrix.*

**Note**: This proposal is not intended to be a complete idea. It should be heavily reviewed prior
to implementation. It may be closed or replaced by a different approach as needed.

[MSC4457](https://github.com/matrix-org/matrix-spec-proposals/pull/4457) introduces a generic reporting
API which can be used to report a wide variety of content and material. The API lacks an ability to
copy the report to community and remote server safety teams, however. This proposal adds that routing
capability at time of submission.

This proposal does *not* define the precise mechanisms used to actually forward the report. Other
proposals and their alternatives are best placed to determine how exactly a report is actually sent
to the routable destinations.

**Process note**: Although this proposal is not technically blocked on the specific mechanisms used,
it would be best to artificially block it anyway. If the mechanism can produce errors, for example,
then the caller might need to be made aware of those and thus this proposal will need small changes.


## Proposal

MSC4457's `/report` endpoint is extended to include the following *optional* request body parameters
for all report types:

```json5
{
  "must_send_to": { // OPTIONAL
    "communities": { // OPTIONAL
      "!room": { "disclose_sender_id": true /* OPTIONAL; Default `false` */ },
    },
    "servers": { // OPTIONAL
      "example.org": { "disclose_sender_id": false /* OPTIONAL; Default `false` */ }
    }
  }
}
```

`must_send_to` explicitly describes the destinations it can send to as subobjects to avoid confusion
around "must send to `!room`" being interpretted as literally sending to `!room` rather than the
community safety team behind `!room` (if any). If `must_send_to`, `communities`, `servers`, or the
values under `communities`/`servers` are not objects, a `400 M_BAD_JSON` error is returned.

Each key under `communities` MUST be a [room ID](https://spec.matrix.org/v1.18/appendices/#room-ids).
Any keys which aren't room IDs cause a `400 M_BAD_JSON` error.

Each key under `servers` MUST be a [server name](https://spec.matrix.org/v1.18/appendices/#server-name).
Any keys which aren't server names cause a `400 M_BAD_JSON` error.

For each key under `communities` and `servers`, `disclose_sender_id` MAY be present in the object to
indicate whether the local server is to disclose the user ID that is sending the report to the destination.
If `disclose_sender_id` is `false` (the default if not provided) or not a boolean value, the local
server MUST NOT include the sender's user ID in the report to that destination.

For each destination, the local server MUST forward a copy of the locally filed report to the destination.
If a destination cannot feasibly be sent a report, it MAY be ignored or queued for later. If the
mechanism to send a report is asynchronous, network/DNS errors are *not* reasons to fail sending.
Examples where it's not feasible to send a report include the local server not knowing about a given
room ID or where the room does not specify enough information to use a forwarding mechanism.

The forwarded reports SHOULD use the same `report_id` that is being returned to the reporting user ID.

**Note**: Local servers can (and probably should) still forward reports after the initial request to
other parties as needed. They would simply use the same mechanisms they'd normally use at the initial
request time.

**Note**: None of the report destinations, including the local server, guarantee that the destination
will actually handle the report. This proposal aims to enable delivery of the report, leaving action
taken (or lack thereof) to other, non-technical, systems.


## Potential issues

* This proposal is written with an assumption that an async mechanism will be used to forward reports,
  like [MSC4468](https://github.com/matrix-org/matrix-spec-proposals/pull/4468) or
  [MSC4469](https://github.com/matrix-org/matrix-spec-proposals/pull/4469). If a sync mechanism is
  chosen instead, this proposal might need (hopefully trivial) changes to accomodate those proposals.

* The local server *always* ends up opening a report, or at least generating a report ID, even if
  that report is not handled under the server's safety policies. This is extra work for the local
  server, however it's entirely possible for a local server to auto-close or otherwise mark the
  report as unprocessable and move on.

  A similar situation arises when a report is forwarded to another destination (either during the
  initial request or later by the local server's safety team): the destination might not be able to
  handle the report and might auto-close it on their end.


## Alternatives

No major alternatives are identified. This proposal is largely agnostic to which mechanisms are used
to forward reports to other destinations.


## Security considerations

* This can allow a reporter to spam-forward reports at unrelated destinations. Local servers are
  encouraged to make use of the `429` error code to limit a sender's ability to spam-forward reports
  at multiple destinations, especially when requests to forward reports to more than 4 destinations
  are received. Additionally, clients SHOULD NOT provide UI/UX which allows a user to enter their own
  destinations. Users SHOULD be given a (short) list of checkboxes to choose from, such as "Report to
  this user's homeserver admins" and "Report to this room's moderators".

* When forwarding reports, users might not want to have their user ID disclosed to the destination.
  There are a number of reasons for why this might be, and they aren't iterated here. Users can opt
  *in* to sending their user ID to remote destinations if they choose.

  **Note**: The reporter can expect to still be contacted by remote destinations based on the report
  ID, even if they do not send their user ID along with their report. Future proposals will define
  how these communication mechanisms work, and might include an ability to deny contact where needed.
  Those future proposals are also expected to preserve requests to hide the reporter's user ID, even
  while replying to the destination's request for communication.


## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc4470.must_send_to`
instead of `must_send_to`. This prefix should be used even if MSC4457 itself is not considered stable.


## Dependencies

This proposal relies on the following proposals:

* [MSC4457: Generic reporting API](https://github.com/matrix-org/matrix-spec-proposals/pull/4457)
