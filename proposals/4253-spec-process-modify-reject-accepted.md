# MSC4253: Modifying or rejecting accepted MSCs

The [spec process](https://spec.matrix.org/proposals/) defines the stages and steps an MSC goes through
before becoming actual specification. That process has an awkward accepted-but-not-merged state where
the MSC has successfully completed a *merge* FCP, but has not yet had a spec PR merged to introduce
that MSC to the formal specification. During this time, implementations MAY use stable identifiers when
speaking the MSC.

The general theory of this stage is that after several rounds of review, the MSC is unlikely to materially
change, but the MSC *could* still change if needed. Typically, this would be most likely to happen
during spec PR review.

The spec process does carve out the awkward state for potential modification, but does not describe
how modification (or post-acceptance rejection) actually happens though. This proposal clarifies what
is believed to be current operating procedure for these two actions.

## Proposal

For MSCs which are *accepted* but not *merged* (anywhere between `finished-final-comment-period` with
`disposition-merge` to `spec-pr-in-review`, inclusive), the following process steps MAY be taken:

1. The SCT may choose to revert FCP acceptance to bring the MSC back to "open, in review" or pull the
   MSC to `rejected` instead. The SCT is required to provide guidance to stable implementations, if
   applicable, for how to handle the change when this happens. It is left as an implementation detail
   to determine whether an MSC is brought back to `in-review` or pushed to `rejected`, and how to
   enact this process step. This step is known as "post-acceptance rejection", regardless of target
   state for the affected MSC.

2. Another MSC is required to change the text of the accepted MSC, provided it does two things:

   1. Describe the rationale for the change being made in a dedicated MSC; and
   2. Modify the accepted MSC's actual text in the same GitHub PR. This is to ensure that the change
      is captured in two ways: with a dedicated, unmerged, MSC and as real rendered text in the event
      someone is reviewing the accepted MSC's text.

When reviewing spec PRs for accuracy to their respective MSCs, reviewers are encouraged to use the
accepted, rendered, text as reference rather than the original GitHub PR for the MSC due to PRs not
updating post-merge.

## Potential issues

Spec PR reviewers may still miss MSCs which modify another accepted MSC. SCT members should consider
when it is more appropriate to use post-acceptance rejection instead of modification. For example, it
may be more correct to pull an MSC back to `in-review` when a modification would be significant or
easily forgotten.

Stable implementations of accepted MSCs may be severely affected by either process step. The SCT is
expected to work out a plan for how to address those incompatibilities when performing either step.

## Alternatives

No significant alternatives.

## Security considerations

No significant concerns.

## Unstable prefix

No unstable prefix is required for process MSCs.

## Dependencies

No direct dependencies, though [MSC4252](https://github.com/matrix-org/matrix-spec-proposals/pull/4252)
makes use of this MSC.
