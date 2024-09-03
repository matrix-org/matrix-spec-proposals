# MSC Checklist

This document contains a list of final checks to perform on an MSC before it
is accepted. The purpose is to prevent small clarifications needing to be
made to the MSC after it has already been accepted.

Spec Core Team (SCT) members, please ensure that all of the following checks
pass before accepting a given Matrix Spec Change (MSC).

MSC authors, feel free to ask in a thread on your PR or in the
[#matrix-spec:matrix.org](https://matrix.to/#/#matrix-spec:matrix.org) room for
clarification of any of these points.

- [ ] Are [appropriate
      implementation(s)](https://spec.matrix.org/proposals/#implementing-a-proposal)
      specified in the MSC’s PR description?
- [ ] Are all MSCs that this MSC depends on already accepted?
- [ ] For each new endpoint that is introduced:
    - [ ] Have authentication requirements been specified?
    - [ ] Have rate-limiting requirements been specified?
    - [ ] Have guest access requirements been specified?
    - [ ] Are error responses specified?
        - [ ] Does each error case have a specified `errcode` (e.g. `M_FORBIDDEN`) and HTTP status code?
            - [ ] If a new `errcode` is introduced, is it clear that it is new?
- [ ] Will the MSC require a new room version, and if so, has that been made clear?
    - [ ] Is the reason for a new room version clearly stated? For example,
          modifying the set of redacted fields changes how event IDs are calculated,
          thus requiring a new room version.
- [ ] Are backwards-compatibility concerns appropriately addressed?
- [ ] Are the [endpoint conventions](https://spec.matrix.org/latest/appendices/#conventions-for-matrix-apis) honoured?
    - [ ] Do HTTP endpoints `use_underscores_like_this`?
    - [ ] Will the endpoint return unbounded data? If so, has pagination been considered?
    - [ ] If the endpoint utilises pagination, is it consistent with [the
          appendices](https://spec.matrix.org/v1.8/appendices/#pagination)?
- [ ] An introduction exists and clearly outlines the problem being solved.
      Ideally, the first paragraph should be understandable by a non-technical
      audience
- [ ] All outstanding threads are resolved
    - [ ] All feedback is incorporated into the proposal text itself, either as a fix or noted as an alternative
- [ ] While the exact sections do not need to be present, the details implied by the proposal template are covered. Namely:
    - [ ] Introduction
    - [ ] Proposal text
    - [ ] Potential issues
    - [ ] Alternatives
    - [ ] Security considerations
    - [ ] Dependencies
- [ ] Stable identifiers are used throughout the proposal, except for the unstable prefix section
    - [ ] Unstable prefixes [consider](README.md#unstable-prefixes) the awkward accepted-but-not-merged state
    - [ ] Chosen unstable prefixes do not pollute any global namespace (use “org.matrix.mscXXXX”, not “org.matrix”).
- [ ] Changes have applicable [Sign Off](CONTRIBUTING.md#sign-off) from all authors/editors/contributors
