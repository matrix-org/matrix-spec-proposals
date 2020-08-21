# MSC2526: Add ability to delete key backups

[MSC1219](https://github.com/matrix-org/matrix-doc/issues/1219) defined a
mechanism for key backups.  However, it inadvertently omitted the endpoint to
delete an entire key backup.  This proposal adds the endpoint.

## Proposal

An endpoint is added, `DELETE /room_keys/version/{version}`, that deletes a
backup version.  Both the information about the key backup, as well as all keys
associated with the backup should be deleted.  If the specified version was
previously deleted, the endpoint succeeds, returning an HTTP code of 200.  If
the specified version never existed, the endpoint returns an HTTP code of 404
with a Matrix `errcode` of `M_NOT_FOUND`.
