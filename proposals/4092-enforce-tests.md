# MSC4092: Enforce tests around sensitive parts of the specification

*This MSC proposes a change in procedure to how proposals and clarifications land in the specification.
It does not add any new endpoints or alter the Matrix protocol in any way.*

The specification contains the rules that all clients and servers must follow in order to interoperate.
It is crucial that these rules are correct and consistent for the health of the Matrix ecosystem.
This MSC proposes enforcing extra requirements on proposals _and clarifications_ that modify these rules
in order to ensure that any changes remain consistent and correct.

## Proposal

Recently, it has become apparent that there are insufficient guard rails around changes to the specification,
such that [clarifications](https://github.com/matrix-org/matrix-spec/issues/1710) have been made to the
specification incorrectly. These changes can have security implications on the entire Matrix ecosystem. This
proposal proposes that any changes to the following areas of the specification MUST have end-to-end testing in
at least one homeserver implementation:
 - Room Versions
 - Server-Server API:
    * Authentication
    * PDUs
    * Room State Resolution
    * Signing Events
    * Joining Rooms

All of these areas are exclusive to server implementations. This means end-to-end testing MUST test with a
real homeserver implementation.

In practice, the ecosystem currently has the following end-to-end testing frameworks:
 - [Sytest](https://github.com/matrix-org/sytest)
 - [Complement](https://github.com/matrix-org/complement)

As such, **this proposal would force any proposal or clarification which touches the named areas of the specification
to have tests** in one of these projects. However, any end-to-end testing framework would suffice, at the
spec core team's discretion.

## Potential issues

This adds extra barriers for contributors, who now need to write code in order to get their proposal landed into
the specification. However, this has always been the case as the MSC proposal demands that there is a working
client and server implementation. In practice, these implementations _should have tests_ so the actual impact on
the MSC process is reduced.

However, this has significant implications on clarifications which typically do not have the same level of rigour
applied to them as the proposal process. This would likely result in fewer clarifications being made to these areas,
but when they are made they are more likely to be correct. The reduction in the number of clarifications to these
areas may outweigh the extra safety guarantees this proposal is attempting to make.


## Alternatives

The areas of the specification which need extra guard rails can be changed to reduce friction. However,
these areas were chosen because they are critical to the security of Matrix rooms.

The guard rails being applied could be made more or less strict, allowing unit tests to suffice in place
of end-to-end tests. Alternatively, a robust justification could be sufficient, provided it is backed
with evidence. In cases where clarifications to the specification were incorrect, whilst a robust
justification _was proposed_, it was not backed by evidence to support the claims being made.


## Security considerations

This MSC _should_ increase security around the proposals and clarifications process.
Psychologically, there is a risk that reviewers may become less vigilant if there are tests. Tests
are error-prone and may not be testing what is described in the clarification/proposal.

## Affected clarifications

As of this writing, the following clarifications would now be subject to the extra guard rails. This is
not an exhaustive list:
 - https://github.com/matrix-org/matrix-spec/issues/1708
 - https://github.com/matrix-org/matrix-spec/issues/1642
 - https://github.com/matrix-org/matrix-spec/issues/1569
 - https://github.com/matrix-org/matrix-spec/issues/1515
 - https://github.com/matrix-org/matrix-spec/issues/1514
 - https://github.com/matrix-org/matrix-spec/issues/1482
 - https://github.com/matrix-org/matrix-spec/issues/1373
 - https://github.com/matrix-org/matrix-spec/issues/1247
 - https://github.com/matrix-org/matrix-spec/issues/1246
 - https://github.com/matrix-org/matrix-spec/issues/1244
 - https://github.com/matrix-org/matrix-spec/issues/1136
 - https://github.com/matrix-org/matrix-spec/issues/1098
 - https://github.com/matrix-org/matrix-spec/issues/1061
 - https://github.com/matrix-org/matrix-spec/issues/1048
 - https://github.com/matrix-org/matrix-spec/issues/1046
 - https://github.com/matrix-org/matrix-spec/issues/849