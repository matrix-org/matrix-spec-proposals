# Add ability to delete key backups

[MSC1219](https://github.com/matrix-org/matrix-doc/issues/1219) defined a
mechanism for key backups.  However, it inadvertently omitted the endpoint to
delete an entire key backup.  This proposal adds the endpoint.

## Proposal

An endpoint is added, `DELETE /room_keys/version/{version}`, that deletes a
backup version.  Both the information about the key backup, as well as all keys
associated with the backup should be deleted.  Like `POST
/room_keys/version/{version}`, and unlike `GET /room_keys/version/{version}`,
`{version}` cannot be empty, to ensure that the wrong backup is not
accidentally deleted.
