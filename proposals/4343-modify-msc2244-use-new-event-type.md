# MSC4343: Making mass redactions use a new event type

[MSC2244 (accepted)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2244-mass-redactions.md)
introduces a concept of "mass redactions", where a single `m.room.redaction` event can redact upwards
of about 1500 other events. This massively improves scalability of the redactions system in Matrix,
though by reusing `m.room.redaction` (and the `redacts`) key, the MSC becomes backwards incompatible
for clients which are expecting `redacts` to be a string.

MSC2244 does call out that it should have landed prior to [MSC2174 (merged)](https://github.com/matrix-org/matrix-spec-proposals/blob/main/proposals/2174-move-redacts-key.md)
to minimize this breaking change, but unfortunately that did not happen in practice.

This proposal suggests moving mass redactions to a new `m.room.redactions` (plural of `m.room.redaction`)
event type to minimize breakage in clients.


## Proposal

Instead of modifying the existing `m.room.redaction` event schema, MSC2244 is updated to say it uses
a new event type: `m.room.redactions`.

This change is primarily to maintain support for outdated clients (and to a degree, servers) which
may not support the `redacts` key being an array instead of string.


## Process note

MSC2244 is accepted under an older MSC process and has no known implementations. Typically, changes
such as those described above would happen prior to acceptance as they would have been caught during
implementation.

To honour the older MSC process as best as possible, MSC2244 is considered to remain accepted, but
is modified directly by this MSC as a pre-merge change. This MSC requires an implementation before
the modifications are accepted into the spec, and further MSC2244. This is why the PR for this MSC
modifies MSC2244 itself.


## Potential issues

Using another event type for redactions isn't great. Ideally, there would be a non-conflicting key
or fallback we could provide to `redacts` which has the same meaning, however it's difficult to
represent an array as a single string target within the same event.


## Alternatives

No significant alternatives. Proposals like [MSC4292](https://github.com/matrix-org/matrix-spec-proposals/pull/4292)
may prove valuable in gating MSC2244 behind a (breaking) room version, though such areas of thinking
are experimental as of writing.


## Security considerations

No significant security concerns apply.


## Unstable prefix

While this proposal is not considered stable, implementations should use `org.matrix.msc2244.redactions`
in place of `m.room.redactions`. Further, MSCs should note the room version requirements of MSC2244.

## Dependencies

This proposal has a mandatory dependency on MSC2244.
