# Remove `mimetype` from `EncryptedFile` object


## Proposal
The example in the spec currently lists `mimetype` in the [examples for `EncryptedFile`](https://matrix.org/docs/spec/client_server/r0.6.1#extensions-to-m-message-msgtypes) but not in
the object definition. As that is duplicate information of the `info` block of file events, the
mimetype should just be removed altogether.


## Potential issues
Some clients might depend on this.  However, as of August 2021, all known clients have
been confirmed to not use this.
