# MSC4085: Improved C-S-Api Errors

In many places of the specification there currently are no error codes defined for obvious error cases.
This means that servers have to either decide it on their own, use `M_UNKNOWN` too often or cant handle it
properly. Additionally this also means that clients often end up preferring to state errors as verbatism
rather than having ways to show rich errors to users of their application.
This MSC is trying to improve this by proposing additional errors which can be used by both servers and
clients to improve the above stated scenarios.

## Proposal

The Proposal focuses on adding error codes to the C-S API primarily. The primary focus is formally defining
the obvious and easy errors like missing params, errors for parameters which are only required if a certain
condition was met and similar cases.

The proposal is split into different subsections for the various endpoints.


## Potential issues

Servers might need to change their logic to be able to emit some of these codes and adaption might take
a bit therefor.
Also Clients might end up with previously unknown errors and this may introduce new bugs into clients.


## Alternatives

Instead of enforcing these errors it might also be an option to do this in a similar fashion like
SMTP did with the ["Enhanced Status Codes"](https://www.rfc-editor.org/rfc/rfc3463) extension.
That means these would be errors which are attached to the less precise errors using well defined subtypes
of the error codes.

## Security considerations

None considered at this time.

## Unstable prefix

For existing error codes used in new places the existing names shall be used. For newly introduced error types
the `MSC4085_ERRORCODE` pattern should be used instead of `M_ERRORCODE`.
