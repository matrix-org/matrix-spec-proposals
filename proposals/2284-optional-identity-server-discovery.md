# MSC2284: Making the identity server optional during discovery

Currently the specification requires that clients `FAIL_ERROR` (hard failure - do not continue)
when the `.well-known` file for `m.identity_server` points to somewhere invalid or is invalid
itself. This can cause problems for clients if they either don't need an identity server to
function (and are forced to validate it anyways) or the client ends up having to disable all
their login UX because the identity server is misconfigured/down.

This proposal aims to change that by allowing clients to make a conscious decision to continue
with the invalid identity server configuration, provided the homeserver configuration is valid.

## Proposal

Instead of `FAIL_ERROR` for an invalid `m.identity_server` schema/server, clients are to move
to the `FAIL_PROMPT` (inform the user, ask for input if applicable) state. Clients can decide
to show a warning that the identity server is unavailable and allow the user to continue with
the invalid (or client's default) configuration.

## Tradeoffs

Clients can end up being configured with an invalid or inoperable identity server. This is
considered a feature by this proposal to allow for less intelligent clients to have their
identity server disabled. Intelligent clients could interpret the lack of identity server
as the homeserver/user asking that identity server functionality be disabled in the client.
