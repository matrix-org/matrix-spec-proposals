MSC3895: Federation API Behaviour of Partial-State Resident Servers
============================================================================================================================

**TODO Draft MSC**
- need to define obligations for sending PDUs
- need to more thoroughly think through & define acceptable circumstances to use this error code


---

This appendix to [MSC3706] suggests adding an error code (`M_UNABLE_DUE_TO_PARTIAL_STATE`) to the Server-Server API.

This error can be returned by a server when it is unable to answer a query whilst it is undergoing an MSC3706 partial state join, for example because:

- it can't prove (or shouldn't be expected to be able to prove) whether the requesting homeserver is a member of the room or not
- it otherwise doesn't have enough state to answer the request


[MSC3706]: https://github.com/matrix-org/matrix-spec-proposals/blob/rav/proposal/partial_state_on_join/proposals/3706-partial-state-in-send-join.md

## Obligations to answer

In some cases, use of the error code is illegal and the receiving homeserver MUST NOT use this error; it is obliged to answer the request.

These cases are listed below.


### `/get_missing_events` or `/event_auth` after sending an event to the requesting homeserver

**TODO** I'm only assuming that `/event_auth` is actually needed. Are any other endpoints needed?

If a homeserver receives a `/get_missing_events` or `/event_auth` request nominating (**TODO** bad terminology) an event and:

- the receiving homeserver only has partial state for the room in question
- the receiving homeserver previously sent that nominated event to the sending homeserver

then the homeserver must be able to supply a response. The `M_UNABLE_DUE_TO_PARTIAL_STATE` error code is illegal in this situation.


## Backwards Compatibility

It is already the case that existing homeservers need to know how to work around malicious or misconfigured homeservers that may report invalid error codes, for example by trying the relevant requests against a different homeserver.

The addition of this error code to the specification should therefore not have any negative impact on backwards compatibility.


## Unstable Prefixes

`M_UNABLE_DUE_TO_PARTIAL_STATE` should be `ORG.MATRIX.MSC3895_UNABLE_DUE_TO_PARTIAL_STATE` whilst this proposal is unstable.


## Open questions

1. Why not just report a generic error instead?
    a. 'explicit rather than implicit' yada yada
    b. makes it clear that the server isn't down, it's just temporarily unable to answer that query (e.g. due to **TODO**). Avoids trouble with backoff.
    c. we may later find uses for this information, at which point it will be too late to specify it

