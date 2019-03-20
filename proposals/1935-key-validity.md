# Proposal to actually embrace key validity periods

A bug in Synapse (https://github.com/matrix-org/synapse/issues/4364) and therefore a bug in
the vast majority of the public federation means the current r0.1.1 specification has a bug
in it. In the interest of maintaining backwards compatibility with reality, this proposal
is to have the next room version (nicknamed "v4") enforce these restrictions. Version 1, 2,
and 3 rooms are expected to document that the validity period should have been respected
but wasn't.

Ultimately, this results in the next revision of the server-server spec saying that the
`valid_until_ts` property on a signing key does not matter unless the room version is v4
or a derivitive of v4.
