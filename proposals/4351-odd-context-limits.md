# MSC4351: Odd Context Limits

Client-Server Version 1.15<sup>*</sup> § 10.23.1 [GET /_matrix/client/v3/rooms/{roomId}/context/{eventId}](https://spec.matrix.org/v1.15/client-server-api/#get_matrixclientv3roomsroomidcontexteventid) specifies query parameter `limit`:

> The maximum number of context events to return. The limit applies to the sum of the `events_before` and `events_after` arrays.

The treatment of a remainder from any odd dividend over the specified divisor of two is currently unspecified. The naïve implementation may perform two integer divisions of the `limit` which truncates the remainder to return equal counts of `events_before` and `events_after`; this does not technically violate the specification as it does not exceed the "maximum number" expressed by the `limit`.

Synapse instead biases the remainder to `events_after` which always returns the `limit` as requested (if sufficient events are available) rather than truncation. This is arguably more intuitive to client authors, especially after counting the "specified event" or "requested event" — `?limit=3` plus one for the requested event predictably returns four events, one before, and two after. This can be relied upon rather than ad hoc determinations to make additional requests or assumptions those requests will yield no more results.

We therefore codify the existing de facto behavior for odd context limits. With approximately 73.8%<sup>†</sup> of deployments already running Synapse: the impact is either negligible or actually compelling, with some client and library implementations possibly already making use of this behavior<sup>‡</sup>.

## Alternatives

The written specification will remain ambiguous to the de facto behavior of the principal server implementation. There are several negative implications to this alternative:
- The naïve implementation is arguably buggy: `limit=1` is effectively truncated to `limit=0`, contravening an intent of the request.
- Clients may realistically mistake the de facto behavior as canonical and misbehave when used with other implementations.
- The principal implementation has no obligation to maintain the behavior which may put mistaking clients at unnecessary risk.
- Alternative server implementations are under no obligation to _not_ mimic the principal implementation and even have compelling reasons to do so, further diverging the written specification out of relevance.

---
<sup>*. In addition to all earlier stable versions.</sup><br>
<sup>†. Statistics published by matrix.org [blog](https://matrix.org/blog/2025/09/19/this-week-in-matrix-2025-09-19/#matrix-federation-stats).</sup><br>
<sup>‡. Related discussion in issue [2202](https://github.com/matrix-org/matrix-spec/issues/2202).</sup><br>
<sup>א. Potential Issues: None</sup><br>
<sup>ב. Security Implications: None</sup><br>
