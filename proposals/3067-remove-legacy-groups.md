# MSC3067: Remove all references to legacy groups implementation

[Groups](https://github.com/matrix-org/matrix-doc/issues/1513) were a conceptual idea of being able
to carve out a little corner of Matrix to list a series (or group) of rooms. Typically this would
be used by communities to represent their community/project on Matrix.

Though the feature worked for the extremely common use case, it had/has multiple sharp edges which
prevent it from being considered ready for widespread adoption. The details of which are spread over
multiple issue trackers and not recorded here, however the summary is that 
[MSC1772: Spaces](https://github.com/matrix-org/matrix-doc/pull/1772) is destined to replace the entire 
Groups system in Matrix.

To help accomodate Spaces landing in the spec, this MSC proposes a number of measures to ensure Groups
do not interfere.

## Proposal

Groups were originally designed and deployed before there was a formal MSC review process. As such,
some clients and servers ended up implementing the feature in the stable namespace without an 
appropriate spec release to back it up. This MSC proposes that the spec *not* introduce the lacking
documentation for groups. To action this, the spec would close [issue 1513](https://github.com/matrix-org/matrix-doc/issues/1513)
and all associated issues/PRs (except MSC1772, given that is Spaces), and refuse to add Groups to
the spec at a later date.

The [grammar](https://matrix.org/docs/spec/appendices#group-identifiers) for group identifiers has
already made it into the spec documents. This proposal removes that specification.

For the few non-Spaces MSCs listed on [issue 1513](https://github.com/matrix-org/matrix-doc/issues/1513),
the idea would be to propose FCP closure or mark those MSCs as abandoned/obsolete given the underlying
structure called a "group" would not be in the spec.

## Potential issues

By not including groups in any version of the specification there leaves a significant documentation
gap for a key feature in Matrix's history. This means that implementations, MSC authors, and interested 
developers will be required to dig up the history of Groups themselves if it is important for their
mission. The author of this MSC does not believe the effort required to document the whole Groups
system just to scrap it for Spaces provides enough value. Additional links can be added to the 
[canonical issue for groups in Matrix](https://github.com/matrix-org/matrix-doc/issues/1513) to
help cover any implementation details for future archeology, though this MSC does not mandate that
such links be provided.

This MSC could be perceived as blocked behind Spaces landing in Matrix, however this is not entirely
the case: given the Groups work is using a very ancient process, this MSC serves as a way to reject
the idea from entering the spec (as otherwise it would not have a chance to be considered).

## Security considerations

None relevant. This is essentially an MSC to say that a whole feature is not being added to Matrix
in its current form.
