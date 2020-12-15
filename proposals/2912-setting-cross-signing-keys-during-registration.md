# MSC2912: Setting cross-signing keys during registration

Setting cross-signing keys (the `/keys/device_signing/upload` endpoint)
requires UI Authentication as an extra layer of security to ensure that an
attacker cannot easily replace a user's cross-signing keys with one that they
control.  One of the side-effects of this is that when a user registers an
account, the client will need to another UI Auth to upload the user's
cross-signing key.  Some clients temporarily cache the user's password when
registering, to avoid prompting the user a second time for their password.
However, this does not work for users that sign in using Single Sign-on.

This proposal introduces a new field to the `/register` endpoint to allow a
client to upload the user's cross-signing keys when it is registering to avoid
needing to make a separate call to `/keys/device_signing/upload`.


## Proposal

A new field, `device_signing`, is added to the request body of the `/register`
endpoint, which allows a client to upload the user's cross-signing keys.  The
format for the new field is the same as the format of the request body for the
`/keys/device_signing/upload` endpoint.  That is, currently, it has
`master_key`, `self_signing_key`, and `user_signing_key` fields giving the
master cross-signing key, the self-signing key, and the user-signing key,
respectively.

If the server detects that given cross-signing keys are invalid in any way (for
example, if the self-signing key does not have a valid signature by the master
key), the `/register` request will fail with the same error as a corresponding
call to `/keys/device_signing/upload` would have given.


## Potential issues

If a client uploads the user's cross-signing keys in this way to an old server
that does not support the changes, then the user will be left without
cross-signing keys.  The client should detect this situation and re-upload the
cross-signing keys using `/keys/device_signing/upload`.  The client could
detect this by:

* checking that the server advertises a version of the spec that supports this
  change,
* checking that the server advertises support for the unstable feature flag,
  and/or
* fetching the user's cross-signing keys after registration is completed and
  ensuring that it is present and matches what was uploaded.


## Alternatives

We could instead drop the UI Auth requirement for
`/keys/device_signing/upload`.  This would reduce the security of the
cross-signing keys, though it is unclear how much security this actually adds.


## Security considerations

None.  This only adds the ability for a client to include cross-signing keys
when registering an account, so by definition, this is done by the owner of the
account.

## Unstable prefix

Until the changes land in a released version of the Matrix spec,
implementations should use `org.matrix.msc2912.device_signing` as the field
name rather than `device_signing`.  Servers should advertise the fact that they
support this unstable field name by using adding `org.matrix.msc2912` to the
`unstable_features` field of `/_matrix/client/versions`.
