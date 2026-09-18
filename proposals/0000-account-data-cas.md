# MSC0000: Atomic Account Data Updates via Compare-and-Swap

Clients may want to update account data while preventing race conditions with other clients,
in particular to prevent outdated clients from accidentally undoing newer changes made by other clients
when coming back online after some time and still having queued server requests.
Such behaviour may, for example, be used for syncing message drafts via account data (ideally combined with
some kind of account data encryption, e.g. as proposed in
[MSC4483](https://github.com/matrix-org/matrix-spec-proposals/pull/4483)).

As account data currently cannot ensure that the writing client is "up-to-date", the only way to achieve
similar resilience against races from outdated clients would involve tracking history manually (e.g. in
some dedicated private room using special events), which can, however, become expensive in terms of both storage
and computation.
Accordingly, this proposal suggests a way to support atomic compare-and-swap account data updates
on the server.


## Proposal

Clients may choose to include an `m.revision_id` field at the top level of the account data content,
which holds an opaque ASCII string to uniquely identify a revision of account data content.
This revision ID should be selected in a way that makes collisions unlikely (e.g., a random UUID, a timestamp
formatted as a string, or a hash of the local representation of the content).
The exact choice here is left as a client implementation detail.
When combined with some form of encrypted account data, e.g. via
[MSC4483](https://github.com/matrix-org/matrix-spec-proposals/pull/4483),
the revision ID must be stored outside of the encrypted payload.

Server endpoints for modifying account data should then accept a new optional query parameter, `expect_revision_id`.
This includes the following endpoints:

- `PUT /_matrix/client/v3/user/{userId}/account_data/{type}` for global account data
- `PUT /_matrix/client/v3/user/{userId}/rooms/{roomId}/account_data/{type}` for room account data

If `expect_revision_id` is not set, the endpoints will continue to work as usual, accepting arbitrary contents
(with or without a revision ID in the account data content).

If `expect_revision_id` is set, the server will look up the current account data content for the same key (and room ID
in the case of room account data) before writing, and compare its revision ID with the provided one.
If the revision IDs match, the server persists the new content as usual.
Otherwise, it responds with HTTP status code 409 for "Conflict".

The possible cases in more detail:

- If no account data exists yet, or the already persisted account data content lacks the `m.revision_id` field, then
  any provided value for `expect_revision_id` is treated as a match, and the value gets persisted as usual.
- If `m.revision_id` was set in the latest account data but is not a string, treat it as if the field were not set.
- Else, if `expect_revision_id` is set but empty, the write succeeds only if there's no pre-existing account data, or
  the currently stored account data lacks `m.revision_id` in its content, or the persisted revision ID is empty as well.
- Else, the write succeeds only if the revision IDs match exactly.

The server must execute this compare-and-swap atomically, to prevent multiple concurrent writes from satisfying the
write conditions while still conflicting with each other.
Even if `expect_revision_id` is set, the server does not require the new content to be written to contain any
`m.revision_id` field itself.

On revision mismatch, a 409 response from the server should use `M_REVISION_ID_MISMATCH` as `errcode`.
Servers are encouraged to include the conflicting account data payload in the response under the `current_content`
field to help clients resolve the conflict. Example:

```json
{
  "current_content": {
    "m.revision_id": "some_revision",
    "some_value": "Hi"
  },
  "errcode": "M_REVISION_ID_MISMATCH",
  "error": "Account data revision ID mismatch"
}
```

When clients receive a 409 conflict response, they are encouraged to persist the `current_content` locally
(or re-fetch the latest account data content if it's missing in the server response) in order to unblock future
writes, in case they missed previous account data updates or otherwise disagree on the latest account data content.


## Potential issues

Clients that are not aware of compare-and-swap account data can drop existing revision IDs and thus
remove any guarantees of being up-to-date for subsequent writes. This behaviour is preferred for
compatibility with revision-unaware clients, which should still be able to update account data
even if another client previously added a revision ID.


## Alternatives

Instead of a revision ID, one may decide to compare the whole account data JSON. Such an approach has several downsides:
- For arbitrary JSON content, it can be tricky to ensure that re-serialization produces exactly the same representation.
- Clients may not even want to store the original account data JSON. For example, when account data is encrypted,
  clients may not be interested in persisting the ciphertext, but since the server cannot decrypt the content,
  the actual ciphertext would have to be matched.


## Security considerations

Server implementations need to ensure that atomic compare-and-swap updates avoid excessive locking across users.
Otherwise, attackers could exploit lock contention by issuing compare-and-swap account data updates to cause a
denial of service.


## Unstable prefix

- To persist the revision ID in account data, use `com.beeper.revision_id` (instead of `m.revision_id`).
- To opt into compare-and-swap functionality, use `com.beeper.expect_revision_id` as the query parameter (instead of
  `expect_revision_id`).
- For the error code returned on a revision mismatch, use `COM.BEEPER.REVISION_ID_MISMATCH` (instead of
  `M_REVISION_ID_MISMATCH`).
- The error response may use `com.beeper.current_content` (instead of `current_content`) to provide the
  conflicting content.

## Dependencies

None.
