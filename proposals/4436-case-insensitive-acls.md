# MSC4436: Make server ACLs case insensitive

[MSC1383](https://github.com/matrix-org/matrix-spec-proposals/issues/1383) originally introduced
[server ACLs](https://spec.matrix.org/v1.17/server-server-api/#server-access-control-lists-acls). At
the time, the MSC failed to clarify whether ACLs are case sensitive or insenstive. The
[Synapse implementation](https://github.com/matrix-org/synapse/commit/3cf3e08a97f4617763ce10da4f127c0e21d7ff1d#diff-996dafa2cabdf043e51a444e5d3c5ba8389d48e6cdab0d469677974bd470d58fR726)
used `re.IGNORECASE` to match entries, indicating preference that the ACLs should be case insensitive.
Implementations based on Ruma will also [check case insensitively](https://github.com/ruma/ruma/blob/c242467a8ac13e691af10d69f76ca8c293e165db/crates/ruma-events/src/room/server_acl.rs#L64-L65).

Prior/internal drafts of the Server ACLs MSC available to the Spec Core Team also do not clarify case
sensitivity.

> **Note**: There is already a [spec PR](https://github.com/matrix-org/matrix-spec/pull/2334) for
> this change. A proposal is arguably not required, though because none of the proposal documentation
> states case sensitivity, this bug fix MSC is being opened to ensure there's no major compatibility
> issues with enforcing this. A similar process was used to enforce ACLs upon EDUs in
> [MSC4163](https://github.com/matrix-org/matrix-spec-proposals/pull/4163).


## Proposal

Server ACLs become case insensitive matches. `EXAMPLE.org` and `example.ORG` are the same.


## Potential issues

* [Server names](https://spec.matrix.org/v1.17/appendices/#server-name) are case sensitive in Matrix.
  This might mean that servers who aren't explicit targets of an ACL are affected, though in practice
  there's effectively zero non-lowercase server names in the public federation.

* Implementations which perform case sensitive matches might "leak" events from an ACL'd server. Tooling
  which checks for such leaks will need to consider that the implementation might be doing a case
  sensitive match on the ACL.


## Alternatives

Nothing noteworthy.


## Security considerations

Implied by the Potential Issues, attackers may use case sensitivity to get around an ACL. Clients
setting the ACL can add case variations of the server name to the ACL to temporarily patch those
servers.


## Safety considerations

Typically, if `example.org` is going on a deny list then the moderator also expects that `EXAMPLE.ORG`
will be denied too. This proposal reinforces that assumption/expectation.


## Unstable prefix

None applicable - this is already implemented in some implementations.


## Dependencies

No direct dependencies.
