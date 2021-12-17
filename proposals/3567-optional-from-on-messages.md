# MSC3567: Allow requesting events from the start/end of the room history

It can be useful to request the latest events in a room directly without calling
`/_matrix/client/v3/sync` first to fetch the room state. Some use-cases include:

* Requesting events using a different filter after receiving a `/sync` response.
* A client which does not need to fully sync an account, but wishes to inspect a
  specific room's history (perhaps for exporting or auditing).


## Proposal

The `from` field on the [`/_matrix/client/v3/rooms/{roomId}/messages`](https://spec.matrix.org/v1.1/client-server-api/#get_matrixclientv3roomsroomidmessages)
becomes optional. If it is not provided, the homeserver shall return a list of
messages from the first or last (per the value of the `dir` parameter) visible
event in the room history for the requesting user.

Note that Synapse already implements this, but it is not spec-compliant. It is
known to be used by Element Android [^1] and Element Web, and there are other
use-cases involving threads [^2], which shows real-world usage that this would
be valuable.

Ideally this would not be necessary and the `prev_batch` token received from
calling `/sync` could be provided as the pagination token to `/messages`, but this
will not work if you `/sync` with a filter that excludes a given class of event
(such as threaded replies), and all the events taking place in a room are of that
class. This will result in your `/sync` not returning an update for that room,
which means that your most recent `prev_batch` token precedes all the excluded
events. Trying to back-paginate from `prev_batch` using `/messages` will not
result in seeing the excluded events.


## Potential issues

None.


## Alternatives

The alternative is today's status quo: a client must first make a request to
`/_matrix/client/v3/sync` and then follow-up that request with queries to
`/_matrix/client/v3/rooms/{roomId}/messages`. This is clunky if the client is
going to throw away most of the information received from the `/sync` request.

The behavior also seems undefined if a different `filter` parameter is provided
for the call to `/sync` compared to the one used for `/messages`.


## Security considerations

None.


## Unstable prefix

Since this is modifying the endpoint to support not including a field, no unstable
prefix is necessary.


## Dependencies

N/A

[^1]: https://github.com/matrix-org/synapse/issues/5538

[^2]: In order to list all threads in a room without pulling the history locally
it uses `/messages` to push the filtering onto the homeserver. See https://github.com/matrix-org/matrix-js-sdk/pull/2065
