# MSC4587: Relaxing requirements for reauthentication on cross-signing-key upload

The current specification has this to say about uploading public cross-signing keys
via [`POST /_matrix/client/v3/keys/device_signing/upload`]:

[`POST /_matrix/client/v3/keys/device_signing/upload`]: https://spec.matrix.org/v1.19/client-server-api/#post_matrixclientv3keysdevice_signingupload

> User-Interactive Authentication MUST be performed for regular clients, except in these cases:
>
> * there is no existing master signing key uploaded to the homeserver, OR
> * there is an existing master signing key and it exactly matches the master
>   signing key provided in the request body [and other keys also match].

In practice, we have found this overly restrictive. This proposal suggests
relaxing the requirement, allowing server implementations to make their own
decision as to when to apply this additional check.

## Background

Matrix encryption expects each user to have a set of cross-signing keys, also
known (under [MSC4161]) as the user's "digital identity". Each of the user's
devices must then be signed by this identity.

[MSC4161]: https://github.com/matrix-org/matrix-spec-proposals/blob/andybalaam/crypto-terminology/proposals/4161-crypto-terminology.md#digital-identity

The cross-signing keys are asymmetric: they each have a public part, which the user
shares freely, and a secret part, which the user keeps to themselves.

The public parts are published by calling [`POST
/_matrix/client/v3/keys/device_signing/upload`]. Other users can then download
the public cross-signing keys for a particular user, and use them to validate
the signatures on each of that user's devices, to ensure they are genuine.

It is clear, then, that uploading a new set of public keys represents a
powerful attack vector for a would-be eavesdropper. Consider that Mallory has
gained access to an access token belonging to Alice: Mallory could then upload
a new set of cross-signing keys, which she then uses to sign a device under her
control, and is therefore able to intercept encrypted messages sent to Alice.

For this reason, the `/keys/device_signing/upload` endpoint is subject to
additional authentication requirements:

 * Initially the requirement (under
   [MSC1756](https://github.com/matrix-org/matrix-spec-proposals/pull/1756))
   was that all requests must pass through user-interactive authentication.

 * This was later relaxed in
   [MSC3697](https://github.com/matrix-org/matrix-spec-proposals/pull/3967) to
   allow the upload to take place without re-authentication if there was no
   existing published key.

 * A further change came in
   [MSC4312](https://github.com/matrix-org/matrix-spec-proposals/pull/4312),
   which specified how the re-authentication requirement should interact with
   OAuth 2.0 authentication (though note that no changes were made to when the
   reauthentication should take place).

In practice, the reauthentication requirements continue to be overly
zealous. For example, consider a user who has no active devices and has never
set up [server-side
secret storage](https://spec.matrix.org/v1.19/client-server-api/#storage) (aka
"Recovery"). Such a user has no alternative but to reset their cross-signing
keys; however under the terms of the current spec the server MUST require the
user to reauthenticate.

Rather than continue a series of MSCs making amall changes to the
reauthentication requirements, we propose to make this
implementation-dependent, and instead provide recommendations to homeserver
implementers.

## Proposal

Replace the current UIAA requirement for [`POST
/_matrix/client/v3/keys/device_signing/upload`] with the following text:

> Servers MAY require that clients reauthenticate themselves via the
> User-Interactive Authentication API.

Also, provide an informational box with text similar to the following:

> Implementers should be mindful that replacing cross-signing keys is a
> powerful attack vector, and should default to requiring a client to
> re-authenticate rather than allowing a client with only an access token to
> replace the keys.
>
> It will normally be appropriate to skip reauthentication if the user has no
> existing master signing key. It may also be appropriate to relax the
> requirement if the user has no alternative: for example, if they have no
> other devices, and have not set up server-side secret storage.

## Potential issues

TODO

## Alternatives

- Just drop the reauthentication requirement
- Do nothing
- Spell it out fully

## Security considerations

Yes. TODO

## Unstable prefix

None required.


## Dependencies

None
